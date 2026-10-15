"""Mutation feedback (blueprint stage 3, R26): a passing candidate is probed with deliberate breakages on the lines its
tests executed; survivors go back to the model once, as a diff; the manifest records what was caught after."""
import json
from pathlib import Path

from harness.adapters import python as py
from harness.stages import generate

SRC = '''
def f(x):
    if x > 3:
        return x * 2
    return x + 1

def g(y):
    return y - 1
'''


def _src(tmp: Path) -> Path:
    p = tmp / "pkg"; p.mkdir(parents=True)
    (p / "__init__.py").write_text("from .core import f, g\n")
    (p / "core.py").write_text(SRC)
    return tmp


def test_budget_is_the_teams_setting_and_zero_disables(monkeypatch):
    monkeypatch.setenv("HARNESS_MUTATION_FEEDBACK", "5")
    assert generate.feedback_budget() == 5
    monkeypatch.setenv("HARNESS_MUTATION_FEEDBACK", "0")
    assert generate.feedback_budget() == 0
    monkeypatch.setenv("HARNESS_MUTATION_FEEDBACK", "x")
    assert generate.feedback_budget() == 3


def test_the_hint_shows_the_model_each_breakage_as_a_diff():
    surv = [{"file": "pkg/core.py", "line": 3, "op": "compare-swap", "excerpt": "-    if x > 3:\n+    if x < 3:"}]
    h = generate.mutation_hint(surv, "pkg")
    assert h.startswith("MUTATION FEEDBACK") and "pkg/core.py:3 (compare-swap)" in h and "+    if x < 3:" in h
    assert "FAILS on the broken code and PASSES on the real code" in h
    ex = generate._excerpt("a\nb\nc\nd\ne\n", "a\nb\nX\nd\ne\n", 3)
    assert "-c" in ex and "+X" in ex


def test_probe_sites_come_from_executed_lines_and_reached_closures_first(tmp_path):
    root = _src(tmp_path / "src")
    cov = {"files": {"/work/venv/lib/python3.12/site-packages/pkg/core.py": {"executed_lines": [2, 3, 4, 5, 7, 8]}}}
    (tmp_path / "coverage.json").write_text(json.dumps(cov))
    run = {"sandbox": {"coverage": str(tmp_path / "coverage.json")}}
    facts = {"package": "pkg", "new_version": "1.0"}
    all_sites = generate.probe_sites("code", run, py, facts, root, ["pkg"], 50, "seed")
    assert all_sites and all(s["file"] == "pkg/core.py" for s in all_sites)
    assert {s["line"] for s in all_sites} <= {2, 3, 4, 5, 7, 8}
    units = {"pkg.core.g": [("pkg.core.g", "pkg/core.py", 7, 8)]}
    chosen = generate.probe_sites("code", run, py, facts, root, ["pkg"], 1, "seed", units)
    assert len(chosen) == 1 and chosen[0]["line"] in (7, 8), "the reached behaviour's lines get the first probe"
    assert generate.probe_sites("code", {"sandbox": {}}, py, facts, root, ["pkg"], 3, "seed") == [], "no coverage, no probe"
    assert generate.probe_sites("code", run, py, facts, root, ["pkg"], 0, "seed") == [], "zero disables"


def test_probe_run_reports_survived_or_killed_with_the_diff(tmp_path, monkeypatch):
    root = _src(tmp_path / "src")
    facts = {"package": "pkg", "new_version": "1.0"}
    site = next(s for s in py.mutation_sites(root / "pkg" / "core.py", {3}) if s["op"] == "compare-swap")
    site = {"file": "pkg/core.py", **site}
    calls = {}

    def fake_run_tests(env, tests_dir, out_dir, cover, label, overlay_dir=None, limits=None, per_test=False):
        calls["overlay"] = overlay_dir
        assert (overlay_dir / "pkg" / "core.py").exists(), "the mutant is laid over the package"
        return {"label": label}
    monkeypatch.setattr(py, "run_tests", fake_run_tests)
    monkeypatch.setattr(py, "parse_results", lambda s: {"t::test_a": {"status": "pass"}, "t::test_b": {"status": "pass"}})
    out = generate.probe_run("def test_a(): pass\n", site, py, facts, root, {"dir": "x", "requirements": []}, tmp_path / "gen", "lbl")
    assert out["status"] == "survived" and out["killed_by"] == [] and "if x" in out["excerpt"]
    monkeypatch.setattr(py, "parse_results", lambda s: {"t::test_a": {"status": "fail"}, "t::test_b": {"status": "pass"}})
    out = generate.probe_run("def test_a(): pass\n", site, py, facts, root, {"dir": "x", "requirements": []}, tmp_path / "gen", "lbl2")
    assert out["status"] == "killed" and out["killed_by"] == ["test_a"]


def test_the_recorded_probe_site_is_enough_to_apply_the_mutation_again(tmp_path):
    """The re-probe after the feedback round reads the sites back from the manifest record; the record must carry
    everything the mutator needs, not a summary of it."""
    from harness.adapters import python as py
    from harness.stages.generate import site_record
    src = tmp_path / "m.py"; src.write_text("def f(x):\n    if x > 1:\n        return True\n    return False\n")
    sites = py.mutation_sites(src, {2, 3})
    assert sites, "the fixture has a comparison and a constant to mutate"
    rec = site_record(sites[0])
    assert set(sites[0]) <= set(rec), "nothing dropped"
    mutated = py.apply_mutation(src, rec)
    assert mutated and mutated != src.read_text()
    import json; json.dumps(rec)
