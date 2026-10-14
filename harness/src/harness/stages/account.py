"""The accounting (blueprint principle 14): every behaviour the change reaches ends in exactly one state.

The three states are `validated`, `for-your-environment` and `stated-gap`; a gap carries exactly one
reason. Nothing is silent: every reached behaviour appears once, the counts sum to the number of units,
and a unit without a state is a harness defect (assessment goal G13).

A unit is a reached behaviour. For a dependency it is each distinct call-site symbol outside test files
that resolves to a public function, method or type of the package, re-exports resolved to their
definition; a bare module import is not a unit. For a first-party change it is each added or changed
public symbol; for a rescan with no change, every public symbol, those beyond the budget recorded as
`out-of-budget` rather than dropped. A type's behaviours are its public methods; a type with none is
listed as excluded, because its behaviour is the functions that raise or return it.

A unit's lines are its closure: its own span plus the private functions and methods it delegates to,
transitively, within the module (`analyze/<pkg>/internals.json`). Execution is attributed per test when
the sandbox recorded coverage contexts (one label per test function), else from the run's aggregate
coverage; the record says which. Strength is a mutant sampled inside the closure and killed by a kept
test that executed the unit. Mutation sampling is stratified over the reached units (`mutate.py`) so a
reached behaviour gets a mutant before the rest of the package does. docs/18 records the dry run that
showed why.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..util import log, now_iso, read_json, write_json

STATES = ("validated", "for-your-environment", "stated-gap")
REASONS = {
    "pipeline-cannot-validate": "the repository's CI cannot run or validate the proposed tests",
    "no-test-generated": "no kept test names or executes this behaviour",
    "did-not-build": "every candidate for this behaviour failed to compile or collect",
    "flaky": "the only tests for this behaviour disagreed with themselves",
    "failed-on-head": "the tests for this behaviour are wrong",
    "executed-not-checked": "lines ran, no mutant inside them was killed",
    "strength-not-sampled": "lines ran, no mutant was placed inside them; a sampling gap the harness owns",
    "not-in-public-api": "the application references a name the package's public API does not define",
    "out-of-budget": "beyond this run's budget; recorded so it is not forgotten",
}
TYPE_KINDS = ("class", "struct", "type", "interface")
BEHAVIOUR_KINDS = ("function", "method")
ENVIRONMENT = re.compile(r"permission denied|operation not permitted|name or service not known|temporary failure in name resolution|"
                         r"network is unreachable|connection refused|no such device|read-only file system|address family not supported", re.I)
RESCAN_BUDGET = 60
# Pipeline rules that mean the proposed tests cannot run or be validated where the repository runs them.
CANNOT_VALIDATE_RULES = ("P-00",)


def _last(name: str) -> str:
    return name.rsplit(".", 1)[-1]


def _spans(symbols: list[dict]) -> dict[str, tuple[str, int, int | None]]:
    """Each symbol's file and line span. Without an end line, the span runs to the next symbol in the file."""
    by_file: dict[str, list[dict]] = {}
    for s in symbols:
        by_file.setdefault(s["file"], []).append(s)
    out = {}
    for f, syms in by_file.items():
        syms = sorted(syms, key=lambda s: s["line"])
        for i, s in enumerate(syms):
            if s["kind"] == "module":
                continue
            end = s.get("end_line")
            if not end:
                # a method's span ends at the next symbol; a class's at the next symbol that is not its own method
                nxt = next((n for n in syms[i + 1:] if not (s["kind"] in TYPE_KINDS and n["qualname"].startswith(s["qualname"] + "."))), None)
                end = nxt["line"] - 1 if nxt else None
            out[s["qualname"]] = (f, s["line"], end)
    return out


def load_internals(workdir: Path, pkg: str) -> dict:
    p = workdir / "analyze" / pkg / "internals.json"
    doc = read_json(p) if p.exists() else {}
    return {"private": doc.get("private") or [], "calls": doc.get("calls") or {}}


