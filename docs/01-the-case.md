# AI Test Harness Business Case

## Blueprint Identity

**Owner:** Chris Roadfeldt

**Elevator pitch:** How do you know a change is safe when most of what you ship is code your team
never wrote? The AI Test Harness writes the tests nobody will write by hand, for your own code and
for every package you depend on. Every pull request arrives with its evidence: the tests that ran on
both sides of the change, and a signed record of the results. The person at the gate decides with
proof in hand instead of trust.

## Problem Statement

**Customer name:** Any organization that ships software built on code it did not write: product
teams, platform teams, and the security and compliance functions that answer for what they ship. The
first pilot runs on two example projects, one Python and one Go; the first customer team is to be named
with the sponsor.

**Customer stakeholder:** Whoever answers for the safety of a change and for the proof of it: the head
of engineering for delivery, the CISO or product security lead for exposure, the platform owner for
the pipeline. The pilot serves the person who approves the merge, and their measures come first: did
every change arrive with evidence, how much review time did it cost, what did it catch that review
alone would have missed. For the pilot that is whoever reviews the example projects' test pull
requests.

**Customer pain:** Most of what any team ships is code it did not write. A mid-sized service resolves
hundreds to thousands of packages; its engineers chose perhaps fifty. Nobody has read or tested the
rest, and when one changes behaviour the team finds out in production. Across a fleet the same unread
package sits in every service, so one bad version lands everywhere at once. The XZ Utils backdoor
arrived exactly this way: a trusted package, a routine update. AI-assisted development widens the gap:
teams with high AI adoption merge 98 percent more pull requests while review time per request rises
91 percent (Faros AI, 2025). Writing tests for code you did not write is slow and never prioritized,
so it does not happen.

**Current workaround:** A modern build platform says precisely what is in the product, hermetic
builds, a bill of materials, signed provenance, policy gates, but not whether any of it works or
whether a new version still does what the old one did. Teams bump dependencies on trust, run their own
suite, which rarely touches the dependency, and read changelogs. Commercial AI test tools cover one
language each, run outside the pipeline and produce no provenance; the best-known open one is
abandoned. Nothing, open or commercial, tests a dependency upgrade differentially for an application.

**Impact of inaction:** Regressions and vulnerabilities in code nobody looked at keep reaching
production and are found by customers. Every dependency bump stays a judgement call without evidence,
so upgrades are delayed and known vulnerabilities stay open longer. When a customer or regulator asks
what we verified about the code we ship, the answer for most of it is nothing, with no record to point
at.

**Impact of action:** Every change arrives at the gate with tests that ran, a plain-terms verdict and
a signed record. Every behaviour a change reaches ends in one of three states, validated, handed to
the team for their environment, or a stated gap with its reason; nothing is silent. Known
vulnerabilities get a test that proves the fix and a draft VEX statement backed by it. Review time is
the toil that remains, and it is measured on every run. Because the evidence is in a fixed, signed
form, approval can later be automated within policy. Upgrades get faster and safer, and the tests that
earn their keep join the team's suite, so the asset grows with every run.

## Proposed solution

**Landing BUs:** Trusted Software Supply Chain (the evidence chain: provenance, VEX, SLSA), Red Hat
OpenShift AI (model serving and the agent runtime), and the build platform and developer tooling
teams (the pipeline it runs in). To be confirmed with the sponsor.

**Aligned TDPs:** To be named with the sponsor; the natural fits are the supply chain security and
trusted AI plans.

**Considered alternatives:** IBM Research has published the closest designs, but they ship only inside
watsonx Code Assistant, for Java. The open LLM test generators are narrower or gone: the best known,
Qodo-Cover, has been unmaintained since June 2025. Commercial tools cover one language each, run
outside our pipeline and produce no provenance. Differential testing of upgrades exists only at
distribution scale. Buying would give a fraction of the capability and none of the evidence chain. The
components underneath are open and maintained, several of them Red Hat's; what did not exist was the
assembly. The survey is in the [landscape](04-landscape.md).

**Solution overview:** A change arrives, a pull request or a new dependency version. The harness
resolves the dependency graph at both versions, looks every package up for advisories, and scores
each one's risk to set a budget. Given facts from static analysis, not asked to guess, a model writes
unit, negative and vulnerability-targeted tests. Every candidate runs in a sealed sandbox on both
sides of the change; a fix is proven only by a test that fails on the vulnerable version and passes on
the fixed one. Mutation testing shows how firmly the tests hold. Triage classifies every verdict with
a confidence and a route, and the run writes its own story. The tests reach the repository only
through a pull request a person merges; the harness never merges, fixes code, publishes or deletes.
Every accepted test carries a signed record. The harness is platform-agnostic and runs wherever the
team's pipeline runs. Appendix A answers, step by step, the questions reviewers asked about each part.

