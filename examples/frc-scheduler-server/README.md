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

## Which tests the change makes irrelevant (`-run5/execute/*/relevance.json`)

The relevance engine proposes retirements with evidence; a person approves; nothing is deleted.

| Package | Proposals | What they say |
|---|---|---|
| python-jose | 4 redundant | four characterization tests whose mutant kills are all among another test's kills |
| pyasn1 | 8 redundant | the eight existence-only unit tests killed no sampled mutant, the same tests the trivial-assertion rule now rejects at generation time |
| starlette | 1 obsolete, 4 redundant | one CVE exposure test references a class whose required parameters change in the 1.3.1 upgrade, so it breaks when that upgrade lands; four unit tests killed nothing |

Forty-seven of the application's own tests were examined too; five files reference these packages and
none references a symbol the changes remove. The proposals appear in each packet's "Promotions and
retirements" section, marked advisory, with the horizon they apply to.

## The same facts as UDLM records (`-run5/attest/*/udlm/`)

Every attestation directory also holds the run's facts as records in the Unified Data Lifecycle
Model, the shape UDLM adopted in its own registry after this run produced them: one vulnerability
record per CVE, the package version, the run as a job, one candidate test-evidence record per accepted
test at the harness's provider class, and the draft VEX statement per vulnerability. Each record is
sealed with UDLM's own chain code, and the signed statement names each evidence record's head as a
subject, so a consumer can verify the signature, match a subject to a record, and follow references
from the evidence to the vulnerability, the package, the run, and the claim. The records validate
against UDLM's state-record schema; `udlm/index.json` says whether they were sealed and how many
schema problems remain, and the attestation's "unverified" list repeats it when either is not clean.
A candidate is an intent record; a reviewer's acceptance would be a realized record, by a human act.

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

## The same pipeline on a cluster (`-cluster/`, `-cluster-run2/`, `-cluster-run3/`)

Everything above ran on a workstation. These two runs are the same pipeline as a Tekton PipelineRun
on OpenShift: one task per stage, stage 0 first, and the execute pod is the sandbox. A deny-all
network policy, no service account token, and a read-only root are set by the pod spec, and the pod's
first step proves them before any generated test runs. Nothing about the cluster is in the records
beyond the image digest; the model was the same laptop model, reached from the pod over the network.

| Run | Tests ran | Proven | Accepted | Mutation score | UDLM records | Trigger to packet |
|---|---|---|---|---|---|---|
| `-cluster/` | 14 | 1 vulnerability (CVE-2024-33663) | 10 | 0.40 (10 of 25) | 19, sealed | 49 minutes |
| `-cluster-run2/` | 7 | 0 | 0 | 0.48 (12 of 25) | 9, sealed | 62 minutes |
| `-cluster-run3/` | 14 | 0 | 8 | 0.44 (11 of 25) | 17, sealed | 66 minutes |

The first cluster run proved the key-confusion vulnerability and signed the evidence, but two stages
were re-run by hand on the same workspace: attest and assess had crashed on a package that was
analyzed and never selected. The re-run gave attest the selection explicitly and gave assess the
fix, which is that later stages only handle what the run executed. The second run went end to end
unaided and proved nothing. Same model, same
rules: the unit file it wrote imported a name the package does not have, and the generator shipped
it anyway because the keep step cut only tests named in the baseline failures, and a file that fails
to import names no test. That is register entry GF-020, with a check that now runs before every run. The third run carried
every fix and went end to end unaided: the unit file collected, eight tests were accepted and
signed, and none of the three CVE tests told the two versions apart. Three runs, same model, same
rules, one proof: at this model size the proof is a matter of attempts, which is what the
stronger-model rung is for.

Getting the pipeline through the cluster took ten runs. The first seven each stopped one stage further
than the last, on something the workstation never sees, and each fix is one commit:

| Stopped at | Cause | Fix |
|---|---|---|
| scheduling | Tekton lets a task pod bind one claim; three workspaces on three claims never scheduled | one shared workspace, three directories under it |
| intake | the stage pod referenced a secret by an empty name | every stage receives the model secret |
| intake | the clone and the harness run as different user ids, and git refused the checkout | stage pods tell git to trust the workspace |
| intake | a CI clone checks the revision out detached and never creates the branch name | intake resolves a name, then the remote's copy, then fetches it |
| generate | the isolation probe ran in a pod that is not the sandbox | stage pods skip the probe; the execute pod's first step is the probe |
| execute | the isolation probe installs one wheel and the sealed pod cannot download it | stage 0 fetches it into the shared workspace first |
| attest | later stages followed the analyzed package list, not the executed one | triage, packet, attest and assess only handle what the run executed |
| records | the pod's sandbox records had no image digest and the run record had shortened a branch name | the pod is told its own digest reference; only real paths are shortened |

## The test pull request (`-run6/propose/`)

Lifecycle B's last step, run on run 6: the harness put the seven accepted python-jose tests, the
packet, the draft VEX, the provenance record, the signed statement and the UDLM records on a branch of
the test overlay repository under its own identity and opened
[a pull request](https://github.com/croadfeldt/ai-test-harness-overlays/pull/1). The pull request's
text is the packet's plain-terms summary. The harness pushed that one branch and nothing else; the
overlay repository's main branch did not move; the commit is unsigned and says so, because no signing
key is configured on this install. `propose/python-jose/proposal.json` records the branch, the commit,
the files and the pull request; `pull-request.md` is the text as posted. A person decides from here.

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
.venv/bin/harness propose  --workdir $D --select python-jose   # the test pull request; needs [propose].repo, a checkout of the overlay repository
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
| `pr-fix-known-vulns-cluster/`, `-cluster-run2/`, `-cluster-run3/` | python-jose through the same pipeline as a Tekton PipelineRun on OpenShift, the execute pod as the sandbox; see "The same pipeline on a cluster" |

Inside a run: `intake/` (dependency graph, SBOM, work list), `analyze/` (facts per package),
`generate/` (candidate tests, every model prompt and response), `execute/` (results on both versions,
mutation), `triage/`, `packet/`, `attest/`, `assess/`, and `selfcheck/` (stage 0, run first). Large
raw files and downloaded packages are not committed; the commands above recreate them.
