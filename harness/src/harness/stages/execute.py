"""Stage 4: execution and validation. Blueprint section 5 stage 4.

The gauntlet, in order: compile, run, flake re-run, coverage, differential (old versus new). Mutation
and the relevance check on existing tests arrive with the triage slice. Output is TestResults in the
schema from blueprint/adapter-interface.md, one per package, plus the raw junit, coverage, and logs
for every sandbox run.
"""
from __future__ import annotations

from pathlib import Path

from .. import adapters
from ..util import log, now_iso, read_json, sha256_file, write_json


def base_name(test_id: str) -> str:
    """GF-018. 'tests.test_x::test_a[asyncio]' -> 'test_a'; Go 'harnesstest::TestA/case' -> 'TestA'.
    Manifests name tests by function."""
    name = test_id.split("::")[-1]
    return name.split("[", 1)[0].split("/", 1)[0]


def _reqs(workdir: Path, tag: str, adapter=None) -> list[str]:
    g = read_json(workdir / "intake" / f"graph.{tag}.json")["packages"]
    return (adapter or adapters.get("python")).requirements(g)


def verdict(t: dict, msg_old: str, roles: dict, fix_patch: str | None) -> str:
    """Every old/new outcome maps to a fixed, honest verdict (GF-012). CVE tests are judged by the
    differential with the roles from the advisories (GF-016); a test that did not compile is a test
    bug in either category; the others are characterization outcomes."""
    from .agent import fix_reached
    o, n = t["versions"]["old"], t["versions"]["new"]
    msg_new = t.get("message", "")
    if t["status"] == "flaky":
        return "flaky: discard"
    if t["category"] == "cve":
        # GF-016: roles, not commit order. On a downgrade the NEW version is the vulnerable one.
        vuln_status, fixed_status = (n, o) if roles["direction"] in ("downgrade", "candidate") else (o, n)
        if vuln_status == "fail" and fixed_status == "pass":
            return ("exposure confirmed: the downgrade to the vulnerable version fails this test and the previous, fixed version passes it"
                    if roles["direction"] == "downgrade" else
                    f"exposure confirmed: fails at head {roles['vulnerable']}, passes with the fixed candidate {roles['fixed']}"
                    if roles["direction"] == "candidate" else "fix-pinning confirmed: fails on vulnerable, passes on fixed")
        if o == "pass" and n == "pass":
            return "not a fix-pinning test: passes on both versions; keep only as characterization if it covers the symbol"
        if msg_new.startswith("did not compile"):
            return "did not compile: test bug; back to generation"
        if n in ("fail", "error") and fix_reached(msg_new, fix_patch):
            return "fix reached, assertion wrong: the fixed version raised the error the fix introduced; expect it on new and show old accepting the input"
        if n in ("fail", "error") and o in ("fail", "error") and msg_new and msg_new.split(":")[0] == msg_old.split(":")[0] \
                and not msg_new.startswith(("AssertionError", "Failed: DID NOT RAISE", "assert ")):
            return f"blocked on both versions: {msg_new.split(':')[0]} on old and new; possible package or environment defect, reproducer attached"
        if n in ("fail", "error"):
            return "fails on the fixed version: test bug or the advisory is misread; back to generation"
        return f"inconclusive (old={o}, new={n})"
    if msg_new.startswith("did not compile"):
        return "did not compile: test bug; back to generation"
    if n == "pass" and o in ("pass", "na"):
        return "candidate: passes on head" + (", same on old" if o == "pass" else "")
    if n == "pass" and o in ("fail", "error"):
        return "behavior changed between versions: passes on new, fails on old; reviewer note"
    return f"fails on head: test bug or defect (new={n})"


