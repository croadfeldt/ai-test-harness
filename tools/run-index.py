#!/usr/bin/env python3
"""Refresh what the harness writes after every stage, for run directories that already exist:
run-index.json, README.md (the story) and packet/<pkg>/pull-request.md where a packet has none yet.
`python3 tools/run-index.py <run>...` or, with no argument, every run under examples/."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness" / "src"))
from harness import runindex, story  # noqa: E402
from harness.stages.packet import pull_request  # noqa: E402
from harness.util import read_json  # noqa: E402

runs = [Path(a) for a in sys.argv[1:]] or sorted(p for p in (ROOT / "examples").glob("*/*/") if (p / "intake").is_dir())
for r in runs:
    for pj in sorted(r.glob("packet/*/packet.json")):
        if not (pj.parent / "pull-request.md").exists() and (pj.parent / "tests.patch").exists():
            title, body = pull_request(r, pj.parent.name)
            (pj.parent / "pull-request.md").write_text(f"# {title}\n\n{body}")
    idx = runindex.update(r)
    story.write(r, read_json(idx))
    print(idx.parent.relative_to(ROOT) if idx.is_relative_to(ROOT) else idx.parent)
