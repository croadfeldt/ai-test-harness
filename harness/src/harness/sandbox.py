"""Sealed execution: run generated tests in a disposable container with no network and no secrets.

Blueprint stage 4 and section 11. This is the Podman target from docs/09 (class podman). The
Kubernetes target (a Tekton task with a Kata or gVisor RuntimeClass) reuses the same plan.

The only thing that ever touches the network is the wheelhouse prefetch, which runs before the
sandbox exists and executes no package code. Inside the sandbox: --network none, all capabilities
dropped, no new privileges, read-only mounts for inputs, memory, pid, and time limits, and the
container is removed when the run ends.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .util import HarnessError, log, now_iso, run, sha256_file, write_json

from . import config as _config
IMAGE = str(_config.get("sandbox", "image", "HARNESS_SANDBOX_IMAGE", "docker.io/library/python:3.12-slim"))
LIMITS = {"memory": "2g", "pids": 512, "timeout_s": 900, "cpus": "2"}
RUNNER_DEPS = ["pytest", "coverage"]


def prefetch_wheelhouse(requirements: list[str], python_version: str, dest: Path, extra: list[str] = RUNNER_DEPS) -> Path:
    """Download every wheel the sandbox will need, for the sandbox interpreter. No code executed."""
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".complete"
    if marker.exists():
        return dest
    (dest / "requirements.txt").write_text("\n".join(requirements + extra) + "\n")
    # Download inside the sandbox image itself so wheel tags and markers match exactly what will run.
    # In pod mode the harness image IS that interpreter, so download in place.
    image = f"docker.io/library/python:{python_version}-slim"
    if TARGET == "pod":
        cmd = [sys.executable, "-m", "pip", "download", "--quiet", "--only-binary=:all:", "--dest", str(dest.resolve()), "-r", str(dest / "requirements.txt")]
    else:
        cmd = ["podman", "run", "--rm", "-v", f"{dest.resolve()}:/wh:rw,Z", image, "sh", "-c",
               "pip download --quiet --only-binary=:all: --dest /wh -r /wh/requirements.txt"]
    proc = run(cmd, check=False, timeout=1800)
    if proc.returncode != 0:
        raise HarnessError(f"wheelhouse prefetch failed: {proc.stderr.strip()[-800:]}")
    marker.write_text(now_iso())
    return dest


TARGET = str(_config.get("sandbox", "target", "HARNESS_SANDBOX_TARGET", "podman"))   # podman | pod


def run_tests(*, wheelhouse: Path, requirements: list[str], tests_dir: Path, out_dir: Path,
              cover: list[str], label: str, image: str = IMAGE, limits: dict = LIMITS,
              overlay_dir: Path | None = None) -> dict:
    """Install from the wheelhouse offline, run pytest with coverage, return a summary.

    Writes junit.xml, coverage.json, stdout.log, stderr.log into out_dir. Two targets: `podman`
    starts a sealed container on this machine; `pod` runs in-process because the pod the harness is
    already running in IS the sandbox (a Tekton task pod with a deny-all NetworkPolicy, no
    service-account token, read-only root). In pod mode the isolation is the pod spec's claim, and
    stage 0's probe verifies it from inside before any generated code runs.
    """
    if TARGET == "pod":
        return _run_in_pod(wheelhouse=wheelhouse, requirements=requirements, tests_dir=tests_dir, out_dir=out_dir,
                           cover=cover, label=label, limits=limits, overlay_dir=overlay_dir)
    if not shutil.which("podman"):
        raise HarnessError("podman is required for the sandbox target")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "requirements.txt").write_text("\n".join(requirements + RUNNER_DEPS) + "\n")
    script = f"""set -u
python -m venv /work/venv >/dev/null
/work/venv/bin/pip install --quiet --no-index --find-links /wheelhouse -r /out/requirements.txt || {{ echo "INSTALL_FAILED"; exit 97; }}
cd /work
cp -r /tests /work/tests
if [ -d /mutant ]; then cp -r /mutant/. /work/venv/lib/python3.12/site-packages/; fi
/work/venv/bin/python -m coverage run --branch --source={",".join(cover) or "."} -m pytest -q -p no:cacheprovider --continue-on-collection-errors \\
    --junitxml=/out/junit.xml -o junit_family=xunit2 /work/tests ; rc=$?
