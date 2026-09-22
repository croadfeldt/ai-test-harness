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

## Anything else

Any system that can run a command with two refs can trigger a run: a cron entry, a webhook receiver,
a person. `harness run` is the whole pipeline; the stage commands remain for running it a step at a
time. Every trigger produces the same artifacts and the same story, so a reviewer reads a run the
same way whatever started it.
