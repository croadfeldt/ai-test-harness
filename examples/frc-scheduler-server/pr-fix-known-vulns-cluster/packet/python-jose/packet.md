# Review packet: python-jose 3.3.0 -> 3.4.0

**In plain terms.** This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness proved 1 of the 3 with a test that fails on the vulnerable version and passes on the fixed one; the other 2 are unproven and marked so. Accept the 10 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `3d9fa72b859b`. Generated 2026-09-13T22:57:49+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
python-jose at depth 1, change `bumped`, reachable from first-party code: **true**
(8 production references). Risk score 51, budget full.
API diff: +3 / -0 / ~0, 0 breaking.
Advisories: 0 open at head, 5 on the replaced version.

## What was tested
14 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 14 pass on head, 0 flaky,
2 fix-pinning confirmed, 582 lines of the package covered. Model: `qwen/qwen3.8-27b`.
Mutation: score 0.4 (10 of 25 sampled mutants killed, 141 sites on executed lines, seed 512944556). Tests that killed nothing: ['test_utils_base64url_roundtrip']. Target in the blueprint: 0.6.

## Findings
- **redundant** (0.6): python-jose: test_jwt_decode_wrong_key_raises_jwt_error's 3 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 4. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jwt_decode_expired_raises_expired_signature_error's 5 mutant kill(s) are all among test_jwt_encode_decode_roundtrip_hmac's 6. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jwt_decode_audience_mismatch_raises_jwt_claims_error's 5 mutant kill(s) are all among test_jwt_encode_decode_roundtrip_hmac's 6. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jwt_get_unverified_header_returns_alg_and_typ's 3 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 4. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jwt_get_unverified_claims_returns_claims_without_verification's 3 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 4. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.6): python-jose: test_jws_sign_verify_roundtrip's 4 mutant kill(s) are all among test_jwt_decode_audience_mismatch_raises_jwt_claims_error's 5. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`
- **redundant** (0.5): python-jose: test_utils_base64url_roundtrip killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold. Evidence: `execute/python-jose/relevance.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| test_PYSEC_2025_185_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_PYSEC_2025_185_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_6c5p_j8vq_pqhj_fix_pinning | cve | fail | pass | behavior-change | accept as CVE evidence; VEX status fixed |
| test_ghsa_6c5p_j8vq_pqhj_exposure | cve | fail | pass | behavior-change | accept as CVE evidence; VEX status fixed |
| test_ghsa_cjwg_qfpm_7377_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_cjwg_qfpm_7377_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_jwt_encode_decode_roundtrip_hmac | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_decode_wrong_key_raises_jwt_error | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_decode_expired_raises_expired_signature_error | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_decode_audience_mismatch_raises_jwt_claims_error | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_get_unverified_header_returns_alg_and_typ | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jwt_get_unverified_claims_returns_claims_without_verification | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_jws_sign_verify_roundtrip | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_utils_base64url_roundtrip | unit | pass | pass | behavior-change | accept as characterization candidate |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2024-33663 | fixed | fix-pinning test(s) ['test_ghsa_6c5p_j8vq_pqhj_exposure', 'test_ghsa_6c5p_j8vq_pqhj_fix_pinning'] fail on pkg: |
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
| test_jwt_decode_wrong_key_raises_jwt_error | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_decode_wrong_key_raises_jwt_error's 3 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 4 |
| test_jwt_decode_expired_raises_expired_signature_error | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_decode_expired_raises_expired_signature_error's 5 mutant kill(s) are all among test_jwt_encode_decode |
| test_jwt_decode_audience_mismatch_raises_jwt_claims_error | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_decode_audience_mismatch_raises_jwt_claims_error's 5 mutant kill(s) are all among test_jwt_encode_dec |
| test_jwt_get_unverified_header_returns_alg_and_typ | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_get_unverified_header_returns_alg_and_typ's 3 mutant kill(s) are all among test_jws_sign_verify_round |
| test_jwt_get_unverified_claims_returns_claims_without_verification | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jwt_get_unverified_claims_returns_claims_without_verification's 3 mutant kill(s) are all among test_jws_s |
| test_jws_sign_verify_roundtrip | test_python_jose_unit.py | redundant | redundant-subsumed |  | low | test_jws_sign_verify_roundtrip's 4 mutant kill(s) are all among test_jwt_decode_audience_mismatch_raises_jwt_c |
| test_utils_base64url_roundtrip | test_python_jose_unit.py | redundant | redundant-no-kills |  | low | test_utils_base64url_roundtrip killed none of 25 sampled mutants in this run |

## Artifacts
- tests as a patch against the overlay layout: `packet/python-jose/tests.patch`
- verdicts and logs: `execute/python-jose/results.json`, `execute/python-jose/{new,new-rerun,old}/`
- facts: `analyze/python-jose/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/python-jose/manifest.json`, every prompt and response under `generate/python-jose/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/python-jose/statement.json` (after stage attest)
