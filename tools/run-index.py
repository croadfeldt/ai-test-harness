#!/usr/bin/env python3
"""Write or refresh run-index.json for run directories: `python3 tools/run-index.py <run>...` or, with no
argument, every run under examples/. The harness writes the same file at the end of every stage."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness" / "src"))
from harness import runindex  # noqa: E402

runs = [Path(a) for a in sys.argv[1:]] or sorted(p for p in (ROOT / "examples").glob("*/*/") if (p / "intake").is_dir())
for r in runs:
    idx = runindex.update(r)
    print(idx.relative_to(ROOT) if idx.is_relative_to(ROOT) else idx)
