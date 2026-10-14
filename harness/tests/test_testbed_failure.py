"""Testbed failure (blueprint stage 4, R25): the environment's failure is its own status at the run level and per
test, never the test's or the package's verdict, and the CTRF export carries it as `other`."""
import json
from pathlib import Path

from harness import testbed
from harness.stages.execute import verdict

ROLES = {"direction": "upgrade", "vulnerable": "1.0", "fixed": "1.1"}


def _t(message, needs="none", status="fail"):
    return {"status": status, "category": "unit", "needs": needs, "versions": {"old": "na", "new": status}, "message": message}


def test_the_environment_refusing_a_test_is_the_testbeds_doing():
    assert testbed.refused(_t("PermissionError: [Errno 13] Permission denied: '/etc/x'")).startswith("the environment refused")
    assert testbed.refused(_t("OSError: [Errno 30] Read-only file system: '/usr/x'"))
    assert testbed.refused(_t("panic: runtime error: cannot allocate memory", status="error"))
    assert testbed.refused(_t("AssertionError: assert 1 == 2")) is None, "an assertion is the test's verdict"
    assert testbed.refused(_t("x", status="pass")) is None


def test_an_undeclared_connection_is_not_a_testbed_failure_but_a_refused_declared_need_is():
    net = "ConnectionRefusedError: [Errno 111] Connection refused"
    assert testbed.refused(_t(net, needs="none")) is None, "the test's own defect: undeclared need"
    assert testbed.refused(_t("HarnessUndeclaredNeed: undeclared need: ...", needs="none")) is None
    assert testbed.refused(_t(net, needs="network"), provides={"none", "localhost", "network"}).startswith("declared need network refused")
    assert testbed.refused(_t("dial tcp: lookup x: no such host", needs="machine"), provides={"none", "machine"})


def test_verdict_and_run_failure():
    v = verdict(_t("PermissionError: [Errno 13] Permission denied"), "", ROLES, None)
    assert v.startswith("testbed failure:") and "not a verdict about the test" in v
    assert verdict(_t("ConnectionRefusedError: Connection refused"), "", ROLES, None).startswith("undeclared need")
    assert testbed.run_failure({"install_failed": True}, {})["kind"] == "install-failed"
    assert testbed.run_failure({"timed_out": True, "isolation": {"limits": {"timeout_s": 900}}}, {})["kind"] == "timed-out"
    assert testbed.run_failure({"build_failed": True, "returncode": 1}, {})["kind"] == "build-failed"
    assert testbed.run_failure({"build_failed": True, "files_not_compiled": {"a_test.go": []}, "returncode": 1}, {}) is None, "a build failure blamed on a test file is the tests' doing"
    assert testbed.run_failure({"returncode": 137}, {})["kind"] == "no-result"
    assert testbed.run_failure({"returncode": 1}, {"t::a": {"status": "fail"}}) is None, "tests ran and one failed: a verdict, not a testbed failure"


