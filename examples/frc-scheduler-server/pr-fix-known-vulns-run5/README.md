# Run 76a3fa863e76: frc-scheduler-server 2ad04243861b..cfa8f4a3292b

What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.

## In plain terms

**pyasn1.** This change moves pyasn1 from 0.6.4 to 0.4.8, a version with 4 known vulnerabilities. That is a downgrade. The harness proved 1 of the 4 with a test that fails on the vulnerable version and passes on the fixed one; the other 3 are unproven and marked so. Accept the 10 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**python-jose.** This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness proved 1 of the 3 with a test that fails on the vulnerable version and passes on the fixed one; the other 2 are unproven and marked so. Accept the 7 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**starlette.** This change leaves starlette at 0.41.3, which has 7 known vulnerabilities the application is exposed to. The harness proved 1 of the 7 with a test that fails on the vulnerable version and passes on the fixed one; the other 6 are unproven and marked so. Accept the 6 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

## Who, what, why, where, when

|  |  |
|---|---|
| Who | The AI Test Harness 0.1.0 did the work without a person in the loop. A person decides the result; nothing in this run has been merged. |
| What | Tests for pyasn1 0.6.4 to 0.4.8, python-jose 3.3.0 to 3.4.0, starlette 0.41.3, chosen from a work list of 64 packages, 5 of which this change touched. Repository frc-scheduler-server, change 2ad04243861b..cfa8f4a3292b, mode diff. |
| Why | The risk score decides the budget; the two strongest reasons per package: pyasn1 (score 90, budget full): reachability unknown, treated as reachable; 8 known vulnerabilities for this version; 0 advisories before the change, 8 after. python-jose (score 51, budget full): reachable from first-party code; 159 source lines changed; 5 advisories before the change, 0 after. starlette (score 80, budget full): reachable from first-party code; 14 known vulnerabilities for this version. |
| Where | Every test ran in a sealed sandbox (podman, network none, image docker.io/library/python:3.12-slim); the model was qwen/qwen3.8-27b in agent mode; the run's own files are in this folder. |
| When | Started 2026-09-12 01:41:41 UTC. The last stage to write was self-verification at 2026-09-13 16:25:42 UTC. |

## What the harness did, step by step

Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join.

| Stage | When | What it did |
|---|---|---|
| 0 Self-verification | 2026-09-13 16:25:42 UTC | Ran 19 checks from the failure register on its own code before touching the target; all passed. Sandbox probe skipped, model probe skipped. |
| 1 Intake | 2026-09-12 01:42:29 UTC | Resolved the dependency graph at head (63 packages) and at base (63), looked every version up in OSV (4 with advisories at head), and wrote a work list of 64 packages, 5 of them changed by this change. |
| 2 Analysis | 2026-09-13 02:49:36 UTC | For each package, diffed the two versions' public API and source, found the application's call sites and read the advisories; risk score and budget: pyasn1 90 (full), python-jose 51 (full), starlette 80 (full). |
| 3 Generation | 2026-09-13 04:26:14 UTC | pyasn1: asked the model (qwen/qwen3.8-27b) for tests in 47 calls; kept 16 tests in 5 file(s), cut 2 that did not hold up on the baseline run, discarded 0 whole attempt(s). python-jose: asked the model (qwen/qwen3.8-27b) for tests in 34 calls; kept 11 tests in 4 file(s), cut 5 that did not hold up on the baseline run, discarded 0 whole attempt(s). starlette: asked the model (qwen/qwen3.8-27b) for tests in 85 calls; kept 18 tests in 8 file(s), cut 6 that did not hold up on the baseline run, discarded 0 whole attempt(s). |
| 4 Validation execution | 2026-09-13 04:29:47 UTC | pyasn1: ran 16 tests on head, again for flakes, and on the other version (new, new-rerun, old); 12 pass on head, 0 flaky, 2 proved a fix; 1423 lines of the package covered. Mutation: 5 of 12 sampled mutants killed, score 0.417. python-jose: ran 11 tests on head, again for flakes, and on the other version (new, new-rerun, old); 9 pass on head, 0 flaky, 2 proved a fix; 640 lines of the package covered. Mutation: 5 of 12 sampled mutants killed, score 0.417. starlette: ran 18 tests on head, again for flakes, and on the other version (new, new-rerun, old); 10 pass on head, 0 flaky, 2 proved a fix; 1368 lines of the package covered. Mutation: 0 of 12 sampled mutants killed, score 0.0. |
| 5 Triage | 2026-09-13 16:25:41 UTC | pyasn1: classified every verdict; 10 tests to accept, 6 to discard or regenerate, 11 finding(s), 8 escalated to a person. python-jose: classified every verdict; 7 tests to accept, 4 to discard or regenerate, 6 finding(s), 5 escalated to a person. starlette: classified every verdict; 6 tests to accept, 12 to discard or regenerate, 9 finding(s), 6 escalated to a person. |
| 6 Review packet | 2026-09-13 16:25:41 UTC | Wrote the review packet per package: the verdict in plain terms, the tests as a patch, the findings, the draft VEX statements, and the pull request text. |
| Attestation | 2026-09-13 16:25:41 UTC | pyasn1: signed the in-toto statement over the patch and the records (PASSED) and sealed the UDLM records. python-jose: signed the in-toto statement over the patch and the records (PASSED) and sealed the UDLM records. starlette: signed the in-toto statement over the patch and the records (PASSED) and sealed the UDLM records. |
| Assessment | 2026-09-13 16:25:42 UTC | Measured the run against the blueprint's goals: 9 met, 0 not met, 0 not applicable, 1 other. |

