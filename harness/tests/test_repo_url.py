"""A repository by URL: cloned under the run, any ref resolvable by name, including pull request refs."""
import subprocess
from pathlib import Path

from harness import config
from harness.stages.intake import _resolve_ref, repository_name


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def test_url_target_is_cloned_once_and_pull_request_refs_resolve(tmp_path):
    src = tmp_path / "upstream"; src.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(src)], check=True)
    _git(src, "config", "user.email", "t@example.invalid"); _git(src, "config", "user.name", "t")
    (src / "requirements.txt").write_text("requests==2.31.0\n"); _git(src, "add", "."); _git(src, "commit", "-q", "-m", "base")
    base = _git(src, "rev-parse", "HEAD")
    (src / "requirements.txt").write_text("requests==2.32.0\n"); _git(src, "commit", "-q", "-am", "bump")
    head = _git(src, "rev-parse", "HEAD")
    _git(src, "update-ref", "refs/pull/7/head", head)      # what GitHub serves for a pull request
    _git(src, "reset", "-q", "--hard", base)                 # main stays at base; the change lives only on the PR ref
    bare = tmp_path / "my-app.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(src), str(bare)], check=True)
    _git(bare, "update-ref", "refs/pull/7/head", head)
    url = f"file://{bare}"
    work = tmp_path / "run"
    assert config.is_url(url) and not config.is_url("/tmp/x") and config.is_url("git@github.com:o/r.git")
    repo = config.target_repo(url, work)
    assert repo == work / "cache" / "repo" / "my-app" and (repo / ".git").is_dir() and config.owned_clone(repo, work)
    assert repository_name(repo) == "my-app"
    assert _resolve_ref(repo, "refs/pull/7/head") == head and _resolve_ref(repo, "main") == base and _resolve_ref(repo, head[:10]) == head
    assert config.target_repo(url, work) == repo, "a second call fetches; it does not clone again"
    assert config.resolve_repo("my-app", None, work) == repo, "later stages find the clone intake made"


def test_later_stages_find_the_clone_through_a_shared_cache(tmp_path):
    """The bench shares one cache between sibling work directories by symlink; the clone lives in it."""
    base = tmp_path / "base"; (base / "cache" / "repo" / "my-app" / ".git").mkdir(parents=True)
    sibling = tmp_path / "sibling"; sibling.mkdir(); (sibling / "cache").symlink_to(base / "cache")
    assert config.resolve_repo("my-app", None, sibling) == sibling / "cache" / "repo" / "my-app"