/work/venv/bin/python -m coverage json -o /out/coverage.json >/dev/null 2>&1 || true
exit $rc
"""
    (out_dir / "run.sh").write_text(script)
    cmd = ["podman", "run", "--rm", "--network", "none", "--cap-drop", "all", "--security-opt", "no-new-privileges",
           "--memory", limits["memory"], "--pids-limit", str(limits["pids"]), "--cpus", limits["cpus"],
           "--read-only", "--tmpfs", "/work:rw,size=1g", "--tmpfs", "/tmp:rw,size=256m",
           "-v", f"{wheelhouse.resolve()}:/wheelhouse:ro,Z", "-v", f"{tests_dir.resolve()}:/tests:ro,Z",
           "-v", f"{out_dir.resolve()}:/out:rw,Z",
           *(["-v", f"{overlay_dir.resolve()}:/mutant:ro,Z"] if overlay_dir else []),
           "--label", f"ai-test-harness={label}", image,
           # env -i: the sandbox inherits nothing from the image or the host, only what is listed here.
           "env", "-i", "PATH=/usr/local/bin:/usr/bin:/bin", "HOME=/work", "LANG=C.UTF-8",
           "PIP_NO_CACHE_DIR=1", "PYTHONDONTWRITEBYTECODE=1", "bash", "/out/run.sh"]
    started = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=limits["timeout_s"])
        rc, timed_out = proc.returncode, False
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        rc, timed_out = 124, True
        stdout, stderr = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), "timeout"
    (out_dir / "stdout.log").write_text(stdout)
    (out_dir / "stderr.log").write_text(stderr)
    summary = {
        "label": label, "image": image, "image_digest": image_digest(image), "returncode": rc, "timed_out": timed_out,
        "duration_s": round(time.time() - started, 1), "install_failed": "INSTALL_FAILED" in stdout,
        "isolation": {"network": "none", "capabilities": "all dropped", "no_new_privileges": True, "rootfs": "read-only",
                      "secrets": "none mounted; environment cleared with env -i", "limits": limits, "disposable": True},
        "junit": str(out_dir / "junit.xml") if (out_dir / "junit.xml").exists() else None,
        "coverage": str(out_dir / "coverage.json") if (out_dir / "coverage.json").exists() else None,
        "finished": now_iso(),
    }
    write_json(out_dir / "sandbox.json", summary)
    return summary


def _run_in_pod(*, wheelhouse: Path, requirements: list[str], tests_dir: Path, out_dir: Path,
                cover: list[str], label: str, limits: dict, overlay_dir: Path | None) -> dict:
    """The pod target: same run script, executed here, in a fresh venv under a temp work directory."""
    import os
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "requirements.txt").write_text("\n".join(requirements + RUNNER_DEPS) + "\n")
    work = Path(tempfile.mkdtemp(prefix="harness-pod-", dir=os.environ.get("HARNESS_WORK_TMP") or None))
    script = f"""set -u