def test_ctrf_export_maps_the_statuses_and_names_the_class(tmp_path):
    results = {"harness_version": "x", "target": {"class": "podman"}, "testbed_failure": None, "testbed": {"provides": ["none"]},
               "tests": [{"id": "t::a", "status": "pass", "verdict": "candidate", "versions": {"old": "pass", "new": "pass"}, "needs": "none", "duration_ms": 3},
                         {"id": "t::b", "status": "fail", "verdict": "fails on head", "versions": {"old": "na", "new": "fail"}, "needs": "none", "message": "AssertionError"},
                         {"id": "t::c", "status": "fail", "verdict": "testbed failure: the environment refused the test: PermissionError", "versions": {"old": "na", "new": "fail"}, "needs": "none"},
                         {"id": "t::d", "status": "flaky", "verdict": "flaky: discard", "versions": {"old": "na", "new": "pass"}, "needs": "none"},
                         {"id": "t::e", "status": "skipped", "verdict": "needs network: not provided", "versions": {"old": "na", "new": "na"}, "needs": "network"},
                         {"id": "t::f", "status": "fail", "verdict": "undeclared need: ...", "versions": {"old": "na", "new": "fail"}, "needs": "none"}]}
    rep = testbed.ctrf(results, tmp_path / "r.ctrf.json")
    by = {t["name"]: t for t in rep["results"]["tests"]}
    assert by["t::a"]["status"] == "passed" and by["t::b"]["status"] == "failed"
    assert by["t::c"]["status"] == "other" and by["t::c"]["extra"]["harness"]["class"] == "testbed-failure"
    assert by["t::d"]["status"] == "other" and by["t::d"]["extra"]["harness"]["class"] == "flaky" and by["t::d"]["flaky"]
    assert by["t::e"]["status"] == "skipped" and by["t::e"]["extra"]["harness"]["class"] == "for-your-environment"
    assert by["t::f"]["status"] == "failed" and by["t::f"]["extra"]["harness"]["class"] == "undeclared-need"
    s = rep["results"]["summary"]
    assert (s["tests"], s["passed"], s["failed"], s["skipped"], s["other"]) == (6, 1, 2, 1, 2)
    assert rep["results"]["environment"]["healthy"] is True and json.loads((tmp_path / "r.ctrf.json").read_text())["results"]["tool"]["name"] == "ai-test-harness"


def test_accounting_names_the_testbed_as_the_reason(tmp_path):
    from harness.stages.account import account_package
    from test_accounting_strength import _run
    run = _run(tmp_path, contexts=True, killer="test_f_adds_one")
    res_path = run / "execute" / "pkg" / "results.json"
    res = json.loads(res_path.read_text())
    res["testbed_failure"] = {"runs": {"new": {"kind": "timed-out", "detail": "the sandbox run exceeded its limit (900 s)"}}, "detail": "new: the sandbox run exceeded its limit (900 s)"}
    res_path.write_text(json.dumps(res))
    rec = account_package(run, "pkg")
    assert rec["counts"]["units"] >= 1 and all(u["state"] == "stated-gap" and u["reason"] == "testbed-failure" for u in rec["units"]), rec["units"]
    assert rec["counts"]["by_reason"] == {"testbed-failure": rec["counts"]["units"]}
    from harness import runindex, story
    md = story.to_markdown(story.build(run, runindex.build(run)))
    assert "**Testbed failure on pkg.**" in md and "Nothing in this run is a verdict" in md


def test_a_single_refused_test_is_a_gap_with_the_testbeds_name_not_the_tests(tmp_path):
    from harness.stages.account import account_package
    from test_accounting_strength import _run
    run = _run(tmp_path, contexts=True, killer="test_f_adds_one")
    a = run / "analyze" / "pkg"
    api = json.loads((a / "api.new.json").read_text())
    api["symbols"].append({"module": "pkg.core", "qualname": "pkg.core.g2", "kind": "function", "signature": "(x)", "doc": "", "file": "pkg/core.py", "line": 40, "end_line": 41})
    (a / "api.new.json").write_text(json.dumps(api))
    (a / "call-sites.json").write_text(json.dumps({"sites": [{"symbol": "pkg.g2", "file": "app.py", "line": 2, "in_test": False}]}))
    res_path = run / "execute" / "pkg" / "results.json"
    res = json.loads(res_path.read_text())
    res["tests"].append({"id": "t::test_g2_writes", "name": "test_g2_writes", "status": "fail", "needs": "none", "versions": {"old": "na", "new": "fail"},
                         "verdict": "testbed failure: the environment refused the test: PermissionError", "category": "unit", "symbols_exercised": ["pkg.core.g2"],
                         "message": "PermissionError: [Errno 13] Permission denied"})
    res_path.write_text(json.dumps(res))
    u = next(x for x in account_package(run, "pkg")["units"] if x["symbol"] == "pkg.core.g2")
    assert u["state"] == "stated-gap" and u["reason"] == "testbed-failure" and u["evidence"]["refused"] == ["test_g2_writes"]
