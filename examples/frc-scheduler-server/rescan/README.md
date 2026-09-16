# Run a16348ae128b: frc-scheduler-server 2ad04243861b

What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.

## In plain terms

This run has not reached the review packet yet; the last stage that wrote was intake.

## Who, what, why, where, when

|  |  |
|---|---|
| Who | The AI Test Harness 0.1.0 did the work without a person in the loop. A person decides the result; nothing in this run has been merged. |
| What | A scheduled scan of frc-scheduler-server at 2ad04243861b, no change under review. 7 of 64 packages carry known vulnerabilities. Tests for ecdsa 0.19.2, pdfminer-six 20231228, pillow 11.0.0, python-jose 3.3.0, python-multipart 0.0.12, starlette 0.41.3, weasyprint 63.1. |
| Why | The risk score decides the budget; the two strongest reasons per package: ecdsa (score 65, budget full): reachability unknown, treated as reachable; 2 known vulnerabilities for this version. pdfminer-six (score 65, budget full): reachability unknown, treated as reachable; 4 known vulnerabilities for this version. pillow (score 65, budget full): reachability unknown, treated as reachable; 34 known vulnerabilities for this version. python-jose (score 80, budget full): reachable from first-party code; 5 known vulnerabilities for this version. python-multipart (score 65, budget full): reachability unknown, treated as reachable; 16 known vulnerabilities for this version. starlette (score 80, budget full): reachable from first-party code; 14 known vulnerabilities for this version. weasyprint (score 80, budget full): reachable from first-party code; 6 known vulnerabilities for this version. |
| Where | The run's own files are in this folder. |
| When | Started 2026-09-12 01:42:31 UTC. The last stage to write was analysis at 2026-09-12 01:43:23 UTC. |

## What the harness did, step by step

Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join.

| Stage | When | What it did |
|---|---|---|
| 1 Intake | 2026-09-12 01:42:53 UTC | Resolved the dependency graph at head (63 packages) and at base (63), looked every version up in OSV (7 with advisories at head), and wrote a work list of 64 packages, 0 of them changed by this change. |
| 2 Analysis | 2026-09-12 01:43:23 UTC | For each package, read each package's API and source, found the application's call sites and read the advisories; risk score and budget: ecdsa 65 (full), pdfminer-six 65 (full), pillow 65 (full), python-jose 80 (full), python-multipart 65 (full), starlette 80 (full), weasyprint 80 (full). |

## Decisions the harness made

- No decisions yet; the run has not reached triage.

## Actions it took

- ecdsa: no pull request was opened in this run; the packet holds what one would carry.
- pdfminer-six: no pull request was opened in this run; the packet holds what one would carry.
- pillow: no pull request was opened in this run; the packet holds what one would carry.
- python-jose: no pull request was opened in this run; the packet holds what one would carry.
- python-multipart: no pull request was opened in this run; the packet holds what one would carry.
- starlette: no pull request was opened in this run; the packet holds what one would carry.
- weasyprint: no pull request was opened in this run; the packet holds what one would carry.

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
- `analyze/ecdsa/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/pdfminer-six/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/pillow/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/python-jose/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/python-multipart/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/starlette/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/weasyprint/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.

**Product Security**

- `intake/vulns.json`: Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports.
- `analyze/ecdsa/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/pdfminer-six/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/pillow/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/python-jose/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/python-multipart/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/starlette/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/weasyprint/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.

**Supply Chain Security and auditors**

- `run.json`: What was run, with which tool versions, on which repository by name.
- `intake/sbom.new.cdx.json`: The software bill of materials at head, CycloneDX.

**The person who ran the harness**

- `analyze/ecdsa/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/pdfminer-six/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/pillow/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/python-jose/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/python-multipart/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/starlette/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/weasyprint/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.

**Tools (kept for replay and proof; not meant to be read)**

- `run-index.json`: What this run holds: stages, packages, headline numbers, and where every file is; the renderers read it.
- `intake/graph.new.json`: The dependency graph at head as the ecosystem's own resolver produced it.
- `intake/graph.old.json`: The dependency graph at base.
- `analyze/ecdsa/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/pdfminer-six/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/pillow/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/python-jose/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/python-multipart/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/starlette/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/weasyprint/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/ecdsa/call-sites.json`: Every place the application references this package.
- `analyze/pdfminer-six/call-sites.json`: Every place the application references this package.
- `analyze/pillow/call-sites.json`: Every place the application references this package.
- `analyze/python-jose/call-sites.json`: Every place the application references this package.
- `analyze/python-multipart/call-sites.json`: Every place the application references this package.
- `analyze/starlette/call-sites.json`: Every place the application references this package.
- `analyze/weasyprint/call-sites.json`: Every place the application references this package.
