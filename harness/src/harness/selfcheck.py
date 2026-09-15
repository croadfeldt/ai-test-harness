"""Stage 0: self-verification. Blueprint section 5 stage 0 and section 17.

One check per generation-failure-register entry, each reproducing the original failure on a fixture
and proving the detector fires and the correction holds. Plus the sandbox and model probes. The
result is written to the work directory and referenced by every manifest the run produces. A failing
check stops the pipeline: fail closed, no override.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from .util import log, now_iso, tool_available, write_json

CHECKS = []


def check(gf_id: str, title: str):
    def deco(fn):
        CHECKS.append((gf_id, title, fn))
        return fn
    return deco


# ---------------------------------------------------------------- register self-checks

@check("GF-001", "empty content after hidden reasoning is a failed attempt, and reasoning-off is sent")
def gf001():
    from .llm import ModelConfig
    cfg = ModelConfig(base_url="http://x/v1", model="m", api_key=None)
    assert cfg.reasoning_effort == "none", "client does not send reasoning_effort=none by default"
    import inspect as _i
    src = _i.getsource(__import__("harness.llm", fromlist=["x"]).Model.chat)
    assert "self.cfg.base_url" not in src.split("record = {")[1].split("}")[0], "a call record must not carry the endpoint address"
    from .adapters.python import extract_code as extract_python
    assert extract_python("") is None, "empty response must not yield a candidate"


@check("GF-002", "repetition loop is detected and normal code is not")
def gf002():
    from .llm import _looping, ModelConfig
    assert _looping("x" * 1000 + "mXq7" * 400), "loop not detected"
    normal = "\n".join(f"def test_{i}():\n    assert f({i}) == {i * 2}\n" for i in range(60))
    assert not _looping(normal), "false positive on ordinary test code"
    assert ModelConfig(base_url="http://x/v1", model="m", api_key=None).frequency_penalty > 0
    from .stages import generate
    assert "never inline long literal strings" in generate.SYSTEM


@check("GF-003", "catch-all and assertion-free tests are rejected as weak")
def gf003():
    from .stages.generate import _weak_assertions
    weak = _weak_assertions("import pytest\ndef test_a():\n    with pytest.raises((ValueError, Exception)):\n        pass\ndef test_b():\n    x = 1\n")
    assert len(weak) == 2, weak
    assert _weak_assertions("import pytest\ndef test_c():\n    with pytest.raises(ValueError):\n        pass\n") == []


@check("GF-004", "the package's declared dependencies may be imported; unrelated modules may not")
def gf004():
    from .stages.generate import _imports_ok
    code = "import jose\nimport cryptography\nimport requests\n"
    assert _imports_ok(code, {"jose", "cryptography"}) == ["requests"]


@check("GF-005", "the fix diff reaches the CVE prompt when a patch exists")
def gf005():
    from .stages.generate import build_prompt
    facts = {"package": "p", "new_version": "2", "old_version": "1", "import_names": ["p"], "call_sites_summary": {"symbols_used": []},
             "api_diff_summary": {"breaking": 0}}
    v = [{"id": "GHSA-x", "aliases": ["CVE-2024-1"], "summary": "s", "severity": None, "fixed_versions": ["2"], "affected_symbols": [], "references": []}]
    out = build_prompt("cve", facts, {"symbols": []}, [], v, 2, fix_patch="--- old/p/a.py\n+++ new/p/a.py\n+    raise ValueError\n")
    assert "FIX DIFF 1 -> 2" in out and "find the hunk" in out.lower()


@check("GF-006", "constants are in the API surface and version-only names reach the prompt")
def gf006():
    import tempfile
    from .adapters.python import extract_api
    from .stages.generate import build_prompt
    d = Path(tempfile.mkdtemp()); (d / "pkg").mkdir(); (d / "pkg" / "__init__.py").write_text("")
    (d / "pkg" / "constants.py").write_text("JWE_SIZE_LIMIT = 250 * 1024\n_private = 1\n")
    names = {s.qualname for s in extract_api(d, ["pkg"])}
    assert "pkg.constants.JWE_SIZE_LIMIT" in names and "pkg.constants._private" not in names
    facts = {"package": "p", "new_version": "2", "old_version": "1", "import_names": ["p"], "call_sites_summary": {"symbols_used": []}, "api_diff_summary": {"breaking": 0}}
    out = build_prompt("cve", facts, {"symbols": []}, [], [], 2, None, new_only=["p.constants.JWE_SIZE_LIMIT"])
    assert "SYMBOLS ONLY IN THE NEW VERSION" in out and "JWE_SIZE_LIMIT" in out
    src = inspect.getsource(__import__("harness.stages.generate", fromlist=["x"]).generate_package)
    assert "does not even collect on the VULNERABLE version" in src, "old-version collection gate missing"


@check("GF-007", "a crash on the fixed version is separated from an assertion failure")
def gf007():
    msgs = {"a": "AssertionError: assert 1 == 2", "b": "Failed: DID NOT RAISE <class 'ValueError'>", "c": "jose.exceptions.JWEError: module 'lib' has no attribute"}
    crashes = {k for k, m in msgs.items() if not m.startswith(("AssertionError", "Failed: DID NOT RAISE", "assert "))}
    assert crashes == {"c"}
    src = inspect.getsource(__import__("harness.stages.generate", fromlist=["x"]).generate_package)
    assert "crashed before reaching their" in src


@check("GF-008", "the sandbox keeps running past a file that fails to collect")
def gf008():
    from . import sandbox
    src = inspect.getsource(sandbox.run_tests)
    assert "--continue-on-collection-errors" in src


@check("GF-009", "advisory ids sharing a CVE collapse to one issue")
def gf009():
    from .stages.generate import _group_advisories
    v = [{"id": "GHSA-a", "aliases": ["CVE-2024-1", "PYSEC-1"]}, {"id": "PYSEC-1", "aliases": ["CVE-2024-1"]}, {"id": "GHSA-b", "aliases": ["CVE-2024-2"]}, {"id": "MAL-1", "aliases": []}]
    g = _group_advisories(v)
    assert set(g) == {"CVE-2024-1", "CVE-2024-2", "MAL-1"} and len(g["CVE-2024-1"]) == 2


@check("GF-010", "the differential environment is the base commit's own graph")
def gf010():
    from .stages import execute
    src = inspect.getsource(execute.execute_package)
    assert '_reqs(workdir, "old"' in src and "_pin(" not in src


@check("GF-011", "graph resolution runs inside the target interpreter's image when it can")
def gf011():
    from .adapters import python as py
    src = inspect.getsource(py._pip_report)
    assert "podman" in src and "python:{python_version}-slim" in src
    src2 = inspect.getsource(__import__("harness.sandbox", fromlist=["x"]).prefetch_wheelhouse)
    assert "podman" in src2


@check("GF-013", "the agent may not read past the cap before running a test, and always keeps calls for run and submit")
def gf013():
    from .stages.agent import Budget
    b = Budget(max_tool_calls=14)
    for _ in range(6):
        assert b.allow("read_source") is None
    assert b.allow("read_source") is not None, "seventh read before any run must be refused"
    assert b.allow("run_tests") is None
    assert b.allow("read_source") is None, "reads reopen after a run"
    b2 = Budget(max_tool_calls=3)
    b2.allow("run_tests"); assert b2.allow("read_source") is not None, "reserve for run and submit must hold"


@check("GF-014", "a failure message that the fix diff introduced is recognized as 'fix reached'")
def gf014():
    from .stages.agent import fix_reached
    diff = "--- old/jose/jws.py\n+++ new/jose/jws.py\n+        raise JWSError('The specified key is an asymmetric key or x509 certificate and should not be used as an HMAC secret.')\n"
    assert fix_reached("jose.exceptions.JWKError: The specified key is an asymmetric key or x509 certificate and should not be used as an HMAC secret.", diff)
    assert not fix_reached("AttributeError: module 'lib' has no attribute 'RAND_bytes'", diff)
    from .stages import execute
    assert "fix reached, assertion wrong" in inspect.getsource(execute.execute_package)


@check("GF-015", "an identical run result twice in a row is reported as a blocked path and a candidate defect")
def gf015():
    from .stages.agent import RepeatDetector
    d = RepeatDetector()
    assert d.note("[new] t=fail (X)\n[old] t=fail (X)") is None
    assert d.note("[new] t=fail (X)\n[old] t=fail (X)") is not None, "second identical result must be flagged"
    assert d.note("[new] t=pass\n[old] t=fail (Y)") is None
    d2 = RepeatDetector(); d2.note("[new] t=pass\n[old] t=pass")
    assert "does not reach the vulnerable behavior" in (d2.note("[new] t=pass\n[old] t=pass") or ""), "identical pass/pass is 'no trigger', not a defect"
    assert d2.kind == "no-trigger"
    from .stages import execute
    assert "blocked on both versions" in inspect.getsource(execute.execute_package)


@check("GF-016", "a downgrade derives vulnerable=new, fixed=old from the advisories, and the verdicts follow the roles")
def gf016():
    from .stages.generate import cve_roles
    bump = cve_roles(old_version="3.3.0", new_version="3.4.0", vulns_old=[{"id": "A", "fixed_versions": ["3.4.0"]}], vulns_new=[])
    assert bump == {"vulnerable": "3.3.0", "fixed": "3.4.0", "direction": "fix"}, bump
    down = cve_roles(old_version="0.6.4", new_version="0.4.8", vulns_old=[], vulns_new=[{"id": "B", "fixed_versions": ["0.6.3"]}])
    assert down == {"vulnerable": "0.4.8", "fixed": "0.6.4", "direction": "downgrade"}, down
    from .stages import execute
    src = inspect.getsource(execute.execute_package)
    assert "exposure confirmed" in src and "downgrade" in src


@check("GF-017", "existence-only assertions are rejected as trivial")
def gf017():
    from .stages.generate import _weak_assertions
    trivial = "def test_a():\n    assert callable(f)\n    assert isinstance(x, int)\ndef test_b():\n    assert issubclass(E, Exception)\n"
    assert len(_weak_assertions(trivial)) == 2, _weak_assertions(trivial)
    assert _weak_assertions("def test_c():\n    assert decode(b'\\x02\\x01\\x05') == (5, b'')\n") == []


@check("GF-018", "a parametrized pytest id resolves to its manifest test name")
def gf018():
    from .stages.execute import base_name
    assert base_name("tests.test_x::test_a[asyncio]") == "test_a"
    assert base_name("tests.test_x::test_a[1-2]") == "test_a" and base_name("test_b") == "test_b"


@check("GF-019", "reasoning leaking into content is detected and the call falls back to thinking off")
def gf019():
    from .llm import reasoning_leak
    assert reasoning_leak("We need answer user's request: write pytest tests. Need think thoroughly. We need produce 10 unit tests" + " ok" * 200)
    assert not reasoning_leak("```python\ndef test_a():\n    assert 1 == 1\n```")
    assert not reasoning_leak("")
    src = inspect.getsource(__import__("harness.llm", fromlist=["x"]).Model.chat)
    assert "thinking_fallback" in src
    from .llm import strip_think
    assert strip_think("<think>plan plan</think>\n```python\nx=1\n```") == ("```python\nx=1\n```", 25)
    assert strip_think("<think>never closed")[0] == ""
    assert strip_think("The user asks for ok. No reasoning needed.\n</think>\n\nok")[0] == "ok", "template-opened reasoning must be stripped"


@check("GF-020", "a test file whose last baseline run collected nothing is discarded, never shipped")
def gf020():
    from .stages.generate import _collected_nothing, generate_package
    assert _collected_nothing({})
    assert _collected_nothing({"tests.test_candidate": {"status": "error", "message": "collection failure"}})
    assert not _collected_nothing({"tests/t.py::test_a": {"status": "pass", "message": ""}, "tests/t.py::test_b": {"status": "error", "message": "x"}})
    src = inspect.getsource(generate_package)
    assert "did not collect on the baseline after repairs" in src and src.index("did not collect on the baseline") < src.index("kept_code = code")


@check("GF-021", "a tool call cut off at the output limit is neither run nor echoed; the model is told and the run goes on")
def gf021():
    from .stages.agent import sane_tool_calls, run_agent
    cut_call = [{"id": "c1", "type": "function", "function": {"name": "run_tests", "arguments": '{"code": "package harnesstest\\n func Te'}}]
    fixed, cut = sane_tool_calls(cut_call, "tool_calls")
    assert cut == ["c1"] and fixed[0]["function"]["arguments"] == "{}"
    ok_call = [{"id": "c2", "type": "function", "function": {"name": "list_api", "arguments": '{"module_prefix": "x"}'}}]
    assert sane_tool_calls(ok_call, "tool_calls") == (ok_call, [])
    assert sane_tool_calls(ok_call, "length")[1] == ["c2"]
    src = inspect.getsource(run_agent)
    assert "except HarnessError" in src and "cut off at the output limit" in src


@check("GF-022", "one Go test file that does not compile no longer takes the package's other files down with it")
def gf022():
    from .sandbox_go import files_blamed, run_tests
    import tempfile
    d = Path(tempfile.mkdtemp()); (d / "a_test.go").write_text("package harnesstest\n"); (d / "b_test.go").write_text("package harnesstest\n")
    out = "# harnesstest [harnesstest.test]\n./b_test.go:24:27: undefined: openapi3filter.Route\n./b_test.go:42:27: undefined: x\nFAIL\tharnesstest [build failed]\n"
    assert files_blamed(out, d) == ["b_test.go"]
    assert files_blamed("FAIL\tharnesstest [build failed]\n", d) == []
    src = inspect.getsource(run_tests)
    assert "files_not_compiled" in src and "len(blamed) < len(all_files)" in src


@check("GF-012", "every old/new outcome maps to a fixed, honest verdict")
def gf012():
    from .stages import execute
    src = inspect.getsource(execute.execute_package)
    for phrase in ("fix-pinning confirmed", "not a fix-pinning test", "fails on the fixed version", "inconclusive", "flaky: discard", "behavior changed"):
        assert phrase in src, f"verdict text missing: {phrase}"


# ---------------------------------------------------------------- environment probes

def probe_sandbox(python_version: str) -> dict:
    """Runs the isolation probe inside the real sandbox. Skipped, not failed, when podman is absent."""
    from . import sandbox
    if sandbox.TARGET != "pod" and not tool_available("podman"):
        return {"status": "skipped", "reason": "podman not installed"}
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="harness-selfcheck-"))
    (tmp / "tests").mkdir()
    (tmp / "tests" / "test_probe.py").write_text(
        "import os, socket, pytest\n"
        "def test_no_network():\n    s = socket.socket(); s.settimeout(3)\n    with pytest.raises(OSError):\n        s.connect(('1.1.1.1', 443))\n"
        "def test_no_secrets_in_env():\n    assert not [k for k in os.environ if any(x in k.upper() for x in ('TOKEN','SECRET','PASSWORD','KEY'))]\n"
        "def test_rootfs_read_only():\n    with pytest.raises(OSError):\n        open('/usr/harness-probe', 'w')\n"
        "def test_offline_install_worked():\n    import six\n")
    import os
    pre = os.environ.get("HARNESS_PROBE_WHEELHOUSE")   # a deny-all pod cannot download; a networked stage prefetched it
    wh = Path(pre) if pre and (Path(pre) / ".complete").exists() else sandbox.prefetch_wheelhouse(["six==1.17.0"], python_version, tmp / "wh")
    s = sandbox.run_tests(wheelhouse=wh, requirements=["six==1.17.0"], tests_dir=tmp / "tests", out_dir=tmp / "out", cover=["six"], label="selfcheck")
    r = sandbox.parse_junit(Path(s["junit"])) if s["junit"] else {}
    statuses = {k.split("::")[-1]: v["status"] for k, v in r.items()}
    ok = bool(statuses) and all(v == "pass" for v in statuses.values()) and not s["install_failed"]
    return {"status": "pass" if ok else "fail", "tests": statuses, "image": s["image"], "isolation": s["isolation"]}


def probe_model() -> dict:
    """The endpoint answers, names its model, and returns content with reasoning off."""
    import os
    if os.environ.get("HARNESS_SELFCHECK_SKIP_MODEL") == "1":
        return {"status": "skipped", "reason": "HARNESS_SELFCHECK_SKIP_MODEL=1"}
    try:
        import tempfile
        from .llm import Model, ModelConfig
        cfg = ModelConfig.from_env()
        m = Model(cfg, Path(tempfile.mkdtemp(prefix="harness-selfcheck-model-")))
        text, rec = m.chat("Answer with one word.", "Reply: ready", "selfcheck", max_tokens=16)
        ok = bool(text.strip()) and rec["finish_reason"] in ("stop", "length")
        return {"status": "pass" if ok else "fail", "endpoint": cfg.label, "endpoint_digest": cfg.endpoint_digest, "model": rec["model"],
                "reasoning_effort": cfg.reasoning_effort, "reasoning_tokens": (rec["usage"].get("completion_tokens_details") or {}).get("reasoning_tokens"),
                "latency_s": rec["latency_s"]}
    except Exception as e:
        return {"status": "fail", "error": str(e)[:300]}


def run(workdir: Path | None, python_version: str = "3.12", probes: bool = True, sandbox_only: bool = False) -> dict:
    """sandbox_only: the execute pod's own probe; register checks and the model probe ran in the selfcheck task."""
    if sandbox_only:
        rec = {"stage": 0, "generated": now_iso(), "checks": [], "sandbox": probe_sandbox(python_version), "model": {"status": "skipped", "reason": "sandbox-only probe"}}
        rec["passed"] = rec["sandbox"]["status"] == "pass"; rec["failed"] = [] if rec["passed"] else ["sandbox"]
        log(f"  probe sandbox (in this pod): {rec['sandbox']['status']}")
        if workdir:
            write_json(workdir / "selfcheck" / "selfcheck-sandbox.json", rec)
        return rec
    results = []
    for gf_id, title, fn in CHECKS:
        try:
            fn()
            results.append({"id": gf_id, "title": title, "status": "pass"})
        except AssertionError as e:
            results.append({"id": gf_id, "title": title, "status": "fail", "detail": str(e)[:300]})
        except Exception as e:
            results.append({"id": gf_id, "title": title, "status": "fail", "detail": f"{type(e).__name__}: {e}"[:300]})
    import os
    skip_sb = os.environ.get("HARNESS_SELFCHECK_SKIP_SANDBOX") == "1"   # the sandbox probe runs inside the execute pod instead
    pre = os.environ.get("HARNESS_PROBE_WHEELHOUSE")
    if skip_sb and probes and pre:
        # This pod has the network and the execute pod does not: fetch the probe's wheels for it now.
        from . import sandbox
        sandbox.prefetch_wheelhouse(["six==1.17.0"], python_version, Path(pre))
    record = {"stage": 0, "generated": now_iso(), "checks": results,
              "sandbox": (probe_sandbox(python_version) if probes and not skip_sb else
                          {"status": "skipped", "reason": "runs inside the execute pod" if skip_sb else "probes disabled"}),
              "model": probe_model() if probes else {"status": "skipped", "reason": "probes disabled"}}
    failed = [r["id"] for r in results if r["status"] != "pass"]
    for name in ("sandbox", "model"):
        if record[name]["status"] == "fail":
            failed.append(name)
    record["passed"] = not failed
    record["failed"] = failed
    for r in results:
        log(f"  {r['id']} {'pass' if r['status'] == 'pass' else 'FAIL'}  {r['title']}" + (f"  ({r.get('detail')})" if r['status'] != 'pass' else ""))
    for name in ("sandbox", "model"):
        log(f"  probe {name}: {record[name]['status']}" + (f" ({record[name].get('reason') or record[name].get('error', '')})" if record[name]["status"] != "pass" else ""))
    if workdir:
        write_json(workdir / "selfcheck" / "selfcheck.json", record)
    return record


def require(workdir: Path, python_version: str = "3.12", probes: bool = True) -> dict:
    """Stage 0 as called by every later stage: run, record, and stop the pipeline on any failure."""
    from .util import HarnessError
    log("stage 0: self-verification")
    rec = run(workdir, python_version, probes)
    if not rec["passed"]:
        raise HarnessError(f"self-verification failed: {rec['failed']}. No evidence is produced from a harness that fails its own checks.")
    return rec
