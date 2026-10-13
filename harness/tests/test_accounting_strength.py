"""Principle 14, second slice: a behaviour's lines include the private helpers it delegates to, execution is
attributed per test when the sandbox recorded coverage contexts, strength needs the test that executed the
unit to be the one that killed the mutant, and mutation sampling aims at the reached behaviours first."""
import json
import random
import shutil
from pathlib import Path

import pytest

from harness.adapters import python as py
from harness.stages.account import account_package, closure, closure_spans, contexts_by_line, stratified_sample

needs_go = pytest.mark.skipif(shutil.which("go") is None, reason="go toolchain not installed")

SRC = '''
def f(x):
    """public"""
    return _g(x) + 1

def _g(x):
    return _h(x) * 2

def _h(x):
    return x

class C:
    def run(self):
        return self._step()
    def _step(self):
        return 1
'''


def _pkg(tmp: Path) -> Path:
    p = tmp / "pkg"
    p.mkdir(parents=True)
    (p / "__init__.py").write_text("from .core import f, C\n")
    (p / "core.py").write_text(SRC)
    return tmp


def test_python_internals_name_private_helpers_and_who_calls_them(tmp_path):
    root = _pkg(tmp_path)
    doc = py.internals(root, ["pkg"])
    private = {p["qualname"]: p for p in doc["private"]}
    assert set(private) == {"pkg.core._g", "pkg.core._h", "pkg.core.C._step"}
    assert private["pkg.core._g"]["line"] == 6 and private["pkg.core._g"]["end_line"] == 7
    assert doc["calls"] == {"pkg.core.f": ["pkg.core._g"], "pkg.core._g": ["pkg.core._h"], "pkg.core.C.run": ["pkg.core.C._step"]}
    api = py.extract_api(root, ["pkg"])
    f = next(s for s in api if s.qualname == "pkg.core.f")
    assert (f.line, f.end_line) == (2, 4), "public symbols carry an end line"


def test_closure_follows_private_callees_transitively():
    calls = {"a.f": ["a._g"], "a._g": ["a._h", "a._g"], "a._h": []}
    assert closure("a.f", calls) == ["a.f", "a._g", "a._h"]
    spans = {"a.f": ("a.py", 1, 3), "a._g": ("a.py", 5, 6), "a._h": ("a.py", 8, 9)}
    assert [x for (x, *_r) in closure_spans("a.f", spans, calls)] == ["a.f", "a._g", "a._h"]
    assert closure_spans("a.missing", spans, calls) == []


def test_contexts_by_line_maps_coverage_contexts_to_test_names(tmp_path):
    cov = {"files": {"/work/venv/lib/python3.12/site-packages/pkg/core.py": {
        "executed_lines": [2, 3, 6, 7], "contexts": {"3": ["tests.test_pkg.test_f_adds_one", ""], "7": ["setup|tests.test_pkg.test_f_adds_one", "tests.test_pkg.test_other"]}}}}
    p = tmp_path / "coverage.json"
    p.write_text(json.dumps(cov))
    by = contexts_by_line(p, lambda fname: "pkg/core.py" if fname.endswith("pkg/core.py") else None)
    assert by == {"pkg/core.py": {3: {"test_f_adds_one"}, 7: {"test_f_adds_one", "test_other"}}}
    assert contexts_by_line(tmp_path / "missing.json", lambda f: f) == {}


def _run(tmp: Path, *, contexts: bool, killer: str) -> Path:
    """A synthetic run: one reached function `pkg.core.f` whose behaviour lives in `_g` and `_h`; one kept test
    that executed it; one mutant inside `_h`, killed by `killer`."""
    run = tmp / "run"
    (run / "intake").mkdir(parents=True)
    (run / "intake" / "worklist.json").write_text(json.dumps({"ecosystem": "python", "run_id": "t"}))
    a = run / "analyze" / "pkg"; a.mkdir(parents=True)
    (a / "facts.json").write_text(json.dumps({"package": "pkg", "import_names": ["pkg"], "new_version": "1.0", "first_party": None, "call_sites_summary": {}}))
    root = _pkg(tmp / "src")
    api = [s.__dict__ for s in py.extract_api(root, ["pkg"])]
    (a / "api.new.json").write_text(json.dumps({"symbols": api}))
    (a / "internals.json").write_text(json.dumps(py.internals(root, ["pkg"])))
    (a / "call-sites.json").write_text(json.dumps({"sites": [{"symbol": "pkg.f", "file": "app.py", "line": 1, "in_test": False}]}))
    e = run / "execute" / "pkg"; (e / "new").mkdir(parents=True); (e / "mutation").mkdir()
    (e / "results.json").write_text(json.dumps({"tests": [
        {"id": "t::test_f_adds_one", "name": "test_f_adds_one", "status": "pass", "versions": {"old": "pass", "new": "pass"}, "verdict": "candidate", "category": "unit"},
        {"id": "t::test_other", "name": "test_other", "status": "pass", "versions": {"old": "pass", "new": "pass"}, "verdict": "candidate", "category": "unit"}]}))
    fdata = {"executed_lines": [2, 3, 6, 7, 9, 10, 13]}
    if contexts:
        fdata["contexts"] = {str(l): ["tests.test_pkg.test_f_adds_one"] for l in (3, 7, 10)}
        fdata["contexts"]["13"] = ["tests.test_pkg.test_other"]   # C.run, outside f's closure
    (e / "new" / "coverage.json").write_text(json.dumps({"files": {"/work/venv/lib/python3.12/site-packages/pkg/core.py": fdata}}))
    (e / "mutation" / "mutation.json").write_text(json.dumps({"mutants": [{"id": "m001", "file": "pkg/core.py", "line": 10, "status": "killed", "killed_by": [killer]}]}))
    t = run / "triage" / "pkg"; t.mkdir(parents=True)
    (t / "triage.json").write_text(json.dumps({"tests": [{"test_id": "t::test_f_adds_one", "class": "behavior-change"}, {"test_id": "t::test_other", "class": "behavior-change"}]}))
    return run


