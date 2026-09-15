"""Stage 7 against a local bare repository: the harness proposes, a person merges with one test edited
and one dropped, and the capture reads the decisions back, emits requested and realized records for
what landed, and signs an acceptance statement. GitHub is stubbed by passing the pull request's facts."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from harness.adapters import python as py
from harness.stages import feedback as F
from harness.stages import propose as P

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "frc-scheduler-server" / "pr-fix-known-vulns-run6"
pytestmark = pytest.mark.skipif(not (EXAMPLE / "packet" / "summary.json").exists() or shutil.which("git") is None, reason="example run or git missing")
IDENT = {"GIT_AUTHOR_NAME": "reviewer", "GIT_AUTHOR_EMAIL": "reviewer@example.invalid", "GIT_COMMITTER_NAME": "reviewer", "GIT_COMMITTER_EMAIL": "reviewer@example.invalid"}


def _git(*args, cwd, env=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env={**os.environ, **(env or {})}).stdout


def test_capture_reads_accepted_edited_and_rejected_back(tmp_path: Path):
    bare = tmp_path / "overlays.git"; _git("init", "--quiet", "--bare", "--initial-branch=main", str(bare), cwd=tmp_path)
    seed = tmp_path / "seed"; _git("clone", "--quiet", str(bare), str(seed), cwd=tmp_path)
    (seed / "README.md").write_text("# overlays\n"); _git("add", ".", cwd=seed); _git("commit", "--quiet", "-m", "seed", cwd=seed, env=IDENT); _git("push", "--quiet", "origin", "main", cwd=seed)
    clone = tmp_path / "overlays"; _git("clone", "--quiet", str(bare), str(clone), cwd=tmp_path)
    work = tmp_path / "run"; shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns("cache", "scratch", "propose", "feedback"))
    prop = P.propose_package(work, "python-jose", clone, remote="origin", base="main", author=("AI Test Harness", "bot@example.invalid"),
                             sign=False, signing_key="", signing_format="ssh", push=True, open_pr=False)
    # The reviewer merges the harness branch, edits the unit file (drops one test, tweaks another), and deletes one CVE file.
    _git("fetch", "--quiet", "origin", cwd=seed); _git("merge", "--quiet", "--no-edit", f"origin/{prop['branch']}", cwd=seed, env=IDENT)
    d = seed / prop["overlay_dir"]
    unit = next(p for p in d.glob("test_*_unit.py"))
    names = py.test_names(unit.read_text()); dropped, tweaked = names[0], names[1]
    src = py.drop_tests(unit.read_text(), {dropped}).replace(f"def {tweaked}(", f"def {tweaked}(  # reviewed\n", 1)
    unit.write_text(src)
    cve_files = sorted(d.glob("test_*_cve_*.py")); removed = cve_files[0]; removed_names = py.test_names(removed.read_text()); removed.unlink()
    _git("add", "-A", cwd=seed); _git("commit", "--quiet", "-m", "review: keep most, edit one, drop one file", cwd=seed, env=IDENT); _git("push", "--quiet", "origin", "main", cwd=seed)
    merge = _git("rev-parse", "HEAD", cwd=seed).strip()
    pr = {"url": "https://example.invalid/pr/1", "number": 1, "state": "merged", "merged_at": "2026-09-15T16:16:06Z", "closed_at": "2026-09-15T16:16:06Z",
          "merged_by": "reviewer", "merge_commit": merge, "review_decision": "", "reviews": []}
    rec = F.capture(work, "python-jose", pr, clone, py)
    by_path = {Path(x["path"]).name: x for x in rec["decisions"]}
    assert by_path[unit.name]["decision"] == "edited" and by_path[unit.name]["tests"][dropped] == "rejected" and by_path[unit.name]["tests"][tweaked] == "edited"
    assert by_path[removed.name]["decision"] == "rejected" and set(by_path[removed.name]["tests"].values()) == {"rejected"}
    untouched = next(x for x in rec["decisions"] if Path(x["path"]).name == cve_files[1].name)
    assert untouched["decision"] == "accepted" and set(untouched["tests"].values()) == {"accepted"}
    assert rec["counts"]["rejected"] == 1 + len(removed_names) and rec["counts"]["accepted"] >= 1 and rec["counts"]["edited"] >= 1
    lines = [json.loads(l) for l in (work / "feedback" / "python-jose" / "decisions.jsonl").read_text().splitlines()]
    assert {l["decision"] for l in lines} == {"accepted", "edited", "rejected"} and all(l["accepted_by"] == "reviewer" for l in lines)
    # Records: one requested and one realized per accepted or edited test that had a candidate record; intents untouched.
    docs = [x for x in yaml.safe_load_all((work / "feedback" / "python-jose" / "udlm" / "test-evidence.yaml").read_text()) if x]
    states = [x["state"] for x in docs]
    assert states.count("Requested") == states.count("Realized") == rec["counts"]["accepted"] + rec["counts"]["edited"]
    real = next(x for x in docs if x["state"] == "Realized")
    assert real["requested_ref"] and real["outputs"]["merge_commit"] == merge and real["outputs"]["accepted_by"] == "reviewer"
    sealed = bool(rec["records"]["sealed"])   # sealing needs a UDLM checkout; CI has none and the records say so
    assert ("integrity" in real) == sealed
    assert (rec["records"] or {}).get("schema_problems") in (0, None), rec["records"]
    from harness.stages.attest import verify
    fb = work / "feedback" / "python-jose"
    assert verify(fb / "acceptance-statement.dsse.json", fb / "signer.pub.pem")
    st = json.loads((fb / "acceptance-statement.json").read_text())
    assert st["subject"][0]["digest"]["gitCommit"] == merge and len(st["subject"]) == 1 + (states.count("Realized") if sealed else 0)


def test_closed_without_merge_rejects_everything(tmp_path: Path):
    work = tmp_path / "run"; shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns("cache", "scratch", "feedback"))
    bare = tmp_path / "overlays.git"; _git("init", "--quiet", "--bare", "--initial-branch=main", str(bare), cwd=tmp_path)
    clone = tmp_path / "overlays"; _git("clone", "--quiet", str(bare), str(clone), cwd=tmp_path)
    pr = {"url": "https://example.invalid/pr/2", "number": 2, "state": "closed", "merged_at": None, "closed_at": "2026-09-15T00:00:00Z",
          "merged_by": None, "merge_commit": None, "review_decision": "", "reviews": []}
    rec = F.capture(work, "python-jose", pr, clone, py)
    assert rec["outcome"].startswith("closed without merge") and rec["counts"]["accepted"] == 0 and rec["records"] is None
