# Run 3d9fa72b859b: source 2ad04243861b..cfa8f4a3292b

What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.

## In plain terms

**ecdsa.** This change leaves ecdsa at 0.19.2, which has 1 known vulnerability the application is exposed to. The harness could not prove any of the 1 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**pdfminer-six.** This change leaves pdfminer-six at 20231228, which has 2 known vulnerabilities the application is exposed to. The harness could not prove any of the 2 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**pillow.** This change updates pillow from 11.0.0 to 12.3.0, which closes 17 known vulnerabilities. The harness could not prove any of the 17 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**pyasn1.** This change moves pyasn1 from 0.6.4 to 0.4.8, a version with 4 known vulnerabilities. That is a downgrade. The harness could not prove any of the 4 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**python-jose.** This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness proved 1 of the 3 with a test that fails on the vulnerable version and passes on the fixed one; the other 2 are unproven and marked so. Accept the 10 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**python-multipart.** This change updates python-multipart from 0.0.12 to 0.0.31, which closes 8 known vulnerabilities. The harness could not prove any of the 8 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**starlette.** This change leaves starlette at 0.41.3, which has 7 known vulnerabilities the application is exposed to. The harness could not prove any of the 7 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

**weasyprint.** This change updates weasyprint from 63.1 to 70.0, which closes 3 known vulnerabilities. The harness could not prove any of the 3 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

## Who, what, why, where, when

