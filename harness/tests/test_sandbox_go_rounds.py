"""GF-022: the Go build retry drops blamed files round after round and reports every test it dropped."""
from pathlib import Path

from harness import sandbox_go


def test_build_retry_loops_until_the_package_builds(tmp_path, monkeypatch):
    tests = tmp_path / "tests"; tests.mkdir()
    for n in "abc":
        (tests / f"{n}_test.go").write_text(f"package harnesstest\n\nimport \"testing\"\n\nfunc Test{n.upper()}(t *testing.T) {{}}\n")
    out = tmp_path / "out"; out.mkdir()
    rounds = []

    def fake_run_once(*, env_dir, tests_dir, out_dir, cover, label, image, limits, overlay_dir, include=None):
        rounds.append(include)
        blame = {1: "a_test.go", 2: "b_test.go"}.get(len(rounds))
        if blame:
            (out_dir / "stdout.log").write_text(f"# harnesstest [harnesstest.test]\n./{blame}:5:1: undefined: x\nFAIL\tharnesstest [build failed]\n")
            (out_dir / "test.json").write_text("")
            return {"build_failed": True, "install_failed": False, "junit": None, "coverage": None, "files_not_compiled": {}}
        (out_dir / "stdout.log").write_text("ok\n")
        (out_dir / "test.json").write_text('{"Test":"TestC","Action":"pass","Elapsed":0.01}\n')
        return {"build_failed": False, "install_failed": False, "junit": str(out_dir / "junit.xml"), "coverage": None, "files_not_compiled": {}}

    monkeypatch.setattr(sandbox_go, "_run_once", fake_run_once)
    summary = sandbox_go.run_tests(env_dir=tmp_path, tests_dir=tests, out_dir=out, cover=[], label="t")
    assert rounds == [None, ["b_test.go", "c_test.go"], ["c_test.go"]]
    assert summary["build_failed"] is False and summary["build_rounds"] == 3
    assert set(summary["files_not_compiled"]) == {"a_test.go", "b_test.go"}
    junit = (out / "junit.xml").read_text()
    assert 'name="TestA"' in junit and 'name="TestB"' in junit and "did not compile" in junit
    assert (out / "stdout-1.log").exists() and (out / "stdout-2.log").exists()


def test_build_retry_reports_everything_when_nothing_builds(tmp_path, monkeypatch):
    tests = tmp_path / "tests"; tests.mkdir()
    (tests / "a_test.go").write_text("package harnesstest\n\nimport \"testing\"\n\nfunc TestA(t *testing.T) {}\n")
    out = tmp_path / "out"; out.mkdir()

    def fake_run_once(*, out_dir, **kw):
        (out_dir / "stdout.log").write_text("./a_test.go:5:1: undefined: x\nFAIL\tharnesstest [build failed]\n")
        (out_dir / "test.json").write_text("")
        return {"build_failed": True, "install_failed": False, "junit": None, "coverage": None, "files_not_compiled": {}}

    monkeypatch.setattr(sandbox_go, "_run_once", fake_run_once)
    summary = sandbox_go.run_tests(env_dir=tmp_path, tests_dir=tests, out_dir=out, cover=[], label="t")
    assert summary["build_failed"] is True and list(summary["files_not_compiled"]) == ["a_test.go"]
    assert 'name="TestA"' in (out / "junit.xml").read_text()
