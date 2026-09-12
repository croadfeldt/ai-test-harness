"""Python ecosystem adapter: resolve_graph, extract_api, api_diff, plus call-site and source-diff
helpers the analysis stage needs. build/run_tests/coverage/mutate/fuzz arrive with the execution slice.

Tool choices (docs/05-capability-map.md, docs/09 Python flow): pip's own resolver for the graph, the
standard-library ast for API surface and call sites. No model is involved anywhere in this file.
"""
from __future__ import annotations

import ast
import difflib
import re
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement

from ..model import ApiChange, ApiSymbol, CallSite, DependencyGraph, Package
from ..util import HarnessError, log, read_json, run, sha256_file, tool_available

ECOSYSTEM = "python"
EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "site-packages", "__pycache__", "build", "dist",
                 ".tox", ".mypy_cache", ".pytest_cache", "static"}
PLATFORMS = ["manylinux_2_17_x86_64", "manylinux2014_x86_64", "manylinux_2_28_x86_64", "any"]


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def purl(name: str, version: str) -> str:
    return f"pkg:pypi/{normalize(name)}@{version}"


# ---------------------------------------------------------------- resolve_graph

def _pip_report(manifest: Path, python_version: str | None, tmp: Path) -> tuple[dict, str]:
    """Resolve with pip in --dry-run --report mode.

    When a target interpreter version is given and podman is available, resolution runs inside that
    interpreter's own container image, the same image the sandbox uses. pip on the host cannot be
    trusted to evaluate environment markers (python_version, platform_machine) for a different
    interpreter: it silently dropped sqlalchemy's greenlet dependency when asked to resolve for 3.12
    from a 3.14 host. Resolution executes no package code: wheels only, metadata only.
    """
    report = tmp / "report.json"
    if python_version and tool_available("podman"):
        image = f"docker.io/library/python:{python_version}-slim"
        mdir = tmp / "m"; mdir.mkdir(exist_ok=True)
        (mdir / "req.txt").write_text(manifest.read_text())
        cmd = ["podman", "run", "--rm", "-v", f"{mdir}:/m:ro,Z", "-v", f"{tmp}:/out:rw,Z", image, "sh", "-c",
               "pip install --dry-run --ignore-installed --quiet --only-binary=:all: --report /out/report.json -r /m/req.txt"]
        proc = run(cmd, check=False, timeout=900)
        if proc.returncode == 0 and report.exists():
            ver = run(["podman", "run", "--rm", image, "python", "-c", "import pip,sys;print(sys.version.split()[0], pip.__version__)"], check=False).stdout.strip()
            return read_json(report), f"pip --dry-run --report inside {image} (python/pip {ver}), wheels only"
        log(f"  container resolution for Python {python_version} failed, falling back to the host interpreter: "
            f"{proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ''}")
    base = [sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed", "--quiet",
            "--report", str(report), "-r", str(manifest)]
    run(base, timeout=900)
    return read_json(report), f"pip {_pip_version()} --dry-run --report, host interpreter {sys.version.split()[0]} (markers evaluated for the host, not the target)"


def _pip_version() -> str:
    import pip
    return pip.__version__


def _edges(requires_dist: list[str], resolved: set[str], env: dict) -> tuple[list[str], list[str]]:
    """(hard edges, optional edges). An optional edge is declared under an extra or a marker that is
    false for this environment; the package may still import it at runtime (FastAPI and python-multipart)."""
    hard, optional = set(), set()
    for spec in requires_dist or []:
        try:
            req = Requirement(spec)
        except InvalidRequirement:
            continue
        target = normalize(req.name)
        if target not in resolved:
            continue
        if req.marker is not None:
            try:
                if not req.marker.evaluate({**env, "extra": ""}):
                    optional.add(target)
                    continue
            except Exception:
                pass
        hard.add(target)
    return sorted(hard), sorted(optional - hard)


