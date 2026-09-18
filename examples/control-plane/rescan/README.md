# Run 558e6e085fe1: control-plane 147f74f4edc2

What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.

## In plain terms

This run has not reached the review packet yet; the last stage that wrote was self-verification.

## Who, what, why, where, when

|  |  |
|---|---|
| Who | The AI Test Harness 0.1.0 did the work without a person in the loop. A person decides the result; nothing in this run has been merged. |
| What | A scheduled scan of control-plane at 147f74f4edc2, no change under review. 14 of 251 packages carry known vulnerabilities. Tests for github.com/getkin/kin-openapi v0.139.0, github.com/gomarkdown/markdown v0.0.0-20240328165702-4d01890c35c0, github.com/jackc/pgx/v5 v5.8.0, github.com/klauspost/compress v1.18.5, github.com/labstack/echo/v4 v4.15.1, github.com/nats-io/nats-server/v2 v2.12.5, github.com/yuin/goldmark v1.4.13, go.opentelemetry.io/otel v1.43.0, golang.org/x/crypto v0.51.0, golang.org/x/mod v0.35.0, golang.org/x/net v0.53.0, golang.org/x/text v0.37.0, google.golang.org/grpc v1.81.0, oras.land/oras-go/v2 v2.6.0. |
| Why | The risk score decides the budget; the two strongest reasons per package: github.com/getkin/kin-openapi (score 70, budget full): reachable from first-party code; 8 known vulnerabilities for this version. github.com/gomarkdown/markdown (score 55, budget snapshot): reachability unknown, treated as reachable; 4 known vulnerabilities for this version. github.com/jackc/pgx/v5 (score 55, budget snapshot): reachability unknown, treated as reachable; 6 known vulnerabilities for this version. github.com/klauspost/compress (score 45, budget snapshot): reachability unknown, treated as reachable; 1 known vulnerability for this version. github.com/labstack/echo/v4 (score 55, budget snapshot): reachability unknown, treated as reachable; 2 known vulnerabilities for this version. github.com/nats-io/nats-server/v2 (score 45, budget reduced): 22 known vulnerabilities for this version; at least one advisory carries a severity rating. github.com/yuin/goldmark (score 45, budget snapshot): reachability unknown, treated as reachable; 1 known vulnerability for this version. go.opentelemetry.io/otel (score 45, budget snapshot): reachability unknown, treated as reachable; 1 known vulnerability for this version. golang.org/x/crypto (score 65, budget full): reachability unknown, treated as reachable; 30 known vulnerabilities for this version. golang.org/x/mod (score 45, budget snapshot): reachability unknown, treated as reachable; 2 known vulnerabilities for this version. golang.org/x/net (score 55, budget snapshot): reachability unknown, treated as reachable; 8 known vulnerabilities for this version. golang.org/x/text (score 45, budget snapshot): reachability unknown, treated as reachable; 1 known vulnerability for this version. google.golang.org/grpc (score 55, budget snapshot): reachability unknown, treated as reachable; 5 known vulnerabilities for this version. oras.land/oras-go/v2 (score 55, budget snapshot): reachability unknown, treated as reachable; 10 known vulnerabilities for this version. |
| Where | The run's own files are in this folder. |
| When | Started 2026-09-13 20:43:59 UTC. The last stage to write was analysis at 2026-09-13 20:47:30 UTC. |

## What the harness did, step by step

Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join.

| Stage | When | What it did |
|---|---|---|
| 0 Self-verification | 2026-09-13 20:43:59 UTC | Ran 19 checks from the failure register on its own code before touching the target; all passed. Sandbox probe skipped, model probe skipped. |
| 1 Intake | 2026-09-13 20:44:23 UTC | Resolved the dependency graph at head (250 packages) and at base (250), looked every version up in OSV (14 with advisories at head), and wrote a work list of 251 packages, 0 of them changed by this change. |
| 2 Analysis | 2026-09-13 20:47:30 UTC | For each package, read each package's API and source, found the application's call sites and read the advisories; risk score and budget: github.com/getkin/kin-openapi 70 (full), github.com/gomarkdown/markdown 55 (snapshot), github.com/jackc/pgx/v5 55 (snapshot), github.com/klauspost/compress 45 (snapshot), github.com/labstack/echo/v4 55 (snapshot), github.com/nats-io/nats-server/v2 45 (reduced), github.com/yuin/goldmark 45 (snapshot), go.opentelemetry.io/otel 45 (snapshot), golang.org/x/crypto 65 (full), golang.org/x/mod 45 (snapshot), golang.org/x/net 55 (snapshot), golang.org/x/text 45 (snapshot), google.golang.org/grpc 55 (snapshot), oras.land/oras-go/v2 55 (snapshot). |

## Decisions the harness made

- No decisions yet; the run has not reached triage.

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
- `analyze/github.com/getkin/kin-openapi/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/gomarkdown/markdown/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/jackc/pgx/v5/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/klauspost/compress/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/labstack/echo/v4/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/nats-io/nats-server/v2/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/github.com/yuin/goldmark/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/go.opentelemetry.io/otel/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/golang.org/x/crypto/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/golang.org/x/mod/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/golang.org/x/net/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/golang.org/x/text/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/google.golang.org/grpc/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.
- `analyze/oras.land/oras-go/v2/facts.json`: The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned.

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
- `analyze/golang.org/x/crypto/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/golang.org/x/mod/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/golang.org/x/net/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/golang.org/x/text/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/google.golang.org/grpc/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.
- `analyze/oras.land/oras-go/v2/vulns.json`: The advisories on this package's versions, with the symbols they name and the fixed versions.

**Supply Chain Security and auditors**

- `run.json`: What was run, with which tool versions, on which repository by name.
- `selfcheck/selfcheck.json`: Stage 0: every failure-register check and the sandbox and model probes, before any evidence was produced.
- `intake/sbom.new.cdx.json`: The software bill of materials at head, CycloneDX.

**The person who ran the harness**

- `analyze/github.com/getkin/kin-openapi/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/gomarkdown/markdown/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/jackc/pgx/v5/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/klauspost/compress/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/labstack/echo/v4/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/nats-io/nats-server/v2/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/github.com/yuin/goldmark/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/go.opentelemetry.io/otel/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/golang.org/x/crypto/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/golang.org/x/mod/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/golang.org/x/net/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/golang.org/x/text/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/google.golang.org/grpc/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.
- `analyze/oras.land/oras-go/v2/notes.untrusted.md`: Package metadata and description as published upstream; untrusted text, kept for context.

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
- `analyze/golang.org/x/crypto/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/golang.org/x/mod/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/golang.org/x/net/api.new.json`: The public API surface at head, extracted by tools.
- `analyze/golang.org/x/text/api.new.json`: The public API surface at head, extracted by tools.
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
- `analyze/golang.org/x/crypto/call-sites.json`: Every place the application references this package.
- `analyze/golang.org/x/mod/call-sites.json`: Every place the application references this package.
- `analyze/golang.org/x/net/call-sites.json`: Every place the application references this package.
- `analyze/golang.org/x/text/call-sites.json`: Every place the application references this package.
- `analyze/google.golang.org/grpc/call-sites.json`: Every place the application references this package.
- `analyze/oras.land/oras-go/v2/call-sites.json`: Every place the application references this package.
