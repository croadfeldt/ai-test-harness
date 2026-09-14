"""Stage 4, step 5: mutation testing. Blueprint section 5 stage 4 and section 10 (mutation score).

The capability map names mutmut as the Python mutation engine. mutmut mutates a project's own source
tree; the harness's target is a dependency installed from a wheel, and no mutmut integration for
that exists yet. Until it does, the harness applies its own bounded set of classic mutation
operators to the package's source, restricted to lines the accepted tests execute, and runs the tests
against each mutant in the sandbox. A mutant the tests fail on is killed; one they pass on survived.
The score and each test's kills go into the provenance records. Operators, sample size, and the
seed are recorded so a run can be replayed.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import random
from pathlib import Path

from .. import adapters, sandbox
from ..util import log, now_iso, read_json, write_json

SAMPLE = 25
OPERATORS = ("compare-swap", "boolop-swap", "const-int", "const-bool", "raise-drop", "return-none", "not-drop")


class _Sites(ast.NodeVisitor):
    """Enumerate mutation sites on executed lines."""
    def __init__(self, lines: set[int]):
        self.lines, self.sites = lines, []

    def _on(self, node) -> bool:
        return getattr(node, "lineno", -1) in self.lines

    def visit_Compare(self, node):
        if self._on(node) and len(node.ops) == 1 and type(node.ops[0]) in _SWAP:
            self.sites.append(("compare-swap", node))
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        if self._on(node):
            self.sites.append(("boolop-swap", node))
        self.generic_visit(node)

    def visit_Constant(self, node):
        if self._on(node):
            if isinstance(node.value, bool):
                self.sites.append(("const-bool", node))
            elif isinstance(node.value, int) and not isinstance(node.value, bool) and abs(node.value) < 10 ** 9:
                self.sites.append(("const-int", node))
        self.generic_visit(node)

    def visit_Raise(self, node):
        if self._on(node):
            self.sites.append(("raise-drop", node))
        self.generic_visit(node)

    def visit_Return(self, node):
        if self._on(node) and node.value is not None and not isinstance(node.value, ast.Constant):
            self.sites.append(("return-none", node))
        self.generic_visit(node)

    def visit_UnaryOp(self, node):
        if self._on(node) and isinstance(node.op, ast.Not):
            self.sites.append(("not-drop", node))
        self.generic_visit(node)


_SWAP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
         ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}


def _apply(tree: ast.Module, op: str, target) -> ast.Module:
    """Return a deep copy of the tree with the one site mutated (matched by position and type)."""
    new = copy.deepcopy(tree)
    for node in ast.walk(new):
        if type(node) is type(target) and getattr(node, "lineno", None) == target.lineno and getattr(node, "col_offset", None) == target.col_offset:
            if op == "compare-swap":
                node.ops = [_SWAP[type(node.ops[0])]()]
            elif op == "boolop-swap":
                node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
            elif op == "const-int":
                node.value = node.value + 1
            elif op == "const-bool":
                node.value = not node.value
            elif op == "raise-drop":
                node.__class__ = ast.Pass
                for attr in ("exc", "cause"):
                    if hasattr(node, attr):
                        delattr(node, attr)
            elif op == "return-none":
                node.value = ast.Constant(value=None)
            elif op == "not-drop":
                node.op = ast.UAdd(); node.operand = ast.Call(func=ast.Name(id="bool", ctx=ast.Load()), args=[node.operand], keywords=[])
            return new
    return new


def mutate_package(workdir: Path, pkg: str, python_version: str, sample: int = SAMPLE) -> dict:
    results = read_json(workdir / "execute" / pkg / "results.json")
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    gen = read_json(workdir / "generate" / pkg / "manifest.json")
    cov_path = workdir / "execute" / pkg / "new" / "coverage.json"
    out = workdir / "execute" / pkg / "mutation"
    out.mkdir(parents=True, exist_ok=True)
    roots = [r.split("/")[0] for r in facts["import_names"]]
    keep = {t["name"] for t in results["tests"] if t["versions"]["new"] == "pass" and t["status"] != "flaky"}
    if not keep or not cov_path.exists():
        rec = {"package": pkg, "status": "skipped", "reason": "no passing tests or no coverage", "generated": now_iso()}
        write_json(out / "mutation.json", rec); return rec
    # Tests that pass on head, as one directory (only those tests, cut from the generated files).
    tests_dir = out / "tests"; tests_dir.mkdir(exist_ok=True)
    for f in gen["files"]:
        src = (workdir / "generate" / pkg / f["file"]).read_text()
        tree = ast.parse(src)
        tree.body = [n for n in tree.body if not (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_") and n.name not in keep)]
        if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_") for n in tree.body):
            (tests_dir / Path(f["file"]).name).write_text(ast.unparse(tree) + "\n")
    # Executed lines per package file from the head coverage run.
    cov = json.loads(cov_path.read_text())
    site_pkgs = {}
    for fname, fdata in cov.get("files", {}).items():
        if "site-packages/" in fname and any(f"/{r}/" in fname or fname.endswith(f"/{r}.py") for r in roots):
            rel = fname.split("site-packages/")[-1]
            site_pkgs[rel] = set(fdata.get("executed_lines", []))
    # Source of the installed version from the unpacked wheel in the cache.
    cache = workdir / "cache"
    adapter = adapters.get("python")
    unpacked = adapter.unpack(adapter.fetch(pkg, facts["new_version"], cache, python_version), cache)
    sites = []
    for rel, lines in site_pkgs.items():
        src_path = unpacked / rel
        if not src_path.exists():
            continue
        try:
            tree = ast.parse(src_path.read_text(errors="replace"))
        except SyntaxError:
            continue
        v = _Sites(lines); v.visit(tree)
        for op, node in v.sites:
            sites.append((rel, op, node.lineno, node.col_offset, tree, node))
    seed = int(hashlib.sha256(f"{pkg}{facts['new_version']}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    chosen = rng.sample(sites, min(sample, len(sites))) if sites else []
    log(f"    {pkg}: {len(sites)} mutation sites on {sum(len(l) for l in site_pkgs.values())} executed lines; sampling {len(chosen)} (seed {seed})")
    reqs_new = [f"{p['name']}=={p['version']}" for p in read_json(workdir / "intake" / "graph.new.json")["packages"].values()]
    wheelhouse = workdir / "cache" / "wheelhouse" / "new"
    mutants = []
    for i, (rel, op, line, col, tree, node) in enumerate(chosen, 1):
        mid = f"m{i:03d}"
        mdir = out / "mutants" / mid
        (mdir / Path(rel).parent).mkdir(parents=True, exist_ok=True)
        mutated = _apply(tree, op, node)
        try:
            code = ast.unparse(mutated)
        except Exception as e:
            mutants.append({"id": mid, "file": rel, "line": line, "operator": op, "status": "invalid", "detail": str(e)[:100]}); continue
        (mdir / rel).write_text(code)
        s = sandbox.run_tests(wheelhouse=wheelhouse, requirements=reqs_new, tests_dir=tests_dir, out_dir=mdir / "out",
                              cover=[], label=f"{pkg}-{mid}", overlay_dir=mdir, limits={**sandbox.LIMITS, "timeout_s": 300})
        r = sandbox.parse_junit(Path(s["junit"])) if s["junit"] else {}
        killed_by = sorted({k.split("::")[-1].split("[")[0] for k, v in r.items() if v["status"] in ("fail", "error")})
        if s["timed_out"]:
            status = "killed-timeout"
        elif not r:
            status = "killed-import" if s["returncode"] else "error"
        else:
            status = "killed" if killed_by else "survived"
        mutants.append({"id": mid, "file": rel, "line": line, "operator": op, "status": status, "killed_by": killed_by,
                        "duration_s": s["duration_s"]})
        log(f"      {mid} {op:<13} {rel}:{line} {status}" + (f" by {killed_by[:3]}" if killed_by else ""))
    valid = [m for m in mutants if m["status"] not in ("invalid", "error")]
    killed = [m for m in valid if m["status"].startswith("killed")]
    per_test = {}
    for m in killed:
        for t in m.get("killed_by", []):
            per_test.setdefault(t, []).append(m["id"])
    unique = {t: [mid for mid in ids if sum(1 for mm in killed if t in mm.get("killed_by", []) and mid == mm["id"] and len(mm["killed_by"]) == 1)]
              for t, ids in per_test.items()}
    rec = {"package": pkg, "version": facts["new_version"], "generated": now_iso(), "status": "ran",
           "engine": "harness AST mutator (diff- and coverage-scoped); mutmut integration pending", "operators": list(OPERATORS),
           "seed": seed, "sites": len(sites), "sampled": len(chosen), "valid": len(valid), "killed": len(killed),
           "survived": sum(1 for m in valid if m["status"] == "survived"),
           "score": round(len(killed) / len(valid), 3) if valid else None,
           "per_test": {t: {"killed": ids, "unique": unique.get(t, [])} for t, ids in per_test.items()},
           "mutants": mutants, "tests": sorted(keep)}
    write_json(out / "mutation.json", rec)
    log(f"    {pkg}: mutation score {rec['score']} ({len(killed)} of {len(valid)} killed); {len(per_test)} of {len(keep)} tests killed at least one")
    return rec


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
        outs.append(mutate_package(workdir, pkg, python_version, sample))
    merge_summary(workdir / "execute" / "mutation-summary.json", [{"package": o["package"], "status": o["status"], "score": o.get("score"),
                                                                    "sampled": o.get("sampled"), "killed": o.get("killed")} for o in outs])
    return outs