def resolve_graph(source_dir: Path, manifest: Path, python_version: str | None = None) -> DependencyGraph:
    """Full transitive graph from pip's resolver, without installing anything."""
    with tempfile.TemporaryDirectory(prefix="harness-resolve-") as td:
        report, resolver = _pip_report(manifest, python_version, Path(td))
    env = default_environment()
    if python_version:
        env["python_version"] = python_version
        env["python_full_version"] = python_version + ".0"
    installs = report.get("install", [])
    resolved = {normalize(i["metadata"]["name"]) for i in installs}
    pkgs: dict[str, Package] = {}
    for i in installs:
        md = i["metadata"]
        name = normalize(md["name"])
        hard, optional = _edges(md.get("requires_dist", []), resolved, env)
        pkgs[name] = Package(name=name, version=md["version"], purl=purl(name, md["version"]),
                             depth=1 if i.get("requested") else 99, direct=bool(i.get("requested")),
                             requires=hard, optional_requires=optional,
                             download_url=(i.get("download_info") or {}).get("url"))
    # Depth = shortest path from a requested root; parents = who requires it.
    for p in pkgs.values():
        for child in p.requires:
            if p.name not in pkgs[child].parents:
                pkgs[child].parents.append(p.name)
    frontier = [p.name for p in pkgs.values() if p.direct]
    seen = set(frontier)
    depth = 1
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
            p.depth = 2  # resolved through an extra or environment marker we could not evaluate
            p.parents = p.parents or ["<unresolved-edge>"]
    return DependencyGraph(ecosystem=ECOSYSTEM, source_dir=str(source_dir), manifest=str(manifest),
                           manifest_digest=sha256_file(manifest), resolver=resolver,
                           python_version=python_version, packages=dict(sorted(pkgs.items())))


# ---------------------------------------------------------------- fetch + unpack

def fetch(name: str, version: str, cache_dir: Path, python_version: str | None) -> Path:
    """Download the wheel (or sdist when no wheel exists) for one exact version. Cached."""
    dest = cache_dir / "archives"
    dest.mkdir(parents=True, exist_ok=True)
    existing = [p for p in dest.glob(f"{name.replace('-', '_')}-{version}*") if p.suffix in (".whl", ".gz", ".zip")]
    existing += [p for p in dest.glob(f"{name}-{version}*") if p.suffix in (".whl", ".gz", ".zip")]
    if existing:
        return existing[0]
    base = [sys.executable, "-m", "pip", "download", "--no-deps", "--quiet", "--dest", str(dest), f"{name}=={version}"]
    cmd = base + ["--only-binary=:all:"]
    if python_version:
        cmd += ["--python-version", python_version, "--implementation", "cp"]
        for plat in PLATFORMS:
            cmd += ["--platform", plat]
    proc = run(cmd, check=False, timeout=600)
    if proc.returncode != 0:
        proc = run(base + ["--no-binary=:all:", "--no-build-isolation"], check=False, timeout=600)
        if proc.returncode != 0:
            raise HarnessError(f"cannot download {name}=={version}: {proc.stderr.strip()[-500:]}")
    found = sorted(dest.glob(f"*{version}*"), key=lambda p: p.stat().st_mtime)
    if not found:
        raise HarnessError(f"downloaded {name}=={version} but no archive appeared in {dest}")
    return found[-1]


def unpack(archive: Path, cache_dir: Path) -> Path:
    out = cache_dir / "unpacked" / archive.name
    if out.exists():
        return out
    out.mkdir(parents=True)
    if archive.suffix == ".whl" or archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as z:
            z.extractall(out)
    else:
        with tarfile.open(archive) as t:
            t.extractall(out, filter="data")
    return out


def import_names(unpacked: Path, dist_name: str) -> list[str]:
    """Top-level import names, from the wheel's top_level.txt when present, else from the layout."""
    for tl in unpacked.glob("*.dist-info/top_level.txt"):
        names = [n.strip() for n in tl.read_text().splitlines() if n.strip() and not n.startswith("_")]
        if names:
            return sorted(names)
    root = unpacked
    inner = [d for d in unpacked.iterdir() if d.is_dir() and not d.name.endswith(".dist-info")]
    if len(inner) == 1 and (inner[0] / "src").exists():
        root = inner[0] / "src"
    elif len(inner) == 1 and not (inner[0] / "__init__.py").exists() and any((inner[0] / x).exists() for x in ("setup.py", "pyproject.toml")):
        root = inner[0]
    names = set()
    for p in root.iterdir():
        if p.name.startswith((".", "_")) or p.name.endswith((".dist-info", ".data", ".egg-info")):
            continue
        if p.is_dir() and (p / "__init__.py").exists():
            names.add(p.name)
        elif p.suffix == ".py" and p.stem not in ("setup", "conftest"):
            names.add(p.stem)
    return sorted(names) or [normalize(dist_name).replace("-", "_")]


# ---------------------------------------------------------------- extract_api