## Decisions the harness made

- pyasn1: cut 2 generated test(s) before execution: 2 fails on baseline after repair.
- pyasn1: triage decided per test: 2 accept as CVE evidence; VEX status affected: the change introduces the exposure; 4 discard as CVE evidence; keep as characterization only if reviewer wants it; 2 open issue; reproducer is the test; advisory stays under investigation; 8 accept as characterization candidate.
- pyasn1: finding, security at confidence 0.95: pyasn1 downgraded 0.6.4 -> 0.4.8 into a version with 8 known advisories. Route: Product Security.
- pyasn1: finding, security at confidence 0.75: pyasn1 0.4.8 has 8 open advisories at head; reachable=unknown. Route: Product Security.
- pyasn1: finding, defect at confidence 0.8: pyasn1: a code path raised the same internal error on both versions during CVE test generation (CVE-2026-59885). Route: open issue with reproducer.
- pyasn1: finding, redundant at confidence 0.5: pyasn1: test_printer_is_callable killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- pyasn1: finding, redundant at confidence 0.5: pyasn1: test_debug_is_callable killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- pyasn1: finding, redundant at confidence 0.5: pyasn1: test_setlogger_returns_none killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- pyasn1: finding, redundant at confidence 0.5: pyasn1: test_hexdump_empty_bytes killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- pyasn1: finding, redundant at confidence 0.5: pyasn1: test_pyasn1error_is_exception_subclass killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- pyasn1: finding, redundant at confidence 0.5: pyasn1: test_value_constraint_error_is_pyasn1error_subclass killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- pyasn1: finding, redundant at confidence 0.5: pyasn1: test_substrate_underrun_error_is_pyasn1error_subclass killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- pyasn1: finding, redundant at confidence 0.5: pyasn1: test_pyasn1unicode_error_is_unicode_error_subclass killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- pyasn1: mutation score 0.417 is below the blueprint's 0.6; the packet says so, and the reviewer sees which tests killed nothing.
- pyasn1: draft VEX per advisory: CVE-2026-30922 affected, CVE-2026-59884 under_investigation, CVE-2026-59885 under_investigation, CVE-2026-59886 under_investigation.
- python-jose: cut 5 generated test(s) before execution: 5 fails on baseline after repair.
- python-jose: triage decided per test: 2 open issue; reproducer is the test; advisory stays under investigation; 2 discard as CVE evidence; keep as characterization only if reviewer wants it; 2 accept as CVE evidence; VEX status fixed; 5 accept as characterization candidate.
- python-jose: finding, defect at confidence 0.4: python-jose: a code path raised the same internal error on both versions during CVE test generation (CVE-2024-33663); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold.
- python-jose: finding, defect at confidence 0.8: python-jose: a code path raised the same internal error on both versions during CVE test generation (CVE-2024-29370). Route: open issue with reproducer.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_decode_wrong_key_raises_jwterror's 2 mutant kill(s) are all among test_jwt_decode_expired_raises_expiredsignatureerror's 4. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_get_unverified_header's 2 mutant kill(s) are all among test_jwt_decode_expired_raises_expiredsignatureerror's 4. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_get_unverified_claims's 2 mutant kill(s) are all among test_jwt_decode_expired_raises_expiredsignatureerror's 4. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_decode_expired_raises_expiredsignatureerror's 4 mutant kill(s) are all among test_jwt_encode_decode_roundtrip's 5. Route: escalate: below confidence threshold.
- python-jose: mutation score 0.417 is below the blueprint's 0.6; the packet says so, and the reviewer sees which tests killed nothing.
- python-jose: draft VEX per advisory: CVE-2024-29370 under_investigation, CVE-2024-33663 under_investigation, CVE-2024-33664 fixed.
- starlette: cut 6 generated test(s) before execution: 6 fails on baseline after repair.
- starlette: triage decided per test: 4 regenerate or discard; 6 discard as CVE evidence; keep as characterization only if reviewer wants it; 2 open issue; reproducer is the test; advisory stays under investigation; 2 accept as CVE evidence; VEX status affected: the change introduces the exposure; 4 accept as characterization candidate.
- starlette: finding, security at confidence 0.9: starlette 0.41.3 has 14 open advisories at head; reachable=true. Route: Product Security.
- starlette: finding, defect at confidence 0.4: starlette: a code path raised the same internal error on both versions during CVE test generation (CVE-2025-54121); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold.
- starlette: finding, defect at confidence 0.4: starlette: a code path raised the same internal error on both versions during CVE test generation (CVE-2026-54283); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold.
- starlette: finding, defect at confidence 0.8: starlette: a code path raised the same internal error on both versions during CVE test generation (CVE-2026-48817). Route: open issue with reproducer.
- starlette: finding, obsolete at confidence 0.85: starlette: test_ghsa_jp82_jpqv_5vv3_exposure references starlette.requests.Request, which the upgrade to 1.3.1 changes the required parameters of. Route: propose retirement.
- starlette: finding, redundant at confidence 0.5: starlette: test_simple_user_authenticated killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- starlette: finding, redundant at confidence 0.5: starlette: test_cookie_parser_basic killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- starlette: finding, redundant at confidence 0.5: starlette: test_response_status_and_body killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- starlette: finding, redundant at confidence 0.5: starlette: test_json_response_renders_json killed none of 12 sampled mutants in this run. Route: escalate: below confidence threshold.
- starlette: mutation score 0.0 is below the blueprint's 0.6; the packet says so, and the reviewer sees which tests killed nothing.
- starlette: draft VEX per advisory: CVE-2025-54121 affected, CVE-2025-62727 affected, CVE-2026-48710 affected, CVE-2026-48817 affected, CVE-2026-48818 affected, CVE-2026-54282 affected, CVE-2026-54283 affected.

