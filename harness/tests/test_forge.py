"""The forges: GitHub and GitLab by CLI or API, requests opened for a pushed branch, decisions read back."""
import io
import json

import pytest

from harness.sources import forge
from harness.util import HarnessError


def test_detect_hosts_and_paths():
    assert forge.detect("https://github.com/o/r.git") == {"host": "github.com", "kind": "github", "path": "o/r", "api": "https://api.github.com"}
    assert forge.detect("git@github.com:o/r.git")["path"] == "o/r"
    g = forge.detect("ssh://git@gitlab.example.com/group/sub/r.git")
    assert g["kind"] == "gitlab" and g["path"] == "group/sub/r" and g["api"] == "https://gitlab.example.com/api/v4"
    assert forge.detect("https://bitbucket.org/o/r")["kind"] == "unknown"


class Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_open_pr_by_api_when_no_cli(monkeypatch):
    monkeypatch.setattr(forge.shutil, "which", lambda name: None)
    monkeypatch.setenv("GH_TOKEN", "t"); monkeypatch.setenv("GITLAB_TOKEN", "u")
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append((req.get_method(), req.full_url, json.loads(req.data.decode()), dict(req.header_items())))
        if "api.github.com" in req.full_url:
            return Resp(json.dumps({"html_url": "https://github.com/o/r/pull/7", "number": 7}).encode())
        return Resp(json.dumps({"web_url": "https://gitlab.example.com/g/r/-/merge_requests/3", "iid": 3}).encode())

    monkeypatch.setattr(forge.urllib.request, "urlopen", fake_urlopen)
    pr = forge.open_pr("https://github.com/o/r.git", "harness/x-1", "main", "T", "B", ".")
    assert pr == {"url": "https://github.com/o/r/pull/7", "number": 7, "via": "api"}
    m, url, body, headers = calls[0]
    assert m == "POST" and url.endswith("/repos/o/r/pulls") and body == {"title": "T", "head": "harness/x-1", "base": "main", "body": "B"} and headers["Authorization"] == "Bearer t"
    mr = forge.open_pr("git@gitlab.example.com:g/r.git", "harness/x-1", "main", "T", "B", ".")
    assert mr["url"].endswith("/merge_requests/3") and mr["number"] == 3
    m, url, body, headers = calls[1]
    assert url.endswith("/projects/g%2Fr/merge_requests") and body["source_branch"] == "harness/x-1" and headers["Private-token"] == "u"


def test_open_pr_without_token_or_cli_leaves_the_branch_and_says_so(monkeypatch):
    monkeypatch.setattr(forge.shutil, "which", lambda name: None)
    monkeypatch.delenv("GH_TOKEN", raising=False); monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(HarnessError):
        forge.open_pr("https://github.com/o/r.git", "harness/x", "main", "T", "B", ".")
    with pytest.raises(HarnessError):
        forge.open_pr("https://bitbucket.org/o/r.git", "harness/x", "main", "T", "B", ".")


def test_pr_facts_by_api_for_both_forges(monkeypatch):
    monkeypatch.setattr(forge.shutil, "which", lambda name: None)
    monkeypatch.setenv("GH_TOKEN", "t"); monkeypatch.setenv("GITLAB_TOKEN", "u")

    def fake_urlopen(req, timeout=None):
        u = req.full_url
        if u.endswith("/pulls/7"):
            return Resp(json.dumps({"html_url": "https://github.com/o/r/pull/7", "number": 7, "merged": True, "state": "closed", "merged_at": "2026-01-01T00:00:00Z",
                                    "closed_at": "2026-01-01T00:00:00Z", "merged_by": {"login": "alice"}, "merge_commit_sha": "abc"}).encode())
        if u.endswith("/pulls/7/reviews"):
            return Resp(json.dumps([{"user": {"login": "bob"}, "state": "APPROVED"}]).encode())
        if u.endswith("/merge_requests/3"):
            return Resp(json.dumps({"web_url": "https://gitlab.example.com/g/r/-/merge_requests/3", "iid": 3, "state": "merged", "merged_at": "2026-01-02T00:00:00Z",
                                    "closed_at": None, "merged_by": {"username": "carol"}, "merge_commit_sha": "def"}).encode())
        return Resp(json.dumps({"approved": True, "approved_by": [{"user": {"username": "dave"}}]}).encode())

    monkeypatch.setattr(forge.urllib.request, "urlopen", fake_urlopen)
    gh = forge.pr_facts("https://github.com/o/r/pull/7")
    assert gh["state"] == "merged" and gh["merged_by"] == "alice" and gh["merge_commit"] == "abc" and gh["reviews"] == [{"by": "bob", "state": "APPROVED"}]
    gl = forge.pr_facts("https://gitlab.example.com/g/r/-/merge_requests/3")
    assert gl["state"] == "merged" and gl["merged_by"] == "carol" and gl["merge_commit"] == "def" and gl["review_decision"] == "approved" and gl["reviews"][0]["by"] == "dave"
