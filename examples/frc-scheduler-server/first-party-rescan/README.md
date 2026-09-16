# Run 50ec3b2446fe: frc-scheduler-server 2ad04243861b

What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.

## In plain terms

**frc-scheduler-server.** This is the application's own code, frc-scheduler-server, at commit 2ad04243861b. No known vulnerability applies to it, so there is nothing to prove; the tests below characterize what the code does today. Accept the 4 candidate tests if they look right, act on the findings below.

## Who, what, why, where, when

|  |  |
|---|---|
| Who | The AI Test Harness 0.1.0 did the work without a person in the loop. A person decides the result; nothing in this run has been merged. |
| What | A scheduled scan of frc-scheduler-server at 2ad04243861b, no change under review. 7 of 64 packages carry known vulnerabilities. Tests for the application's own code at 2ad04243861b. |
| Why | frc-scheduler-server: the application's own changed code has no tests from anyone else; the harness tests what the change added or changed. |
| Where | Every test ran in a sealed sandbox (podman, network none, image docker.io/library/python:3.12-slim); the model was qwen38-27b in fixed mode; the run's own files are in this folder. |
| When | Started 2026-09-15 20:02:08 UTC. The last stage to write was self-verification at 2026-09-15 20:29:43 UTC. |

## What the harness did, step by step

Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join.

| Stage | When | What it did |
|---|---|---|
| 0 Self-verification | 2026-09-15 20:29:43 UTC | Ran 22 checks from the failure register on its own code before touching the target; all passed. Sandbox probe skipped, model probe skipped. |
| 1 Intake | 2026-09-15 20:02:45 UTC | Resolved the dependency graph at head (63 packages) and at base (63), looked every version up in OSV (7 with advisories at head), and wrote a work list of 64 packages, 0 of them changed by this change. |
| 2 Analysis | 2026-09-15 20:02:45 UTC | frc-scheduler-server: read the application's diff and found the symbols it added or changed. |
| 3 Generation | 2026-09-15 20:06:25 UTC | frc-scheduler-server: asked the model (qwen38-27b) for tests in 6 calls; kept 4 tests in 1 file(s), cut 3 that did not hold up on the baseline run, discarded 1 whole attempt(s). |
| 4 Validation execution | 2026-09-15 20:08:18 UTC | frc-scheduler-server: ran 4 tests on head, again for flakes, and on the other version (new, new-rerun); 4 pass on head, 0 flaky, 0 proved a fix; 350 lines of the package covered. Mutation: 1 of 25 sampled mutants killed, score 0.04. |
| 5 Triage | 2026-09-15 20:28:26 UTC | frc-scheduler-server: classified every verdict; 4 tests to accept, 0 to discard or regenerate, 4 finding(s), 4 escalated to a person. |
| 6 Review packet | 2026-09-15 20:29:42 UTC | Wrote the review packet per package: the verdict in plain terms, the tests as a patch, the findings, the draft VEX statements, and the pull request text. |
| Attestation | 2026-09-15 20:29:43 UTC | frc-scheduler-server: signed the in-toto statement over the patch and the records (PASSED) and sealed the UDLM records. |
| Assessment | 2026-09-15 20:29:43 UTC | Measured the run against the blueprint's goals: 8 met, 1 not met, 1 not applicable, 1 other. |

## Decisions the harness made

- frc-scheduler-server: cut 3 generated test(s) before execution: 3 fails on baseline after repair.
- frc-scheduler-server: discarded 1 generation attempt(s): 1 no parseable test file after repairs.
- frc-scheduler-server: triage decided per test: 4 accept as candidate.
- frc-scheduler-server: finding, redundant at confidence 0.5: frc-scheduler-server: test_canonical_filename_encodes_shape killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold.
- frc-scheduler-server: finding, redundant at confidence 0.5: frc-scheduler-server: test_canonical_path_uses_base_dir killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold.
- frc-scheduler-server: finding, redundant at confidence 0.5: frc-scheduler-server: test_load_canonical_missing_returns_none killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold.
- frc-scheduler-server: finding, redundant at confidence 0.5: frc-scheduler-server: test_parse_csv_reads_rows killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold.
- frc-scheduler-server: mutation score 0.04 is below the blueprint's 0.6; the packet says so, and the reviewer sees which tests killed nothing.

## Actions it took

- frc-scheduler-server: wrote a review packet with 4 accepted test(s) as a patch, ready for a pull request.
- frc-scheduler-server: drafted VEX statements for Product Security.
- frc-scheduler-server: signed the test-result statement (PASSED).
- frc-scheduler-server: no pull request was opened in this run; the packet holds what one would carry.

## Actions it did not take, by design

- It did not merge anything. Tests reach a repository only through a pull request that a person merges.
- It did not change production code and did not propose a fix. Fixes come from a separate fix pipeline; this harness only tests.
- It did not publish a VEX statement. The drafts are proposals for Product Security.
- It did not delete any existing test. Retirements are proposed with evidence for a person to act on.

## The records, in plain terms

