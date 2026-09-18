# Run 76a3fa863e76: frc-scheduler-server 2ad04243861b..cfa8f4a3292b

What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.

## In plain terms

This run has not reached the review packet yet; the last stage that wrote was intake.

## Who, what, why, where, when

|  |  |
|---|---|
| Who | The AI Test Harness 0.1.0 did the work without a person in the loop. A person decides the result; nothing in this run has been merged. |
| What | Tests for python-jose 3.3.0 to 3.4.0, chosen from a work list of 64 packages, 5 of which this change touched. Repository frc-scheduler-server, change 2ad04243861b..cfa8f4a3292b, mode diff. |
| Why | python-jose (score 51, budget full): reachable from first-party code; 159 source lines changed; 5 advisories before the change, 0 after. |
| Where | Every test ran in a sealed sandbox (podman, network none, image docker.io/library/python:3.12-slim); the model was qwen/qwen3.8-27b in fixed mode; the run's own files are in this folder. |
| When | Started 2026-09-12 01:41:41 UTC. The last stage to write was validation execution at 2026-09-12 04:05:40 UTC. |

## What the harness did, step by step

Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join.

| Stage | When | What it did |
|---|---|---|
| 1 Intake | 2026-09-12 01:42:29 UTC | Resolved the dependency graph at head (63 packages) and at base (63), looked every version up in OSV (4 with advisories at head), and wrote a work list of 64 packages, 5 of them changed by this change. |
| 2 Analysis | 2026-09-12 03:45:43 UTC | For each package, diffed the two versions' public API and source, found the application's call sites and read the advisories; risk score and budget: python-jose 51 (full). |
| 3 Generation | 2026-09-12 04:04:37 UTC | python-jose: asked the model (qwen/qwen3.8-27b) for tests in 12 calls; kept 14 tests in 4 file(s), cut 2 that did not hold up on the baseline run, discarded 0 whole attempt(s). |
| 4 Validation execution | 2026-09-12 04:05:40 UTC | python-jose: ran 14 tests on head, again for flakes, and on the other version (new, new-rerun, old); 8 pass on head, 0 flaky, 0 proved a fix; 560 lines of the package covered. |

## Decisions the harness made

- python-jose: cut 2 generated test(s) before execution: 2 fails on baseline after repair.

## Actions it took

- None yet.

## Actions it did not take, by design

- It did not merge anything. Tests reach a repository only through a pull request that a person merges.
- It did not change production code and did not propose a fix. Fixes come from a separate fix pipeline; this harness only tests.
- It did not publish a VEX statement. The drafts are proposals for Product Security.
- It did not delete any existing test. Retirements are proposed with evidence for a person to act on.

## What is in this folder, and who it is for

Every file exists for a reader or a tool named here. The plain-English files come first; the machine files stay because they are the proof and the replay.

**Everyone**

- `README.md`: The story of this run: who, what, why, where, when, the outcome, the decisions and the actions.

**Reviewers (the developer or team that owns the change)**

- `intake/worklist.json`: The work list: every package at base and head, what changed, what is reachable, what carries advisories.
- `analyze/python-jose/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/python-jose/api-diff.json`: Every added, removed or changed public symbol between the two versions, with a breaking flag.
- `generate/python-jose/tests/`: The candidate test files as generated, before any decision.
- `execute/python-jose/results.json`: The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged.

**Product Security**

- `intake/vulns.json`: Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports.
- `analyze/python-jose/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.

**Supply Chain Security and auditors**

- `run.json`: What was run, with which tool versions, on which repository by name.
- `intake/sbom.new.cdx.json`: The software bill of materials at head, CycloneDX.
- `generate/python-jose/model-calls/`: Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said.

**The person who ran the harness**

- `analyze/python-jose/source-diff.patch`: The package's own source diff between the versions; the model reads it to find the fix.
- `analyze/python-jose/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `generate/python-jose/manifest.json`: What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests.

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
