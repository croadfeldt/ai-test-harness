"""A mutant is kept as a patch and its run, never as a copy of the source file."""
from harness.stages.mutate import keep_as_patch


def test_mutant_kept_as_patch_and_the_copy_removed(tmp_path):
    mdir = tmp_path / "m001"; (mdir / "jose").mkdir(parents=True)
    (mdir / "jose" / "utils.py").write_text("x = 2\n")
    (mdir / "out").mkdir(); (mdir / "out" / "junit.xml").write_text("<testsuite/>")
    patch = keep_as_patch(mdir, "jose/utils.py", "x = 1\n", "x = 2\n")
    assert patch.read_text().splitlines()[2:] == ["@@ -1 +1 @@", "-x = 1", "+x = 2"]
    assert not (mdir / "jose").exists() and (mdir / "out" / "junit.xml").exists()