|  |  |
|---|---|
| Who | The AI Test Harness 0.1.0 did the work without a person in the loop. A person decides the result; nothing in this run has been merged. |
| What | Tests for ecdsa 0.19.2, pdfminer-six 20231228, pillow 11.0.0 to 12.3.0, pyasn1 0.6.4 to 0.4.8, python-jose 3.3.0 to 3.4.0, python-multipart 0.0.12 to 0.0.31, starlette 0.41.3, weasyprint 63.1 to 70.0, chosen from a work list of 64 packages, 5 of which this change touched. Repository source, change 2ad04243861b..cfa8f4a3292b, mode diff. |
| Why | The risk score decides the budget; the two strongest reasons per package: ecdsa (score 65, budget full): reachability unknown, treated as reachable; 2 known vulnerabilities for this version. pdfminer-six (score 65, budget full): reachability unknown, treated as reachable; 4 known vulnerabilities for this version. pillow (score 55, budget full): reachability unknown, treated as reachable; 12 breaking API change(s); 34 advisories before the change, 0 after. pyasn1 (score 90, budget full): reachability unknown, treated as reachable; 8 known vulnerabilities for this version; 0 advisories before the change, 8 after. python-jose (score 51, budget full): reachable from first-party code; 159 source lines changed; 5 advisories before the change, 0 after. python-multipart (score 55, budget full): reachability unknown, treated as reachable; 82 breaking API change(s); 16 advisories before the change, 0 after. starlette (score 80, budget full): reachable from first-party code; 14 known vulnerabilities for this version. weasyprint (score 70, budget full): reachable from first-party code; 152 breaking API change(s); 6 advisories before the change, 0 after. |
| Where | Every test ran in a sealed sandbox (podman, network deny-all networkpolicy on the task pod (claim; verified by the stage 0 probe in this pod), image the pod's own image); the model was qwen/qwen3.8-27b in agent mode; the run's own files are in this folder. |
| When | Started 2026-09-13 22:08:39 UTC. The last stage to write was self-verification at 2026-09-13 23:01:24 UTC. |

## What the harness did, step by step

Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join.

| Stage | When | What it did |
|---|---|---|
| 0 Self-verification | 2026-09-13 23:01:24 UTC | Ran 19 checks from the failure register on its own code before touching the target; all passed. Sandbox probe skipped, model probe skipped. |
| 1 Intake | 2026-09-13 22:08:59 UTC | Resolved the dependency graph at head (63 packages) and at base (63), looked every version up in OSV (4 with advisories at head), and wrote a work list of 64 packages, 5 of them changed by this change. |
| 2 Analysis | 2026-09-13 22:09:09 UTC | For each package, diffed the two versions' public API and source, found the application's call sites and read the advisories; risk score and budget: ecdsa 65 (full), pdfminer-six 65 (full), pillow 55 (full), pyasn1 90 (full), python-jose 51 (full), python-multipart 55 (full), starlette 80 (full), weasyprint 70 (full). |
| 3 Generation | 2026-09-13 22:48:33 UTC | python-jose: asked the model (qwen/qwen3.8-27b) for tests in 50 calls; kept 14 tests in 4 file(s), cut 2 that did not hold up on the baseline run, discarded 0 whole attempt(s). |
| 4 Validation execution | 2026-09-13 22:49:42 UTC | python-jose: ran 14 tests on head, again for flakes, and on the other version (new, new-rerun, old); 14 pass on head, 0 flaky, 2 proved a fix; 582 lines of the package covered. Mutation: 10 of 25 sampled mutants killed, score 0.4. |
| 5 Triage | 2026-09-13 22:57:45 UTC | ecdsa: classified every verdict; 0 tests to accept, 0 to discard or regenerate, 1 finding(s), 0 escalated to a person. pdfminer-six: classified every verdict; 0 tests to accept, 0 to discard or regenerate, 1 finding(s), 0 escalated to a person. pillow: classified every verdict; 0 tests to accept, 0 to discard or regenerate, 0 finding(s), 0 escalated to a person. pyasn1: classified every verdict; 0 tests to accept, 0 to discard or regenerate, 2 finding(s), 0 escalated to a person. python-jose: classified every verdict; 10 tests to accept, 4 to discard or regenerate, 7 finding(s), 7 escalated to a person. python-multipart: classified every verdict; 0 tests to accept, 0 to discard or regenerate, 0 finding(s), 0 escalated to a person. starlette: classified every verdict; 0 tests to accept, 0 to discard or regenerate, 1 finding(s), 0 escalated to a person. weasyprint: classified every verdict; 0 tests to accept, 0 to discard or regenerate, 0 finding(s), 0 escalated to a person. |
| 6 Review packet | 2026-09-13 22:57:49 UTC | Wrote the review packet per package: the verdict in plain terms, the tests as a patch, the findings, the draft VEX statements, and the pull request text. |
| Attestation | 2026-09-13 22:59:31 UTC | python-jose: signed the in-toto statement over the patch and the records (PASSED) and sealed the UDLM records. |
| Assessment | 2026-09-13 23:01:24 UTC | Measured the run against the blueprint's goals: 9 met, 0 not met, 0 not applicable, 1 other. |

## Decisions the harness made

- ecdsa: triage decided per test: .
- ecdsa: finding, security at confidence 0.75: ecdsa 0.19.2 has 2 open advisories at head; reachable=unknown. Route: Product Security.
- ecdsa: draft VEX per advisory: CVE-2024-23342 under_investigation.
- pdfminer-six: triage decided per test: .
- pdfminer-six: finding, security at confidence 0.75: pdfminer-six 20231228 has 4 open advisories at head; reachable=unknown. Route: Product Security.
- pdfminer-six: draft VEX per advisory: CVE-2025-64512 under_investigation, CVE-2025-70559 under_investigation.
- pillow: triage decided per test: .
- pillow: draft VEX per advisory: CVE-2026-25990 under_investigation, CVE-2026-40192 under_investigation, CVE-2026-42308 under_investigation, CVE-2026-42310 under_investigation, CVE-2026-42311 under_investigation, CVE-2026-54058 under_investigation, CVE-2026-54059 under_investigation, CVE-2026-54060 under_investigation, CVE-2026-55379 under_investigation, CVE-2026-55380 under_investigation, CVE-2026-55798 under_investigation, CVE-2026-59197 under_investigation, CVE-2026-59198 under_investigation, CVE-2026-59199 under_investigation, CVE-2026-59200 under_investigation, CVE-2026-59204 under_investigation, CVE-2026-59205 under_investigation.
- pyasn1: triage decided per test: .
- pyasn1: finding, security at confidence 0.95: pyasn1 downgraded 0.6.4 -> 0.4.8 into a version with 8 known advisories. Route: Product Security.
- pyasn1: finding, security at confidence 0.75: pyasn1 0.4.8 has 8 open advisories at head; reachable=unknown. Route: Product Security.
- pyasn1: draft VEX per advisory: CVE-2026-30922 under_investigation, CVE-2026-59884 under_investigation, CVE-2026-59885 under_investigation, CVE-2026-59886 under_investigation.
- python-jose: cut 2 generated test(s) before execution: 2 fails on baseline after repair.
- python-jose: triage decided per test: 4 discard as CVE evidence; keep as characterization only if reviewer wants it; 2 accept as CVE evidence; VEX status fixed; 8 accept as characterization candidate.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_decode_wrong_key_raises_jwt_error's 3 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 4. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_decode_expired_raises_expired_signature_error's 5 mutant kill(s) are all among test_jwt_encode_decode_roundtrip_hmac's 6. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_decode_audience_mismatch_raises_jwt_claims_error's 5 mutant kill(s) are all among test_jwt_encode_decode_roundtrip_hmac's 6. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_get_unverified_header_returns_alg_and_typ's 3 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 4. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jwt_get_unverified_claims_returns_claims_without_verification's 3 mutant kill(s) are all among test_jws_sign_verify_roundtrip's 4. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.6: python-jose: test_jws_sign_verify_roundtrip's 4 mutant kill(s) are all among test_jwt_decode_audience_mismatch_raises_jwt_claims_error's 5. Route: escalate: below confidence threshold.
- python-jose: finding, redundant at confidence 0.5: python-jose: test_utils_base64url_roundtrip killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold.
- python-jose: mutation score 0.4 is below the blueprint's 0.6; the packet says so, and the reviewer sees which tests killed nothing.
- python-jose: draft VEX per advisory: CVE-2024-29370 under_investigation, CVE-2024-33663 fixed, CVE-2024-33664 under_investigation.
- python-multipart: triage decided per test: .
- python-multipart: draft VEX per advisory: CVE-2024-53981 under_investigation, CVE-2026-24486 under_investigation, CVE-2026-40347 under_investigation, CVE-2026-42561 under_investigation, CVE-2026-53537 under_investigation, CVE-2026-53538 under_investigation, CVE-2026-53539 under_investigation, CVE-2026-53540 under_investigation.
- starlette: triage decided per test: .
- starlette: finding, security at confidence 0.9: starlette 0.41.3 has 14 open advisories at head; reachable=true. Route: Product Security.
- starlette: draft VEX per advisory: CVE-2025-54121 affected, CVE-2025-62727 affected, CVE-2026-48710 affected, CVE-2026-48817 affected, CVE-2026-48818 affected, CVE-2026-54282 affected, CVE-2026-54283 affected.
- weasyprint: triage decided per test: .
- weasyprint: draft VEX per advisory: CVE-2025-68616 under_investigation, CVE-2026-49452 under_investigation, CVE-2026-55073 under_investigation.

## Actions it took

- ecdsa: wrote a review packet with 0 accepted test(s) as a patch, ready for a pull request.
- ecdsa: drafted VEX statements for Product Security.
- ecdsa: no pull request was opened in this run; the packet holds what one would carry.
- pdfminer-six: wrote a review packet with 0 accepted test(s) as a patch, ready for a pull request.
- pdfminer-six: drafted VEX statements for Product Security.
- pdfminer-six: no pull request was opened in this run; the packet holds what one would carry.
- pillow: wrote a review packet with 0 accepted test(s) as a patch, ready for a pull request.
- pillow: drafted VEX statements for Product Security.
- pillow: no pull request was opened in this run; the packet holds what one would carry.
- pyasn1: wrote a review packet with 0 accepted test(s) as a patch, ready for a pull request.
- pyasn1: drafted VEX statements for Product Security.
- pyasn1: no pull request was opened in this run; the packet holds what one would carry.
- python-jose: wrote a review packet with 10 accepted test(s) as a patch, ready for a pull request.
- python-jose: drafted VEX statements for Product Security.
- python-jose: signed the test-result statement (PASSED).
- python-jose: no pull request was opened in this run; the packet holds what one would carry.
- python-multipart: wrote a review packet with 0 accepted test(s) as a patch, ready for a pull request.
- python-multipart: drafted VEX statements for Product Security.
- python-multipart: no pull request was opened in this run; the packet holds what one would carry.
- starlette: wrote a review packet with 0 accepted test(s) as a patch, ready for a pull request.
- starlette: drafted VEX statements for Product Security.
- starlette: no pull request was opened in this run; the packet holds what one would carry.
- weasyprint: wrote a review packet with 0 accepted test(s) as a patch, ready for a pull request.
- weasyprint: drafted VEX statements for Product Security.
- weasyprint: no pull request was opened in this run; the packet holds what one would carry.

## Actions it did not take, by design

- It did not merge anything. Tests reach a repository only through a pull request that a person merges.
- It did not change production code and did not propose a fix. Fixes come from a separate fix pipeline; this harness only tests.
- It did not publish a VEX statement. The drafts are proposals for Product Security.
- It did not delete any existing test. Retirements are proposed with evidence for a person to act on.

## The records, in plain terms

19 UDLM records, each a fact from this run in the estate's own language. Intent is what the harness proposed, Requested is what a person was asked to decide, Realized is what landed and who made it so. All are sealed with a content hash.

| Record | State | What it says | Written |
|---|---|---|---|
| Job | Requested | The harness was asked to run on source from 2ad04243861b to cfa8f4a3292b in diff mode. | 2026-09-13 22:08:39 UTC |
| Job | Realized | The run finished; its outputs are the records this statement seals. | 2026-09-13 22:49:42 UTC |
| SoftwarePackage | Discovered | python-jose 3.4.0 (pypi) is the version this change installs. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_ghsa_6c5p_j8vq_pqhj_exposure` is an exposure test for CVE-2024-33663 in `tests/test_python_jose_cve_cve_2024_33663.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_ghsa_6c5p_j8vq_pqhj_fix_pinning` is a fix-pinning test for CVE-2024-33663 in `tests/test_python_jose_cve_cve_2024_33663.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_jws_sign_verify_roundtrip` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_jwt_decode_audience_mismatch_raises_jwt_claims_error` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_jwt_decode_expired_raises_expired_signature_error` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_jwt_decode_wrong_key_raises_jwt_error` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_jwt_encode_decode_roundtrip_hmac` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_jwt_get_unverified_claims_returns_claims_without_verification` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_jwt_get_unverified_header_returns_alg_and_typ` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| TestEvidence | Intent | `test_utils_base64url_roundtrip` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 22:49:42 UTC |
| VexStatement | Intent | Draft: CVE-2024-33663 is `fixed` in this package. fix-pinning test(s) ['test_ghsa_6c5p_j8vq_pqhj_exposure', 'test_ghsa_6c5p_j8vq_pqhj_fix_pinning'] fail on pkg:pypi/python-jose@3.3.0 and pass on pkg:pypi/python-jose@3.4.0 | 2026-09-13 22:49:42 UTC |
| VexStatement | Intent | Draft: CVE-2024-33664 is `under_investigation` in this package. bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet | 2026-09-13 22:49:42 UTC |
| VexStatement | Intent | Draft: CVE-2024-29370 is `under_investigation` in this package. bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet | 2026-09-13 22:49:42 UTC |
| Vulnerability | Discovered | CVE-2024-33663 is a known vulnerability affecting <3.4.0. Also known as GHSA-6c5p-j8vq-pqhj, PYSEC-2024-232. | 2026-09-13 22:49:42 UTC |
| Vulnerability | Discovered | CVE-2024-33664 is a known vulnerability affecting <3.4.0. Also known as GHSA-cjwg-qfpm-7377, PYSEC-2024-233. | 2026-09-13 22:49:42 UTC |
| Vulnerability | Discovered | CVE-2024-29370 is a known vulnerability affecting versions the advisory does not pin. Also known as PYSEC-2025-185. | 2026-09-13 22:49:42 UTC |

## What is in this folder, and who it is for

Every file exists for a reader or a tool named here. The plain-English files come first; the machine files stay because they are the proof and the replay.

**Everyone**

- `README.md`: The story of this run: who, what, why, where, when, the outcome, the decisions and the actions.
- `assess/assess.md`: The run against the blueprint's eleven goals, each with the measurement and the file it came from.

**Reviewers (the developer or team that owns the change)**

- `intake/worklist.json`: The work list: every package at base and head, what changed, what is reachable, what carries advisories.
- `analyze/ecdsa/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/pdfminer-six/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/pillow/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/pyasn1/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/python-jose/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/python-multipart/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/starlette/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/weasyprint/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/pillow/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `analyze/pyasn1/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `analyze/python-jose/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `analyze/python-multipart/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `analyze/weasyprint/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `generate/python-jose/tests/`: The candidate test files as generated, before any decision.
- `execute/python-jose/results.json`: The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged.
- `execute/python-jose/mutation/mutation.json`: How strong the accepted tests are: which mutants of the package's source they killed, and the score.
- `execute/python-jose/relevance.json`: Which existing tests this change makes obsolete or redundant, proposed with evidence; nothing is deleted.
- `triage/ecdsa/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/pdfminer-six/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/pillow/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/pyasn1/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/python-jose/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/python-multipart/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/starlette/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `triage/weasyprint/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `packet/ecdsa/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/pdfminer-six/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/pillow/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/pyasn1/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/python-jose/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/python-multipart/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/starlette/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/weasyprint/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/ecdsa/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/pdfminer-six/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/pillow/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/pyasn1/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/python-jose/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/python-multipart/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/starlette/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/weasyprint/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/ecdsa/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/pdfminer-six/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/pillow/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/pyasn1/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/python-jose/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/python-multipart/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/starlette/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `packet/weasyprint/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.

**Product Security**

- `intake/vulns.json`: Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports.
- `analyze/ecdsa/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/pdfminer-six/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/pillow/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/pyasn1/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/python-jose/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/python-multipart/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/starlette/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/weasyprint/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `packet/ecdsa/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/pdfminer-six/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/pillow/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/pyasn1/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/python-jose/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/python-multipart/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/starlette/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.
- `packet/weasyprint/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.

**Supply Chain Security and auditors**

- `run.json`: What was run, with which tool versions, on which repository by name.
- `selfcheck/selfcheck.json`: Stage 0: every failure-register check and the sandbox and model probes, before any evidence was produced.
- `intake/sbom.new.cdx.json`: The software bill of materials at head, CycloneDX.
- `generate/python-jose/model-calls/`: Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said.
- `attest/python-jose/MANIFEST.json`: The provenance record per accepted test: model, prompt and response digests, sandbox image digest, verdicts.
- `attest/python-jose/statement.json`: The in-toto test-result statement; its subjects are the patch, the record and each evidence record's head.
- `attest/python-jose/statement.dsse.json`: The statement signed as a DSSE envelope.
- `attest/python-jose/signer.pub.pem`: The public key that verifies the envelope.
- `attest/python-jose/attest.json`: Which key signed, whether it verified locally, and what the run could not back.
- `attest/python-jose/udlm/`: The same facts as sealed UDLM records: the vulnerability, the package, the run, each accepted test, the draft VEX.

**The person who ran the harness**

- `analyze/pillow/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/pyasn1/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/python-jose/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/python-multipart/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/weasyprint/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/ecdsa/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/pdfminer-six/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/pillow/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/pyasn1/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/python-jose/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/python-multipart/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/starlette/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/weasyprint/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `generate/python-jose/manifest.json`: What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests.
- `generate/python-jose/manifest.agent.json`: The tool-using agent's traces: every tool call per advisory, and the budget it had.

**Tools (kept for replay and proof; not meant to be read)**

- `run-index.json`: What this run holds: stages, packages, headline numbers, and where every file is; the renderers read it.
- `intake/graph.new.json`: The dependency graph at head as the ecosystem's own resolver produced it.
- `intake/graph.old.json`: The dependency graph at base.
- `analyze/ecdsa/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/pdfminer-six/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/pillow/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/pyasn1/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/python-jose/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/python-multipart/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/starlette/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/weasyprint/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/pillow/api.old.json`: The public API surface at base.
- `analyze/pyasn1/api.old.json`: The public API surface at base.
- `analyze/python-jose/api.old.json`: The public API surface at base.
- `analyze/python-multipart/api.old.json`: The public API surface at base.
- `analyze/weasyprint/api.old.json`: The public API surface at base.
- `analyze/ecdsa/call-sites.json`: Every place the application references this package.
- `analyze/pdfminer-six/call-sites.json`: Every place the application references this package.
- `analyze/pillow/call-sites.json`: Every place the application references this package.
- `analyze/pyasn1/call-sites.json`: Every place the application references this package.
- `analyze/python-jose/call-sites.json`: Every place the application references this package.
- `analyze/python-multipart/call-sites.json`: Every place the application references this package.
- `analyze/starlette/call-sites.json`: Every place the application references this package.
- `analyze/weasyprint/call-sites.json`: Every place the application references this package.
- `execute/python-jose/new/`: The sealed run on head: the run script, the junit report, coverage, logs.
- `execute/python-jose/new-rerun/`: The second run on head, to catch flakes.
- `execute/python-jose/old/`: The run on the base version, for the differential.
- `execute/python-jose/mutation/mutants/`: Each sampled mutant: the mutated file and its sealed run.
- `packet/ecdsa/packet.json`: The packet's facts in structured form.
- `packet/pdfminer-six/packet.json`: The packet's facts in structured form.
- `packet/pillow/packet.json`: The packet's facts in structured form.
- `packet/pyasn1/packet.json`: The packet's facts in structured form.
- `packet/python-jose/packet.json`: The packet's facts in structured form.
- `packet/python-multipart/packet.json`: The packet's facts in structured form.
- `packet/starlette/packet.json`: The packet's facts in structured form.
- `packet/weasyprint/packet.json`: The packet's facts in structured form.
- `assess/assess.json`: The assessment in structured form.
