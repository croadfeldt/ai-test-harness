"""Stage 5: triage. Blueprint section 5 stage 5.

Deterministic classification of everything stages 1 to 4 produced, with a confidence and the
evidence path for each finding. The classes are the blueprint's. Rules first; a model-based pass over
raw logs (Log Detective style) can be added behind the same output without changing consumers.
Anything under the confidence threshold is escalated to a person rather than auto-routed.
"""
from __future__ import annotations

from pathlib import Path

from ..util import log, now_iso, read_json, write_json

THRESHOLD = 0.7
ROUTING = {"test-bug": "regenerate or discard; no human time", "behavior-change": "note in review summary",
           "undocumented-change": "flag for reviewer", "defect": "open issue with reproducer",
           "security": "Product Security", "suspicious": "Supply Chain Security; block merge",
           "obsolete": "propose retirement", "redundant": "propose retirement or merge"}


def _aliases_for(vulns_doc: dict, cve: str) -> list[str]:
    out = []
    for v in vulns_doc.get("vulns_old", []) + vulns_doc.get("vulns", []):
        ids = [v["id"], *v.get("aliases", [])]
        if cve in ids:
            out.extend(ids)
    return sorted(set(out))


def _finding(cls, confidence, summary, evidence, package, **extra):
    f = {"class": cls, "confidence": round(confidence, 2), "summary": summary, "evidence_ref": evidence, "package": package,
         "routing": ROUTING[cls] if confidence >= THRESHOLD else "escalate: below confidence threshold", "escalated": confidence < THRESHOLD}
    f.update(extra)
    return f