## Actions it took

- pyasn1: wrote a review packet with 10 accepted test(s) as a patch, ready for a pull request.
- pyasn1: drafted VEX statements for Product Security.
- pyasn1: signed the test-result statement (PASSED).
- pyasn1: no pull request was opened in this run; the packet holds what one would carry.
- python-jose: wrote a review packet with 7 accepted test(s) as a patch, ready for a pull request.
- python-jose: drafted VEX statements for Product Security.
- python-jose: signed the test-result statement (PASSED).
- python-jose: no pull request was opened in this run; the packet holds what one would carry.
- starlette: wrote a review packet with 6 accepted test(s) as a patch, ready for a pull request.
- starlette: drafted VEX statements for Product Security.
- starlette: signed the test-result statement (PASSED).
- starlette: no pull request was opened in this run; the packet holds what one would carry.

## Actions it did not take, by design

- It did not merge anything. Tests reach a repository only through a pull request that a person merges.
- It did not change production code and did not propose a fix. Fixes come from a separate fix pipeline; this harness only tests.
- It did not publish a VEX statement. The drafts are proposals for Product Security.
- It did not delete any existing test. Retirements are proposed with evidence for a person to act on.

## The records, in plain terms

60 UDLM records, each a fact from this run in the estate's own language. Intent is what the harness proposed, Requested is what a person was asked to decide, Realized is what landed and who made it so. All are sealed with a content hash.

