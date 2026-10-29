# Pilot plan

**Status:** 2026-10-29. The first two milestones of the [case](01-the-case.md) made operational: what to
stand up, in what order, what to measure, where each measure is read from, and who signs off. Re-sequenced on
2026-10-29 so the claim path comes first, matching the Lightwell AI Test Generation proof of concept; the pull
request path follows as milestone 2.
**Owner:** Chris Roadfeldt. **Team:** two to four engineers; durations are replaced by measured velocity.

## The shape

Two milestones of six weeks each, on example projects already building on a supported build platform.

**Milestone 1, the claim path.** One Python project. For every published fix claim that names a package the
project ships, from one feed the team already reads, the harness writes an exposure test at our call site and
a fix-pinning test that fails on the version we ship and passes on the claimed fix, runs both sealed on both
versions, and ends the claim in one verdict with its evidence: confirmed, disputed, not reachable, or could
not verify, with the provenance label of the claim on it. Each verdict becomes a draft VEX statement that
names the publisher's, for Product Security to confirm. The design is the
[verified fix ingestion use case](19-use-case-verified-fix-ingestion.md); the work items are its F1 to F9 and
the queue's Q19 and Q20, in the order the [MVP map](17-design-queue.md#the-mvp-map) gives.

**Milestone 2, the pull request path.** Two example projects, one Python and one Go, our own code and direct
dependencies, triggered from the pull request, review packets as pull request comments and a test pull
request per change. The person we serve is the one who approves the merge, the reviewer or engineering lead;
the measures that matter first are theirs.

Both milestones share the model endpoint, the sandbox image, the bot identity and the reference jobs, so
milestone 2 starts from a running system.

## Before the first run

| Week | What lands | Who provides it |
|---|---|---|
| 0 | A model endpoint per language, OpenAI-compatible, with the bench run on the reference jobs and the result on the evaluation table | Platform team, with the harness team running `harness bench` |
| 0 | A sandbox image per ecosystem, pinned by digest, built from `harness/Containerfile` or the team's equivalent | Harness team |
| 0 | A bot identity and signing key for the test pull request; a GitHub App identity if the verdict is to post as a required check | Platform team and security |
| 0 | The team's settings file in each pilot repository: what the testbed provides, repeats, mutation feedback, time budget per change, which gaps block | The project owners, with defaults explained |
| 1 | For milestone 1: the claim feed to follow, the SBOM store or directory that says what the project ships, and the publishers the team trusts, in the team's settings | The project owners with Product Security |
| 1 | For milestone 1: the sweep, from `deploy/`, running the harness on every new or changed claim and publishing to the runs store | Harness team with the project owners |
| 7 | For milestone 2: the trigger in each repository's own engine, from `deploy/`, running `harness run` on every pull request and publishing to the runs store | Harness team with the project owners |
| 1 | The pilot's own reference jobs: one fixed change per service whose answers are known, kept as the regression check for every later release | Harness team with the project owners |

Items that should land before week 1: F1, F3, F4, F5 and F6 from the use case, since nothing runs on a claim
without them, and Q8, the resolved configuration written into every run, so the team's settings are visible
in the evidence. Items that can land during milestone 1: Q19 and Q20, F7, Q11. Items for milestone 2: Q6,
the "Not covered" report with line notes; Q12, reviewer time from the forge timeline; Q7, the verdict as a
required check, once the identity decision is made.

## Milestone 1, weeks 1 to 6: the claim path

- **Weeks 1 and 2.** Every new or changed claim in the feed runs. The harness team reads every run's story
  and fixes what breaks; each new failure mode enters the register with its check before any fix. No default
  model or prompt changes except through the evaluation table.
- **Weeks 3 and 4.** Product Security is asked to read every draft VEX statement and say whether it would
  stand as the basis for theirs; a disputed claim's reproducer is handed to a person to confirm. The dashboard
  of claims received, verified, confirmed, disputed, not reachable and could not verify is shown weekly.
- **Weeks 5 and 6.** The exit measures are read, one verdict is consumed by a gate end to end, and the
  milestone's reference jobs, the published python-jose runs and one claim of the team's own, are rerun on
  the harness as it stands at the end.

