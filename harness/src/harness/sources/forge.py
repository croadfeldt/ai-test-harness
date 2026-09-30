"""The code forges the harness talks to: GitHub and GitLab, hosted or self-managed, through their
command-line tools when present and their APIs when not. Two operations only: open a pull request
(GitLab: merge request) for a branch the harness has already pushed, and read a request's decision
back. Nothing here merges, approves, comments, or touches a default branch.

Tokens come from the environment the caller runs in: GH_TOKEN or GITHUB_TOKEN for GitHub, GITLAB_TOKEN
or HARNESS_GITLAB_TOKEN for GitLab. A token is never written to a record; the request's URL is.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request

from ..util import HarnessError


def detect(remote_url: str) -> dict:
    """Host, kind (github, gitlab, unknown), repository path and API root for a git remote URL."""
    m = re.match(r"^(?:(?:https?|ssh|git)://)?(?:[^@/]+@)?([^/:]+)(?::\d+)?[:/](.+?)(?:\.git)?/?$", remote_url.strip())
    if not m:
        return {"host": "", "kind": "unknown", "path": "", "api": ""}
    host, path = m.group(1), m.group(2)
    if host == "github.com" or host.startswith("github."):
        kind, api = "github", ("https://api.github.com" if host == "github.com" else f"https://{host}/api/v3")
    elif "gitlab" in host:
        kind, api = "gitlab", f"https://{host}/api/v4"
    else:
        kind, api = "unknown", ""
    return {"host": host, "kind": kind, "path": path, "api": api}


def token_for(kind: str) -> str | None:
    names = {"github": ("GH_TOKEN", "GITHUB_TOKEN"), "gitlab": ("GITLAB_TOKEN", "HARNESS_GITLAB_TOKEN")}.get(kind, ())
    return next((os.environ[n] for n in names if os.environ.get(n)), None)


def _api(method: str, url: str, kind: str, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "User-Agent": "ai-test-harness/0.1", "Content-Type": "application/json"}
    headers["Authorization" if kind == "github" else "PRIVATE-TOKEN"] = (f"Bearer {token}" if kind == "github" else token)
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raise HarnessError(f"{kind} API {method} {url}: {e.code} {e.read().decode(errors='replace')[:300]}") from e


def open_pr(remote_url: str, branch: str, base: str, title: str, body: str, cwd) -> dict:
    """Open the request for a pushed branch. Returns {url, number}. Raises when it cannot; the branch stays."""
    f = detect(remote_url)
    if f["kind"] == "github":
        if shutil.which("gh") and not os.environ.get("HARNESS_FORGE_API_ONLY"):
            proc = subprocess.run(["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body],
                                  cwd=cwd, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0:
                url = proc.stdout.strip().splitlines()[-1]
                return {"url": url, "number": int(url.rstrip("/").rsplit("/", 1)[-1]) if url.rstrip("/").rsplit("/", 1)[-1].isdigit() else None, "via": "gh"}
            if not token_for("github"):
                raise HarnessError(f"gh pr create: {proc.stderr.strip()[-300:]}")
        token = token_for("github")
        if not token:
            raise HarnessError("no gh on this machine and no GH_TOKEN or GITHUB_TOKEN in the environment")
        d = _api("POST", f"{f['api']}/repos/{f['path']}/pulls", "github", token, {"title": title, "head": branch, "base": base, "body": body})
        return {"url": d["html_url"], "number": d["number"], "via": "api"}
    if f["kind"] == "gitlab":
        if shutil.which("glab") and not os.environ.get("HARNESS_FORGE_API_ONLY"):
            proc = subprocess.run(["glab", "mr", "create", "--source-branch", branch, "--target-branch", base, "--title", title,
                                   "--description", body, "--yes", "--no-editor"], cwd=cwd, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0:
                url = next((l for l in proc.stdout.strip().splitlines()[::-1] if "://" in l), proc.stdout.strip().splitlines()[-1])
                return {"url": url, "number": int(url.rstrip("/").rsplit("/", 1)[-1]) if url.rstrip("/").rsplit("/", 1)[-1].isdigit() else None, "via": "glab"}
            if not token_for("gitlab"):
                raise HarnessError(f"glab mr create: {proc.stderr.strip()[-300:]}")
        token = token_for("gitlab")
        if not token:
            raise HarnessError("no glab on this machine and no GITLAB_TOKEN in the environment")
        proj = urllib.parse.quote(f["path"], safe="")
        d = _api("POST", f"{f['api']}/projects/{proj}/merge_requests", "gitlab", token,
                 {"source_branch": branch, "target_branch": base, "title": title, "description": body, "remove_source_branch": False})
        return {"url": d["web_url"], "number": d["iid"], "via": "api"}
    raise HarnessError(f"{f['host'] or remote_url}: not a forge the harness knows; the branch {branch} is pushed, open the request by hand")


def pr_facts(url: str) -> dict:
    """What the forge says about a request: state, who merged it and when, the merge commit, reviews.
    The shape feedback reads, whichever forge produced it."""
    m = re.match(r"^https?://([^/]+)/(.+?)/(?:-/)?(pull|merge_requests)/(\d+)/?$", url.strip())
    if not m:
        raise HarnessError(f"not a pull or merge request URL: {url}")
    host, path, kind_word, number = m.group(1), m.group(2), m.group(3), int(m.group(4))
    f = detect(f"https://{host}/{path}")
    if kind_word == "pull" and f["kind"] in ("github", "unknown"):
        if shutil.which("gh") and not os.environ.get("HARNESS_FORGE_API_ONLY"):
            proc = subprocess.run(["gh", "pr", "view", url, "--json", "state,mergedAt,mergedBy,mergeCommit,closedAt,reviewDecision,reviews,url,number"],
                                  capture_output=True, text=True, timeout=120)
            if proc.returncode == 0:
                d = json.loads(proc.stdout)
                return {"url": d["url"], "number": d["number"], "state": d["state"].lower(), "merged_at": d.get("mergedAt"), "closed_at": d.get("closedAt"),
                        "merged_by": (d.get("mergedBy") or {}).get("login"), "merge_commit": (d.get("mergeCommit") or {}).get("oid"),
                        "review_decision": d.get("reviewDecision") or "", "reviews": [{"by": r["author"]["login"], "state": r["state"]} for r in d.get("reviews", [])]}
        token = token_for("github")
        if not token:
            raise HarnessError("reading a GitHub pull request needs gh or GH_TOKEN")
        api = "https://api.github.com" if host == "github.com" else f"https://{host}/api/v3"
        d = _api("GET", f"{api}/repos/{path}/pulls/{number}", "github", token)
        reviews = _api("GET", f"{api}/repos/{path}/pulls/{number}/reviews", "github", token)
        state = "merged" if d.get("merged") else d.get("state", "")
        return {"url": d["html_url"], "number": d["number"], "state": state, "merged_at": d.get("merged_at"), "closed_at": d.get("closed_at"),
                "merged_by": (d.get("merged_by") or {}).get("login"), "merge_commit": d.get("merge_commit_sha") if d.get("merged") else None,
                "review_decision": "", "reviews": [{"by": r["user"]["login"], "state": r["state"]} for r in (reviews if isinstance(reviews, list) else [])]}
    token = token_for("gitlab")
    if not token:
        raise HarnessError("reading a GitLab merge request needs GITLAB_TOKEN")
    api = f"https://{host}/api/v4"; proj = urllib.parse.quote(path, safe="")
    d = _api("GET", f"{api}/projects/{proj}/merge_requests/{number}", "gitlab", token)
    approvals = _api("GET", f"{api}/projects/{proj}/merge_requests/{number}/approvals", "gitlab", token)
    return {"url": d["web_url"], "number": d["iid"], "state": d.get("state", ""), "merged_at": d.get("merged_at"), "closed_at": d.get("closed_at"),
            "merged_by": (d.get("merged_by") or d.get("merge_user") or {}).get("username"), "merge_commit": d.get("merge_commit_sha"),
            "review_decision": "approved" if approvals.get("approved") else "",
            "reviews": [{"by": a["user"]["username"], "state": "APPROVED"} for a in approvals.get("approved_by", [])]}