| Record | State | What it says | Written |
|---|---|---|---|
| Job | Requested | The harness was asked to run on frc-scheduler-server from 2ad04243861b to cfa8f4a3292b in diff mode. | 2026-09-12 01:41:41 UTC |
| Job | Realized | The run finished; its outputs are the records this statement seals. | 2026-09-13 02:40:04 UTC |
| SoftwarePackage | Discovered | pyasn1 0.4.8 (pypi) is the version this change installs. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_debug_is_callable` is a unit test in `tests/test_pyasn1_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_ghsa_jr27_m4p2_rc6r_exposure` is an exposure test for CVE-2026-30922 in `tests/test_pyasn1_cve_cve_2026_30922.py`; it failed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_ghsa_jr27_m4p2_rc6r_fix_pinning` is a fix-pinning test for CVE-2026-30922 in `tests/test_pyasn1_cve_cve_2026_30922.py`; it failed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_hexdump_empty_bytes` is a unit test in `tests/test_pyasn1_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_printer_is_callable` is a unit test in `tests/test_pyasn1_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_pyasn1error_is_exception_subclass` is a unit test in `tests/test_pyasn1_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_pyasn1unicode_error_is_unicode_error_subclass` is a unit test in `tests/test_pyasn1_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_setlogger_returns_none` is a unit test in `tests/test_pyasn1_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_substrate_underrun_error_is_pyasn1error_subclass` is a unit test in `tests/test_pyasn1_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| TestEvidence | Intent | `test_value_constraint_error_is_pyasn1error_subclass` is a unit test in `tests/test_pyasn1_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 02:40:04 UTC |
| VexStatement | Intent | Draft: CVE-2026-59885 is `under_investigation` in this package. open at head; reachable=unknown; fixed in ['0.6.4'] | 2026-09-13 02:40:04 UTC |
| VexStatement | Intent | Draft: CVE-2026-59886 is `under_investigation` in this package. open at head; reachable=unknown; fixed in ['0.6.4'] | 2026-09-13 02:40:04 UTC |
| VexStatement | Intent | Draft: CVE-2026-30922 is `affected` in this package. exposure test(s) ['test_ghsa_jr27_m4p2_rc6r_fix_pinning', 'test_ghsa_jr27_m4p2_rc6r_exposure'] fail on pkg:pypi/pyasn1@0.4.8 and pass on pkg:pypi/pyasn1@0.6.4: the change introduces this exposure | 2026-09-13 02:40:04 UTC |
| VexStatement | Intent | Draft: CVE-2026-59884 is `under_investigation` in this package. open at head; reachable=unknown; fixed in ['0.6.4'] | 2026-09-13 02:40:04 UTC |
| Vulnerability | Discovered | CVE-2026-59885 is a known vulnerability affecting <0.6.4. Also known as GHSA-8ppf-4f7h-5ppj, PYSEC-2026-3456. | 2026-09-13 02:40:04 UTC |
| Vulnerability | Discovered | CVE-2026-59886 is a known vulnerability affecting <0.6.4. Also known as GHSA-hm4w-wwcw-mr6r, PYSEC-2026-3457. | 2026-09-13 02:40:04 UTC |
| Vulnerability | Discovered | CVE-2026-30922 is a known vulnerability affecting <0.6.3. Also known as GHSA-jr27-m4p2-rc6r, PYSEC-2026-2263. | 2026-09-13 02:40:04 UTC |
| Vulnerability | Discovered | CVE-2026-59884 is a known vulnerability affecting <0.6.4. Also known as GHSA-m4p7-r5rc-7g4j, PYSEC-2026-3455. | 2026-09-13 02:40:04 UTC |
| Job | Requested | The harness was asked to run on frc-scheduler-server from 2ad04243861b to cfa8f4a3292b in diff mode. | 2026-09-12 01:41:41 UTC |
| Job | Realized | The run finished; its outputs are the records this statement seals. | 2026-09-12 06:51:29 UTC |
| SoftwarePackage | Discovered | python-jose 3.4.0 (pypi) is the version this change installs. | 2026-09-12 06:51:29 UTC |
| TestEvidence | Intent | `test_ghsa_cjwg_qfpm_7377_exposure` is an exposure test for CVE-2024-33664 in `tests/test_python_jose_cve_cve_2024_33664.py`; it passed on head in the sealed sandbox. | 2026-09-12 06:51:29 UTC |
| TestEvidence | Intent | `test_ghsa_cjwg_qfpm_7377_fix_pinning` is a fix-pinning test for CVE-2024-33664 in `tests/test_python_jose_cve_cve_2024_33664.py`; it passed on head in the sealed sandbox. | 2026-09-12 06:51:29 UTC |
| TestEvidence | Intent | `test_jwt_decode_expired_raises_expiredsignatureerror` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-12 06:51:29 UTC |
| TestEvidence | Intent | `test_jwt_decode_wrong_key_raises_jwterror` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-12 06:51:29 UTC |
| TestEvidence | Intent | `test_jwt_encode_decode_roundtrip` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-12 06:51:29 UTC |
| TestEvidence | Intent | `test_jwt_get_unverified_claims` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-12 06:51:29 UTC |
| TestEvidence | Intent | `test_jwt_get_unverified_header` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-12 06:51:29 UTC |
| VexStatement | Intent | Draft: CVE-2024-33663 is `under_investigation` in this package. bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet | 2026-09-12 06:51:29 UTC |
| VexStatement | Intent | Draft: CVE-2024-33664 is `fixed` in this package. fix-pinning test(s) ['test_ghsa_cjwg_qfpm_7377_exposure', 'test_ghsa_cjwg_qfpm_7377_fix_pinning'] fail on pkg:pypi/python-jose@3.3.0 and pass on pkg:pypi/python-jose@3.4.0 | 2026-09-12 06:51:29 UTC |
| VexStatement | Intent | Draft: CVE-2024-29370 is `under_investigation` in this package. bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet | 2026-09-12 06:51:29 UTC |
| Vulnerability | Discovered | CVE-2024-33663 is a known vulnerability affecting <3.4.0. Also known as GHSA-6c5p-j8vq-pqhj, PYSEC-2024-232. | 2026-09-12 06:51:29 UTC |
| Vulnerability | Discovered | CVE-2024-33664 is a known vulnerability affecting <3.4.0. Also known as GHSA-cjwg-qfpm-7377, PYSEC-2024-233. | 2026-09-12 06:51:29 UTC |
| Vulnerability | Discovered | CVE-2024-29370 is a known vulnerability affecting versions the advisory does not pin. Also known as PYSEC-2025-185. | 2026-09-12 06:51:29 UTC |
| Job | Requested | The harness was asked to run on frc-scheduler-server from 2ad04243861b to cfa8f4a3292b in diff mode. | 2026-09-12 01:41:41 UTC |
| Job | Realized | The run finished; its outputs are the records this statement seals. | 2026-09-13 04:29:47 UTC |
| SoftwarePackage | Discovered | starlette 0.41.3 (pypi) is the version this change installs. | 2026-09-13 04:29:47 UTC |
| TestEvidence | Intent | `test_cookie_parser_basic` is a unit test in `tests/test_starlette_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 04:29:47 UTC |
| TestEvidence | Intent | `test_ghsa_82w8_qh3p_5jfq_exposure` is an exposure test for CVE-2026-54283 in `tests/test_starlette_cve_cve_2026_54283.py`; it failed on head in the sealed sandbox. | 2026-09-13 04:29:47 UTC |
| TestEvidence | Intent | `test_ghsa_82w8_qh3p_5jfq_fix_pinning` is a fix-pinning test for CVE-2026-54283 in `tests/test_starlette_cve_cve_2026_54283.py`; it failed on head in the sealed sandbox. | 2026-09-13 04:29:47 UTC |
| TestEvidence | Intent | `test_json_response_renders_json` is a unit test in `tests/test_starlette_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 04:29:47 UTC |
| TestEvidence | Intent | `test_response_status_and_body` is a unit test in `tests/test_starlette_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 04:29:47 UTC |
| TestEvidence | Intent | `test_simple_user_authenticated` is a unit test in `tests/test_starlette_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 04:29:47 UTC |
| VexStatement | Intent | Draft: CVE-2025-54121 is `affected` in this package. open at head; reachable=true; fixed in ['0.47.2'] | 2026-09-13 04:29:47 UTC |
| VexStatement | Intent | Draft: CVE-2025-62727 is `affected` in this package. open at head; reachable=true; fixed in ['0.49.1'] | 2026-09-13 04:29:47 UTC |
| VexStatement | Intent | Draft: CVE-2026-54283 is `affected` in this package. exposure test(s) ['test_ghsa_82w8_qh3p_5jfq_exposure', 'test_ghsa_82w8_qh3p_5jfq_fix_pinning'] fail on pkg:pypi/starlette@0.41.3 and pass on pkg:pypi/starlette@0.41.3: the change introduces this exposure | 2026-09-13 04:29:47 UTC |
| VexStatement | Intent | Draft: CVE-2026-48710 is `affected` in this package. open at head; reachable=true; fixed in ['1.0.1'] | 2026-09-13 04:29:47 UTC |
| VexStatement | Intent | Draft: CVE-2026-54282 is `affected` in this package. open at head; reachable=true; fixed in ['1.3.0'] | 2026-09-13 04:29:47 UTC |
| VexStatement | Intent | Draft: CVE-2026-48818 is `affected` in this package. open at head; reachable=true; fixed in ['1.1.0'] | 2026-09-13 04:29:47 UTC |
| VexStatement | Intent | Draft: CVE-2026-48817 is `affected` in this package. open at head; reachable=true; fixed in ['1.1.0'] | 2026-09-13 04:29:47 UTC |
| Vulnerability | Discovered | CVE-2025-54121 is a known vulnerability affecting <0.47.2. Also known as GHSA-2c2j-9gv5-cj73, PYSEC-2026-1941. | 2026-09-13 04:29:47 UTC |
| Vulnerability | Discovered | CVE-2025-62727 is a known vulnerability affecting <0.49.1. Also known as GHSA-7f5h-v6xp-fcq8, PYSEC-2026-1942. | 2026-09-13 04:29:47 UTC |
| Vulnerability | Discovered | CVE-2026-54283 is a known vulnerability affecting <1.3.1. Also known as GHSA-82w8-qh3p-5jfq, PYSEC-2026-249. | 2026-09-13 04:29:47 UTC |
| Vulnerability | Discovered | CVE-2026-48710 is a known vulnerability affecting <1.0.1. Also known as GHSA-86qp-5c8j-p5mr, PYSEC-2026-161. | 2026-09-13 04:29:47 UTC |
| Vulnerability | Discovered | CVE-2026-54282 is a known vulnerability affecting <1.3.0. Also known as GHSA-jp82-jpqv-5vv3, PYSEC-2026-248. | 2026-09-13 04:29:47 UTC |
| Vulnerability | Discovered | CVE-2026-48818 is a known vulnerability affecting <1.1.0. Also known as GHSA-wqp7-x3pw-xc5r, PYSEC-2026-2281. | 2026-09-13 04:29:47 UTC |
| Vulnerability | Discovered | CVE-2026-48817 is a known vulnerability affecting <1.1.0. Also known as GHSA-x746-7m8f-x49c, PYSEC-2026-2280. | 2026-09-13 04:29:47 UTC |

## What is in this folder, and who it is for

Every file exists for a reader or a tool named here. The plain-English files come first; the machine files stay because they are the proof and the replay.

**Everyone**

- `README.md`: The story of this run: who, what, why, where, when, the outcome, the decisions and the actions.
- `assess/assess.md`: The run against the blueprint's eleven goals, each with the measurement and the file it came from.

**Reviewers (the developer or team that owns the change)**

- `intake/worklist.json`: The work list: every package at base and head, what changed, what is reachable, what carries advisories.
- `analyze/pyasn1/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/python-jose/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/starlette/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/pyasn1/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `analyze/python-jose/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `generate/pyasn1/tests/`: The candidate test files as generated, before any decision.
- `generate/python-jose/tests/`: The candidate test files as generated, before any decision.
- `generate/starlette/tests/`: The candidate test files as generated, before any decision.
- `execute/pyasn1/results.json`: The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged.
- `execute/python-jose/results.json`: The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged.
- `execute/starlette/results.json`: The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged.
- `execute/pyasn1/mutation/mutation.json`: How strong the accepted tests are: which mutants of the package's source they killed, and the score.
- `execute/python-jose/mutation/mutation.json`: How strong the accepted tests are: which mutants of the package's source they killed, and the score.
- `execute/starlette/mutation/mutation.json`: How strong the accepted tests are: which mutants of the package's source they killed, and the score.
- `execute/pyasn1/relevance.json`: Which existing tests this change makes obsolete or redundant, proposed with evidence; nothing is deleted.
- `execute/python-jose/relevance.json`: Which existing tests this change makes obsolete or redundant, proposed with evidence; nothing is deleted.
- `execute/starlette/relevance.json`: Which existing tests this change makes obsolete or redundant, proposed with evidence; nothing is deleted.
- `triage/pyasn1/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/python-jose/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/starlette/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `packet/pyasn1/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/python-jose/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/starlette/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/pyasn1/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/python-jose/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/starlette/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/pyasn1/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/python-jose/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/starlette/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.

**Product Security**

- `intake/vulns.json`: Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports.
- `analyze/pyasn1/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/python-jose/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/starlette/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/starlette/fixed-candidate.json`: When the change left a vulnerable version in place: the environment the harness resolved with the fixed version, and what had to move.
- `packet/pyasn1/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/python-jose/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/starlette/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.

