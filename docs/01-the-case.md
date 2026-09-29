# The case

**For:** CTOs, VPs of Engineering, CISOs, and anyone deciding whether to fund this. Fifteen minutes.

## What I am asking for

A six-week pilot on two services already building on Konflux, a named executive sponsor, a compute
budget with a model endpoint fit for Go, and two product teams who will review what the harness
produces. The harness exists and has run end to end on real repositories in the lab; the pilot puts it
on product services and measures it there, against real reviewers, not against my opinion.

## What exists, and what it has shown

The implementation covers every stage for Python and Go, on a workstation and as a pipeline on
OpenShift, and every run explains itself in plain terms. Three results from the lab set expectations:

- **On a real dependency bump it works end to end.** For python-jose 3.3.0 to 3.4.0 the harness
  proposed seven tests and proved three known vulnerabilities fixed; a reviewer merged all seven, and
  the signed records of that decision exist. That is the whole loop, once, on real code.
- **The model is the risk, and it is measured, not assumed.** On a Go package the 27B model wrote no
  compilable test; the 235B wrote clean Go with one wrong API detail per file and proved no advisory,
  at ten to twenty times the model time. Every model and every prompt now earns its place on one
  table, and the first prompt change we thought would help lost on it. That table is what the pilot
  reads.
- **The harness catches its own defects.** Twenty-eight failures are in a register, each with a fix
  and a check that runs before every run. Nine of them came from the last three weeks of real runs.

## The problem, with numbers you can check

A mid-sized Go or Java service resolves several hundred to a few thousand packages. Our engineers chose
perhaps fifty of them. The rest arrived as dependencies of dependencies. Nobody on our side has read
them. Nobody on our side has tested them. When one of them changes behavior in a minor version, we find
out in production.

This is not a theoretical risk. The most serious supply chain incidents of the last several years,
including the XZ Utils backdoor of 2024, arrived through exactly this path: a trusted package, a routine
update, a change whose description bore no relation to its effect.

We already have strong tooling for one half of this problem. Konflux gives us hermetic builds, a
complete bill of materials, signed provenance at SLSA Build Level 3, and policy gates. It tells us
precisely what is in the product. It tells us nothing about whether any of it works, or whether a new
version still does what the old one did.

## What the harness adds

The harness fills the testing half. For every incoming change, at every depth, it produces evidence:

| Question | How the harness answers it |
|---|---|
| What does this code do? | AI-written characterization tests, run and scored |
| Did it change from the version we had? | The same tests run against old and new, results compared |
| Does it fail safely? | Negative tests with malformed and hostile input |
| Are we exposed to what is already known to be wrong with it? | CVE-targeted tests at our own call sites, producing draft VEX statements |
| Is it doing anything it has no reason to do? | Sandbox observation and pre-flight scans, routed to security |
| Can we prove all of this later? | Signed provenance for every test, attached to the build attestation |

## Why AI, and why now

Writing tests for code you did not write is slow, tedious, and rarely prioritized. That is why it does
not happen. Large language models are now good enough at reading unfamiliar code and writing plausible
tests that the bottleneck moves from writing to verifying. Verifying is something we can automate:
compile it, run it, mutate the code and see whether the test notices, compare old and new. A test that
survives that gauntlet is worth a reviewer's minute. One that does not is discarded before anyone sees
it.

The research published in 2025 and 2026, much of it from IBM Research, shows this loop works when the
model is given facts from static analysis rather than asked to guess. The tools that implement it are
either proprietary or abandoned. The components underneath them are open, maintained, and in several
cases already Red Hat's. What does not exist is the assembly. That is what this project builds.

## Why not just buy something

I looked. The [landscape](04-landscape.md) document lists everything I found. The short version:

- The best-known open source AI test generator is abandoned and copyleft-licensed.
- IBM's research tools are the closest match and ship only inside watsonx Code Assistant, for Java.
- Commercial tools cover one language each, do not run in our pipeline, and produce no provenance.
- Nothing, open or commercial, does differential testing of a dependency upgrade for an application.
  Linux distributions do it at their scale. Nobody does it for a service.

We would be buying a fraction of the capability and none of the evidence chain.

## What it costs

| Item | Pilot (6 weeks) | Steady state |
|---|---|---|
| People | 2 engineers, part-time reviewer time from 2 product teams | A small team owning the pipeline, prompts, and adapters; reviewer time scales with findings, not with packages |
| Compute | Sandboxed runs for two services, depth 0 and 1 only | Risk-weighted: full effort on what we reach, cheap snapshots on the rest; budgeted per ecosystem with alerts |
| Model usage | Metered, reported per run | Metered, with a cheaper model for high-volume classification |
| Risk | Low: advisory only, nothing merges; the human gate has been exercised on a real pull request | Managed: only security findings block, everything else advises |

I have deliberately not put a currency figure here because the pilot exists to produce one. The cost
per work item is a tracked metric from day one.

## What it returns

1. **Fewer incidents from code we never looked at.** The number I will report quarterly is regressions
   and vulnerabilities caught by harness tests that nothing else would have caught.
2. **Faster, safer upgrades.** A dependency bump arrives with a one-page packet saying what changed,
   what broke, and what to do. In the lab that takes one and a half to three hours on a self-hosted
   model, most of it model time; a faster model endpoint is the lever.
3. **Proof.** Every test carries a signed record. Every known vulnerability gets a VEX statement backed
   by a test or a reachability analysis. When a customer or regulator asks what we verified, we show them.
4. **A growing asset.** Tests that earn their keep are promoted into the standard suite. The harness gets
   cheaper and the suite gets stronger with every run.

## What could go wrong, and what I have done about it

| Risk | Mitigation in the plan |
|---|---|
| The tests are shallow and just restate the code | Mutation testing on the lines the tests ran: a test that catches no injected bugs is marked weak. Differential runs. Measured so far: 0.6 on Go, 0.25 to 0.4 on Python. |
| The model is not good enough for a language | Fitness is measured per model and prompt on reference jobs and published; a model that proves nothing on Go is not used for Go. The pilot budgets a model endpoint fit for each language. |
| Reviewers drown | Risk-weighted budgets, one-page packets, advisory by default. Only security findings block. |
| A malicious package escapes the sandbox | No network, no secrets, kernel-isolated runtimes, disposable containers, pre-flight scans before anything executes. |
| The AI is manipulated by text hidden in a package | Everything from outside is treated as data, never as instructions. The agent has no tool that acts outside the sandbox. A manipulation attempt is itself a security finding. |
| Cost runs away on transitive dependencies | Depth policy, reachability analysis, cheap snapshots as the default, budget alerts. |
| We claim provenance we cannot prove | Conforma verifies every attestation. SLSA levels are measured by the platform, not declared by us. |
| Teams do not trust AI-written tests | Every test is labeled, every test is human-approved, and I publish what the tests catch. |
| A component we reuse is abandoned | Every reused component shipped a release in 2026. Adapters isolate each one. |

## The decision

Fund six weeks. Judge the result on the benchmark and the reviewer feedback. Then decide about the next
phase. The full phasing is in the [roadmap](07-roadmap.md).
