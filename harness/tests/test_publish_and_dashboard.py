"""The runs store and the dashboard: a run publishes four small files; the page is rendered from them and the examples."""
import importlib.util
import json
from pathlib import Path

from harness.stages.publish import publish_into

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "examples" / "frc-scheduler-server" / "pr-fix-known-vulns-run6"


def test_publish_into_a_directory_store_is_idempotent(tmp_path):
    store = tmp_path / "store"
    dest = publish_into(RUN, store)
    assert dest == store / "runs" / "frc-scheduler-server" / "76a3fa863e76"
    assert (dest / "run-index.json").exists() and (dest / "README.md").exists() and (dest / "evaluation.json").exists()
    assert json.loads((dest / "evaluation.json").read_text())["rows"][0]["package"] == "python-jose"
    idx = json.loads((store / "index.json").read_text())
    assert idx["format"] == "ai-test-harness/runs-store/v1" and [r["run_id"] for r in idx["runs"]] == ["76a3fa863e76"]
    publish_into(RUN, store)
    assert len(json.loads((store / "index.json").read_text())["runs"]) == 1, "publishing the same run twice adds nothing"


def test_dashboard_collects_every_run_and_renders(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("build_dashboard", ROOT / "tools" / "build-dashboard.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    store = tmp_path / "store"; publish_into(RUN, store)
    mod.STORE = str(store); mod.SITE = tmp_path / "site"
    data = mod.collect()
    refs = [r["ref"] for r in data["runs"]]
    assert any(r.startswith("examples/") for r in refs) and any(r.startswith("store/") for r in refs)
    run6 = next(r for r in data["runs"] if r["ref"] == "examples/frc-scheduler-server/pr-fix-known-vulns-run6")
    assert run6["proven"] == 3 and run6["reviewer_accepted"] == 7 and run6["merged"] and run6["page"].endswith("pr-fix-known-vulns-run6/index.html")
    assert any(g["reads_as"].startswith("accepted by a reviewer") for g in data["aggregate"])
    out = mod.main()
    html = out.read_text()
    assert "For leadership" in html and "For engineering" in html and "For pipeline owners" in html and '"run_id": "76a3fa863e76"' in html
    assert "{{" not in html, "no unrendered template braces"
