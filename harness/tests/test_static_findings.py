"""Static analysis findings reach the prompt and triage, whichever linter wrote them."""
from harness.stages.generate import security_findings, static_lines
from harness.stages.triage import static_findings

BANDIT = {"tool": "bandit", "status": "ran", "issues": [{"filename": "app/auth.py", "line_number": 12, "test_id": "B105", "issue_severity": "LOW", "issue_text": "Possible hardcoded password"}]}
GOSEC = {"tool": "gosec", "status": "ran", "issues": [{"file": "openapi3/loader.go", "line": "88", "rule_id": "G304", "severity": "HIGH", "details": "Potential file inclusion via variable"}]}


def test_lines_from_both_linters_and_the_prompt_section():
    assert static_lines(BANDIT) == ["app/auth.py:12 B105 low: Possible hardcoded password"]
    assert static_lines(GOSEC) == ["openapi3/loader.go:88 G304 high: Potential file inclusion via variable"]
    assert static_lines({"tool": "bandit", "status": "not_run"}) == [] and static_lines(None) == []
    sec = security_findings({"static_analysis": BANDIT, "static_analysis_package": GOSEC})
    assert sec.startswith("Static analysis findings. Aim negative tests at these first") and "changed files" in sec and "call sites" in sec
    assert security_findings({"static_analysis": {"status": "not_run"}}) is None, "no finding the harness did not have"


def test_high_severity_in_the_changed_code_is_a_security_finding_for_a_person():
    out = static_findings("pkg", {"static_analysis_package": GOSEC})
    assert len(out) == 1 and out[0]["class"] == "security" and out[0]["escalated"] and "G304" in out[0]["summary"]
    assert static_findings("pkg", {"static_analysis_package": BANDIT}) == [], "low severity stays in the prompt, not in the findings"
