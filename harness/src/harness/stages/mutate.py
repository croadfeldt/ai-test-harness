"""Stage 4, step 5: mutation testing. Blueprint section 5 stage 4 and section 10 (mutation score).

The harness applies a bounded set of classic mutation operators to the package's source, restricted
to lines the accepted tests execute, and runs the tests against each mutant in the sandbox. A mutant
the tests fail on is killed; one they pass on survived; one that does not compile is invalid and not
counted. The operators, the sample size, and the seed are recorded so a run can be replayed. The
operators live in the adapter: Python's on the standard library ast, Go's in the go/ast helper.
mutmut and go-mutesting mutate a project's own tree; the harness's target is a dependency, so it
carries its own.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

from .. import adapters
from ..util import log, now_iso, read_json, write_json

SAMPLE = 25


def mutate_package(workdir: Path, pkg: str, python_version: str, sample: int = SAMPLE, adapter=None) -> dict:
    adapter = adapter or adapters.get("python")
    results = read_json(workdir / "execute" / pkg / "results.json")
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    gen = read_json(workdir / "generate" / pkg / "manifest.json")
    cov_path = workdir / "execute" / pkg / "new" / "coverage.json"
    out = workdir / "execute" / pkg / "mutation"
    out.mkdir(parents=True, exist_ok=True)
    roots = adapter.import_roots(facts)
    keep = {t["name"] for t in results["tests"] if t["versions"]["new"] == "pass" and t["status"] != "flaky"}
    if not keep or not cov_path.exists():
        rec = {"package": pkg, "status": "skipped", "reason": "no passing tests or no coverage", "generated": now_iso()}
        write_json(out / "mutation.json", rec); return rec
    # Tests that pass on head, as one directory (only those tests, cut from the generated files).
    tests_dir = out / "tests"; tests_dir.mkdir(exist_ok=True)
    for f in gen["files"]:
        src = (workdir / "generate" / pkg / f["file"]).read_text()
        cut = {n for n in f["tests"] if n not in keep}
        code = adapter.drop_tests(src, cut) if cut else src
        if adapter.test_names(code):
            (tests_dir / Path(f["file"]).name).write_text(code)
    # Executed lines per package file from the head coverage run; source from the cache.
    executed = adapter.coverage_files(cov_path, roots)
    cache = workdir / "cache"
    unpacked = adapter.pkg_root(adapter.unpack(adapter.fetch(pkg, facts["new_version"], cache, python_version), cache))
    sites = []
    for rel, lines in executed.items():
        src_path = unpacked / rel
        if src_path.exists():
            sites += [{"file": rel, **s} for s in adapter.mutation_sites(src_path, lines)]
    seed = int(hashlib.sha256(f"{pkg}{facts['new_version']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    chosen = rng.sample(sites, min(sample, len(sites))) if sites else []
    log(f"    {pkg}: {len(sites)} mutation sites on {sum(len(l) for l in executed.values())} executed lines; sampling {len(chosen)} (seed {seed})")
    from .generate import env_dir
    graph_new = read_json(workdir / "intake" / "graph.new.json")["packages"]
    env = adapter.prefetch(adapter.requirements(graph_new), python_version, env_dir(workdir, adapter, "new"))
    limits = {"timeout_s": 300}
    mutants = []
    for i, site in enumerate(chosen, 1):
        mid = f"m{i:03d}"
        mdir = out / "mutants" / mid
        code = adapter.apply_mutation(unpacked / site["file"], site)
        if code is None:
            mutants.append({"id": mid, "file": site["file"], "line": site["line"], "operator": site["op"], "status": "invalid", "detail": "could not render"}); continue
        adapter.write_overlay(mdir, site["file"], code, facts)
        s = adapter.run_tests(env, tests_dir, mdir / "out", cover=[], label=f"{pkg}-{mid}", overlay_dir=mdir, limits=_limits(adapter, limits))
        r = adapter.parse_results(s)
        from .execute import base_name
        killed_by = sorted({base_name(k) for k, v in r.items() if v["status"] in ("fail", "error")})
        status = adapter.mutant_status(s, r, killed_by)
        mutants.append({"id": mid, "file": site["file"], "line": site["line"], "operator": site["op"], "status": status, "killed_by": killed_by,
                        "duration_s": s["duration_s"]})
        log(f"      {mid} {site['op']:<13} {site['file']}:{site['line']} {status}" + (f" by {killed_by[:3]}" if killed_by else ""))
    valid = [m for m in mutants if not m["status"].startswith(("invalid", "error"))]
    killed = [m for m in valid if m["status"].startswith("killed")]
    per_test = {}
    for m in killed:
        for t in m.get("killed_by", []):
            per_test.setdefault(t, []).append(m["id"])
    unique = {t: [mid for mid in ids if sum(1 for mm in killed if t in mm.get("killed_by", []) and mid == mm["id"] and len(mm["killed_by"]) == 1)]
              for t, ids in per_test.items()}
    rec = {"package": pkg, "version": facts["new_version"], "generated": now_iso(), "status": "ran",
           "engine": f"harness {adapter.ECOSYSTEM} mutator (diff- and coverage-scoped)", "operators": list(adapter.MUTATION_OPERATORS),
           "seed": seed, "sites": len(sites), "sampled": len(chosen), "valid": len(valid), "killed": len(killed),
           "invalid": sum(1 for m in mutants if m["status"].startswith("invalid")),
           "survived": sum(1 for m in valid if m["status"] == "survived"),
           "score": round(len(killed) / len(valid), 3) if valid else None,
           "per_test": {t: {"killed": ids, "unique": unique.get(t, [])} for t, ids in per_test.items()},
           "mutants": mutants, "tests": sorted(keep)}
    write_json(out / "mutation.json", rec)
    log(f"    {pkg}: mutation score {rec['score']} ({len(killed)} of {len(valid)} killed); {len(per_test)} of {len(keep)} tests killed at least one")
    return rec


def _limits(adapter, override: dict) -> dict:
    from .. import sandbox, sandbox_go
    base = sandbox_go.LIMITS if adapter.ECOSYSTEM == "go" else sandbox.LIMITS
    return {**base, **override}


def mutate(*, workdir: Path, select: list[str] | None = None, python_version: str = "3.12", sample: int = SAMPLE) -> list[dict]:
    from .. import selfcheck
    from ..util import merge_summary
    selfcheck.require(workdir, python_version, probes=False)
    # Packages with stage 4 results on disk, not just summary rows: the results file is the truth.
    pkgs = [p["package"] for p in read_json(workdir / "execute" / "summary.json")["packages"]] if (workdir / "execute" / "summary.json").exists() else []
    adapter = adapters.get(read_json(workdir / "intake" / "worklist.json").get("ecosystem", "python"))
    outs = []
    for pkg in pkgs:
        if select and pkg not in select:
            continue
        log(f"  {pkg}")
        if not adapter.MUTATION:
            rec = {"package": pkg, "status": "skipped", "reason": f"no mutation engine for {adapter.ECOSYSTEM} yet; the score is not measured, not zero",
                   "generated": now_iso()}
            out = workdir / "execute" / pkg / "mutation"; out.mkdir(parents=True, exist_ok=True); write_json(out / "mutation.json", rec)
            log(f"    {pkg}: mutation skipped ({rec['reason']})"); outs.append(rec); continue
        outs.append(mutate_package(workdir, pkg, python_version, sample, adapter))
    merge_summary(workdir / "execute" / "mutation-summary.json", [{"package": o["package"], "status": o["status"], "score": o.get("score"),
                                                                    "sampled": o.get("sampled"), "killed": o.get("killed")} for o in outs])
    return outs
