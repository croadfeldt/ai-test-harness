"""One job, several prompt sets: the controlled comparison behind the evaluation table.

Takes a run that has finished intake and analysis, and for each prompt set copies those results into a
sibling work directory, runs generation, execution, mutation and triage there with that set active, then
evaluates every directory together. One variable changes per run: the words. The model is whatever the
configuration points at, so a model comparison is the same command with a different endpoint.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from ..util import HarnessError, log
from .evaluate import evaluate

COPIED = ("run.json", "selfcheck", "intake", "analyze")


def prepare(base: Path, prompt_set: str) -> Path:
    """The sibling work directory for one prompt set: intake and analysis copied, the cache shared."""
    if not (base / "analyze").is_dir():
        raise HarnessError(f"{base} has no analysis to build on; run intake and analyze first")
    dest = base.parent / f"{base.name}-bench-{prompt_set.replace('/', '_')}"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name in COPIED:
        src = base / name
        if src.is_dir():
            shutil.copytree(src, dest / name)
        elif src.is_file():
            shutil.copy(src, dest / name)
    if (base / "cache").exists() and not (dest / "cache").exists():
        os.symlink((base / "cache").resolve(), dest / "cache")
    return dest


def bench(*, base: Path, prompt_sets: list[str], select: list[str] | None, categories: list[str] | None, mode: str,
          python_version: str | None = None, stages: tuple[str, ...] = ("generate", "execute", "mutate", "triage")) -> Path:
    harness = [sys.executable, "-m", "harness.cli"]
    dirs = []
    for ps in prompt_sets:
        dest = prepare(base, ps)
        log(f"bench: prompt set {ps} in {dest}")
        env = {**os.environ, "HARNESS_PROMPT_SET": ps}
        for stage in stages:
            args = [*harness, stage, "--workdir", str(dest)]
            if stage in ("generate", "execute", "mutate") and select:
                args += ["--select", *select]
            if stage == "generate":
                args += ["--mode", mode] + (["--categories", *categories] if categories else [])
            if stage in ("generate", "execute") and python_version:
                args += ["--python-version", python_version]
            proc = subprocess.run(args, env=env)
            if proc.returncode != 0:
                raise HarnessError(f"bench: {stage} failed for prompt set {ps} (see {dest})")
        dirs.append(dest)
    out = base.parent / f"{base.name}-bench"
    evaluate(dirs, out)
    log(f"bench: evaluation at {out / 'evaluation.md'}")
    return out
