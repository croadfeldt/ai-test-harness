# AI Test Harness Business Case

## Blueprint Identity

**Owner:** Chris Roadfeldt

**Elevator pitch:** The AI Test Harness writes, runs and scores tests for every piece of code that enters a
product, our own and every dependency down to any depth, in a sealed sandbox, and hands a person the
evidence with a signed record. It fills the half of the supply chain story our build platform does not
cover: not what is in the product, but whether any of it works and still does what it did.

## Problem Statement

**Customer name:** Red Hat product teams building on Konflux, first; any organization with a software
supply chain to defend, after. The pilot customers are two product teams to be named with the sponsor.

**Customer stakeholder:** the executive sponsor and the two product team leads, to be named.

**Customer pain:** A mid-sized service resolves several hundred to a few thousand packages. Its engineers
chose perhaps fifty. Nobody on the team has read the rest, nobody has tested them, and when one changes
behaviour in a minor version the team finds out in production. The most serious supply chain incidents
of recent years, the XZ Utils backdoor among them, arrived exactly this way: a trusted package, a routine
update, a change whose description bore no relation to its effect. Writing tests for code you did not
write is slow, tedious and never prioritized, so it does not happen.

**Current workaround:** Konflux gives hermetic builds, a complete bill of materials, signed provenance
and policy gates: it says precisely what is in the product and nothing about whether it works. Teams
bump dependencies on trust, run their own suite, which rarely touches the dependency, and read
changelogs. Commercial AI test tools cover one language each, run outside the pipeline and produce no
provenance; the best-known open one is abandoned. Nothing, open or commercial, tests a dependency
upgrade differentially for an application.

**Impact of inaction:** Regressions and vulnerabilities in code nobody looked at keep reaching
production and are found by customers. Every dependency bump stays a judgement call made without
evidence, so upgrades are delayed and known vulnerabilities stay open longer. When a customer or a
regulator asks what we verified about the code we ship, the answer for most of it is nothing, with no
record to point at.

**Impact of action:** Every incoming change arrives with tests that ran, a plain-terms verdict and a
signed record, within hours. Known vulnerabilities get a test that proves the fix and a draft VEX
statement backed by it. Upgrades get faster and safer, incidents from unread code fall, and the proof of
testing travels with the product for anyone downstream to check. The tests that earn their keep join
the standard suite, so the asset grows with every run.

## Proposed solution

**Landing BUs:** Trusted Software Supply Chain (the evidence chain: provenance, VEX, SLSA), Red Hat
OpenShift AI (the model serving and the agent runtime), and the Konflux and Developer tooling teams
(the pipeline it runs in). To be confirmed with the sponsor.

**Aligned TDPs:** to be named with the sponsor; the natural fits are the supply chain security and
trusted AI plans.

**Considered alternatives:** IBM Research's test generators, the closest match, ship only inside watsonx
Code Assistant, for Java. The best-known open source AI test generator is abandoned and copyleft.
Commercial tools cover one language each, do not run in our pipeline and produce no provenance. Buying
would give a fraction of the capability and none of the evidence chain. The components underneath, the
resolvers, sandboxes, mutation and coverage tools, attestation formats and open models, are open and
maintained, several of them Red Hat's; what did not exist was the assembly. The full survey is in the
[landscape](04-landscape.md).

**Solution overview:** A change arrives, a pull request or a new dependency version, named by
repository and two refs. The harness resolves the dependency graph at both, looks every version up for
advisories, and scores each package's risk to set a budget. A model, given facts from static analysis
rather than asked to guess, writes characterization, negative and vulnerability-targeted tests through a
tool-using loop. Every candidate runs in a sealed sandbox with no network and no secrets, twice on the
new version and once on the old, so a fix is proven only by a test that fails on the vulnerable version
and passes on the fixed one. Mutation testing on the lines the tests executed shows how firmly they
hold. Triage classifies every verdict with a confidence and a route, and the run writes its own story:
who, what, why, where, when, and every decision. Tests reach a repository only through a pull request a
person merges; the harness never merges, publishes or deletes. Every accepted test carries a signed
in-toto record and a sealed UDLM record, and the reviewer's decision is read back as evidence. The
harness also reads the repository's own CI and states where it is provably short of what validating a
test needs, with the fix, and it measures every model and prompt on a public table before either
becomes a default. It is built and has run end to end on real repositories, for Python and Go, on a
workstation and as a Tekton pipeline on OpenShift; twenty-eight of its own failures are written down,
each with a check that runs before every run.

**Timeline & Milestones:**

1. **Pilot, weeks 1 to 6.** Two product services on Konflux, our own code and direct dependencies,
   triggered from the pull request, review packets as PR comments. Value from the first run: a verdict
   and a signed record on every dependency bump, and the two pipeline findings on each service. Exit:
   generated tests build more than 80 percent of the time, at least one real finding, reviewer feedback
   from both teams, and no default model or prompt changed except by the evaluation table.
2. **First-party at scale, weeks 7 to 12.** Every pull request in the pilot repositories, unattended;
   the test overlay repository and the test pull request as the standard path; the remaining pipeline
   questions. Value: tests on the team's own changes without anyone pressing a button.
3. **Direct dependencies, weeks 13 to 20.** Every bump, pre-flight gates, CVE-targeted tests and VEX
   drafts on every advisory, SLSA Build L3 on the records. Value: every known vulnerability in a direct
   dependency answered with a test or a stated gap.
4. **Transitive dependencies, weeks 21 to 30.** Reachability and risk scoring across the whole graph,
   cheap snapshots where we do not reach, full effort where we do.
5. **Continuous operation, week 31 on.** Scheduled rescans, the remaining ecosystems, upstream
   contributions of the tests that earned their place.

Durations assume a team of two to four engineers and are replaced by measured velocity after the pilot.

**Definition of Done:** The blueprint is done when a product team can point it at a repository and a
pull request and receive, without anyone from the harness team involved, a review packet, a test pull
request and signed records that Conforma verifies at release; when the two reference jobs, python-jose
on frc-scheduler-server and kin-openapi on control-plane, are rerun on the candidate release and match
or beat the published baselines; when every entry of the failure register passes as the first step of
every run; when at least one regression or vulnerability caught by a harness test that nothing else
would have caught has been reported; and when the pipeline is a Konflux integration-service task with a
documented model endpoint per language, so that it can ship as part of Trusted Software Supply Chain
or stand as a product of its own.
