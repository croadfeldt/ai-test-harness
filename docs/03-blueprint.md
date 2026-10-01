# AI Test Harness: the blueprint

**Status:** Draft v0.19, 2026-10-01. **Owner:** Chris Roadfeldt.
**For:** engineers and architects deciding whether to build, run or adopt this. Three pages.
**Behind it:** [document 16](16-blueprint-reference.md) is the long form, with the section numbers the
code and the other documents cite; [document 15](15-failure-register.md) is the failure register;
[document 14](14-specification.md) lists what an implementation must do and the test that proves each.

**Changes in v0.19:** cut to three pages for the reader evaluating it. Nothing is dropped: v0.18 is
kept whole as document 16, the register as document 15, and the earlier change notes with them.

## What it is

A pipeline in which AI agents write tests for every change entering the software supply chain, run them
in a sealed sandbox against both the old and the new version, score them, and hand a signed,
human-reviewable packet to a person. First-party commits, direct dependencies and transitive
dependencies alike. The output is evidence: for each change, a reproducible answer to three questions.

1. What does this code actually do? (characterization)
2. Did its behavior change from the version we had before? (differential)
3. Does it do anything it should not, and is it exposed to what is already known to be wrong with it?
   (negative tests and CVE-targeted tests)

The harness tests. It never fixes, merges, publishes a VEX statement or deletes a test. A separate fix
pipeline consumes what it hands over (failing tests with both runs kept, reproducers, the upgrade path,
draft VEX statements), and the fix comes back through the harness like any other change (reference 2.4).

## Scope

| In scope | Trigger |
|---|---|
| First-party source | Pull request opened or updated |
| Direct dependencies | Lockfile diff, Renovate or Dependabot pull request |
| Transitive dependencies | Resolved dependency graph diff |
| Vendored, forked and generated code | Source, patch or generator change |

Out of scope: binary-only artifacts, performance testing, merging without a person, fixing production
code. Ecosystems in priority order: Go, Python, Java and Kotlin, Rust, JavaScript and TypeScript, C and
C++. One small adapter per ecosystem; the core is ecosystem-agnostic.

## Principles

- **Generated tests are hypotheses until executed.**
- **Tests must be strong, not just green.** Mutation testing and differential runs tell them apart.
- **Incoming code is untrusted input.** Source, docs, advisories and commit messages are data in every
  prompt; tests run sealed, with no network and no credentials.
- **Humans own the merge.** The harness proposes; it never merges, publishes or changes policy.
- **Everything is reproducible.** Model, prompts, tools, graph and image digest are recorded per run.
- **Cost is a first-class metric.** Budget follows risk and stops when the next test is not worth it.
- **Reuse before building** ([documents 04](04-landscape.md) and [05](05-capability-map.md)).
- **Native first.** Generated tests look and run like the team's own, with no harness present.
- **Generated tests are provenance,** and candidates for the standard suite: each carries a signed record
  of source, model, prompt, version and approver.
- **The harness extends the chain of trust and never launders it.** Its own code, prompts, images and
  models are attested like anything it tests.
- **The harness tests itself first.** Every observed failure mode is a register entry with a detector,
  a correction and a self-check that runs before every run and fails closed.
- **The harness retires tests as well as writing them,** by proposal with evidence, never by deletion.
- **Fitness for purpose is validated, never assumed** (principle 12). A prompt set or a model becomes
  the default only by winning a measured table.
- **The pipeline is under test too** (principle 13). A CI provably short of what validating a test
  needs is a finding with the correcting change, routed to its owners, never an edit.

## The pipeline

One core, eight stages, each writing the records the next one reads. The run's story and file index are
rewritten after every stage.

| Stage | What it does | Writes |
|---|---|---|
| 0 Self-verification | Every register self-check, then sandbox and model probes; any failure stops the run | `selfcheck` record, cited by every manifest |
| 1 Intake | A repository and two refs (no base means rescan); the dependency graph at both, resolved in the target's own interpreter image; pre-flight gates; advisories per version | Work list: a row per package with depth, reachability and pre-flight result, and one for the repository |
| 2 Analysis | Per row: API surface and diff from tooling, never the model; source diff; our call sites; advisories with symbols and fix diff; what the CI does with untrusted code and what the suite reaches; a risk score that sets the budget | Fact bundles |
| 3 Generation | Unit, functional, negative, CVE-targeted, property and fuzz tests plus support code; compile, baseline run, repair; kept only if it compiles, collects and passes on the baseline | Candidates with a manifest |
| 4 Validation execution | Sealed, both versions, once: head run, flake re-run, coverage, mutation on executed lines only, differential against the base or a resolved fixed candidate, relevance of existing tests | An honest verdict per test |
| 5 Triage | A class, a confidence and a route for every verdict and finding; below the threshold a person decides | Findings |
| 6 Review | The packet in plain terms, tests as a patch, a draft VEX per advisory, promotions and retirements, the signed statement and UDLM records, the pull request text; the CI loop opens the test pull request | Packet, attestation, pull request |
| 7 Feedback | Reviewer decisions read back as labeled examples and realized records; prompt sets and models scored; a new failure mode enters the register before any fix | Acceptance records, evaluation table |

