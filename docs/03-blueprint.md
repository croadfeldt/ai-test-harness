# AI Test Harness: the blueprint

**Status:** Draft v0.28, 2026-10-14. **Owner:** Chris Roadfeldt.
**For:** engineers and architects deciding whether to build, run or adopt this. Three pages.
**Behind it:** [document 16](16-blueprint-reference.md) is the long form, with the section numbers the
code and the other documents cite; [document 15](15-failure-register.md) is the failure register;
[document 14](14-specification.md) lists what an implementation must do and the test that proves each.

**Changes in v0.28:** the behaviour worklist (stage 2). For every public function the parser lists
the results a test should check: each return, each raise or error return, the fall-through, each
parameter's type with the edges its domain implies, each decision with more than one condition. Each
advisory is listed as a result that must never happen. The model reads it for the functions the
application uses; the accounting counts it per reached behaviour as the denominator behaviour
coverage will be measured against. Specification R27.

**Changes in v0.27:** mutation feedback (stage 3). Before a passing file is believed, the harness
breaks the package where the file's tests ran and runs the file against each breakage. A breakage
the tests let through goes back to the model once as a diff, and the manifest records what was
caught after. Specification R26.

**Changes in v0.26:** the flake check runs the candidates about to be proposed as many times as the team
sets, five by default (TestGen-LLM's figure), after the two runs every test gets; any disagreement
quarantines. Specification R9 updated.

**Changes in v0.25:** testbed failure is its own status (stage 4), at the run level and per test.
The environment's failure is never reported as the test's or the package's. The story opens with it,
the accounting names it as the reason, and a CTRF report beside the results carries it as `other`.
Specification R25.

**Changes in v0.24:** declared needs (stage 4). Every test says what it needs from its testbed, `none`,
`localhost`, `network` or `machine`; the team says what the testbed provides. A test that needs more is
withheld from the sealed run, recorded as skipped with its need, proposed to the team with the declaration,
and its behaviour is accounted for your environment. A test that declared nothing and opened a connection is
a defect in the test, and the verdict says so. Specification R24.

**Changes in v0.23:** per-test attribution for Go. The head run gives each passing test its own
coverage profile and folds them into the coverage record as contexts. The accounting then applies
the same rule in both ecosystems: the test that executed a behaviour must be the one that proved it.

**Changes in v0.22:** the accounting credits a behaviour with the private helpers it delegates to,
the closure, from a new `internals.json` the extractors write for Python and Go. It attributes
execution per test through coverage contexts recorded in the Python sandbox, and requires the test
that executed a behaviour to be the one that proved it. Mutation sampling aims at the reached
behaviours first. Specification R11 and R23 updated.

**Changes in v0.21:** the accounting (principle 15). Every behaviour the change reaches ends in exactly
one state, validated, for your environment, or a stated gap with its reason, and nothing is silent. Triage
writes it per package and rolled up; the story, the pull request text, the run index, the dashboard and the
evaluation table carry it; assessment goal 13 checks that the counts sum and every gap has a reason. On the
published runs it reads lower than "accepted", which is the point: see the dry run in
[document 18](18-design-queue-research.md).

**Changes in v0.20:** the static analysis is named as implemented (reference, stage 2): the
harness's own API extractors and diffs, the call-site scans, OSV, and now `bandit`, `gosec` and
GuardDog in the image. Their findings reach the prompt as SECURITY FINDINGS, and a high-severity
finding in the changed code is a `security` finding for a person. What the design names and the code
does not yet run is listed beside it.

**Changes in v0.19:** cut to three pages for the reader evaluating it. Nothing is dropped: v0.18 is
kept whole as document 16, the register as document 15, and the earlier change notes with them.

## What it is

A pipeline in which AI agents write tests for every change entering the software supply chain and
run them in a sealed sandbox against both the old and the new version. The tests are scored, and a
signed, human-reviewable packet goes to a person. First-party commits, direct dependencies and
transitive dependencies alike. The output is evidence: for each change, a reproducible answer to
three questions.

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
C++. One small adapter per ecosystem; the core is ecosystem-agnostic. It is platform-agnostic too: Konflux
is the example build platform throughout these documents, and the harness runs wherever its triggers run,
GitHub Actions, GitLab CI, Jenkins, Azure Pipelines or plain Tekton (`deploy/`).

## Principles

Fifteen, numbered so the code, the goals and the other documents can cite them.

1. **Generated tests are hypotheses until executed.**
2. **Tests must be strong, not just green.** Mutation testing and differential runs tell them apart.
3. **Incoming code is untrusted input.** Source, docs, advisories and commit messages are data in every
   prompt; tests run sealed, with no network and no credentials.
4. **Humans own the merge.** The harness proposes; it never merges, publishes or changes policy.
5. **Everything is reproducible.** Model, prompts, tools, graph and image digest are recorded per run.
6. **Cost is a first-class metric.** Budget follows risk and stops when the next test is not worth it.
7. **Reuse before building** ([documents 04](04-landscape.md) and [05](05-capability-map.md)).
8. **Native first.** Generated tests look and run like the team's own, with no harness present.
9. **Generated tests are provenance,** and candidates for the standard suite: each carries a signed record
   of source, model, prompt, version and approver.
10. **The harness extends the chain of trust and never launders it.** Its own code, prompts, images and
   models are attested like anything it tests.
11. **The harness tests itself first.** Every observed failure mode is a register entry with a detector,
   a correction and a self-check that runs before every run and fails closed.
12. **The harness retires tests as well as writing them,** by proposal with evidence, never by deletion.
13. **Fitness for purpose is validated, never assumed**. A prompt set or a model becomes
   the default only by winning a measured table.
14. **The pipeline is under test too**. A CI provably short of what validating a test
   needs is a finding with the correcting change, routed to its owners, never an edit.
15. **Every reached behaviour is accounted for**. Validated, for your environment, or a
   stated gap with its reason; nothing is silent, and nothing is implied that was not earned.

## The pipeline

One core, eight stages, each writing the records the next one reads. The run's story and file index are
rewritten after every stage.

| Stage | What it does | Writes |
|---|---|---|
| 0 Self-verification | Every register self-check, then sandbox and model probes; any failure stops the run | `selfcheck` record, cited by every manifest |
| 1 Intake | A repository and two refs (no base means rescan); the dependency graph at both, resolved in the target's own interpreter image; pre-flight gates; advisories per version | Work list: a row per package with depth, reachability and pre-flight result, and one for the repository |
| 2 Analysis | Per row: API surface and diff from tooling, never the model; source diff; our call sites; advisories with symbols and fix diff; security linting (`bandit`, `gosec`) of the call sites and the changed code, a pre-flight scan (GuardDog, OSV) of new packages; what the CI does with untrusted code and what the suite reaches; a risk score that sets the budget. Every tool that ran or did not is named in the bundle (reference, stage 2); the behaviour worklist: every result each public function can produce, from the parser | Fact bundles |
| 3 Generation | Unit, functional, negative, CVE-targeted, property and fuzz tests plus support code; compile, baseline run, repair; kept only if it compiles, collects and passes on the baseline; mutation feedback: a passing file is probed with deliberate breakages of the package, and the ones its tests miss go back to the model once | Candidates with a manifest |
| 4 Validation execution | Sealed, both versions, once: head run, flake check (two runs for every test, five for the candidates about to be proposed, the count the team's), coverage, mutation on executed lines only, differential against the base or a resolved fixed candidate, relevance of existing tests; every test's declared need honoured: none and localhost run sealed, network and machine are withheld and proposed to the team, an undeclared connection is a test defect; a failure of the testbed itself is its own status, never a verdict about the tests | An honest verdict per test |
| 5 Triage | A class, a confidence and a route for every verdict and finding; below the threshold a person decides; then the accounting: every reached behaviour in one of three states | Findings; the accounting |
| 6 Review | The packet in plain terms, tests as a patch, a draft VEX per advisory, promotions and retirements, the signed statement and UDLM records, the pull request text; the CI loop opens the test pull request | Packet, attestation, pull request |
| 7 Feedback | Reviewer decisions read back as labeled examples and realized records; prompt sets and models scored; a new failure mode enters the register before any fix | Acceptance records, evaluation table |

Triage classes: `test-bug`, `behavior-change`, `undocumented-change`, `defect`, `security`,
`suspicious` (blocks the merge), `obsolete`, `redundant`, and for the CI itself `coverage-gap` and
`pipeline`.

**Two lifecycles, one core.** In the developer's inner loop the harness runs on the branch, in the
same sealed sandbox, and the kept tests go into the developer's own pull request. In the CI outer
loop it runs on every change unattended and opens a test pull request under a bot identity with
signed commits and provenance. Dependency tests go to an overlay repository; first-party tests go to
the repository under test, on the change's branch. In both, the merge is a pull request a person
owns, and no generated test runs outside the sandbox before someone has read it. The gate reads two
inputs, the pipeline's result and the harness's verdict, and either can hold the merge under the team's
policy. The harness's run
is validation execution; the suite's later runs are regression execution, not a harness stage.

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

For every advisory on a version in the graph: locate the vulnerable symbols from the advisory or the
fix diff. Write an exposure test at our call site if our code reaches them, and a fix-pinning test
that fails on the vulnerable version and passes on the fixed one. Draft a VEX statement: `affected`
with the exposure test, `not_affected` with reachability evidence, `fixed` only on a proven test.
Roles come from the advisories, not commit order, so a downgrade reports as exposure. Product
Security confirms every statement; the harness never publishes one.

## Test lifecycle and provenance

A test is a `candidate` until a reviewer accepts it, and `accepted` until the owning team promotes
it to `standard`. Promotion means it kills a mutant no other test kills, has survived two version
bumps or caught a regression, and asserts behavior we depend on. A test is `retired` only by a
person's approval of a proposal with evidence, as a state, never a deletion. Dependency tests live
in an overlay repository by ecosystem, package and version range; first-party tests live in the
repository.

Every test carries a provenance record: a UDLM `TestEvidence` record, with `SoftwarePackage`,
`Vulnerability`, `Job` and `VexStatement` around it, sealed with UDLM's tamper-evident head, and a
signed in-toto `test-result/v0.1` statement naming those heads as subjects. Endpoints, repositories and
paths appear by label, name and digest only. SLSA targets: Build L3 for harness outputs, Source L3 for
the overlay repository, Source L4 for the standard suite. The harness confers no level on what it tests.

## Security rules

- Candidates run only sealed: no network, no secrets, read-only root, disposable. Kernel isolation (Kata) where
  the cluster provides it; where it does not, a test that declares it needs a real kernel is handed to the team,
  not run on a promise.
- A prompt injection yields at most a bad test, which validation discards, and is itself a `suspicious`
  finding.
- Signing keys live in the pipeline, never in the sandbox.
- Tests for undisclosed vulnerabilities stay restricted until disclosure; reproducers are rewritten,
  never copied.
- Hermeto (GPL-3.0) is invoked, never vendored; AGPL and unlicensed components are excluded.

## Built here, reused from elsewhere

Reused: a build platform and its pipeline engine (Konflux and Tekton, in the example), Hermeto, Trustify,
Conforma and Trusted Artifact Signer, each ecosystem's
own resolver, runner, API-diff and mutation tools. Built here: the assembly and adapter interface, the
generation and triage agents, cross-ecosystem differential testing, the overlay repository and its
provenance, the relevance engine, and CVE-targeted generation with VEX drafts.

## How it is judged

- Stage 0 passes: every register entry has a self-check; the register stands at twenty-eight.
- Every run is assessed against thirteen goals, each with its measurement and the file it came from.
- The reference jobs are rerun against the baseline in [document 12](12-prompt-and-model-evaluation.md).
- [Document 14](14-specification.md) lists the twenty-seven requirements and the test that proves each.
- Done is a standard of behaviour on work never seen before, every reached behaviour in one of three
  states and nothing claimed that was not proven, plus a regression check on the reference jobs, whose
  known answers are two-sided. The settled positions behind this are in [document 21](21-decision-record.md).

Targets that matter most: mutation score above 0.6 on sampled mutants, flake rate under 1%, reviewer
acceptance above 70%, a CVE-targeted test for every known vulnerability, a signed record on every
accepted test. The full metrics, risks, rollout, governance, open questions and worked example are in
document 16.
