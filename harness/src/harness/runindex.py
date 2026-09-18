"""run-index.json: what a run directory holds, so a reader or a renderer never has to know the layout.

Written at the end of every stage. Lists the run's identity, which stages have written, every package
with the files each stage produced for it, and the headline numbers, each read from the file that
holds it. Nothing here is computed that is not already in a record; the index only says where.
"""
from __future__ import annotations

from pathlib import Path

from . import __version__
from .util import now_iso, read_json, write_json

STAGES = ("selfcheck", "intake", "analyze", "generate", "execute", "triage", "packet", "attest", "assess", "propose", "feedback")

# Every artifact the harness writes, who it is for, and why it exists. The story and the site's
# catalogue are generated from this table, so a file is never present without a reason a person can read.
# Audiences: everyone, reviewer, security (Product Security), audit (Supply Chain Security, auditors),
# developer (the person who ran it), machine (consumed by tools; kept for replay and proof).
CATALOGUE = {
    "README.md": ("everyone", "The story of this run: who, what, why, where, when, the outcome, the decisions and the actions."),
    "run.json": ("audit", "What was run, with which tool versions, on which repository by name."),
    "run-index.json": ("machine", "What this run holds: stages, packages, headline numbers, and where every file is; the renderers read it."),
    "selfcheck/selfcheck.json": ("audit", "Stage 0: every failure-register check and the sandbox and model probes, before any evidence was produced."),
    "intake/worklist.json": ("reviewer", "The work list: every package at base and head, what changed, what is reachable, what carries advisories."),
    "intake/graph.new.json": ("machine", "The dependency graph at head as the ecosystem's own resolver produced it."),
    "intake/graph.old.json": ("machine", "The dependency graph at base."),
    "intake/sbom.new.cdx.json": ("audit", "The software bill of materials at head, CycloneDX."),
    "intake/vulns.json": ("security", "Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports."),
    "analyze/facts.json": ("reviewer", "The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned."),
    "analyze/vulns.json": ("security", "The advisories on this package's versions, with the symbols they name and the fixed versions."),
    "analyze/api-diff.json": ("reviewer", "Every added, removed or changed public symbol between the two versions, with a breaking flag."),
    "analyze/fixed-candidate.json": ("security", "When the change left a vulnerable version in place: the environment the harness resolved with the fixed version, and what had to move."),
    "analyze/api.new.json": ("machine", "The public API surface at head, extracted by tools."),
    "analyze/api.old.json": ("machine", "The public API surface at base."),
    "analyze/call-sites.json": ("machine", "Every place the application references this package."),
    "analyze/source-diff.patch": ("developer", "The package's own source diff between the versions; the model reads it to find the fix."),
    "analyze/notes.untrusted.md": ("developer", "Package metadata and description as published upstream; untrusted text, kept for context."),
    "generate/manifest.json": ("developer", "What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests."),
    "generate/manifest.agent.json": ("developer", "The tool-using agent's traces: every tool call per advisory, and the budget it had."),
    "generate/tests/": ("reviewer", "The candidate test files as generated, before any decision."),
    "generate/model-calls/": ("audit", "Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said."),
    "generate/scratch/": ("machine", "Every attempt that ran in the sandbox during generation, with its output; not committed."),
    "execute/results.json": ("reviewer", "The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged."),
    "execute/new/": ("machine", "The sealed run on head: the run script, the junit report, coverage, logs."),
    "execute/new-rerun/": ("machine", "The second run on head, to catch flakes."),
    "execute/old/": ("machine", "The run on the base version, for the differential."),
    "execute/fixed-candidate/": ("machine", "The run on the resolved fixed version, for the differential when the change did not move the package."),
    "execute/mutation/mutation.json": ("reviewer", "How strong the accepted tests are: which mutants of the package's source they killed, and the score."),
    "execute/mutation/mutants/": ("machine", "Each sampled mutant: the mutated file and its sealed run."),
    "execute/relevance.json": ("reviewer", "Which existing tests this change makes obsolete or redundant, proposed with evidence; nothing is deleted."),
    "triage/triage.json": ("reviewer", "Every verdict and finding classified, with a confidence and a route; below the threshold a person decides."),
    "packet/packet.md": ("reviewer", "The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action."),
    "packet/packet.json": ("machine", "The packet's facts in structured form."),
    "packet/tests.patch": ("reviewer", "The accepted tests as a patch in the layout they will live in."),
    "packet/vex.openvex.json": ("security", "One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness."),
    "packet/pull-request.md": ("reviewer", "The text and the file list the test pull request carries, whether or not one was opened."),
    "attest/MANIFEST.json": ("audit", "The provenance record per accepted test: model, prompt and response digests, sandbox image digest, verdicts."),
    "attest/statement.json": ("audit", "The in-toto test-result statement; its subjects are the patch, the record and each evidence record's head."),
    "attest/statement.dsse.json": ("audit", "The statement signed as a DSSE envelope."),
    "attest/signer.pub.pem": ("audit", "The public key that verifies the envelope."),
    "attest/attest.json": ("audit", "Which key signed, whether it verified locally, and what the run could not back."),
    "attest/udlm/": ("audit", "The same facts as sealed UDLM records: the vulnerability, the package, the run, each accepted test, the draft VEX."),
    "assess/assess.md": ("everyone", "The run against the blueprint's eleven goals, each with the measurement and the file it came from."),
    "assess/assess.json": ("machine", "The assessment in structured form."),
    "propose/proposal.json": ("audit", "The branch, the commit, the files and the pull request the harness opened; the signature status."),
    "propose/pull-request.md": ("reviewer", "The pull request's text as posted."),
    "feedback/acceptance.json": ("audit", "What a person accepted, edited or rejected on the pull request, and who and when."),
    "feedback/decisions.jsonl": ("machine", "One labeled example per test for prompt evaluation: the decision with the prompt and response digests behind it."),
    "feedback/acceptance-statement.dsse.json": ("audit", "The signed acceptance statement naming the merge commit and each realized record."),
    "feedback/udlm/": ("audit", "The requested and realized records for every accepted test: the reviewer's act, and the test as it landed."),
}


