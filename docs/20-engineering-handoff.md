# Engineering handoff

**Status:** 2026-10-14, against the blueprint at v0.28 and the implementation on `main`.
**For:** the engineering team that takes this on. Two pages: what exists, what it maps to, how to run it,
how to extend it, what it needs from you, and what is known not to work.

## What you are taking on

A blueprint and a working example implementation of it. The blueprint is the three-page
[document 03](03-blueprint.md), with the [specification](14-specification.md) listing the twenty-seven
things an implementation must do and the test that proves each. The implementation under `harness/`
does all twenty-seven, for Python and Go, on a laptop with Podman and as a Tekton pipeline on
Kubernetes. It has run end to end on two real repositories; every run is under `examples/` and on the
[site](https://croadfeldt.github.io/ai-test-harness/), and nothing there is written by hand.

Treat the implementation as the proof of the blueprint, not as the product. It is honest about what it
has not done, and the test suite is the contract: 130 tests, green on every merge.

## Stage by stage: what exists, where, and what proves it

| Stage | Module | Proves it | State |
|---|---|---|---|
| 0 Self-verification | `selfcheck.py` | `test_selfcheck` | Built. 28 register checks, sandbox and model probes |
| 1 Intake | `stages/intake.py`, `sources/osv.py`, `sources/pypi.py` | `test_graph`, `test_intake_fresh`, `test_repo_url` | Built. Repository by path or URL, two refs, graph in the target's interpreter, OSV, pre-flight |
| 2 Analysis | `stages/analyze.py`, `sources/ci.py`, `adapters/*` | `test_api_diff`, `test_call_sites`, `test_pipeline_facts`, `test_static_findings`, `test_behaviours` | Built. API diff, call sites, advisories, `bandit`/`gosec`, GuardDog, CI facts, behaviour worklist, risk score. Not built: call-graph reachability |
| 3 Generation | `stages/generate.py`, `stages/agent.py`, `prompts.py` | `test_agent_gate`, `test_keep_best_attempt`, `test_mutation_feedback`, `test_declared_needs` | Built. Fixed loop and tool-using agent, prompt sets, mutation feedback, declared needs withheld |
| 4 Validation execution | `stages/execute.py`, `sandbox.py`, `sandbox_go.py`, `stages/mutate.py`, `stages/relevance.py` | `test_verdicts`, `test_repeats`, `test_testbed_failure`, `test_go_per_test`, `test_mutation_sites_executed_only`, `test_relevance` | Built. Both versions sealed, five repeats, per-test coverage, stratified mutation, differential, relevance. Not built: a Kata testbed for the `machine` tier |
| 5 Triage and accounting | `stages/triage.py`, `stages/account.py` | `test_accounting`, `test_accounting_strength` | Built. Classes, confidence, routes; three-state accounting with closures |
| 6 Review | `stages/packet.py`, `stages/attest.py`, `stages/udlm_records.py`, `stages/propose.py`, `sources/forge.py` | `test_packet_vex_case`, `test_udlm_records`, `test_propose`, `test_forge` | Built. Packet, VEX drafts, in-toto DSSE, UDLM records, pull request on GitHub or GitLab. Not built: the verdict as a required check with annotations (queue Q7) |
| 7 Feedback | `stages/feedback.py`, `stages/evaluate.py`, `stages/bench.py`, `stages/publish.py` | `test_feedback`, `test_prompts_and_evaluate`, `test_publish_and_dashboard` | Built. Decisions read back, evaluation table, bench, runs store, dashboard. Not built: reviewer time per finding (Q12) |
| Story and index | `story.py`, `runindex.py`, `tools/` | `test_story`, `test_runindex` | Built. Every run tells its story; the catalogue names every file's reader |

The command line exposes every stage (`harness <stage>`) and `harness run` for all of them in order.
`harness evaluate`, `bench`, `propose`, `feedback` and `publish` are the lifecycle commands around them.

## How to run it

1. Python 3.12, Podman, and for Go the toolchain. `cd harness && python -m venv .venv && . .venv/bin/activate
   && pip install -e ".[dev]"`. `pytest -q` must pass before anything else.
2. Copy `harness.example.toml` to `harness.local.toml` (git-ignored) and set the model endpoint and the
   target repository. The example file documents every setting and the environment variable that
   overrides it; the sandbox, repeats, mutation feedback and provides settings are the team's.
3. `harness selfcheck` with a sandbox and a model reachable; then `harness run --repo <url> --base <ref>
   --head <ref>`. Read the run's `README.md` first; [document 10](10-reading-the-artifacts.md) says what
   each reader opens next.
4. In CI, pick the trigger under `deploy/` for your engine, GitHub Actions, GitLab CI, Jenkins, Azure
   Pipelines, Tekton or a plain script, and follow [document 13](13-running-on-real-repositories.md). The
   image carries the Go toolchain, the helper, `bandit`, `gosec` and GuardDog.

## How to extend it

- **A new ecosystem** is one adapter: implement the functions in `blueprint/adapter-interface.md` the way
  `adapters/python.py` and `adapters/go.py` do, resolve, unpack, API surface with end lines, internals and
  behaviours, call sites, test file inspection, sandbox runner, coverage files, mutation kit. The core
  never looks inside a language.
- **A new prompt set** is a TOML under `harness/prompts/` overriding named texts. It becomes the default
  only after `harness bench` has measured it against the current one on the reference jobs.
- **A new failure mode** is a register entry in [document 15](15-failure-register.md) and a self-check in
  `selfcheck.py` that fails first, then the correction. The register is the harness's own test suite.
- **A queue item** starts from its row in [document 17](17-design-queue.md) and the research behind it
  in [document 18](18-design-queue-research.md). Each is sized for one pull request.

## What it needs from you

- **A model endpoint**, OpenAI-compatible, with a documented rung per language. The published table in
  [document 12](12-prompt-and-model-evaluation.md) shows what a 27B dense model and a 235B mixture did:
  the small one wrote no usable Go. Fitness is measured, not assumed; run the bench before you trust a
  default.
- **A sandbox image** per ecosystem, pinned and recorded by digest; the one in `harness/Containerfile` is
  the example.
- **A bot identity and a signing key** for the test pull request, and a GitHub App identity if the verdict
  is to post as a check with annotations (queue Q7, the one decision outstanding).
- **The test overlay repository** for dependency tests, if you want them outside the application's own
  repository; first-party tests go to the repository under test.
- **Compute time.** Model time dominates; everything else is small beside it and scales with the inference
  hardware you give it.

## Known not to work, or not yet

- The `machine` testbed tier has no runtime on a VM-hosted Kubernetes cluster; such tests are handed to
  the team's pipeline with the declaration.
- Call-graph reachability is not built; reachability is the application's call sites plus hints, and the
  record says "unknown" where it is.
- The published example runs still carry the first accounting; re-running them under the current rules
  waits for compute time. Expect "validated" to read lower than "accepted" everywhere; that is the point.
- The verdict reaches the pull request as text and a patch, not yet as a required check (Q7). The
  environment-aware planner (Q9), the resolved configuration (Q8), reviewer time (Q12) and the "Not
  covered" report with line notes (Q6) are the remaining queue items; none changes the design.
- Everything measured so far came from one lab on consumer hardware. The numbers are the harness's
  honesty about itself, not a benchmark of what it costs you.
