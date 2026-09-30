# Running it on real repositories

**For:** the engineer wiring the harness into a repository's pipeline, and the reviewer who wants to
know what will run when. One command, any git repository, any ref; then the triggers that call it
from GitHub Actions, GitLab CI, Tekton, or a schedule. The human gate is unchanged: the harness only
proposes, a person merges.

## One command, one change

```
harness run --repo https://github.com/org/app.git --base main --head refs/pull/123/head --workdir out/pr-123
```

That runs every stage in order on the difference between the pull request and its base: intake,
analysis, generation, execution, mutation, relevance, triage, packet, attestation, assessment. The
work directory ends with the story at its top (`README.md`), the review packet and the pull request
text under `packet/`, and the signed records under `attest/`. Add `--propose` to open the test pull
request on the overlay repository afterwards; the harness pushes one branch and never merges.

`--repo` takes a path on the machine or a git URL (https, ssh, file). A URL is cloned once under the
run's cache and fetched on later calls; the harness checks its own clone out at the change and never
touches a checkout it did not make. `--head` and `--base` take anything git can name on that
repository:

| You want to test | `--base` | `--head` |
|---|---|---|
| A pull request against its base branch | `main` | `refs/pull/123/head` (GitHub), `refs/merge-requests/123/head` (GitLab) |
| A push to the base branch, against what was there before | the previous commit | the new commit |
| A branch against the trunk | `main` | `feature/x` |
| A release, against the last one | `v1.4.0` | `refs/tags/v1.5.0` |
| The current state of a branch, no change under review (a rescan) | omitted | `main` |

Pull request refs are fetched by name, so the harness never needs the branch to exist locally, and
the repository name in every record comes from the URL, not from the directory it was cloned into.

`--target first-party` tests the repository's own code instead of its dependencies; `all` does both.
`--select` narrows to named packages; without it, every package the change touched or that carries
an advisory is in scope, at the budget its risk score earned.

## What every trigger needs

- **The harness** with its sandbox: `pip install` from this repository, plus podman on the runner, or
  the container image with the `pod` sandbox target inside a cluster. Generated tests run before
  anyone has read them, so a runner without a sealed sandbox is not an option.
- **A model endpoint**: `HARNESS_MODEL_BASE_URL`, `HARNESS_MODEL`, and a key if the endpoint wants
  one, from the platform's secret store. The endpoint's address is recorded only as a label and a
  digest.
- **Somewhere for the output**: the work directory as a build artifact, and, in the pipeline's loop,
  credentials for the overlay repository so `--propose` can open the test pull request.
- **Time**: budget an hour or more for a package with advisories on a served model; the run is
  validation, not the suite's regression run, and it happens once per change.

## GitHub Actions

`deploy/github-actions/ai-test-harness.yml` is a complete workflow. It runs on three triggers:

- `pull_request`: base is the pull request's base branch, head is the pull request's head ref. The
  packet's verdict in plain terms is posted as a comment on the pull request; the run directory is
  uploaded as an artifact. Nothing is merged.
- `push` to the default branch: base is the commit before the push, head is the pushed commit.
- `schedule`: a rescan of the default branch, so advisories published since the last change still
  produce tests.

`workflow_dispatch` lets a person run any two refs by hand. Secrets: the model endpoint and key,
and a token with write access to the overlay repository if the workflow proposes.

## GitLab CI