7 UDLM records, each a fact from this run in the estate's own language. Intent is what the harness proposed, Requested is what a person was asked to decide, Realized is what landed and who made it so. All are sealed with a content hash.

| Record | State | What it says | Written |
|---|---|---|---|
| Job | Requested | The harness was asked to run on frc-scheduler-server from None to 2ad04243861b in rescan mode. | 2026-09-15 20:02:08 UTC |
| Job | Realized | The run finished; its outputs are the records this statement seals. | 2026-09-15 20:08:18 UTC |
| SoftwarePackage | Discovered | frc-scheduler-server 2ad04243861b (generic) is the version this change installs. | 2026-09-15 20:08:18 UTC |
| TestEvidence | Intent | `test_canonical_filename_encodes_shape` is a unit test in `tests/test_frc_scheduler_server_unit.py`; it passed on head in the sealed sandbox. | 2026-09-15 20:08:18 UTC |
| TestEvidence | Intent | `test_canonical_path_uses_base_dir` is a unit test in `tests/test_frc_scheduler_server_unit.py`; it passed on head in the sealed sandbox. | 2026-09-15 20:08:18 UTC |
| TestEvidence | Intent | `test_load_canonical_missing_returns_none` is a unit test in `tests/test_frc_scheduler_server_unit.py`; it passed on head in the sealed sandbox. | 2026-09-15 20:08:18 UTC |
| TestEvidence | Intent | `test_parse_csv_reads_rows` is a unit test in `tests/test_frc_scheduler_server_unit.py`; it passed on head in the sealed sandbox. | 2026-09-15 20:08:18 UTC |

## What is in this folder, and who it is for

Every file exists for a reader or a tool named here. The plain-English files come first; the machine files stay because they are the proof and the replay.

**Everyone**

- `README.md`: The story of this run: who, what, why, where, when, the outcome, the decisions and the actions.
- `assess/assess.md`: The run against the blueprint's eleven goals, each with the measurement and the file it came from.

**Reviewers (the developer or team that owns the change)**

- `intake/worklist.json`: The work list: every package at base and head, what changed, what is reachable, what carries advisories.
- `analyze/frc-scheduler-server/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `generate/frc-scheduler-server/tests/`: The candidate test files as generated, before any decision.
- `execute/frc-scheduler-server/results.json`: The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged.
- `execute/frc-scheduler-server/mutation/mutation.json`: How strong the accepted tests are: which mutants of the package's source they killed, and the score.
- `execute/frc-scheduler-server/relevance.json`: Which existing tests this change makes obsolete or redundant, proposed with evidence; nothing is deleted.
- `triage/frc-scheduler-server/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `packet/frc-scheduler-server/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/frc-scheduler-server/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/frc-scheduler-server/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.

**Product Security**

- `intake/vulns.json`: Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports.
- `analyze/frc-scheduler-server/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `packet/frc-scheduler-server/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.

**Supply Chain Security and auditors**

- `run.json`: What was run, with which tool versions, on which repository by name.
- `selfcheck/selfcheck.json`: Stage 0: every failure-register check and the sandbox and model probes, before any evidence was produced.
- `intake/sbom.new.cdx.json`: The software bill of materials at head, CycloneDX.
- `generate/frc-scheduler-server/model-calls/`: Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said.
- `attest/frc-scheduler-server/MANIFEST.json`: The provenance record per accepted test: model, prompt and response digests, sandbox image digest, verdicts.
- `attest/frc-scheduler-server/statement.json`: The in-toto test-result statement; its subjects are the patch, the record and each evidence record's head.
- `attest/frc-scheduler-server/statement.dsse.json`: The statement signed as a DSSE envelope.
- `attest/frc-scheduler-server/signer.pub.pem`: The public key that verifies the envelope.
- `attest/frc-scheduler-server/attest.json`: Which key signed, whether it verified locally, and what the run could not back.
- `attest/frc-scheduler-server/udlm/`: The same facts as sealed UDLM records: the vulnerability, the package, the run, each accepted test, the draft VEX.

**The person who ran the harness**

- `generate/frc-scheduler-server/manifest.json`: What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests.

**Tools (kept for replay and proof; not meant to be read)**

- `run-index.json`: What this run holds: stages, packages, headline numbers, and where every file is; the renderers read it.
- `intake/graph.new.json`: The dependency graph at head as the ecosystem's own resolver produced it.
- `intake/graph.old.json`: The dependency graph at base.
- `analyze/frc-scheduler-server/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/frc-scheduler-server/call-sites.json`: Every place the application references this package.
- `execute/frc-scheduler-server/new/`: The sealed run on head: the run script, the junit report, coverage, logs.
- `execute/frc-scheduler-server/new-rerun/`: The second run on head, to catch flakes.
- `execute/frc-scheduler-server/mutation/mutants/`: Each sampled mutant: the mutated file and its sealed run.
- `packet/frc-scheduler-server/packet.json`: The packet's facts in structured form.
- `assess/assess.json`: The assessment in structured form.
