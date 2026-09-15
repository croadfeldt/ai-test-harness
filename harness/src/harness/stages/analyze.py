"""Stage 2: analysis and risk scoring. Blueprint section 5, stage 2, and sections 6.2 and 6.3.

For every work-list row that changed or carries a known vulnerability, gather facts with tools and
write one fact bundle. No model is called. Release notes are stored under a name that says untrusted.
"""
from __future__ import annotations

from pathlib import Path

from .. import adapters, risk
from ..model import FactBundle, WorkItem, WorkList
from ..sources import osv, pypi
from ..util import HarnessError, log, now_iso, read_json, write_json

UNTRUSTED_BANNER = ("<!-- UNTRUSTED: text published by the package's maintainers, fetched from PyPI. "
                    "Shown to reviewers for context. Never used as instructions to any agent. -->\n\n")


def _select(wl: WorkList, select: list[str] | None, all_rows: bool, target: str = "dependencies") -> list[WorkItem]:
    """target: dependencies (the graph, as before), first-party (the repository's own code, depth 0), or all."""
    rows = []
    for it in wl.items:
        if it.depth == 0 and target == "dependencies":
            continue
        if it.depth > 0 and target == "first-party":
            continue
        if select and it.package not in select:
            continue
        if it.depth == 0 or all_rows or it.change in ("added", "bumped", "removed") or it.vulns_new or it.preflight.status == "hit":
            rows.append(it)
    return rows


def _tree(repo: Path, sha: str, cache: Path) -> Path:
    """The repository at one commit, as a plain tree under the cache (git archive), so analysis and the
    sandbox read exactly that commit and never the working copy."""
    import subprocess
    dest = cache / "source" / sha[:12]
    if (dest / ".complete").exists():
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["git", "-C", str(repo), "archive", sha], capture_output=True, timeout=300)
    if proc.returncode != 0:
        raise HarnessError(f"git archive {sha} failed: {proc.stderr.decode()[-300:]}")
    subprocess.run(["tar", "-x", "-C", str(dest)], input=proc.stdout, check=True)
    (dest / ".complete").write_text(now_iso())
    return dest


