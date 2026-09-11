"""Stage 1: intake and inventory. Blueprint section 5, stage 1.

Trigger: a commit range on the target repository (base..head), or a rescan of one ref. The stage
resolves the full dependency graph at both refs, diffs them, runs the pre-flight gates it has, probes
reachability cheaply, and writes the work list. It downloads nothing but wheel metadata and never
executes package code.
"""
from __future__ import annotations

import hashlib
import re
import tempfile
from pathlib import Path

from .. import adapters
from ..model import DependencyGraph, Preflight, WorkItem, WorkList
from ..sources import osv
from ..util import HarnessError, log, now_iso, run, tool_available, write_json


def _git(repo: Path, *args: str) -> str:
    return run(["git", "-C", str(repo), *args]).stdout.strip()


def _manifest_at(repo: Path, ref: str, manifest: str, dest: Path) -> Path:
    proc = run(["git", "-C", str(repo), "show", f"{ref}:{manifest}"], check=False)
    if proc.returncode != 0:
        raise HarnessError(f"{manifest} does not exist at {ref}: {proc.stderr.strip()}")
    out = dest / f"{re.sub(r'[^A-Za-z0-9]+', '_', ref)}-{Path(manifest).name}"
    out.write_text(proc.stdout)
    return out


def _project_name(repo: Path) -> str:
    py = repo / "pyproject.toml"
    if py.exists():
        m = re.search(r'^name\s*=\s*"([^"]+)"', py.read_text(), re.M)
        if m:
            return m.group(1)
    return repo.name


def _guarddog(name: str, version: str) -> dict:
    if not tool_available("guarddog"):
        return {"status": "not_installed"}
    proc = run(["guarddog", "pypi", "scan", name, "--version", version, "--output-format", "json"], check=False, timeout=300)
    return {"status": "ran", "returncode": proc.returncode, "stdout": proc.stdout[-4000:]}


def _cyclonedx(graph: DependencyGraph, run_id: str) -> dict:
    comps = [{"type": "library", "name": p.name, "version": p.version, "purl": p.purl,
              "bom-ref": p.purl} for p in graph.packages.values()]
    deps = [{"ref": p.purl, "dependsOn": [graph.packages[c].purl for c in p.requires]} for p in graph.packages.values()]
    return {"bomFormat": "CycloneDX", "specVersion": "1.5", "serialNumber": f"urn:uuid:{run_id}",
            "version": 1, "metadata": {"timestamp": now_iso(),
                                       "tools": [{"name": "ai-test-harness", "version": "0.1.0"}],
                                       "component": {"type": "application", "name": Path(graph.source_dir).name}},
            "components": comps, "dependencies": deps}


