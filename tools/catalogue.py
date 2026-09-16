#!/usr/bin/env python3
"""Rewrite the artifact catalogue in docs/10-reading-the-artifacts.md from the harness's own table, so
the document and the run index can never name a file differently. `python3 tools/catalogue.py [--check]`."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness" / "src"))
from harness.runindex import CATALOGUE  # noqa: E402
from harness.story import AUDIENCE_NAMES  # noqa: E402

DOC = ROOT / "docs" / "10-reading-the-artifacts.md"
START, END = "<!-- catalogue:start -->", "<!-- catalogue:end -->"


def render() -> str:
    out = [START, "", "Generated from `harness/src/harness/runindex.py` by `tools/catalogue.py`; the run index carries the same",
           "label on every file it lists, and the story at the top of each run groups the files by it.", ""]
    for aud, name in AUDIENCE_NAMES.items():
        rows = [(k, why) for k, (a, why) in CATALOGUE.items() if a == aud]
        if not rows:
            continue
        out += [f"**{name}**", "", "| File | What it is for |", "|---|---|"]
        out += [f"| `{k}` | {why} |" for k, why in rows] + [""]
    out.append(END)
    return "\n".join(out)


def main(check: bool = False) -> int:
    text = DOC.read_text()
    if START not in text or END not in text:
        raise SystemExit(f"{DOC} has no catalogue markers")
    new = text[: text.index(START)] + render() + text[text.index(END) + len(END):]
    if check:
        return 0 if new == text else 1
    DOC.write_text(new)
    return 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
