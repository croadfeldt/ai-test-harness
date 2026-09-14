# Review packet: python-multipart 0.0.12 -> 0.0.31

**In plain terms.** This change updates python-multipart from 0.0.12 to 0.0.31, which closes 8 known vulnerabilities. The harness could not prove any of the 8 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `3d9fa72b859b`. Generated 2026-09-13T22:57:49+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
python-multipart at depth 1, change `bumped`, reachable from first-party code: **unknown**
(0 production references). Risk score 55, budget full.
API diff: +92 / -82 / ~0, 82 breaking.
Advisories: 0 open at head, 16 on the replaced version.

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
| CVE-2024-53981 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-53539 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-53538 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-40347 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-42561 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-53540 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-53537 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |
| CVE-2026-24486 | under_investigation | bump to a fixed version per advisory metadata; no confirmed fix-pinning test yet |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet (section 8.3). Retirements: relevance stage not run.

## Artifacts
- tests as a patch against the overlay layout: `packet/python-multipart/tests.patch`
- verdicts and logs: `execute/python-multipart/results.json`, `execute/python-multipart/{new,new-rerun,old}/`
- facts: `analyze/python-multipart/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/python-multipart/manifest.json`, every prompt and response under `generate/python-multipart/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/python-multipart/statement.json` (after stage attest)
