"""Stage 7: the review gate's decisions, captured. Blueprint section 5.0 and stage 7.

Lifecycle B ends with a person merging, editing, or closing the test pull request the harness
opened. This stage reads that decision back: which proposed tests landed unchanged, which were edited
before landing, which were dropped, and who decided when. Each decision becomes a labeled example for
prompt evaluation, and each accepted test's candidate record becomes a requested record (the
reviewer's act) and a realized record (the test as it landed), sealed like the rest. A signed
acceptance statement names the merge commit and the realized records. Nothing here changes any
repository; it only reads.
"""
from __future__ import annotations

import base64
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from .. import adapters, config
from ..util import HarnessError, log, now_iso, read_json, write_json

ACCEPTANCE_PREDICATE = "https://github.com/croadfeldt/ai-test-harness/attestation/acceptance/v0.1"
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"


def pr_facts(url: str) -> dict:
    """What GitHub says about the pull request. Needs gh; the caller may pass facts directly instead."""
    proc = subprocess.run(["gh", "pr", "view", url, "--json", "state,mergedAt,mergedBy,mergeCommit,closedAt,reviewDecision,reviews,url,number"],
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise HarnessError(f"gh pr view {url}: {proc.stderr.strip()[-300:]}")
    d = json.loads(proc.stdout)
    return {"url": d["url"], "number": d["number"], "state": d["state"].lower(), "merged_at": d.get("mergedAt"), "closed_at": d.get("closedAt"),
            "merged_by": (d.get("mergedBy") or {}).get("login"), "merge_commit": (d.get("mergeCommit") or {}).get("oid"),
            "review_decision": d.get("reviewDecision") or "", "reviews": [{"by": r["author"]["login"], "state": r["state"]} for r in d.get("reviews", [])]}


def _show(repo: Path, rev: str, path: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True, text=True, timeout=60)
    return proc.stdout if proc.returncode == 0 else None


def compare(repo: Path, proposal: dict, pr: dict, adapter) -> list[dict]:
    """One decision per proposed test file, and per test inside it, from the merged tree."""
    subprocess.run(["git", "-C", str(repo), "fetch", "--quiet", proposal.get("remote", "origin")], capture_output=True, timeout=300)
    out = []
    for path in proposal["files"]:
        if not path.startswith(proposal["overlay_dir"] + "/") or not adapter.is_test_file(Path(path)):
            continue
        before = _show(repo, proposal["commit"], path)
        after = _show(repo, pr["merge_commit"], path) if pr.get("merge_commit") else None
        if before is None:
            continue
        if after is None:
            out.append({"path": path, "decision": "rejected", "tests": {n: "rejected" for n in adapter.test_names(before)}})
            continue
        edited = after != before
        names_before, names_after = adapter.test_names(before), set(adapter.test_names(after))
        tests = {n: ("rejected" if n not in names_after else ("edited" if edited else "accepted")) for n in names_before}
        rec = {"path": path, "decision": "edited" if edited else "accepted", "tests": tests,
               "merged_digest": "sha256:" + hashlib.sha256(after.encode()).hexdigest()}
        if edited:
            rec["diff"] = "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                                       fromfile=f"proposed/{path}", tofile=f"merged/{path}", n=2))[:20000]
            rec["added_tests"] = sorted(names_after - set(names_before))
        out.append(rec)
    return out


def _intents(workdir: Path, pkg: str) -> dict[str, dict]:
    path = workdir / "attest" / pkg / "udlm" / "test-evidence.yaml"
    if not path.exists():
        return {}
    docs = [d for d in yaml.safe_load_all(path.read_text()) if d and d.get("record_type") == "intent_record"]
    return {d["fields"]["test_id"].split("::")[1]: d for d in docs}


def _sign(workdir: Path, statement: dict, out: Path) -> dict:
    from .attest import _dsse, _key
    priv, pub_pem, keyid = _key(workdir)
    payload = json.dumps(statement, sort_keys=True, separators=(",", ":")).encode()
    env = _dsse(payload, "application/vnd.in-toto+json", priv, keyid)
    write_json(out / "acceptance-statement.json", statement)
    write_json(out / "acceptance-statement.dsse.json", env)
    (out / "signer.pub.pem").write_text(pub_pem)
    return {"envelope": "acceptance-statement.dsse.json", "keyid": keyid, "signer": "local Ed25519 development key; Trusted Artifact Signer in Konflux"}


def capture(workdir: Path, pkg: str, pr: dict, repo: Path, adapter) -> dict:
    proposal = read_json(workdir / "propose" / pkg / "proposal.json")
    out = workdir / "feedback" / pkg
    out.mkdir(parents=True, exist_ok=True)
    gen = read_json(workdir / "generate" / pkg / "manifest.json")
    results = read_json(workdir / "execute" / pkg / "results.json")
    by_test = {t["name"]: t for t in results["tests"]}
    file_meta = {f["file"].split("/")[-1]: f for f in gen["files"]}
    rec = {"package": pkg, "run_id": proposal["run_id"], "generated": now_iso(), "pull_request": pr, "proposal": {"branch": proposal["branch"], "commit": proposal["commit"]},
           "decisions": [], "counts": {"accepted": 0, "edited": 0, "rejected": 0}, "records": None, "statement": None}
    if pr["state"] != "merged":
        rec["outcome"] = "closed without merge: every proposed test rejected" if pr["state"] == "closed" else "open: no decision yet"
        if pr["state"] == "closed":
            for path in proposal["files"]:
                if adapter.is_test_file(Path(path)):
                    names = adapter.test_names(_show(repo, proposal["commit"], path) or "")
                    rec["decisions"].append({"path": path, "decision": "rejected", "tests": {n: "rejected" for n in names}})
                    rec["counts"]["rejected"] += len(names)
        write_json(out / "acceptance.json", rec); log(f"    {pkg}: {rec['outcome']}"); return rec
    rec["outcome"] = f"merged by {pr['merged_by']} at {pr['merged_at']}"
    rec["decisions"] = compare(repo, proposal, pr, adapter)
    # Labeled examples for prompt evaluation: what the model wrote, what a person did with it.
    with (out / "decisions.jsonl").open("w") as f:
        for d in rec["decisions"]:
            meta = file_meta.get(Path(d["path"]).name, {})
            for name, decision in d["tests"].items():
                rec["counts"][decision] += 1
                t = by_test.get(name, {})
                f.write(json.dumps({"test": name, "file": d["path"], "decision": decision, "category": t.get("category", meta.get("category")),
                                    "verdict": t.get("verdict"), "model": meta.get("model"), "prompt_sha256": meta.get("prompt_sha256"),
                                    "response_sha256": meta.get("response_sha256"), "accepted_by": pr["merged_by"], "accepted_at": pr["merged_at"]}) + "\n")
    # Accepted candidates become requested and realized records; the intent records stay as they were.
    from .udlm_records import Emitter
    intents = _intents(workdir, pkg)
    em = Emitter(workdir, pkg)
    overlay_provider = f"{em.estate}/providers/test-overlay-repository"
    realized_heads = []
    for d in rec["decisions"]:
        for name, decision in d["tests"].items():
            if decision in ("accepted", "edited") and name in intents:
                req, real = em.acceptance(intents[name], {**d, "decision": decision}, pr, overlay_provider)
                if "integrity" in real:
                    realized_heads.append({"name": real["handle"] + "@realized", "digest": {"sha256": real["integrity"]["head"].split(":", 1)[1]}})
    if em.records:
        idx = em.write(out / "udlm")
        rec["records"] = {"index": "udlm/index.json", "sealed": idx["sealed"], "schema_problems": (idx.get("schema_validation") or {}).get("count"),
                          "requested_and_realized": sum(len(v) for v in em.records.values())}
    subjects = [{"name": f"git:{pr['url']}", "digest": {"gitCommit": pr["merge_commit"]}}] + realized_heads
    statement = {"_type": STATEMENT_TYPE, "subject": subjects, "predicateType": ACCEPTANCE_PREDICATE,
                 "predicate": {"pull_request": pr["url"], "accepted_by": pr["merged_by"], "accepted_at": pr["merged_at"],
                               "proposal_commit": proposal["commit"], "run_id": proposal["run_id"], "counts": rec["counts"],
                               "decisions": [{"path": d["path"], "decision": d["decision"], "tests": d["tests"]} for d in rec["decisions"]],
                               "note": "The merge is the human act; this statement records it and names the realized records it produced."}}
    rec["statement"] = _sign(workdir, statement, out)
    write_json(out / "acceptance.json", rec)
    c = rec["counts"]
    log(f"    {pkg}: {rec['outcome']}; {c['accepted']} accepted, {c['edited']} edited, {c['rejected']} rejected; "
        f"{(rec['records'] or {}).get('requested_and_realized', 0)} UDLM record(s), statement signed")
    return rec


def feedback(*, workdir: Path, select: list[str] | None = None, overlay_repo_path: str | None = None, facts: dict | None = None) -> list[dict]:
    from .. import selfcheck
    from ..util import merge_summary
    from .propose import overlay_repo
    selfcheck.require(workdir, probes=False)
    repo = overlay_repo(overlay_repo_path)
    adapter = adapters.get(read_json(workdir / "intake" / "worklist.json").get("ecosystem", "python"))
    outs = []
    for row in read_json(workdir / "propose" / "summary.json")["packages"]:
        pkg = row["package"]
        if select and pkg not in select:
            continue
        if not row.get("pull_request"):
            log(f"    {pkg}: no pull request was opened, nothing to capture"); continue
        outs.append(capture(workdir, pkg, facts or pr_facts(row["pull_request"]), repo, adapter))
    merge_summary(workdir / "feedback" / "summary.json", [{"package": o["package"], "outcome": o["outcome"], **o["counts"]} for o in outs])
    return outs
