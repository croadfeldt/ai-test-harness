# Run 8e6fa6151887: control-plane 1acc678bd670..1acc678bd670

What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.

## In plain terms

**github.com/getkin/kin-openapi.** This change leaves github.com/getkin/kin-openapi at v0.139.0, which has 4 known vulnerabilities the application is exposed to. The harness could not prove any of the 4 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

## Who, what, why, where, when

|  |  |
|---|---|
| Who | The AI Test Harness 0.1.0 did the work without a person in the loop. A person decides the result; nothing in this run has been merged. |
| What | Tests for github.com/getkin/kin-openapi v0.139.0, chosen from a work list of 277 packages, 0 of which this change touched; 15 other package(s) were analyzed and scored but not selected for generation. Repository control-plane, change 1acc678bd670..1acc678bd670, mode diff. |
| Why | github.com/getkin/kin-openapi (score 70, budget full): reachable from first-party code; 8 known vulnerabilities for this version. |
| Where | Every test ran in a sealed sandbox (pod, network deny-all networkpolicy on the task pod (claim; verified by the stage 0 probe in this pod), image image-registry.openshift-image-registry.svc:5000/ai-test-harness/harness@sha256:5b882bca9a1029974d5dc49c0e646c0a0305e031bafec85c13628d1b8e816439); the model was qwen3-235b in agent mode; the run's own files are in this folder. |
| When | Started 2026-09-18 13:14:43 UTC. The last stage to write was self-verification at 2026-09-18 16:56:48 UTC. |

## What the harness did, step by step

Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join.

| Stage | When | What it did |
|---|---|---|
| 0 Self-verification | 2026-09-18 16:56:48 UTC | Ran 24 checks from the failure register on its own code before touching the target; all passed. Sandbox probe skipped, model probe skipped. |
| 1 Intake | 2026-09-18 13:14:47 UTC | Resolved the dependency graph at head (276 packages) and at base (276), looked every version up in OSV (16 with advisories at head), and wrote a work list of 277 packages, 0 of them changed by this change. |
| 2 Analysis | 2026-09-18 13:15:23 UTC | For each package, diffed the two versions' public API and source, found the application's call sites and read the advisories; risk score and budget: github.com/getkin/kin-openapi 70 (full), github.com/gomarkdown/markdown 55 (snapshot), github.com/jackc/pgx/v5 55 (reduced), github.com/klauspost/compress 45 (snapshot), github.com/labstack/echo/v4 55 (snapshot), github.com/nats-io/nats-server/v2 45 (reduced), github.com/yuin/goldmark 45 (snapshot), go.opentelemetry.io/otel 45 (snapshot), go.opentelemetry.io/otel/exporters/otlp/otlptrace 55 (snapshot), go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc 55 (snapshot), go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp 65 (full), go.opentelemetry.io/otel/sdk 55 (snapshot), golang.org/x/crypto 55 (snapshot), golang.org/x/mod 45 (snapshot), google.golang.org/grpc 55 (snapshot), oras.land/oras-go/v2 55 (snapshot). |
| 3 Generation | 2026-09-18 16:55:07 UTC | github.com/getkin/kin-openapi: asked the model (qwen3-235b) for tests in 74 calls; kept 4 tests in 2 file(s), cut 0 that did not hold up on the baseline run, discarded 3 whole attempt(s). |
| 4 Validation execution | 2026-09-18 16:55:34 UTC | github.com/getkin/kin-openapi: ran 4 tests on head, again for flakes, and on the other version (new, new-rerun, old); 0 pass on head, 0 flaky, 0 proved a fix; 0 lines of the package covered. Mutation skipped. |
| 5 Triage | 2026-09-18 16:56:05 UTC | github.com/getkin/kin-openapi: classified every verdict; 0 tests to accept, 4 to discard or regenerate, 2 finding(s), 5 escalated to a person. |
| 6 Review packet | 2026-09-18 16:56:17 UTC | Wrote the review packet per package: the verdict in plain terms, the tests as a patch, the findings, the draft VEX statements, and the pull request text. |
| Attestation | 2026-09-18 16:56:35 UTC | github.com/getkin/kin-openapi: signed the in-toto statement over the patch and the records (PASSED) and sealed the UDLM records. |
| Assessment | 2026-09-18 16:56:48 UTC | Measured the run against the blueprint's goals: 9 met, 0 not met, 1 not applicable, 1 other. |

