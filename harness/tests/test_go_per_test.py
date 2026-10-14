"""Principle 14 for Go: the head run gives every passing test its own coverage profile, folded into
coverage.json as contexts in the shape coverage.py writes, so the accounting attributes execution per test
in both ecosystems the same way."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from harness import sandbox_go
from harness.stages.account import contexts_by_line

needs_go = pytest.mark.skipif(shutil.which("go") is None, reason="go toolchain not installed")


def _script(per_test: bool) -> str:
    return sandbox_go._script(mod="/mod", modcache="/mc", gocache="/gc", tests="/tests", out="/out", work="/work",
                              coverpkg="example.com/m/...", timeout_s=1200, overlay=None, mutant_src="", per_test=per_test)


def test_the_head_run_script_reruns_each_passing_test_alone_and_other_runs_do_not():
    s = _script(True)
    assert "per-test" in s and '-run "^${t}$"' in s and f'-gt {sandbox_go.PER_TEST_CAP}' in s
    assert '"Test":"[^"/]*"' in s, "top-level tests only; subtests ride with their parent"
    assert "per-test" not in _script(False), "old, re-run and mutant runs pay nothing extra"


def test_add_contexts_folds_per_test_profiles_into_the_coverage_shape(tmp_path):
    d = tmp_path / "per-test"; d.mkdir()
    (d / "TestA.cover.out").write_text("mode: set\nexample.com/m/lib.go:3.20,5.2 2 1\nexample.com/m/lib.go:7.20,9.2 1 0\n")
    (d / "TestB.cover.out").write_text("mode: set\nexample.com/m/lib.go:3.20,5.2 2 1\nexample.com/m/other.go:1.1,2.2 1 1\n")
    cov = {"files": {"example.com/m/lib.go": {"summary": {}, "executed_lines": [3, 4, 5]}}, "totals": {}}
    sandbox_go.add_contexts(cov, d)
    lib = cov["files"]["example.com/m/lib.go"]
    assert lib["contexts"]["3"] == ["TestA", "TestB"] and lib["contexts"]["5"] == ["TestA", "TestB"]
    assert "7" not in lib["contexts"], "a block TestA did not execute is not attributed to it"
    assert cov["files"]["example.com/m/other.go"]["contexts"]["1"] == ["TestB"]
    assert cov["per_test_profiles"] == 2
    p = tmp_path / "coverage.json"; p.write_text(json.dumps(cov))
    by = contexts_by_line(p, lambda f: f[len("example.com/m/"):] if f.startswith("example.com/m/") else None)
    assert by["lib.go"][3] == {"TestA", "TestB"} and by["other.go"][1] == {"TestB"}


@needs_go
def test_the_per_test_block_works_against_a_real_go_test_run(tmp_path):
    """The shell block, run here with the toolchain: two passing tests, each gets a profile that covers only
    what it executed. No sandbox and no network: a self-contained module."""
    m = tmp_path / "m"; m.mkdir(); out = tmp_path / "out"; out.mkdir()
    (m / "go.mod").write_text("module example.com/m\n\ngo 1.22\n")
    (m / "lib.go").write_text("package m\n\nfunc A() int { return 1 }\n\nfunc B() int { return 2 }\n")
    (m / "lib_test.go").write_text('package m\n\nimport "testing"\n\nfunc TestA(t *testing.T) { if A() != 1 { t.Fatal() } }\n\nfunc TestB(t *testing.T) { if B() != 2 { t.Fatal() } }\n')
    script = ("set -u\ncd " + str(m) + "\nexport GOFLAGS=-mod=mod GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOCACHE=" + str(tmp_path / "gc") + "\n"
              f"go test -json -count=1 -coverprofile={out}/cover.out -coverpkg=example.com/m/... . > {out}/test.json 2> {out}/build.log ; rc=$?\n"
              + sandbox_go.per_test_block(str(out), "example.com/m/...", 1200) + "exit $rc\n")
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=600, env={**os.environ, "HOME": str(tmp_path)})
    assert proc.returncode == 0, proc.stdout + proc.stderr + (out / "build.log").read_text()
    profiles = sorted(p.name for p in (out / "per-test").glob("*.cover.out"))
    assert profiles == ["TestA.cover.out", "TestB.cover.out"]
    cov = sandbox_go._coverage_json(out / "cover.out")
    sandbox_go.add_contexts(cov, out / "per-test")
    ctx = cov["files"]["example.com/m/lib.go"]["contexts"]
    assert ctx["3"] == ["TestA"] and ctx["5"] == ["TestB"], ctx
