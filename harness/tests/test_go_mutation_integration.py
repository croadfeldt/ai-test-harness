"""The Go mutation path end to end on a real, tiny module: prefetch, a sealed run for coverage,
sites on executed lines, one mutant through the replace directive. Needs podman, go, and the
network once for the module. Skipped otherwise."""
import json
import shutil
from pathlib import Path

import pytest

from harness.adapters import go

pytestmark = pytest.mark.skipif(shutil.which("podman") is None or shutil.which("go") is None, reason="podman and go required")

TEST = '''package harnesstest

import (
	"testing"

	"github.com/google/uuid"
)

// TestParseRejectsGarbage asserts that a non-UUID string does not parse.
func TestParseRejectsGarbage(t *testing.T) {
	if _, err := uuid.Parse("not-a-uuid"); err == nil {
		t.Fatal("expected an error")
	}
}

// TestParseRoundTrip asserts that a canonical UUID parses back to the same string.
func TestParseRoundTrip(t *testing.T) {
	const s = "123e4567-e89b-12d3-a456-426614174000"
	u, err := uuid.Parse(s)
	if err != nil || u.String() != s {
		t.Fatalf("got %v, %v", u, err)
	}
}
'''


def test_go_mutants_run_through_a_replaced_module(tmp_path: Path):
    reqs = ["github.com/google/uuid@v1.6.0"]
    env = go.prefetch(reqs, None, tmp_path / "env")
    tests = tmp_path / "tests"; tests.mkdir(); (tests / "uuid_unit_test.go").write_text(TEST)
    base = go.run_tests(env, tests, tmp_path / "base", cover=["github.com/google/uuid"], label="mut-base")
    results = go.parse_results(base)
    assert {k.split("::")[-1]: v["status"] for k, v in results.items()} == {"TestParseRejectsGarbage": "pass", "TestParseRoundTrip": "pass"}
    executed = go.coverage_files(Path(base["coverage"]), ["github.com/google/uuid"])
    assert "uuid.go" in executed and executed["uuid.go"]
    src_root = go.fetch("github.com/google/uuid", "v1.6.0", tmp_path / "cache", None)
    sites = go.mutation_sites(src_root / "uuid.go", executed["uuid.go"])
    assert sites, "executed lines of uuid.go must offer mutation sites"
    # One compare-swap on an executed line: Parse's length or delimiter checks. Killed or survived, not invalid.
    site = next(s for s in sites if s["op"] in ("compare-swap", "cond-negate"))
    code = go.apply_mutation(src_root / "uuid.go", site)
    assert code and code != (src_root / "uuid.go").read_text()
    facts = {"package": "github.com/google/uuid", "new_version": "v1.6.0"}
    mdir = tmp_path / "m001"; go.write_overlay(mdir, "uuid.go", code, facts)
    assert json.loads((mdir / "overlay.json").read_text())["module"] == "github.com/google/uuid"
    s = go.run_tests(env, tests, mdir / "out", cover=[], label="mut-m001", overlay_dir=mdir)
    r = go.parse_results(s)
    killed_by = sorted({k.split("::")[-1] for k, v in r.items() if v["status"] in ("fail", "error")})
    status = go.mutant_status(s, r, killed_by)
    assert status in ("killed", "killed-init", "survived"), (status, (mdir / "out" / "stdout.log").read_text()[-600:])
    assert "/work/mutant" in (mdir / "out" / "run.sh").read_text()
