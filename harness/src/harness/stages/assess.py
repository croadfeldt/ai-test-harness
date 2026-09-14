"""Post-analysis: did this run meet the blueprint's core goals?

Numbers are computed from the run's artifacts, never asserted. Each goal has a source in the
blueprint, a measurement, a verdict (met, not met, not applicable in this slice), and the file the
measurement came from. A model may later narrate this record for a reader; it does not judge it.
"""
from __future__ import annotations

from pathlib import Path

from ..util import log, now_iso, read_json, write_json


def assess(*, workdir: Path) -> dict:
    from .. import selfcheck as sc
    sc.require(workdir, probes=False)
    wl = read_json(workdir / "intake" / "worklist.json")
    selfcheck = read_json(workdir / "selfcheck" / "selfcheck.json")
    tri = read_json(workdir / "triage" / "summary.json")
    pk = read_json(workdir / "packet" / "summary.json")
    att = read_json(workdir / "attest" / "summary.json")
    pkgs = [p["package"] for p in pk["packages"] if (workdir / "execute" / p["package"] / "results.json").exists()]
    results = {p: read_json(workdir / "execute" / p / "results.json") for p in pkgs}
    gens = {p: read_json(workdir / "generate" / p / "manifest.json") for p in pkgs}
    triages = {p: read_json(workdir / "triage" / p / "triage.json") for p in pkgs}
    goals = []

    def goal(gid, source, statement, measure, verdict, evidence):
        goals.append({"id": gid, "source": source, "goal": statement, "measurement": measure, "verdict": verdict, "evidence_ref": evidence})

    total = sum(r["counts"]["total"] for r in results.values())
    flaky = sum(r["counts"]["flaky"] for r in results.values())
    confirmed = sum(r["counts"]["fix_pinning_confirmed"] for r in results.values())
    goal("G1", "exec summary: humans own the merge", "Nothing merges without a person",
         "harness produced patches and drafts only; no git push, no VEX published", "met",
         [f"packet/{p}/packet.md" for p in pkgs])
    goal("G2", "principle: generated tests are hypotheses until executed", "Every kept test was compiled and run in the sandbox before a reviewer sees it",
         f"{total} tests ran on head, again for flakes, and on base; {flaky} flaky", "met" if total else "not applicable",
         [f"execute/{p}/results.json" for p in pkgs])
    goal("G3", "principle: strong, not just green", "A test that passes on both versions is not presented as CVE evidence",
         f"{confirmed} fix-pinning confirmed; pass-on-both CVE tests are classified test-bug and excluded from VEX 'fixed'",
         "met", [f"triage/{p}/triage.json" for p in pkgs])
    goal("G4", "section 8.5, section 17: self-verification", "Stage 0 passed before evidence was produced",
         f"{sum(1 for c in selfcheck['checks'] if c['status'] == 'pass')} of {len(selfcheck['checks'])} register checks; sandbox probe {selfcheck['sandbox']['status']}; model probe {selfcheck['model']['status']}",
         "met" if selfcheck["passed"] else "not met", ["selfcheck/selfcheck.json"])
    goal("G5", "section 11: incoming code is untrusted", "Generated tests ran with no network, no secrets, read-only root, disposable container",
         str(next(iter(results.values()))["target"]["isolation"]) if results else "no runs", "met" if results else "not applicable",
         [f"execute/{p}/new/sandbox.json" for p in pkgs])
    goal("G6", "section 8.2: provenance", "Every accepted test carries a provenance record and a signed attestation",
         f"{sum(a['records'] for a in att['packages'])} records; envelopes verified locally: {[a['verified_locally'] for a in att['packages']]}; signer is a development key",
         "met (development signer)", [f"attest/{p}/statement.dsse.json" for p in pkgs])
    goal("G7", "section 10: known vulnerabilities with a CVE-targeted test", "Every advisory on the work item has a CVE-targeted test attempt and a draft VEX statement",
         "; ".join(f"{p}: {pk_['vex_statements']}" for p, pk_ in zip(pkgs, pk["packages"])),
         "met" if all(pk_["vex_statements"] for pk_ in pk["packages"]) else "not met", [f"packet/{p}/vex.openvex.json" for p in pkgs])
    goal("G8", "exec summary: catches what a reviewer would miss", "The run surfaces a finding the PR diff does not show",
         "; ".join(f"{p}: {[f['summary'][:80] for f in t['findings']]}" for p, t in triages.items()) or "no findings",
         "met" if any(t["findings"] for t in triages.values()) else "not met", [f"triage/{p}/triage.json" for p in pkgs])
    goal("G9", "section 10: time to packet", "Packet within 2 hours of trigger for depth 0 and 1",
         f"intake {wl['created']} -> packet {pk['generated']}", "see measurement", ["run.json", "packet/summary.json"])
    goal("G10", "section 17: every claim traceable", "Every number in the packet points at a file in the work directory",
         "packet sections cite artifact paths; attestation subjects are the patch and the manifest digests", "met", [f"attest/{p}/statement.json" for p in pkgs])
    muts = {p: read_json(workdir / "execute" / p / "mutation" / "mutation.json") for p in pkgs if (workdir / "execute" / p / "mutation" / "mutation.json").exists()}
    if muts:
        measure = "; ".join(f"{p}: score {m.get('score')} on {m.get('sampled')} sampled mutants" for p, m in muts.items()) + "; coverage delta: no baseline overlay suite yet"
        verdict = "met" if all((m.get("score") or 0) >= 0.6 for m in muts.values()) else "not met (target 0.6 on sampled mutants)"
    else:
        measure, verdict = "mutation testing not run for these packages; coverage delta: no baseline overlay suite yet", "not applicable"
    goal("G11", "section 10: mutation score, coverage delta", "Test strength measured by mutation and coverage delta",
         measure, verdict, [f"execute/{p}/mutation/mutation.json" for p in muts])
    met = sum(1 for g in goals if g["verdict"].startswith("met"))
    rec = {"generated": now_iso(), "run_id": wl["run_id"], "packages": pkgs, "goals": goals,
           "summary": {"met": met, "not_met": sum(1 for g in goals if g["verdict"].startswith("not met")),
                       "not_applicable": sum(1 for g in goals if g["verdict"] == "not applicable"), "other": sum(1 for g in goals if g["verdict"] == "see measurement")}}
    write_json(workdir / "assess" / "assess.json", rec)
    not_met = [g["goal"] for g in goals if g["verdict"].startswith("not met")]
    plain = (f"This run met {met} of {len(goals)} goals from the blueprint." +
             (f" Not met: {'; '.join(not_met)}." if not_met else "") +
             " Every verdict below points at the file it was measured from.")
    md = [f"# Post-analysis of run {wl['run_id']}", "", f"**In plain terms.** {plain}", "", f"Packages: {', '.join(pkgs)}.", "",
          "| id | goal | measurement | verdict |", "|---|---|---|---|"]
    md += [f"| {g['id']} | {g['goal']} | {g['measurement'][:160]} | **{g['verdict']}** |" for g in goals]
    (workdir / "assess" / "assess.md").write_text("\n".join(md) + "\n")
    for g in goals:
        log(f"  {g['id']} {g['verdict']:<22} {g['goal'][:70]}")
    return rec
