"""Prompt sets are named and digested; the evaluator scores finished runs; the bench prepares one directory per set."""
from pathlib import Path

import pytest

from harness import prompts
from harness.stages import bench
from harness.stages.evaluate import aggregate, rows_for, verdict

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "examples" / "frc-scheduler-server" / "pr-fix-known-vulns-run6"


def test_v1_is_the_code_and_a_set_overrides_by_key():
    v1 = prompts.load("v1")
    assert v1.name == "v1" and v1.digest.startswith("sha256:") and set(v1.parts) >= {"system.python", "system.go", "task.cve.python", "agent.rules"}
    s = prompts.load("go-api-first")
    assert s.parts["system.python"] == v1.parts["system.python"] and s.parts["system.go"] != v1.parts["system.go"]
    assert s.digest != v1.digest and s.record()["overrides"] == ["system.go"]
    with pytest.raises(ValueError):
        prompts.PromptSet("bad", {"no.such.key": "x"}).parts


def test_evaluate_reads_a_finished_run_and_names_the_ground_truth():
    rows = rows_for(RUN)
    assert len(rows) == 1 and rows[0]["package"] == "python-jose" and rows[0]["proven"] == 3 and rows[0]["reviewer_accepted"] == 7
    agg = aggregate(rows + rows)
    assert agg[0]["runs"] == 2 and agg[0]["proven"] == 6 and verdict(agg[0]).startswith("accepted by a reviewer")
    assert verdict({"reviewer_accepted": 0, "proven": 0, "accepted": 0, "kept": 4, "generated": 8}) == "not fit: tests ran, none accepted"


def test_bench_prepares_one_directory_per_set(tmp_path):
    base = tmp_path / "run"
    for d in ("intake", "analyze/pkg", "cache/x"):
        (base / d).mkdir(parents=True)
    (base / "run.json").write_text("{}")
    dest = bench.prepare(base, "v1")
    assert dest == tmp_path / "run-bench-v1" and (dest / "analyze" / "pkg").is_dir() and (dest / "run.json").exists()
    assert (dest / "cache").is_symlink() and not (dest / "generate").exists()
