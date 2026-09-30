#!/usr/bin/env bash
# The whole harness loop as one script, for any CI engine that can run a shell step: install, run every
# stage on two refs, keep the run directory as the artifact, post the verdict where the change is
# reviewed, and open the test pull request. GitHub Actions, GitLab CI, Jenkins, Azure Pipelines and
# Tekton examples in the sibling directories are this script in each engine's own syntax.
#
# Inputs (environment):
#   HARNESS_REPO_URL      the repository under test (git URL)            required
#   HARNESS_HEAD          the change: branch, tag, commit, refs/pull/N/head required
#   HARNESS_BASE          the last known-good ref; empty for a rescan    optional
#   HARNESS_MODEL_BASE_URL, HARNESS_MODEL, HARNESS_MODEL_API_KEY           the model endpoint (secrets)
#   HARNESS_OVERLAY_URL   the test overlay repository (git URL)          optional; without it no request is opened
#   HARNESS_FORGE_TOKEN   a token that can push a branch and open a request on the overlay repository
#                         (and on the repository under test, for first-party changes)
#   HARNESS_PROPOSE_AUTHOR, HARNESS_PROPOSE_EMAIL  the bot identity the request is authored under
#   HARNESS_WORKDIR       where the run lives                             default: run
set -euo pipefail
: "${HARNESS_REPO_URL:?}" "${HARNESS_HEAD:?}"
WORKDIR="${HARNESS_WORKDIR:-run}"

python3 -m pip install --quiet "git+https://github.com/croadfeldt/ai-test-harness.git#subdirectory=harness"
command -v podman >/dev/null || { echo "podman is required: generated tests run only in a sealed sandbox"; exit 2; }

harness run --repo "$HARNESS_REPO_URL" ${HARNESS_BASE:+--base "$HARNESS_BASE"} --head "$HARNESS_HEAD" --workdir "$WORKDIR"

# The verdict in plain terms, for a comment on the change under review (the engine posts it).
sed -n '3p' "$WORKDIR"/packet/*/pull-request.md 2>/dev/null > "$WORKDIR/verdict.txt" || true

if [[ -n "${HARNESS_OVERLAY_URL:-}" && -n "${HARNESS_FORGE_TOKEN:-}" ]]; then
  # Clone the overlay repository with the token, never storing it: a one-shot credential helper.
  git -c credential.helper='!f() { echo "username=x-access-token"; echo "password=$HARNESS_FORGE_TOKEN"; }; f' \
      clone --quiet "$HARNESS_OVERLAY_URL" "$WORKDIR-overlay"
  export GH_TOKEN="$HARNESS_FORGE_TOKEN" GITLAB_TOKEN="$HARNESS_FORGE_TOKEN"
  export HARNESS_PROPOSE_AUTHOR="${HARNESS_PROPOSE_AUTHOR:-AI Test Harness}" HARNESS_PROPOSE_EMAIL="${HARNESS_PROPOSE_EMAIL:-ai-test-harness@example.invalid}"
  git -C "$WORKDIR-overlay" config credential.helper '!f() { echo "username=x-access-token"; echo "password=$HARNESS_FORGE_TOKEN"; }; f'
  harness propose --workdir "$WORKDIR" --overlay-repo "$WORKDIR-overlay"
fi
echo "run: $WORKDIR/README.md"
