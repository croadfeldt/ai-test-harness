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

# Stages 5, 6, attestation, and the post-analysis:
.venv/bin/harness triage --workdir out/run1 --select python-jose
.venv/bin/harness packet --workdir out/run1 --select python-jose
.venv/bin/harness attest --workdir out/run1 --select python-jose
.venv/bin/harness assess --workdir out/run1
```

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
| 4 execute | implemented: sandbox run on head, flake re-run, coverage, differential against the base graph or a resolved fixed candidate, TestResults in the adapter-interface schema. `harness mutate` adds the mutation score and per-test kills; the relevance check on existing tests is next. |
| 5 triage | implemented: deterministic classes with confidence and routing; below threshold escalates; agent-reported defects need stage 4 corroboration |
| 6 packet | implemented: one-page packet, accepted tests as a patch in the overlay layout, draft OpenVEX per vulnerability (fixed only with a confirmed fix-pinning test) |
| 7 feedback | register loop implemented (section 17); reviewer-decision capture waits for a real reviewer |
| attest | implemented: provenance record per accepted test (manifest.schema.yaml) and the same facts as UDLM records (TestEvidence at the harness's provider class, VexStatement, Vulnerability, SoftwarePackage, Job) sealed with UDLM's chain code from a local checkout; in-toto Statement with the test-result/v0.1 predicate whose subjects include each evidence record's head; DSSE envelope signed with a local Ed25519 development key and verified; Trusted Artifact Signer replaces the key in Konflux |
| assess | implemented: eleven goals from the blueprint, each measured from the run's files with a verdict and evidence path |
| Go adapter | after the Python adapter is complete end to end |