## Decisions the harness made

- github.com/getkin/kin-openapi: discarded 3 generation attempt(s): 1 did not collect on the baseline after repairs; 2 agent exhausted its budget without an accepted submission.
- github.com/getkin/kin-openapi: triage decided per test: 4 escalate.
- github.com/getkin/kin-openapi: finding, security at confidence 0.9: github.com/getkin/kin-openapi v0.139.0 has 8 open advisories at head; reachable=true. Route: Product Security.
- github.com/getkin/kin-openapi: finding, defect at confidence 0.4: github.com/getkin/kin-openapi: a code path raised the same internal error on both versions during CVE test generation (CVE-2026-76905); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold.
- github.com/getkin/kin-openapi: draft VEX per advisory: CVE-2026-73501 affected, CVE-2026-73502 affected, CVE-2026-76905 affected, CVE-2026-77354 affected.

## Actions it took

- github.com/getkin/kin-openapi: wrote a review packet with 0 accepted test(s) as a patch, ready for a pull request.
- github.com/getkin/kin-openapi: drafted VEX statements for Product Security.
- github.com/getkin/kin-openapi: signed the test-result statement (PASSED).
- github.com/getkin/kin-openapi: no pull request was opened in this run; the packet holds what one would carry.

## Actions it did not take, by design

- It did not merge anything. Tests reach a repository only through a pull request that a person merges.
- It did not change production code and did not propose a fix. Fixes come from a separate fix pipeline; this harness only tests.
- It did not publish a VEX statement. The drafts are proposals for Product Security.
- It did not delete any existing test. Retirements are proposed with evidence for a person to act on.

## The records, in plain terms

11 UDLM records, each a fact from this run in the estate's own language. Intent is what the harness proposed, Requested is what a person was asked to decide, Realized is what landed and who made it so. All are sealed with a content hash.

| Record | State | What it says | Written |
|---|---|---|---|
| Job | Requested | The harness was asked to run on source from 1acc678bd670 to 1acc678bd670 in diff mode. | 2026-09-18 13:14:43 UTC |
| Job | Realized | The run finished; its outputs are the records this statement seals. | 2026-09-18 16:55:34 UTC |
| SoftwarePackage | Discovered | github.com/getkin/kin-openapi v0.139.0 (golang) is the version this change installs. | 2026-09-18 16:55:34 UTC |
| VexStatement | Intent | Draft: CVE-2026-73502 is `affected` in this package. open at head; reachable=true; fixed in ['0.144.0'] | 2026-09-18 16:55:34 UTC |
| VexStatement | Intent | Draft: CVE-2026-76905 is `affected` in this package. open at head; reachable=true; fixed in ['0.141.0'] | 2026-09-18 16:55:34 UTC |
| VexStatement | Intent | Draft: CVE-2026-73501 is `affected` in this package. open at head; reachable=true; fixed in ['0.144.0'] | 2026-09-18 16:55:34 UTC |
| VexStatement | Intent | Draft: CVE-2026-77354 is `affected` in this package. open at head; reachable=true; fixed in ['0.142.0'] | 2026-09-18 16:55:34 UTC |
| Vulnerability | Discovered | CVE-2026-73502 is a known vulnerability affecting <0.144.0. Also known as GHSA-jpcw-4wr7-c3vq, GO-2026-6112. | 2026-09-18 16:55:34 UTC |
| Vulnerability | Discovered | CVE-2026-76905 is a known vulnerability affecting <0.141.0. Also known as GHSA-mmfr-pmjx-hw9w, GO-2026-6274. | 2026-09-18 16:55:34 UTC |
| Vulnerability | Discovered | CVE-2026-73501 is a known vulnerability affecting <0.144.0. Also known as GHSA-r277-6w6q-xmqw, GO-2026-6095. | 2026-09-18 16:55:34 UTC |
| Vulnerability | Discovered | CVE-2026-77354 is a known vulnerability affecting <0.142.0. Also known as GHSA-xhj3-7xw9-vr34, GO-2026-6275. | 2026-09-18 16:55:34 UTC |

