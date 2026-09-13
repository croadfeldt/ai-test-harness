# Example: a real pull request, judged by the harness

**In plain terms.** A pull request on a FastAPI service I run set out to fix four packages with known
vulnerabilities. The harness read the change, wrote and ran tests in a sealed sandbox, and reported: one
vulnerability proven closed, one proven introduced by a downgrade the PR never mentions, and one proven
still open in a package the PR left alone. Nobody wrote any of that by hand. Every file under the run
directories is harness output, kept exactly as produced.

## Who should read what

| You are | Read | Time |
|---|---|---|
| Deciding whether this approach is worth funding | This page down to "What it took" | 5 minutes |
| Reviewing the pull request | `pr-fix-known-vulns-run5/packet/*/packet.md`, one page per package | 1 minute each |
| Building or running the harness | The rest of this page, then `harness/README.md` | 30 minutes |

## The verdict on the pull request

| Package | What the PR did | Proven by a test | Still unproven | Draft VEX for Product Security |
|---|---|---|---|---|
| python-jose | updated 3.3.0 to 3.4.0 | 1 vulnerability closed | 2 | 1 fixed, 2 under investigation |
| pyasn1 | silently downgraded 0.6.4 to 0.4.8 | 1 vulnerability introduced | 3 | 1 affected with evidence, 3 under investigation |
| starlette | left at 0.41.3 | 1 vulnerability live today | 6 | 7 affected; upgrade path: fastapi 0.141.1 |

"Proven" means a test that fails on the vulnerable version and passes on the fixed one, run in the
sandbox on both. "Unproven" means the harness tried, could not build a trigger, and says so instead of
shipping a green test. The pyasn1 downgrade is the finding a reviewer would most likely have missed: pip
chose it while resolving the python-jose bump, and the PR diff never shows it.

Each package also has a signed record of every accepted test, and the run met 9 of 11 goals from the
blueprint. The two not met: test strength by mutation score (below), and time-to-packet, which had no
target because the trigger was manual.

## How strong are the accepted tests

Mutation testing changes the package's code in small ways and checks whether the tests notice. The
blueprint's target is 0.6.

| Package | Accepted tests | Mutants sampled | Killed | Score |
|---|---|---|---|---|
| python-jose | 7 | 12 | 5 | 0.417 |
| pyasn1 | 10 | 12 | 5 | 0.417 |
| starlette | 6 | 12 | 0 | 0.0 |

Starlette's accepted tests noticed nothing. They are not wrong, they are weak, and the packet says so.
That is the gate working: a weak test is reported, not promoted.

## What it took

The same package, python-jose, was run five times on one model, changing one thing each time. The
first four runs proved nothing. The harness reported that honestly each time, and each failure became
a permanent, self-checked rule in the blueprint's failure register (section 17).

| Run | One change | Vulnerabilities proven |
|---|---|---|
| 1 | baseline: one prompt, retry on error | 0 |
| 2 | reject tests that cannot fail; allow the package's own dependencies; stop runaway output | 0 |
| 3 | give the model the fix's own diff and the names that differ between versions | 0 |
| 4 | let the model use tools: read source, run its test on both versions | 0 |
| 5 | cap reading before a test run; tell the model when it reached the fix; flag repeated failures | **1 of 3** |

Runs 1 to 4 each took 15 to 60 minutes on a 27B model on a laptop. The run that worked used three tool
calls. Run 6 (`-run6/`) held everything from run 5 and moved the same model to a two-GPU server,
five times faster: 2 of 3 vulnerabilities proven in 22 minutes end to end, the
key-confusion one included. Same model, same rules; the speed bought more attempts inside the
same budget. Then pyasn1 and starlette went through the same pipeline once each and each proved one
vulnerability. The register grew to nineteen entries along the way; every one has a check that runs
before every pipeline run.

## What the harness could not do, said plainly

- **Build every trigger.** Fourteen vulnerabilities were tried across the three packages; three were
  proven, eleven were not. For the eleven the model either never reached the vulnerable behavior
  or ran into a code path broken on both versions. A stronger model is the next thing to try, and
  the packets record exactly which ones remain.
- **Prove test strength for starlette.** Score zero. The tests are characterization, not proof.
- **Sign with production keys.** Attestations are signed with a local development key and say so.
  Trusted Artifact Signer replaces it inside Konflux.
- **Run scanners that were not installed.** Pre-flight and static analysis record "not run" rather
  than "clean".

## A defect found on the side

python-jose's encryption feature is broken against the crypto library this application uses, on both
the old and the new version. The harness hit it repeatedly while trying to build a trigger, recorded
it as a candidate defect, and triage routed it with the reproducer. The application does not use that
feature, so it is low severity, but it is real.

## Reproduce it

```
cd harness && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
D=../examples/frc-scheduler-server/pr-fix-known-vulns-run5
.venv/bin/harness intake   --repo ../../frc-scheduler-server --base main --head deps/fix-known-vulns --python-version 3.12 --workdir $D
.venv/bin/harness analyze  --workdir $D --python-version 3.12
.venv/bin/harness generate --workdir $D --select python-jose --categories cve unit --mode agent   # needs a model endpoint
.venv/bin/harness execute  --workdir $D --select python-jose
.venv/bin/harness mutate   --workdir $D --select python-jose
.venv/bin/harness triage   --workdir $D; .venv/bin/harness packet --workdir $D; .venv/bin/harness attest --workdir $D
.venv/bin/harness assess   --workdir $D
```

The trigger is a branch in the application's repository, `deps/fix-known-vulns`, that bumps the four
pins. The model was `qwen/qwen3.8-27b` at 8-bit through LM Studio on a laptop, reasoning off; run 6
used the same model served by vLLM on a two-GPU server. Point the harness at any OpenAI-compatible
endpoint in `harness/harness.local.toml`; every call's prompt and response is kept.

The records name endpoints by a label and a digest of their address, and the target repository by its
name, never by an address or a local path. Records from the earlier runs were rewritten to that form
before this repository went public, and the attestations that covered them were re-signed; test file
digests, verdicts, and every other recorded fact are unchanged (`tools/redact-local-details.py`).

## What is in each run directory

| Directory | What it holds |
|---|---|
| `rescan/` | A scheduled scan of `main`: 63 packages, 7 with known vulnerabilities, before any change |
| `pr-fix-known-vulns/` through `-run4/` | python-jose runs 1 to 4, kept as produced, for the ladder above |
| `pr-fix-known-vulns-run5/` | The full pipeline on all three packages: the packets, VEX drafts, signed attestations, mutation results, and the post-analysis |

Inside a run: `intake/` (dependency graph, SBOM, work list), `analyze/` (facts per package),
`generate/` (candidate tests, every model prompt and response), `execute/` (results on both versions,
mutation), `triage/`, `packet/`, `attest/`, `assess/`, and `selfcheck/` (stage 0, run first). Large
raw files and downloaded packages are not committed; the commands above recreate them.
