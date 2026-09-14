"""Go ecosystem adapter: the same interface as the Python adapter, with Go's own tools.

Graph: `go list -m -json all` and `go mod graph` on the module at the requested commit, so the
graph is what the Go toolchain resolves, not what a file says. Source: `go mod download` into the
module cache. API surface and call sites: `gohelper`, a small Go program in this package built with
the toolchain at first use, parsing with go/ast. Contract diff: any signature change is breaking; Go
has no optional parameters. Vulnerabilities: OSV's Go ecosystem, keyed by module path.
Stages 1 and 2 only in this slice; generation and execution for Go follow.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..model import ApiChange, ApiSymbol, CallSite, DependencyGraph, Package
from ..util import HarnessError, http_json, log, read_json, run, sha256_file, sha256_text, write_json

ECOSYSTEM = "go"
OSV_ECOSYSTEM = "Go"
MANIFEST = "go.mod"
EXCLUDED_DIRS = {".git", "vendor", "node_modules", "testdata"}
HELPER_SRC = Path(__file__).parent / "gohelper"
_HELPER: Path | None = None


def normalize(name: str) -> str:
    return name


def purl(name: str, version: str) -> str:
    return f"pkg:golang/{name}@{version}"


def _helper() -> Path:
    global _HELPER
    if _HELPER and _HELPER.exists():
        return _HELPER
    if not shutil.which("go"):
        raise HarnessError("the Go toolchain is required for the go adapter")
    out = Path(tempfile.gettempdir()) / f"ai-test-harness-gohelper-{sha256_text(str(HELPER_SRC))[7:19]}"
    run(["go", "build", "-o", str(out), "."], cwd=HELPER_SRC, timeout=300)
    _HELPER = out
    return out


def _go(args: list[str], cwd: Path, timeout: int = 600) -> str:
    proc = run(["go", *args], cwd=cwd, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise HarnessError(f"go {' '.join(args)} failed: {proc.stderr.strip()[-600:]}")
    return proc.stdout


def _json_stream(text: str) -> list[dict]:
    docs, buf, depth = [], [], 0
    for line in text.splitlines():
        buf.append(line)
        depth += line.count("{") - line.count("}")
        if depth == 0 and buf:
            chunk = "\n".join(buf).strip()
            if chunk:
                docs.append(json.loads(chunk))
            buf = []
    return docs


# ---------------------------------------------------------------- resolve_graph

def resolve_graph(source_dir: Path, manifest: Path, python_version: str | None = None, ref: str | None = None) -> DependencyGraph:
    """The module graph the Go toolchain resolves at `ref` (or the working tree)."""
    with tempfile.TemporaryDirectory(prefix="harness-go-") as td:
        tree = Path(td) / "src"
        tree.mkdir()
        if ref:
            proc = subprocess.run(["git", "-C", str(source_dir), "archive", ref], capture_output=True, timeout=300)
            if proc.returncode != 0:
                raise HarnessError(f"git archive {ref} failed: {proc.stderr.decode()[-300:]}")
            subprocess.run(["tar", "-x", "-C", str(tree)], input=proc.stdout, check=True)
        else:
            shutil.copytree(source_dir, tree, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git"))
        mods = _json_stream(_go(["list", "-m", "-json", "all"], tree))
        edges = _go(["mod", "graph"], tree)
    main = next((m["Path"] for m in mods if m.get("Main")), None)
    pkgs: dict[str, Package] = {}
    for m in mods:
        if m.get("Main") or not m.get("Version"):
            continue
        pkgs[m["Path"]] = Package(name=m["Path"], version=m["Version"], purl=purl(m["Path"], m["Version"]),
                                  depth=99, direct=not m.get("Indirect", False), download_url=None)
    # go mod graph: "from@ver to@ver" lines; edges among resolved modules only (MVS picks one version)
    req: dict[str, set[str]] = {n: set() for n in pkgs}
    for line in edges.splitlines():
        a, _, b = line.partition(" ")
        src = a.split("@")[0]; dst = b.split("@")[0]
        if dst in pkgs and (src == main or src in pkgs):
            if src == main:
                continue
            req[src].add(dst)
    for n, p in pkgs.items():
        p.requires = sorted(req[n])
        for c in p.requires:
            if n not in pkgs[c].parents:
                pkgs[c].parents.append(n)
    frontier = [n for n, p in pkgs.items() if p.direct]
    seen, depth = set(frontier), 1
    while frontier:
        nxt = []
        for n in frontier:
            pkgs[n].depth = min(pkgs[n].depth, depth)
            for c in pkgs[n].requires:
                if c not in seen:
                    seen.add(c); nxt.append(c)
        frontier, depth = nxt, depth + 1
    for p in pkgs.values():
        if p.depth == 99:
            p.depth = 2; p.parents = p.parents or ["<unresolved-edge>"]
    return DependencyGraph(ecosystem=ECOSYSTEM, source_dir=source_dir.name, manifest=manifest.name, manifest_digest=sha256_file(manifest),
                           resolver=f"go list -m -json all + go mod graph ({_go(['version'], source_dir).strip()})", python_version=None,
                           packages=dict(sorted(pkgs.items())))


# ---------------------------------------------------------------- fetch + unpack

def fetch(name: str, version: str, cache_dir: Path, python_version: str | None = None) -> Path:
    """The module's source directory from the Go module cache (`go mod download`)."""
    env_dir = cache_dir / "gomodcache"
    env_dir.mkdir(parents=True, exist_ok=True)
    import os
    env = {**os.environ, "GOMODCACHE": str(env_dir.resolve()), "GOFLAGS": "-mod=mod"}
    proc = subprocess.run(["go", "mod", "download", "-json", f"{name}@{version}"], capture_output=True, text=True, env=env, timeout=600, cwd=tempfile.gettempdir())
    if proc.returncode != 0:
        raise HarnessError(f"go mod download {name}@{version}: {proc.stderr.strip()[-400:]}")
    docs = _json_stream(proc.stdout)
    if not docs or "Dir" not in docs[-1]:
        raise HarnessError(f"go mod download {name}@{version}: no Dir in {proc.stdout[:200]!r}")
    return Path(docs[-1]["Dir"])