Triage classes: `test-bug`, `behavior-change`, `undocumented-change`, `defect`, `security`,
`suspicious` (blocks the merge), `obsolete`, `redundant`, and for the CI itself `coverage-gap` and
`pipeline`.

**Two lifecycles, one core.** In the developer's inner loop the harness runs on the branch, in the same
sealed sandbox, and the kept tests go into the developer's own pull request. In the CI outer loop it
runs on every change unattended and opens a test pull request under a bot identity with signed commits
and provenance: dependency tests to an overlay repository, first-party tests to the repository under
test on the change's branch. In both, the merge is a pull request a person owns, and no generated test
runs outside the sandbox before someone has read it. The harness's run is validation execution; the
suite's later runs are regression execution, not a harness stage.

## Dependencies: where the budget goes

| Depth | Policy |
|---|---|
| 0, our code | Full generation on every pull request; no advisory lookup for the application itself |
| 1, direct | Full generation on version change; functional tests target our call sites |
| 2 and deeper | Generation only when reachable or above the risk threshold; otherwise a characterization snapshot |
| Any | A new package gets pre-flight and characterization regardless; a known vulnerability gets CVE-targeted tests and a draft VEX regardless of depth |

The risk score weighs reachability most, then change size and contract change, sensitivity, upstream
signals, known vulnerabilities, pre-flight hits and history. The same tests on the old and the new
version is the highest-value technique for dependencies and the first thing built.

## Known vulnerabilities become evidence

For every advisory on a version in the graph: locate the vulnerable symbols from the advisory or the fix
diff; an exposure test at our call site if our code reaches them; a fix-pinning test that fails on the
vulnerable version and passes on the fixed one; a draft VEX statement, `affected` with the exposure
test, `not_affected` with reachability evidence, `fixed` only on a proven test. Roles come from the
advisories, not commit order, so a downgrade reports as exposure. Product Security confirms every
statement; the harness never publishes one.

## Test lifecycle and provenance

A test is a `candidate` until a reviewer accepts it, `accepted` until the owning team promotes it to
`standard` (it kills a mutant no other test kills, has survived two version bumps or caught a
regression, and asserts behavior we depend on), and `retired` only by a person's approval of a proposal
with evidence, as a state, never a deletion. Dependency tests live in an overlay repository by
ecosystem, package and version range; first-party tests live in the repository.

Every test carries a provenance record: a UDLM `TestEvidence` record, with `SoftwarePackage`,
`Vulnerability`, `Job` and `VexStatement` around it, sealed with UDLM's tamper-evident head, and a
signed in-toto `test-result/v0.1` statement naming those heads as subjects. Endpoints, repositories and
paths appear by label, name and digest only. SLSA targets: Build L3 for harness outputs, Source L3 for
the overlay repository, Source L4 for the standard suite. The harness confers no level on what it tests.

## Security rules

- Candidates run only sealed: no network, no secrets, read-only root, disposable, kernel isolation at
  depth 1 and deeper.
- A prompt injection yields at most a bad test, which validation discards, and is itself a `suspicious`
  finding.
- Signing keys live in the pipeline, never in the sandbox.
- Tests for undisclosed vulnerabilities stay restricted until disclosure; reproducers are rewritten,
  never copied.
- Hermeto (GPL-3.0) is invoked, never vendored; AGPL and unlicensed components are excluded.

## Built here, reused from elsewhere

Reused: Konflux and Tekton, Hermeto, Trustify, Conforma and Trusted Artifact Signer, each ecosystem's
own resolver, runner, API-diff and mutation tools. Built here: the assembly and adapter interface, the
generation and triage agents, cross-ecosystem differential testing, the overlay repository and its
provenance, the relevance engine, and CVE-targeted generation with VEX drafts.

## How it is judged

- Stage 0 passes: every register entry has a self-check; the register stands at twenty-eight.
- Every run is assessed against twelve goals, each with its measurement and the file it came from.
- The reference jobs are rerun against the baseline in [document 12](12-prompt-and-model-evaluation.md).
- [Document 14](14-specification.md) lists the twenty-two requirements and the test that proves each.

Targets that matter most: mutation score above 0.6 on sampled mutants, flake rate under 1%, reviewer
acceptance above 70%, a CVE-targeted test for every known vulnerability, a signed record on every
accepted test. The full metrics, risks, rollout, governance, open questions and worked example are in
document 16.