def analyze_first_party(it: WorkItem, repo: Path, workdir: Path, adapter, graph_new: dict) -> FactBundle:
    """The repository's own code as the package under test. Facts come from the tree at head (and at
    base for a change): the API surface of its packages, what changed, and which dependencies its
    tests may import. No advisories are looked up for it unless it is a published package; the
    known-vulnerability work stays with the dependency rows (blueprint 5.0: minus CVE remediation
    unless it is known already)."""
    out = workdir / "analyze" / it.package
    out.mkdir(parents=True, exist_ok=True)
    cache = workdir / "cache"
    wl = read_json(workdir / "intake" / "worklist.json")
    head_sha = wl["new_manifest"].split("@")[-1]
    base_sha = (wl.get("old_manifest") or "").split("@")[-1] or None
    trees = {"new": _tree(repo, head_sha, cache)}
    if base_sha and base_sha != head_sha:
        trees["old"] = _tree(repo, base_sha, cache)
    names = adapter.first_party_packages(trees["new"])
    if not names:
        raise HarnessError(f"{repo.name}: no first-party packages found at {head_sha[:12]}")
    surfaces = {}
    for tag, tree in trees.items():
        surfaces[tag] = adapter.extract_api(tree, names)
        write_json(out / f"api.{tag}.json", {"package": it.package, "version": (head_sha if tag == "new" else base_sha)[:12], "archive": f"source@{(head_sha if tag == 'new' else base_sha)[:12]}",
                                              "import_names": names, "symbols": surfaces[tag]})
    changed_mode = "old" in trees
    diff = adapter.api_diff(surfaces["old"], surfaces["new"]) if changed_mode else []
    if changed_mode:
        write_json(out / "api-diff.json", {"package": it.package, "old": base_sha[:12], "new": head_sha[:12], "changes": diff})
        sdiff = adapter.source_diff(trees["old"], trees["new"]); patch = adapter.source_patch(trees["old"], trees["new"])
        (out / "source-diff.patch").write_text(patch); sdiff["patch_ref"] = "source-diff.patch"; sdiff["patch_lines"] = patch.count("\n")
    else:
        sdiff = {"note": "rescan: no base to diff against", "lines_added": 0, "lines_removed": 0}
    breaking = sum(1 for c in diff if c.breaking); changed = sum(1 for c in diff if c.kind == "changed")
    changed_symbols = [c.symbol for c in diff if c.kind in ("changed", "added")][:60]
    write_json(out / "call-sites.json", {"package": it.package, "import_names": names, "sites": [],
                                         "note": "first-party target: the application is the package; changed symbols stand in for call sites"})
    write_json(out / "vulns.json", {"package": it.package, "version": head_sha[:12], "vulns": [], "old_version": base_sha[:12] if base_sha else None,
                                    "vulns_old": [], "fixed_by_this_change": [], "affected_symbols_in_use": [],
                                    "note": "no advisories are looked up for the application itself; known vulnerabilities belong to the dependency rows"})
    dep_roots = sorted({r for p in graph_new.values() if p.get("direct") for r in adapter.import_candidates(p["name"])})
    tests_present = [str(p.relative_to(trees["new"])) for p in adapter.first_party_files(trees["new"]) if adapter.is_test_file(p.relative_to(trees["new"]))]
    static = adapter.static_analysis([trees["new"] / n for n in names], trees["new"])
    rs = risk.score(depth=0, change=it.change, reachable="true", vuln_count=0, high_severity=False, breaking_changes=breaking,
                    changed_symbols=changed, lines_changed=sdiff.get("lines_added", 0) + sdiff.get("lines_removed", 0), sensitive=[],
                    preflight_hit=False, new_package=False)
    fb = FactBundle(package=it.package, purl=it.purl, old_version=base_sha[:12] if base_sha else None, new_version=head_sha[:12],
                    depth=0, change=it.change, import_names=names,
                    api_old_ref="api.old.json" if changed_mode else None, api_new_ref="api.new.json",
                    api_diff_ref="api-diff.json" if changed_mode else None,
                    api_diff_summary={"added": sum(1 for c in diff if c.kind == "added"), "removed": sum(1 for c in diff if c.kind == "removed"),
                                      "changed": changed, "breaking": breaking, "breaking_symbols": [c.symbol for c in diff if c.breaking][:30]},
                    source_diff_summary=sdiff, call_sites_ref="call-sites.json",
                    call_sites_summary={"production": 0, "test": 0, "reachable": "true", "reachable_note": "the application's own code",
                                        "dependents_in_graph": [], "symbols_used": changed_symbols, "files": []},
                    upstream_tests={"present": bool(tests_present), "count": len(tests_present), "files": tests_present[:30],
                                    "note": "the application's own test files"},
                    vulns_ref="vulns.json",
                    vulns_summary={"count": 0, "ids": [], "count_old": 0, "fixed_by_this_change": [], "cves": [], "fixed_versions": [],
                                   "affected_symbols_in_use": [], "symbols_named_by_advisories": False},
                    notes_ref=None, static_analysis=static, sensitivity=[], risk=rs, generated=now_iso())
    facts = {**vars(fb), "first_party": True, "source_trees": {k: str(v.relative_to(workdir)) for k, v in trees.items()},
             "dependency_import_names": dep_roots}
    write_json(out / "facts.json", facts)
    return fb