`deploy/gitlab-ci/ai-test-harness.gitlab-ci.yml` does the same with GitLab's variables: on a merge
request, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` is the base and `refs/merge-requests/<iid>/head` the
head; on a push to the default branch, `CI_COMMIT_BEFORE_SHA` and `CI_COMMIT_SHA`; on a pipeline
schedule, a rescan. The run directory is a job artifact; the verdict goes to the merge request as a
note through the API.

## Tekton, on OpenShift

The pipeline in `deploy/tekton/` already takes `repo-url`, `base` and `head` as parameters. The
triggers under `deploy/tekton/triggers/` connect a GitHub webhook to it: an EventListener receives
the event, a TriggerBinding maps a pull request's base and head ref (or a push's before and after
commits) onto the parameters, and a TriggerTemplate creates the PipelineRun. The same pipeline runs
on a schedule as a CronJob that creates a PipelineRun with `head` set to the default branch and no
`base`.

## What the harness says about the pipeline it runs in

Fitting into a repository's CI is the default; fitting in silently is not. Every run reads the CI
definitions at the reviewed commit and states, as findings routed to the pipeline's owners, where that
CI is provably short of what validating a test needs. Two questions today:

- **Can untrusted code reach secrets or the network while tests run?** A pull request checked out under
  the base repository's secrets, write permissions on a pull request workflow, actions resolved by a
  mutable tag, a download piped to a shell, a test job with repository secrets in its environment, a
  self-hosted runner for pull requests, a floating image tag, a privileged step. Each finding names
  the file, what was found, and the change that corrects it. A repository with no CI at all is a
  finding too.
- **Does the existing suite reach what changed?** For each package in scope the harness counts the
  repository's own test files that reference it and those that reach the symbols the change altered.
  Zero, where the application reaches the package in production, is a coverage gap with the call sites
  to test.

They appear in the packet under "The pipeline this change runs through", in the story's decisions, and
in `triage/pipeline.json`. The harness changes nothing in the pipeline; the owners decide. The harness
reads its own workflows the same way, and reports that its actions are pinned by tag.

## Opening the test pull request from CI

The pipeline's loop ends with the test pull request, and every engine can open it. What a run needs:

- **Where the tests go.** Dependency tests go to the test overlay repository: `HARNESS_OVERLAY_REPO`
  (a checkout) or the `HARNESS_OVERLAY_URL` the examples clone. First-party tests go to the repository
  under test, as a request against the change's own branch, so they land in the developer's pull
  request; against the default branch when the change was a commit or a pull request ref.
- **A token** that can push a branch and open a request there: `GH_TOKEN` for GitHub, `GITLAB_TOKEN`
  for GitLab, or `HARNESS_FORGE_TOKEN` in the examples, which set both. The harness uses `gh` or
  `glab` when present and the forge's API when not; any other forge gets the pushed branch and a
  message to open the request by hand.
- **An identity**: `HARNESS_PROPOSE_AUTHOR` and `HARNESS_PROPOSE_EMAIL`, the bot the requests are
  authored under, and optionally a signing key (`[propose].sign`).

The request's text is the packet's plain-terms verdict, the numbers, the file list, and the run's story
folded below it, so a reviewer has the whole account without leaving the request. The harness pushes
that one branch and nothing else, and it never merges.

| Engine | Example | Trigger and refs | Opens the request |
|---|---|---|---|
| GitHub Actions | `deploy/github-actions/ai-test-harness.yml` | pull request, push to main, weekly, by hand | when the variable `HARNESS_OVERLAY_REPO` and the secret `HARNESS_OVERLAY_TOKEN` are set |
| GitLab CI | `deploy/gitlab-ci/ai-test-harness.gitlab-ci.yml` | merge request, push to the default branch, schedule | when `HARNESS_OVERLAY_URL` and `HARNESS_FORGE_TOKEN` are CI variables |
| Jenkins | `deploy/jenkins/Jenkinsfile` | multibranch or pull request job | with the `harness-forge-token` credential |
| Azure Pipelines | `deploy/azure-pipelines/azure-pipelines.yml` | pull request, push, schedule | from the `ai-test-harness` variable group |
| Tekton on OpenShift | `deploy/tekton/` | webhook and CronJob (`triggers/`) | the `propose` task when the `propose` parameter is `true`, with the `harness-forge` secret |
| Anything else | `deploy/generic/run-and-propose.sh` | whatever the engine passes as two refs | when `HARNESS_OVERLAY_URL` and `HARNESS_FORGE_TOKEN` are set |

Every example does the same five things: install the harness, run every stage on the two refs the
event implies, keep the run directory as the build's artifact, post the plain-terms verdict where the
change is reviewed, and open the test pull request. With `HARNESS_RUNS_STORE` set they do a sixth:
publish the run's index and story to the runs store, so it appears on the dashboard. The generic script is those five steps in shell;
the others are the same steps in each engine's own syntax.

## From a developer's assistant

`skills/ai-test-harness/` is an Agent Skill: the instructions a coding agent such as Claude Code loads
to run the harness on the branch in front of the developer, read the story, and propose the tests,
keeping the rules (sealed sandbox only, nothing merged, unproven stated as unproven). Copy it into
`.claude/skills/` and lifecycle A is one instruction away.

## Anything else

Any system that can run a command with two refs can trigger a run: a cron entry, a webhook receiver,
a person. `harness run` is the whole pipeline; the stage commands remain for running it a step at a
time. Every trigger produces the same artifacts and the same story, so a reviewer reads a run the
same way whatever started it.
