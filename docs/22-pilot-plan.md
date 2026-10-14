# Pilot plan

**Status:** 2026-10-14. The first milestone of the [case](01-the-case.md) made operational: what to stand
up, in what order, what to measure, where each measure is read from, and who signs off.
**Owner:** Chris Roadfeldt. **Team:** two to four engineers; durations are replaced by measured velocity.

## The shape

Six weeks, two example projects already building on a supported build platform, one Python and one
Go,
our own code and direct dependencies, triggered from the pull request, review packets as pull request
comments and a test pull request per change. The person we serve is the one who approves the merge, the
reviewer or engineering lead; the measures that matter first are theirs.

## Before the first run

| Week | What lands | Who provides it |
|---|---|---|
| 0 | A model endpoint per language, OpenAI-compatible, with the bench run on the reference jobs and the result on the evaluation table | Platform team, with the harness team running `harness bench` |
| 0 | A sandbox image per ecosystem, pinned by digest, built from `harness/Containerfile` or the team's equivalent | Harness team |
| 0 | A bot identity and signing key for the test pull request; a GitHub App identity if the verdict is to post as a required check | Platform team and security |
| 0 | The team's settings file in each pilot repository: what the testbed provides, repeats, mutation feedback, time budget per change, which gaps block | The project owners, with defaults explained |
| 1 | The trigger in each repository's own engine, from `deploy/`, running `harness run` on every pull request and publishing to the runs store | Harness team with the project owners |
| 1 | The pilot's own reference jobs: one fixed change per service whose answers are known, kept as the regression check for every later release | Harness team with the project owners |

Queue items that should land before week 1: Q8, the resolved configuration written into every run, so the
team's settings are visible in the evidence. Items that can land during the pilot: Q6, the "Not covered"
report with line notes; Q12, reviewer time from the forge timeline; Q7, the verdict as a required check,
once the identity decision is made.

## Weeks 1 to 6

- **Weeks 1 and 2.** Every pull request runs. The harness team reads every run's story and fixes what
  breaks; each new failure mode enters the register with its check before any fix. No default model or
  prompt changes except through the evaluation table.
- **Weeks 3 and 4.** Reviewers are asked to decide on every test pull request, accept, edit or reject, so
  the feedback stage has decisions to read back. The dashboard is shown to the team weekly.
- **Weeks 5 and 6.** The exit measures are read, the pipeline findings on each service are handed to their
  owners, and the pilot's reference jobs are rerun on the harness as it stands at the end.

## Exit criteria, and where each is read

| Criterion | Where it is read | Who signs |
|---|---|---|
| Every pull request in the pilot repositories arrived with its evidence | The runs store: one run per pull request, each with a story, a packet and a signed record | Harness team |
| Reviewer time per finding is measured and reported | The feedback records and the dashboard (Q12 lands it from the forge timeline; until then, measured by hand from the pull request timestamps) | The project owners |
| At least one finding a reviewer confirms would otherwise have been missed | A test pull request where the reviewer's accept carries that note; the run's story | The reviewer who confirms it |
| The share of proposed tests reviewers accepted is reported | `feedback/acceptance.json` per run, rolled up on the dashboard; no target set until there is a number | Harness team |
| The pilot's reference jobs are established and rerun without regression | `evaluation.json` for each reference job, the row on the evaluation table | Harness team |
| The default model and prompt stayed above the fitness floor | The evaluation table: the share of generated candidates that build, starting at 80 percent, set by the team from there | Harness team and platform team |
| The pipeline findings, if any, were handed to their owners | `triage/pipeline.json` per run, and the owners' acknowledgement | The project's pipeline owner |

## What the pilot does not do

It does not run on transitive dependencies, does not open vulnerability-targeted tests against advisories
beyond the direct dependencies in scope, and does not merge anything. It does not change a model or prompt
default on judgment. It does not report timings as cost; it reports model time per run and lets the
platform team translate.

## After the pilot

Milestone 2 of the case, first-party at scale: every pull request in the pilot repositories, unattended,
with the test pull request as the standard path. The decision to proceed rests on the exit measures above
and on the reviewers' answer to one question: did the evidence change what you would have merged.
