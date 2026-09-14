# Review packet: ecdsa 0.19.2 -> 0.19.2

**In plain terms.** This change leaves ecdsa at 0.19.2, which has 1 known vulnerability the application is exposed to. The harness could not prove any of the 1 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `3d9fa72b859b`. Generated 2026-09-13T22:57:49+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
ecdsa at depth 2, change `unchanged`, reachable from first-party code: **unknown**
(0 production references). Risk score 65, budget full.
API diff: +0 / -0 / ~0, 0 breaking.
Advisories: 2 open at head, 0 on the replaced version.

## What was tested
0 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 0 pass on head, 0 flaky,
0 fix-pinning confirmed, 0 lines of the package covered. Model: `n/a`.
Mutation: not run.

## Findings
- **security** (0.75): ecdsa 0.19.2 has 2 open advisories at head; reachable=unknown. Route: Product Security. Evidence: `analyze/ecdsa/vulns.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| none | | | | | |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2024-23342 | under_investigation | open at head; reachable=unknown; fixed in no fixed version published |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet (section 8.3). Retirements: relevance stage not run.

## Artifacts
- tests as a patch against the overlay layout: `packet/ecdsa/tests.patch`
- verdicts and logs: `execute/ecdsa/results.json`, `execute/ecdsa/{new,new-rerun,old}/`
- facts: `analyze/ecdsa/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/ecdsa/manifest.json`, every prompt and response under `generate/ecdsa/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/ecdsa/statement.json` (after stage attest)
