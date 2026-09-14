"""Stage 4, step 7: the relevance engine. Blueprint section 8.4 and workflow 9.

Which existing tests does this change make irrelevant? The engine proposes, with evidence; a person
approves; nothing is deleted. Signals, using only data the run already has:

- obsolete-symbol-removed: a test references a package symbol the API diff removed or whose required
  parameters changed. When a symbol with the same short name was added, the test is a rewrite
  candidate, not a retirement.
- redundant-no-kills: a passing test killed no sampled mutant in this run. Advisory at n=1; the
  blueprint asks for the last N runs, and this stage says how many runs it has seen.
- redundant-subsumed: a test's killed-mutant set is a non-empty strict subset of another test's.
  Per-test coverage is not collected yet, so this is kills only, and says so.
- redundant-skipped: a test carries a skip marker.

Two populations are examined: the tests this run generated (the overlay), and the application's own
tests that reference the package (human-written; routed to the owning team at lower priority).
For a package the change did not move but a fixed candidate exists for, the diff is head to
candidate, and a proposal reads "will become obsolete when the upgrade lands".
"""
from __future__ import annotations

from pathlib import Path

from .. import adapters, config
from ..util import log, now_iso, read_json, write_json

REASONS = ("obsolete-symbol-removed", "obsolete-path-deleted", "obsolete-behavior-changed",
           "redundant-no-kills", "redundant-subsumed", "redundant-skipped")


def _matches(symbol: str, changed: set[str]) -> str | None:
    """A referenced symbol is affected when it IS a changed symbol or lives UNDER one (a removed
    module takes its members with it). A reference to a module is not affected because some other
    member of that module changed."""
    for c in changed:
        if symbol == c or symbol.startswith(c + "."):
            return c
    return None


