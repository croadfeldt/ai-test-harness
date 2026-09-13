"""Local install configuration. Blueprint principle: the repository carries the design and the
implementation; anything about a particular machine, network, or account lives in a git-ignored file
next to the code (harness.local.toml, from harness.example.toml) or in environment variables.

Records never carry an endpoint address or a local path. They carry the endpoint's label and a
digest of its address, and the target repository's name.
"""
from __future__ import annotations

import hashlib
import os
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent   # the harness/ directory
LOCAL = HERE / "harness.local.toml"
EXAMPLE = HERE / "harness.example.toml"


def load() -> dict:
    cfg = tomllib.loads(EXAMPLE.read_text()) if EXAMPLE.exists() else {}
    if LOCAL.exists():
        local = tomllib.loads(LOCAL.read_text())
        for section, values in local.items():
            cfg.setdefault(section, {}).update(values)
    return cfg


def get(section: str, key: str, env: str | None = None, default=None):
    """Environment variable first, then the local file, then the example file's default."""
    if env and os.environ.get(env) not in (None, ""):
        return os.environ[env]
    return load().get(section, {}).get(key, default)


def endpoint_digest(url: str) -> str:
    return "sha256:" + hashlib.sha256(url.rstrip("/").encode()).hexdigest()[:16]


def target_repo(explicit: str | None = None) -> Path:
    raw = explicit or get("target", "repo", "HARNESS_TARGET_REPO")
    if not raw:
        raise SystemExit("no target repository configured: pass --repo, set HARNESS_TARGET_REPO, or set [target].repo in harness/harness.local.toml")
    p = Path(raw)
    return p if p.is_absolute() else (HERE / p).resolve()
