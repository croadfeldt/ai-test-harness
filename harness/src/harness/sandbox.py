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

IMAGE = "docker.io/library/python:3.12-slim"
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
    image = f"docker.io/library/python:{python_version}-slim"
    cmd = ["podman", "run", "--rm", "-v", f"{dest.resolve()}:/wh:rw,Z", image, "sh", "-c",
           "pip download --quiet --only-binary=:all: --dest /wh -r /wh/requirements.txt"]
    proc = run(cmd, check=False, timeout=1800)
    if proc.returncode != 0:
        raise HarnessError(f"wheelhouse prefetch failed: {proc.stderr.strip()[-800:]}")
    marker.write_text(now_iso())
    return dest


def run_tests(*, wheelhouse: Path, requirements: list[str], tests_dir: Path, out_dir: Path,
              cover: list[str], label: str, image: str = IMAGE, limits: dict = LIMITS) -> dict:
    """Install from the wheelhouse offline, run pytest with coverage, return a summary.

    Writes junit.xml, coverage.json, stdout.log, stderr.log into out_dir.
    """
    if not shutil.which("podman"):
        raise HarnessError("podman is required for the sandbox target")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "requirements.txt").write_text("\n".join(requirements + RUNNER_DEPS) + "\n")
    script = f"""set -u
python -m venv /work/venv >/dev/null
/work/venv/bin/pip install --quiet --no-index --find-links /wheelhouse -r /out/requirements.txt || {{ echo "INSTALL_FAILED"; exit 97; }}
cd /work
cp -r /tests /work/tests
/work/venv/bin/python -m coverage run --branch --source={",".join(cover) or "."} -m pytest -q -p no:cacheprovider \\
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
        "label": label, "image": image, "returncode": rc, "timed_out": timed_out,
        "duration_s": round(time.time() - started, 1), "install_failed": "INSTALL_FAILED" in stdout,
        "isolation": {"network": "none", "capabilities": "all dropped", "no_new_privileges": True, "rootfs": "read-only",
                      "secrets": "none mounted; environment cleared with env -i", "limits": limits, "disposable": True},
        "junit": str(out_dir / "junit.xml") if (out_dir / "junit.xml").exists() else None,
        "coverage": str(out_dir / "coverage.json") if (out_dir / "coverage.json").exists() else None,
        "finished": now_iso(),
    }
    write_json(out_dir / "sandbox.json", summary)
    return summary


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
