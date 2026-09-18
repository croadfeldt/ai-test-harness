# Review packet: github.com/getkin/kin-openapi v0.139.0 -> v0.139.0

**In plain terms.** This change leaves github.com/getkin/kin-openapi at v0.139.0, which has 4 known vulnerabilities the application is exposed to. The harness could not prove any of the 4 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

Run `8e6fa6151887`. Generated 2026-09-18T16:56:17+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
github.com/getkin/kin-openapi at depth 1, change `unchanged`, reachable from first-party code: **true** (30 production references). Risk score 70, budget full.
API diff: +0 / -0 / ~0, 0 breaking.
Advisories: 8 open at head, 0 on the replaced version.

## What was tested
4 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 0 pass on head, 0 flaky,
0 fix-pinning confirmed, 0 lines of the package covered. Model: `qwen3-235b`.
Mutation: not run.

## Findings
- **security** (0.9): github.com/getkin/kin-openapi v0.139.0 has 8 open advisories at head; reachable=true. Route: Product Security. Evidence: `analyze/github.com/getkin/kin-openapi/vulns.json`
- **defect** (0.4): github.com/getkin/kin-openapi: a code path raised the same internal error on both versions during CVE test generation (CVE-2026-76905); NOT corroborated by stage 4 verdicts. Route: escalate: below confidence threshold. Evidence: `generate/github.com/getkin/kin-openapi/manifest.agent.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| Test_GHSA_jpcw_4wr7_c3vq_fix_pinning | cve | error | error | test-bug | escalate |
| Test_GHSA_jpcw_4wr7_c3vq_exposure | cve | error | error | test-bug | escalate |
| Test_GHSA_xhj3_7xw9_vr34_fix_pinning | cve | error | error | test-bug | escalate |
| Test_GHSA_xhj3_7xw9_vr34_exposure | cve | error | error | test-bug | escalate |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| CVE-2026-73502 | affected | open at head; reachable=true; fixed in ['0.144.0'] |
| CVE-2026-76905 | affected | open at head; reachable=true; fixed in ['0.141.0'] |
| CVE-2026-73501 | affected | open at head; reachable=true; fixed in ['0.144.0'] |
| CVE-2026-77354 | affected | open at head; reachable=true; fixed in ['0.142.0'] |

## Upgrade path
The advisories are fixed in github.com/getkin/kin-openapi v0.144.0. The harness resolved an environment with it: go get raised the module to the fixed version; minimal version selection moved what it had to. Packages that move: github.com/getkin/kin-openapi v0.139.0 -> v0.144.0, github.com/go-openapi/jsonpointer v0.22.4 -> v0.22.5, github.com/go-openapi/swag/jsonname v0.25.4 -> v0.25.5, github.com/go-openapi/testify/v2 v2.0.2 -> v2.4.0, github.com/oasdiff/yaml v0.1.0 -> v0.1.1, github.com/oasdiff/yaml3 v0.0.13 -> v0.0.14.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet (section 8.3). Retirements: none proposed for the upgrade to v0.144.0; 4 generated and 0 application test(s) examined against 15 removed and 0 changed symbols.

## Artifacts
- tests as a patch against the overlay layout: `packet/github.com/getkin/kin-openapi/tests.patch`; the pull request they would travel in: `packet/github.com/getkin/kin-openapi/pull-request.md`
- verdicts and logs: `execute/github.com/getkin/kin-openapi/results.json`, `execute/github.com/getkin/kin-openapi/{new,new-rerun,old}/`
- facts: `analyze/github.com/getkin/kin-openapi/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/github.com/getkin/kin-openapi/manifest.json`, every prompt and response under `generate/github.com/getkin/kin-openapi/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/github.com/getkin/kin-openapi/statement.json` (after stage attest)