## Milestone 2, weeks 7 to 12: the pull request path

- **Weeks 7 and 8.** Every pull request runs on both example projects. Same discipline: read every story,
  register before fix, no judgment changes to the defaults.
- **Weeks 9 and 10.** Reviewers are asked to decide on every test pull request, accept, edit or reject, so
  the feedback stage has decisions to read back. The dashboard is shown to the team weekly.
- **Weeks 11 and 12.** The exit measures are read, the pipeline findings on each service are handed to their
  owners, and the pilot's reference jobs are rerun on the harness as it stands at the end.

## Exit criteria, and where each is read

**Milestone 1.**

| Criterion | Where it is read | Who signs |
|---|---|---|
| Every claim in the feed for the packages in scope ended in exactly one verdict, with its reason and the claim's provenance label | The runs store: one run per claim and product, each with a story, a packet and a signed record; the dashboard's claim counts | Harness team |
| At least one disputed claim came with a reproducer a person confirmed | The run's story and the person's note on the finding | The person who confirmed it |
| Product Security accepted at least one of our VEX statements as the basis for theirs | Product Security's acknowledgement against the statement's id | Product Security |
| One verdict was consumed by a gate end to end: evidence attached to the change, read by policy, merge held or allowed on it | The gate's log against the run's signed record | The project's pipeline owner |
| Cost per claim is reported in tokens and CPU-minutes from the first run | Every run's model-call records and sandbox timings, rolled up on the dashboard | Harness team |
| The milestone's reference jobs are established and rerun without regression | `evaluation.json` for each reference job, the row on the evaluation table | Harness team |

**Milestone 2.**

| Criterion | Where it is read | Who signs |
|---|---|---|
| Every pull request in the pilot repositories arrived with its evidence | The runs store: one run per pull request, each with a story, a packet and a signed record | Harness team |
| Reviewer time per finding is measured and reported | The feedback records and the dashboard (Q12 lands it from the forge timeline; until then, measured by hand from the pull request timestamps) | The project owners |
| At least one finding a reviewer confirms would otherwise have been missed | A test pull request where the reviewer's accept carries that note; the run's story | The reviewer who confirms it |
| The share of proposed tests reviewers accepted is reported | `feedback/acceptance.json` per run, rolled up on the dashboard; no target set until there is a number | Harness team |
| The pilot's reference jobs are established and rerun without regression | `evaluation.json` for each reference job, the row on the evaluation table | Harness team |
| The default model and prompt stayed above the fitness floor | The evaluation table: the share of generated candidates that build, starting at 80 percent, set by the team from there | Harness team and platform team |
| The pipeline findings, if any, were handed to their owners | `triage/pipeline.json` per run, and the owners' acknowledgement | The project's pipeline owner |

## Targets and cost, stated up front

The initial targets are the blueprint's (reference, section 10): generated tests build more than 80 percent
of the time, the pilot's floor; flake rate of accepted tests under 1 percent; false `suspicious` findings
under 5 percent; reviewer acceptance above 70 percent of proposed tests; mutation score above 0.6 on the
sampled mutants. Reviewer time per finding is measured and reported, not targeted, until there is a
baseline. The harness runs beside the pull request pipeline and adds nothing to its critical path; the
verdict's arrival is bounded by the team's time budget. Cost is reported per pull request in tokens and
CPU-minutes from the first run, since every model call records its usage; the example runs cost half a
million to one and a quarter million prompt tokens per package change, a figure from one lab and two models
that the pilot replaces with its own.

## What the pilot does not do

It does not run on transitive dependencies, does not go beyond the one claim feed and the direct
dependencies in scope, does not publish a VEX statement, and does not merge anything. It does not change a model or prompt
default on judgment. It does not report timings as cost; it reports model time per run and lets the
platform team translate.

## After the pilot

Milestone 3 of the case, first-party at scale: every pull request in the pilot repositories, unattended,
with the test pull request as the standard path, and the claim sweep running on every product the SBOM store
knows. The decision to proceed rests on the exit measures above and on two answers: Product Security's, did
the evidence change what you would have published, and the reviewers', did it change what you would have
merged.
