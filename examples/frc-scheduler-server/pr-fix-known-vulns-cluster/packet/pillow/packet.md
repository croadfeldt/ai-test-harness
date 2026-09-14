# Review packet: pillow 11.0.0 -> 12.3.0

**In plain terms.** This change updates pillow from 11.0.0 to 12.3.0, which closes 17 known vulnerabilities. The harness could not prove any of the 17 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `3d9fa72b859b`. Generated 2026-09-13T22:57:49+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
pillow at depth 1, change `bumped`, reachable from first-party code: **unknown**
(0 production references). Risk score 55, budget full.
API diff: +62 / -8 / ~45, 12 breaking.
Advisories: 0 open at head, 34 on the replaced version.

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
| CVE-2026-55379 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-55798 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-54060 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-54058 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-59199 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-54059 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-59205 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-25990 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-59198 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-59200 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-55380 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-42311 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-42310 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-59204 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-40192 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-42308 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-59197 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet (section 8.3). Retirements: relevance stage not run.

## Artifacts
- tests as a patch against the overlay layout: `packet/pillow/tests.patch`
- verdicts and logs: `execute/pillow/results.json`, `execute/pillow/{new,new-rerun,old}/`
- facts: `analyze/pillow/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/pillow/manifest.json`, every prompt and response under `generate/pillow/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/pillow/statement.json` (after stage attest)