**Timeline & Milestones:**

1. **Pilot, weeks 1 to 6.** Two example projects, one Python and one Go, our own code and direct
   dependencies, triggered from the pull request. Exit criteria in Appendix B.
2. **First-party at scale, weeks 7 to 12.** Every pull request in the pilot repositories, unattended;
   the test pull request as the standard path.
3. **Direct dependencies, weeks 13 to 20.** Every bump, CVE-targeted tests and VEX drafts on every
   advisory, SLSA Build L3 on the records.
4. **Transitive dependencies, weeks 21 to 30.** Reachability and risk scoring across the whole graph.
5. **Continuous operation, week 31 on.** Scheduled rescans, the remaining ecosystems, upstream
   contributions. The extended goal is coverage of behaviour, defined in Appendix B.

Durations assume a team of two to four engineers and are replaced by measured velocity after the pilot.

**Definition of Done:** The harness is done with a change when the evidence is at the gate: the pull
request carries the tests, their results on both sides of the change, and a signed record. The merge
decision and what follows belong to the team.

The blueprint is done when a product team can point it at a repository and a pull request and receive
that evidence without anyone from the harness team involved; when on any new change every reached
behaviour ends in one of the three states and nothing is claimed that was not proven; when the
reference jobs rerun on a release with no measure worse than the last; when every entry of the failure
register passes at the start of every run; and when it runs where the customer already runs, in the
team's build platform and through the shipped triggers. The full standard is in Appendix B.

## Appendix A: the solution, step by step

The paragraphs below answer the questions reviewers asked about each part of the solution overview.

*What the model is given.* Facts, not a request to guess. From the package: its public API at both
versions and the diff between them with breaking changes flagged, the source diff, and the security
linter's findings on the changed code (bandit for Python, gosec for Go). From the application: every
call site into the package and the symbols it uses, and what its existing tests already cover. From
the advisories: each vulnerability with affected and fixed versions, from OSV. Before anything runs,
GuardDog and OSV's malicious-package feed screen a new or changed package. The extractors are the
languages' own parsers. From the same parsers comes the behaviour worklist. For every function the
application uses it lists each return and error path, each parameter's type with the edges its
domain implies, each decision with more than one condition, and each advisory as a result that must
never happen. The model gets it as the list of results to check. Next in line, and named so no one
assumes it exists: call-graph reachability, with govulncheck's approach for Go and CodeLLM-Devkit
for the rest.

*The sandbox.* A locked-down container today: no network, no secrets, nothing inherited from the host,
read-only file system, the package's declared dependencies copied in beforehand. On OpenShift, a pod
with the same locks. For tests that need to touch the kernel or native code, the design follows
Debian's autopkgtest and Fedora's Testing Farm: a stronger testbed, a small virtual machine under Kata
or gVisor, chosen per test. The sandbox is where a candidate proves it is worth a person's time. Once
accepted, a test lives in the team's repository and runs in the team's pipeline, with their services
and their native libraries, every time.

*Tests declare what they need.* Native code can behave differently in a container, and some tests
need a network. The industry's answer is the one we adopt: every test declares its needs, the way
Debian's tests declare `isolation-machine` and Google's declare a size, and the sandbox denies by
default, as Bazel's does. A test that needs nothing, or only the local host, runs sealed. A test
that needs a real kernel or native libraries is marked "machine" and runs in a virtual-machine
testbed, or, until we have one, is handed to the team's pipeline with that declaration attached. A
test that needs a live service is written against a fake the model produces with it. One that
declares it needs the real network is proposed to the team with the declaration, and proves itself
in their pipeline, never in ours. A test that declared nothing and then opened a connection is a
defect in the test, pytest-socket's rule, and is sent back to generation. A test that fails because
the testbed refused something it was promised is reported as a testbed failure, autopkgtest's exit
code 16, never as a defect and never thrown away. What no testbed can see is code that behaves
differently on the team's own hardware or services, which is why the test pull request runs the
team's pipeline before anyone merges.

