# Review packet: python-jose 3.3.0 -> 3.4.0

Run `76a3fa863e76`. Generated 2026-09-13T04:29:48+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
python-jose at depth 1, change `bumped`, reachable from first-party code: **true**
(8 production references). Risk score 51, budget full.
API diff: +3 / -0 / ~0, 0 breaking.
Advisories: 0 open at head, 5 on the replaced version.

## What was tested
11 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 9 pass on head, 0 flaky,
2 fix-pinning confirmed, 640 lines of the package covered. Model: `qwen/qwen3.8-27b`.

## Findings
- **defect** (0.4): python-jose: a code path raised the same internal error on both versions during CVE test generation (CVE-2024-33663); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold. Evidence: `generate/python-jose/manifest.agent.json`
- **defect** (0.8): python-jose: a code path raised the same internal error on both versions during CVE test generation (CVE-2024-29370). Route: open issue with reproducer. Evidence: `generate/python-jose/manifest.agent.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| test_pysec_2025_185_fix_pinning | cve | fail | fail | defect | open issue; reproducer is the test; advisory stays under investigation |
| test_pysec_2025_185_exposure | cve | fail | fail | defect | open issue; reproducer is the test; advisory stays under investigation |
| test_ghsa_6c5p_j8vq_pqhj_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_6c5p_j8vq_pqhj_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_cjwg_qfpm_7377_fix_pinning | cve | fail | pass | behavior-change | accept as CVE evidence; VEX status fixed |
| test_ghsa_cjwg_qfpm_7377_exposure | cve | fail | pass | behavior-change | accept as CVE evidence; VEX status fixed |
| test_jwt_encode_decode_roundtrip | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_decode_wrong_key_raises_jwterror | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_get_unverified_header | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_get_unverified_claims | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_decode_expired_raises_expiredsignatureerror | unit | pass | pass | behavior-change | accept as characterization candidate |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2024-33663 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2024-33664 | fixed | fix-pinning test(s) ['test_ghsa_cjwg_qfpm_7377_fix_pinning', 'test_ghsa_cjwg_qfpm_7377_exposure'] fail on pkg: |
| CVE-2024-29370 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
None proposed: promotion needs a survived bump or a caught regression (section 8.3); the relevance engine is not in this slice.

## Artifacts
- tests as a patch against the overlay layout: `packet/python-jose/tests.patch`
- verdicts and logs: `execute/python-jose/results.json`, `execute/python-jose/{new,new-rerun,old}/`
- facts: `analyze/python-jose/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/python-jose/manifest.json`, every prompt and response under `generate/python-jose/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/python-jose/statement.json` (after stage attest)
