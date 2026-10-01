---
name: ai-test-harness
description: Run the AI Test Harness on the change in front of you and read its verdict. Use when a developer asks for tests on their branch, on a dependency bump, or on a known vulnerability, or asks whether a change is safe to merge; the harness generates, runs and scores tests in a sealed sandbox and proposes them through a pull request, never merging.
---

# AI Test Harness

The harness writes, runs and scores tests for a change, first-party code or any dependency, in a sealed
sandbox, and hands a person the evidence. You run it and read its story; you never merge for it.

## When to use

- The developer asks for tests on the branch they are working on, or on a dependency they just bumped.
- A known vulnerability was fixed or introduced by a version change and someone asks whether it is proven.
- Someone asks whether a change is safe to merge and the existing suite does not touch what changed.

Do not use it as a plain test runner, and do not read generated tests before they have run: they are
untrusted until the sandbox has executed them.

## How to run it

The harness needs `podman` on the machine and a model endpoint in the environment or in
`harness/harness.local.toml` (`HARNESS_MODEL_BASE_URL`, `HARNESS_MODEL`, optionally `HARNESS_MODEL_API_KEY`).
Install once:

```
python3 -m pip install "git+https://github.com/croadfeldt/ai-test-harness.git#subdirectory=harness"
```

One command runs every stage on a change. Point it at the repository (a path or a git URL) and two refs:

```
harness run --repo . --base main --head "$(git branch --show-current)" --workdir out/harness
```

Omit `--base` for a rescan of one ref. `--target first-party` tests the application's own code, `all`
does dependencies too. `--select <package>` narrows to one package. Expect minutes to hours; the time is
model time.

## How to read the result

Open `out/harness/README.md` first. It is the run's story: who, what, why, where, when; the verdict in
plain terms; the decisions the harness made; the actions it took and, by design, did not take; the
records in plain terms; and every file with the reader it is for. Then, per package:

- `packet/<package>/packet.md`: the review packet, one row per test with its verdict on both versions.
- `packet/<package>/pull-request.md`: what the test pull request would carry.
- `triage/pipeline.json`: what the harness found about the repository's own CI, with the change that corrects each finding.

A fix is proven only by a test that fails on the vulnerable version and passes on the fixed one. "Unproven"
is stated, never hidden. Report the story's plain-terms sentence to the developer, then the findings.

## Proposing the tests

With an overlay repository configured (`[propose].repo` or `HARNESS_OVERLAY_REPO`) and a token in
`GH_TOKEN` or `GITLAB_TOKEN`, `harness propose --workdir out/harness` pushes one branch and opens the
pull request. First-party tests go to the application's repository against the change's own branch.
Nothing is merged by the harness; tell the developer the request is theirs to review.

## Rules you keep

- Never run generated tests outside the harness's sandbox.
- Never edit, merge or approve the pull request the harness opened.
- Never present an unproven fix as proven; quote the story's wording.
- If a stage fails, read `out/harness/selfcheck/selfcheck.json` and the stage's log before retrying; the
  failure register (document 15) names the known ones.
