"""GF-027: an unused import is pruned rather than sent back to the model; the loop keeps the attempt that ran."""
import inspect

from harness.adapters.go import cut_at_errors, prune_imports
from harness.adapters.go import test_names as go_test_names
from harness.stages.generate import generate_package


def test_unused_import_is_pruned_not_reported():
    code = "package harnesstest\n\nimport (\n\t\"context\"\n\t\"testing\"\n)\n\nfunc TestA(t *testing.T) {\n\tif 1 != 1 {\n\t\tt.Fatal(\"x\")\n\t}\n}\n"
    kept, cut, outside = cut_at_errors(code, "# harnesstest\n./candidate_test.go:4:2: \"context\" imported and not used\nFAIL\tharnesstest [build failed]\n")
    assert cut == [] and outside == [] and "context" not in kept and go_test_names(kept) == ["TestA"]
    assert "context" not in prune_imports(code)
    _, _, outside2 = cut_at_errors(code, "./candidate_test.go:2:1: undefined: helper\n")
    assert outside2, "a real error outside a test still goes back"


def test_generation_keeps_the_last_attempt_that_ran():
    src = inspect.getsource(generate_package)
    assert "best = (code, run1, list(precut), attempts)" in src
    assert src.index("code, run_final, precut, kept_attempt = best") < src.index("did not collect on the baseline after repairs")
