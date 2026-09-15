# harness: the opinionated implementation

**In plain terms.** This is the code that does what the blueprint describes, for Python packages. It
reacts to a commit or pull request, works out which dependencies changed and which carry known
vulnerabilities, has a model write tests, runs them in a sealed container against both versions, scores
them, and produces a one-page review packet, draft VEX statements, and a signed record. It checks
itself before every run and stops if any check fails.

This directory is the second of three layers: the blueprint (`docs/`, `blueprint/`) says what the
harness must do; this package is one way of doing it; `examples/` holds what it produced on real code.

## The choices it makes

Opinionated means the capability map's primary choices are fixed here, not configurable:

## More than one target repository

A work directory belongs to the repository intake ran on. Stages that read the repository (`analyze`,
`relevance`) take it from the local configuration, or from `--repo`, and refuse to run when the two
disagree, so facts are never gathered from the wrong checkout.

## Configure a local install

Nothing about a particular machine, network, or account is in this repository. Copy
`harness.example.toml` to `harness.local.toml` (git-ignored) and set the model endpoint, the target
repository path, and the interpreter version. Environment variables override the file
(`HARNESS_MODEL_BASE_URL`, `HARNESS_MODEL`, `HARNESS_TARGET_REPO`, and the others named in the example
file). Records never carry the endpoint address or a local path: they carry the endpoint's label from
the file and a digest of its address, and the repository by name.

## Run it

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest

# Stage 0 on its own (every later stage also runs it first and stops if it fails):
.venv/bin/harness selfcheck --workdir out/run1

# Stage 1, react to a commit range on a target repo (the product team's PR):
.venv/bin/harness intake --base main --head HEAD --workdir out/run1      # repo, manifest, interpreter from harness.local.toml

# Or a scheduled rescan of one ref:
.venv/bin/harness intake --head main --workdir out/rescan

# Stage 2, facts and risk for every changed or vulnerable row:
.venv/bin/harness analyze --workdir out/run1 --python-version 3.12

# Stage 3, the model writes candidate tests, verified in the sandbox as it goes:
.venv/bin/harness generate --workdir out/run1 --select python-jose --categories cve unit

# Stage 4, the gauntlet: head run, flake re-run, coverage, differential against the old version:
.venv/bin/harness execute --workdir out/run1 --select python-jose

# Stage 4 step 5, mutation testing of the passing tests (25 sampled mutants by default):
.venv/bin/harness mutate --workdir out/run1 --select python-jose

# Stage 4 step 7, which existing tests the change makes obsolete or redundant (proposals with evidence):
.venv/bin/harness relevance --workdir out/run1 --select python-jose

# Stages 5, 6, attestation, and the post-analysis:
.venv/bin/harness triage --workdir out/run1 --select python-jose
.venv/bin/harness packet --workdir out/run1 --select python-jose
.venv/bin/harness attest --workdir out/run1 --select python-jose
.venv/bin/harness assess --workdir out/run1
```

## On a cluster

`deploy/tekton/` runs the same stages as one Tekton PipelineRun: stage 0 first, then intake through
the post-analysis, with the execute task's pod as the sandbox (deny-all network policy, no
service-account token, read-only root, a probe from inside before any generated code runs). The
image is built from `Containerfile`. Set `HARNESS_SANDBOX_TARGET=pod` to use the in-pod sandbox
outside Tekton too. See `deploy/tekton/README.md`.

## Two languages, one pipeline

Everything a stage needs from a language sits behind the adapter as a small test toolkit
(`adapters/python.py` and `adapters/go.py`, same function names): how a test file is named and
headed, which prompt rules and task text the model gets, how a response is parsed, compiled, checked
for forbidden imports and assertions that cannot fail, how failing tests are cut from a file, how an
offline environment is prefetched and a sealed run is started, and how results and coverage are read
back. The stages call those functions and nothing else that is language-specific, so the Python
examples and the Go example go through the same generate, execute, triage, packet, attest, and
assess code.

## Work directory layout

```
run.json                       harness version, tool versions, exact command
selfcheck/selfcheck.json       stage 0: every register check by id, pass/fail; sandbox and model probes
intake/
  graph.old.json graph.new.json   full transitive graph at base and head, depth and parents per package
  sbom.new.cdx.json             CycloneDX SBOM of the head graph
  vulns.json                    every OSV entry for every (package, version) in either graph
  worklist.json                 one row per package: change, depth, reachable, pre-flight, vulns