## What is in this folder, and who it is for

Every file exists for a reader or a tool named here. The plain-English files come first; the machine files stay because they are the proof and the replay.

**Everyone**

- `README.md`: The story of this run: who, what, why, where, when, the outcome, the decisions and the actions.
- `assess/assess.md`: The run against the blueprint's eleven goals, each with the measurement and the file it came from.

**Reviewers (the developer or team that owns the change)**

- `intake/worklist.json`: The work list: every package at base and head, what changed, what is reachable, what carries advisories.
- `analyze/github.com/getkin/kin-openapi/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/gomarkdown/markdown/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/jackc/pgx/v5/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/klauspost/compress/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/labstack/echo/v4/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/nats-io/nats-server/v2/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/yuin/goldmark/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/go.opentelemetry.io/otel/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/go.opentelemetry.io/otel/sdk/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/golang.org/x/crypto/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/golang.org/x/mod/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/google.golang.org/grpc/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/oras.land/oras-go/v2/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `generate/github.com/getkin/kin-openapi/tests/`: The candidate test files as generated, before any decision.
- `execute/github.com/getkin/kin-openapi/results.json`: The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged.
- `execute/github.com/getkin/kin-openapi/mutation/mutation.json`: How strong the accepted tests are: which mutants of the package's source they killed, and the score.
- `execute/github.com/getkin/kin-openapi/relevance.json`: Which existing tests this change makes obsolete or redundant, proposed with evidence; nothing is deleted.
- `triage/github.com/getkin/kin-openapi/triage.json`: Every verdict and finding classified, with a confidence and a route; below the threshold a person decides.
- `packet/github.com/getkin/kin-openapi/packet.md`: The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action.
- `packet/github.com/getkin/kin-openapi/tests.patch`: The accepted tests as a patch in the layout they will live in.
- `packet/github.com/getkin/kin-openapi/pull-request.md`: The text and the file list the test pull request carries, whether or not one was opened.

**Product Security**

- `intake/vulns.json`: Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports.
- `analyze/github.com/getkin/kin-openapi/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/github.com/gomarkdown/markdown/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/github.com/jackc/pgx/v5/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/github.com/klauspost/compress/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/github.com/labstack/echo/v4/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/github.com/nats-io/nats-server/v2/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/github.com/yuin/goldmark/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/go.opentelemetry.io/otel/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/go.opentelemetry.io/otel/sdk/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/golang.org/x/crypto/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/golang.org/x/mod/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/google.golang.org/grpc/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/oras.land/oras-go/v2/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/github.com/getkin/kin-openapi/fixed-candidate.json`: When the change left a vulnerable version in place: the environment the harness resolved with the fixed version, and what had to move.
- `packet/github.com/getkin/kin-openapi/vex.openvex.json`: One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness.

**Supply Chain Security and auditors**

- `run.json`: What was run, with which tool versions, on which repository by name.
- `selfcheck/selfcheck.json`: Stage 0: every failure-register check and the sandbox and model probes, before any evidence was produced.
- `intake/sbom.new.cdx.json`: The software bill of materials at head, CycloneDX.
- `generate/github.com/getkin/kin-openapi/model-calls/`: Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said.
- `attest/github.com/getkin/kin-openapi/MANIFEST.json`: The provenance record per accepted test: model, prompt and response digests, sandbox image digest, verdicts.
- `attest/github.com/getkin/kin-openapi/statement.json`: The in-toto test-result statement; its subjects are the patch, the record and each evidence record's head.
- `attest/github.com/getkin/kin-openapi/statement.dsse.json`: The statement signed as a DSSE envelope.
- `attest/github.com/getkin/kin-openapi/signer.pub.pem`: The public key that verifies the envelope.
- `attest/github.com/getkin/kin-openapi/attest.json`: Which key signed, whether it verified locally, and what the run could not back.
- `attest/github.com/getkin/kin-openapi/udlm/`: The same facts as sealed UDLM records: the vulnerability, the package, the run, each accepted test, the draft VEX.

**The person who ran the harness**

- `analyze/github.com/getkin/kin-openapi/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/gomarkdown/markdown/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/jackc/pgx/v5/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/klauspost/compress/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/labstack/echo/v4/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/nats-io/nats-server/v2/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/yuin/goldmark/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/go.opentelemetry.io/otel/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/go.opentelemetry.io/otel/sdk/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/golang.org/x/crypto/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/golang.org/x/mod/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/google.golang.org/grpc/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/oras.land/oras-go/v2/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `generate/github.com/getkin/kin-openapi/manifest.json`: What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests.
- `generate/github.com/getkin/kin-openapi/manifest.agent.json`: The tool-using agent's traces: every tool call per advisory, and the budget it had.

