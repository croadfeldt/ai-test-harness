"""A --select run must not hide other packages from later stages."""
from pathlib import Path

from harness.util import merge_summary, read_json


def test_selective_runs_accumulate(tmp_path: Path):
    p = tmp_path / "summary.json"
    merge_summary(p, [{"package": "a", "n": 1}, {"package": "b", "n": 1}])
    merge_summary(p, [{"package": "b", "n": 2}])
    rows = {r["package"]: r["n"] for r in read_json(p)["packages"]}
    assert rows == {"a": 1, "b": 2}
    merge_summary(p, [{"package": "c", "n": 3}], extra={"mode": "agent"})
    d = read_json(p)
    assert sorted(r["package"] for r in d["packages"]) == ["a", "b", "c"] and d["mode"] == "agent"