analyze/<package>/
  api.old.json api.new.json     public API surface, tool-derived
  api-diff.json                 added / removed / changed symbols, breaking flag and reason
  call-sites.json               every first-party reference, production and test
  vulns.json                    advisories with fixed versions and any named symbols
  notes.untrusted.md            maintainer text from PyPI, banner says untrusted
  facts.json                    the fact bundle stage 3 consumes, including the risk score and budget
analyze/summary.json            one line per analyzed package
generate/<package>/
  tests/test_<package>_<category>.py   candidate tests, pytest, header says generated and unreviewed
  manifest.json                 per file: category, tests kept and cut, attempts, model, prompt and response digests
  model-calls/                  every prompt and response verbatim, with usage and latency
  scratch/                      baseline sandbox runs made during repair
execute/<package>/
  results.json                  TestResults: per test status, old/new versions, verdict, coverage summary
  new/ new-rerun/ old/          junit.xml, coverage.json, logs, sandbox.json for each run
  mutation/mutation.json        sampled mutants with status and killers, score, per-test kills and unique kills
  relevance.json                retirement proposals with reason, evidence, horizon, and rewrite flag
triage/<package>/triage.json    findings and per-test classes with confidence, routing, evidence refs
packet/<package>/
  packet.md                     the one-page review packet
  tests.patch                   accepted tests as a patch against overlays/python/<package>/<major.minor>.x/
  vex.openvex.json              draft OpenVEX, one statement per vulnerability, for Product Security
attest/<package>/
  MANIFEST.json                 provenance record per accepted test (blueprint/manifest.schema.yaml)
  udlm/*.yaml, udlm/index.json  the same facts as UDLM records, sealed; index lists heads and schema validation
  statement.json                in-toto Statement, predicate test-result/v0.1 with the harness record
  statement.dsse.json           DSSE envelope; signer.pub.pem verifies it
assess/assess.md                the run against the blueprint's goals
cache/                          downloaded archives, unpacked trees, OSV and PyPI responses
```

## Status

| Stage | State |
|---|---|
| 0 self-verification | implemented: one check per failure-register entry (blueprint section 17), sandbox probe, model probe; runs before intake, generate, and execute; fails closed; record referenced from every manifest |
| 1 intake | implemented, Python |
| 2 analyze | implemented, Python |
| 3 generate | implemented: ASTER-style loop (facts as DATA, compile, baseline run in the sandbox, repair, cut failing tests, coverage gate). Not yet run against a model; the first run is the next step. |
| 4 execute | implemented: sandbox run on head, flake re-run, coverage, differential against the base graph or a resolved fixed candidate, TestResults in the adapter-interface schema. `harness mutate` adds the mutation score and per-test kills; `harness relevance` proposes retirements: tests that reference symbols the change removes or alters (rewrite candidates when a same-named symbol was added), tests that killed no sampled mutant, tests whose kills are a strict subset of another's, and skipped tests. Proposals only; a person approves. |
| 5 triage | implemented: deterministic classes with confidence and routing; below threshold escalates; agent-reported defects need stage 4 corroboration |
| 6 packet | implemented: one-page packet, accepted tests as a patch in the overlay layout, draft OpenVEX per vulnerability (fixed only with a confirmed fix-pinning test) |
| 7 feedback | register loop implemented (section 17); reviewer-decision capture waits for a real reviewer |
| lifecycles (blueprint 5.0) | A, the developer's inner loop: this command line and the Tekton run are it. B, the pipeline's outer loop: everything up to the packet; the step that opens the test pull request from the packet is not written yet |
| attest | implemented: provenance record per accepted test (manifest.schema.yaml) and the same facts as UDLM records (TestEvidence at the harness's provider class, VexStatement, Vulnerability, SoftwarePackage, Job) sealed with UDLM's chain code from a local checkout; in-toto Statement with the test-result/v0.1 predicate whose subjects include each evidence record's head; DSSE envelope signed with a local Ed25519 development key and verified; Trusted Artifact Signer replaces the key in Konflux |
| assess | implemented: eleven goals from the blueprint, each measured from the run's files with a verdict and evidence path |
| Go adapter | all stages: `go list`/`go mod graph` for the graph, `go mod download` for source, a go/ast helper (`adapters/gohelper/`) for API surfaces, call sites, and the test-file gates; tests are `package harnesstest` files on the standard testing package, run by `sandbox_go.py` in a sealed container with a read-only module cache (`GOPROXY=off`); the fixed-candidate environment comes from `go get` on a scratch copy of the application. Mutation for Go runs through the same helper (seven operators on go/ast) against a writable copy of the module reached by a replace directive; a mutant that does not compile is invalid, not killed. Not yet for Go: the Tekton pod target (the harness image has no Go toolchain). |
