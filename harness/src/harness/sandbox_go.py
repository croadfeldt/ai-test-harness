"""Sealed execution for Go: the same isolation as sandbox.py, with the Go toolchain.

The environment is a scratch module, `harnesstest`, whose go.mod requires every module of the
application's resolved graph at the resolved version, so minimal version selection picks exactly
what the application runs with. The prefetch fills a module cache for that go.mod with the network
on and executes no package code (`go mod download` only unpacks). Inside the sandbox the cache is
mounted read-only, GOPROXY is off, and the generated tests run with `go test -json`, coverage on the
module under test. Results are written as junit.xml and coverage.json in the same shape the Python
sandbox produces, so every later stage reads them the same way.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from xml.sax.saxutils import escape

from . import config as _config
from .util import HarnessError, now_iso, write_json

IMAGE = str(_config.get("sandbox", "go_image", "HARNESS_GO_SANDBOX_IMAGE", "docker.io/library/golang:1.25-bookworm"))
LIMITS = {"memory": "4g", "pids": 1024, "timeout_s": 1200, "cpus": "2"}
MODULE = "harnesstest"


def go_mod_text(requirements: list[str], go_version: str) -> str:
    lines = [f"module {MODULE}", "", f"go {go_version}", "", "require ("]
    for r in requirements:
        path, _, ver = r.partition("@")
        lines.append(f"\t{path} {ver}")
    lines += [")", ""]
    return "\n".join(lines)


def prefetch_modcache(requirements: list[str], go_version: str, dest: Path, image: str = IMAGE) -> Path:
    """dest/go.mod + dest/go.sum + dest/modcache with the whole closure. Network on, no code run."""
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".complete"
    if marker.exists():
        return dest
    (dest / "go.mod").write_text(go_mod_text(requirements, go_version))
    (dest / "go.sum").write_text("")
    (dest / "modcache").mkdir(exist_ok=True)
    from . import sandbox as _py
    if _py.TARGET == "pod":
        # The stage pod has the network and the toolchain; download in place, onto the shared workspace.
        import os
        env = {**os.environ, "GOMODCACHE": str((dest / "modcache").resolve()), "GOFLAGS": "-mod=mod -modcacherw", "GOTOOLCHAIN": "local",
               "GOCACHE": str((dest / "gocache").resolve()), "HOME": os.environ.get("HARNESS_WORK_TMP") or tempfile.gettempdir()}
        proc = subprocess.run(["go", "mod", "download", "all"], cwd=dest, capture_output=True, text=True, timeout=3600, env=env)
    else:
        script = ("set -e; cd /mod; export GOMODCACHE=/mod/modcache GOFLAGS=-mod=mod GOTOOLCHAIN=local GOCACHE=/tmp/gocache HOME=/tmp; "
                  "go mod download all >/tmp/download.log 2>&1 || { tail -20 /tmp/download.log; exit 97; }; "
                  "chmod -R u+w /mod/modcache")
        if not shutil.which("podman"):
            raise HarnessError("podman is required for the Go sandbox target")
        proc = subprocess.run(["podman", "run", "--rm", "--userns=keep-id", "-v", f"{dest.resolve()}:/mod:rw,Z", "--tmpfs", "/tmp:rw,size=2g",
                               image, "sh", "-c", script], capture_output=True, text=True, timeout=3600)
    if proc.returncode != 0:
        raise HarnessError(f"go module prefetch failed: {(proc.stdout + proc.stderr).strip()[-800:]}")
    marker.write_text(now_iso())
    return dest


def _script(*, mod: str, modcache: str, gocache: str, tests: str, out: str, work: str, coverpkg: str, timeout_s: int, overlay: dict | None, mutant_src: str,
            include: list[str] | None = None) -> str:
    """The run, as a shell script, for either target. Paths differ; the steps do not."""
    replace = ""
    if overlay:
        replace = f"""
