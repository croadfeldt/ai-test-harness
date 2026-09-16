"""run-index.json says what a run holds, read from the records, for a reader or a renderer."""
from pathlib import Path

import pytest

from harness import runindex

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "frc-scheduler-server" / "pr-fix-known-vulns-run6"
pytestmark = pytest.mark.skipif(not (EXAMPLE / "intake" / "worklist.json").exists(), reason="example run missing")


def test_index_names_stages_packages_and_files():
    idx = runindex.build(EXAMPLE)
    assert idx["format"] == "ai-test-harness/run-index/v1" and idx["run_id"] == "76a3fa863e76" and idx["repository"] == "frc-scheduler-server"
    assert idx["stages"]["execute"]["present"] and idx["stages"]["feedback"]["present"]
    assert idx["stages"]["intake"]["summary"]["packages_at_head"] == 63
    pk = {p["package"]: p for p in idx["packages"]}
    assert list(pk) == ["python-jose"], "rows carried over from another run must not appear"
    p = pk["python-jose"]
    assert p["tests"]["ran"] == 10 and p["tests"]["proven"] == 3 and p["tests"]["accepted"] == 7
    assert p["mutation"]["status"] == "ran" and p["attestation"]["result"] == "PASSED" and p["review"]["accepted"] == 7
    for key in ("execute/results.json", "packet/packet.md", "attest/statement.dsse.json", "feedback/acceptance.json"):
        assert key in p["files"] and (EXAMPLE / p["files"][key]).exists(), key


def test_index_is_written_by_update(tmp_path: Path):
    import shutil
    work = tmp_path / "run"; shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns("cache", "scratch", "model-calls"))
    out = runindex.update(work)
    assert out.name == "run-index.json" and out.exists()
