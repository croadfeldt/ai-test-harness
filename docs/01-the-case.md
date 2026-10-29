# AI Test Harness Business Case

## Blueprint Identity

**Owner:** Chris Roadfeldt

**Elevator pitch:** How do you know a change is safe when most of what you ship is code your team
never wrote? The AI Test Harness writes the tests nobody will write by hand, for your own code and
for every package you depend on, and makes every pull request arrive with its evidence: the tests
that ran on both sides of the change, and a signed record of the results. The person at the gate
decides with proof in hand instead of trust.

## Problem Statement

**Customer name:** Any organization that ships software built on code it did not write: product
teams, platform teams, and the security and compliance functions that answer for what they ship. The
first pilot runs on two example projects, one Python and one Go; the first customer team is to be
named with the sponsor.

**Customer stakeholder:** Whoever answers for the safety of a change and for the proof of it: the head
of engineering, the product security lead, the platform owner. The pilot serves the person who
approves the merge, and their measures come first: did every change arrive with evidence, how much
review time did it cost, what did it catch that review alone would have missed.

**Customer pain:** Most of what any team ships is code it did not write. A mid-sized service resolves
hundreds to thousands of packages; its engineers chose perhaps fifty, and nobody has read or tested
the rest. Across a fleet the same unread package sits in every service, so one bad version lands
everywhere at once; the XZ Utils backdoor arrived exactly this way. AI-assisted development widens
the gap: teams with high AI adoption merge 98 percent more pull requests while review time per
request rises 91 percent (Faros AI, 2025). Writing tests for code you did not write is never
prioritized, so it does not happen.

**Current workaround:** A modern build platform says what is in the product, hermetic builds, a bill
of materials, signed provenance, policy gates, but not whether any of it works. Teams bump
dependencies on trust and read changelogs. Commercial AI test tools cover one language each, run
outside the pipeline and produce no provenance; the best-known open one is abandoned. Nothing tests a
dependency upgrade differentially for an application.

**Impact of inaction:** Regressions and vulnerabilities in code nobody looked at reach production and
are found by customers. Every dependency bump stays a judgement call without evidence, so upgrades
are delayed and known vulnerabilities stay open longer. Asked what we verified about the code we
ship, we have no record to point at.

**Impact of action:** Every change arrives at the gate with tests that ran, a plain-terms verdict and
a signed record. Every behaviour a change reaches is validated, handed to the team for their
environment, or a stated gap with its reason; nothing is silent. Known vulnerabilities get a test
that proves the fix and a draft VEX statement. Review time is the toil that remains, and it is
measured on every run. The tests that earn their keep join the team's suite, so the asset grows with
every run, and the evidence's fixed form lets approval be automated later within policy.

## Proposed solution

**Landing BUs:** Trusted Software Supply Chain (the evidence chain), Red Hat OpenShift AI (model
serving and the agent runtime), and the build platform and developer tooling teams. To be confirmed
with the sponsor.

**Aligned TDPs:** To be named with the sponsor; the natural fits are the supply chain security and
trusted AI plans.

**Considered alternatives:** IBM Research's designs ship only inside watsonx Code Assistant, for Java.
The open generators are narrower or gone; the best known, Qodo-Cover, is unmaintained since 2025.
Commercial tools cover one language each with no provenance. Buying would give a fraction of the
capability and none of the evidence chain; the components underneath are open and maintained, and
what did not exist was the assembly. Survey in the [landscape](04-landscape.md).

**Solution overview:** A change arrives. The harness resolves the dependency graph at both versions,
looks every package up for advisories, and scores risk to set a budget. Given facts from static
analysis, a model writes unit, negative and vulnerability-targeted tests. Every candidate runs sealed
on both sides of the change; a fix is proven only by a test that fails on the vulnerable version and
passes on the fixed one, and mutation testing shows how firmly the tests hold. Triage classifies every
verdict, the run writes its own story, and the tests reach the repository only through a pull request
a person merges. The harness only tests: it never merges, fixes code, publishes or deletes. It is
platform-agnostic and runs wherever the team's pipeline runs. The design is the
[blueprint](03-blueprint.md); the positions settled in review are the
[decision record](21-decision-record.md); a proof of concept has run it end to end on two real
repositories, every run [published](11-evidence-rollup.md).

**Cost and noise, as measured on the example runs.** These figures come from one lab and two models and
are examples, not a forecast for another environment. A package change cost half a million to one and a
quarter million prompt tokens and under fifty thousand completion tokens, plus a few CPU-minutes of sandbox
and mutation time; the same tokens took 97 minutes of model time on one model and 8 on another, so model
time is the cost and it follows the inference hardware. A platform owner prices it in their own tokens and
throughput. The harness runs beside the pull request pipeline, adding nothing to its critical path. Nothing
reaches a reviewer unless it built, passed on both sides, ran five times without disagreement and killed
a mutant; the initial targets are a flake rate under 1 percent, false suspicious findings under 5 percent
and reviewer acceptance above 70 percent (blueprint reference, section 10).

**Timeline & Milestones:**

1. **Pilot, weeks 1 to 6.** The claim path on one Python project: for every published fix claim, an
   exposure test and a fix-pinning test on both versions, one verdict per claim, a draft VEX statement that
   names the publisher's. Exit criteria in the [pilot plan](22-pilot-plan.md).
2. **The pull request path, weeks 7 to 12.** Two example projects, own code and direct dependencies, from
   the pull request; a test pull request per change.
3. **First-party at scale, weeks 13 to 18.** Every pull request, unattended; the test pull request as the
   standard path.
4. **Direct dependencies, weeks 19 to 26.** Every bump; CVE-targeted tests and VEX drafts on every
   advisory; SLSA Build L3 on the records.
5. **Transitive dependencies, weeks 27 to 36.** Reachability and risk scoring across the whole graph.
6. **Continuous operation, week 37 on.** Scheduled rescans, remaining ecosystems, upstream contributions;
   the extended goal is coverage of behaviour, not lines.

Durations assume two to four engineers and are replaced by measured velocity after the pilot.

**Definition of Done:** A product team can point the harness at a repository and a pull request and
receive, without the harness team involved, a pull request that carries the tests, their results on
both sides of the change and a signed record that the release gate verifies. On any new change every
reached behaviour ends in one of the three states and nothing is claimed that was not proven. The
reference jobs rerun on each release with no measure worse than the last. Every failure-register entry
passes at the start of every run. It runs where the customer runs, in their build platform and
through the shipped triggers. The full standard is decision D4 and D14 in the decision record.

## References

- Faros AI, [The AI Productivity Paradox](https://www.faros.ai/blog/ai-software-engineering), 2025.
- [A survey of unit test case generation methods](https://www.sciencedirect.com/science/article/abs/pii/S095058492600131X),
  Information and Software Technology 196, 2026.
- Meta, [TestGen-LLM](https://arxiv.org/abs/2402.09171), 2024; IBM Research, [ASTER](https://arxiv.org/abs/2409.03093), 2024.
- NIST, [CVE-2024-3094](https://nvd.nist.gov/vuln/detail/CVE-2024-3094): the XZ Utils backdoor.
- In this repository: the [blueprint](03-blueprint.md) and its [reference](16-blueprint-reference.md),
  the [decision record](21-decision-record.md), the [pilot plan](22-pilot-plan.md), the
  [research notes](18-design-queue-research.md) with every industry source, and the
  [evaluation table](12-prompt-and-model-evaluation.md).
