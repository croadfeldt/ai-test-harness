# Review packet: python-jose 3.3.0 -> 3.4.0

**In plain terms.** This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness could not prove any of the 3 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `5f493a6b7288`. Generated 2026-09-14T00:08:59+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
python-jose at depth 1, change `bumped`, reachable from first-party code: **true**
(8 production references). Risk score 51, budget full.
API diff: +3 / -0 / ~0, 0 breaking.
Advisories: 0 open at head, 5 on the replaced version.

## What was tested
7 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 6 pass on head, 0 flaky,
0 fix-pinning confirmed, 543 lines of the package covered. Model: `qwen/qwen3.8-27b`.
Mutation: score 0.48 (12 of 25 sampled mutants killed, 118 sites on executed lines, seed 512944556). Tests that killed nothing: none. Target in the blueprint: 0.6.

## Findings
- **defect** (0.4): python-jose: a code path raised the same internal error on both versions during CVE test generation (CVE-2024-33664); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold. Evidence: `generate/python-jose/manifest.agent.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| tests.test_python_jose_unit | unknown | error | error | test-bug | regenerate or discard |
| test_PYSEC_2025_185_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_PYSEC_2025_185_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_6c5p_j8vq_pqhj_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_6c5p_j8vq_pqhj_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_cjwg_qfpm_7377_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_cjwg_qfpm_7377_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2024-33663 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2024-33664 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2024-29370 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet (section 8.3). Retirements: none proposed for this change; 16 generated and 47 application test(s) examined against 0 removed and 0 changed symbols.

## Artifacts
- tests as a patch against the overlay layout: `packet/python-jose/tests.patch`
- verdicts and logs: `execute/python-jose/results.json`, `execute/python-jose/{new,new-rerun,old}/`
- facts: `analyze/python-jose/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/python-jose/manifest.json`, every prompt and response under `generate/python-jose/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/python-jose/statement.json` (after stage attest)
