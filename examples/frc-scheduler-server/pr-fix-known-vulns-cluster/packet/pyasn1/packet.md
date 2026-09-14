# Review packet: pyasn1 0.6.4 -> 0.4.8

**In plain terms.** This change moves pyasn1 from 0.6.4 to 0.4.8, a version with 4 known vulnerabilities. That is a downgrade. The harness could not prove any of the 4 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `3d9fa72b859b`. Generated 2026-09-13T22:57:49+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
pyasn1 at depth 2, change `bumped`, reachable from first-party code: **unknown**
(0 production references). Risk score 90, budget full.
API diff: +90 / -142 / ~12, 146 breaking.
Advisories: 8 open at head, 0 on the replaced version.

## What was tested
0 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 0 pass on head, 0 flaky,
0 fix-pinning confirmed, 0 lines of the package covered. Model: `n/a`.
Mutation: not run.

## Findings
- **security** (0.95): pyasn1 downgraded 0.6.4 -> 0.4.8 into a version with 8 known advisories. Route: Product Security. Evidence: `analyze/pyasn1/facts.json`
- **security** (0.75): pyasn1 0.4.8 has 8 open advisories at head; reachable=unknown. Route: Product Security. Evidence: `analyze/pyasn1/vulns.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| none | | | | | |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2026-59885 | under_investigation | open at head; reachable=unknown; fixed in ['0.6.4'] |
| CVE-2026-59886 | under_investigation | open at head; reachable=unknown; fixed in ['0.6.4'] |
| CVE-2026-30922 | under_investigation | open at head; reachable=unknown; fixed in ['0.6.3'] |
| CVE-2026-59884 | under_investigation | open at head; reachable=unknown; fixed in ['0.6.4'] |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet (section 8.3). Retirements: relevance stage not run.

## Artifacts
- tests as a patch against the overlay layout: `packet/pyasn1/tests.patch`
- verdicts and logs: `execute/pyasn1/results.json`, `execute/pyasn1/{new,new-rerun,old}/`
- facts: `analyze/pyasn1/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/pyasn1/manifest.json`, every prompt and response under `generate/pyasn1/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/pyasn1/statement.json` (after stage attest)
