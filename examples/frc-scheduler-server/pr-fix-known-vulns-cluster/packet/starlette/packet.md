# Review packet: starlette 0.41.3 -> 0.41.3

**In plain terms.** This change leaves starlette at 0.41.3, which has 7 known vulnerabilities the application is exposed to. The harness could not prove any of the 7 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `3d9fa72b859b`. Generated 2026-09-13T22:57:49+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
starlette at depth 2, change `unchanged`, reachable from first-party code: **true**
(8 production references). Risk score 80, budget full.
API diff: +0 / -0 / ~0, 0 breaking.
Advisories: 14 open at head, 0 on the replaced version.

## What was tested
0 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 0 pass on head, 0 flaky,
0 fix-pinning confirmed, 0 lines of the package covered. Model: `n/a`.
Mutation: not run.

## Findings
- **security** (0.9): starlette 0.41.3 has 14 open advisories at head; reachable=true. Route: Product Security. Evidence: `analyze/starlette/vulns.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| none | | | | | |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2025-54121 | affected | open at head; reachable=true; fixed in ['0.47.2'] |
| CVE-2025-62727 | affected | open at head; reachable=true; fixed in ['0.49.1'] |
| CVE-2026-54283 | affected | open at head; reachable=true; fixed in ['1.3.1'] |
| CVE-2026-48710 | affected | open at head; reachable=true; fixed in ['1.0.1'] |
| CVE-2026-54282 | affected | open at head; reachable=true; fixed in ['1.3.0'] |
| CVE-2026-48818 | affected | open at head; reachable=true; fixed in ['1.1.0'] |
| CVE-2026-48817 | affected | open at head; reachable=true; fixed in ['1.1.0'] |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet (section 8.3). Retirements: relevance stage not run.

## Artifacts
- tests as a patch against the overlay layout: `packet/starlette/tests.patch`
- verdicts and logs: `execute/starlette/results.json`, `execute/starlette/{new,new-rerun,old}/`
- facts: `analyze/starlette/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/starlette/manifest.json`, every prompt and response under `generate/starlette/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/starlette/statement.json` (after stage attest)