def closure(q: str, calls: dict[str, list[str]]) -> list[str]:
    """The unit and every private callee it reaches, transitively, in a stable order."""
    out, todo = [], [q]
    while todo:
        x = todo.pop(0)
        if x in out:
            continue
        out.append(x)
        todo += [c for c in calls.get(x, []) if c not in out]
    return out


def closure_spans(q: str, spans: dict[str, tuple[str, int, int | None]], calls: dict[str, list[str]]) -> list[tuple[str, str, int, int | None]]:
    """(qualname, file, start, end) for the unit and its private callees that have a span."""
    return [(x, *spans[x]) for x in closure(q, calls) if x in spans]


def _in(span: tuple[str, int, int | None], f: str, line: int) -> bool:
    sf, a, b = span
    return sf == f and a <= line <= (b if b else 10**9)


def _test_of(label: str) -> str | None:
    """The test function in a coverage context label: `static|dynamic` joined, the dynamic part a qualified
    name such as `tests.test_x.test_a`; the part whose last name starts with `test` wins."""
    parts = [p.rsplit(".", 1)[-1] for p in label.split("|") if p]
    return next((p for p in parts if p.startswith("test") or p.startswith("Test")), None)


def contexts_by_line(cov_path: Path, rel_of) -> dict[str, dict[int, set[str]]]:
    """Per package file, the test contexts that executed each line, when the sandbox recorded them
    (`coverage json --show-contexts`); empty when it did not. `rel_of` maps a coverage file name to the
    package-relative path or None."""
    if not cov_path.exists():
        return {}
    doc = read_json(cov_path)
    out: dict[str, dict[int, set[str]]] = {}
    for fname, fdata in (doc.get("files") or {}).items():
        ctx = fdata.get("contexts")
        if not ctx:
            continue
        rel = rel_of(fname)
        if not rel:
            continue
        lines = out.setdefault(rel, {})
        for ln, labels in ctx.items():
            tests = {_test_of(lab) for lab in labels if lab and _test_of(lab)}
            if tests:
                lines.setdefault(int(ln), set()).update(tests)
    return out


def stratified_sample(sites: list[dict], unit_sites: dict[str, list[dict]], sample: int, rng) -> tuple[list[dict], dict]:
    """Mutants for the reached behaviours first: one site per unit, round-robin, then the remainder of the
    package. Returns the chosen sites and what the stratification did."""
    chosen, taken = [], set()
    pools = {u: list(ss) for u, ss in unit_sites.items() if ss}
    for p in pools.values():
        rng.shuffle(p)
    while len(chosen) < sample and any(pools.values()):
        for u in sorted(pools):
            if len(chosen) >= sample:
                break
            while pools[u]:
                s = pools[u].pop()
                key = (s["file"], s["line"], s.get("col"), s["op"])
                if key not in taken:
                    taken.add(key); chosen.append(s); break
    in_units = len(chosen)
    rest = [s for s in sites if (s["file"], s["line"], s.get("col"), s["op"]) not in taken]
    if len(chosen) < sample and rest:
        chosen += rng.sample(rest, min(sample - len(chosen), len(rest)))
    return chosen, {"units": len(unit_sites), "units_with_sites": len([u for u, ss in unit_sites.items() if ss]), "sampled_in_units": in_units}


def resolve(symbol: str, api: dict[str, dict]) -> str | None:
    """A call-site symbol as the package's own definition: exact, else a unique match on the last name
    among functions, methods and types (the re-export case: `jose.JWTError` is `jose.exceptions.JWTError`)."""
    if symbol in api and api[symbol]["kind"] != "module":
        return symbol
    cands = [q for q, s in api.items() if s["kind"] != "module" and q.endswith("." + _last(symbol))]
    return cands[0] if len(cands) == 1 else None


