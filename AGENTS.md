# For AI agents working in this repository

You are reading the AI Test Harness: a blueprint and an example implementation of a pipeline in which AI
writes tests for every change entering the software supply chain, runs them sealed against both the old
and the new version, and hands a person signed evidence. This page is for an assistant or coding agent
that has been pointed at the repository. People start at [README.md](README.md).

## What is where

| Path | What it is |
|---|---|
| `docs/00` to `docs/03` | Executive summary, business case, how it works, the blueprint in three pages |
| `docs/14` | The specification: what an implementation must do, and the test that proves each requirement |
| `docs/15`, `docs/16` | The failure register; the long-form reference behind the blueprint (a reference, not a read-through) |
| `docs/17`, `docs/18` | The design queue (what remains to build) and the research behind each item |
| `docs/10` | How to read a run's output, per reader |
| `harness/` | The implementation: `src/harness/stages/` one module per stage, `adapters/` one per language, `tests/` |
| `harness/prompts/` | Every text the harness says to a model, under source control, digested |
| `examples/` | Real runs. Every file is harness output; none is written by hand |
| `deploy/` | Triggers for GitHub Actions, GitLab CI, Jenkins, Azure Pipelines, Tekton |
| `skills/ai-test-harness/` | The Agent Skill: how to run the harness from inside a coding agent |
| `tools/` | The site, the dashboard, the catalogue and the evaluation table generators |

## Rules that hold everywhere

- **The harness only tests.** It never fixes production code, merges, publishes a VEX statement or deletes a
  test. Do not add code that does. A separate fix pipeline consumes what it hands over.
- **Nothing about a machine, a network or an account goes in this repository.** Endpoints, hosts, paths and
  credentials appear by label and digest only; the local configuration file is git-ignored. Material from the
  maintainer's employer's internal programmes stays out.
- **Generated output is never hand-edited.** Change the code, then regenerate: `python3 tools/run-index.py`
  for the examples' indexes and stories, `python3 tools/build-site.py` for the site, the catalogue and the
  evaluation table. The tests check that the catalogue in `docs/10` matches the code.
- **Documents stay in sync with every change.** A new capability lands with its row in the implementation
  README, its line in the design queue, and the specification row that names its test. The blueprint's design
  (`docs/03`, `docs/16`) does not change without the maintainer's decision; it stands at v0.28.
- **Product agnostic.** The harness runs in the build platform a team already has. Konflux, Tekton, Conforma and
  Trustify appear as examples, "in the example", never as the assumption; the same for any vendor product.
- **Every claim carries its evidence.** A number in a document points at the file it came from. A claim about
  another tool carries its source. The harness's own timings are not evidence of cost; they came from one
  lab.
- **The maintainer runs anything that touches a model, a GPU or a cluster.** An agent does not start model
  runs, bench runs or cluster changes on its own; it prepares them and says what to run.

## How to work

- Python 3.12, a virtual environment under `harness/.venv`, `pip install -e ".[dev]"` in `harness/`. Run
  `pytest -q` there; the suite is the contract and must stay green. `harness selfcheck --no-probes` runs
  the failure register's checks without a sandbox or a model.
- The Go helper under `harness/src/harness/adapters/gohelper/` builds with the toolchain on the machine;
  tests that need it skip when it is absent.
- One pull request is one complete thing, small enough to read, based on `main`, never chained on another
  open branch. The maintainer merges by rebase, so a follow-up fix is a new pull request, not a push to a
  merged branch. CI must be green before you report done.
- Tests first for a new failure mode: a register entry and a self-check that fails, then the correction.

## How to write

Plain English, for a named reader, in the maintainer's first-person voice. Short sentences, one idea each.
No em-dashes. Say what a reference decided, not just its number. Lead with the outcome; cut what does not
move a decision. A reader who knows the domain but did not watch the work must be able to act on the
message alone.

## Where to look first for common tasks

- Understand a run: `docs/10-reading-the-artifacts.md`, then an example's `README.md`.
- Add a language: `blueprint/adapter-interface.md`, then `harness/src/harness/adapters/`.
- Pick up a queue item: `docs/17-design-queue.md`, then the matching section of `docs/18`.
- Change what the model is told: `harness/prompts/` and `docs/12`; a new prompt set is measured before it
  becomes a default.
