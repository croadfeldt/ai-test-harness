"""Stage 6: the review packet. Blueprint section 5 stage 6 and section 8.

One packet per work item: a one-page summary, the accepted candidate tests as a patch against the
overlay layout (section 8.1), per-test verdicts, findings with routing, draft VEX statements in
OpenVEX (capability map: vexctl-compatible), and references to every artifact the claims rest on.
The harness proposes; the reviewer approves, edits, or rejects. Nothing here merges anything.
"""
from __future__ import annotations

import difflib
import json
from pathlib import Path

from ..util import log, now_iso, read_json, sha256_text, write_json


def _overlay_path(pkg: str, version: str, fname: str, ecosystem: str = "python") -> str:
    major_minor = ".".join(version.split(".")[:2]) + ".x" if version.count(".") >= 1 else version
    return f"overlays/{ecosystem}/{pkg}/{major_minor}/{fname}"


def _patch(files: list[tuple[str, str]]) -> str:
    out = []
    for path, content in files:
        lines = content.splitlines(keepends=True)
        out.append(f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n+++ b/{path}\n")
        out.extend(list(difflib.unified_diff([], lines, fromfile="/dev/null", tofile=f"b/{path}", n=0))[2:])
    return "".join(out)


def _vex(pkg: str, purl_new: str, purl_old: str | None, vulns_doc: dict, triage: dict, run_id: str) -> dict:
    """OpenVEX document with one statement per advisory: fixed when a confirmed fix-pinning test
    exists, affected when the advisory is open at head and the package is reachable, otherwise
    under_investigation. Every statement is a DRAFT for Product Security; none is published here."""
    confirmed_ids = set()
    for t in triage["tests"]:
        if t["action"].startswith("accept as CVE evidence"):
            for tid in t["test_id"], t["name"]:
                confirmed_ids.add(t["name"])
    statements = []
    # advisories fixed by this change
    for v in vulns_doc.get("vulns_old", []):
        cves = [a for a in v["aliases"] if a.startswith("CVE-")] or [v["id"]]
        proven = [n for n in confirmed_ids if any(x.lower().replace("-", "_") in n for x in [v["id"], *v["aliases"]])]
        statements.append({"vulnerability": {"name": cves[0], "aliases": [v["id"], *v["aliases"]]},
                           "products": [{"@id": purl_new}],
                           "status": "fixed" if proven else "under_investigation",
                           "status_notes": (f"fix-pinning test(s) {proven} fail on {purl_old} and pass on {purl_new}" if proven
                                            else "bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet"),
                           "harness_evidence": {"tests": proven, "confirmed": bool(proven)}})
    # advisories still open at head (including those a downgrade introduced)
    for v in vulns_doc.get("vulns", []):
        cves = [a for a in v["aliases"] if a.startswith("CVE-")] or [v["id"]]
        proven = [n for n in confirmed_ids if any(x.lower().replace("-", "_") in n for x in [v["id"], *v["aliases"]])]
        if proven:
            status, notes = "affected", f"exposure test(s) {proven} fail on {purl_new} and pass on {purl_old}: the change introduces this exposure"
        elif triage.get("_reachable") == "true":
            status, notes = "affected", f"open at head; reachable=true; fixed in {v['fixed_versions'] or 'no fixed version published'}"
        else:
            status, notes = "under_investigation", f"open at head; reachable={triage.get('_reachable')}; fixed in {v['fixed_versions'] or 'no fixed version published'}"
        statements.append({"vulnerability": {"name": cves[0], "aliases": [v["id"], *v["aliases"]]},
                           "products": [{"@id": purl_new}], "status": status, "status_notes": notes,
                           "harness_evidence": {"tests": proven, "confirmed": bool(proven)}})
    # One statement per vulnerability: OSV, GHSA and PYSEC ids for the same CVE collapse, aliases merged,
    # and the strongest status wins (fixed > affected > under_investigation).
    rank = {"fixed": 3, "affected": 2, "under_investigation": 1}
    merged: dict[str, dict] = {}
    for st in statements:
        name = st["vulnerability"]["name"]
        if name not in merged:
            merged[name] = st
        else:
            m = merged[name]
            m["vulnerability"]["aliases"] = sorted(set(m["vulnerability"]["aliases"]) | set(st["vulnerability"]["aliases"]))
            if rank[st["status"]] > rank[m["status"]]:
                m["status"], m["status_notes"], m["harness_evidence"] = st["status"], st["status_notes"], st["harness_evidence"]
    statements = list(merged.values())
    return {"@context": "https://openvex.dev/ns/v0.2.0", "@id": f"https://ai-test-harness.local/vex/{run_id}/{pkg}",
            "author": "ai-test-harness (DRAFT, requires Product Security review)", "role": "draft", "timestamp": now_iso(), "version": 1,
            "statements": statements}


def packet_package(workdir: Path, pkg: str, run_id: str) -> dict:
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    ecosystem = read_json(workdir / "intake" / "worklist.json").get("ecosystem", "python")
    triage = read_json(workdir / "triage" / pkg / "triage.json")
    triage["_reachable"] = facts["call_sites_summary"]["reachable"]
    vulns_doc = read_json(workdir / "analyze" / pkg / "vulns.json")
    gen_path = workdir / "generate" / pkg / "manifest.json"
    gen = read_json(gen_path) if gen_path.exists() else {"files": [], "model": {}}
    res_path = workdir / "execute" / pkg / "results.json"
    results = read_json(res_path) if res_path.exists() else None
    out = workdir / "packet" / pkg
    out.mkdir(parents=True, exist_ok=True)
    accept = {t["name"] for t in triage["tests"] if t["action"].startswith("accept")}

    # Tests as a patch against the overlay layout, only the tests triage accepts, per file. The
    # adapter cuts the others out of the file the way its language allows.
    from .. import adapters
    adapter = adapters.get(ecosystem)
    patch_files = []
    for f in gen["files"]:
        src = (workdir / "generate" / pkg / f["file"]).read_text()
        cut = {n for n in f["tests"] if n not in accept}
        content = adapter.drop_tests(src, cut) if cut else src
        if not adapter.test_names(content):
            continue
        patch_files.append((_overlay_path(pkg, facts["new_version"] or facts["old_version"], Path(f["file"]).name, ecosystem), content))
    patch = _patch(patch_files)
    (out / "tests.patch").write_text(patch)
    vex = _vex(pkg, facts["purl"], adapter.purl(pkg, facts["old_version"]) if facts["old_version"] else None, vulns_doc, triage, run_id)
    write_json(out / "vex.openvex.json", vex)

    mut_path = workdir / "execute" / pkg / "mutation" / "mutation.json"
    mut = read_json(mut_path) if mut_path.exists() else None
    if mut and mut.get("status") == "ran":
        weak = sorted(set(mut["tests"]) - set(mut["per_test"]))
        mut_md = (f"score {mut['score']} ({mut['killed']} of {mut['valid']} sampled mutants killed, {mut['sites']} sites on executed lines, "
                  f"seed {mut['seed']}). Tests that killed nothing: {weak or 'none'}. Target in the blueprint: 0.6.")
    else:
        mut_md = "not run."
    s = triage["summary"]; c = results["counts"] if results else {}
    cov = results["coverage_summary"]["covered_lines_in_target"] if results else 0
    findings_md = "\n".join(f"- **{f['class']}** ({f['confidence']}): {f['summary']}. Route: {f['routing']}. Evidence: `{f['evidence_ref']}`" for f in triage["findings"]) or "- none"
    tests_md = "\n".join(f"| {t['name']} | {t['category']} | {t['versions']['old']} | {t['versions']['new']} | {t['class']} | {t['action']} |" for t in triage["tests"]) or "| none | | | | | |"
    vex_md = "\n".join(f"| {st['vulnerability']['name']} | {st['status']} | {st['status_notes'][:110]} |" for st in vex["statements"]) or "| none | | |"
    cand_path = workdir / "analyze" / pkg / "fixed-candidate.json"
    cand = read_json(cand_path) if cand_path.exists() else None
    if cand and cand.get("status") == "resolved":
        upgrade_md = (f"The advisories are fixed in {pkg} {cand['fixed_version']}. The harness resolved an environment with it: {cand['note']}. "
                      f"Packages that move: " + (", ".join(f"{k} {a} -> {b}" for k, (a, b) in cand.get("moved", {}).items()) or "none") + ".")
    elif cand:
        upgrade_md = f"No environment with the fixed version ({cand['fixed_version']}) resolves: {cand['note']}. " + "; ".join(a.get("error", "") for a in cand.get("attempts", []) if a.get("error"))
    else:
        upgrade_md = "Not applicable: the change brought the fixed version, or no advisory is open at head."
    rel_path = workdir / "execute" / pkg / "relevance.json"
    rel = read_json(rel_path) if rel_path.exists() else None
    if rel and rel["proposals"]:
        rows = "\n".join(f"| {p['test']} | {p['file']} | {p['class']} | {p['reason']} | {'yes' if p['rewrite_candidate'] else ''} | {'owning team, low' if p['human_written'] else p['priority']} | {p['text'][:110]} |" for p in rel["proposals"])
        retire_md = (f"Promotions: none yet; promotion needs a survived version change or a caught regression (section 8.3).\n\n"
                     f"Retirement proposals, for {rel['horizon']}. Advisory: a person approves, a retired test is kept and re-run once on the next change, nothing is deleted.\n\n"
                     f"| test | file | class | reason | rewrite | priority | evidence |\n|---|---|---|---|---|---|---|\n{rows}")
    elif rel:
        retire_md = (f"Promotions: none yet (section 8.3). Retirements: none proposed for {rel['horizon']}; "
                     f"{rel['examined']['generated']} generated and {rel['examined']['application']} application test(s) examined against "
                     f"{rel['api_changes_considered']['removed']} removed and {rel['api_changes_considered']['breaking_changed']} changed symbols.")
    else:
        retire_md = "Promotions: none yet (section 8.3). Retirements: relevance stage not run."
    recommended = ("**Do not merge** until Supply Chain Security clears the suspicious finding." if s.get("blocking") else
                   "**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.")
    # In plain terms: the verdict first, in words, then the evidence.
    # Count vulnerabilities, not advisory ids or tests: one CVE may carry three ids and two tests.
    from .generate import _group_advisories
    groups_open = _group_advisories(vulns_doc.get("vulns", [])); groups_fixed = _group_advisories(vulns_doc.get("vulns_old", []))
    n_open, n_fixed = len(groups_open), len(groups_fixed)
    proven_ids = {t["name"] for t in triage["tests"] if t["action"].startswith("accept as CVE evidence")}
    def _proven(groups):
        return sum(1 for key, grp in groups.items() if any(x.lower().replace("-", "_") in n for n in proven_ids for v in grp for x in [v["id"], *v.get("aliases", [])]))
    confirmed = _proven(groups_open) + _proven(groups_fixed)
    n_issues = n_open + n_fixed
    if facts["change"] == "bumped" and n_fixed and not n_open:
        what = f"This change updates {pkg} from {facts['old_version']} to {facts['new_version']}, which closes {n_fixed} known vulnerabilit{'y' if n_fixed == 1 else 'ies'}."
    elif facts["change"] == "bumped" and n_open and not n_fixed:
        what = f"This change moves {pkg} from {facts['old_version']} to {facts['new_version']}, a version with {n_open} known vulnerabilit{'y' if n_open == 1 else 'ies'}. That is a downgrade."
    elif facts["change"] == "unchanged" and n_open:
        what = f"This change leaves {pkg} at {facts['new_version']}, which has {n_open} known vulnerabilit{'y' if n_open == 1 else 'ies'} the application is exposed to."
    else:
        what = f"This change moves {pkg} from {facts['old_version']} to {facts['new_version']}."
    proven = (f"The harness proved {confirmed} of the {n_issues} with a test that fails on the vulnerable version and passes on the fixed one; the other {n_issues - confirmed} {'is' if n_issues - confirmed == 1 else 'are'} unproven and marked so."
              if confirmed else f"The harness could not prove any of the {n_issues} with a test; that is stated, not hidden.")
    accepted_n = len(accept)
    todo = ("Do not merge until Supply Chain Security clears the suspicious finding." if s.get("blocking") else
            f"Accept the {accepted_n} candidate test{'s' if accepted_n != 1 else ''} if they look right, act on the findings below, and send the draft VEX statements to Product Security.")
    plain = f"{what} {proven} {todo}"
    md = f"""# Review packet: {pkg} {facts['old_version']} -> {facts['new_version']}

**In plain terms.** {plain}

Run `{run_id}`. Generated {now_iso()}. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
{pkg} at depth {facts['depth']}, change `{facts['change']}`, reachable from first-party code: **{facts['call_sites_summary']['reachable']}**
({facts['call_sites_summary']['production']} production references). Risk score {facts['risk']['score']}, budget {facts['risk']['budget']['level']}.
API diff: +{facts['api_diff_summary']['added']} / -{facts['api_diff_summary']['removed']} / ~{facts['api_diff_summary']['changed']}, {facts['api_diff_summary']['breaking']} breaking.
Advisories: {facts['vulns_summary']['count']} open at head, {facts['vulns_summary'].get('count_old', 0)} on the replaced version.

## What was tested
{c.get('total', 0)} generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. {c.get('pass_on_new', 0)} pass on head, {c.get('flaky', 0)} flaky,
{c.get('fix_pinning_confirmed', 0)} fix-pinning confirmed, {cov} lines of the package covered. Model: `{gen.get('model', {}).get('id', 'n/a')}`.
Mutation: {mut_md}

## Findings
{findings_md}

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
{tests_md}

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
{vex_md}

## Upgrade path
{upgrade_md}

## Recommended action
{recommended}

## Promotions and retirements
{retire_md}

## Artifacts
- tests as a patch against the overlay layout: `packet/{pkg}/tests.patch`
- verdicts and logs: `execute/{pkg}/results.json`, `execute/{pkg}/{{new,new-rerun,old}}/`
- facts: `analyze/{pkg}/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/{pkg}/manifest.json`, every prompt and response under `generate/{pkg}/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/{pkg}/statement.json` (after stage attest)
"""
    (out / "packet.md").write_text(md)
    rec = {"package": pkg, "generated": now_iso(), "packet_md": f"packet/{pkg}/packet.md", "patch": f"packet/{pkg}/tests.patch",
           "patch_sha256": sha256_text(patch), "vex": f"packet/{pkg}/vex.openvex.json", "tests_in_patch": sorted(accept),
           "vex_statements": {st["vulnerability"]["name"]: st["status"] for st in vex["statements"]}, "recommended": recommended}
    write_json(out / "packet.json", rec)
    log(f"    {pkg}: packet with {len(accept)} accepted test(s), {len(vex['statements'])} VEX draft(s): {rec['vex_statements']}")
    return rec


def packet(*, workdir: Path, select: list[str] | None = None) -> list[dict]:
    from .. import selfcheck
    selfcheck.require(workdir, probes=False)
    run_id = read_json(workdir / "intake" / "worklist.json")["run_id"]
    tri = read_json(workdir / "triage" / "summary.json")
    outs = [packet_package(workdir, p["package"], run_id) for p in tri["packages"] if not select or p["package"] in select]
    from ..util import merge_summary
    merge_summary(workdir / "packet" / "summary.json", outs)
    return outs
