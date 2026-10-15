"""The behaviour worklist (blueprint stage 2, R27): per public function, every result a test should check, from the
parser; parameter edges inferred from the type and labelled so; advisories as results that must never happen."""
import json
import shutil
from pathlib import Path

import pytest

from harness.adapters import python as py
from harness.stages.generate import behaviour_lines

needs_go = pytest.mark.skipif(shutil.which("go") is None, reason="go toolchain not installed")

SRC = '''
from typing import Optional

class JWTError(Exception):
    pass

def decode(token: str, key, algorithms: Optional[list] = None, verify: bool = True) -> dict:
    """decode a token"""
    if not token or (verify and key is None):
        raise JWTError("bad")
    if token.count(".") != 2:
        raise ValueError("segments")
    return {"ok": True}

def helper(x: int):
    if x > 3:
        return x

def _private(y):
    return y

class Loader:
    def load(self, path: str, strict: bool = False):
        try:
            return open(path).read()
        except OSError:
            raise
'''


def _pkg(tmp: Path) -> Path:
    p = tmp / "pkg"; p.mkdir(parents=True)
    (p / "__init__.py").write_text("from .core import decode\n")
    (p / "core.py").write_text(SRC)
    return tmp


def test_python_worklist_names_returns_raises_params_and_decisions(tmp_path):
    b = py.behaviours(_pkg(tmp_path), ["pkg"])
    assert set(b) == {"pkg.core.decode", "pkg.core.helper", "pkg.core.Loader.load"}, "public functions and methods only"
    d = b["pkg.core.decode"]
    kinds = {x["kind"] for x in d}
    assert kinds == {"param", "raise", "return", "decision"}
    assert {x.get("detail") for x in d if x["kind"] == "raise"} == {"raises JWTError", "raises ValueError"}
    assert any(x.get("detail") == "returns {'ok': True}" for x in d)
    dec = next(x for x in d if x["kind"] == "decision")
    assert dec["conditions"] == 2 and "verify and key is None" in dec["detail"]
    params = {x["name"]: x for x in d if x["kind"] == "param"}
    assert params["token"]["type"] == "str" and "the empty string" in params["token"]["try"]
    assert params["key"]["type"] is None and "None" in params["key"]["try"] and "a value of the wrong type" in params["key"]["try"]
    assert params["algorithms"]["default"] == "None" and "None" in params["algorithms"]["try"] and "an empty list" in params["algorithms"]["try"]
    assert params["verify"]["try"] == ["True", "False"]


def test_fall_through_and_re_raise_are_behaviours_too(tmp_path):
    b = py.behaviours(_pkg(tmp_path), ["pkg"])
    helper = b["pkg.core.helper"]
    assert any(x.get("detail") == "returns x" for x in helper) and any("fall through" in (x.get("detail") or "") for x in helper), helper
    load = b["pkg.core.Loader.load"]
    assert any(x.get("detail") == "re-raises the current exception" for x in load)
    assert not any(x.get("name") == "self" for x in load), "self is not a parameter to try"


def test_prompt_lines_cover_the_used_functions_and_the_advisories(tmp_path):
    b = py.behaviours(_pkg(tmp_path), ["pkg"])
    doc = {"units": b, "must_never": [{"advisory": "CVE-2024-1", "detail": "algorithm confusion lets a public key verify as HMAC", "symbols": ["decode"]}]}
    lines = behaviour_lines(doc, ["pkg.decode", "pkg.core.helper", "pkg.nothing"])
    assert lines[0].startswith("pkg.core.decode: "), "a re-export resolves to its definition by its one last name"
    assert "raises JWTError" in lines[0] and "params token:str (try the empty string" in lines[0] and "decisions" in lines[0]
    assert lines[1].startswith("pkg.core.helper: ")
    assert lines[-1].startswith("MUST NEVER (CVE-2024-1)") and "[decode]" in lines[-1]
    assert behaviour_lines(None, ["x"]) == [] and behaviour_lines({"units": {}}, ["x"]) == []


def test_accounting_records_how_many_behaviours_each_unit_has(tmp_path):
    from harness.stages.account import account_package
    from test_accounting_strength import _run
    run = _run(tmp_path, contexts=True, killer="test_f_adds_one")
    (run / "analyze" / "pkg" / "behaviours.json").write_text(json.dumps({"units": {"pkg.core.f": [{"kind": "param"}, {"kind": "return"}, {"kind": "return"}]}, "must_never": []}))
    rec = account_package(run, "pkg")
    u = next(x for x in rec["units"] if x["symbol"] == "pkg.core.f")
    assert u["evidence"]["behaviours_identified"] == 3 and rec["counts"]["behaviours_identified"] == 3


@needs_go
def test_go_worklist_names_error_returns_panics_params_and_decisions(tmp_path):
    from harness.adapters import go
    mod = tmp_path / "mod"; mod.mkdir()
    (mod / "go.mod").write_text("module example.com/m\n\ngo 1.22\n")
    (mod / "lib.go").write_text('''package m

import "errors"

// Parse parses.
func Parse(s string, limit int, opts []string) (int, error) {
	if s == "" || limit < 0 {
		return 0, errors.New("bad input")
	}
	if limit > 100 {
		panic("too big")
	}
	return len(s), nil
}

type T struct{}

func (t *T) Run(ok bool) bool { return ok }
''')
    b = go.behaviours(mod, ["example.com/m"])
    assert set(b) == {"example.com/m.Parse", "example.com/m.T.Run"}
    p = b["example.com/m.Parse"]
    kinds = [x["kind"] for x in p]
    assert kinds.count("param") == 3 and "error" in kinds and "return" in kinds and "raise" in kinds and "decision" in kinds
    params = {x["name"]: x for x in p if x["kind"] == "param"}
    assert params["s"]["type"] == "string" and "the empty string" in params["s"]["try"]
    assert params["opts"]["type"] == "[]string" and "nil" in params["opts"]["try"]
    dec = next(x for x in p if x["kind"] == "decision")
    assert dec["conditions"] == 2
    assert any(x.get("detail") == "panics" for x in p)


def test_write_behaviours_treats_a_unit_with_nothing_to_check_as_an_empty_list(tmp_path):
    """An adapter may hand back None for a function with no results to check (Go's encoder writes an empty slice
    as null); the worklist records it as an empty list and counts it. The kin-openapi v2 run on 2026-10-15
    crashed here before this was pinned."""
    from harness.stages.analyze import write_behaviours

    class Adapter:
        @staticmethod
        def behaviours(source, names):
            return {"m.Noop": None, "m.Parse": [{"kind": "return", "detail": "returns 1"}]}
    doc = write_behaviours(tmp_path, "m", "1.0", Adapter(), tmp_path, ["m"], [])
    assert doc["units"]["m.Noop"] == [] and doc["counts"] == {"functions": 2, "behaviours": 1, "by_kind": {"param": 0, "return": 1, "error": 0, "raise": 0, "decision": 0}, "must_never": 0}


@needs_go
def test_go_function_with_nothing_to_check_is_an_empty_list(tmp_path):
    from harness.adapters import go
    mod = tmp_path / "mod"; mod.mkdir()
    (mod / "go.mod").write_text("module example.com/m\n\ngo 1.22\n")
    (mod / "lib.go").write_text("package m\n\n// Noop does nothing.\nfunc Noop() {}\n")
    b = go.behaviours(mod, ["example.com/m"])
    assert b == {"example.com/m.Noop": []}
