"""Intake starts from a clean work directory: a previous run's outputs go, the cache stays."""
from harness.stages.intake import start_fresh


def test_start_fresh_removes_previous_outputs_and_keeps_the_cache(tmp_path):
    for d in ("intake", "execute/pkg/mutation/mutants/m001", "cache/gomod/new"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "README.md").write_text("old story"); (tmp_path / "run-index.json").write_text("{}")
    (tmp_path / "cache" / "gomod" / "new" / "keep").write_text("x")
    removed = start_fresh(tmp_path)
    assert set(removed) == {"intake", "execute", "README.md", "run-index.json"}
    assert not (tmp_path / "execute").exists() and (tmp_path / "cache" / "gomod" / "new" / "keep").exists()