def catalogue_for(workdir: Path, packages: list[str]) -> list[dict]:
    """Every file or directory of this run that the catalogue names, with its audience and purpose."""
    out = []
    for key, (aud, why) in CATALOGUE.items():
        if "/" not in key or key.startswith(("selfcheck/", "intake/", "assess/")):
            if (workdir / key).exists():
                out.append({"path": key, "audience": aud, "purpose": why})
            continue
        stage, rel = key.split("/", 1)
        for pkg in packages:
            if (workdir / stage / pkg / rel).exists():
                out.append({"path": f"{stage}/{pkg}/{rel}", "package": pkg, "audience": aud, "purpose": why})
    return out


def _load(p: Path):
    return read_json(p) if p.exists() else None


def _packages(workdir: Path) -> list[str]:
    names: list[str] = []
    for stage in ("analyze", "generate", "execute", "triage", "packet", "attest", "propose", "feedback"):
        summ = _load(workdir / stage / "summary.json")
        rows = (summ or {}).get("items") or (summ or {}).get("packages") or []
        for r in rows:
            if r.get("package") and r["package"] not in names:
                names.append(r["package"])
    return names


def build(workdir: Path) -> dict:
    wl = _load(workdir / "intake" / "worklist.json") or {}
    run = _load(workdir / "run.json") or {}
    gen = _load(workdir / "generate" / "summary.json") or {}
    stages = {}
    for st in STAGES:
        present = (workdir / st).is_dir() and any((workdir / st).iterdir())
        summ = _load(workdir / st / "summary.json") or (_load(workdir / st / f"{st}.json") if st in ("selfcheck", "assess") else None) or {}
        rows = summ.get("items") or summ.get("packages") or []
        # A small, honest per-stage summary for a timeline: when it wrote, how many rows, and the scalar facts it recorded.
        brief = {k: v for k, v in summ.items() if isinstance(v, (str, int, float, bool)) and k not in ("generated",)}
        if st == "selfcheck":
            brief = {"checks": len(summ.get("checks", [])), "passed": summ.get("passed"),
                     "sandbox": (summ.get("sandbox") or {}).get("status"), "model": (summ.get("model") or {}).get("status")}
        if st == "assess":
            brief = dict(summ.get("summary") or {})
        stages[st] = {"present": present, "generated": summ.get("generated"), "rows": len(rows) if rows else None, "summary": brief}
    if stages["intake"]["present"]:
        g_new = _load(workdir / "intake" / "graph.new.json") or {}; g_old = _load(workdir / "intake" / "graph.old.json") or {}
        stages["intake"]["summary"] = {"packages_at_head": len(g_new.get("packages", {})), "packages_at_base": len(g_old.get("packages", {})),
                                       "work_list_rows": len(wl.get("items", [])),
                                       "with_advisories_at_head": sum(1 for i in wl.get("items", []) if i.get("vulns_new")),
                                       "changed": sum(1 for i in wl.get("items", []) if i.get("change") in ("added", "removed", "bumped")),
                                       "resolver": g_new.get("resolver")}
    packages = []
    for pkg in _packages(workdir):
        if not any((workdir / st / pkg).exists() for st in ("analyze", "generate", "execute", "triage", "packet", "attest")):
            continue   # a summary row carried over from another run; nothing of it is here
        p = workdir
        files = {}
        def has(stage: str, rel: str, key: str | None = None):
            path = p / stage / pkg / rel
            if path.exists():
                files[key or f"{stage}/{rel}"] = f"{stage}/{pkg}/{rel}"
        has("analyze", "facts.json"); has("analyze", "vulns.json"); has("analyze", "api-diff.json"); has("analyze", "fixed-candidate.json")
        has("generate", "manifest.json"); has("generate", "manifest.agent.json")
        has("execute", "results.json"); has("execute", "mutation/mutation.json", "execute/mutation.json"); has("execute", "relevance.json")
        has("triage", "triage.json"); has("packet", "packet.md"); has("packet", "packet.json"); has("packet", "tests.patch"); has("packet", "vex.openvex.json")
        has("attest", "MANIFEST.json"); has("attest", "statement.json"); has("attest", "statement.dsse.json"); has("attest", "signer.pub.pem"); has("attest", "attest.json"); has("attest", "udlm/index.json")
        has("propose", "proposal.json"); has("feedback", "acceptance.json"); has("feedback", "acceptance-statement.dsse.json"); has("feedback", "udlm/index.json")
        res = _load(p / "execute" / pkg / "results.json") or {}
        tri = _load(p / "triage" / pkg / "triage.json") or {}
        mut = _load(p / "execute" / pkg / "mutation" / "mutation.json") or {}
        att = _load(p / "attest" / pkg / "attest.json") or {}
        facts = _load(p / "analyze" / pkg / "facts.json") or {}
        fb = _load(p / "feedback" / pkg / "acceptance.json") or {}
        prop = _load(p / "propose" / pkg / "proposal.json") or {}
        c = res.get("counts", {})
        packages.append({
            "package": pkg, "first_party": bool(facts.get("first_party")), "old_version": facts.get("old_version"), "new_version": facts.get("new_version"),
            "change": facts.get("change"), "depth": facts.get("depth"), "budget": (facts.get("risk") or {}).get("budget", {}).get("level"),
            "advisories": (facts.get("vulns_summary") or {}).get("count"),
            "tests": {"generated": sum(len(f.get("tests", [])) for f in (_load(p / "generate" / pkg / "manifest.json") or {}).get("files", [])),
                      "ran": c.get("total"), "pass_on_head": c.get("pass_on_new"), "flaky": c.get("flaky"), "proven": c.get("fix_pinning_confirmed"),
                      "accepted": (tri.get("summary") or {}).get("tests_accept")},
            "mutation": {"status": mut.get("status"), "score": mut.get("score"), "sampled": mut.get("sampled"), "killed": mut.get("killed")} if mut else None,
            "attestation": {"result": att.get("result"), "keyid": att.get("keyid")} if att else None,
            "proposal": {"status": prop.get("status"), "pull_request": prop.get("pull_request")} if prop else None,
            "review": {"outcome": fb.get("outcome"), **fb.get("counts", {})} if fb else None,
            "files": files,
        })
    ass = _load(workdir / "assess" / "assess.json") or {}
    return {"format": "ai-test-harness/run-index/v1", "catalogue": catalogue_for(workdir, [p["package"] for p in packages]), "harness_version": __version__, "updated": now_iso(),
            "run_id": wl.get("run_id"), "repository": wl.get("repository") or wl.get("source_dir"), "ecosystem": wl.get("ecosystem", "python"), "mode": wl.get("mode"),
            "base": (wl.get("old_manifest") or "").split("@")[-1] or None, "head": (wl.get("new_manifest") or "").split("@")[-1] or None,
            "started": run.get("started"), "model": gen.get("model"), "generation_mode": gen.get("mode"),
            "stages": stages, "packages": packages,
            "goals": (ass.get("summary") if ass else None),
            "files": {k: v for k, v in {"run": "run.json", "selfcheck": "selfcheck/selfcheck.json", "worklist": "intake/worklist.json", "sbom": "intake/sbom.new.cdx.json",
                                        "assess": "assess/assess.md"}.items() if (workdir / v).exists()}}


def update(workdir: Path) -> Path:
    out = workdir / "run-index.json"
    write_json(out, build(workdir))
    return out
