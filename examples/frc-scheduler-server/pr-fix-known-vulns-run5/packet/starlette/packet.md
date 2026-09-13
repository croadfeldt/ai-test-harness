# Review packet: starlette 0.41.3 -> 0.41.3

**In plain terms.** This change leaves starlette at 0.41.3, which has 7 known vulnerabilities the application is exposed to. The harness proved 1 of the 7 with a test that fails on the vulnerable version and passes on the fixed one; the other 6 are unproven and marked so. Accept the 6 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `76a3fa863e76`. Generated 2026-09-13T13:17:48+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
starlette at depth 2, change `unchanged`, reachable from first-party code: **true**
(8 production references). Risk score 80, budget full.
API diff: +0 / -0 / ~0, 0 breaking.
Advisories: 14 open at head, 0 on the replaced version.

## What was tested
18 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 10 pass on head, 0 flaky,
2 fix-pinning confirmed, 1368 lines of the package covered. Model: `qwen/qwen3.8-27b`.
Mutation: score 0.0 (0 of 12 sampled mutants killed, 319 sites on executed lines, seed 3701344546). Tests that killed nothing: ['test_cookie_parser_basic', 'test_gdsa_wqp7_x3pw_xc5r_exposure', 'test_gdsa_wqp7_x3pw_xc5r_fix_pinning', 'test_ghsa_7f5h_v6xp_fcq8_exposure', 'test_ghsa_7f5h_v6xp_fcq8_fix_pinning', 'test_ghsa_86qp_5c8j_p5mr_exposure', 'test_ghsa_86qp_5c8j_p5mr_fix_pinning', 'test_json_response_renders_json', 'test_response_status_and_body', 'test_simple_user_authenticated']. Target in the blueprint: 0.6.

## Findings
- **security** (0.9): starlette 0.41.3 has 14 open advisories at head; reachable=true. Route: Product Security. Evidence: `analyze/starlette/vulns.json`
- **defect** (0.4): starlette: a code path raised the same internal error on both versions during CVE test generation (CVE-2025-54121); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold. Evidence: `generate/starlette/manifest.agent.json`
- **defect** (0.4): starlette: a code path raised the same internal error on both versions during CVE test generation (CVE-2026-54283); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold. Evidence: `generate/starlette/manifest.agent.json`
- **defect** (0.8): starlette: a code path raised the same internal error on both versions during CVE test generation (CVE-2026-48817). Route: open issue with reproducer. Evidence: `generate/starlette/manifest.agent.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| test_GHSA_2c2j_9gv5_cj73_fix_pinning | cve | fail | fail | test-bug | regenerate or discard |
| test_GHSA_2c2j_9gv5_cj73_exposure | cve | fail | fail | test-bug | regenerate or discard |
| test_ghsa_7f5h_v6xp_fcq8_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_7f5h_v6xp_fcq8_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_86qp_5c8j_p5mr_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_86qp_5c8j_p5mr_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_x746_7m8f_x49c_fix_pinning | cve | fail | fail | defect | open issue; reproducer is the test; advisory stays under investigation |
| test_ghsa_x746_7m8f_x49c_exposure | cve | fail | fail | defect | open issue; reproducer is the test; advisory stays under investigation |
| test_gdsa_wqp7_x3pw_xc5r_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_gdsa_wqp7_x3pw_xc5r_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_jp82_jpqv_5vv3_fix_pinning | cve | fail | fail | test-bug | regenerate or discard |
| test_ghsa_jp82_jpqv_5vv3_exposure | cve | fail | fail | test-bug | regenerate or discard |
| test_ghsa_82w8_qh3p_5jfq_fix_pinning | cve | pass | fail | security | accept as CVE evidence; VEX status affected: the change introduces the exposure |
| test_ghsa_82w8_qh3p_5jfq_exposure | cve | pass | fail | security | accept as CVE evidence; VEX status affected: the change introduces the exposure |
| test_simple_user_authenticated | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_cookie_parser_basic | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_response_status_and_body | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_json_response_renders_json | unit | pass | pass | behavior-change | accept as characterization candidate |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2025-54121 | affected | open at head; reachable=true; fixed in ['0.47.2'] |
| CVE-2025-62727 | affected | open at head; reachable=true; fixed in ['0.49.1'] |
| CVE-2026-54283 | affected | exposure test(s) ['test_ghsa_82w8_qh3p_5jfq_exposure', 'test_ghsa_82w8_qh3p_5jfq_fix_pinning'] fail on pkg:pyp |
| CVE-2026-48710 | affected | open at head; reachable=true; fixed in ['1.0.1'] |
| CVE-2026-54282 | affected | open at head; reachable=true; fixed in ['1.3.0'] |
| CVE-2026-48818 | affected | open at head; reachable=true; fixed in ['1.1.0'] |
| CVE-2026-48817 | affected | open at head; reachable=true; fixed in ['1.1.0'] |

## Upgrade path
The advisories are fixed in starlette 1.3.1. The harness resolved an environment with it: also let direct dependents move: ['fastapi']. Packages that move: fastapi 0.115.5 -> 0.141.1, starlette 0.41.3 -> 1.3.1.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
None proposed: promotion needs a survived bump or a caught regression (section 8.3); the relevance engine is not in this slice.

## Artifacts
- tests as a patch against the overlay layout: `packet/starlette/tests.patch`
- verdicts and logs: `execute/starlette/results.json`, `execute/starlette/{new,new-rerun,old}/`
- facts: `analyze/starlette/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/starlette/manifest.json`, every prompt and response under `generate/starlette/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/starlette/statement.json` (after stage attest)