def unpack(archive: Path, cache_dir: Path) -> Path:
    return archive   # already a directory


def import_names(unpacked: Path, dist_name: str) -> list[str]:
    m = re.search(r"^module\s+(\S+)", (unpacked / "go.mod").read_text(), re.M) if (unpacked / "go.mod").exists() else None
    return [m.group(1) if m else dist_name]


# ---------------------------------------------------------------- extract_api / api_diff

def extract_api(unpacked: Path, names: list[str]) -> list[ApiSymbol]:
    modpath = names[0] if names else ""
    out = subprocess.run([str(_helper()), "api", str(unpacked)], capture_output=True, text=True, timeout=600)
    if out.returncode != 0:
        raise HarnessError(f"gohelper api failed: {out.stderr[-300:]}")
    syms = []
    for s in json.loads(out.stdout).get("symbols") or []:
        pkg = f"{modpath}/{s['module']}" if s["module"] else modpath
        syms.append(ApiSymbol(module=pkg, qualname=f"{pkg}.{s['qualname'].split('.', 1)[-1] if s['module'] else s['qualname']}",
                              kind=s["kind"], signature=s["signature"], doc=s["doc"], file=s["file"], line=s["line"]))
    return syms


def api_diff(old: list[ApiSymbol], new: list[ApiSymbol]) -> list[ApiChange]:
    o = {s.qualname: s for s in old}; n = {s.qualname: s for s in new}
    changes = []
    for q in sorted(set(o) - set(n)):
        changes.append(ApiChange(q, "removed", True, o[q].signature or None, None, f"{o[q].kind} removed"))
    for q in sorted(set(n) - set(o)):
        changes.append(ApiChange(q, "added", False, None, n[q].signature or None, f"{n[q].kind} added"))
    for q in sorted(set(o) & set(n)):
        if o[q].signature != n[q].signature:
            changes.append(ApiChange(q, "changed", True, o[q].signature, n[q].signature, "signature changed (Go has no optional parameters)"))
    return changes


