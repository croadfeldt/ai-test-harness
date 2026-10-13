# AI Test Harness Business Case

## Blueprint Identity

**Owner:** Chris Roadfeldt

**Elevator pitch:** How do you know a change is safe when most of what you ship is code your team never
wrote? The AI Test Harness writes, runs and scores tests for every change in a sealed sandbox and hands a
person the evidence with a signed record. Its engine is dependency verification: the same test runs on
the old and the new version of a package, so a difference is proven, not read about in a changelog. It
applies that engine in layers: first to the change itself, then to the direct dependencies the change
touches, then to the transitive ones.

## Problem Statement

**Customer name:** Any organization that ships software built on code it did not write: product teams,
platform teams, and the security and compliance functions that answer for what they ship. The first
pilot is with Red Hat product teams building on Konflux, to be named with the sponsor.

**Customer stakeholder:** whoever answers for the safety of a change and for the proof of it: the head
of engineering for delivery, the CISO or product security lead for exposure, the platform owner for the
pipeline. The pilot's primary persona is the engineering lead who merges dependency bumps, and the
metrics that matter to them come first: a verdict on every bump, the findings it surfaces, and the review
time the packet costs. The security and platform personas, with their own metrics, follow in the later
phases. For the pilot, the executive sponsor and the leads of the participating teams, to be named.

**Customer pain:** Most of what any team ships is code it did not write. Take a mid-sized service as
one example: it resolves several hundred to a few thousand packages, its engineers chose perhaps fifty,
and the rest arrived as dependencies of dependencies. Nobody on the team has read them or tested them,
and when one changes behaviour in a minor version the team finds out in production. The ratio is the
same for a small tool or a large platform, and across a fleet it multiplies: the same unread package
sits in every service, so one bad version lands everywhere at once. The most serious supply chain
incidents of recent years, the XZ Utils backdoor among them, arrived exactly this way: a trusted
package, a routine update, a change whose description bore no relation to its effect. Writing tests for
code you did not write is slow, tedious and never prioritized, so it does not happen.

AI-assisted development makes the gap wider, not narrower. Faros AI's 2025 study of telemetry from more
than ten thousand developers found that teams with high AI adoption complete 21 percent more tasks and
merge 98 percent more pull requests, while review time per pull request rises 91 percent and the
pull requests grow larger and carry more defects. The bottleneck moves from writing code to proving it is
safe, and that proof is still produced by hand.

**Current workaround:** A modern build platform answers the first half of the question. Konflux, to
take our own as the example, gives hermetic builds, a complete bill of materials, signed provenance and
policy gates: it says precisely what is in the product. No build platform says whether any of it works,
or whether a new version still does what the old one did. So teams bump dependencies on trust, run
their own suite, which rarely touches the dependency, and read changelogs. Commercial AI test tools
cover one language each, run outside the pipeline and produce no provenance; the best-known open one
is abandoned. The research field is active (a 2026 survey in Information and Software Technology
reviews 67 unit test generation methods from the last five years, and finds that search-based and
model-based approaches do best combined), but every method in it tests one version of one codebase.
Nothing, open or commercial, tests a dependency upgrade differentially for an application.

**Impact of inaction:** Regressions and vulnerabilities in code nobody looked at keep reaching
production and are found by customers. Every dependency bump stays a judgement call made without
evidence, so upgrades are delayed and known vulnerabilities stay open longer. When a customer or a
regulator asks what we verified about the code we ship, the answer for most of it is nothing, with no
record to point at.

**Impact of action:** Every incoming change arrives with tests that ran, a plain-terms verdict and a
signed record, in minutes to hours: the time is almost all model time, so it follows the inference
hardware, and the hours measured in our lab on self-hosted models become minutes on faster serving.
Known vulnerabilities get a test that proves the fix and a draft VEX statement backed by it. Upgrades
get faster and safer, incidents from unread code fall, and the proof of testing travels with the product
for anyone downstream to check. The tests that earn their keep join the standard suite, so the asset
grows with every run.

## Proposed solution

**Landing BUs:** Trusted Software Supply Chain (the evidence chain: provenance, VEX, SLSA), Red Hat
OpenShift AI (the model serving and the agent runtime), and the Konflux and Developer tooling teams
(the pipeline it runs in). To be confirmed with the sponsor.

**Aligned TDPs:** to be named with the sponsor; the natural fits are the supply chain security and
trusted AI plans.

