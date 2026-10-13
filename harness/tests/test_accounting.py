"""Principle 14: every behaviour the change reaches ends in exactly one state, and nothing is silent.

The two example runs are real harness output. The Python one is the dry run docs/18 describes: three
functions reached, all executed, none with a mutant sampled inside them, so three stated gaps that name
the sampling as the reason. That the accounting says so, rather than counting the run as validated, is
the point of the test."""
import shutil
from pathlib import Path

import pytest

from harness.stages.account import REASONS, STATES, account, account_package, plain, resolve

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "examples" / "frc-scheduler-server" / "pr-fix-known-vulns-235b"
GO = ROOT / "examples" / "control-plane" / "kin-openapi-bench-v1"


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "accounting"
API = {PY.name: ("python-jose", "python-jose.api.new.json"), GO.name: ("github.com/getkin/kin-openapi", "kin-openapi.api.new.json")}


def _copy(src: Path, tmp: Path) -> Path:
    """The example run, plus its API surface: every run writes api.new.json, but examples/ ignores it for
    size, so a trimmed copy of the two the tests need lives in fixtures/."""
    dst = tmp / src.name
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("model-calls", "scratch", "mutants"))
    pkg, fixture = API[src.name]
    api = dst / "analyze" / pkg / "api.new.json"
    if not api.exists():
        shutil.copy(FIXTURES / fixture, api)
    return dst


def test_every_reached_behaviour_has_exactly_one_state(tmp_path):
    run = _copy(PY, tmp_path)
    rec = account_package(run, "python-jose")
    assert rec["format"] == "ai-test-harness/accounting/v1"
    for u in rec["units"]:
        assert u["state"] in STATES
        assert (u["reason"] in REASONS) if u["state"] == "stated-gap" else u["reason"] is None
    c = rec["counts"]
    assert c["units"] == c["validated"] + c["for_your_environment"] + c["stated_gap"]
    assert sum(c["by_reason"].values()) == c["stated_gap"]


def test_the_python_dry_run_reads_as_docs_18_says(tmp_path):
    run = _copy(PY, tmp_path)
    rec = account_package(run, "python-jose")
    by = {u["symbol"]: u for u in rec["units"]}
    assert set(by) == {"jose.jwt.encode", "jose.jwt.decode", "jose.jwt.get_unverified_header"}
    for u in by.values():
        assert u["state"] == "stated-gap" and u["reason"] == "strength-not-sampled"
        assert u["evidence"]["lines_executed"] > 0 and u["evidence"]["mutants"]["sampled"] == 0
    excluded = {e["symbol"]: e["reason"] for e in rec["excluded"]}
    assert "jose.jwt" in excluded and "module import" in excluded["jose.jwt"]
    assert "jose.exceptions.JWTError" in excluded, "the re-export resolved to its definition, then set aside as a type without methods"
    assert (run / "triage" / "python-jose" / "accounting.json").exists()


def test_go_package_imports_are_not_behaviours_and_a_type_is_judged_by_its_methods(tmp_path):
    run = _copy(GO, tmp_path)
    rec = account_package(run, "github.com/getkin/kin-openapi")
    by = {u["symbol"]: u for u in rec["units"]}
    assert "github.com/getkin/kin-openapi/openapi3" not in by, "a package import is a module, not a behaviour"
    assert any("module import" in e["reason"] for e in rec["excluded"])
    t = by["github.com/getkin/kin-openapi/openapi3.T"]
    assert t["kind"] == "struct" and t["evidence"]["judged_by"] == "its public methods" and t["evidence"]["methods"]
    assert all(u["reason"] != "not-in-public-api" for u in rec["units"]), rec["counts"]["by_reason"]


def test_roll_up_sums_and_story_and_pull_request_carry_it(tmp_path):
    run = _copy(PY, tmp_path)
    summ = account(run, ["python-jose"])
    assert (run / "triage" / "accounting-summary.json").exists()
    assert summ["counts"]["units"] == 3 and summ["counts"]["stated_gap"] == 3
    assert plain(summ["counts"]) == "3 behaviours reached: 0 validated, 0 for your environment, 3 stated gaps."
    from harness import runindex, story
    idx = runindex.build(run)
    p = next(x for x in idx["packages"] if x["package"] == "python-jose")
    assert p["accounting"] == {"units": 3, "validated": 0, "for_your_environment": 0, "stated_gap": 3}
    assert "triage/accounting.json" in p["files"]
    assert any(c["path"] == "triage/accounting-summary.json" for c in idx["catalogue"])
    md = story.to_markdown(story.build(run, idx))
    assert "## What was accounted for, and what was not" in md and "3 behaviours reached" in md and "`jose.jwt.decode`" in md
    from harness.stages.packet import pull_request
    _, body = pull_request(run, "python-jose")
    assert "| Accounted for | 3 behaviours reached" in body and "Not covered:" in body and "`jose.jwt.encode`: " in body


def test_resolve_prefers_exact_then_unique_last_name():
    api = {"p.mod.f": {"kind": "function"}, "p.other.g": {"kind": "function"}, "p.a.h": {"kind": "function"}, "p.b.h": {"kind": "function"}, "p": {"kind": "module"}}
    assert resolve("p.mod.f", api) == "p.mod.f"
    assert resolve("p.g", api) == "p.other.g", "a re-export resolves to its one definition"
    assert resolve("p.h", api) is None, "two definitions with the same last name do not resolve by guess"
    assert resolve("p", api) is None


@pytest.mark.parametrize("state", STATES)
def test_states_are_the_three_the_case_promises(state):
    assert state in ("validated", "for-your-environment", "stated-gap")
