# Use case: verified fix ingestion

**Status:** Proposal, 2026-10-14. An extension of the [blueprint](03-blueprint.md) at v0.28; it changes
nothing the blueprint says the harness is, and it adds one trigger, two verdicts and one relationship.
**Owner:** Chris Roadfeldt.
**For:** the people who decide whether to build it, and the engineers who would.

## The problem

When a publisher says a vulnerability is fixed, we take its word. The statement arrives as a
security advisory, a VEX document or an advisory database entry: "fixed in version X." Our scanners
stop flagging the package once we move to X, and the matter closes. Nobody runs anything. The fix
may be incomplete. The fixed version may not resolve into our product the way the publisher built
it. The fix may land in a code path our product never reaches while the one we do reach is still
open. In each case we find out the way we always have: later, from someone else.

The harness already has the one primitive this needs. A fix is proven by a test that fails on the
vulnerable version and passes on the fixed one. A publisher's "fixed" claim is exactly the hypothesis that
test is built to check.

## The use case in one paragraph

A publisher, an upstream project, a distribution or a vendor, publishes a claim that a vulnerability
is fixed in an artifact. The harness reads the claim, checks the artifact's provenance, and finds
every product of ours that ships the vulnerable version. For each one it writes and runs the tests
that would prove the claim in our environment against our usage. An exposure test runs at our call
site, and a fix-pinning test fails on the version we ship and passes on the claimed fix. Each claim
ends in one verdict with evidence, and each verdict becomes our own VEX statement, signed,
referencing the publisher's. A claim we cannot confirm is disputed with a reproducer, not quietly
accepted.

## What arrives, and what we do first

**Inputs.** Claims in the formats publishers already use: CSAF VEX documents, OpenVEX statements, and
advisory database entries that carry fixed ranges (OSV and the ecosystem feeds behind it). Each names a
package, a vulnerability, a vulnerable range and a fixed version or artifact. Optionally the artifact
itself, with provenance: a signed in-toto or SLSA attestation, a Sigstore signature, or a distribution's
signed metadata.

**Trust before verification.** Before anything runs, the harness checks what it can about the claim's
origin: the document's signature, the artifact's signature and provenance, the publisher's identity against
the list the team trusts. The result is recorded on the claim as verified, unverified or failed, and it
travels with every verdict. A claim with failed provenance is still processed, so that we know what it
would have proven, but its verdict carries the label and the gate policy can treat it accordingly. The
harness never turns an unverified input into a verified-looking output; that is principle 10.

## How it maps onto the pipeline

Everything below is the existing pipeline with a different trigger. The stages, the sandbox, the
differential run, the records and the rules are the blueprint's.

| Stage | What it does for a claim | New or reused |
|---|---|---|
| Trigger | A new or changed claim from a publisher feed, or a scheduled sweep of the feeds the team follows | New: a claims source |
| 0 Self-verification | Unchanged | Reused |
| 1 Intake | For each product that ships the vulnerable version: a work item naming the package, the version we ship, the claimed fixed artifact, and the claim. Products come from the SBOM store (Trustify, in the example). The fixed version is resolved into the product's graph the way the fixed-candidate path already does | Reused, with a claim mode |
| 2 Analysis | The advisory and the fix diff between the version we ship and the claimed fix; our call sites; the security linter on the changed code; the behaviour worklist for the functions the advisory names | Reused |
| 3 Generation | CVE-targeted tests only: exposure at our call site, fix-pinning across the two versions | Reused |
| 4 Validation execution | The differential run, both versions, sealed, with the roles taken from the claim: the version we ship is vulnerable, the claimed artifact is fixed | Reused |
| 5 Triage | Two new classes, `claim-confirmed` and `claim-disputed`, beside the existing ones; the accounting unchanged | New classes |
| 6 Review | Our VEX statement per claim, with a relationship to the publisher's statement; the packet; the signed record | Reused, one field added |
| 7 Feedback | A disputed claim that the publisher later corrects, or that a reviewer overturns, is read back as a labelled example | Reused |

## The verdicts

Every claim ends in exactly one, with the evidence that produced it. Nothing is silent.

