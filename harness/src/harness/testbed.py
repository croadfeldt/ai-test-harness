"""Testbed failure: when the environment, not the test and not the package, decided the outcome (blueprint stage 4).

Every mature runner keeps this apart from a test failure: autopkgtest exits 16 for "testbed failure" and
reports `SKIP` when "a required resource was not available"; Bazel has `REMOTE_FAILURE` and exit codes 32
and 36 for environment failures; Testing Farm keeps a request-level `error` apart from "tests failed".
The harness does the same at two levels:

- **Run level.** The sandbox itself failed: the environment did not install, the run timed out, the
  container exited with no result, or the module did not build for a reason no test file is blamed for.
  `results.json` carries `testbed_failure` with the reason, every test in that run is `not-run`, the story
  opens with it, triage raises a `testbed-failure` finding routed to the harness's operators, and the
  accounting puts every reached behaviour in a stated gap with reason `testbed-failure`. Nothing below a
  run-level failure is a verdict about the tests.
- **Test level.** One test's failure reads as the environment refusing something: a permission the
  container denies, a read-only file system, a missing device, exhausted memory; or, for a test that
  declared `network` or `machine` and ran because the testbed said it provided it, a network error. Its
  verdict is `testbed failure`, its triage class `testbed-failure`, and it is neither a defect nor a test
  bug. An undeclared connection is not a testbed failure; it is a defect in the test (`needs.py`).

Export: the harness writes a CTRF report beside `results.json`. CTRF has no status for this, so a testbed
failure is `other` with `extra.harness.class = "testbed-failure"`; in JUnit terms it is `<error
type="testbed-failure">`, never `<failure>`. Consumers that read only the status see "not pass, not fail".
"""
from __future__ import annotations

import re
from pathlib import Path

from .util import now_iso, write_json

# The environment refusing a test: not an assertion, not a wrong argument, not the package's behaviour.
ENVIRONMENT = re.compile(r"PermissionError|permission denied|operation not permitted|read-only file system|no such device|"
                         r"no space left on device|cannot allocate memory|MemoryError|out of memory|Killed\b|"
                         r"address family not supported|too many open files", re.I)
NETWORK = re.compile(r"dial tcp|connection refused|no such host|network is unreachable|name resolution|Name or service not known|"
                     r"ConnectionRefusedError|gaierror|HarnessUndeclaredNeed|undeclared need", re.I)
VERDICT = "testbed failure"
REASON = "testbed-failure"


def refused(t: dict, provides: set[str] | None = None) -> str | None:
    """Why this test's outcome is the testbed's doing, or None. A test that declared `none` or `localhost`
    and met the network is NOT refused: that is an undeclared need, the test's own defect."""
    from .needs import normalize
    if t.get("status") not in ("fail", "error") and t.get("versions", {}).get("new") not in ("fail", "error"):
        return None
    msg = t.get("message") or ""
    need = normalize(t.get("needs"))
    if need in ("network", "machine") and (provides is None or need in provides) and NETWORK.search(msg) and not re.search(r"undeclared need|HarnessUndeclaredNeed", msg, re.I):
        return f"declared need {need} refused: {msg.splitlines()[0][:160]}"
    if ENVIRONMENT.search(msg) and not NETWORK.search(msg):
        return f"the environment refused the test: {msg.splitlines()[0][:160]}"
    return None


def run_failure(sandbox: dict, results: dict) -> dict | None:
    """Why a whole sandbox run is not a verdict, or None. Build failures a test file is blamed for are the
    tests' doing and are reported per test; everything else here is the testbed's."""
    if sandbox.get("install_failed"):
        return {"kind": "install-failed", "detail": "the environment did not install from the prefetched dependencies"}
    if sandbox.get("timed_out"):
        return {"kind": "timed-out", "detail": f"the sandbox run exceeded its limit ({(sandbox.get('isolation') or {}).get('limits', {}).get('timeout_s', '?')} s)"}
    if sandbox.get("build_failed") and not results and not sandbox.get("files_not_compiled"):
        return {"kind": "build-failed", "detail": "the module did not build and no test file is blamed; a toolchain or module problem"}
    if sandbox.get("returncode") not in (0, 1, 5, None) and not results:
        return {"kind": "no-result", "detail": f"the sandbox exited {sandbox.get('returncode')} with no test result"}
    return None


def ctrf(results: dict, out: Path) -> dict:
    """The run's results as a CTRF report (https://ctrf.io): the interchange shape, with the harness's
    verdict and declared need in `extra`. Status mapping: pass -> passed; fail, error -> failed; skip and a
    withheld declared need -> skipped; flaky and testbed failure -> other, named in extra.harness.class."""
    tests = []
    for t in results.get("tests", []):
        v = t.get("verdict") or ""
        if v.startswith(VERDICT):
            status, cls = "other", REASON
        elif t.get("status") == "flaky":
            status, cls = "other", "flaky"
        elif t.get("status") in ("skip", "skipped"):
            status, cls = "skipped", "for-your-environment" if t.get("needs") not in (None, "none") and t.get("status") == "skipped" else "skipped"
        elif t.get("status") == "pass":
            status, cls = "passed", "pass"
        else:
            status, cls = "failed", "undeclared-need" if v.startswith("undeclared need") else "fail"
        tests.append({"name": t.get("id") or t.get("name"), "status": status, "duration": t.get("duration_ms", 0),
                      "message": (t.get("message") or "")[:500] or None, "suite": t.get("file"),
                      "flaky": t.get("status") == "flaky", "retries": max(0, (t.get("runs_on_head") or (1 if t.get("versions", {}).get("new") not in (None, "na") else 0)) - 1),
                      "extra": {"harness": {"class": cls, "verdict": v, "needs": t.get("needs", "none"), "versions": t.get("versions")}}})
    summary = {"tests": len(tests), "passed": sum(1 for x in tests if x["status"] == "passed"), "failed": sum(1 for x in tests if x["status"] == "failed"),
               "skipped": sum(1 for x in tests if x["status"] == "skipped"), "pending": 0, "other": sum(1 for x in tests if x["status"] == "other"),
               "start": 0, "stop": 0}
    rep = {"results": {"tool": {"name": "ai-test-harness", "version": results.get("harness_version")}, "summary": summary, "tests": tests,
                       "environment": {"testEnvironment": (results.get("target") or {}).get("class"), "healthy": results.get("testbed_failure") is None,
                                       "extra": {"testbed_failure": results.get("testbed_failure"), "testbed": results.get("testbed"), "generated": now_iso()}}}}
    write_json(out, rep)
    return rep