def reached_units(workdir: Path, pkg: str, facts: dict, api: list[dict]) -> tuple[list[dict], list[dict]]:
    """The units to account for, and the references excluded with the reason."""
    by_q = {s["qualname"]: s for s in api}
    units, excluded = [], []
    seen = set()

    def add(q: str, via: str, kind_hint: str | None = None):
        if q in seen:
            return
        seen.add(q)
        s = by_q.get(q)
        kind = (s or {}).get("kind") or kind_hint or "unknown"
        units.append({"symbol": q, "kind": kind, "file": (s or {}).get("file"), "via": via})

    if facts.get("first_party"):
        diff_path = workdir / "analyze" / pkg / "api-diff.json"
        if diff_path.exists():
            for c in read_json(diff_path).get("changes", []):
                if c["kind"] in ("added", "changed") and by_q.get(c["symbol"], {}).get("kind") != "module":
                    add(c["symbol"], f"{c['kind']} in this change")
        else:
            public = [s for s in api if s["kind"] in BEHAVIOUR_KINDS + TYPE_KINDS]
            for s in public[:RESCAN_BUDGET]:
                add(s["qualname"], "public API, rescan")
            for s in public[RESCAN_BUDGET:]:
                excluded.append({"symbol": s["qualname"], "kind": s["kind"], "reason": "out-of-budget"})
        return units, excluded

    cs_path = workdir / "analyze" / pkg / "call-sites.json"
    sites = read_json(cs_path).get("sites", []) if cs_path.exists() else []
    modules = {s["module"] for s in api if s.get("module")}
    for sym in sorted({s["symbol"] for s in sites if not s.get("in_test")}):
        s = by_q.get(sym)
        if (s and s["kind"] == "module") or (not s and sym in modules):
            excluded.append({"symbol": sym, "kind": "module", "reason": "a module import is not a behaviour"})
            continue
        q = resolve(sym, by_q)
        if q is None:
            if sym not in seen:
                seen.add(sym)
                units.append({"symbol": sym, "kind": "unknown", "file": None, "via": "call site"})
            continue
        add(q, "call site" if q == sym else f"call site as {sym}")
    return units, excluded


def _tests_for(unit: dict, tests: list[dict]) -> list[dict]:
    """Tests linked to a unit by name or by the targets the generator recorded. Per-test coverage replaces
    this in the next slice; until then the link is nominal and the span decides execution."""
    last = _last(unit["symbol"]).lower()
    out = []
    for t in tests:
        name = t.get("name", "").lower()
        targets = [str(x).lower() for x in t.get("symbols_exercised", [])]
        if re.search(rf"(^|_){re.escape(last)}(_|$)", name) or any(unit["symbol"].lower() in x or x.endswith("." + last) for x in targets):
            out.append(t)
    return out


