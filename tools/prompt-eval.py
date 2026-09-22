#!/usr/bin/env python3
"""docs/12-prompt-and-model-evaluation.md, generated from every example run: the fitness-for-purpose table.
`python3 tools/prompt-eval.py` rewrites it; the site build runs it too."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness" / "src"))
from harness.stages.evaluate import aggregate, rows_for, to_markdown  # noqa: E402


def main(write: str | None = None) -> str:
    runs = sorted(p for p in (ROOT / "examples").glob("*/*/") if (p / "run-index.json").exists())
    rows = [r for run in runs for r in rows_for(run)]
    for r in rows:
        r["run"] = f"{Path(r['run']).name}"
    md = to_markdown(aggregate(rows), rows)
    md = md.replace("# Prompt and model evaluation", "# Prompt and model evaluation\n\n**For:** anyone deciding which model or prompt set to run, and anyone asking whether the harness's results can be trusted. "
                    "Generated from the example runs by `tools/prompt-eval.py`; the same table for any set of runs comes from `harness evaluate`.", 1)
    if write:
        Path(write).write_text(md)
    return md


if __name__ == "__main__":
    out = ROOT / "docs" / "12-prompt-and-model-evaluation.md"
    main(write=str(out)); print(out)