def _sig(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = ast.unparse(node.args)
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"({args}){ret}"


def _first_line(doc: str | None) -> str:
    return (doc or "").strip().splitlines()[0][:160] if doc and doc.strip() else ""


def extract_api(unpacked: Path, names: list[str]) -> list[ApiSymbol]:
    """Public symbols with signatures, from the AST. Private modules and names are skipped."""
    symbols: list[ApiSymbol] = []
    roots = []
    for cand in [unpacked, *[d for d in unpacked.iterdir() if d.is_dir()]]:
        for n in names:
            if (cand / n).is_dir() or (cand / f"{n}.py").exists():
                roots.append((cand, n))
        if (cand / "src").is_dir():
            for n in names:
                if (cand / "src" / n).is_dir():
                    roots.append((cand / "src", n))
    seen_files = set()
    for base, n in roots:
        target = base / n if (base / n).is_dir() else base / f"{n}.py"
        files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        for f in files:
            if f in seen_files:
                continue
            seen_files.add(f)
            rel = f.relative_to(base)
            parts = list(rel.with_suffix("").parts)
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if any(p.startswith("_") and p != "__init__" for p in parts) or any(p in ("tests", "test", "testing") for p in parts):
                continue
            module = ".".join(parts)
            try:
                tree = ast.parse(f.read_text(errors="replace"))
            except (SyntaxError, ValueError):
                continue
            symbols.append(ApiSymbol(module=module, qualname=module, kind="module", signature="",
                                     doc=_first_line(ast.get_docstring(tree)), file=str(rel), line=1))
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                    symbols.append(ApiSymbol(module, f"{module}.{node.name}", "function", _sig(node),
                                             _first_line(ast.get_docstring(node)), str(rel), node.lineno))
                elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    bases = ", ".join(ast.unparse(b) for b in node.bases)
                    symbols.append(ApiSymbol(module, f"{module}.{node.name}", "class", f"({bases})",
                                             _first_line(ast.get_docstring(node)), str(rel), node.lineno))
                    for m in node.body:
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and (not m.name.startswith("_") or m.name == "__init__"):
                            symbols.append(ApiSymbol(module, f"{module}.{node.name}.{m.name}", "method", _sig(m),
                                                     _first_line(ast.get_docstring(m)), str(rel), m.lineno))
    return symbols


# ---------------------------------------------------------------- api_diff

def _required_params(signature: str) -> list[str]:
    if not signature.startswith("("):
        return []
    body = signature.split(" -> ")[0]
    try:
        fn = ast.parse(f"def f{body}: pass").body[0]
    except SyntaxError:
        return []
    a = fn.args
    positional = a.posonlyargs + a.args
    n_default = len(a.defaults)
    required = [p.arg for p in positional[: len(positional) - n_default]]
    required += [k.arg for k, d in zip(a.kwonlyargs, a.kw_defaults) if d is None]
    return [r for r in required if r not in ("self", "cls")]


def api_diff(old: list[ApiSymbol], new: list[ApiSymbol]) -> list[ApiChange]:
    o = {s.qualname: s for s in old}
    n = {s.qualname: s for s in new}
    changes: list[ApiChange] = []
    for q in sorted(set(o) - set(n)):
        changes.append(ApiChange(q, "removed", True, o[q].signature or None, None, f"{o[q].kind} removed"))
    for q in sorted(set(n) - set(o)):
        changes.append(ApiChange(q, "added", False, None, n[q].signature or None, f"{n[q].kind} added"))
    for q in sorted(set(o) & set(n)):
        if o[q].signature == n[q].signature or o[q].kind == "module":
            continue
        ro, rn = _required_params(o[q].signature), _required_params(n[q].signature)
        if ro != rn:
            reason = f"required parameters changed: {ro} -> {rn}"
            breaking = True
        else:
            reason = "optional parameters or annotations changed"
            breaking = False
        changes.append(ApiChange(q, "changed", breaking, o[q].signature, n[q].signature, reason))
    return changes


# ---------------------------------------------------------------- first-party call sites

def first_party_files(source_dir: Path) -> list[Path]:
    out = []
    for p in source_dir.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in p.relative_to(source_dir).parts):
            continue
        out.append(p)
    return sorted(out)


def _is_test(rel: Path) -> bool:
    return any(part in ("tests", "test") for part in rel.parts) or rel.name.startswith("test_") or rel.name.endswith("_test.py")