def execute_package(workdir: Path, pkg: str, python_version: str, adapter=None) -> dict:
    adapter = adapter or adapters.get("python")
    gen = read_json(workdir / "generate" / pkg / "manifest.json")
    tests_dir = workdir / "generate" / pkg / "tests"
    out = workdir / "execute" / pkg
    out.mkdir(parents=True, exist_ok=True)
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    roots = adapter.import_roots(facts)
    from .agent import fix_reached
    from .generate import cve_roles, env_dir
    vdoc = read_json(workdir / "analyze" / pkg / "vulns.json")
    cand_path0 = workdir / "analyze" / pkg / "fixed-candidate.json"
    roles = cve_roles(gen["old_version"], gen["new_version"], vdoc.get("vulns_old", []), vdoc.get("vulns", []),
                      read_json(cand_path0) if cand_path0.exists() else None)
    patch_path = workdir / "analyze" / pkg / "source-diff.patch"
    fix_patch = patch_path.read_text() if patch_path.exists() else None
    reqs_new = _reqs(workdir, "new", adapter)
    runs = {}
    plans = [("new", reqs_new), ("new-rerun", reqs_new)]
    cand_path = workdir / "analyze" / pkg / "fixed-candidate.json"
    candidate = read_json(cand_path) if cand_path.exists() else None
    if roles["direction"] == "candidate" and candidate and candidate.get("status") == "resolved":
        env_c = adapter.prefetch(candidate["requirements"], python_version, env_dir(workdir, adapter, f"fixed-{pkg.replace('/', '_')}"))
        log(f"    sandbox run fixed-candidate ({pkg} {candidate['fixed_version']})")
        s = adapter.run_tests(env_c, tests_dir, out / "fixed-candidate", cover=roots, label=f"{pkg}-fixed-candidate")
        runs["old"] = {"sandbox": s, "results": adapter.parse_results(s), "coverage": adapter.coverage_for(s, roots)}
        plans = [p for p in plans if p[0] != "old"]
    if gen["old_version"] and gen["old_version"] != gen["new_version"]:
        # Differential: the base commit's own resolved graph, which is the state the application
        # actually ran with before the change. Swapping one package inside the head graph produces
        # sets that never existed and may not resolve (python-jose 3.3.0 with head's pyasn1 did not).
        plans.append(("old", _reqs(workdir, "old", adapter)))
    trees = facts.get("source_trees") if facts.get("first_party") else None
    for label, reqs in plans:
        if label == "old" and "old" in runs:
            continue
        env_tag = "old" if label == "old" else "new"
        env = adapter.prefetch(reqs, python_version, env_dir(workdir, adapter, env_tag),
                               source=(workdir / trees[env_tag]) if trees and env_tag in trees else None)
        log(f"    sandbox run {label}")
        s = adapter.run_tests(env, tests_dir, out / label, cover=roots, label=f"{pkg}-{label}")
        runs[label] = {"sandbox": s, "results": adapter.parse_results(s), "coverage": adapter.coverage_for(s, roots)}
    by_file = {}
    for f in gen["files"]:
        for t in f["tests"]:
            by_file[t] = f
    tests = []
    for tid, r_new in runs["new"]["results"].items():
        name = base_name(tid)
        f = by_file.get(name, {})
        rerun = runs["new-rerun"]["results"].get(tid, {}).get("status", "na")
        old = runs["old"]["results"].get(tid, {}).get("status", "na") if "old" in runs else "na"
        status = r_new["status"]
        if rerun != "na" and rerun != status:
            status = "flaky"
        tests.append({"id": tid, "name": name, "param_id": tid.split("::")[-1], "category": f.get("category", "unknown"), "file": f.get("file"),
                      "status": status, "duration_ms": r_new["duration_ms"], "message": r_new["message"][:500],
                      "versions": {"old": old, "new": r_new["status"]},
                      "expected_differential": f.get("expected_differential"),
                      "symbols_exercised": f.get("targets", [])[:10]})
    # Verdict per test from the differential, per blueprint stage 3 and 4.
    for t in tests:
        msg_old = (runs["old"]["results"].get(t["id"], {}).get("message", "") if "old" in runs else "")
        t["verdict"] = verdict(t, msg_old, roles, fix_patch)
    cov_new = runs["new"]["coverage"]
    results = {
        "run_id": read_json(workdir / "intake" / "worklist.json")["run_id"],
        "selfcheck_ref": "../../selfcheck/selfcheck.json",
        "artifact_digest": None, "generated": now_iso(),
        "target": {"class": runs["new"]["sandbox"]["isolation"].get("target", "podman"), "provisioner": "local podman" if runs["new"]["sandbox"]["isolation"].get("target", "podman") == "podman" else "the task pod",
                   "identity": runs["new"]["sandbox"]["image"],
                   "image_digest": runs["new"]["sandbox"].get("image_digest"), "isolation": runs["new"]["sandbox"]["isolation"]},
        "package": {"purl": gen["purl"], "old_version": gen["old_version"], "new_version": gen["new_version"]},
        "tests": tests,
        "counts": {"total": len(tests),
                   "pass_on_new": sum(1 for t in tests if t["versions"]["new"] == "pass"),
                   "flaky": sum(1 for t in tests if t["status"] == "flaky"),
                   "fix_pinning_confirmed": sum(1 for t in tests if t["verdict"].startswith(("fix-pinning confirmed", "exposure confirmed"))),
                   "cve_roles": roles,
                   "fix_reached_assertion_wrong": sum(1 for t in tests if t["verdict"].startswith("fix reached")),
                   "blocked_both_versions": sum(1 for t in tests if t["verdict"].startswith("blocked on both")),
                   "behavior_changed": sum(1 for t in tests if t["verdict"].startswith("behavior changed"))},
        "coverage_ref": "new/coverage.json" if cov_new.get("available") else None,
        "coverage_summary": {"covered_lines_in_target": cov_new.get("covered_lines_in_target", 0),
                             "files": {k: {"covered": v["covered_lines"], "statements": v["num_statements"]}
                                       for k, v in cov_new.get("files", {}).items()}},
        "mutation_ref": None, "fuzz_ref": None,
        "runs": {k: {"returncode": v["sandbox"]["returncode"], "duration_s": v["sandbox"]["duration_s"],
                     "timed_out": v["sandbox"]["timed_out"]} for k, v in runs.items()},
        "test_files": [{"file": f["file"], "sha256": f["sha256"]} for f in gen["files"]],
    }
    write_json(out / "results.json", results)
    c = results["counts"]
    log(f"    {pkg}: {c['total']} tests, {c['pass_on_new']} pass on head, {c['flaky']} flaky, "
        f"{c['fix_pinning_confirmed']} fix-pinning confirmed, {c['behavior_changed']} behavior changes")
    return results


def execute(*, workdir: Path, select: list[str] | None = None, python_version: str = "3.12") -> list[dict]:
    from .. import selfcheck
    selfcheck.require(workdir, python_version, probes=False)   # register checks again; the sandbox was probed before generation
    gen_summary = read_json(workdir / "generate" / "summary.json")
    adapter = adapters.get(read_json(workdir / "intake" / "worklist.json").get("ecosystem", "python"))
    outs = []
    for p in gen_summary["packages"]:
        pkg = p["package"]
        if select and pkg not in select:
            continue
        if p["files"] == 0:
            log(f"  {pkg}: nothing generated"); continue
        log(f"  {pkg}")
        outs.append((pkg, execute_package(workdir, pkg, python_version, adapter)))
    from ..util import merge_summary
    # Rows carry the package name the work list uses (a Go module path has slashes; the purl's last segment is not it).
    merge_summary(workdir / "execute" / "summary.json", [
        {"package": pkg, **{k: v for k, v in r["counts"].items() if k != "cve_roles"}} for pkg, r in outs])
    outs = [r for _, r in outs]
    return outs
