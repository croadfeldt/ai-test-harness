"""Small shared helpers: subprocess, JSON files, HTTP, hashing, time."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HarnessError(RuntimeError):
    """A stage could not complete. The message is meant for the operator."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def to_jsonable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def write_json(path: Path, obj: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(obj), indent=2, sort_keys=True) + "\n")
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 600, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise HarnessError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr[-4000:]}")
    return proc


def tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def tool_version(cmd: list[str]) -> str | None:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (proc.stdout or proc.stderr).strip().splitlines()[0] if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return None


def http_json(url: str, body: Any | None = None, timeout: int = 30) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json",
                                                          "User-Agent": "ai-test-harness/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise HarnessError(f"HTTP {e.code} from {url}") from e
    except urllib.error.URLError as e:
        raise HarnessError(f"cannot reach {url}: {e.reason}") from e


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
