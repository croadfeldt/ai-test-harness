# Review packet: pyasn1 0.6.4 -> 0.4.8

Run `76a3fa863e76`. Generated 2026-09-13T04:29:48+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
pyasn1 at depth 2, change `bumped`, reachable from first-party code: **unknown**
(0 production references). Risk score 90, budget full.
API diff: +90 / -142 / ~12, 146 breaking.
Advisories: 8 open at head, 0 on the replaced version.

## What was tested
16 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 12 pass on head, 0 flaky,
2 fix-pinning confirmed, 1423 lines of the package covered. Model: `qwen/qwen3.8-27b`.

## Findings
- **security** (0.95): pyasn1 downgraded 0.6.4 -> 0.4.8 into a version with 8 known advisories. Route: Product Security. Evidence: `analyze/pyasn1/facts.json`
- **security** (0.75): pyasn1 0.4.8 has 8 open advisories at head; reachable=unknown. Route: Product Security. Evidence: `analyze/pyasn1/vulns.json`
- **defect** (0.8): pyasn1: a code path raised the same internal error on both versions during CVE test generation (CVE-2026-59885). Route: open issue with reproducer. Evidence: `generate/pyasn1/manifest.agent.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| test_ghsa_jr27_m4p2_rc6r_fix_pinning | cve | pass | fail | security | accept as CVE evidence; VEX status affected: the change introduces the exposure |
| test_ghsa_jr27_m4p2_rc6r_exposure | cve | pass | fail | security | accept as CVE evidence; VEX status affected: the change introduces the exposure |
| test_ghsa_m4p7_r5rc_7g4j_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_m4p7_r5rc_7g4j_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_8ppf_4f7h_5ppj_fix_pinning | cve | fail | fail | defect | open issue; reproducer is the test; advisory stays under investigation |
| test_ghsa_8ppf_4f7h_5ppj_exposure | cve | fail | fail | defect | open issue; reproducer is the test; advisory stays under investigation |
| test_ghsa_hm4w_wwcw_mr6r_fix_pinning | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_ghsa_hm4w_wwcw_mr6r_exposure | cve | pass | pass | test-bug | discard as CVE evidence; keep as characterization only if reviewer wants it |
| test_printer_is_callable | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_debug_is_callable | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_setlogger_returns_none | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_hexdump_empty_bytes | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_pyasn1error_is_exception_subclass | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_value_constraint_error_is_pyasn1error_subclass | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_substrate_underrun_error_is_pyasn1error_subclass | unit | pass | pass | behavior-change | accept as characterization candidate |
| test_pyasn1unicode_error_is_unicode_error_subclass | unit | pass | pass | behavior-change | accept as characterization candidate |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2026-59885 | under_investigation | open at head; reachable=unknown; fixed in ['0.6.4'] |
| CVE-2026-59886 | under_investigation | open at head; reachable=unknown; fixed in ['0.6.4'] |
| CVE-2026-30922 | affected | exposure test(s) ['test_ghsa_jr27_m4p2_rc6r_exposure', 'test_ghsa_jr27_m4p2_rc6r_fix_pinning'] fail on pkg:pyp |
| CVE-2026-59884 | under_investigation | open at head; reachable=unknown; fixed in ['0.6.4'] |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
None proposed: promotion needs a survived bump or a caught regression (section 8.3); the relevance engine is not in this slice.

## Artifacts
- tests as a patch against the overlay layout: `packet/pyasn1/tests.patch`
- verdicts and logs: `execute/pyasn1/results.json`, `execute/pyasn1/{new,new-rerun,old}/`
- facts: `analyze/pyasn1/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/pyasn1/manifest.json`, every prompt and response under `generate/pyasn1/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/pyasn1/statement.json` (after stage attest)
