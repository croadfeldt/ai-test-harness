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
    assert _git("log", "-1", "--format=%s", rec["branch"], cwd=bare).strip() == rec["title"] and not rec["title"].startswith("#")
    body = (work / "propose" / "python-jose" / "pull-request.md").read_text()
    assert body.startswith("# Tests for python-jose 3.4.0") and "In plain terms" not in body.split("<details>")[0] and "a person decides" in body
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


def test_first_party_tests_go_to_the_application_against_its_branch(tmp_path: Path, monkeypatch):
    """First-party: the request targets the repository under test and the change's own branch; no records are copied into it."""
    from harness.stages import propose as P
    from harness import config
    app = tmp_path / "app"; app.mkdir()
    _git("init", "-q", "-b", "main", cwd=app); _git("config", "user.email", "t@x", cwd=app); _git("config", "user.name", "t", cwd=app)
    (app / "README.md").write_text("app\n"); _git("add", ".", cwd=app); _git("commit", "-q", "-m", "init", cwd=app)
    _git("checkout", "-q", "-b", "feature/x", cwd=app); (app / "app.py").write_text("x = 1\n"); _git("add", ".", cwd=app); _git("commit", "-q", "-m", "change", cwd=app)
    bare = tmp_path / "app.git"; subprocess.run(["git", "clone", "-q", "--bare", str(app), str(bare)], check=True)
    _git("remote", "add", "origin", str(bare), cwd=app); _git("fetch", "-q", "origin", cwd=app)
    work = tmp_path / "run"
    for d in ("intake", "analyze/my-app", "packet/my-app", "attest/my-app", "execute/my-app", "selfcheck"):
        (work / d).mkdir(parents=True)
    (work / "run.json").write_text(json.dumps({"args": {"head": "feature/x", "base": "main"}}))
    (work / "intake" / "worklist.json").write_text(json.dumps({"run_id": "r1", "repository": "my-app", "source_dir": "app", "ecosystem": "python", "items": []}))
    (work / "analyze" / "my-app" / "facts.json").write_text(json.dumps({"first_party": True, "old_version": None, "new_version": "abc", "purl": "pkg:generic/my-app", "call_sites_summary": {"reachable": "true"}}))
    patch = "--- /dev/null\n+++ b/tests/test_app.py\n@@ -0,0 +1,2 @@\n+def test_x():\n+    assert 1 == 1\n"
    (work / "packet" / "my-app" / "tests.patch").write_text(patch)
    (work / "packet" / "my-app" / "packet.md").write_text("# Review packet\n\n**In plain terms.** Fine.\n")
    (work / "packet" / "my-app" / "vex.openvex.json").write_text("{}")
    (work / "packet" / "my-app" / "packet.json").write_text(json.dumps({"package": "my-app", "packet_md": "packet/my-app/packet.md", "patch": "packet/my-app/tests.patch", "vex": "packet/my-app/vex.openvex.json", "tests_in_patch": ["test_x"], "run_id": "r1"}))
    (work / "packet" / "summary.json").write_text(json.dumps({"packages": [{"package": "my-app", "tests_in_patch": ["test_x"], "packet_md": "packet/my-app/packet.md", "patch": "packet/my-app/tests.patch", "vex": "packet/my-app/vex.openvex.json"}]}))
    (work / "attest" / "summary.json").write_text(json.dumps({"packages": []}))
    (work / "README.md").write_text("# Run r1\n\nthe story\n")
    monkeypatch.setattr(config, "resolve_repo", lambda name, explicit, workdir: app)
    monkeypatch.setattr(P.selfcheck if hasattr(P, "selfcheck") else __import__("harness.selfcheck", fromlist=["x"]), "require", lambda *a, **k: None)
    outs = P.propose(workdir=work, push=True, open_pr=False)
    rec = outs[0]
    assert rec["status"] == "branch pushed" and rec["base_branch"] == "feature/x"
    assert rec["files"] == ["tests/test_app.py"], "tests only; no packet or records in the application's tree"
    assert "the story" in (work / "propose" / "my-app" / "pull-request.md").read_text()
    remote_refs = _git("ls-remote", "--heads", str(bare), cwd=app)
    assert "refs/heads/harness/my-app-r1" in remote_refs and "refs/heads/main" in remote_refs
