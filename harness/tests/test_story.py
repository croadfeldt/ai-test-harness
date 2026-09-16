"""The story and the catalogue: every run folder opens with who, what, why, where, when, and every file has a reader."""
from pathlib import Path

from harness import runindex, story

RUN = Path(__file__).resolve().parents[2] / "examples" / "frc-scheduler-server" / "pr-fix-known-vulns-run6"


def test_every_catalogued_file_has_an_audience_and_a_reason():
    idx = runindex.build(RUN)
    assert idx["catalogue"], "the example run has files to catalogue"
    for c in idx["catalogue"]:
        assert c["audience"] in story.AUDIENCE_NAMES, c
        assert c["purpose"].endswith(".") and len(c["purpose"]) > 20, c
        assert (RUN / c["path"]).exists(), c["path"]


def test_story_answers_the_five_questions_and_shows_the_records(tmp_path):
    st = story.build(RUN)
    titles = [s["title"] for s in st["sections"]]
    assert titles[:2] == ["In plain terms", "Who, what, why, where, when"]
    five = dict(st["sections"][1]["table"]["rows"])
    assert set(five) == {"Who", "What", "Why", "Where", "When"}
    assert "merged by" in five["Who"] and "python-jose 3.3.0 to 3.4.0" in five["What"]
    recs = next(s for s in st["sections"] if s["title"] == "The records, in plain terms")
    states = {r[1] for r in recs["table"]["rows"]}
    assert {"Discovered", "Intent", "Requested", "Realized"} <= states
    not_taken = next(s for s in st["sections"] if s["title"].startswith("Actions it did not take"))
    assert any("did not merge" in b for b in not_taken["bullets"])
    md = story.to_markdown(st)
    assert md.startswith("# Run 76a3fa863e76") and "## What is in this folder" in md
    assert "|" not in "".join(r[2] for r in recs["table"]["rows"]) or "\\|" in md   # cells never break the table


def test_pull_request_text_is_written_at_packet_time():
    text = (RUN / "packet" / "python-jose" / "pull-request.md").read_text()
    assert text.startswith("# Tests for python-jose 3.4.0:")
    assert "Files this pull request carries:" in text and "tests.patch" not in text
    assert "overlays/python/python-jose/3.4.x/statement.dsse.json" in text


def test_document_10_catalogue_matches_the_table():
    import importlib.util
    spec = importlib.util.spec_from_file_location("catalogue", RUN.parents[2] / "tools" / "catalogue.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert mod.main(check=True) == 0, "run python3 tools/catalogue.py and commit docs/10"
