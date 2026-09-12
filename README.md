# AI Test Harness

**A blueprint for using AI to generate, run, and prove tests for every piece of code we ship, including
the code we did not write.**

Author: Chris Roadfeldt. Status: working draft, September 2026.

Most of the software in any product today was written by someone else. A typical service pulls in
hundreds of open source packages, most of them several layers removed from anything our engineers ever
read. We test what we write. We trust what we import. This project is a plan to close that gap with AI
agents that write tests, run them in isolation, prove what they found, and hand the evidence to a human
to approve. Nothing merges without a person. Everything the harness produces is signed and traceable.

## Start here, by audience

| If you are | Read | Time |
|---|---|---|
| A CEO, managing director, board member, or anyone who wants the point without the mechanics | [Executive summary](docs/00-executive-summary.md) | 5 minutes |
| A CTO, VP of Engineering, or CISO deciding whether to fund this | [Executive summary](docs/00-executive-summary.md), then [The case](docs/01-the-case.md) and [Roadmap](docs/07-roadmap.md) | 20 minutes |
| An engineer, architect, or security analyst who will build or run it | [How it works](docs/02-how-it-works.md), then [Blueprint](docs/03-blueprint.md), [Capability map](docs/05-capability-map.md), [Workflows and RACI](docs/06-workflows-and-raci.md) | 2 hours |
| A member of the public, a journalist, a student, or a customer | [Executive summary](docs/00-executive-summary.md) and [Glossary](docs/08-glossary.md) | 10 minutes |
| Someone presenting this | [Slide deck](slides/deck.md), 25 slides | 30 minutes |

## Three layers

1. **The blueprint** (`docs/`, `blueprint/`) says what the harness must do and why.
2. **An opinionated implementation** (`harness/`) makes the capability map's primary choices concrete
   in code, one ecosystem adapter at a time, starting with Python.
3. **Examples** (`examples/`) hold what that implementation produced when it reacted to real commits in
   real repositories, plus a post-analysis of whether the run met the blueprint's core goals. Every file
   under `examples/` is harness output. None of it is written by hand.

## What is in this repository

```
docs/
  00-executive-summary.md    The point, in one page
  01-the-case.md             Why, what it costs, what it returns, what could go wrong
  02-how-it-works.md         The pipeline explained with diagrams
  03-blueprint.md            The full technical plan
  04-landscape.md            Every existing open source project we reuse, learn from, or avoid
  05-capability-map.md       Each capability we need, mapped to the software that fills it, and the orchestration choice
  06-workflows-and-raci.md   A process map and a RACI for every stage and lifecycle event
  07-roadmap.md              Phases, exit criteria, and what "done" means
  08-glossary.md             Plain-language definitions
  09-language-and-target-flows.md  Creation and execution flows per language, on Kubernetes, Podman, VM, bare metal
slides/
  deck.md                    A slide deck in markdown with Mermaid diagrams
blueprint/
  adapter-interface.md       The contract each language ecosystem adapter implements
  manifest.schema.yaml       The provenance record every generated test carries
  test-evidence-predicate.json  The in-toto attestation predicate
  pipeline-skeleton.yaml     A Tekton pipeline outline for Konflux
diagrams/
  *.mmd                      Mermaid sources for every diagram, reusable in slides
harness/
  src/harness/               The implementation: cli, model, risk, adapters/, sources/, stages/
  tests/                     Unit tests for the parts that need no network
examples/
  frc-scheduler-server/      Two runs against a real FastAPI service: a scheduled rescan and a dependency-fix PR
tools/
  build-site.py              Builds a single-page HTML site from docs/ and blueprint/ into site/ (git-ignored)
  site.css, site.js          Styling and audience-path navigation for that page
```

To build the web version locally: `python3 tools/build-site.py` (needs the `markdown` Python package), then
open `site/index.html`. Mermaid blocks are emitted as `<pre class="mermaid">` for any Mermaid-aware host.

All diagrams are Mermaid and render directly on GitHub. The slide deck is plain markdown that Slidev
renders with Mermaid support out of the box; Marp works with its Mermaid plugin.

## The one-paragraph version

Every incoming change, whether a pull request from our own team or a version bump of a package five
layers deep, goes through the same stages: the harness verifies itself, then intake, analysis, generation,
execution, triage, review, and feedback. AI agents write the tests, in the framework and layout each repository already uses so they run with the
team's existing commands and CI. Sandboxes run them with no network and no secrets. Mutation
testing proves the tests are strong. A differential run against the previous version shows what changed.
Everything is classified, attached to a signed provenance record, and handed to a reviewer. Tests that
earn their keep are promoted into our standard suite. Tests that code changes have made irrelevant are
retired. Known vulnerabilities get targeted tests whose results become draft VEX statements for Product
Security to confirm. The whole thing runs on Konflux and targets SLSA Build Level 3.

## Status and how to contribute

The blueprint is complete for review. The implementation covers intake and analysis; generation and execution are next. Open decisions are listed in
[the blueprint, section 15](docs/03-blueprint.md#15-open-questions). Comments, corrections, and pull
requests against any document are welcome. I would especially like to hear from maintainers of the
projects named in the [landscape](docs/04-landscape.md) if I have described their work inaccurately.

## License

Documentation and blueprint files in this repository are licensed under Apache-2.0. See [LICENSE](LICENSE).
