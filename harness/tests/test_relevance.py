from pathlib import Path

from harness.stages.relevance import _matches, _skipped, _symbol_refs


def test_symbol_refs_and_skip_markers(tmp_path: Path):
    f = tmp_path / "test_x.py"
    f.write_text("import pytest\nfrom jose import jwt\nimport jose.jwe as jwe\n\ndef test_a():\n    jwt.decode('t', 'k')\n\n@pytest.mark.skip(reason='old')\ndef test_b():\n    jwe.encrypt(b'x', 'k')\n")
    refs = _symbol_refs(f, ["jose"])
    assert ("jose.jwt.decode", 6) in refs["test_a"] and ("jose.jwe.encrypt", 10) in refs["test_b"]
    assert _skipped(f) == {"test_b"}


def test_matching_removed_symbols():
    gone = {"jose.jwt.decode", "jose.jwe"}
    assert _matches("jose.jwt.decode", gone) == "jose.jwt.decode"
    assert _matches("jose.jwe.encrypt", gone) == "jose.jwe"       # a removed module takes its members with it
    assert _matches("jose.jws.sign", gone) is None
    assert _matches("jose.jwt", {"jose.jwt.get_unverified_claims"}) is None   # a module is not gone because one member is