def intake(*, repo: Path, head: str, base: str | None, manifest: str, workdir: Path,
           ecosystem: str = "python", python_version: str | None = None) -> WorkList:
    adapter = adapters.get(ecosystem)
    out = workdir / "intake"
    out.mkdir(parents=True, exist_ok=True)
    cache = workdir / "cache"
    head_sha = _git(repo, "rev-parse", head)
    base_sha = _git(repo, "rev-parse", base) if base else head_sha
    mode = "diff" if base else "rescan"
    run_id = hashlib.sha256(f"{repo}{base_sha}{head_sha}{now_iso()}".encode()).hexdigest()[:12]
    log(f"intake: {mode} {repo.name} {base_sha[:8]}..{head_sha[:8]} manifest={manifest} run={run_id}")

    with tempfile.TemporaryDirectory(prefix="harness-intake-") as td:
        tdp = Path(td)
        new_manifest = _manifest_at(repo, head_sha, manifest, tdp)
        log("  resolving graph at head")
        new_graph = adapter.resolve_graph(repo, new_manifest, python_version)
        new_graph.manifest = f"{manifest}@{head_sha[:12]}"
        if base:
            old_manifest = _manifest_at(repo, base_sha, manifest, tdp)
            log("  resolving graph at base")
            old_graph = adapter.resolve_graph(repo, old_manifest, python_version)
            old_graph.manifest = f"{manifest}@{base_sha[:12]}"
        else:
            old_graph = new_graph
    write_json(out / "graph.new.json", new_graph)
    write_json(out / "graph.old.json", old_graph)
    write_json(out / "sbom.new.cdx.json", _cyclonedx(new_graph, run_id))
    log(f"  {len(new_graph.packages)} packages at head, {len(old_graph.packages)} at base")

    # Known vulnerabilities + Malicious Packages, one batch for every (name, version) in either graph.
    pairs = sorted({(p.name, p.version) for g in (old_graph, new_graph) for p in g.packages.values()})
    log(f"  OSV lookup for {len(pairs)} package versions")
    vulns = osv.lookup(pairs, cache_dir=cache)
    write_json(out / "vulns.json", {f"{n}@{v}": vl for (n, v), vl in vulns.items()})

    # Cheap reachability probe: does first-party code import this package's likely root?
    first_party_imports = set(adapter.imports_root(repo, list({
        c for p in new_graph.packages.values() for c in _candidates(p.name)})))

    items: list[WorkItem] = []
    fp_name = _project_name(repo)
    items.append(WorkItem(package=fp_name, purl=f"pkg:generic/{fp_name}@{head_sha[:12]}",
                          old_version=base_sha[:12], new_version=head_sha[:12], depth=0,
                          change="first_party", reachable="true", reachable_evidence=["first-party code"],
                          preflight=Preflight(status="not_run", tools={"note": "first-party pre-flight is the PR case; not in this slice"}),
                          vulns_old=[], vulns_new=[], parents=[]))
    names = sorted(set(old_graph.packages) | set(new_graph.packages))
    for name in names:
        o, n = old_graph.packages.get(name), new_graph.packages.get(name)
        pkg = n or o
        if o and n:
            change = "bumped" if o.version != n.version else "unchanged"
        else:
            change = "added" if n else "removed"
        ev = [f"first-party imports '{c}'" for c in _candidates(name) if c in first_party_imports]
        if ev:
            reachable = "true"
        elif pkg.depth == 1:
            reachable = "unknown"; ev = ["direct dependency, no import of the obvious root name; analysis resolves import names from the wheel"]
        else:
            reachable = "unknown"; ev = ["transitive; call-graph reachability not in this slice"]
        v_old = [v.id for v in vulns.get((name, o.version), [])] if o else []
        v_new = [v.id for v in vulns.get((name, n.version), [])] if n else []
        mal = [v.id for v in vulns.get((name, pkg.version), []) if v.malicious]
        gd = _guarddog(name, pkg.version) if change in ("added", "bumped") else {"status": "skipped", "reason": "unchanged version"}
        findings = [{"tool": "openssf-malicious-packages", "id": m} for m in mal]
        if gd.get("status") == "ran" and gd.get("returncode"):
            findings.append({"tool": "guarddog", "output": gd.get("stdout")})
        status = "hit" if findings else ("clean" if gd.get("status") == "ran" or mal == [] else "not_run")
        items.append(WorkItem(package=name, purl=pkg.purl, old_version=o.version if o else None,
                              new_version=n.version if n else None, depth=pkg.depth, change=change,
                              reachable=reachable, reachable_evidence=ev,
                              preflight=Preflight(status=status, findings=findings,
                                                  tools={"openssf-malicious-packages": "ran (via OSV)", "guarddog": gd.get("status", "not_installed"),
                                                         "capslock": "n/a (Go only)"}),
                              vulns_old=v_old, vulns_new=v_new, parents=pkg.parents))
    wl = WorkList(run_id=run_id, created=now_iso(), mode=mode, source_dir=str(repo),
                  old_manifest=old_graph.manifest if base else None, new_manifest=new_graph.manifest, items=items)
    write_json(out / "worklist.json", wl)
    changed = [i for i in items if i.change in ("added", "removed", "bumped")]
    vuln_items = [i for i in items if i.vulns_new]
    log(f"  work list: {len(items)} rows, {len(changed)} changed, {len(vuln_items)} with known vulnerabilities at head")
    return wl


def _candidates(dist_name: str) -> list[str]:
    n = dist_name.lower()
    c = {n.replace("-", "_"), n.replace("-", ""), re.sub(r"^python[-_]", "", n).replace("-", "_"),
         re.sub(r"^py", "", n).replace("-", "_")}
    if n == "pillow":
        c.add("PIL")
    if n == "pyyaml":
        c.add("yaml")
    if n == "beautifulsoup4":
        c.add("bs4")
    return sorted(x for x in c if x)