*Flaky tests never reach a person.* Each candidate runs more than once on the new version and once on
the old. Meta's TestGen-LLM proposes only tests that pass repeatedly, and Google treats a 0.15 percent
flake rate as a problem worth engineering hours. A candidate that disagrees with itself on any run is
set aside. Twice is the floor; the candidates about to be proposed run five times by default, the
team's number. A fix is proven only by a test that fails on the vulnerable version and passes on the
fixed one.

*Mutation testing, bounded.* Its job is narrow: prove that each generated test checks something, by
breaking the code it executed and seeing whether the test notices. Mutants are placed only on lines
the generated tests ran, aimed first at the behaviours the application calls and the helpers they
delegate to, and sampled within the package's budget, never across the whole package. In the proof
of concept a Go package offered 2,787 sites and the harness ran 25. Google applies mutation testing
the same way, only to changed code during review. A mutant that survives names a behaviour the test
did not check, and the model is told so. Before a passing file is believed it is probed with a few
such breakages, and the ones its tests miss go back to the model once, as a diff.

*What comes out.* Every function the change reaches ends in exactly one of three states. Validated:
a test ran on both sides of the change, ran consistently, exercised code nothing else did, and
caught deliberate breakage, with the record to prove it. For your environment: a real test that
needs something only the team has, handed over with its declaration. Stated gap: the harness could
not produce a test it trusts, or the pipeline cannot validate one, and the record says why. The pull
request carries a "Not covered" section per function. Each gap has its reason and a note on the line
in the diff where the unchecked behaviour lives. The team's existing tests are counted, so the gaps
are real ones. Where the harness can, it adds a test skeleton with the setup done and the assertion
left for the developer to finish in minutes. The gaps are kept as data, so a team watches its count
fall, or not, per repository over time.

*The gate reads two things, and either can say no.* The pipeline's own result, which now includes the
harness's tests running in the team's environment, existing suite included. And the harness's verdict:
what was validated, what needs the team's environment, and what was not checked, with the reasons.
What counts as inadequate, an unchecked behaviour an advisory says must never happen, a strength score
under the floor, too many gaps on new code, is the team's policy, set in their own file. Both land on
the pull request as statuses a branch policy can require. The person who merges decides with the
evidence in hand. The harness does not run the repository's existing suite, does not fix code, never
merges and never decides alone, but when the policy says its result is a negative, the merge waits, and
the record says why. A fix is someone else's change and goes through the harness like any other.

*The pipeline it runs in.* The harness reads how the repository runs its tests, because it must, to
propose a test that will actually run there. When that reading shows the pipeline cannot run or
validate what the harness proposes, no test step, tests not run on pull requests, no coverage
reported, the run says so, with the change that would fix it. Without that change the evidence at
the gate is incomplete. That is the only finding it makes about the pipeline.

*The record.* Every accepted test carries a signed in-toto record, and the vulnerability tests back
a draft OpenVEX statement. The run's provenance meets SLSA Build L3, the supply-chain level where
the build platform itself produces and signs the record, so a build cannot forge its own provenance.
The same evidence can be exported as UDLM records, which link it into the wider lifecycle chain the
DCM work is building, so one record spans the change, the build and the estate.

*Fitness, validated, and the harness learns.* The harness has no AI of its own. It calls whatever
model the team points it at and gives it written instructions that can also be changed. Different
models and instructions produce very different tests, so neither becomes the default until it has
run the same reference jobs and the results are published in a
[table](12-prompt-and-model-evaluation.md) anyone can read. Every test records the model and
instructions that made it, and the reviewer's decision on that test is read back against the record.
Over time that shows which combinations produce the tests people keep, which are the ones that join
the long-term suite, and it points at what to improve next. The harness learns from its own failures
the same way. Every way it has gone wrong in our runs, 28 so far, is written in the [failure
register](15-failure-register.md) with its cause, and turned into a check that runs before every
run, so the same mistake cannot return unnoticed.

