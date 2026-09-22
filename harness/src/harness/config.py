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


def is_url(raw: str) -> bool:
    """A repository given by address rather than by path: https://, ssh://, git://, file://, or scp-style user@host:path."""
    import re
    return bool(re.match(r"^(https?|ssh|git|file)://", raw)) or bool(re.match(r"^[\w.-]+@[\w.-]+:", raw))


def repo_name_from_url(url: str) -> str:
    tail = url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    return tail[:-4] if tail.endswith(".git") else tail


def clone_dir(url: str, workdir: Path) -> Path:
    return workdir / "cache" / "repo" / repo_name_from_url(url)


def checkout(url: str, workdir: Path) -> Path:
    """The repository at `url`, cloned once under the run's cache and fetched on every later call, so a
    run can name a repository by address and any ref on it: a branch, a tag, a commit, a pull request."""
    import subprocess
    dest = clone_dir(url, workdir)
    if (dest / ".git").is_dir():
        have = subprocess.run(["git", "-C", str(dest), "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
        if have != url:
            raise SystemExit(f"{dest} is a clone of {have}, not of {url}; remove it or use another work directory")
        subprocess.run(["git", "-C", str(dest), "fetch", "--quiet", "--prune", "origin"], check=True, timeout=600)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["git", "clone", "--quiet", url, str(dest)], capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        raise SystemExit(f"clone of {url} failed: {proc.stderr.strip()[-400:]}")
    return dest


def target_repo(explicit: str | None = None, workdir: Path | None = None) -> Path:
    raw = explicit or get("target", "repo", "HARNESS_TARGET_REPO")
    if not raw:
        raise SystemExit("no target repository configured: pass --repo <path or URL>, set HARNESS_TARGET_REPO, or set [target].repo in harness/harness.local.toml")
    if is_url(raw):
        if workdir is None:
            raise SystemExit("a repository by URL needs a work directory to clone into")
        return checkout(raw, workdir)
    p = Path(raw)
    return p if p.is_absolute() else (HERE / p).resolve()


def owned_clone(repo: Path, workdir: Path | None) -> bool:
    """True when the harness made this checkout itself and may move it to any commit."""
    return bool(workdir) and repo.resolve().is_relative_to((workdir / "cache" / "repo").resolve())


def resolve_repo(work_list_repo_name: str, explicit: str | None = None, workdir: Path | None = None) -> Path:
    """The repository a later stage should read, checked against the work list it is continuing.
    A stage that silently read a different repository than intake did would produce facts about the
    wrong code; that happened once (call sites scanned in the wrong checkout), so it refuses now."""
    if explicit is None and workdir is not None and (workdir / "cache" / "repo" / work_list_repo_name / ".git").is_dir():
        return workdir / "cache" / "repo" / work_list_repo_name   # the clone intake made for this run
    p = target_repo(explicit, workdir)
    if p.name != work_list_repo_name:
        raise SystemExit(f"this work directory is for repository '{work_list_repo_name}' but the configured repository is "
                         f"'{p.name}'; pass --repo <path or URL of {work_list_repo_name}> or set HARNESS_TARGET_REPO")
    return p