# ---------------------------------------------------------------- call sites and friends

def first_party_files(source_dir: Path) -> list[Path]:
    return sorted(p for p in source_dir.rglob("*.go") if not any(part in EXCLUDED_DIRS for part in p.relative_to(source_dir).parts))


def call_sites(source_dir: Path, names: list[str]) -> list[CallSite]:
    sites = []
    for modpath in names:
        out = subprocess.run([str(_helper()), "sites", str(source_dir), modpath], capture_output=True, text=True, timeout=600)
        if out.returncode != 0:
            continue
        for s in json.loads(out.stdout).get("sites") or []:   # Go encodes an empty slice as null
            sites.append(CallSite(symbol=s["symbol"], file=s["file"], line=s["line"], in_test=s["in_test"], context=s["context"]))
    uniq = {(s.symbol, s.file, s.line): s for s in sites}
    return [uniq[k] for k in sorted(uniq)]


def imports_root(source_dir: Path, candidates: list[str]) -> list[str]:
    pat = re.compile(r'^\s*(?:import\s+)?(?:\w+\s+)?"([^"]+)"', re.M)
    hits = set()
    for f in first_party_files(source_dir):
        if f.name.endswith("_test.go"):
            continue
        for m in pat.finditer(f.read_text(errors="replace")):
            p = m.group(1)
            for c in candidates:
                if p == c or p.startswith(c + "/"):
                    hits.add(c)
    return sorted(hits)


def import_candidates(dist_name: str) -> list[str]:
    return [dist_name]   # a Go module is imported by its own path


def source_diff(old_dir: Path, new_dir: Path) -> dict:
    from . import python as py
    return py.source_diff(old_dir, new_dir, suffix=".go")


def source_patch(old_dir: Path, new_dir: Path, max_lines: int = 1500) -> str:
    from . import python as py
    return py.source_patch(old_dir, new_dir, max_lines=max_lines, suffix=".go")


def upstream_tests(unpacked: Path) -> dict:
    files = [str(p.relative_to(unpacked)) for p in unpacked.rglob("*_test.go")]
    return {"present": bool(files), "count": len(files), "files": files[:30], "note": "Go modules ship their tests in the module"}


def static_analysis(files: list[Path], source_dir: Path) -> dict:
    if shutil.which("gosec") and files:
        proc = run(["gosec", "-fmt=json", "-quiet", *[str(f) for f in files][:50]], cwd=source_dir, check=False, timeout=300)
        try:
            data = json.loads(proc.stdout)
            return {"tool": "gosec", "status": "ran", "issues": data.get("Issues", [])[:50]}
        except ValueError:
            return {"tool": "gosec", "status": "error"}
    return {"tool": "gosec", "status": "not_run", "reason": "gosec not installed" if files else "no files"}


def metadata(name: str, version: str, cache_dir: Path | None):
    """deps.dev: license and links for a module version; no long description exists for Go modules."""
    from urllib.parse import quote
    key = f"{name.replace('/', '_')}-{version}.json"
    if cache_dir and (cache_dir / "depsdev" / key).exists():
        return read_json(cache_dir / "depsdev" / key)
    try:
        data = http_json(f"https://api.deps.dev/v3/systems/go/packages/{quote(name, safe='')}/versions/{quote(version, safe='')}")
    except HarnessError:
        data = None
    slim = {"name": name, "version": version, "summary": "", "keywords": "", "classifiers": [],
            "project_urls": {l.get("label", "link"): l.get("url") for l in (data or {}).get("links", [])},
            "licenses": (data or {}).get("licenses", []), "upload_time": (data or {}).get("publishedAt"),
            "description": "", "description_content_type": None, "yanked": False, "requires_python": None, "requires_dist": []}
    if cache_dir:
        write_json(cache_dir / "depsdev" / key, slim)
    return slim
