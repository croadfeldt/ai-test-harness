"""The runs store: the one place every run's index, story, evaluation row and pipeline findings land, so
the dashboard and the roll-ups read every run the harness ever made, wherever it ran. A directory or a
git repository; `harness publish` copies four small files per run and, for a repository, commits and
pushes them. The store is the harness's own ledger, not a code repository: nothing under review lives
there, and no evidence file is rewritten, only added.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import config
from ..util import HarnessError, log, now_iso, read_json, write_json
from .evaluate import rows_for

FILES = ("run-index.json", "README.md", "triage/pipeline.json")


def store_target(explicit: str | None = None) -> str:
    raw = explicit or config.get("publish", "store", "HARNESS_RUNS_STORE")
    if not raw:
        raise HarnessError("no runs store configured: pass --to <directory or git URL>, set HARNESS_RUNS_STORE, or [publish].store in harness.local.toml")
    return str(raw)


def _is_url(raw: str) -> bool:
    return config.is_url(raw)


def publish_into(workdir: Path, store: Path) -> Path:
    """Copy the run's files into <store>/runs/<repository>/<run_id>/ and refresh the store's index."""
    idx = read_json(workdir / "run-index.json")
    repo = (idx.get("repository") or "unknown").replace("/", "_")
    run_id = idx.get("run_id") or workdir.name
    dest = store / "runs" / repo / run_id
    dest.mkdir(parents=True, exist_ok=True)
    for rel in FILES:
        src = workdir / rel
        if src.exists():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dest / rel)
    write_json(dest / "evaluation.json", {"rows": rows_for(workdir), "published": now_iso()})
    entries = []
    for e in sorted(store.glob("runs/*/*/run-index.json")):
        i = read_json(e)
        entries.append({"path": str(e.parent.relative_to(store)), "run_id": i.get("run_id"), "repository": i.get("repository"),
                        "ecosystem": i.get("ecosystem"), "started": i.get("started"), "model": i.get("model")})
    write_json(store / "index.json", {"format": "ai-test-harness/runs-store/v1", "updated": now_iso(), "runs": entries})
    return dest


def publish(*, workdir: Path, to: str | None = None, push: bool = True) -> dict:
    target = store_target(to)
    if not _is_url(target):
        dest = publish_into(workdir, Path(target).expanduser().resolve())
        log(f"  publish: {dest}")
        return {"store": target, "path": str(dest), "pushed": False}
    tmp = Path(tempfile.mkdtemp(prefix="harness-runs-store-"))
    try:
        env = {**os.environ}
        subprocess.run(["git", "clone", "--quiet", "--depth", "1", target, str(tmp)], check=True, capture_output=True, text=True, timeout=600, env=env)
        dest = publish_into(workdir, tmp)
        rel = str(dest.relative_to(tmp))
        author = (str(config.get("propose", "author_name", "HARNESS_PROPOSE_AUTHOR", "AI Test Harness")),
                  str(config.get("propose", "author_email", "HARNESS_PROPOSE_EMAIL", "ai-test-harness@example.invalid")))
        env.update({"GIT_AUTHOR_NAME": author[0], "GIT_AUTHOR_EMAIL": author[1], "GIT_COMMITTER_NAME": author[0], "GIT_COMMITTER_EMAIL": author[1]})
        subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True, capture_output=True, timeout=60)
        proc = subprocess.run(["git", "-C", str(tmp), "commit", "--quiet", "-m", f"run {read_json(workdir / 'run-index.json').get('run_id')}: {rel}"],
                              capture_output=True, text=True, timeout=60, env=env)
        if proc.returncode != 0 and "nothing to commit" not in proc.stdout + proc.stderr:
            raise HarnessError(f"runs store commit failed: {proc.stderr.strip()[-300:]}")
        if push and proc.returncode == 0:
            proc = subprocess.run(["git", "-C", str(tmp), "push", "--quiet"], capture_output=True, text=True, timeout=600, env=env)
            if proc.returncode != 0:
                raise HarnessError(f"runs store push failed: {proc.stderr.strip()[-300:]}")
        log(f"  publish: {rel} in {target}" + (" (pushed)" if push else ""))
        return {"store": target, "path": rel, "pushed": bool(push and proc.returncode == 0)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
