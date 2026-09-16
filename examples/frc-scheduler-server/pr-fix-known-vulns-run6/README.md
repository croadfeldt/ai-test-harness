# Run 76a3fa863e76: frc-scheduler-server 2ad04243861b..cfa8f4a3292b

What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.

## In plain terms

**python-jose.** This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness proved 2 of the 3 with a test that fails on the vulnerable version and passes on the fixed one; the other 1 is unproven and marked so. Accept the 7 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

## Who, what, why, where, when

|  |  |
|---|---|
| Who | The AI Test Harness 0.1.0 did the work without a person in the loop. A person decided the result: merged by croadfeldt at 2026-09-15T16:16:06Z. |
| What | Tests for python-jose 3.3.0 to 3.4.0, chosen from a work list of 64 packages, 5 of which this change touched. Repository frc-scheduler-server, change 2ad04243861b..cfa8f4a3292b, mode diff. |
| Why | python-jose (score 51, budget full): reachable from first-party code; 159 source lines changed; 5 advisories before the change, 0 after. |
| Where | Every test ran in a sealed sandbox (podman, network none, image docker.io/library/python:3.12-slim); the model was qwen38-27b in agent mode; the tests were proposed to the overlay repository as https://github.com/croadfeldt/ai-test-harness-overlays/pull/1; the run's own files are in this folder. |
| When | Started 2026-09-12 01:41:41 UTC. The last stage to write was feedback at 2026-09-15 16:27:52 UTC. |

## What the harness did, step by step

Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join.

| Stage | When | What it did |
|---|---|---|
| 0 Self-verification | 2026-09-13 15:34:55 UTC | Ran 19 checks from the failure register on its own code before touching the target; all passed. Sandbox probe skipped, model probe skipped. |
| 1 Intake | 2026-09-12 01:42:29 UTC | Resolved the dependency graph at head (63 packages) and at base (63), looked every version up in OSV (4 with advisories at head), and wrote a work list of 64 packages, 5 of them changed by this change. |
| 2 Analysis | 2026-09-13 02:49:36 UTC | For each package, diffed the two versions' public API and source, found the application's call sites and read the advisories; risk score and budget: python-jose 51 (full). |
| 3 Generation | 2026-09-13 13:28:46 UTC | python-jose: asked the model (qwen38-27b) for tests in 36 calls; kept 10 tests in 4 file(s), cut 3 that did not hold up on the baseline run, discarded 0 whole attempt(s). |
| 4 Validation execution | 2026-09-13 13:29:49 UTC | python-jose: ran 10 tests on head, again for flakes, and on the other version (new, new-rerun, old); 9 pass on head, 0 flaky, 3 proved a fix; 573 lines of the package covered. Mutation: 3 of 12 sampled mutants killed, score 0.25. |
| 5 Triage | 2026-09-13 13:33:56 UTC | python-jose: classified every verdict; 7 tests to accept, 3 to discard or regenerate, 1 finding(s), 1 escalated to a person. |
| 6 Review packet | 2026-09-13 13:33:56 UTC | Wrote the review packet per package: the verdict in plain terms, the tests as a patch, the findings, the draft VEX statements, and the pull request text. |
| Attestation | 2026-09-13 15:34:55 UTC | python-jose: signed the in-toto statement over the patch and the records (PASSED) and sealed the UDLM records. |
| Assessment | 2026-09-13 13:33:56 UTC | Measured the run against the blueprint's goals: 9 met, 0 not met, 0 not applicable, 1 other. |
| Test pull request | 2026-09-15 16:12:15 UTC | python-jose: pull request opened, https://github.com/croadfeldt/ai-test-harness-overlays/pull/1. The harness pushed one branch and opened the pull request; it merged nothing. |
| 7 Feedback | 2026-09-15 16:27:52 UTC | python-jose: read the pull request as a person left it (merged by croadfeldt at 2026-09-15T16:16:06Z): 7 accepted, 0 edited, 0 rejected; wrote the requested and realized records and the signed acceptance statement. |

## Decisions the harness made

- python-jose: cut 3 generated test(s) before execution: 3 fails on baseline after repair.
- python-jose: triage decided per test: 2 discard as CVE evidence; keep as characterization only if reviewer wants it; 3 accept as CVE evidence; VEX status fixed; 1 regenerate or discard; 4 accept as characterization candidate.
- python-jose: finding, defect at confidence 0.4: python-jose: a code path raised the same internal error on both versions during CVE test generation (CVE-2024-33663); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold.
- python-jose: mutation score 0.25 is below the blueprint's 0.6; the packet says so, and the reviewer sees which tests killed nothing.
- python-jose: draft VEX per advisory: CVE-2024-29370 under_investigation, CVE-2024-33663 fixed, CVE-2024-33664 fixed.
- python-jose: the reviewer's decision, merged by croadfeldt at 2026-09-15T16:16:06Z: 7 accepted, 0 edited, 0 rejected.

## Actions it took