**Supply Chain Security and auditors**

- `run.json`: What was run, with which tool versions, on which repository by name.
- `selfcheck/selfcheck.json`: Stage 0: every failure-register check and the sandbox and model probes, before any evidence was produced.
- `intake/sbom.new.cdx.json`: The software bill of materials at head, CycloneDX.
- `generate/pyasn1/model-calls/`: Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said.
- `generate/python-jose/model-calls/`: Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said.
- `generate/starlette/model-calls/`: Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said.
- `attest/pyasn1/MANIFEST.json`: The provenance record per accepted test: model, prompt and response digests, sandbox image digest, verdicts.
- `attest/python-jose/MANIFEST.json`: The provenance record per accepted test: model, prompt and response digests, sandbox image digest, verdicts.
- `attest/starlette/MANIFEST.json`: The provenance record per accepted test: model, prompt and response digests, sandbox image digest, verdicts.
- `attest/pyasn1/statement.json`: The in-toto test-result statement; its subjects are the patch, the record and each evidence record's head.
- `attest/python-jose/statement.json`: The in-toto test-result statement; its subjects are the patch, the record and each evidence record's head.
- `attest/starlette/statement.json`: The in-toto test-result statement; its subjects are the patch, the record and each evidence record's head.
- `attest/pyasn1/statement.dsse.json`: The statement signed as a DSSE envelope.
- `attest/python-jose/statement.dsse.json`: The statement signed as a DSSE envelope.
- `attest/starlette/statement.dsse.json`: The statement signed as a DSSE envelope.
- `attest/pyasn1/signer.pub.pem`: The public key that verifies the envelope.
- `attest/python-jose/signer.pub.pem`: The public key that verifies the envelope.
- `attest/starlette/signer.pub.pem`: The public key that verifies the envelope.
- `attest/pyasn1/attest.json`: Which key signed, whether it verified locally, and what the run could not back.
- `attest/python-jose/attest.json`: Which key signed, whether it verified locally, and what the run could not back.
- `attest/starlette/attest.json`: Which key signed, whether it verified locally, and what the run could not back.
- `attest/pyasn1/udlm/`: The same facts as sealed UDLM records: the vulnerability, the package, the run, each accepted test, the draft VEX.
- `attest/python-jose/udlm/`: The same facts as sealed UDLM records: the vulnerability, the package, the run, each accepted test, the draft VEX.
- `attest/starlette/udlm/`: The same facts as sealed UDLM records: the vulnerability, the package, the run, each accepted test, the draft VEX.

