"""Every old/new outcome maps to a fixed verdict, for CVE tests and characterization tests alike."""
from harness.stages.execute import verdict

FIX = {"direction": "fix", "vulnerable": "1.0", "fixed": "1.1"}
NONE = {"direction": "none", "vulnerable": "1.1", "fixed": None}


def t(category, old, new, message="", status=None):
    return {"category": category, "versions": {"old": old, "new": new}, "message": message, "status": status or new}


def test_cve_verdicts():
    assert verdict(t("cve", "fail", "pass"), "", FIX, None).startswith("fix-pinning confirmed")
    assert verdict(t("cve", "pass", "fail"), "", {**FIX, "direction": "downgrade"}, None).startswith("exposure confirmed")
    assert verdict(t("cve", "pass", "pass"), "", FIX, None).startswith("not a fix-pinning test")
    assert verdict(t("cve", "error", "error", "did not compile: ./x_test.go:3: undefined"), "did not compile", FIX, None) == "did not compile: test bug; back to generation"
    assert verdict(t("cve", "error", "error", "RuntimeError: boom"), "RuntimeError: boom", FIX, None).startswith("blocked on both versions")
    assert verdict(t("cve", "pass", "fail", "AssertionError: x"), "", FIX, None).startswith("fails on the fixed version")
    assert verdict(t("cve", "fail", "fail", "ValueError: JWE too big for us"), "x", FIX, "+    raise ValueError('JWE too big for us')").startswith("fix reached")
    assert verdict(t("cve", "na", "skip"), "", NONE, None).startswith("inconclusive")


def test_characterization_verdicts():
    assert verdict(t("unit", "pass", "pass"), "", NONE, None) == "candidate: passes on head, same on old"
    assert verdict(t("unit", "na", "pass"), "", NONE, None) == "candidate: passes on head"
    assert verdict(t("unit", "fail", "pass"), "", NONE, None).startswith("behavior changed")
    assert verdict(t("unit", "pass", "fail", "AssertionError"), "", NONE, None).startswith("fails on head")
    assert verdict(t("unit", "error", "error", "did not compile: x"), "", NONE, None) == "did not compile: test bug; back to generation"
    assert verdict(t("unit", "pass", "pass", status="flaky"), "", NONE, None) == "flaky: discard"