**Tools (kept for replay and proof; not meant to be read)**

- `run-index.json`: What this run holds: stages, packages, headline numbers, and where every file is; the renderers read it.
- `intake/graph.new.json`: The dependency graph at head as the ecosystem's own resolver produced it.
- `intake/graph.old.json`: The dependency graph at base.
- `analyze/github.com/getkin/kin-openapi/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/github.com/gomarkdown/markdown/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/github.com/jackc/pgx/v5/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/github.com/klauspost/compress/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/github.com/labstack/echo/v4/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/github.com/nats-io/nats-server/v2/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/github.com/yuin/goldmark/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/go.opentelemetry.io/otel/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/go.opentelemetry.io/otel/sdk/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/golang.org/x/crypto/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/golang.org/x/mod/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/google.golang.org/grpc/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/oras.land/oras-go/v2/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/github.com/getkin/kin-openapi/call-sites.json`: Every place the application references this package.
- `analyze/github.com/gomarkdown/markdown/call-sites.json`: Every place the application references this package.
- `analyze/github.com/jackc/pgx/v5/call-sites.json`: Every place the application references this package.
- `analyze/github.com/klauspost/compress/call-sites.json`: Every place the application references this package.
- `analyze/github.com/labstack/echo/v4/call-sites.json`: Every place the application references this package.
- `analyze/github.com/nats-io/nats-server/v2/call-sites.json`: Every place the application references this package.
- `analyze/github.com/yuin/goldmark/call-sites.json`: Every place the application references this package.
- `analyze/go.opentelemetry.io/otel/call-sites.json`: Every place the application references this package.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/call-sites.json`: Every place the application references this package.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/call-sites.json`: Every place the application references this package.
- `analyze/go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/call-sites.json`: Every place the application references this package.
- `analyze/go.opentelemetry.io/otel/sdk/call-sites.json`: Every place the application references this package.
- `analyze/golang.org/x/crypto/call-sites.json`: Every place the application references this package.
- `analyze/golang.org/x/mod/call-sites.json`: Every place the application references this package.
- `analyze/google.golang.org/grpc/call-sites.json`: Every place the application references this package.
- `analyze/oras.land/oras-go/v2/call-sites.json`: Every place the application references this package.
- `execute/github.com/getkin/kin-openapi/new/`: The sealed run on head: the run script, the junit report, coverage, logs.
- `execute/github.com/getkin/kin-openapi/new-rerun/`: The second run on head, to catch flakes.
- `execute/github.com/getkin/kin-openapi/fixed-candidate/`: The run on the resolved fixed version, for the differential when the change did not move the package.
- `packet/github.com/getkin/kin-openapi/packet.json`: The packet's facts in structured form.
- `assess/assess.json`: The assessment in structured form.
