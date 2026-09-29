"""The pipeline is under test too: what the repository's CI does with untrusted code, and whether its suite reaches what changed."""
from pathlib import Path

from harness.sources import ci
from harness.stages.triage import coverage_gap_findings

ROOT = Path(__file__).resolve().parents[2]


def _repo(tmp_path, workflow: str, name="ci.yml") -> Path:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / name).write_text(workflow)
    return tmp_path


def test_github_workflow_rules(tmp_path):
    repo = _repo(tmp_path, """
name: ci
on: [pull_request_target]
permissions: write-all
jobs:
  test:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
        with: { ref: "${{ github.event.pull_request.head.sha }}" }
      - run: curl -sSf https://example.invalid/install.sh | bash
      - name: run tests
        run: pytest
        env: { API_TOKEN: "${{ secrets.API_TOKEN }}" }
""")
    facts = ci.inspect(repo)
    assert facts["systems"] == ["github-actions"]
    rules = sorted(f["rule"] for f in facts["facts"])
    assert rules == ["P-01", "P-02", "P-03", "P-04", "P-05", "P-08"], rules
    assert all(f["suggested_change"] for f in facts["facts"])
    assert {f["severity"] for f in facts["facts"] if f["rule"] in ("P-01", "P-02", "P-04", "P-05", "P-08")} == {"security"}


def test_a_clean_pinned_workflow_yields_no_fact(tmp_path):
    repo = _repo(tmp_path, """
on: [pull_request]
permissions: { contents: read }
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@0ad4b8fadaa221de15dcec353f45205ec38ea70b # v4
      - run: pytest
""")
    assert ci.inspect(repo)["facts"] == []


def test_no_ci_is_a_fact(tmp_path):
    facts = ci.inspect(tmp_path)
    assert facts["files"] == [] and "no CI definition" in facts["note"]


def test_gitlab_and_tekton_rules(tmp_path):
    (tmp_path / ".gitlab-ci.yml").write_text("test:\n  image: python:latest\n  script:\n    - curl https://x/y.sh | sh\n    - pytest\n")
    (tmp_path / ".tekton").mkdir()
    (tmp_path / ".tekton" / "t.yaml").write_text("apiVersion: tekton.dev/v1\nkind: Task\nmetadata: {name: t}\nspec:\n  steps:\n    - name: s\n      image: alpine:3\n      securityContext: {privileged: true}\n")
    rules = sorted(f["rule"] for f in ci.inspect(tmp_path)["facts"])
    assert rules == ["P-04", "P-06", "P-07", "P-07"], rules


def test_the_harness_reads_its_own_pipeline():
    facts = ci.inspect(ROOT)
    assert "github-actions" in facts["systems"]
    assert any(f["rule"] == "P-03" for f in facts["facts"]), "our own actions are pinned by tag; the harness says so about itself"


def test_coverage_gap_findings_state_what_the_suite_misses():
    reach = {"call_sites_summary": {"reachable": "true"}}
    none = coverage_gap_findings("pkg", {**reach, "existing_suite": {"test_files": 12, "files_referencing_package": 0, "changed_symbols": 3, "files_reaching_changed_symbols": 0}})
    assert len(none) == 1 and none[0]["class"] == "coverage-gap" and "none of its 12 test files" in none[0]["summary"] and none[0]["suggested_change"]
    partial = coverage_gap_findings("pkg", {**reach, "existing_suite": {"test_files": 12, "files_referencing_package": 2, "changed_symbols": 3, "files_reaching_changed_symbols": 0}})
    assert len(partial) == 1 and "alters 3 symbol(s)" in partial[0]["summary"]
    assert coverage_gap_findings("pkg", {**reach, "existing_suite": {"test_files": 12, "files_referencing_package": 2, "changed_symbols": 3, "files_reaching_changed_symbols": 1}}) == []
    assert coverage_gap_findings("pkg", {**reach, "first_party": True, "existing_suite": {"test_files": 0}}) == []