def triage_package(workdir: Path, pkg: str) -> dict:
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    vulns = read_json(workdir / "analyze" / pkg / "vulns.json")
    res_path = workdir / "execute" / pkg / "results.json"
    results = read_json(res_path) if res_path.exists() else None
    gen_path = workdir / "generate" / pkg / "manifest.json"
    gen = read_json(gen_path) if gen_path.exists() else None
    agent_path = workdir / "generate" / pkg / "manifest.agent.json"
    agent = read_json(agent_path) if agent_path.exists() else None
    findings, tests = [], []

    # Package-level findings from stages 1 and 2.
    if facts["change"] == "bumped" and facts["old_version"] and facts["new_version"]:
        from packaging.version import InvalidVersion, Version
        try:
            if Version(facts["new_version"]) < Version(facts["old_version"]):
                findings.append(_finding("security" if facts["vulns_summary"]["count"] else "undocumented-change", 0.95,
                                         f"{pkg} downgraded {facts['old_version']} -> {facts['new_version']}"
                                         + (f" into a version with {facts['vulns_summary']['count']} known advisories" if facts["vulns_summary"]["count"] else ""),
                                         f"analyze/{pkg}/facts.json", pkg, advisories=facts["vulns_summary"]["cves"]))
        except InvalidVersion:
            pass
    open_advisories = [v for v in vulns["vulns"]]
    if open_advisories and facts["change"] != "removed":
        reach = facts["call_sites_summary"]["reachable"]
        conf = 0.9 if reach == "true" else 0.75
        findings.append(_finding("security", conf, f"{pkg} {facts['new_version']} has {len(open_advisories)} open advisor{'y' if len(open_advisories) == 1 else 'ies'} at head; reachable={reach}",
                                 f"analyze/{pkg}/vulns.json", pkg, advisories=sorted({a for v in open_advisories for a in v['aliases'] if a.startswith('CVE-')})))
    used = set(facts["call_sites_summary"]["symbols_used"])
    breaking_used = [s for s in facts["api_diff_summary"].get("breaking_symbols", []) if any(u == s or u.startswith(s + ".") or s.startswith(u) for u in used)]
    if breaking_used:
        findings.append(_finding("undocumented-change", 0.8, f"{len(breaking_used)} breaking API change(s) touch symbols the application uses",
                                 f"analyze/{pkg}/api-diff.json", pkg, symbols=breaking_used[:20]))
    if facts["risk"]["inputs"].get("preflight_hit"):
        findings.append(_finding("suspicious", 0.95, "pre-flight gate hit", f"intake/worklist.json", pkg))

    # Test-level classification from stage 4.
    if results:
        for t in results["tests"]:
            v = t["verdict"]
            if t["status"] == "flaky":
                cls, conf, action = "test-bug", 0.95, "discard"
            elif v.startswith("fix-pinning confirmed"):
                cls, conf, action = "behavior-change", 0.95, "accept as CVE evidence; VEX status fixed"
            elif v.startswith("exposure confirmed"):
                cls, conf, action = "security", 0.95, "accept as CVE evidence; VEX status affected: the change introduces the exposure"
            elif v.startswith("candidate"):
                cls, conf, action = "behavior-change", 0.85, "accept as characterization candidate" if "same on old" in v else "accept as candidate"
            elif v.startswith("behavior changed"):
                cls, conf, action = "undocumented-change", 0.7, "reviewer decides"
            elif v.startswith("blocked on both"):
                cls, conf, action = "defect", 0.8, "open issue; reproducer is the test; advisory stays under investigation"
            elif v.startswith("fix reached"):
                cls, conf, action = "test-bug", 0.9, "regenerate with the fix-reached hint"
            elif v.startswith("not a fix-pinning test"):
                cls, conf, action = "test-bug", 0.8, "discard as CVE evidence; keep as characterization only if reviewer wants it"
            elif v.startswith("fails on the fixed version") or v.startswith("fails on head"):
                cls, conf, action = "test-bug", 0.75, "regenerate or discard"
            else:
                cls, conf, action = "test-bug", 0.5, "escalate"
            tests.append({"test_id": t["id"], "name": t["name"], "category": t["category"], "class": cls, "confidence": conf,
                          "action": action, "verdict": v, "versions": t["versions"], "escalated": conf < THRESHOLD,
                          "evidence_ref": f"execute/{pkg}/results.json"})
    # Candidate defects the agent recorded (blocked paths). A deterministic signal must corroborate:
    # stage 4 has to show a test for that issue blocked on both versions. Otherwise the finding is
    # escalated at low confidence, never auto-routed as a defect.
    for cd in (agent or {}).get("candidate_defects", []):
        issue_key = cd["issue"].lower().replace("-", "_")
        corroborated = [t for t in tests if t["verdict"].startswith("blocked on both") and
                        (issue_key in t["name"] or any(a.lower().replace("-", "_") in t["name"] for a in _aliases_for(vulns, cd["issue"])))]
        conf = 0.8 if corroborated else 0.4
        findings.append(_finding("defect", conf, f"{pkg}: a code path raised the same internal error on both versions during CVE test generation ({cd['issue']})"
                                 + ("" if corroborated else "; NOT corroborated by stage 4 verdicts"),
                                 f"generate/{pkg}/manifest.agent.json", pkg, reproducer=cd["blocked_paths"][0][:200],
                                 corroborating_tests=[t["name"] for t in corroborated]))
    # Advisory pairing: a confirmed fix-pinning test for one issue is evidence for any other advisory in the same fix.
    confirmed = [t for t in tests if t["action"].startswith("accept as CVE evidence")]
    out = {"package": pkg, "generated": now_iso(), "threshold": THRESHOLD, "findings": findings, "tests": tests,
           "summary": {"findings": len(findings), "escalated": sum(1 for f in findings if f["escalated"]) + sum(1 for t in tests if t["escalated"]),
                       "tests_accept": sum(1 for t in tests if t["action"].startswith("accept")),
                       "tests_discard_or_regenerate": sum(1 for t in tests if not t["action"].startswith("accept")),
                       "cve_confirmed": len(confirmed),
                       "blocking": [f["class"] for f in findings if f["class"] in ("suspicious",) and not f["escalated"]]}}
    write_json(workdir / "triage" / pkg / "triage.json", out)
    s = out["summary"]
    log(f"    {pkg}: {s['findings']} findings, {s['tests_accept']} tests to accept, {s['tests_discard_or_regenerate']} to discard/regenerate, {s['escalated']} escalated")
    return out


def triage(*, workdir: Path, select: list[str] | None = None) -> list[dict]:
    from .. import selfcheck
    selfcheck.require(workdir, probes=False)
    summary = read_json(workdir / "analyze" / "summary.json")
    outs = []
    for item in summary["items"]:
        if select and item["package"] not in select:
            continue
        outs.append(triage_package(workdir, item["package"]))
    from ..util import merge_summary
    merge_summary(workdir / "triage" / "summary.json", [{"package": o["package"], **o["summary"]} for o in outs])
    return outs