src=$(go list -m -f '{{{{.Dir}}}}' {overlay["module"]}) || {{ echo "MODULE_NOT_IN_CACHE"; exit 96; }}
mkdir -p {work}/mutant && cp -r "$src"/. {work}/mutant/ && chmod -R u+w {work}/mutant
(cd {mutant_src} && find . -type f ! -name overlay.json | while read f; do cp "$f" "{work}/mutant/$f"; done)
go mod edit -replace {overlay["module"]}={work}/mutant
"""
    files = " ".join(f"{tests}/{f}" for f in include) if include else f"{tests}/*.go"
    return f"""set -u
mkdir -p {work}/m {work}/gopath && cp {mod}/go.mod {mod}/go.sum {work}/m/ && cp {files} {work}/m/
cd {work}/m
export GOMODCACHE={modcache} GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE={gocache} GOPATH={work}/gopath HOME={work}{replace}
go vet . > {out}/vet.log 2>&1 || true
go test -json -count=1 -timeout {max(60, timeout_s - 60)}s -coverprofile={out}/cover.out -coverpkg={coverpkg} . > {out}/test.json 2> {out}/build.log ; rc=$?
exit $rc
"""


def run_tests(*, env_dir: Path, tests_dir: Path, out_dir: Path, cover: list[str], label: str,
              image: str = IMAGE, limits: dict = LIMITS, overlay_dir: Path | None = None) -> dict:
    """See _run_once. A build failure blamed on specific test files is retried without them (GF-022)."""
    summary = _run_once(env_dir=env_dir, tests_dir=tests_dir, out_dir=out_dir, cover=cover, label=label, image=image, limits=limits, overlay_dir=overlay_dir)
    blamed = files_blamed((out_dir / "stdout.log").read_text(errors="replace"), tests_dir) if summary["build_failed"] else []
    all_files = sorted(p.name for p in tests_dir.glob("*_test.go"))
    if blamed and len(blamed) < len(all_files):
        for name in ("stdout.log", "build.log", "test.json", "run.sh"):
            if (out_dir / name).exists():
                (out_dir / name).rename(out_dir / f"{Path(name).stem}-1{Path(name).suffix}")
        summary = _run_once(env_dir=env_dir, tests_dir=tests_dir, out_dir=out_dir, cover=cover, label=label, image=image, limits=limits, overlay_dir=overlay_dir,
                            include=[f for f in all_files if f not in blamed])
        first = (out_dir / "stdout-1.log").read_text(errors="replace")
        summary["files_not_compiled"] = {f: [l for l in first.splitlines() if l.startswith(f"./{f}:")][:5] for f in blamed}
        summary["build_failed"] = False   # the package built once the blamed files were out; their tests are errors, below
        _append_compile_errors(out_dir, tests_dir, summary["files_not_compiled"])
        write_json(out_dir / "sandbox.json", {**summary, "junit": "junit.xml" if summary["junit"] else None, "coverage": "coverage.json" if summary["coverage"] else None})
    return summary


def _append_compile_errors(out_dir: Path, tests_dir: Path, blamed: dict) -> None:
    """The tests inside a file that did not compile, as error results, so a reviewer sees each one."""
    from .adapters import go as _go
    tests = _tests_from_events(_events(out_dir / "test.json"))
    for fname, errors in blamed.items():
        for t in _go.test_names((tests_dir / fname).read_text(errors="replace")):
            tests[f"harnesstest::{t}"] = {"status": "error", "duration_ms": 0, "message": "did not compile: " + "; ".join(errors)[:1500]}
    _write_junit(out_dir / "junit.xml", tests)


def _run_once(*, env_dir: Path, tests_dir: Path, out_dir: Path, cover: list[str], label: str,
              image: str = IMAGE, limits: dict = LIMITS, overlay_dir: Path | None = None, include: list[str] | None = None) -> dict:
    """Run every *_test.go in tests_dir as package harnesstest against the prefetched module cache.

    Two targets, like the Python sandbox: `podman` seals a container on this machine; `pod` runs in
    the task pod the harness is already in, which IS the sandbox (deny-all network, no token, read-only
    root), from a work directory under HARNESS_WORK_TMP. overlay_dir, for mutation: files at
    module-relative paths plus overlay.json naming the module. The module is copied out of the
    read-only cache, the files are laid over it, and a replace directive points the scratch module at
    the copy. Nothing else changes."""
    from . import sandbox as _py
    out_dir.mkdir(parents=True, exist_ok=True)
    overlay = json.loads((overlay_dir / "overlay.json").read_text()) if overlay_dir else None
    # The build cache is content-addressed and holds compiled dependencies; keeping it next to the
    # module cache saves recompiling the whole graph on every run. It is the one writable mount.
    gocache = env_dir / "gocache"; gocache.mkdir(exist_ok=True)
    coverpkg = ",".join(f"{c}/..." for c in cover) if cover else "."
    started = time.time()
    if _py.TARGET == "pod":
        import os
        work = Path(tempfile.mkdtemp(prefix="harness-go-pod-", dir=os.environ.get("HARNESS_WORK_TMP") or None))
        script = _script(mod=str(env_dir.resolve()), modcache=str((env_dir / "modcache").resolve()), gocache=str(gocache.resolve()),
                         tests=str(tests_dir.resolve()), out=str(out_dir.resolve()), work=str(work), coverpkg=coverpkg,
                         timeout_s=limits["timeout_s"], overlay=overlay, mutant_src=str(overlay_dir.resolve()) if overlay_dir else "", include=include)
        (out_dir / "run.sh").write_text(script)
        env = {"PATH": os.environ.get("PATH", "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin"), "HOME": str(work), "LANG": "C.UTF-8"}
        try:
            proc = subprocess.run(["bash", str(out_dir / "run.sh")], capture_output=True, text=True, timeout=limits["timeout_s"], env=env)
            rc, timed_out, stdout, stderr = proc.returncode, False, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            rc, timed_out = 124, True
            stdout, stderr = (e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")), "timeout"
        finally:
            shutil.rmtree(work, ignore_errors=True)
        pod_image = os.environ.get("HARNESS_POD_IMAGE", "the pod's own image")
        image_rec = {"image": pod_image, "image_digest": os.environ.get("HARNESS_POD_IMAGE_DIGEST") or (pod_image.split("@", 1)[1] if "@sha256:" in pod_image else None)}
        isolation = {"target": "pod", "network": "deny-all NetworkPolicy on the task pod (claim; verified by the stage 0 probe in this pod)",
                     "service_account_token": "not mounted (claim)", "rootfs": "read-only (claim)", "secrets": "none mounted; environment cleared for the run",
                     "runtime_class": os.environ.get("HARNESS_POD_RUNTIME_CLASS", "default (no Kata or gVisor)"), "limits": limits, "disposable": "the task pod",
                     "module_cache": "on the shared workspace, GOPROXY=off", "build_cache": "per environment on the shared workspace"}
    else:
        if not shutil.which("podman"):
            raise HarnessError("podman is required for the Go sandbox target")
        script = _script(mod="/mod", modcache="/modcache", gocache="/gocache", tests="/tests", out="/out", work="/work", coverpkg=coverpkg,
                         timeout_s=limits["timeout_s"], overlay=overlay, mutant_src="/mutant", include=include)
        (out_dir / "run.sh").write_text(script)
        cmd = ["podman", "run", "--rm", "--network", "none", "--cap-drop", "all", "--security-opt", "no-new-privileges",
               "--memory", limits["memory"], "--pids-limit", str(limits["pids"]), "--cpus", limits["cpus"],
               "--read-only", "--tmpfs", "/work:rw,size=2g,exec", "--tmpfs", "/tmp:rw,size=256m",
               "-v", f"{(env_dir / 'modcache').resolve()}:/modcache:ro,Z", "-v", f"{env_dir.resolve()}:/mod:ro,Z", "-v", f"{gocache.resolve()}:/gocache:rw,Z",
               "-v", f"{tests_dir.resolve()}:/tests:ro,Z", "-v", f"{out_dir.resolve()}:/out:rw,Z",
               *(["-v", f"{overlay_dir.resolve()}:/mutant:ro,Z"] if overlay_dir else []),
               "--label", f"ai-test-harness={label}", image,
               "env", "-i", "PATH=/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin", "HOME=/work", "LANG=C.UTF-8", "bash", "/out/run.sh"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=limits["timeout_s"])
            rc, timed_out, stdout, stderr = proc.returncode, False, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            rc, timed_out = 124, True
            stdout, stderr = (e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")), "timeout"
        image_rec = {"image": image, "image_digest": _py.image_digest(image)}
        isolation = {"network": "none", "capabilities": "all dropped", "no_new_privileges": True, "rootfs": "read-only",
                     "secrets": "none mounted; environment cleared with env -i", "limits": limits, "disposable": True,
                     "module_cache": "read-only mount, GOPROXY=off", "build_cache": "writable mount, content-addressed, per environment"}
    events = _events(out_dir / "test.json")
    build_log = (out_dir / "build.log").read_text(errors="replace") if (out_dir / "build.log").exists() else ""
    tests = _tests_from_events(events)
    # Go 1.24+ reports compiler errors as build-output events, not as output; both are what a reader
    # (or the model repairing the file) needs to see.
    readable = "".join(e.get("Output", "") for e in events if e.get("Action") in ("output", "build-output"))
    (out_dir / "stdout.log").write_text(readable + ("\n" + build_log if build_log.strip() else "") + stdout)
    (out_dir / "stderr.log").write_text(stderr)
    if tests:
        _write_junit(out_dir / "junit.xml", tests)
    if (out_dir / "cover.out").exists():
        write_json(out_dir / "coverage.json", _coverage_json(out_dir / "cover.out"))
    summary = {
        "label": label, **image_rec, "returncode": rc, "timed_out": timed_out,
        "duration_s": round(time.time() - started, 1), "install_failed": "cannot find module" in build_log or "missing go.sum entry" in build_log or "MODULE_NOT_IN_CACHE" in stdout,
        # A build failure is the compiler's verdict (a build-fail event); a test binary that dies at
        # package init is a runtime failure, which is the tests' verdict, and is not one.
        "build_failed": any(e.get("Action") == "build-fail" for e in events) or "[build failed]" in readable,
        "isolation": isolation,
        "junit": str(out_dir / "junit.xml") if (out_dir / "junit.xml").exists() else None,
        "coverage": str(out_dir / "coverage.json") if (out_dir / "coverage.json").exists() else None,
        "finished": now_iso(),
    }
    write_json(out_dir / "sandbox.json", {**summary, "junit": "junit.xml" if summary["junit"] else None, "coverage": "coverage.json" if summary["coverage"] else None})
    return summary


def files_blamed(readable: str, tests_dir: Path) -> list[str]:
    """GF-022. Test files the compiler names in a failed build. In Go every file in tests_dir is one
    package, so one file that does not compile fails all of them; the run drops the blamed files and
    runs the rest, and the blamed files' tests are reported as compile errors, test by test."""
    names = {p.name for p in tests_dir.glob("*_test.go")}
    blamed = []
    for m in re.finditer(r"^\./([A-Za-z0-9_.-]+_test\.go):\d+", readable, re.M):
        if m.group(1) in names and m.group(1) not in blamed:
            blamed.append(m.group(1))
    return blamed


