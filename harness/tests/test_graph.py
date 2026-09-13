import json
from pathlib import Path
from unittest import mock

from harness.adapters import python as py


def test_depth_from_pip_report(tmp_path: Path):
    report = {"install": [
        {"metadata": {"name": "app-dep", "version": "1.0", "requires_dist": ["leaf>=1", "mid; python_version<'2'"]}, "requested": True},
        {"metadata": {"name": "mid", "version": "2.0", "requires_dist": ["leaf"]}, "requested": True},
        {"metadata": {"name": "leaf", "version": "3.0", "requires_dist": []}, "requested": False},
        {"metadata": {"name": "Deep_Thing", "version": "0.1", "requires_dist": []}, "requested": False},
    ]}
    manifest = tmp_path / "requirements.txt"
    manifest.write_text("app-dep==1.0\nmid==2.0\n")
    with mock.patch.object(py, "_pip_report", return_value=(report, "mocked")):
        g = py.resolve_graph(tmp_path, manifest, "3.12")
    assert g.packages["app-dep"].depth == 1 and g.packages["mid"].depth == 1
    assert g.packages["leaf"].depth == 2 and sorted(g.packages["leaf"].parents) == ["app-dep", "mid"]
    assert g.packages["deep-thing"].depth == 2 and g.packages["deep-thing"].parents == ["<unresolved-edge>"]
    assert g.packages["leaf"].purl == "pkg:pypi/leaf@3.0"
    assert "mid" not in g.packages["app-dep"].requires  # marker evaluated false
