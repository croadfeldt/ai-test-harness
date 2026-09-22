"""Fixed-candidate environment for a package that is vulnerable at head and unchanged by the change.

Blueprint section 5 stage 3 (CVE-targeted tests) and docs/02: the fix-pinning test runs on the
vulnerable version and on the fixed version. When the change did not bring the fixed version, the
harness resolves one: the head manifest with the package raised to the advisories' fixed version.
If pip cannot satisfy that because a direct dependency pins the package (fastapi pinning starlette),
the harness relaxes the pins of the package's direct dependents and tries again, and records exactly
what had to move. That record is itself a packet finding: the upgrade path.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from packaging.version import InvalidVersion, Version

from .. import adapters, sandbox
from ..util import log, now_iso, read_json, write_json


def _max_version(versions: list[str]) -> str | None:
    parsed = []
    for v in versions:
        try:
            parsed.append((Version(v), v))
        except InvalidVersion:
            continue
    return max(parsed)[1] if parsed else None


def _override_manifest(text: str, overrides: dict[str, str]) -> str:
    """Rewrite requirement lines for the named packages; append any that were absent."""
    out, seen = [], set()
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*([<>=!~].*)?$", line)
        if m and adapters.python.normalize(m.group(1)) in overrides:
            name = adapters.python.normalize(m.group(1)); seen.add(name)
            out.append(f"{m.group(1)}{m.group(2) or ''}{overrides[name]}")
        else:
            out.append(line)
    for name, spec in overrides.items():
        if name not in seen:
            out.append(f"{name}{spec}")
    return "\n".join(out) + "\n"


def fixed_candidate(workdir: Path, pkg: str, python_version: str = "3.12") -> dict:
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    vdoc = read_json(workdir / "analyze" / pkg / "vulns.json")
    graph = read_json(workdir / "intake" / "graph.new.json")
    wl = read_json(workdir / "intake" / "worklist.json")
    out_path = workdir / "analyze" / pkg / "fixed-candidate.json"
    fixed = _max_version([f for v in vdoc["vulns"] for f in v["fixed_versions"]])
    head = facts["new_version"]
    rec = {"package": pkg, "head_version": head, "generated": now_iso(), "status": "none", "fixed_version": fixed,
           "overrides": {}, "attempts": [], "requirements": None, "note": ""}
    if not fixed or not vdoc["vulns"]:
        rec["note"] = "no advisory names a fixed version"; write_json(out_path, rec); return rec
    try:
        if Version(fixed) <= Version(head):
            rec["note"] = f"advisories' fixed version {fixed} is not above head {head}"; write_json(out_path, rec); return rec
    except InvalidVersion:
        pass
    from .. import config
    repo = config.resolve_repo(wl["source_dir"], None, workdir)
    manifest_name = wl["new_manifest"].split("@")[0]
    manifest_text = (repo / manifest_name).read_text()
    adapter = adapters.get("python")
    direct_dependents = sorted(p for p, d in graph["packages"].items() if pkg in d["requires"] and d["direct"])
    plans = [({pkg: f"=={fixed}"}, "pin the package to the fixed version, nothing else moves")]
    if direct_dependents:
        relax = {pkg: f"=={fixed}"}
        relax.update({d: f">={graph['packages'][d]['version']}" for d in direct_dependents})
        plans.append((relax, f"also let direct dependents move: {direct_dependents}"))
    for overrides, why in plans:
        with tempfile.TemporaryDirectory(prefix="harness-candidate-") as td:
            m = Path(td) / "requirements.txt"
            m.write_text(_override_manifest(manifest_text, overrides))
            try:
                g = adapter.resolve_graph(repo, m, python_version)
                reqs = [f"{p['name']}=={p['version']}" for p in [vars(x) if not isinstance(x, dict) else x for x in g.packages.values()]]
                moved = {n: (graph["packages"][n]["version"], g.packages[n].version) for n in g.packages
                         if n in graph["packages"] and graph["packages"][n]["version"] != g.packages[n].version}
                rec.update({"status": "resolved", "overrides": overrides, "requirements": reqs, "moved": moved,
                            "note": why, "resolver": g.resolver})
                rec["attempts"].append({"overrides": overrides, "result": "resolved", "moved": len(moved)})
                break
            except Exception as e:
                msg = str(e).strip().splitlines()[-1][:300] if str(e).strip() else type(e).__name__
                rec["attempts"].append({"overrides": overrides, "result": "failed", "error": msg})
    if rec["status"] == "resolved":
        wh = sandbox.prefetch_wheelhouse(rec["requirements"], python_version, workdir / "cache" / "wheelhouse" / f"fixed-{pkg}")
        rec["wheelhouse"] = str(wh.relative_to(workdir)) if wh.is_relative_to(workdir) else str(wh)
        log(f"    {pkg}: fixed candidate {fixed} resolved ({rec['note']}); {len(rec['moved'])} package(s) move: "
            + ", ".join(f"{k} {a}->{b}" for k, (a, b) in list(rec["moved"].items())[:6]))
    else:
        rec["note"] = "no resolvable environment with the fixed version, even letting direct dependents move"
        log(f"    {pkg}: no fixed candidate: {rec['attempts'][-1].get('error', '')[:120]}")
    write_json(out_path, rec)
    return rec
