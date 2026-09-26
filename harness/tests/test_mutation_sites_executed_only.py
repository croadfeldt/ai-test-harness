"""GF-028: no executed line, no mutation site; an empty restriction never means every line."""
from harness.adapters import go, python


def test_no_executed_lines_means_no_sites(tmp_path):
    f = tmp_path / "x.go"; f.write_text("package x\n\nfunc F(a int) bool { return a > 1 && a < 5 }\n")
    assert go.mutation_sites(f, set()) == []
    assert go.mutation_sites(f, {3}), "with the executed line named, the helper finds sites on it"
    p = tmp_path / "y.py"; p.write_text("def f(a):\n    return a > 1 and a < 5\n")
    assert python.mutation_sites(p, set()) == []