| Verdict | Meaning | What we publish |
|---|---|---|
| **Confirmed** | The fix-pinning test fails on the version we ship and passes on the claimed fix, at our call site where we have one | VEX `fixed`, referencing the publisher's statement, with the test |
| **Disputed** | The test that fails on the version we ship still fails on the claimed fix, or the claimed fix does not resolve into our product | VEX `affected` or `under_investigation`, with the reproducer; routed to Product Security and, if the team chooses, to the publisher |
| **Not reachable** | Our product never calls the vulnerable code; the exposure test cannot be written at a call site because there is none | VEX `not_affected` with `vulnerable_code_not_in_execute_path` and the reachability evidence, marked approximate where it is |
| **Could not verify** | The model could not construct a trigger for the vulnerability (the register's GF-012), or the testbed failed | No status change; the gap stated with its reason, so the claim is not trusted by default either |
| **Provenance failed** | The claim or artifact did not verify; one of the four verdicts above is still computed and labelled | As above, with the label; the gate policy decides what it is worth |

The publisher's own statement is never republished as ours. Our statement says what we ran, where, and
what happened, and it names theirs.

## Where it runs, and how often

As a scheduled sweep, not only on demand. The feeds the team follows are read on a cadence the team sets;
each new or changed claim is matched against the products whose SBOMs are in the store; each match is a
run. One claim about a widely used package becomes many runs, one per product, because the answer is per
product: the same fix can be confirmed for one and disputed for another that pins a different dependent.
Effort follows risk as everywhere else: a product that does not reach the vulnerable code gets the
reachability verdict without a generation budget.

## High-level implementation

What has to be built, in the order I would build it. Sizes are the queue's: small is a day or two, medium
a week, large more.

| # | Change | Where | Size |
|---|---|---|---|
| F1 | **Claims source.** Readers for CSAF VEX, OpenVEX and OSV fixed ranges, normalised to one claim record: publisher, vulnerability ids, package, vulnerable range, fixed version or artifact digest, statement reference, document signature | `sources/claims.py`, new | Medium |
| F2 | **Provenance check.** Verify the claim document's signature and the artifact's attestation or signature with the same tooling the release gate uses (Conforma and Sigstore, in the example); record verified, unverified or failed on the claim | `sources/provenance.py`, new | Medium |
| F3 | **Product matching.** For a claim, the products whose SBOMs include the vulnerable range, from the SBOM store's API (Trustify's, in the example) or from a directory of SBOMs | `sources/sboms.py`, new | Medium |
| F4 | **Claim mode in intake.** A work item built from a claim and a product: the shipped version as the vulnerable side, the claimed artifact as the fixed side, resolved into the product's graph through the existing fixed-candidate path; `harness claim <claim-ref> --product <sbom>` and `harness sweep` | `stages/intake.py`, `cli.py` | Medium |
| F5 | **Roles from the claim.** The CVE roles already distinguish upgrade, downgrade and candidate; a claim is a fourth direction with the same two sides, so the verdict logic needs the name, not new rules | `stages/generate.py` (`cve_roles`), `stages/execute.py` | Small |
| F6 | **Two triage classes.** `claim-confirmed` and `claim-disputed`, with routes: confirmed to the VEX draft, disputed to Product Security with the reproducer | `stages/triage.py` | Small |
| F7 | **Our VEX statement with a relationship.** One field on the draft: the publisher's statement it answers (document id, statement id, publisher), and the verdict's evidence as the justification | `stages/packet.py` (`_vex`) | Small |
| F8 | **Claims on the dashboard.** Claims received, verified, confirmed, disputed, not reachable, could not verify; time from claim to verdict; disputed rate per publisher | `tools/build-dashboard.py`, `runindex.py` | Medium |
| F9 | **Team settings.** The feeds followed, the publishers trusted, the sweep cadence, the products in scope, what provenance failure means at the gate | the configuration contract (queue Q8) | Small |

Nothing in generation, execution, mutation, the sandbox, the accounting, the records or the self-checks
changes. The register grows only if a run shows a new way to fail.

## What does not change

- The harness only tests. It does not apply the publisher's fix, does not move the product to the fixed
  version, and does not publish a VEX statement; Product Security confirms ours as it confirms every other.
- The boundary with the fix pipeline holds. A disputed claim hands the fix pipeline the same thing a
  vulnerability does: a failing test with both runs kept, and the publisher's claim as context.
- The fifteen principles hold unchanged. The one this use case leans on hardest is the tenth: the chain of
  trust is extended, never laundered, so an unverified claim never becomes a verified-looking statement.

## Required changes to the blueprint, if adopted

Three lines, none of them a change of design. They are listed here and not applied, because the blueprint
stands at v0.28 until this proposal is accepted.

1. **Scope.** One row in the table of what is in scope and what triggers it: "A published fix claim, from
   a publisher's advisory, VEX or database feed; on publication or on a scheduled sweep."
2. **Triage classes.** `claim-confirmed` and `claim-disputed` added to the list.
3. **Known vulnerabilities become evidence.** One sentence: a publisher's fixed claim is verified the same
   way, by a fix-pinning test in our environment, and our VEX statement names the claim it answers.

The specification would gain one requirement: a claim MUST end in exactly one of the five verdicts with its
evidence and provenance label, and our VEX statement MUST reference the publisher's.

## Risks and limits, stated

- **The model cannot always build the trigger.** The register's GF-012 is the honest end of some claims:
  "could not verify" with the reason, never a default to trust. The rate is a fitness measure for the model
  and prompt set, on the evaluation table like every other.
- **The claimed fix may not resolve into our product.** The fixed-candidate path reports what had to move
  and what would not; that is a disputed claim with a precise reason, and often the more useful finding.
- **Reachability is approximate**, especially for Python. A "not reachable" verdict carries the evidence and
  says where it is inferred, and the team's policy decides whether an inferred not-reachable closes a claim.
- **Claims without provenance** are the common case today. The label is the honest answer; refusing to
  process them would hide the evidence we can still produce.
- **Volume.** One claim can fan out to every product that ships the package. The scheduled sweep, the
  reachability verdict without a generation budget, and the planner (queue Q9) keep it bounded; the
  dashboard shows the queue.

## How it would be judged

- Every claim in the followed feeds has a verdict within the sweep cadence, and no claim is silent.
- The disputed rate per publisher, over time; a dispute the publisher later confirms is the use case paying
  for itself.
- Time from a claim's publication to our verdict, per product.
- The share of our VEX statements backed by a test that ran, against the share that rest on reachability
  alone.

## A pilot shape

One ecosystem, one SBOM store, one publisher feed the team already reads, and the products that ship the
ten most common packages in that feed. Eight weeks after the harness pilot in the [case](01-the-case.md),
since it reuses the pilot's model endpoint, sandbox image and bot identity. Exit: every claim in the feed
for those packages has a verdict, at least one claim disputed with a reproducer a person confirmed, and
Product Security has accepted at least one of our statements as the basis for theirs.
