# Review packet: weasyprint 63.1 -> 70.0

**In plain terms.** This change updates weasyprint from 63.1 to 70.0, which closes 3 known vulnerabilities. The harness could not prove any of the 3 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `3d9fa72b859b`. Generated 2026-09-13T22:57:49+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
weasyprint at depth 1, change `bumped`, reachable from first-party code: **true**
(6 production references). Risk score 70, budget full.
API diff: +215 / -98 / ~79, 152 breaking.
Advisories: 0 open at head, 6 on the replaced version.

## What was tested
0 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 0 pass on head, 0 flaky,
0 fix-pinning confirmed, 0 lines of the package covered. Model: `n/a`.
Mutation: not run.

## Findings
- none

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| none | | | | | |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2025-68616 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-55073 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-49452 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet (section 8.3). Retirements: relevance stage not run.

## Artifacts
- tests as a patch against the overlay layout: `packet/weasyprint/tests.patch`
- verdicts and logs: `execute/weasyprint/results.json`, `execute/weasyprint/{new,new-rerun,old}/`
- facts: `analyze/weasyprint/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/weasyprint/manifest.json`, every prompt and response under `generate/weasyprint/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/weasyprint/statement.json` (after stage attest)