class _Visitor(ast.NodeVisitor):
    def __init__(self, roots: set[str], rel: str, lines: list[str], in_test: bool):
        self.roots, self.rel, self.lines, self.in_test = roots, rel, lines, in_test
        self.alias: dict[str, str] = {}
        self.sites: list[CallSite] = []

    def visit_Import(self, node):
        for a in node.names:
            if a.name.split(".")[0] in self.roots:
                self.alias[(a.asname or a.name.split(".")[0])] = a.name if a.asname else a.name.split(".")[0]
                self._add(a.name, node.lineno)

    def visit_ImportFrom(self, node):
        if node.module and node.level == 0 and node.module.split(".")[0] in self.roots:
            for a in node.names:
                full = f"{node.module}.{a.name}"
                self.alias[a.asname or a.name] = full
                self._add(full, node.lineno)

    def _dotted(self, node) -> str | None:
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr); node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
            parts.reverse()
            head = parts[0]
            if head in self.alias:
                return ".".join([self.alias[head], *parts[1:]])
        return None

    def visit_Attribute(self, node):
        full = self._dotted(node)
        if full:
            self._add(full, node.lineno)
        else:
            self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in self.alias and isinstance(node.ctx, ast.Load):
            self._add(self.alias[node.id], node.lineno)

    def _add(self, symbol: str, line: int):
        ctx = self.lines[line - 1].strip()[:160] if 0 < line <= len(self.lines) else ""
        self.sites.append(CallSite(symbol=symbol, file=self.rel, line=line, in_test=self.in_test, context=ctx))


def call_sites(source_dir: Path, names: list[str]) -> list[CallSite]:
    """Every place first-party code imports or references a symbol from the given import roots."""
    roots = set(names)
    sites: list[CallSite] = []
    for f in first_party_files(source_dir):
        try:
            src = f.read_text(errors="replace")
            tree = ast.parse(src)
        except (SyntaxError, ValueError):
            continue
        rel = f.relative_to(source_dir)
        v = _Visitor(roots, str(rel), src.splitlines(), _is_test(rel))
        v.visit(tree)
        sites.extend(v.sites)
    # de-duplicate identical (symbol, file, line)
    uniq = {(s.symbol, s.file, s.line): s for s in sites}
    return [uniq[k] for k in sorted(uniq)]


def imports_root(source_dir: Path, candidates: list[str]) -> list[str]:
    """Cheap reachability probe for intake: which candidate import roots does first-party code import?"""
    pat = re.compile(r"^\s*(?:from\s+([A-Za-z_][\w]*)|import\s+([A-Za-z_][\w]*))", re.M)
    hits = set()
    for f in first_party_files(source_dir):
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        for m in pat.finditer(text):
            root = m.group(1) or m.group(2)
            if root in candidates:
                hits.add(root)
    return sorted(hits)


# ---------------------------------------------------------------- source diff + upstream tests

def source_diff(old_dir: Path, new_dir: Path) -> dict:
    def pyfiles(d: Path) -> dict[str, Path]:
        out = {}
        for p in d.rglob("*.py"):
            rel = p.relative_to(d).parts
            rel = rel[1:] if rel and re.match(r".*-\d", rel[0]) else rel  # strip versioned top dir of an sdist
            out["/".join(rel)] = p
        return out
    o, n = pyfiles(old_dir), pyfiles(new_dir)
    added, removed, changed = sorted(set(n) - set(o)), sorted(set(o) - set(n)), []
    plus = minus = 0
    for rel in sorted(set(o) & set(n)):
        a, b = o[rel].read_text(errors="replace").splitlines(), n[rel].read_text(errors="replace").splitlines()
        if a == b:
            continue
        changed.append(rel)
        for line in difflib.unified_diff(a, b, lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++"):
                plus += 1
            elif line.startswith("-") and not line.startswith("---"):
                minus += 1
    for rel in added:
        plus += len(n[rel].read_text(errors="replace").splitlines())
    for rel in removed:
        minus += len(o[rel].read_text(errors="replace").splitlines())
    return {"files_added": added[:50], "files_removed": removed[:50], "files_changed": changed[:100],
            "counts": {"added": len(added), "removed": len(removed), "changed": len(changed)},
            "lines_added": plus, "lines_removed": minus, "tool": "difflib unified, python files only"}


def upstream_tests(unpacked: Path) -> dict:
    files = [str(p.relative_to(unpacked)) for p in unpacked.rglob("*.py")
             if any(part in ("tests", "test") for part in p.relative_to(unpacked).parts) or p.name.startswith("test_")]
    return {"present": bool(files), "count": len(files), "files": files[:30],
            "note": "wheels rarely ship tests; an sdist or the upstream repository is the source when count is 0"}


def static_analysis(files: list[Path], source_dir: Path) -> dict:
    if not tool_available("bandit") or not files:
        return {"tool": "bandit", "status": "not_run", "reason": "bandit not installed" if files else "no files"}
    proc = run(["bandit", "-q", "-f", "json", *[str(f) for f in files]], cwd=source_dir, check=False, timeout=300)
    try:
        import json
        data = json.loads(proc.stdout)
        return {"tool": "bandit", "status": "ran", "issues": data.get("results", [])[:50],
                "totals": data.get("metrics", {}).get("_totals", {})}
    except ValueError:
        return {"tool": "bandit", "status": "error", "stderr": proc.stderr[-500:]}
