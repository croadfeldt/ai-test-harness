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
    return {"format": "ai-test-harness/run-index/v1", "harness_version": __version__, "updated": now_iso(),
            "run_id": wl.get("run_id"), "repository": wl.get("source_dir"), "ecosystem": wl.get("ecosystem", "python"), "mode": wl.get("mode"),
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