python -m venv {work}/venv >/dev/null
{work}/venv/bin/pip install --quiet --no-index --find-links {wheelhouse.resolve()} -r {out_dir.resolve()}/requirements.txt || {{ echo "INSTALL_FAILED"; exit 97; }}
cd {work}
cp -r {tests_dir.resolve()} {work}/tests
if [ -d "{overlay_dir.resolve() if overlay_dir else '/nonexistent'}" ]; then cp -r {overlay_dir.resolve() if overlay_dir else '/nonexistent'}/. {work}/venv/lib/python3.12/site-packages/; fi
{work}/venv/bin/python -m coverage run --branch --source={",".join(cover) or "."} -m pytest -q -p no:cacheprovider --continue-on-collection-errors \\
    --junitxml={out_dir.resolve()}/junit.xml -o junit_family=xunit2 {work}/tests ; rc=$?
{work}/venv/bin/python -m coverage json -o {out_dir.resolve()}/coverage.json >/dev/null 2>&1 || true
exit $rc
"""
    (out_dir / "run.sh").write_text(script)
    started = time.time()
    env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": str(work), "LANG": "C.UTF-8",
           "PIP_NO_CACHE_DIR": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        proc = subprocess.run(["bash", str(out_dir / "run.sh")], capture_output=True, text=True, timeout=limits["timeout_s"], env=env)
        rc, timed_out, stdout, stderr = proc.returncode, False, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        rc, timed_out = 124, True
        stdout, stderr = (e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")), "timeout"
    finally:
        shutil.rmtree(work, ignore_errors=True)
    (out_dir / "stdout.log").write_text(stdout); (out_dir / "stderr.log").write_text(stderr)
    pod_image = os.environ.get("HARNESS_POD_IMAGE", "the pod's own image")
    # The pipeline references the image by digest, so the reference itself pins the bytes.
    pod_digest = os.environ.get("HARNESS_POD_IMAGE_DIGEST") or (pod_image.split("@", 1)[1] if "@sha256:" in pod_image else None)
    summary = {"label": label, "image": pod_image, "image_digest": pod_digest,
               "returncode": rc, "timed_out": timed_out, "duration_s": round(time.time() - started, 1), "install_failed": "INSTALL_FAILED" in stdout,
               "isolation": {"target": "pod", "network": "deny-all NetworkPolicy on the task pod (claim; verified by the stage 0 probe in this pod)",
                             "service_account_token": "not mounted (claim)", "rootfs": "read-only (claim)", "secrets": "none mounted; environment cleared for the run",
                             "runtime_class": os.environ.get("HARNESS_POD_RUNTIME_CLASS", "default (no Kata or gVisor)"), "limits": limits, "disposable": "the task pod"},
               "junit": str(out_dir / "junit.xml") if (out_dir / "junit.xml").exists() else None,
               "coverage": str(out_dir / "coverage.json") if (out_dir / "coverage.json").exists() else None, "finished": now_iso()}
    write_json(out_dir / "sandbox.json", summary)
    return summary


_DIGESTS: dict[str, str | None] = {}


def image_digest(image: str) -> str | None:
    """The sha256 digest of the local image, so a provenance claim pins bytes, not a tag."""
    if image not in _DIGESTS:
        proc = subprocess.run(["podman", "image", "inspect", image, "--format", "{{.Digest}}"], capture_output=True, text=True)
        d = proc.stdout.strip()
        _DIGESTS[image] = d if proc.returncode == 0 and d.startswith("sha256:") else None
    return _DIGESTS[image]


def parse_junit(path: Path) -> dict[str, dict]:
    """test id -> {status, duration_ms, message}. Status: pass | fail | error | skip."""
    import xml.etree.ElementTree as ET
    out: dict[str, dict] = {}
    if not path or not Path(path).exists():
        return out
    root = ET.parse(path).getroot()
    for tc in root.iter("testcase"):
        tid = f"{tc.get('classname', '')}::{tc.get('name', '')}"
        status, msg = "pass", ""
        for child in tc:
            if child.tag in ("failure", "error", "skipped"):
                status = {"failure": "fail", "error": "error", "skipped": "skip"}[child.tag]
                msg = (child.get("message") or (child.text or "")).strip()[:2000]
        out[tid] = {"status": status, "duration_ms": int(float(tc.get("time", "0")) * 1000), "message": msg}
    return out


def coverage_for(path: Path, roots: list[str]) -> dict:
    """Lines and branches covered inside the package roots, from coverage.json."""
    if not path or not Path(path).exists():
        return {"available": False}
    data = json.loads(Path(path).read_text())
    files = {}
    for fname, fdata in data.get("files", {}).items():
        if any(f"/{r}/" in fname or fname.endswith(f"/{r}.py") for r in roots):
            s = fdata.get("summary", {})
            files[fname.split("site-packages/")[-1]] = {"covered_lines": s.get("covered_lines", 0),
                                                        "num_statements": s.get("num_statements", 0),
                                                        "executed_lines": fdata.get("executed_lines", [])[:400]}
    covered = sum(f["covered_lines"] for f in files.values())
    return {"available": True, "files": files, "covered_lines_in_target": covered,
            "totals": data.get("totals", {})}
