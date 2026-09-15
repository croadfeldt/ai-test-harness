"""A first-party target in the Python sandbox: the application's own tree goes on the import path, its
dependencies come from the wheelhouse, coverage is measured on its files, and a mutant is laid over
the tree, not over site-packages. Needs podman; the wheelhouse download needs the network once."""
import json
import shutil
from pathlib import Path

import pytest

from harness.adapters import python as py

pytestmark = pytest.mark.skipif(shutil.which("podman") is None, reason="podman not installed")

APP = {"app/__init__.py": "", "app/calc.py": "import six\n\n\ndef add(a, b):\n    if a > 100:\n        return 100 + b\n    return a + b\n\n\ndef label(x):\n    return six.text_type(x)\n"}
TEST = "from app.calc import add, label\n\n\ndef test_add():\n    \"\"\"add sums two small numbers.\"\"\"\n    assert add(2, 3) == 5\n\n\ndef test_label():\n    \"\"\"label returns text.\"\"\"\n    assert label(7) == '7'\n"


def test_first_party_tree_runs_with_coverage_and_a_mutant(tmp_path: Path):
    tree = tmp_path / "src-tree"
    for rel, body in APP.items():
        (tree / rel).parent.mkdir(parents=True, exist_ok=True); (tree / rel).write_text(body)
    assert py.first_party_packages(tree) == ["app"]
    env = py.prefetch(["six==1.17.0"], "3.12", tmp_path / "wh", source=tree)
    tests = tmp_path / "tests"; tests.mkdir(); (tests / "test_calc.py").write_text(TEST)
    s = py.run_tests(env, tests, tmp_path / "out", cover=["app"], label="fp")
    r = {k.split("::")[-1]: v["status"] for k, v in py.parse_results(s).items()}
    assert r == {"test_add": "pass", "test_label": "pass"}
    cov = py.coverage_for(s, ["app"])
    assert cov["available"] and "app/calc.py" in cov["files"] and cov["covered_lines_in_target"] >= 4
    executed = py.coverage_files(Path(s["coverage"]), ["app"])
    assert "app/calc.py" in executed and 5 in executed["app/calc.py"] and 7 in executed["app/calc.py"]
    sites = py.mutation_sites(tree / "app" / "calc.py", executed["app/calc.py"])
    # `return a + b` becomes `return None`: a mutant test_add must kill, which proves the mutant reached the copied tree.
    site = next(x for x in sites if x["op"] == "return-none" and x["line"] == 7)
    code = py.apply_mutation(tree / "app" / "calc.py", site)
    assert "return None" in code
    mdir = tmp_path / "m001"; py.write_overlay(mdir, "app/calc.py", code, {"package": "src-tree", "new_version": "x"})
    s2 = py.run_tests(env, tests, mdir / "out", cover=[], label="fp-m001", overlay_dir=mdir)
    r2 = {k.split("::")[-1]: v["status"] for k, v in py.parse_results(s2).items()}
    assert r2 == {"test_add": "fail", "test_label": "pass"}, ((mdir / "out" / "stdout.log").read_text()[-500:], r2)
