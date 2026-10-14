# Decision record

**Status:** 2026-10-14. The positions settled during the review of the business case and the research that
followed it, each with the reason and what it rules out. Engineering should not have to reconstruct
these from the case, the research notes or a conversation.
**Owner:** Chris Roadfeldt.

Each entry: what we decided, why, and what it rules out. Numbers are stable; new decisions append.

**D1. The product delivers evidence at the gate.** Every pull request arrives with the tests that ran on
both sides of the change and a signed record, and the person at the gate decides with proof in hand.
*Why:* the value is in the results, not in the tests as artifacts; a gate requires evidence. *Rules out:*
framing the harness as a test generator, or as something that stops at handing tests over.

**D2. The suite is the asset; toil is minimized, not eliminated.** The harness writes the tests nobody
will write by hand and does the running and the proving; a person keeps the judgment. *Why:* most shipped
code has no tests and never will by hand; and no one would believe a promise that a reviewer never has to
look. *Rules out:* measuring the harness by how many tests it writes; it is measured by review time per
finding.

**D3. Dependency verification is the engine, applied in layers.** The same test runs on both sides of a
change, in our code first, then direct dependencies, then transitive ones. *Why:* the differential run is
what nothing else does for an application, and the layers are how the pilot grows. *Rules out:* dropping
first-party code from scope, or treating all three layers as one phase.

**D4. Three output states, nothing silent.** Every behaviour a change reaches ends in exactly one of
validated, for your environment, or a stated gap with its reason. Validated means a test ran on both
sides, ran consistently, and a mutant inside its closure was killed by that test. *Why:* a gate that hears
"we could not validate this, here is why" is better off than one that hears nothing, and the harness must
never imply coverage it did not earn. *Rules out:* counting an executed line as validated; reporting
"accepted" as if it meant proven. The dry run on the published python-jose run showed zero validated under
this rule, which is why stratified sampling and the private-callee closure became requirements.

**D5. Tests declare their needs; the testbed honours and enforces them.** Four tiers, none, localhost,
network, machine, after autopkgtest's restrictions and Google's test sizes. A need the testbed lacks is a
skip with its reason, handed to the team. An undeclared connection is a defect in the test, pytest-socket's
rule. *Why:* generated tests are untrusted code and the sandbox must be sealed; the industry solved how to
reconcile that with tests that genuinely need more. *Rules out:* running network tests in the harness; and
treating an undeclared network call as the environment's fault.

**D6. The `machine` tier is admitted unavailable on VM-hosted clusters.** Kata needs bare-metal nodes;
gVisor has no runtime on OpenShift. Where neither exists, machine tests go to the team like network tests.
*Why:* the research established it; promising kernel isolation we cannot provide would be a lie in the
evidence. *Rules out:* "gVisor or Kata at depth 1" as a blanket rule.

**D7. Testbed failure is its own status, never a verdict about the test or the package.** At the run level
and per test, with a CTRF export where it reads `other`, never `failed`. *Why:* autopkgtest's exit 16,
Bazel's remote failure, Testing Farm's request error; every mature runner keeps the environment's failure
apart. *Rules out:* a sandbox breakage reported as a defect in the package.

**D8. The gate reads two inputs, and either can say no.** The pipeline's own result, which now includes
the harness's tests running in the team's environment, and the harness's verdict; what counts as
inadequate is the team's policy. *Why:* the harness never merges and never decides alone, but a negative
from it is as legitimate a reason to hold a merge as a failing build. *Rules out:* "the harness never
blocks"; and a `neutral` check conclusion for anything meant to hold a merge, since branch protection
passes neutral.

**D9. The team owns every number.** Mutants, repeats, tests per file, model time per change, which gaps
block, which dependencies get full effort, what the testbed provides: settings in a file in the team's
repository, with defaults the harness ships and explains. *Why:* the person at the gate decides the
evidence standard too. *Rules out:* harness-wide constants a team cannot change.

**D10. Our lab timings justify nothing.** Cost is described by its shape, model time dominates and scales
with the inference hardware, never by the minutes or hours we measured on consumer GPUs. The harness
measures its environment at run start and plans to fit the time it is given, highest-value work first.
*Why:* a team on a hosted frontier model and a team on a laptop live in different worlds. *Rules out:*
"minutes to hours" claims in any document.

**D11. Fitness is validated, never assumed, and the harness learns from two kinds of failure.** No model
or prompt set becomes the default without winning the measured table; every test records the model and
prompt that made it, and the reviewer's decision is read back against that record. The harness's own
failures go in the register with a check that runs before every run. *Rules out:* changing a default on
judgment; a failure mode without a self-check.

**D12. Coverage of behaviour is the extended goal; line coverage is the map of gaps, not the score.**
The results each reached function can produce, as ISTQB defines coverage items, each with a test that
checks it, proven by mutation, or the gap named. *Why:* Google and DO-178C use structural coverage to find
what requirement-based tests missed, never as the target; a model told to maximize line coverage will find
the empty-assertion path first. *Rules out:* "100 percent test coverage" as a goal.

**D13. Standards first; UDLM is enablement.** in-toto, SLSA and OpenVEX are the record a reader must
understand; the same evidence can be exported as UDLM records that link into the wider lifecycle chain.
*Why:* reviewers who have never heard of UDLM should not need it to understand the product. *Rules out:*
UDLM as a requirement in the case or the definition of done.

**D14. Reference jobs are examples of the proof of concept; the pilot establishes its own.** Done is a
standard of behaviour on work never seen before, plus a regression check on the reference jobs, whose known
answers are two-sided (fail-to-pass and pass-to-pass). *Why:* most work is novel; a number to beat only
exists for work done before; one-sided known answers accept regressions. *Rules out:* python-jose and
kin-openapi as deliverables.

**D15. The pipeline finding is scoped.** The harness reads the repository's CI because it must, to propose
a test that will run there, and reports only where the pipeline cannot run or validate what it proposes.
*Rules out:* the harness as a CI audit tool.

**D16. Product agnostic.** The harness runs in the build platform a team already has. Konflux, Tekton,
Conforma and Trustify appear as examples, never as the assumption. *Rules out:* "runs on Konflux" in any
document.

**D17. The blueprint is stable at v0.28.** The remaining queue is implementation; a slice adds its
specification row and queue line, and the design does not change without the maintainer's decision.
*Rules out:* version bumps for implementation slices; principle changes without review.

**D18. The harness only tests.** It never fixes production code, merges, publishes a VEX statement or
deletes a test. A separate fix pipeline consumes what it hands over, and the fix comes back through the
harness like any other change. *Why:* evidence must be independent of the thing it judges. *Rules out:*
any code path that changes production code or publishes a statement.