- python-jose: wrote a review packet with 7 accepted test(s) as a patch, ready for a pull request.
- python-jose: drafted VEX statements for Product Security.
- python-jose: signed the test-result statement (PASSED).
- python-jose: pull request opened (https://github.com/croadfeldt/ai-test-harness-overlays/pull/1).
- python-jose: captured the reviewer's decision and wrote the realized records and the acceptance statement.

## Actions it did not take, by design

- It did not merge anything. Tests reach a repository only through a pull request that a person merges.
- It did not change production code and did not propose a fix. Fixes come from a separate fix pipeline; this harness only tests.
- It did not publish a VEX statement. The drafts are proposals for Product Security.
- It did not delete any existing test. Retirements are proposed with evidence for a person to act on.

## The records, in plain terms

30 UDLM records, each a fact from this run in the estate's own language. Intent is what the harness proposed, Requested is what a person was asked to decide, Realized is what landed and who made it so. All are sealed with a content hash.

| Record | State | What it says | Written |
|---|---|---|---|
| Job | Requested | The harness was asked to run on frc-scheduler-server from 2ad04243861b to cfa8f4a3292b in diff mode. | 2026-09-12 01:41:41 UTC |
| Job | Realized | The run finished; its outputs are the records this statement seals. | 2026-09-13 13:29:49 UTC |
| SoftwarePackage | Discovered | python-jose 3.4.0 (pypi) is the version this change installs. | 2026-09-13 13:29:49 UTC |
| TestEvidence | Intent | `test_ghsa_6c5p_j8vq_pqhj_fix_pinning` is a fix-pinning test for CVE-2024-33663 in `tests/test_python_jose_cve_cve_2024_33663.py`; it passed on head in the sealed sandbox. | 2026-09-13 13:29:49 UTC |
| TestEvidence | Intent | `test_ghsa_cjwg_qfpm_7377_exposure` is an exposure test for CVE-2024-33664 in `tests/test_python_jose_cve_cve_2024_33664.py`; it passed on head in the sealed sandbox. | 2026-09-13 13:29:49 UTC |
| TestEvidence | Intent | `test_ghsa_cjwg_qfpm_7377_fix_pinning` is a fix-pinning test for CVE-2024-33664 in `tests/test_python_jose_cve_cve_2024_33664.py`; it passed on head in the sealed sandbox. | 2026-09-13 13:29:49 UTC |
| TestEvidence | Intent | `test_jwt_decode_expired_raises_expired_signature_error` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 13:29:49 UTC |
| TestEvidence | Intent | `test_jwt_decode_roundtrip_hs256` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 13:29:49 UTC |
| TestEvidence | Intent | `test_jwt_decode_wrong_key_raises_jwt_error` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 13:29:49 UTC |
| TestEvidence | Intent | `test_jwt_encode_hs256_structure` is a unit test in `tests/test_python_jose_unit.py`; it passed on head in the sealed sandbox. | 2026-09-13 13:29:49 UTC |
| VexStatement | Intent | Draft: CVE-2024-33663 is `fixed` in this package. fix-pinning test(s) ['test_ghsa_6c5p_j8vq_pqhj_fix_pinning'] fail on pkg:pypi/python-jose@3.3.0 and pass on pkg:pypi/python-jose@3.4.0 | 2026-09-13 13:29:49 UTC |
| VexStatement | Intent | Draft: CVE-2024-33664 is `fixed` in this package. fix-pinning test(s) ['test_ghsa_cjwg_qfpm_7377_fix_pinning', 'test_ghsa_cjwg_qfpm_7377_exposure'] fail on pkg:pypi/python-jose@3.3.0 and pass on pkg:pypi/python-jose@3.4.0 | 2026-09-13 13:29:49 UTC |
| VexStatement | Intent | Draft: CVE-2024-29370 is `under_investigation` in this package. bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet | 2026-09-13 13:29:49 UTC |
| Vulnerability | Discovered | CVE-2024-33663 is a known vulnerability affecting <3.4.0. Also known as GHSA-6c5p-j8vq-pqhj, PYSEC-2024-232. | 2026-09-13 13:29:49 UTC |
| Vulnerability | Discovered | CVE-2024-33664 is a known vulnerability affecting <3.4.0. Also known as GHSA-cjwg-qfpm-7377, PYSEC-2024-233. | 2026-09-13 13:29:49 UTC |
| Vulnerability | Discovered | CVE-2024-29370 is a known vulnerability affecting versions the advisory does not pin. Also known as PYSEC-2025-185. | 2026-09-13 13:29:49 UTC |
| TestEvidence | Requested | A person was asked to decide `test_ghsa_6c5p_j8vq_pqhj_fix_pinning` on the pull request. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Realized | `test_ghsa_6c5p_j8vq_pqhj_fix_pinning` was accepted by croadfeldt and landed at `overlays/python/python-jose/3.4.x/test_python_jose_cve_cve_2024_33663.py` in merge 87109359f6c3. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Requested | A person was asked to decide `test_ghsa_cjwg_qfpm_7377_fix_pinning` on the pull request. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Realized | `test_ghsa_cjwg_qfpm_7377_fix_pinning` was accepted by croadfeldt and landed at `overlays/python/python-jose/3.4.x/test_python_jose_cve_cve_2024_33664.py` in merge 87109359f6c3. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Requested | A person was asked to decide `test_ghsa_cjwg_qfpm_7377_exposure` on the pull request. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Realized | `test_ghsa_cjwg_qfpm_7377_exposure` was accepted by croadfeldt and landed at `overlays/python/python-jose/3.4.x/test_python_jose_cve_cve_2024_33664.py` in merge 87109359f6c3. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Requested | A person was asked to decide `test_jwt_encode_hs256_structure` on the pull request. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Realized | `test_jwt_encode_hs256_structure` was accepted by croadfeldt and landed at `overlays/python/python-jose/3.4.x/test_python_jose_unit.py` in merge 87109359f6c3. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Requested | A person was asked to decide `test_jwt_decode_roundtrip_hs256` on the pull request. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Realized | `test_jwt_decode_roundtrip_hs256` was accepted by croadfeldt and landed at `overlays/python/python-jose/3.4.x/test_python_jose_unit.py` in merge 87109359f6c3. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Requested | A person was asked to decide `test_jwt_decode_wrong_key_raises_jwt_error` on the pull request. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Realized | `test_jwt_decode_wrong_key_raises_jwt_error` was accepted by croadfeldt and landed at `overlays/python/python-jose/3.4.x/test_python_jose_unit.py` in merge 87109359f6c3. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Requested | A person was asked to decide `test_jwt_decode_expired_raises_expired_signature_error` on the pull request. | 2026-09-15 16:16:06 UTC |
| TestEvidence | Realized | `test_jwt_decode_expired_raises_expired_signature_error` was accepted by croadfeldt and landed at `overlays/python/python-jose/3.4.x/test_python_jose_unit.py` in merge 87109359f6c3. | 2026-09-15 16:16:06 UTC |

## What is in this folder, and who it is for

Every file exists for a reader or a tool named here. The plain-English files come first; the machine files stay because they are the proof and the replay.

**Everyone**

- `README.md`: The story of this run: who, what, why, where, when, the outcome, the decisions and the actions.
- `assess/assess.md`: The run against the blueprint's eleven goals, each with the measurement and the file it came from.

**Reviewers (the developer or team that owns the change)**

- `intake/worklist.json`: The work list: every package at base and head, what changed, what is reachable, what carries advisories.
- `analyze/python-jose/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/python-jose/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `generate/python-jose/tests/`: The candidate test files as generated, before any decision.
- `execute/python-jose/results.json`: The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged.
- `execute/python-jose/mutation/mutation.json`: How strong the accepted tests are: which mutants of the package's source they killed, and the score.
- `triage/python-jose/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `packet/python-jose/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/python-jose/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/python-jose/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.
- `propose/python-jose/pull-request.md`: The pull request's text as posted.

**Product Security**

- `intake/vulns.json`: Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports.
- `analyze/python-jose/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `packet/python-jose/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.

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
- `propose/python-jose/proposal.json`: The branch, the commit, the files and the pull request the harness opened; the signature status.
- `feedback/python-jose/acceptance.json`: What a person accepted, edited or rejected on the pull request, and who and when.
- `feedback/python-jose/acceptance-statement.dsse.json`: The signed acceptance statement naming the merge commit and each realized record.
- `feedback/python-jose/udlm/`: The requested and realized records for every accepted test: the reviewer's act, and the test as it landed.

**The person who ran the harness**

- `analyze/python-jose/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/python-jose/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `generate/python-jose/manifest.json`: What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests.
- `generate/python-jose/manifest.agent.json`: The tool-using agent's traces: every tool call per advisory, and the budget it had.

**Tools (kept for replay and proof; not meant to be read)**

- `run-index.json`: What this run holds: stages, packages, headline numbers, and where every file is; the renderers read it.
- `intake/graph.new.json`: The dependency graph at head as the ecosystem's own resolver produced it.
- `intake/graph.old.json`: The dependency graph at base.
- `analyze/python-jose/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/python-jose/api.old.json`: The public API surface at base.
- `analyze/python-jose/call-sites.json`: Every place the application references this package.
- `generate/python-jose/scratch/`: Every attempt that ran in the sandbox during generation, with its output; not committed.
- `execute/python-jose/new/`: The sealed run on head: the run script, the junit report, coverage, logs.
- `execute/python-jose/new-rerun/`: The second run on head, to catch flakes.
- `execute/python-jose/old/`: The run on the base version, for the differential.
- `execute/python-jose/mutation/mutants/`: Each sampled mutant: the mutated file and its sealed run.
- `packet/python-jose/packet.json`: The packet's facts in structured form.
- `assess/assess.json`: The assessment in structured form.
- `feedback/python-jose/decisions.jsonl`: One labeled example per test for prompt evaluation: the decision with the prompt and response digests behind it.