def account_package(workdir: Path, pkg: str, adapter=None) -> dict:
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    api_path = workdir / "analyze" / pkg / "api.new.json"
    api = read_json(api_path).get("symbols", []) if api_path.exists() else []
    res_path = workdir / "execute" / pkg / "results.json"
    results = read_json(res_path) if res_path.exists() else {"tests": []}
    tri_path = workdir / "triage" / pkg / "triage.json"
    tri = read_json(tri_path) if tri_path.exists() else {"tests": []}
    mut_path = workdir / "execute" / pkg / "mutation" / "mutation.json"
    mut = read_json(mut_path) if mut_path.exists() else {}
    cov_path = workdir / "execute" / pkg / "new" / "coverage.json"
    from .. import adapters   # here, not at import: the site builder renders the story without the adapters' dependencies
    adapter = adapter or adapters.get(read_json(workdir / "intake" / "worklist.json").get("ecosystem", "python"))
    executed = adapter.coverage_files(cov_path, adapter.import_roots(facts)) if cov_path.exists() else {}
    pl_path = workdir / "triage" / "pipeline.json"
    cannot_validate = [f for f in (read_json(pl_path).get("findings", []) if pl_path.exists() else []) if f.get("rule") in CANNOT_VALIDATE_RULES]

    internals = load_internals(workdir, pkg)
    spans = _spans(api + internals["private"])
    calls = internals["calls"]
    roots = adapter.import_roots(facts)
    known_files = {s["file"] for s in api} | {p["file"] for p in internals["private"]}

    def rel_of(fname: str) -> str | None:
        return next((f for f in known_files if fname.endswith("/" + f) or fname == f), None)

    by_test = contexts_by_line(cov_path, rel_of)
    attribution = "per-test coverage contexts" if by_test else "aggregate coverage (no contexts recorded)"
    cls = {t["test_id"].split("::")[-1]: t["class"] for t in tri.get("tests", [])}
    tests = results.get("tests", [])
    kept = [t for t in tests if t["versions"].get("new") == "pass" and t["status"] != "flaky" and cls.get(t["name"]) != "test-bug"]
    kept_names = {t["name"] for t in kept}
    units, excluded = reached_units(workdir, pkg, facts, api)
    methods_of = {}
    for s in api:
        if s["kind"] == "method":
            methods_of.setdefault(s["qualname"].rsplit(".", 1)[0], []).append(s["qualname"])

    def judge(q: str, kind: str) -> dict:
        """One unit's state from its closure: lines executed (per test when contexts exist), mutants sampled
        and killed inside it, and whether a test that executed the unit killed one."""
        linked = _tests_for({"symbol": q}, tests)
        env = [t for t in linked if t["versions"].get("new") != "pass" and ENVIRONMENT.search(t.get("message") or "")]
        ev: dict = {"tests": sorted({t["name"] for t in linked}), "kept_tests": sorted({t["name"] for t in linked if t["name"] in kept_names})}
        if cannot_validate:
            return {"state": "stated-gap", "reason": "pipeline-cannot-validate", "evidence": {**ev, "pipeline": [f["rule"] for f in cannot_validate]}}
        cl = closure_spans(q, spans, calls)
        if not cl:
            return {"state": "stated-gap", "reason": "not-in-public-api", "evidence": ev}
        lines = [(f, l) for (_, f, a, b) in cl for l in executed.get(f, ()) if a <= l <= (b or 10**9)]
        executing = {t for (f, l) in lines for t in by_test.get(f, {}).get(l, ())} & kept_names if by_test else set()
        ms = [m for m in mut.get("mutants", []) if any(_in((f, a, b), m.get("file"), m.get("line", -1)) for (_, f, a, b) in cl)]
        killed = [m for m in ms if str(m.get("status", "")).startswith("killed")]
        killers = {t for m in killed for t in m.get("killed_by", [])}
        proven_by = sorted(killers & executing) if by_test else sorted(killers & kept_names)
        ev.update({"closure": [x for (x, *_r) in cl], "spans": [{"symbol": x, "file": f, "start": a, "end": b} for (x, f, a, b) in cl],
                   "lines_executed": len(lines), "executed_by": sorted(executing), "attribution": attribution,
                   "mutants": {"sampled": len(ms), "killed": len(killed), "killed_by": sorted(killers)}, "proven_by": proven_by})
        if lines and killed and proven_by:
            return {"state": "validated", "reason": None, "evidence": ev}
        if env and not lines:
            return {"state": "for-your-environment", "reason": None, "evidence": {**ev, "refusal": (env[0].get("message") or "")[:200]}}
        if lines:
            return {"state": "stated-gap", "reason": "executed-not-checked" if ms else "strength-not-sampled", "evidence": ev}
        if linked and all(t["status"] == "flaky" for t in linked):
            return {"state": "stated-gap", "reason": "flaky", "evidence": ev}
        if linked and all(cls.get(t["name"]) == "test-bug" for t in linked):
            return {"state": "stated-gap", "reason": "failed-on-head", "evidence": ev}
        return {"state": "stated-gap", "reason": "no-test-generated", "evidence": ev}

    out_units = []
    for u in units:
        if u["kind"] in TYPE_KINDS:
            ms = methods_of.get(u["symbol"], [])
            if not ms:
                excluded.append({"symbol": u["symbol"], "kind": u["kind"], "reason": "a type without public methods; its behaviour is the functions that raise or return it"})
                continue
            judged = {m: judge(m, "method") for m in ms}
            best = next((j for j in judged.values() if j["state"] == "validated"), None) \
                or next((j for j in judged.values() if j["state"] == "for-your-environment"), None) \
                or max(judged.values(), key=lambda j: (j["evidence"].get("lines_executed") or 0))
            out_units.append({**u, **{k: best[k] for k in ("state", "reason")},
                              "evidence": {"methods": {m: {"state": j["state"], "reason": j["reason"]} for m, j in judged.items()}, "judged_by": "its public methods"}})
        else:
            out_units.append({**u, **judge(u["symbol"], u["kind"])})
    counts = {"units": len(out_units), "validated": sum(1 for u in out_units if u["state"] == "validated"),
              "for_your_environment": sum(1 for u in out_units if u["state"] == "for-your-environment"),
              "stated_gap": sum(1 for u in out_units if u["state"] == "stated-gap"),
              "by_reason": {r: sum(1 for u in out_units if u["reason"] == r) for r in REASONS if any(u["reason"] == r for u in out_units)},
              "excluded": len(excluded)}
    rec = {"format": "ai-test-harness/accounting/v1", "package": pkg, "generated": now_iso(),
           "unit": "a behaviour the change reaches: a public function, method or type of the package the application calls, or a public symbol the change altered",
           "method": {"execution": f"lines executed inside the unit's closure, its own span plus its private callees; attribution: {attribution}",
                      "strength": "a mutant sampled inside the closure and killed by a kept test that executed the unit"
                                  + ("" if by_test else " (any kept test, since no per-test contexts were recorded)"),
                      "closure_source": "analyze/<pkg>/internals.json" if internals["private"] or calls else "none recorded; spans are the public symbols alone"},
           "states": list(STATES), "reasons": REASONS, "units": out_units, "excluded": excluded, "counts": counts}
    write_json(workdir / "triage" / pkg / "accounting.json", rec)
    c = counts
    log(f"    {pkg}: {c['units']} behaviour(s) reached: {c['validated']} validated, {c['for_your_environment']} for your environment, {c['stated_gap']} stated gap(s)"
        + (f" ({', '.join(f'{n} {r}' for r, n in c['by_reason'].items())})" if c["by_reason"] else ""))
    return rec