**The person who ran the harness**

- `analyze/pyasn1/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/python-jose/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/pyasn1/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/python-jose/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/starlette/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `generate/pyasn1/manifest.json`: What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests.
- `generate/python-jose/manifest.json`: What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests.
- `generate/starlette/manifest.json`: What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests.
- `generate/pyasn1/manifest.agent.json`: The tool-using agent's traces: every tool call per advisory, and the budget it had.
- `generate/python-jose/manifest.agent.json`: The tool-using agent's traces: every tool call per advisory, and the budget it had.
- `generate/starlette/manifest.agent.json`: The tool-using agent's traces: every tool call per advisory, and the budget it had.

**Tools (kept for replay and proof; not meant to be read)**

- `run-index.json`: What this run holds: stages, packages, headline numbers, and where every file is; the renderers read it.
- `intake/graph.new.json`: The dependency graph at head as the ecosystem's own resolver produced it.
- `intake/graph.old.json`: The dependency graph at base.
- `analyze/pyasn1/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/python-jose/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/starlette/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/pyasn1/api.old.json`: The public API surface at base.
- `analyze/python-jose/api.old.json`: The public API surface at base.
- `analyze/pyasn1/call-sites.json`: Every place the application references this package.
- `analyze/python-jose/call-sites.json`: Every place the application references this package.
- `analyze/starlette/call-sites.json`: Every place the application references this package.
- `generate/pyasn1/scratch/`: Every attempt that ran in the sandbox during generation, with its output; not committed.
- `generate/python-jose/scratch/`: Every attempt that ran in the sandbox during generation, with its output; not committed.
- `generate/starlette/scratch/`: Every attempt that ran in the sandbox during generation, with its output; not committed.
- `execute/pyasn1/new/`: The sealed run on head: the run script, the junit report, coverage, logs.
- `execute/python-jose/new/`: The sealed run on head: the run script, the junit report, coverage, logs.
- `execute/starlette/new/`: The sealed run on head: the run script, the junit report, coverage, logs.
- `execute/pyasn1/new-rerun/`: The second run on head, to catch flakes.
- `execute/python-jose/new-rerun/`: The second run on head, to catch flakes.
- `execute/starlette/new-rerun/`: The second run on head, to catch flakes.
- `execute/pyasn1/old/`: The run on the base version, for the differential.
- `execute/python-jose/old/`: The run on the base version, for the differential.
- `execute/starlette/fixed-candidate/`: The run on the resolved fixed version, for the differential when the change did not move the package.
- `execute/pyasn1/mutation/mutants/`: Each sampled mutant: the mutated file and its sealed run.
- `execute/python-jose/mutation/mutants/`: Each sampled mutant: the mutated file and its sealed run.
- `execute/starlette/mutation/mutants/`: Each sampled mutant: the mutated file and its sealed run.
- `packet/pyasn1/packet.json`: The packet's facts in structured form.
- `packet/python-jose/packet.json`: The packet's facts in structured form.
- `packet/starlette/packet.json`: The packet's facts in structured form.
- `assess/assess.json`: The assessment in structured form.
