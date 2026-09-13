"""Stage 0 in CI: every failure-register self-check must pass, without the environment probes."""
from harness import selfcheck


def test_every_register_entry_has_a_check_and_passes():
    rec = selfcheck.run(None, probes=False)
    failed = [c for c in rec["checks"] if c["status"] != "pass"]
    assert not failed, failed
    ids = [c["id"] for c in rec["checks"]]
    assert len(ids) == len(set(ids)) and len(ids) >= 15 and ids[0] == "GF-001"
    assert ids[-1] == "GF-012", "the escalation entry stays last: it is what remains when every correction has run"
