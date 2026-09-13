# AI Test Harness: Blueprint Business Case

**For:** the FlightPath blueprint review. Written to the Blueprint Business Case template; every claim
below is backed by a document or a run in this repository.

## Blueprint identity

**Owner:** Chris Roadfeldt

**Elevator pitch:**

Most of the code in any product was written by someone else, and nobody on the customer's side has
tested it: a typical service pulls in hundreds of packages, most of them several layers removed from
anything an engineer ever read. The AI Test Harness is a pipeline step in the software supply chain
that uses AI agents to write tests for every piece of incoming code, including dependencies at any
depth, runs them in a sealed sandbox against the old and the new version, scores whether the tests are
any good, and hands a one-page packet to a human to approve. Every test carries a signed provenance
record, every known vulnerability gets a draft VEX statement backed by a test, and nothing merges,
publishes, or is deleted without a person. It runs on Konflux, targets SLSA Build Level 3, and already
works on real code.

## Problem statement

**Customer name:** [customer name]

**Customer stakeholder:** [name and title]

**Customer pain:**

Teams test what they write and trust what they import, and most of what they ship is imported. When a
dependency changes behavior in a minor version, or a fix for one package quietly downgrades another,
they find out in production. Build platforms now prove what is in a product, with SBOMs and signed
provenance, but nothing proves whether any of it works or whether a new version still does what the
old one did. Regulators and customers ask for evidence of testing, and for known vulnerabilities they
ask for VEX statements with something behind them; today those are opinions written by hand, if they
exist at all.

**Current workaround:**

Vulnerability scanners produce lists of CVEs with no evidence of exposure. Dependency bumps are
merged on green builds that test only first-party code. Upgrades that break are found by users.
Security teams write VEX statements from reachability guesses. Writing tests for third-party code by
hand is so slow that it is never prioritized, and the few commercial tools that generate tests cover
one language each, run outside the pipeline, and produce no provenance.

**Impact of inaction:**

Incidents from dependencies nobody looked at continue, and the worst supply chain incidents of recent
years came through exactly this path. Upgrades stay slow because nobody can say what changed. Audit
questions about what was verified get answered with process descriptions rather than evidence. The
provenance the build platform already produces stops at the build step, so the customer pays for
half of a chain of trust.

**Impact of action:**

A dependency change at any depth arrives with a packet within two hours that says what changed, what
broke, what is proven fixed or proven exposed, and what to do. Known vulnerabilities carry VEX
statements backed by tests. Every accepted test is a signed record attached to the build, in the
same data model the rest of the estate uses. Reviewers spend their minutes on evidence rather than
on reading unfamiliar code, and the test suite gets stronger with every run.

## Proposed solution

**Landing BUs:** [proposed: the Konflux and Trusted Software Supply Chain organization; Lightwell, whose
stated remit of validating fixes across open source at volume this blueprint sits inside. To be
confirmed by the owner.]

**Aligned TDPs:** [proposed: Application Platform. To be confirmed by the owner.]

**Considered alternatives:**

- The best-known open source AI test generator: abandoned, copyleft-licensed.
- Research tools from IBM (ASTER, SAINT): the closest match, shipped only inside a commercial
  assistant, for one language.
- Commercial test generators: one language each, outside the pipeline, no provenance.
- Scanners alone: lists of CVEs, no evidence of exposure, no differential testing.
- Doing nothing new and relying on first-party tests: the current state, and the problem.

Nothing, open or commercial, does differential testing of a dependency upgrade for an application.
Distributions do it at their scale; nobody does it for a service. The full survey is in
[the landscape](04-landscape.md) and the decision per capability in [the capability map](05-capability-map.md).

**Solution overview:**

The harness is one more integration test in Konflux, not a new pipeline. Every incoming change,
whether a first-party pull request or a version bump five layers deep, goes through the same stages:
the harness verifies itself, then intake, analysis, generation, execution, triage, review, and
feedback. Intake resolves the full dependency graph in the project's own interpreter image, diffs it
against the last known-good state, and checks every package version against OSV. Analysis gathers
facts with tools, never with a model: the API surface, the contract diff, the application's own call
sites, the advisories with their fixed versions, and the exact diff between the two versions of the
package. Generation has an AI agent write tests in the ecosystem's own framework so they run with the
team's existing commands; the agent has read-only tools and a sandbox run, under a budget, and every
prompt and result is recorded. Execution runs the tests in a sealed container with no network and no
secrets, on the new version, again to catch flakes, and on the old version, then mutates the package
to measure whether the tests would notice a bug. Triage classifies every result with a confidence
and a route; below threshold, a person decides. The packet is one page: what the change did, what was
proven, what remains unproven, what to do, with the tests as a patch and a draft VEX statement per
vulnerability for Product Security.

