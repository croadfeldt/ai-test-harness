# Review packet: python-jose 3.3.0 -> 3.4.0

**In plain terms.** This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness could not prove any of the 3 with a test; that is stated, not hidden. Accept the 8 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `333f5fa69d50`. Generated 2026-09-14T01:20:33+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
python-jose at depth 1, change `bumped`, reachable from first-party code: **true**
(8 production references). Risk score 51, budget full.
API diff: +3 / -0 / ~0, 0 breaking.
Advisories: 0 open at head, 5 on the replaced version.

## What was tested
14 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 14 pass on head, 0 flaky,
0 fix-pinning confirmed, 573 lines of the package covered. Model: `qwen/qwen3.8-27b`.
Mutation: score 0.44 (11 of 25 sampled mutants killed, 135 sites on executed lines, seed 512944556). Tests that killed nothing: ['test_ghsa_6c5p_j8vq_pqhj_exposure']. Target in the blueprint: 0.6.

## Findings
- **defect** (0.4): python-jose: a code path raised the same internal error on both versions during CVE test generation (CVE-2024-33663); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold. Evidence: `generate/python-jose/manifest.agent.json`
- **defect** (0.4): python-jose: a code path raised the same internal error on both versions during CVE test generation (CVE-2024-29370); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold. Evidence: `generate/python-jose/manifest.agent.json`
- **redundant** (0.6): python-jose: test_jwt_decode_wrong_key_raises_jwt_error's 5 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 6. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jwt_decode_expired_raises_expired_signature_error's 8 mutant kill(s) are all among test_jwt_encode_decode_roundtrip's 9. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jwt_get_unverified_header_returns_alg's 7 mutant kill(s) are all among test_jwt_decode_expired_raises_expired_signature_error's 8. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jwt_get_unverified_claims_returns_claims's 6 mutant kill(s) are all among test_jwt_decode_expired_raises_expired_signature_error's 8. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jws_sign_verify_roundtrip's 6 mutant kill(s) are all among test_jwt_decode_expired_raises_expired_signature_error's 8. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_utils_base64url_roundtrip's 1 mutant kill(s) are all among test_ghsa_cjwg_qfpm_7377_exposure's 5. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_utils_ensure_binary_coerces_str_to_bytes's 1 mutant kill(s) are all among test_ghsa_cjwg_qfpm_7377_exposure's 5. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| test_pysec_2025_185_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_pysec_2025_185_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_6c5p_j8vq_pqhj_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_6c5p_j8vq_pqhj_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_cjwg_qfpm_7377_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_cjwg_qfpm_7377_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_jwt_encode_decode_roundtrip | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_decode_wrong_key_raises_jwt_error | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_decode_expired_raises_expired_signature_error | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_get_unverified_header_returns_alg | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_get_unverified_claims_returns_claims | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jws_sign_verify_roundtrip | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_utils_base64url_roundtrip | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_utils_ensure_binary_coerces_str_to_bytes | unit | pass | pass | behavior-change | accept as characterization candidate |

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
Promotions: none yet; promotion needs a survived version change or a caught regression (section 8.3).

Retirement proposals, for this change. Advisory: a person approves, a retired test is kept and re-run once on the next change, nothing is deleted.

| test | file | class | reason | rewrite | priority | evidence |
|---|---|---|---|---|---|---|
| test_jwt_decode_wrong_key_raises_jwt_error | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_decode_wrong_key_raises_jwt_error's 5 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 6 |
| test_jwt_decode_expired_raises_expired_signature_error | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_decode_expired_raises_expired_signature_error's 8 mutant kill(s) are all among test_jwt_encode_decode |
| test_jwt_get_unverified_header_returns_alg | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_get_unverified_header_returns_alg's 7 mutant kill(s) are all among test_jwt_decode_expired_raises_exp |
| test_jwt_get_unverified_claims_returns_claims | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_get_unverified_claims_returns_claims's 6 mutant kill(s) are all among test_jwt_decode_expired_raises_ |
| test_jws_sign_verify_roundtrip | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jws_sign_verify_roundtrip's 6 mutant kill(s) are all among test_jwt_decode_expired_raises_expired_signatu |
| test_utils_base64url_roundtrip | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_utils_base64url_roundtrip's 1 mutant kill(s) are all among test_ghsa_cjwg_qfpm_7377_exposure's 5 |
| test_utils_ensure_binary_coerces_str_to_bytes | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_utils_ensure_binary_coerces_str_to_bytes's 1 mutant kill(s) are all among test_ghsa_cjwg_qfpm_7377_exposu |

## Artifacts
- tests as a patch against the overlay layout: `packet/python-jose/tests.patch`
- verdicts and logs: `execute/python-jose/results.json`, `execute/python-jose/{new,new-rerun,old}/`
- facts: `analyze/python-jose/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/python-jose/manifest.json`, every prompt and response under `generate/python-jose/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/python-jose/statement.json` (after stage attest)