**Considered alternatives:** IBM Research has published the closest designs, ASTER for unit tests and
SAINT and Sakura for service-level tests, but the tools ship only inside watsonx Code Assistant, for
Java. The open LLM test generators are narrower or gone: Qodo-Cover, the open reimplementation of
Meta's TestGen-LLM, is AGPL and its maintainers now say "please fork"; CoverUp (Python, Apache-2.0,
active) and Pynguin (Python, LGPL, release 0.46 in July 2026) each cover one language; TestSpark lives
inside an IDE; EvoSuite, the older search-based baseline, is years behind on Java versions. Commercial
tools (Diffblue Cover, Qodo Cover Pro, Keploy's hosted generator) cover one language each, do not run
in our pipeline and produce no provenance. Differential testing of upgrades exists only at distribution
scale, in Debian's autopkgtest, Rust's Crater and Julia's PkgEval, and nothing does it for an
application. Buying would give a fraction of the capability and none of the evidence chain. The
components underneath, the resolvers, sandboxes, mutation and coverage tools, attestation formats and
open models, are open and maintained, several of them Red Hat's; what did not exist was the assembly.
The full survey, with licences and activity dates, is in the [landscape](04-landscape.md).

**Solution overview:** A change arrives, a pull request or a new dependency version, named by
repository and two refs. The harness resolves the dependency graph at both, looks every version up for
advisories, and scores each package's risk to set a budget. A model writes characterization, negative
and vulnerability-targeted tests through a tool-using loop. Every candidate runs in a sealed sandbox,
and the strong ones reach the repository as a pull request a person merges. The paragraphs below answer
the questions reviewers asked about each step.

*What the model is given.* Facts from static analysis, not a request to guess: the package's public
API at both versions and the diff between them with breaking changes flagged; the source diff; the
application's call sites and the symbols it uses; the advisories from OSV with affected and fixed
versions; and the findings of the ecosystem's security linter, bandit for Python and gosec for Go, on
the call sites and on the changed code. The extractors are the languages' own parsers. GuardDog and
OSV's malicious-package feed screen a new or changed package before anything executes.

*The sandbox.* Today a rootless container: no network, no inherited environment, read-only root,
capabilities dropped, no secrets, with the package's declared dependencies prefetched into it. On
OpenShift it is a pod with the same restrictions; gVisor or Kata isolation is the design for
dependencies below the first level. A test that needs the network is not accepted; the gap is recorded.
A container is not production: native extensions and syscall-level behaviour can differ, so the
harness's claim is about the package as the application calls it, and every record says where the test
ran.

*Why twice.* Each candidate runs twice on the new version, to catch flaky tests, which are quarantined,
and once on the old version. A fix is proven only by a test that fails on the vulnerable version and
passes on the fixed one.

*Mutation testing, bounded.* Mutants are placed only on lines the generated tests executed, a sampled
set within the package's budget, each run sealed. In our lab a Go package offered 2,787 candidate sites
and the harness ran 25. The goal is a strength signal on the generated tests, not a mutation score for
the package.

*Who gates.* Triage classifies every verdict with a confidence and a route, and the run writes its own
story: who, what, why, where, when, and every decision. Tests reach a repository only through a pull
request, which runs the repository's own CI like any other change, and a person merges it. The harness
does not run the repository's existing suite, does not fix code, and never merges, publishes or
deletes. After the merge it reads the decision back, accepted, edited or rejected per test, as evidence
for improving itself. Every accepted test carries a signed in-toto record and a sealed UDLM record, the
open lifecycle record format that links what was intended, what was requested and what was realized for
each test.

*The pipeline it runs in.* To propose a test the harness has to read how the repository runs tests.
Where that reading shows the pipeline cannot validate a test, no test step, no coverage, no sealed
runner, the run says so with the fix. That is the only finding it makes about CI; it is not a separate
audit tool.

*Fitness, validated.* Every model and prompt set the harness uses is measured on the reference jobs and
published in an [evaluation table](12-prompt-and-model-evaluation.md) before it becomes a default.
Nothing is assumed to be fit.

*Effort follows risk.* Effort means model calls and sandbox time. Full generation goes where the
application reaches a package or an advisory applies. Elsewhere a characterization snapshot, the
exported API surface, a hash of each exported function body and the outputs of deterministic calls,
records behaviour cheaply so a later version can be diffed. Reachability is approximate and the harness
says so: static call-graph analysis where the language supports it (Go is strongest), the application's
call sites and import roots where it does not, and the coverage of the existing suite and of the
generated tests as the dynamic signal. Where reachability is unknown the risk score decides, and the
record says it was unknown rather than claiming it. This is what lets the harness scale from one service
to a fleet with reviewer time growing with findings, not with dependencies.

*Where it stands.* It has run end to end on real repositories, for Python and Go, on a workstation and
as a Tekton pipeline on OpenShift. Every failure of the harness itself observed in those runs, 28 so far,
is written in the [failure register](15-failure-register.md) with its cause, its detector and its
correction, and the checks run before every run.

**Timeline & Milestones:**

1. **Pilot, weeks 1 to 6.** Two product services on Konflux, our own code and direct dependencies,
   triggered from the pull request, review packets as PR comments. Value from the first run: a verdict
   and a signed record on every dependency bump, and the two pipeline findings on each service. Exit:
   generated tests build more than 80 percent of the time (a floor set from the lab runs in the
   evaluation table, where Python candidates built nine times in ten and the small model's Go attempts mostly
   produced no usable test at all; below it, review time outweighs the value), at least one real finding, reviewer feedback
   from both teams, and no default model or prompt changed except by the evaluation table.
2. **First-party at scale, weeks 7 to 12.** Every pull request in the pilot repositories, unattended:
   no one starts a run and nothing waits on one. A change the harness cannot handle, no manifest, an
   unsupported ecosystem, a model failure, is recorded in the run story and reported in the pull request
   comment; the harness never blocks a change. The test overlay repository and the test pull request
   become the standard path. Value: tests on the team's own changes without anyone pressing a button.
3. **Direct dependencies, weeks 13 to 20.** Every bump, pre-flight gates, CVE-targeted tests and VEX
   drafts on every advisory, SLSA Build L3 on the records (provenance generated and signed by the build
   platform, isolated from the signing key). Value: every known vulnerability in a direct dependency
   answered with a test or a stated gap.
4. **Transitive dependencies, weeks 21 to 30.** Reachability and risk scoring across the whole graph,
   characterization snapshots where we do not reach, full effort where we do.
5. **Continuous operation, week 31 on.** Scheduled rescans, the remaining ecosystems, upstream
   contributions of the tests that earned their place.

Durations assume a team of two to four engineers and are replaced by measured velocity after the pilot.

**Definition of Done:** The blueprint's scope ends at the test pull request and its record; what
happens after the merge belongs to the software lifecycle and is read back only to improve the harness.
Within that scope, it is done when a product team can point it at a repository and a pull request and
receive, without anyone from the harness team involved, a review packet, a test pull request and signed
records that Conforma verifies at release; when the reference jobs, today two from the proof of concept,
one per supported language (python-jose on frc-scheduler-server and kin-openapi on control-plane), are
rerun on the candidate release and match or beat their published baselines in the evaluation table on
tests that build, tests accepted, fixes proven and mutation score; when every entry of the failure
register passes as the first step of every run; when at least one regression or vulnerability caught by
a harness test that nothing else would have caught has been reported; and when it runs where the
customer already runs, as a Konflux integration-service task and through the shipped GitHub Actions and
GitLab CI triggers, each exercised on a real repository, with a documented model endpoint per language,
so that it can ship as part of Trusted Software Supply Chain or stand as a product of its own.

## References

- Faros AI, [The AI Productivity Paradox](https://www.faros.ai/blog/ai-software-engineering), 2025.
  Telemetry from more than 10,000 developers: 21 percent more tasks, 98 percent more pull requests,
  91 percent longer review time on high-adoption teams.
- [A survey of unit test case generation methods](https://www.sciencedirect.com/science/article/abs/pii/S095058492600131X),
  Information and Software Technology 196, August 2026. 67 methods assessed; hybrids of search-based
  and model-based generation perform best.
- Meta, [TestGen-LLM](https://arxiv.org/abs/2402.09171), 2024. The assured-improvement filter chain
  the open generators reimplement.
- IBM Research, [ASTER](https://arxiv.org/abs/2409.03093), 2024. Static analysis guiding model-written
  unit tests; the closest published design.
- NIST, [CVE-2024-3094](https://nvd.nist.gov/vuln/detail/CVE-2024-3094), 2024. The XZ Utils backdoor:
  a trusted package, a routine update.
- [SLSA](https://slsa.dev/spec/), [in-toto attestations](https://github.com/in-toto/attestation),
  [OpenVEX](https://github.com/openvex/spec) and [OSV](https://osv.dev): the record, provenance,
  exploitability and advisory formats the harness emits and consumes.
- In this repository: the [landscape](04-landscape.md) (every tool considered, with licence and
  activity), the [evaluation table](12-prompt-and-model-evaluation.md) (every model and prompt
  measured) and the [failure register](15-failure-register.md) (every failure of the harness itself).