The evidence is the product. Every accepted test carries a provenance record, and the same facts are
emitted as records in the Unified Data Lifecycle Model, UDLM, sealed with its tamper-evident chain:
the test, the package, the vulnerability, the run, and the VEX draft. The signed in-toto statement
names each record's head, so a consumer verifies the signature, matches it to the record, and follows
the references. UDLM adopted this shape in its own registry after the first real run produced it.
The harness also tests itself: every way its generator has ever failed is a register entry with a
detector, an automatic correction, and a self-check that runs before every pipeline run and stops it
on failure. Nineteen entries exist today, each written check-first.

On the Red Hat side the blueprint reuses what exists: Konflux with Hermeto, Conforma, Mobster,
Trustify, and Trusted Artifact Signer for the build, SBOM, policy, vulnerability, and signing steps;
OpenShift sandboxed containers and the Kuadrant MCP gateway for isolation and tool governance;
OpenShift AI for serving open models; Tekton Chains for attestation. What the blueprint builds is the
assembly, the generation and triage agents, cross-ecosystem differential testing, the relevance
engine, and the CVE-to-VEX path. It is delivered as an open, opinionated implementation the customer
can run today, with the blueprint and the evidence in one public repository.

It has run on real code. A pull request on a FastAPI service set out to fix four vulnerable packages.
The harness proved one vulnerability closed, found that the change silently downgraded a second
package into a version with eight advisories and proved that exposure with a test, and proved a third
package exposed at head with the upgrade path the customer would need. Three signed attestations,
seventy-six sealed UDLM records, nine of eleven blueprint goals met, and every unproven item stated
as unproven. Details: [the example](../examples/frc-scheduler-server/README.md).

**Timeline and milestones:**

| Milestone | When | Done when |
|---|---|---|
| 1. Pilot on two services, own code and direct dependencies | Weeks 1 to 6 | Generated tests build more than 80 percent of the time; at least one real finding; reviewer feedback from both teams; catch rate on a public benchmark of real breaking upgrades reported |
| 2. First-party at scale | Weeks 7 to 12 | Every pull request in the pilot repositories, unattended; mutation and flake gates; every accepted test carries a signed record |
| 3. Direct dependencies with evidence | Weeks 13 to 20 | Every bump arrives with a packet; every known vulnerability has a VEX statement Product Security confirms more than 80 percent of the time without rework; SLSA Build L3 |
| 4. Transitive dependencies within budget | Weeks 21 to 30 | Full-graph run within budget on both services; cost per work item reported; no release blocked by a false positive for four weeks |
| 5. Continuous operation | Week 31 on | Scheduled rescans; remaining ecosystems; upstream contribution of high-value tests; first quarterly report |

Dates are placeholders from a notional October 2026 start; durations are estimates for two to four
engineers and are replaced by measured velocity after the pilot. Detail: [the roadmap](07-roadmap.md).

**Definition of done:**

The blueprint is done when a dependency change at any depth, in any supported ecosystem, produces
within two hours a signed, human-reviewed packet that says what changed, whether the application is
exposed to anything known, and which tests now guard it; when every accepted test is a UDLM record a
consumer can verify from the attestation; when the harness's own failure register has a passing
self-check for every entry; and when a quarterly report can show what that evidence caught. At that
point it is a product component of the supply chain platform, or a product on its own.

## Checklist

Ensure all following steps are completed before moving to the next step:

- [ ] Create a folder in the FlightPath Shared Drive for this blueprint.
- [ ] Add a filled copy of this file to the blueprint folder.
- [ ] Create a FAQ document in the folder (empty for now; questions from review go there).
- [ ] Add a new slide in the Blueprints deck. The [executive deck](../slides/executive.md) in this
      repository is the source for it.