*Effort follows risk, and the team holds the knobs.* Effort means model time and sandbox time. It is
spent writing tests where our code actually calls the package or a known vulnerability applies.
Elsewhere the harness takes a characterization snapshot: a record of what the package's public
functions do today, taken without writing tests, so a later version can be compared against it.
Reachability is approximate and the harness says so. It starts from what is certain, the
application's own call sites. Static call-graph analysis extends that where the language allows (Go)
and only hints where it does not (Python). The dynamic signal grows from what the team's existing
suite executes and from every test the harness itself generates and runs: coverage from one run
refines reachability for the next. Where reachability is unknown the risk score decides and the
record says "unknown." Every number the harness works to is the team's to set, in a file in their
own repository: mutants, repeats, tests per file, model time per change, which gaps block, which
dependencies get full effort. The harness ships defaults and explains them. Cost follows the model:
model time dominates a run, mutation and sandbox time are small beside it, and all of it scales with
the inference hardware the team provides. The harness measures that hardware at the start of each
run and plans to fit the time it was given, highest-value work first, and reports what it did not
reach as a stated gap rather than running out quietly.

*Where this starts from.* A proof of concept exists. I built it to test the blueprint before
proposing it. It runs the whole flow, resolve, analyze, generate, run, mutate, score, attest,
propose, on two real repositories, one Python and one Go, on a workstation and as a Tekton pipeline
on OpenShift. It is not the product. Its job was to find out what breaks, which it did, 28 times,
each written into the failure register, and to show the blueprint at work on real code so that the
estimates below are grounded rather than guessed. Every run it has made is
[published](11-evidence-rollup.md) with its records, so a reader can check any claim in this
document against one.

## Appendix B: measures, exit criteria and the full definition of done

**The milestones in full.**

1. **Pilot, weeks 1 to 6.** Two example projects on their build platform, our own code and direct
   dependencies,
   triggered from the pull request, review packets as pull request comments. Value from the first
   run: a verdict and a signed record on every dependency bump, and the pipeline findings, if any,
   on each service. Exit criteria: every pull request in the pilot repositories arrived with its
   evidence. Reviewer time per finding is measured and reported. At least one finding a reviewer
   confirms would otherwise have been missed. The share of proposed tests reviewers accepted is
   reported. The pilot's own reference jobs are established on its own services. The default model
   and prompt stayed above the fitness floor on the evaluation table. That floor is the share of
   generated candidates that build, starting at 80 percent, just above the published production
   figure of 75 percent, and set by the team from there. 2. **First-party at scale, weeks 7 to 12.**
   Every pull request in the pilot repositories, unattended: no one starts a run and nothing waits
   on one. A change the harness cannot handle, no manifest, an unsupported ecosystem, a model that
   fails, is reported in the pull request as a stated gap with the reason. Whether that counts as a
   negative at the gate is the team's policy. The test overlay repository and the test pull request
   become the standard path. Value: tests on the team's own changes without anyone pressing a
   button. 3. **Direct dependencies, weeks 13 to 20.** Every bump, pre-flight gates, CVE-targeted
   tests and VEX drafts on every advisory, SLSA Build L3 on the records. Value: every known
   vulnerability in a direct dependency answered with a test or a stated gap. 4. **Transitive
   dependencies, weeks 21 to 30.** Reachability and risk scoring across the whole graph,
   characterization snapshots where we do not reach, full effort where we do, and a transitive
   reference job so the measures exist per tier. 5. **Continuous operation, week 31 on.** Scheduled
   rescans, the remaining ecosystems, upstream contributions of the tests that earned their place.
   The extended goal from here is coverage of behaviour, in the sense the testing profession defines
   it. For every function the application reaches, every result it can produce has a test that
   checks it, proven by mutation testing, or the gap is named. The results are the good path, each
   class of bad input and each boundary, each combination of conditions that changes the outcome,
   and each thing an advisory says must never happen. Line coverage is used the way DO-178C and
   Google use it, to find what the behaviour tests missed, not as the score.

**The definition of done in full.** The harness is done with a change when the evidence is at the gate: the pull
request carries the tests, their results on both sides of the change, and a signed record. The merge
decision and what follows belong to the team; the harness reads that decision back only to improve
itself.

Done for the blueprint is a standard of behaviour on work never seen before, and a regression check
on work seen before. On any new change, the harness accounts for every function the change reaches
in exactly one of three states: validated, for the team's environment, or a stated gap with its
reason. It claims nothing it did not prove with a test that ran on both sides, ran consistently and
caught deliberate breakage. It lands its verdict and the pipeline's result on the pull request as
statuses a policy can read. It reports what it cost, reviewer time per finding and the share of its
tests accepted, so each team can watch the trend on its own repositories. On the reference jobs, a
new release gets no measure worse than the last. The measures are candidates that build, behaviours
checked out of behaviours identified, fixes proven out of advisories known, mutation score on what
was checked, and, where a reviewer has looked, tests accepted and reviewer time per finding. A
reference job is a fixed change on a fixed repository whose right answers are known in advance, so
that models, prompts and releases are measured against the same thing. The two in the proof of
concept are examples of the blueprint at work. The pilot establishes its own, at least one per
supported language.

