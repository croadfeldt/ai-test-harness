"""Lifecycle B's last step: the test pull request. Blueprint section 5.0 and stage 6.

The packet already holds the accepted tests as a patch in the overlay layout, the provenance record,
the signed statement, and the UDLM records. This stage puts them on a branch of the test overlay
repository, commits under the harness's own identity, pushes that branch, and opens a pull request
whose body is the packet's plain-terms summary. It never touches the default branch: the only ref it
pushes is the harness branch, and there is no merge anywhere in this file. A person decides.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import config
from ..util import HarnessError, log, now_iso, read_json, run, write_json

BRANCH_PREFIX = "harness/"


def _git(repo: Path, *args: str, check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess:
    import os
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=300,
                          env={**os.environ, **(env or {})}, check=False) if not check else _git_checked(repo, args, env)


def _git_checked(repo: Path, args: tuple, env: dict | None) -> subprocess.CompletedProcess:
    import os
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=300, env={**os.environ, **(env or {})})
    if proc.returncode != 0:
        raise HarnessError(f"git {' '.join(args)} failed: {proc.stderr.strip()[-400:]}")
    return proc


def overlay_repo(explicit: str | None = None) -> Path:
    raw = explicit or config.get("propose", "repo", "HARNESS_OVERLAY_REPO")
    if not raw:
        raise HarnessError("no overlay repository configured: pass --overlay-repo, set HARNESS_OVERLAY_REPO, or set [propose].repo in harness/harness.local.toml")
    p = Path(raw)
    return p if p.is_absolute() else (config.HERE / p).resolve()


def default_branch(repo: Path, remote: str) -> str:
    proc = _git(repo, "symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD", check=False)
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip().split("/", 1)[1]
    for cand in ("main", "master"):
        if _git(repo, "rev-parse", "--verify", "--quiet", f"refs/remotes/{remote}/{cand}", check=False).returncode == 0:
            return cand
    raise HarnessError(f"cannot tell the default branch of {remote}; set [propose].base_branch")


def plain_terms(packet_md: str) -> str:
    m = re.search(r"\*\*In plain terms\.\*\*\s*(.+?)(?:\n\n|\Z)", packet_md, re.S)
    return m.group(1).strip() if m else packet_md.strip().splitlines()[0]


def pr_body(pkg: str, packet_md: str, facts: dict, results: dict, att: dict, run_id: str, files: list[str], signed: bool) -> str:
    c = results["counts"]
    lines = [plain_terms(packet_md), "",
             "| | |", "|---|---|",
             f"| Package | {pkg} {facts['old_version'] or ''} {'->' if facts['old_version'] and facts['old_version'] != facts['new_version'] else ''} {facts['new_version'] or ''} |".replace("  ", " "),
             f"| Tests proposed | {len([f for f in files if not f.endswith(('.json', '.yaml', '.md', '.pem'))])} file(s); {c['total']} ran, {c['pass_on_new']} pass on head, {c['fix_pinning_confirmed']} fix-pinning confirmed |",
             f"| Provenance | MANIFEST.json, in-toto statement, DSSE envelope (key {att.get('keyid', '')[:19]}), UDLM records, all in the same directory |",
             f"| Commit | {'signed' if signed else 'unsigned (no signing key configured; see [propose].sign)'} |",
             f"| Run | {run_id} |", "",
             "Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, "
             "and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.", ""]
    return "\n".join(lines)


def propose_package(workdir: Path, pkg: str, repo: Path, *, remote: str, base: str, author: tuple[str, str], sign: bool,
                    signing_key: str, signing_format: str, push: bool, open_pr: bool) -> dict:
    wl = read_json(workdir / "intake" / "worklist.json")
    run_id = wl["run_id"]
    pk = next(p for p in read_json(workdir / "packet" / "summary.json")["packages"] if p["package"] == pkg)
    out = workdir / "propose" / pkg
    out.mkdir(parents=True, exist_ok=True)
    rec = {"package": pkg, "run_id": run_id, "generated": now_iso(), "repository": repo.name, "remote": remote, "base_branch": base,
           "status": "nothing to propose", "branch": None, "commit": None, "signed": False, "pushed": False, "pull_request": None, "files": []}
    if not pk.get("tests_in_patch"):
        write_json(out / "proposal.json", rec); log(f"    {pkg}: no accepted tests in the packet, nothing to propose"); return rec
    patch = (workdir / pk["patch"]).read_text()
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    results = read_json(workdir / "execute" / pkg / "results.json")
    att = next((a for a in read_json(workdir / "attest" / "summary.json")["packages"] if a["package"] == pkg), {})
    dirs = sorted({m.group(1) for m in re.finditer(r"^\+\+\+ b/(.+)/[^/]+$", patch, re.M)})
    if len(dirs) != 1:
        raise HarnessError(f"{pkg}: the patch must place every test in one overlay directory, found {dirs}")
    overlay_dir = dirs[0]
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", pkg).strip("-")
    branch = f"{BRANCH_PREFIX}{safe}-{run_id}"
    if branch == base or not branch.startswith(BRANCH_PREFIX):
        raise HarnessError("refusing to work on anything but a harness/ branch")
    _git(repo, "fetch", "--quiet", remote)
    wt = Path(tempfile.mkdtemp(prefix="harness-propose-"))
    try:
        _git(repo, "worktree", "add", "--quiet", "-B", branch, str(wt), f"{remote}/{base}")
        _git(wt, "apply", "--index", str((workdir / pk["patch"]).resolve()))
        dest = wt / overlay_dir
        dest.mkdir(parents=True, exist_ok=True)
        copied = []
        for src, name in ((workdir / pk["packet_md"], "packet.md"), (workdir / pk["vex"], "vex.openvex.json"),
                          (workdir / att.get("manifest", ""), "MANIFEST.json"), (workdir / att.get("statement", ""), "statement.json"),
                          (workdir / att.get("envelope", ""), "statement.dsse.json"),
                          (workdir / "attest" / pkg / "signer.pub.pem", "signer.pub.pem")):
            if src.is_file():
                shutil.copy(src, dest / name); copied.append(f"{overlay_dir}/{name}")
        udlm_dir = workdir / "attest" / pkg / "udlm"
        if udlm_dir.is_dir():
            (dest / "udlm").mkdir(exist_ok=True)
            for f in sorted(udlm_dir.iterdir()):
                shutil.copy(f, dest / "udlm" / f.name); copied.append(f"{overlay_dir}/udlm/{f.name}")
        _git(wt, "add", "-A", overlay_dir)
        files = sorted(l.split("\t", 1)[1] for l in _git(wt, "diff", "--cached", "--name-status").stdout.splitlines() if l.strip())
        c = results["counts"]
        title = (f"Tests for {pkg} {facts['new_version'] or facts['old_version']}: {len(pk['tests_in_patch'])} candidate(s), "
                 f"{c['fix_pinning_confirmed']} fix-pinning confirmed")
        body = pr_body(pkg, (workdir / pk["packet_md"]).read_text(), facts, results, att, run_id, files, sign)
        (out / "pull-request.md").write_text(f"# {title}\n\n{body}")
        env = {"GIT_AUTHOR_NAME": author[0], "GIT_AUTHOR_EMAIL": author[1], "GIT_COMMITTER_NAME": author[0], "GIT_COMMITTER_EMAIL": author[1]}
        sign_args = []
        if sign:
            if not signing_key:
                raise HarnessError("[propose].sign is on but no signing_key is configured")
            sign_args = ["-c", f"gpg.format={signing_format}", "-c", f"user.signingkey={signing_key}", "-c", "commit.gpgsign=true"]
        _git_checked(wt, (*sign_args, "commit", "--quiet", "-F", str((out / "pull-request.md").resolve())), env)
        sha = _git(wt, "rev-parse", "HEAD").stdout.strip()
        signed = sign and _git(wt, "log", "-1", "--format=%G?", check=False).stdout.strip() not in ("N", "")
        rec.update({"status": "branch built", "branch": branch, "commit": sha, "signed": bool(signed), "files": files,
                    "author": {"name": author[0], "email": author[1]}, "title": title, "overlay_dir": overlay_dir})
        if push:
            # The one push this stage ever makes: the harness branch, to itself. Never the base branch.
            _git(wt, "push", "--quiet", "--force-with-lease", remote, f"refs/heads/{branch}:refs/heads/{branch}")
            rec["pushed"] = True; rec["status"] = "branch pushed"
            if open_pr:
                proc = subprocess.run(["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body-file", str((out / "pull-request.md").resolve())],
                                      cwd=wt, capture_output=True, text=True, timeout=120)
                if proc.returncode != 0:
                    rec["pull_request_error"] = proc.stderr.strip()[-300:]
                    log(f"    {pkg}: branch pushed but the pull request could not be opened: {proc.stderr.strip()[-120:]}")
                else:
                    rec["pull_request"] = proc.stdout.strip().splitlines()[-1]; rec["status"] = "pull request opened"
    finally:
        _git(repo, "worktree", "remove", "--force", str(wt), check=False)
        shutil.rmtree(wt, ignore_errors=True)
    write_json(out / "proposal.json", rec)
    log(f"    {pkg}: {rec['status']}; {len(files)} file(s) on {branch}" + (f"; {rec['pull_request']}" if rec.get("pull_request") else ""))
    return rec


def propose(*, workdir: Path, select: list[str] | None = None, overlay_repo_path: str | None = None, push: bool = True, open_pr: bool = True) -> list[dict]:
    from .. import selfcheck
    from ..util import merge_summary
    selfcheck.require(workdir, probes=False)
    repo = overlay_repo(overlay_repo_path)
    if not (repo / ".git").exists():
        raise HarnessError(f"{repo} is not a git checkout of the overlay repository")
    remote = str(config.get("propose", "remote", "HARNESS_OVERLAY_REMOTE", "origin"))
    base = str(config.get("propose", "base_branch", "HARNESS_OVERLAY_BASE", "") or "") or default_branch(repo, remote)
    author = (str(config.get("propose", "author_name", "HARNESS_PROPOSE_AUTHOR", "AI Test Harness")),
              str(config.get("propose", "author_email", "HARNESS_PROPOSE_EMAIL", "ai-test-harness@example.invalid")))
    sign = str(config.get("propose", "sign", "HARNESS_PROPOSE_SIGN", "false")).lower() in ("1", "true", "yes")
    key = str(config.get("propose", "signing_key", "HARNESS_PROPOSE_SIGNING_KEY", "") or "")
    fmt = str(config.get("propose", "signing_format", None, "ssh"))
    pkgs = [p["package"] for p in read_json(workdir / "packet" / "summary.json")["packages"]]
    outs = [propose_package(workdir, p, repo, remote=remote, base=base, author=author, sign=sign, signing_key=key, signing_format=fmt,
                            push=push, open_pr=open_pr) for p in pkgs if not select or p in select]
    merge_summary(workdir / "propose" / "summary.json", [{"package": o["package"], "status": o["status"], "branch": o["branch"],
                                                          "pull_request": o.get("pull_request"), "signed": o["signed"]} for o in outs])
    return outs