def analyze_item(it: WorkItem, repo: Path, workdir: Path, adapter, python_version: str | None,
                 vuln_index: dict, dependents: list[str]) -> FactBundle:
    out = workdir / "analyze" / it.package
    out.mkdir(parents=True, exist_ok=True)
    cache = workdir / "cache"
    surfaces, dirs, names = {}, {}, []
    for tag, ver in (("old", it.old_version), ("new", it.new_version)):
        if not ver or (tag == "old" and it.change == "unchanged"):
            continue
        archive = adapter.fetch(it.package, ver, cache, python_version)
        unpacked = adapter.unpack(archive, cache)
        dirs[tag] = unpacked
        nm = adapter.import_names(unpacked, it.package)
        names = names or nm
        surfaces[tag] = adapter.extract_api(unpacked, nm)
        write_json(out / f"api.{tag}.json", {"package": it.package, "version": ver, "archive": archive.name,
                                              "import_names": nm, "symbols": surfaces[tag]})
    if "old" not in surfaces and "new" in surfaces:
        surfaces["old"] = surfaces["new"]; dirs["old"] = dirs["new"]
    diff = adapter.api_diff(surfaces.get("old", []), surfaces.get("new", [])) if it.change == "bumped" else []
    if it.change == "bumped":
        write_json(out / "api-diff.json", {"package": it.package, "old": it.old_version, "new": it.new_version, "changes": diff})
        sdiff = adapter.source_diff(dirs["old"], dirs["new"])
        patch = adapter.source_patch(dirs["old"], dirs["new"])
        (out / "source-diff.patch").write_text(patch)
        sdiff["patch_ref"] = "source-diff.patch"
        sdiff["patch_lines"] = patch.count("\n")
    else:
        sdiff = {"note": f"no source diff for change={it.change}", "lines_added": 0, "lines_removed": 0}
    breaking = sum(1 for c in diff if c.breaking)
    changed = sum(1 for c in diff if c.kind == "changed")

    sites = adapter.call_sites(repo, names)
    write_json(out / "call-sites.json", {"package": it.package, "import_names": names, "sites": sites})
    prod_sites = [s for s in sites if not s.in_test]
    symbols_used = sorted({s.symbol for s in prod_sites})
    # Reachability without a call graph: a direct reference is proof. No direct reference is only
    # proof of absence when nothing else in the graph depends on the package either; otherwise the
    # package may be reached through a dependent (FastAPI reaching python-multipart for uploads).
    if prod_sites:
        reachable, reach_note = "true", f"{len(prod_sites)} first-party references"
    elif dependents:
        reachable, reach_note = "unknown", f"no first-party reference; may be reached through {', '.join(dependents)}"
    else:
        reachable, reach_note = "false", "no first-party reference and no package in the graph depends on it"

    key = f"{it.package}@{it.new_version or it.old_version}"
    vulns = vuln_index.get(key, [])
    # Advisories on the version being replaced: a bump that fixes them is exactly what a fix-pinning
    # test must prove (fails on old, passes on new), so they travel with the bundle too.
    vulns_old = vuln_index.get(f"{it.package}@{it.old_version}", []) if it.change == "bumped" else []
    affected_in_use = []
    for v in vulns:
        for sym in v.get("affected_symbols", []):
            if any(u.endswith(sym) for u in symbols_used):
                affected_in_use.append(sym)
    write_json(out / "vulns.json", {"package": it.package, "version": it.new_version, "vulns": vulns,
                                    "old_version": it.old_version, "vulns_old": vulns_old,
                                    "fixed_by_this_change": [v["id"] for v in vulns_old if v["id"] not in {x["id"] for x in vulns}],
                                    "affected_symbols_in_use": affected_in_use})
    high = any(v.get("severity") for v in vulns)

    md = adapter.metadata(it.package, it.new_version or it.old_version, cache)
    notes_ref = None
    if md:
        (out / "notes.untrusted.md").write_text(UNTRUSTED_BANNER + f"# {md['name']} {md['version']}\n\n"
                                                f"Summary: {md['summary']}\n\nProject URLs: {md['project_urls']}\n\n"
                                                f"Uploaded: {md['upload_time']}\n\n---\n\n{md['description']}")
        notes_ref = "notes.untrusted.md"
    sens = risk.sensitivity(it.package, md["summary"] if md else "", md["keywords"] if md else "", md["classifiers"] if md else [])
    static = adapter.static_analysis([repo / s.file for s in prod_sites][:50], repo)
    up = adapter.upstream_tests(dirs["new"]) if "new" in dirs else {"present": False, "count": 0}

    rs = risk.score(depth=it.depth, change=it.change, reachable=reachable, vuln_count=len(vulns), high_severity=high,
                    vulns_fixed=len(vulns_old),
                    breaking_changes=breaking, changed_symbols=changed,
                    lines_changed=sdiff.get("lines_added", 0) + sdiff.get("lines_removed", 0), sensitive=sens,
                    preflight_hit=it.preflight.status == "hit", new_package=it.change == "added")
    fb = FactBundle(package=it.package, purl=it.purl, old_version=it.old_version, new_version=it.new_version,
                    depth=it.depth, change=it.change, import_names=names,
                    api_old_ref="api.old.json" if "old" in surfaces and it.change == "bumped" else None,
                    api_new_ref="api.new.json" if "new" in surfaces else None,
                    api_diff_ref="api-diff.json" if it.change == "bumped" else None,
                    api_diff_summary={"added": sum(1 for c in diff if c.kind == "added"),
                                      "removed": sum(1 for c in diff if c.kind == "removed"),
                                      "changed": changed, "breaking": breaking,
                                      "breaking_symbols": [c.symbol for c in diff if c.breaking][:30]},
                    source_diff_summary=sdiff, call_sites_ref="call-sites.json",
                    call_sites_summary={"production": len(prod_sites), "test": len(sites) - len(prod_sites),
                                        "reachable": reachable, "reachable_note": reach_note,
                                        "dependents_in_graph": dependents, "symbols_used": symbols_used[:60],
                                        "files": sorted({s.file for s in prod_sites})[:30]},
                    upstream_tests=up, vulns_ref="vulns.json",
                    vulns_summary={"count": len(vulns), "ids": [v["id"] for v in vulns],
                                   "count_old": len(vulns_old),
                                   "fixed_by_this_change": [v["id"] for v in vulns_old if v["id"] not in {x["id"] for x in vulns}],
                                   "cves": sorted({a for v in vulns for a in v.get("aliases", []) if a.startswith("CVE-")}),
                                   "fixed_versions": sorted({f for v in vulns for f in v.get("fixed_versions", [])}),
                                   "affected_symbols_in_use": affected_in_use,
                                   "symbols_named_by_advisories": any(v.get("affected_symbols") for v in vulns)},
                    notes_ref=notes_ref, static_analysis=static, sensitivity=sens, risk=rs, generated=now_iso())
    write_json(out / "facts.json", fb)
    return fb