It is done when a product team can point it at a repository and a pull request and receive all of
the above without anyone from the harness team involved, with records that Conforma verifies at
release. It is done when every entry of the failure register passes as the first step of every run.
And it is done when it runs where the customer already runs: as an integration task of the team's
build platform (Konflux's integration service, in the pilot) and through the shipped GitHub Actions
and GitLab CI triggers. Each trigger has been exercised on a real repository, with a documented
model endpoint per language. Then it can ship as part of Trusted Software Supply Chain or stand as a
product of its own.

## Appendix C: references

- Faros AI, [The AI Productivity Paradox](https://www.faros.ai/blog/ai-software-engineering), 2025.
  Telemetry from more than 10,000 developers: 21 percent more tasks, 98 percent more pull requests,
  91 percent longer review time on high-adoption teams.
- [A survey of unit test case generation methods](https://www.sciencedirect.com/science/article/abs/pii/S095058492600131X),
  Information and Software Technology 196, August 2026. 67 methods assessed; hybrids of search-based
  and model-based generation perform best.
- Meta, [TestGen-LLM](https://arxiv.org/abs/2402.09171), 2024. In production: 75 percent of generated
  tests built, 57 percent passed reliably, 25 percent raised coverage; engineers accepted 73 percent of
  what passed the filters.
- IBM Research, [ASTER](https://arxiv.org/abs/2409.03093), 2024. Static analysis guiding model-written
  unit tests; the closest published design.
- [Qodo-Cover](https://github.com/qodo-ai/qodo-cover): "no longer maintained, please fork," June 2025;
  AGPL-3.0. [EvoSuite](https://github.com/EvoSuite/evosuite): last release v1.2.0, 2021; Java 8 and 11.
- Debian, [autopkgtest package test specification](https://salsa.debian.org/ci-team/autopkgtest/-/raw/master/doc/README.package-tests.rst)
  and [manual](https://manpages.debian.org/testing/autopkgtest/autopkgtest.1.en.html). Tests declare
  `needs-internet`, `isolation-container`, `isolation-machine`, `flaky`; exit 16 is a testbed failure,
  distinct from a test failure.
- Bazel, [common definitions, tags](https://bazel.build/reference/be/common-definitions). The sandbox
  blocks the external network unless a test carries `requires-network`.
- [Software Engineering at Google, chapter 11](https://abseil.io/resources/swe-book/html/ch11.html).
  Test sizes small, medium, large, enforced; a 0.15 percent flake rate fought with engineering hours.
- Google, [Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html),
  2020. Coverage shows what was not tested; it is not a goal.
- Google, [Practical Mutation Testing at Scale](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/),
  2021. Mutation on changed code during review, across 1,000 projects and 24,000 developers.
- Schuler and Zeller, [Assessing Oracle Quality with Checked Coverage](https://www.st.cs.uni-saarland.de/publications/details/schuler-icst-2011/),
  ICST 2011. Only executed statements that influence an assertion count; more sensitive than mutation.
- ISTQB, [Certified Tester Foundation Level syllabus v4.0](https://astqb.org/assets/documents/ISTQB_CTFL_Syllabus-v4.0.pdf).
  Equivalence partitions, boundary values, decision tables and state transitions as coverage items.
- AdaCore, [DO-178C structural coverage analysis](https://learn.adacore.com/booklets/adacore-technologies-for-airborne-software/chapters/analysis.html).
  Tests come from requirements; structural coverage finds what they missed.
- NIST, [CVE-2024-3094](https://nvd.nist.gov/vuln/detail/CVE-2024-3094), 2024. The XZ Utils backdoor.
- [SLSA](https://slsa.dev/spec/), [in-toto attestations](https://github.com/in-toto/attestation),
  [OpenVEX](https://github.com/openvex/spec) and [OSV](https://osv.dev): the record, provenance,
  exploitability and advisory formats the harness emits and consumes.
- In this repository: the [landscape](04-landscape.md), the
  [evidence roll-up](11-evidence-rollup.md), the [evaluation table](12-prompt-and-model-evaluation.md),
  the [failure register](15-failure-register.md) and the [design queue](17-design-queue.md) from this
  review.