def relevance_package(workdir: Path, pkg: str, python_version: str, repo: str | None = None) -> dict:
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    adapter = adapters.get(read_json(workdir / "intake" / "worklist.json").get("ecosystem", "python"))
    roots = adapter.import_roots(facts)
    out = workdir / "execute" / pkg / "relevance.json"
    # The API diff this change implies: bump (old -> new), or head -> fixed candidate.
    diff_path = workdir / "analyze" / pkg / "api-diff.json"
    cand_path = workdir / "analyze" / pkg / "fixed-candidate.json"
    horizon = "this change"
    changes = []
    if diff_path.exists():
        changes = read_json(diff_path)["changes"]
    elif cand_path.exists() and read_json(cand_path).get("status") == "resolved":
        cand = read_json(cand_path)
        cache = workdir / "cache"
        head_api = read_json(workdir / "analyze" / pkg / "api.new.json")["symbols"] if (workdir / "analyze" / pkg / "api.new.json").exists() else []
        unpacked = adapter.unpack(adapter.fetch(pkg, cand["fixed_version"], cache, python_version), cache)
        cand_api = adapter.extract_api(unpacked, adapter.import_names(unpacked, pkg))
        from ..model import ApiSymbol
        head_syms = [ApiSymbol(**s) for s in head_api]
        changes = [vars(c) for c in adapter.api_diff(head_syms, cand_api)]
        horizon = f"the upgrade to {cand['fixed_version']}"
    removed = {c["symbol"] for c in changes if c["kind"] == "removed"}
    breaking_changed = {c["symbol"] for c in changes if c["kind"] == "changed" and c.get("breaking")}
    added_short = {c["symbol"].rsplit(".", 1)[-1] for c in changes if c["kind"] == "added"}
    gone = removed | breaking_changed

    # Populations: this run's generated tests, and the application's own tests.
    populations = []
    gen_tests = workdir / "generate" / pkg / "tests"
    if gen_tests.exists():
        populations.append(("generated", sorted(gen_tests.glob(adapter.TEST_FILE_GLOB)), gen_tests))
    wl = read_json(workdir / "intake" / "worklist.json")
    repo = config.resolve_repo(wl["source_dir"], repo)
    app_tests = [p for p in adapter.first_party_files(repo) if adapter.is_test_file(p.relative_to(repo))]
    populations.append(("application", app_tests, repo))

    mut_path = workdir / "execute" / pkg / "mutation" / "mutation.json"
    mutation = read_json(mut_path) if mut_path.exists() else None
    per_test = (mutation or {}).get("per_test", {})
    passing = set((mutation or {}).get("tests", []))
    res_path = workdir / "execute" / pkg / "results.json"
    results = read_json(res_path) if res_path.exists() else {"tests": []}
    by_name = {t["name"]: t for t in results["tests"]}

    proposals, examined = [], {"generated": 0, "application": 0, "application_files_referencing_package": 0}
    for pop, files, base in populations:
        for f in files:
            refs = adapter.symbol_refs(f, roots)
            if not refs:
                continue
            if pop == "application":
                examined["application_files_referencing_package"] += 1
            skipped = adapter.skipped_tests(f)
            for test, symbols in refs.items():
                examined[pop] += 1
                rel = str(f.relative_to(base))
                human = pop == "application"
                for sym, line in symbols:
                    hit = _matches(sym, gone)
                    if hit:
                        short = hit.rsplit(".", 1)[-1]
                        rewrite = short in added_short
                        proposals.append({"test": test, "file": rel, "population": pop, "human_written": human,
                                          "class": "obsolete", "reason": "obsolete-symbol-removed",
                                          "horizon": horizon, "rewrite_candidate": rewrite,
                                          "evidence": {"symbol": sym, "line": line, "api_change": hit,
                                                       "kind": "removed" if hit in removed else "required parameters changed"},
                                          "priority": "low" if human else "normal",
                                          "text": (f"{test} references {sym}, which {horizon} {'removes' if hit in removed else 'changes the required parameters of'}"
                                                   + (f"; a symbol named {short} was added, so this is a rewrite candidate" if rewrite else ""))})
                        break
                if test in skipped:
                    proposals.append({"test": test, "file": rel, "population": pop, "human_written": human, "class": "redundant",
                                      "reason": "redundant-skipped", "horizon": horizon, "rewrite_candidate": False,
                                      "evidence": {"marker": "skip or xfail"}, "priority": "low" if human else "normal",
                                      "text": f"{test} carries a skip or xfail marker"})
                # Redundancy by mutant kills applies to characterization tests only: a CVE test's value is
                # the differential between versions, not the mutants it happens to kill.
                if pop == "generated" and mutation and test in passing and by_name.get(test, {}).get("category") != "cve":
                    kills = set(per_test.get(test, {}).get("killed", []))
                    if not kills:
                        proposals.append({"test": test, "file": rel, "population": pop, "human_written": False, "class": "redundant",
                                          "reason": "redundant-no-kills", "horizon": horizon, "rewrite_candidate": False,
                                          "evidence": {"mutants_sampled": mutation.get("sampled"), "runs_seen": 1, "note": "blueprint asks for the last N runs; this is n=1, advisory"},
                                          "priority": "low", "text": f"{test} killed none of {mutation.get('sampled')} sampled mutants in this run"})
                    elif kills:
                        for other, pt in per_test.items():
                            oth = set(pt.get("killed", []))
                            if other != test and kills < oth:
                                proposals.append({"test": test, "file": rel, "population": pop, "human_written": False, "class": "redundant",
                                                  "reason": "redundant-subsumed", "horizon": horizon, "rewrite_candidate": False,
                                                  "evidence": {"killed": sorted(kills), "subsumed_by": other, "its_kills": sorted(oth),
                                                               "note": "kills only; per-test coverage not collected yet"},
                                                  "priority": "low", "text": f"{test}'s {len(kills)} mutant kill(s) are all among {other}'s {len(oth)}"})
                                break
    # de-duplicate
    seen, uniq = set(), []
    for p in proposals:
        k = (p["test"], p["file"], p["reason"])
        if k not in seen:
            seen.add(k); uniq.append(p)
    rec = {"package": pkg, "generated": now_iso(), "horizon": horizon, "api_changes_considered": {"removed": len(removed), "breaking_changed": len(breaking_changed), "added": len(added_short)},
           "examined": examined, "proposals": uniq, "reasons": list(REASONS),
           "rule": "the harness proposes with evidence; a person approves; a retired test is kept, re-run once on the next change, never deleted; proposals never block a merge",
           "counts": {"obsolete": sum(1 for p in uniq if p["class"] == "obsolete"), "redundant": sum(1 for p in uniq if p["class"] == "redundant"),
                      "rewrite_candidates": sum(1 for p in uniq if p["rewrite_candidate"]), "human_written": sum(1 for p in uniq if p["human_written"])}}
    write_json(out, rec)
    c = rec["counts"]
    log(f"    {pkg}: horizon {horizon}; {examined['generated']} generated + {examined['application']} application test(s) examined; "
        f"{c['obsolete']} obsolete, {c['redundant']} redundant, {c['rewrite_candidates']} rewrite candidate(s)")
    return rec


def relevance(*, workdir: Path, select: list[str] | None = None, python_version: str = "3.12", repo: str | None = None) -> list[dict]:
    from .. import selfcheck
    from ..util import merge_summary
    selfcheck.require(workdir, python_version, probes=False)
    pkgs = [p["package"] for p in read_json(workdir / "execute" / "summary.json")["packages"]] if (workdir / "execute" / "summary.json").exists() else []
    outs = [relevance_package(workdir, p, python_version, repo) for p in pkgs if not select or p in select]
    merge_summary(workdir / "execute" / "relevance-summary.json", [{"package": o["package"], **o["counts"], "horizon": o["horizon"]} for o in outs])
    return outs
