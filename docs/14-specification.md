# Implementation specification

**For:** the engineer implementing or evaluating an AI Test Harness. One page. What an implementation
must do, the three contracts it must honor, and how it is judged. The reasons are in the
[blueprint](03-blueprint.md); this page states only what is required. MUST is required; SHOULD is
expected unless a written reason says otherwise. Every line names the check or test that proves it in
this implementation, or says there is none yet.

## Requirements

| Id | Requirement | Proved by |
|---|---|---|
| R1 | A run MUST take a repository by path or address and two refs, the change and the last known-good base, any ref git can name including a pull request's own; base omitted means a rescan. | `test_repo_url` |
| R2 | Before touching the target, a run MUST pass every entry of the failure register against its own code and probe the sandbox and the model; any failure stops the run. | `test_selfcheck`, stage 0 record |
| R3 | Intake MUST resolve the dependency graph at both refs with the ecosystem's own resolver inside the target's interpreter image, look every version up for advisories, and write a work list with one row per package and one for the repository. | GF-010, GF-011 |
| R4 | Analysis MUST produce, per package in scope, the public API diff, the application's call sites, the advisories with the symbols they name, and a risk score that sets the budget. | GF-005, GF-006, `test_api_diff`, `test_call_sites`, `test_risk` |
| R5 | Generation MUST reach the model only through a named, digested prompt set recorded in the manifest, and through an adapter that implements the toolkit contract below. | `test_prompts_and_evaluate`, `test_go_toolkit` |
| R6 | A generated test MUST be kept only if it compiles, collects and passes on the baseline; a file's compiler-named tests are cut before any repair; a repair that collects nothing never erases an attempt that ran. | GF-020, GF-024, GF-027 |
| R7 | The tool-using agent MUST submit only text the sandbox ran that collected on every version, within a budget that always reserves one run and one submit. | GF-013, GF-023 |
| R8 | A failure of the path to the model SHOULD be retried; a refusal from the model is final. | GF-025 |
| R9 | Every candidate MUST run in a sealed sandbox: no network, no secrets, read-only root, disposable; twice on head for flakes, and on the base or a resolved fixed candidate for the differential. | `test_sandbox_integration`, GF-008, GF-010 |
| R10 | Every old/new outcome MUST map to a fixed, honest verdict; a fix is proven only by a test that fails on the vulnerable version and passes on the fixed one. | GF-012, GF-016, `test_verdicts` |
| R11 | Mutation MUST sample only lines the generated tests executed, bounded, and record which test killed which mutant; a mutant that does not compile is invalid, not killed. | GF-028, `test_go_mutation_integration`, `test_mutant_patch` |
| R12 | Retirement of existing tests SHOULD be proposed with evidence and MUST NOT be performed. | `test_relevance` |
| R13 | Triage MUST classify every verdict and finding with a confidence and a route; below the threshold a person decides. | no direct check yet; goal G8 reads what was escalated |
| R14 | The packet MUST open in plain terms, carry the accepted tests as a patch, draft a VEX statement per advisory (fixed only on a proven test, matched by id in any case), and the pull request's text and file list. | GF-026, `test_packet_vex_case`, `test_story` |
| R15 | Provenance MUST be a signed in-toto statement over the patch and the records, with the same facts as sealed UDLM records, and the endpoint and repository recorded by label, digest and name only. | `test_udlm_records`, `test_runindex`, goal G6 |
| R16 | Every run MUST write its story and an index that names every file with its reader and reason, after every stage. | `test_story`, `test_runindex` |
| R17 | The harness MUST NOT merge, publish a VEX statement, delete a test, or change production code; in the pipeline's loop it pushes one branch and opens a pull request. | goal G1, `test_propose` |
| R18 | After a person decides, the harness MUST read the decision back as labeled examples and as requested and realized records under a signed acceptance statement. | `test_feedback` |
| R19 | Fitness of a model and a prompt set MUST be measured on finished runs by reviewer decisions, sandbox verdicts and cost, and a set or model becomes a default only by winning that table. | `test_prompts_and_evaluate`, [document 12](12-prompt-and-model-evaluation.md) |
| R20 | A trigger (pull request, push, schedule, person) SHOULD start a run with one command and the refs the event implies. | `test_cli_manifest`; no check for the trigger files yet |
| R21 | Analysis MUST read the repository's CI definitions at the reviewed commit and record what they do with untrusted code while tests run; triage MUST state each as a finding with the correcting change, routed to the pipeline's owners; the harness MUST NOT edit the pipeline. | `test_pipeline_facts`, goal G12 |
| R22 | Analysis MUST count what the existing suite reaches of each package in scope and of the symbols the change altered; triage MUST state a provable gap as a finding with the call sites to test. | `test_pipeline_facts` |

## Contracts

- **Adapter toolkit.** One module per ecosystem exposing the same names: `SYSTEM`, `CATEGORY_TASK`, `prompt_preamble`, `extract_code`, `compile_check`, `test_names`, `drop_tests`, `cut_at_errors` (compiled languages), `imports_ok`, `weak_assertions`, `prefetch`, `run_tests`, `parse_results`, `coverage_for`, `mutation_sites`, `apply_mutation`, `write_overlay`, `mutant_status`, `fixed_candidate`, `symbol_refs`. The stages call nothing else.
- **Sealed sandbox.** Input: an offline environment, a tests directory, an optional overlay for a mutant. Output: `junit.xml`, `coverage.json` with executed lines per file, the run script, stdout and stderr, and a summary with the image digest, timeout and isolation facts. Same shape for every target and language.
- **Records.** `run-index.json` (format `ai-test-harness/run-index/v1`), `README.md` the story, `packet/<pkg>/{packet.md,tests.patch,vex.openvex.json,pull-request.md}`, `attest/<pkg>/{MANIFEST.json,statement.json,statement.dsse.json,udlm/}`, `feedback/<pkg>/{acceptance.json,decisions.jsonl,udlm/}`. Schemas under `blueprint/`.

## How an implementation is judged

1. The register passes: every entry has a check, and stage 0 runs them all before every run.
2. Every run is assessed against the blueprint's twelve goals, with the measurement and the file it came from.
3. The reference jobs, rerun and compared with the baseline in [document 12](12-prompt-and-model-evaluation.md):

| Job | Model, prompt set | Baseline |
|---|---|---|
| python-jose 3.3.0 to 3.4.0 in frc-scheduler-server | qwen38-27b, v1 | 7 tests accepted, 3 of 3 advisories proven, mutation 0.25; merged by a reviewer |
| kin-openapi v0.139.0 in control-plane | qwen3-235b, v1 | 8 tests, 432 lines covered, mutation 0.6, 0 of 4 advisories proven |

A change that lowers a baseline line is a regression until the table says otherwise; a model or set that beats one becomes the default for that job.
