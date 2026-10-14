"""The flake check beyond two runs (blueprint stage 4, R9): the team sets how many times a candidate about to be
proposed runs on head, the agreed candidates run again, any disagreement quarantines, and the record says so."""
from harness import testbed
from harness.stages.execute import agreed_candidates, fold_repeats, head_runs


def test_head_runs_is_the_teams_setting_with_a_floor_of_two(monkeypatch):
    monkeypatch.setenv("HARNESS_REPEATS", "7")
    assert head_runs() == 7
    monkeypatch.setenv("HARNESS_REPEATS", "1")
    assert head_runs() == 2, "the run and its re-run are the floor"
    monkeypatch.setenv("HARNESS_REPEATS", "many")
    assert head_runs() == 5, "nonsense falls back to the default"
    monkeypatch.delenv("HARNESS_REPEATS")
    assert head_runs() == 5


def _runs(new, rerun, *repeats):
    runs = {"new": {"results": {k: {"status": v} for k, v in new.items()}}, "new-rerun": {"results": {k: {"status": v} for k, v in rerun.items()}}}
    for i, r in enumerate(repeats, 3):
        runs[f"new-repeat-{i}"] = {"results": {k: {"status": v} for k, v in r.items()}}
    return runs


def test_only_candidates_that_agreed_on_both_runs_are_repeated():
    runs = _runs({"t::a": "pass", "t::b": "pass", "t::c": "fail"}, {"t::a": "pass", "t::b": "fail", "t::c": "fail"})
    assert agreed_candidates(runs) == ["t::a"]


def test_any_disagreement_on_a_later_run_quarantines():
    runs = _runs({"t::a": "pass", "t::b": "pass"}, {"t::a": "pass", "t::b": "pass"}, {"t::a": "pass", "t::b": "fail"}, {"t::a": "pass", "t::b": "pass"}, {"t::a": "pass", "t::b": "pass"})
    assert fold_repeats("t::a", "pass", runs) == ("pass", 5, 0)
    assert fold_repeats("t::b", "pass", runs) == ("flaky", 5, 1)
    runs2 = _runs({"t::c": "fail"}, {"t::c": "fail"}, {"t::a": "pass"})
    assert fold_repeats("t::c", "fail", runs2) == ("fail", 2, 0), "a test not repeated keeps its two runs"


def test_ctrf_carries_retries_from_the_runs_on_head(tmp_path):
    results = {"tests": [{"id": "t::a", "status": "pass", "verdict": "candidate", "versions": {"old": "na", "new": "pass"}, "needs": "none", "runs_on_head": 5},
                         {"id": "t::b", "status": "flaky", "verdict": "flaky: discard", "versions": {"old": "na", "new": "pass"}, "needs": "none", "runs_on_head": 4, "disagreements": 1}]}
    rep = testbed.ctrf(results, tmp_path / "r.json")
    by = {t["name"]: t for t in rep["results"]["tests"]}
    assert by["t::a"]["retries"] == 4 and not by["t::a"]["flaky"]
    assert by["t::b"]["retries"] == 3 and by["t::b"]["flaky"] and by["t::b"]["status"] == "other"
