# harness: the opinionated implementation

This directory is the second of the three layers in this repository: the blueprint (`docs/`,
`blueprint/`) says what the harness must do; this package is one opinionated way of doing it; the
`examples/` directory holds what this package produced when pointed at real repositories, and the
post-analysis of whether it met the blueprint's goals.

Opinionated means the capability map's primary choices are hard-wired here, not configurable:

| Capability | Choice in this implementation |
|---|---|
| Dependency graph | pip's own resolver in `--dry-run --report` mode, targeting the project's interpreter (from its Containerfile) with wheels only, falling back to the running interpreter. Hermeto output will replace it when the harness runs inside Konflux. |
| SBOM | CycloneDX 1.5 JSON emitted from that graph |
| Known vulnerabilities and malicious-package gate | OSV.dev batch query; MAL- entries are the OpenSSF Malicious Packages feed |
| Pre-flight scanners | GuardDog when installed, recorded as not installed otherwise; Capslock is Go-only |
| API surface and contract diff | Standard-library `ast` over the downloaded wheel: public modules, functions, classes, methods with signatures. A change to the required parameters is breaking. |
| First-party call sites | `ast` over the target repository with venv, node_modules and build directories excluded; test files flagged |
| Release notes | PyPI long description, written to `notes.untrusted.md` with a banner. Never an instruction to a model. |
| Risk score and budget | `risk.py`, weights listed once, every contribution written to the fact bundle as a reason |
| Model for generation | Any OpenAI-compatible chat endpoint; default is the homelab vLLM route serving Qwen3.6-27B. Set `HARNESS_MODEL_BASE_URL`, `HARNESS_MODEL`, `HARNESS_MODEL_API_KEY`. Every call's prompt, response, digests, usage, and latency are written under `generate/<package>/model-calls/`. |
| Sandbox | Podman: `--network none`, all capabilities dropped, no new privileges, read-only root, tmpfs work dir, memory / pid / cpu / time limits, environment cleared with `env -i`, wheels installed offline from a prefetched wheelhouse. `tests/test_sandbox_integration.py` proves each claim with a probe. The Kubernetes target with a Kata or gVisor RuntimeClass reuses the same plan. |

Nothing in stages 1 and 2 calls a model. Facts come from tools; the model gets them in stage 3.

## Run it

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest

# Stage 1, react to a commit range on a target repo (the product team's PR):
.venv/bin/harness intake --repo ../../frc-scheduler-server --base main --head HEAD \
    --manifest requirements.txt --python-version 3.12 --workdir out/run1

# Or a scheduled rescan of one ref:
.venv/bin/harness intake --repo ../../frc-scheduler-server --head main --python-version 3.12 --workdir out/rescan

# Stage 2, facts and risk for every changed or vulnerable row:
.venv/bin/harness analyze --workdir out/run1 --python-version 3.12

# Stage 3, the model writes candidate tests, verified in the sandbox as it goes:
.venv/bin/harness generate --workdir out/run1 --select python-jose --categories cve unit

# Stage 4, the gauntlet: head run, flake re-run, coverage, differential against the old version:
.venv/bin/harness execute --workdir out/run1 --select python-jose
```

## Work directory layout

```
run.json                       harness version, tool versions, exact command
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
cache/                          downloaded archives, unpacked trees, OSV and PyPI responses
```

## Status

| Stage | State |
|---|---|
| 1 intake | implemented, Python |
| 2 analyze | implemented, Python |
| 3 generate | implemented: ASTER-style loop (facts as DATA, compile, baseline run in the sandbox, repair, cut failing tests, coverage gate). Not yet run against a model; the first run is the next step. |
| 4 execute | implemented: sandbox run on head, flake re-run, coverage, differential with the package pinned to its old version, TestResults in the adapter-interface schema. Mutation and relevance arrive with triage. |
| 5 triage, 6 packet, 7 feedback | after that |
| attest | after that: manifest.schema.yaml + in-toto test-result predicate, Tekton Chains |
| assess | post-analysis of a run against the blueprint's core goals |
| Go adapter | after the Python adapter is complete end to end |