def _events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _tests_from_events(events: list[dict]) -> dict[str, dict]:
    """test id -> {status, duration_ms, message}; subtests keep their full name (TestX/case)."""
    out: dict[str, dict] = {}
    output: dict[str, list[str]] = {}
    for e in events:
        t = e.get("Test")
        if not t:
            continue
        pkg = e.get("Package", "harnesstest")
        tid = f"{pkg}::{t}"
        act = e.get("Action")
        if act == "output":
            line = e.get("Output", "")
            if not line.lstrip().startswith(("=== RUN", "--- PASS", "--- FAIL", "--- SKIP", "=== PAUSE", "=== CONT")):
                output.setdefault(tid, []).append(line)
        elif act in ("pass", "fail", "skip"):
            status = {"pass": "pass", "fail": "fail", "skip": "skip"}[act]
            msg = "".join(output.get(tid, [])).strip()
            if status == "fail" and "panic:" in msg:
                status = "error"
            out[tid] = {"status": status, "duration_ms": int(float(e.get("Elapsed", 0)) * 1000), "message": msg[:2000]}
    return out


def _write_junit(path: Path, tests: dict[str, dict]) -> None:
    cases = []
    for tid, r in tests.items():
        cls, _, name = tid.partition("::")
        body = ""
        if r["status"] == "fail":
            body = f'<failure message="{escape(r["message"][:300], {chr(34): "&quot;"})}">{escape(r["message"])}</failure>'
        elif r["status"] == "error":
            body = f'<error message="{escape(r["message"][:300], {chr(34): "&quot;"})}">{escape(r["message"])}</error>'
        elif r["status"] == "skip":
            body = f'<skipped message="{escape(r["message"][:300], {chr(34): "&quot;"})}"/>'
        cases.append(f'<testcase classname="{escape(cls)}" name="{escape(name)}" time="{r["duration_ms"] / 1000:.3f}">{body}</testcase>')
    fails = sum(1 for r in tests.values() if r["status"] == "fail"); errs = sum(1 for r in tests.values() if r["status"] == "error")
    skips = sum(1 for r in tests.values() if r["status"] == "skip")
    path.write_text('<?xml version="1.0" encoding="utf-8"?>\n'
                    f'<testsuites><testsuite name="go test" tests="{len(tests)}" failures="{fails}" errors="{errs}" skipped="{skips}">'
                    + "".join(cases) + "</testsuite></testsuites>\n")