def account(workdir: Path, packages: list[str]) -> dict:
    """The accounting for every triaged package, and the roll-up the story, the index and the dashboard read."""
    recs = [account_package(workdir, p) for p in packages]
    total = {k: sum(r["counts"][k] for r in recs) for k in ("units", "validated", "for_your_environment", "stated_gap", "excluded")}
    by_reason: dict[str, int] = {}
    for r in recs:
        for k, v in r["counts"]["by_reason"].items():
            by_reason[k] = by_reason.get(k, 0) + v
    summary = {"format": "ai-test-harness/accounting-summary/v1", "generated": now_iso(), "states": list(STATES),
               "packages": [{"package": r["package"], **r["counts"]} for r in recs], "counts": {**total, "by_reason": by_reason}}
    write_json(workdir / "triage" / "accounting-summary.json", summary)
    return summary


def plain(counts: dict) -> str:
    """The accounting in one sentence, for the story and the pull request."""
    n = counts.get("units") or 0
    if not n:
        return "No reached behaviour was accounted for in this run."
    parts = [f"{counts.get('validated', 0)} validated", f"{counts.get('for_your_environment', 0)} for your environment", f"{counts.get('stated_gap', 0)} stated gap{'s' if counts.get('stated_gap', 0) != 1 else ''}"]
    return f"{n} behaviour{'s' if n != 1 else ''} reached: " + ", ".join(parts) + "."
