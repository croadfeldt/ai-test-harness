"""Declared needs (blueprint stage 4, R24): a test says what it needs, the sandbox honours and enforces it, a need
the testbed cannot provide is a skip with its reason, an undeclared connection is a defect in the test."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from harness import needs
from harness.adapters import python as py
from harness.stages import generate
from harness.stages.execute import undeclared, verdict

needs_go = pytest.mark.skipif(shutil.which("go") is None, reason="go toolchain not installed")

PY_TESTS = '''
import pytest
import pkg

def test_plain():
    assert pkg.f(1) == 2

@pytest.mark.needs("localhost")
def test_local():
    assert pkg.f(2) == 3

@pytest.mark.needs("network")
def test_remote():
    assert pkg.f(3) == 4
'''


def test_python_marker_is_read_and_unmarked_tests_mean_none():
    assert py.declared_needs(PY_TESTS) == {"test_local": "localhost", "test_remote": "network"}
    assert py.declared_needs("def test_x(): pass\n") == {}
    assert py.declared_needs("def test_x(:\n") == {}


def test_withheld_and_allowed_follow_the_ladder():
    assert needs.withheld({"a": "network", "b": "none", "c": "localhost", "d": "machine"}, {"none", "localhost"}) == {"a": "network", "d": "machine"}
    assert needs.withheld({"a": "network"}, {"none", "localhost", "network"}) == {}
    assert needs.withheld({"a": "bogus"}, {"none"}) == {}, "an unknown word is none"
    assert not needs.allowed("none", "example.org") and not needs.allowed("none", "127.0.0.1")
    assert needs.allowed("localhost", "127.0.0.1") and needs.allowed("localhost", "::1") and not needs.allowed("localhost", "example.org")
    assert needs.allowed("network", "example.org") and needs.allowed("machine", "example.org")


def test_provides_is_the_teams_setting(monkeypatch):
    monkeypatch.setenv("HARNESS_PROVIDES", "network, none")
    assert needs.provided() == {"none", "network"}
    monkeypatch.setenv("HARNESS_PROVIDES", "localhost")
    assert needs.provided() == {"none", "localhost"}, "none is always provided"


def test_the_conftest_enforces_none_allows_loopback_for_localhost_and_leaves_network_alone(tmp_path):
    """Three tests connect to a listening loopback socket: declared none fails with HarnessUndeclaredNeed,
    declared localhost passes, declared network passes. Run under a real pytest, the way the sandbox does."""
    (tmp_path / "conftest.py").write_text(needs.CONFTEST)
    (tmp_path / "test_needs.py").write_text('''
import socket
import pytest

def _connect():
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
    c = socket.socket()
    try:
        c.connect(srv.getsockname())
    finally:
        c.close(); srv.close()

def test_none_connects():
    _connect()

@pytest.mark.needs("localhost")
def test_localhost_connects():
    _connect()

@pytest.mark.needs("network")
def test_network_connects():
    _connect()
''')
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(tmp_path / "junit.xml"), str(tmp_path)],
                          capture_output=True, text=True, timeout=300, cwd=tmp_path)
    junit = (tmp_path / "junit.xml").read_text()
    assert "HarnessUndeclaredNeed" in proc.stdout and "undeclared need" in proc.stdout, proc.stdout[-1500:]
    assert junit.count("<failure") == 1 and 'name="test_none_connects"' in junit, junit
    assert "PytestUnknownMarkWarning" not in proc.stdout, "the conftest registers the marker"


def test_verdict_names_an_undeclared_connection_and_a_withheld_need():
    roles = {"direction": "upgrade", "vulnerable": "1.0", "fixed": "1.1"}
    t = {"status": "fail", "category": "unit", "needs": "none", "versions": {"old": "na", "new": "fail"},
         "message": "HarnessUndeclaredNeed: undeclared need: the test opened a connection to 'example.org' but declared 'none'"}
    assert undeclared(t) and verdict(t, "", roles, None).startswith("undeclared need")
    go = {"status": "fail", "category": "unit", "needs": "none", "versions": {"old": "na", "new": "fail"}, "message": "Get \"https://x\": dial tcp: lookup x: no such host"}
    assert undeclared(go), "Go tests meet the sealed network and are read from the error"
    declared = {**go, "needs": "network"}
    assert not undeclared(declared), "a declared need is not an undeclared one"
    held = {"status": "skipped", "category": "unit", "needs": "network", "versions": {"old": "na", "new": "na"}, "message": ""}
    assert verdict(held, "", roles, None).startswith("needs network: not provided in this testbed")


def test_generation_withholds_declared_tests_from_the_baseline_but_keeps_them_in_the_file(monkeypatch):
    seen = {}

    def fake_run(code, pkg_dir, env, roots, label, adapter=None):
        seen["code"] = code
        return {"results": {"t::test_plain": {"status": "pass"}}, "sandbox": {"install_failed": False, "build_failed": False}, "coverage": {}, "stdout_tail": ""}
    monkeypatch.setattr(generate, "_run_baseline_code", fake_run)
    monkeypatch.setenv("HARNESS_PROVIDES", "none,localhost")
    run = generate._run_baseline(PY_TESTS, Path("."), {}, ["pkg"], "lbl", py)
    assert "test_remote" not in seen["code"] and "test_local" in seen["code"] and "test_plain" in seen["code"]
    assert run["withheld"] == {"test_remote": "network"}
    only = '''import pytest\n@pytest.mark.needs("network")\ndef test_remote():\n    assert True\n'''
    run = generate._run_baseline(only, Path("."), {}, ["pkg"], "lbl", py)
    assert run.get("all_withheld") and run["results"] == {}, "a file whose every test is withheld is not run, and not discarded for it"


def test_prompt_carries_the_rule():
    assert "DECLARED NEEDS" in needs.PROMPT_RULE.upper() or "needs" in needs.PROMPT_RULE
    assert "pytest.mark.needs" in needs.SYNTAX["python"] and "harness:needs" in needs.SYNTAX["go"]


@needs_go
def test_go_directive_is_read_by_the_helper():
    from harness.adapters import go
    code = '''package harnesstest

import "testing"

// harness:needs network
func TestRemote(t *testing.T) { t.Log("x") }

// TestLocal is plain.
func TestLocal(t *testing.T) { t.Log("y") }
'''
    assert go.declared_needs(code) == {"TestRemote": "network"}


def test_accounting_puts_a_withheld_tests_behaviour_for_your_environment(tmp_path):
    """A behaviour whose only test declares a need the testbed lacks is accounted 'for your environment', with the
    declaration as evidence, not as a gap."""
    from harness.stages.account import account_package
    from test_accounting_strength import _run
    run = _run(tmp_path, contexts=True, killer="test_f_adds_one")
    a = run / "analyze" / "pkg"
    api = json.loads((a / "api.new.json").read_text())
    api["symbols"].append({"module": "pkg.core", "qualname": "pkg.core.g2", "kind": "function", "signature": "(x)", "doc": "", "file": "pkg/core.py", "line": 40, "end_line": 41})
    (a / "api.new.json").write_text(json.dumps(api))
    (a / "call-sites.json").write_text(json.dumps({"sites": [{"symbol": "pkg.f", "file": "app.py", "line": 1, "in_test": False},
                                                             {"symbol": "pkg.g2", "file": "app.py", "line": 2, "in_test": False}]}))
    res = json.loads((run / "execute" / "pkg" / "results.json").read_text())
    res["tests"].append({"id": "t::test_g2_remote", "name": "test_g2_remote", "status": "skipped", "needs": "network", "versions": {"old": "na", "new": "na"},
                         "verdict": needs.skip_verdict("network"), "category": "functional", "symbols_exercised": ["pkg.core.g2"], "message": ""})
    (run / "execute" / "pkg" / "results.json").write_text(json.dumps(res))
    rec = account_package(run, "pkg")
    u = next(x for x in rec["units"] if x["symbol"] == "pkg.core.g2")
    assert u["state"] == "for-your-environment" and u["evidence"]["declared"] == ["network"] and u["evidence"]["withheld"] == ["test_g2_remote"]
    assert rec["counts"]["for_your_environment"] == 1