def _coverage_json(cover_out: Path) -> dict:
    """Go's cover profile as the coverage.json shape the pipeline reads: per file, statement counts and executed lines."""
    files: dict[str, dict] = {}
    rx = re.compile(r"^(\S+):(\d+)\.(\d+),(\d+)\.(\d+) (\d+) (\d+)$")
    for line in cover_out.read_text(errors="replace").splitlines():
        m = rx.match(line.strip())
        if not m:
            continue
        fname, l1, _, l2, _, stmts, count = m.group(1), int(m.group(2)), m.group(3), int(m.group(4)), m.group(5), int(m.group(6)), int(m.group(7))
        f = files.setdefault(fname, {"statements": 0, "covered": 0, "lines": set()})
        f["statements"] += stmts
        if count > 0:
            f["covered"] += stmts
            f["lines"].update(range(l1, l2 + 1))
    out = {"files": {}, "totals": {"covered_lines": 0, "num_statements": 0}}
    for fname, f in files.items():
        out["files"][fname] = {"summary": {"covered_lines": len(f["lines"]), "num_statements": f["statements"], "covered_statements": f["covered"]},
                               "executed_lines": sorted(f["lines"])}
        out["totals"]["covered_lines"] += len(f["lines"]); out["totals"]["num_statements"] += f["statements"]
    return out


def coverage_for(path: Path, roots: list[str]) -> dict:
    """Lines covered inside the module paths, from coverage.json."""
    if not path or not Path(path).exists():
        return {"available": False}
    data = json.loads(Path(path).read_text())
    files = {}
    for fname, fdata in data.get("files", {}).items():
        for r in roots:
            if fname == r or fname.startswith(r + "/"):
                s = fdata.get("summary", {})
                files[fname[len(r) + 1:]] = {"covered_lines": s.get("covered_lines", 0), "num_statements": s.get("num_statements", 0),
                                             "executed_lines": fdata.get("executed_lines", [])[:400]}
                break
    return {"available": True, "files": files, "covered_lines_in_target": sum(f["covered_lines"] for f in files.values()),
            "totals": data.get("totals", {})}
