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


def run_tests(*, env_dir: Path, tests_dir: Path, out_dir: Path, cover: list[str], label: str,
              image: str = IMAGE, limits: dict = LIMITS, overlay_dir: Path | None = None) -> dict:
    """Run every *_test.go in tests_dir as package harnesstest against the prefetched module cache.

    overlay_dir, for mutation: files at module-relative paths plus overlay.json naming the module. The
    module is copied out of the read-only cache into the work directory, the files are laid over it,
    and a replace directive points the scratch module at the copy. Nothing else changes."""
    if not shutil.which("podman"):
        raise HarnessError("podman is required for the Go sandbox target")
    out_dir.mkdir(parents=True, exist_ok=True)
    overlay = ""
    if overlay_dir:
        meta = json.loads((overlay_dir / "overlay.json").read_text())
        overlay = f"""
src=$(go list -m -f '{{{{.Dir}}}}' {meta["module"]}) || {{ echo "MODULE_NOT_IN_CACHE"; exit 96; }}
mkdir -p /work/mutant && cp -r "$src"/. /work/mutant/ && chmod -R u+w /work/mutant
(cd /mutant && find . -type f ! -name overlay.json | while read f; do cp "$f" "/work/mutant/$f"; done)
go mod edit -replace {meta["module"]}=/work/mutant
"""
    # The build cache is content-addressed and holds compiled dependencies; keeping it next to the
    # module cache saves recompiling the whole graph on every run. It is the one writable mount.
    gocache = env_dir / "gocache"; gocache.mkdir(exist_ok=True)
    coverpkg = ",".join(f"{c}/..." for c in cover) if cover else "."
    script = f"""set -u
mkdir -p /work/m && cp /mod/go.mod /mod/go.sum /work/m/ && cp /tests/*.go /work/m/
cd /work/m
export GOMODCACHE=/modcache GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=/gocache GOPATH=/work/gopath HOME=/work{overlay}
go vet . > /out/vet.log 2>&1 || true
go test -json -count=1 -timeout {max(60, limits["timeout_s"] - 60)}s -coverprofile=/out/cover.out -coverpkg={coverpkg} . > /out/test.json 2> /out/build.log ; rc=$?
exit $rc
"""
    (out_dir / "run.sh").write_text(script)
    cmd = ["podman", "run", "--rm", "--network", "none", "--cap-drop", "all", "--security-opt", "no-new-privileges",
           "--memory", limits["memory"], "--pids-limit", str(limits["pids"]), "--cpus", limits["cpus"],
           "--read-only", "--tmpfs", "/work:rw,size=2g,exec", "--tmpfs", "/tmp:rw,size=256m",
           "-v", f"{(env_dir / 'modcache').resolve()}:/modcache:ro,Z", "-v", f"{env_dir.resolve()}:/mod:ro,Z", "-v", f"{gocache.resolve()}:/gocache:rw,Z",
           "-v", f"{tests_dir.resolve()}:/tests:ro,Z", "-v", f"{out_dir.resolve()}:/out:rw,Z",
           *(["-v", f"{overlay_dir.resolve()}:/mutant:ro,Z"] if overlay_dir else []),
           "--label", f"ai-test-harness={label}", image,
           "env", "-i", "PATH=/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin", "HOME=/work", "LANG=C.UTF-8", "bash", "/out/run.sh"]
    started = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=limits["timeout_s"])
        rc, timed_out, stdout, stderr = proc.returncode, False, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        rc, timed_out = 124, True
        stdout, stderr = (e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")), "timeout"
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
    from . import sandbox as _py
    summary = {
        "label": label, "image": image, "image_digest": _py.image_digest(image), "returncode": rc, "timed_out": timed_out,
        "duration_s": round(time.time() - started, 1), "install_failed": "cannot find module" in build_log or "missing go.sum entry" in build_log,
        # A build failure is the compiler's verdict (a build-fail event); a test binary that dies at
        # package init is a runtime failure, which is the tests' verdict, and is not one.
        "build_failed": any(e.get("Action") == "build-fail" for e in events) or "[build failed]" in readable,
        "isolation": {"network": "none", "capabilities": "all dropped", "no_new_privileges": True, "rootfs": "read-only",
                      "secrets": "none mounted; environment cleared with env -i", "limits": limits, "disposable": True,
                      "module_cache": "read-only mount, GOPROXY=off", "build_cache": "writable mount, content-addressed, per environment"},
        "junit": str(out_dir / "junit.xml") if (out_dir / "junit.xml").exists() else None,
        "coverage": str(out_dir / "coverage.json") if (out_dir / "coverage.json").exists() else None,
        "finished": now_iso(),
    }
    write_json(out_dir / "sandbox.json", {**summary, "junit": "junit.xml" if summary["junit"] else None, "coverage": "coverage.json" if summary["coverage"] else None})
    return summary


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