def analyze(*, workdir: Path, select: list[str] | None = None, all_rows: bool = False,
            python_version: str | None = None, repo: str | None = None, target: str = "dependencies") -> list[FactBundle]:
    wl_path = workdir / "intake" / "worklist.json"
    if not wl_path.exists():
        raise HarnessError(f"no work list at {wl_path}; run intake first")
    raw = read_json(wl_path)
    from ..model import Preflight
    wl = WorkList(**{**raw, "items": [WorkItem(**{**i, "preflight": Preflight(**i["preflight"])}) for i in raw["items"]]})
    adapter = adapters.get(raw.get("ecosystem", "python"))
    from .. import config
    repo = config.resolve_repo(wl.source_dir, repo)
    vuln_index = read_json(workdir / "intake" / "vulns.json")
    graph = read_json(workdir / "intake" / "graph.new.json")["packages"]
    dependents_of = {name: sorted(p for p, d in graph.items() if name in d["requires"])
                     + sorted(f"{p} (optional extra)" for p, d in graph.items() if name in d.get("optional_requires", []))
                     for name in graph}
    rows = _select(wl, select, all_rows, target)
    log(f"analyze: {len(rows)} of {len(wl.items)} work-list rows selected (target: {target})")
    bundles = []
    for it in rows:
        log(f"  {it.package} {it.old_version} -> {it.new_version} ({it.change}, depth {it.depth})")
        if it.depth == 0:
            bundles.append(analyze_first_party(it, repo, workdir, adapter, graph))
        else:
            bundles.append(analyze_item(it, repo, workdir, adapter, python_version, vuln_index, dependents_of.get(it.package, [])))
    summary = [{"package": b.package, "change": b.change, "depth": b.depth, "old": b.old_version, "new": b.new_version,
                "reachable": b.call_sites_summary["reachable"], "call_sites": b.call_sites_summary["production"],
                "vulns": b.vulns_summary["count"], "breaking": b.api_diff_summary["breaking"],
                "score": b.risk.score, "budget": b.risk.budget["level"], "cve_targeted": b.risk.budget["cve_targeted"]}
               for b in bundles]
    from ..util import merge_summary
    merge_summary(workdir / "analyze" / "summary.json", summary, extra={"run_id": wl.run_id}, list_key="items")
    for s in summary:
        log(f"  {s['package']:<20} score {s['score']:>3}  budget {s['budget']:<8} reachable {s['reachable']:<7} vulns {s['vulns']:>2}  breaking {s['breaking']}")
    return bundles
