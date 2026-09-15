"""The test pull request step against a local bare repository standing in for the overlay repository:
the branch is built and pushed, the default branch is untouched, the commit carries the bot identity,
and the tests, packet and records land in the overlay directory. No pull request (that needs GitHub)."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from harness.stages import propose as P

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "frc-scheduler-server" / "pr-fix-known-vulns-run6"
pytestmark = pytest.mark.skipif(not (EXAMPLE / "packet" / "summary.json").exists() or shutil.which("git") is None, reason="example run or git missing")


def _git(*args, cwd, env=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env={**os.environ, **(env or {})}).stdout


def _overlay_remote(tmp_path: Path) -> tuple[Path, Path]:
    bare = tmp_path / "overlays.git"; _git("init", "--quiet", "--bare", "--initial-branch=main", str(bare), cwd=tmp_path)
    seed = tmp_path / "seed"; _git("clone", "--quiet", str(bare), str(seed), cwd=tmp_path)
    (seed / "README.md").write_text("# overlays\n")
    ident = {"GIT_AUTHOR_NAME": "seed", "GIT_AUTHOR_EMAIL": "seed@example.invalid", "GIT_COMMITTER_NAME": "seed", "GIT_COMMITTER_EMAIL": "seed@example.invalid"}
    _git("add", "README.md", cwd=seed); _git("commit", "--quiet", "-m", "seed", cwd=seed, env=ident); _git("push", "--quiet", "origin", "main", cwd=seed)
    clone = tmp_path / "overlays"; _git("clone", "--quiet", str(bare), str(clone), cwd=tmp_path)
    return bare, clone


def test_propose_builds_and_pushes_a_harness_branch_only(tmp_path: Path):
    bare, clone = _overlay_remote(tmp_path)
    work = tmp_path / "run"; shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns("cache", "scratch"))
    main_before = _git("rev-parse", "refs/heads/main", cwd=bare).strip()
    rec = P.propose_package(work, "python-jose", clone, remote="origin", base="main", author=("AI Test Harness", "bot@example.invalid"),
                            sign=False, signing_key="", signing_format="ssh", push=True, open_pr=False)
    assert rec["status"] == "branch pushed" and rec["branch"].startswith("harness/python-jose-") and rec["pushed"] and not rec["signed"]
    assert _git("rev-parse", "refs/heads/main", cwd=bare).strip() == main_before, "the default branch must not move"
    assert rec["commit"] == _git("rev-parse", f"refs/heads/{rec['branch']}", cwd=bare).strip()
    names = _git("ls-tree", "-r", "--name-only", rec["branch"], cwd=bare).splitlines()
    assert any(n.startswith("overlays/python/python-jose/3.4.x/test_") and n.endswith(".py") for n in names)
    for f in ("packet.md", "MANIFEST.json", "statement.dsse.json", "vex.openvex.json", "udlm/test-evidence.yaml"):
        assert f"overlays/python/python-jose/3.4.x/{f}" in names, f
    assert _git("log", "-1", "--format=%an <%ae>", rec["branch"], cwd=bare).strip() == "AI Test Harness <bot@example.invalid>"
    body = (work / "propose" / "python-jose" / "pull-request.md").read_text()
    assert body.startswith("# Tests for python-jose 3.4.0") and "In plain terms" not in body and "a person decides" in body
    assert json.load(open(work / "propose" / "python-jose" / "proposal.json"))["repository"] == "overlays"


def test_propose_refuses_a_non_harness_branch_and_never_merges():
    src = Path(P.__file__).read_text()
    assert '"merge"' not in src and "pr merge" not in src, "no merge subcommand anywhere in the stage"
    assert 'f"refs/heads/{branch}:refs/heads/{branch}"' in src, "the only push is the harness branch to itself"
    assert src.count('"push"') == 1


def test_no_push_leaves_the_remote_untouched(tmp_path: Path):
    bare, clone = _overlay_remote(tmp_path)
    work = tmp_path / "run"; shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns("cache", "scratch"))
    rec = P.propose_package(work, "python-jose", clone, remote="origin", base="main", author=("AI Test Harness", "bot@example.invalid"),
                            sign=False, signing_key="", signing_format="ssh", push=False, open_pr=False)
    assert rec["status"] == "branch built" and not rec["pushed"]
    assert rec["branch"] not in _git("branch", "-r", cwd=clone)