def test_a_mutant_in_a_private_helper_validates_the_public_function_that_reaches_it(tmp_path):
    run = _run(tmp_path, contexts=True, killer="test_f_adds_one")
    rec = account_package(run, "pkg")
    u = next(x for x in rec["units"] if x["symbol"] == "pkg.core.f")
    assert u["state"] == "validated"
    assert u["evidence"]["closure"] == ["pkg.core.f", "pkg.core._g", "pkg.core._h"]
    assert u["evidence"]["executed_by"] == ["test_f_adds_one"] and u["evidence"]["proven_by"] == ["test_f_adds_one"]
    assert u["evidence"]["attribution"].startswith("per-test")


def test_strength_needs_the_test_that_executed_the_unit_when_contexts_exist(tmp_path):
    run = _run(tmp_path, contexts=True, killer="test_other")
    u = next(x for x in account_package(run, "pkg")["units"] if x["symbol"] == "pkg.core.f")
    assert u["state"] == "stated-gap" and u["reason"] == "executed-not-checked", "test_other killed the mutant but never ran f's lines"


def test_without_contexts_any_kept_killer_counts_and_the_record_says_so(tmp_path):
    run = _run(tmp_path, contexts=False, killer="test_other")
    rec = account_package(run, "pkg")
    u = next(x for x in rec["units"] if x["symbol"] == "pkg.core.f")
    assert u["state"] == "validated" and u["evidence"]["attribution"].startswith("aggregate")
    assert "no per-test contexts" in rec["method"]["strength"]


def test_stratified_sampling_gives_every_reached_unit_a_mutant_first():
    sites = [{"file": "a.py", "line": i, "col": 0, "op": "x"} for i in range(1, 101)]
    unit_sites = {"u1": sites[0:3], "u2": sites[10:12], "u3": []}
    chosen, strat = stratified_sample(sites, unit_sites, 6, random.Random(1))
    assert strat == {"units": 3, "units_with_sites": 2, "sampled_in_units": 5}
    assert len(chosen) == 6 and len({(s["file"], s["line"]) for s in chosen}) == 6
    assert any(s["line"] in (1, 2, 3) for s in chosen[:2]) and any(s["line"] in (11, 12) for s in chosen[:2]), "one per unit before a second from any"
    chosen, strat = stratified_sample(sites, unit_sites, 1, random.Random(1))
    assert len(chosen) == 1 and strat["sampled_in_units"] == 1


@needs_go
def test_go_internals_name_unexported_helpers_and_their_callers(tmp_path):
    from harness.adapters import go
    mod = tmp_path / "mod"; mod.mkdir()
    (mod / "go.mod").write_text("module example.com/m\n\ngo 1.22\n")
    (mod / "lib.go").write_text('''package m

// Public does the thing.
func Public(x int) int { return helper(x) + 1 }

func helper(x int) int { return deeper(x) * 2 }

func deeper(x int) int { return x }

type T struct{}

// Run runs.
func (t *T) Run() int { return t.step() }

func (t *T) step() int { return 1 }
''')
    doc = go.internals(mod, ["example.com/m"])
    private = {p["qualname"]: p for p in doc["private"]}
    assert set(private) == {"example.com/m.helper", "example.com/m.deeper", "example.com/m.T.step"}
    assert private["example.com/m.helper"]["kind"] == "private-function" and private["example.com/m.helper"]["end_line"] >= private["example.com/m.helper"]["line"]
    assert doc["calls"]["example.com/m.Public"] == ["example.com/m.helper"]
    assert doc["calls"]["example.com/m.helper"] == ["example.com/m.deeper"]
    assert doc["calls"]["example.com/m.T.Run"] == ["example.com/m.T.step"]
    api = go.extract_api(mod, ["example.com/m"])
    pub = next(s for s in api if s.qualname == "example.com/m.Public")
    assert pub.end_line and pub.end_line >= pub.line
