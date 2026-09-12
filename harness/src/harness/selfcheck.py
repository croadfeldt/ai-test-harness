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
    from .stages.generate import extract_python
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
    assert '_reqs(workdir, "old")' in src and "_pin(" not in src


@check("GF-011", "graph resolution runs inside the target interpreter's image when it can")
def gf011():
    from .adapters import python as py
    src = inspect.getsource(py._pip_report)
    assert "podman" in src and "python:{python_version}-slim" in src
    src2 = inspect.getsource(__import__("harness.sandbox", fromlist=["x"]).prefetch_wheelhouse)
    assert "podman" in src2


@check("GF-012", "every old/new outcome maps to a fixed, honest verdict")
def gf012():
    from .stages import execute
    src = inspect.getsource(execute.execute_package)
    for phrase in ("fix-pinning confirmed", "not a fix-pinning test", "fails on the fixed version", "inconclusive", "flaky: discard", "behavior changed"):
        assert phrase in src, f"verdict text missing: {phrase}"


# ---------------------------------------------------------------- environment probes

def probe_sandbox(python_version: str) -> dict:
    """Runs the isolation probe inside the real sandbox. Skipped, not failed, when podman is absent."""
    if not tool_available("podman"):
        return {"status": "skipped", "reason": "podman not installed"}
    import tempfile
    from . import sandbox
    tmp = Path(tempfile.mkdtemp(prefix="harness-selfcheck-"))
    (tmp / "tests").mkdir()
    (tmp / "tests" / "test_probe.py").write_text(
        "import os, socket, pytest\n"
        "def test_no_network():\n    s = socket.socket(); s.settimeout(3)\n    with pytest.raises(OSError):\n        s.connect(('1.1.1.1', 443))\n"
        "def test_no_secrets_in_env():\n    assert not [k for k in os.environ if any(x in k.upper() for x in ('TOKEN','SECRET','PASSWORD','KEY'))]\n"
        "def test_rootfs_read_only():\n    with pytest.raises(OSError):\n        open('/usr/harness-probe', 'w')\n"
        "def test_offline_install_worked():\n    import six\n")
    wh = sandbox.prefetch_wheelhouse(["six==1.17.0"], python_version, tmp / "wh")
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
        return {"status": "pass" if ok else "fail", "endpoint": cfg.base_url, "model": rec["model"],
                "reasoning_effort": cfg.reasoning_effort, "reasoning_tokens": (rec["usage"].get("completion_tokens_details") or {}).get("reasoning_tokens"),
                "latency_s": rec["latency_s"]}
    except Exception as e:
        return {"status": "fail", "error": str(e)[:300]}


def run(workdir: Path | None, python_version: str = "3.12", probes: bool = True) -> dict:
    results = []
    for gf_id, title, fn in CHECKS:
        try:
            fn()
            results.append({"id": gf_id, "title": title, "status": "pass"})
        except AssertionError as e:
            results.append({"id": gf_id, "title": title, "status": "fail", "detail": str(e)[:300]})
        except Exception as e:
            results.append({"id": gf_id, "title": title, "status": "fail", "detail": f"{type(e).__name__}: {e}"[:300]})
    record = {"stage": 0, "generated": now_iso(), "checks": results,
              "sandbox": probe_sandbox(python_version) if probes else {"status": "skipped", "reason": "probes disabled"},
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
