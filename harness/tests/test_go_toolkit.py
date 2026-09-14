"""The Go test toolkit: gates through the Go helper, and the sandbox's result conversion. Skipped without a Go toolchain."""
import json
import shutil
from pathlib import Path

import pytest

from harness import sandbox_go
from harness.adapters import go

needs_go = pytest.mark.skipif(shutil.which("go") is None, reason="go toolchain not installed")

FILE = '''package harnesstest

import (
	"strings"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
)

// TestLoaderRejectsGarbage asserts that garbage is not a spec.
func TestLoaderRejectsGarbage(t *testing.T) {
	_, err := openapi3.NewLoader().LoadFromData([]byte("garbage"))
	if err == nil {
		t.Fatal("expected an error")
	}
}

func TestWeak(t *testing.T) {
	_ = strings.ToUpper("x")
}
'''


@needs_go
def test_gates_read_the_file_with_go_ast():
    assert go.compile_check(FILE) is None
    assert go.compile_check("package other\n") is not None
    assert go.compile_check("package harnesstest\nfunc (") is not None
    assert go.test_names(FILE) == ["TestLoaderRejectsGarbage", "TestWeak"]
    assert go.imports_ok(FILE, {"github.com/getkin/kin-openapi"}) == []
    assert go.imports_ok(FILE, set()) == ["github.com/getkin/kin-openapi/openapi3"]
    assert [w.split(":")[0] for w in go.weak_assertions(FILE)] == ["TestWeak"]


@needs_go
def test_drop_tests_removes_the_function_and_its_import():
    kept = go.drop_tests(FILE, {"TestWeak"})
    assert "TestWeak" not in kept and '"strings"' not in kept and "TestLoaderRejectsGarbage" in kept
    assert go.compile_check(kept) is None


@needs_go
def test_symbol_refs_and_skips(tmp_path: Path):
    f = tmp_path / "a_test.go"
    f.write_text(FILE.replace('_ = strings.ToUpper("x")', 't.Skip("later")'))
    refs = go.symbol_refs(f, ["github.com/getkin/kin-openapi"])
    assert refs == {"TestLoaderRejectsGarbage": [("github.com/getkin/kin-openapi/openapi3.NewLoader", 0)]}
    assert go.skipped_tests(f) == {"TestWeak"}


def test_extract_code_takes_the_go_fence():
    assert go.extract_code("text\n```go\npackage harnesstest\n```\n").strip() == "package harnesstest"
    assert go.extract_code("nothing here") is None


def test_go_test_json_becomes_results_and_junit(tmp_path: Path):
    events = [
        {"Action": "run", "Package": "harnesstest", "Test": "TestA"},
        {"Action": "output", "Package": "harnesstest", "Test": "TestA", "Output": "=== RUN   TestA\n"},
        {"Action": "output", "Package": "harnesstest", "Test": "TestA", "Output": "    a_test.go:9: expected an error\n"},
        {"Action": "fail", "Package": "harnesstest", "Test": "TestA", "Elapsed": 0.01},
        {"Action": "run", "Package": "harnesstest", "Test": "TestB"},
        {"Action": "pass", "Package": "harnesstest", "Test": "TestB", "Elapsed": 0.5},
        {"Action": "run", "Package": "harnesstest", "Test": "TestC"},
        {"Action": "output", "Package": "harnesstest", "Test": "TestC", "Output": "panic: runtime error: index out of range\n"},
        {"Action": "fail", "Package": "harnesstest", "Test": "TestC", "Elapsed": 0.0},
    ]
    tests = sandbox_go._tests_from_events(events)
    assert tests["harnesstest::TestA"]["status"] == "fail" and "expected an error" in tests["harnesstest::TestA"]["message"]
    assert tests["harnesstest::TestB"] == {"status": "pass", "duration_ms": 500, "message": ""}
    assert tests["harnesstest::TestC"]["status"] == "error"
    sandbox_go._write_junit(tmp_path / "junit.xml", tests)
    from harness import sandbox
    parsed = sandbox.parse_junit(tmp_path / "junit.xml")
    assert {k: v["status"] for k, v in parsed.items()} == {"harnesstest::TestA": "fail", "harnesstest::TestB": "pass", "harnesstest::TestC": "error"}


def test_cover_profile_becomes_coverage_json(tmp_path: Path):
    prof = tmp_path / "cover.out"
    prof.write_text("mode: set\n"
                    "github.com/getkin/kin-openapi/openapi3/loader.go:10.2,12.3 2 1\n"
                    "github.com/getkin/kin-openapi/openapi3/loader.go:14.2,15.3 1 0\n"
                    "github.com/other/mod/x.go:1.1,2.2 1 1\n")
    (tmp_path / "coverage.json").write_text(json.dumps(sandbox_go._coverage_json(prof)))
    cov = sandbox_go.coverage_for(tmp_path / "coverage.json", ["github.com/getkin/kin-openapi"])
    assert cov["covered_lines_in_target"] == 3
    assert cov["files"]["openapi3/loader.go"]["num_statements"] == 3 and cov["files"]["openapi3/loader.go"]["executed_lines"] == [10, 11, 12]
    assert "x.go" not in json.dumps(cov["files"])


def test_readable_log_keeps_compiler_errors(tmp_path: Path):
    (tmp_path / "test.json").write_text('{"Action":"build-output","ImportPath":"harnesstest","Output":"# harnesstest\\n"}\n'
                                        '{"Action":"build-output","ImportPath":"harnesstest","Output":"./a_test.go:9:2: undefined: openapi3.Nope\\n"}\n'
                                        '{"Action":"build-fail","ImportPath":"harnesstest"}\n')
    events = sandbox_go._events(tmp_path / "test.json")
    readable = "".join(e.get("Output", "") for e in events if e.get("Action") in ("output", "build-output"))
    assert "undefined: openapi3.Nope" in readable and sandbox_go._tests_from_events(events) == {}


def test_go_mod_pins_every_module():
    text = sandbox_go.go_mod_text(["github.com/a/b@v1.2.3", "golang.org/x/net@v0.30.0"], "1.25")
    assert "module harnesstest" in text and "\tgithub.com/a/b v1.2.3\n" in text and "\tgolang.org/x/net v0.30.0\n" in text


def test_base_name_handles_go_subtests():
    from harness.stages.execute import base_name
    assert base_name("harnesstest::TestA/case_1") == "TestA" and base_name("tests.test_x::test_a[asyncio]") == "test_a"


def test_semver_max_prefers_the_highest_fixed_version():
    assert go._max_semver(["0.144.0", "0.141.0", "v0.142.0"]) == "v0.144.0"
    assert go._semver_key("v0.144.0") > go._semver_key("v0.139.0")
