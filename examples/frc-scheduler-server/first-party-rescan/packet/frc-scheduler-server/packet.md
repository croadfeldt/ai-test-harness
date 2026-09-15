# Review packet: frc-scheduler-server at 2ad04243861b

**In plain terms.** This is the application's own code, frc-scheduler-server, at commit 2ad04243861b. No known vulnerability applies to it, so there is nothing to prove; the tests below characterize what the code does today. Accept the 4 candidate tests if they look right, act on the findings below.

Run `50ec3b2446fe`. Generated 2026-09-15T20:29:42+00:00. This packet proposes; a reviewer decides. Nothing here has been merged.

## What changed
frc-scheduler-server is the application itself (depth 0), scanned at commit 2ad04243861b. Risk score 35, budget full.
API diff: +0 / -0 / ~0, 0 breaking.
Advisories: 0 open at head, 0 on the replaced version.

## What was tested
4 generated tests ran in the sealed sandbox on head, again for flakes, and on the base version. 4 pass on head, 0 flaky,
0 fix-pinning confirmed, 350 lines of the package covered. Model: `qwen38-27b`.
Mutation: score 0.04 (1 of 25 sampled mutants killed, 211 sites on executed lines, seed 724864561). Tests that killed nothing: ['test_canonical_filename_encodes_shape', 'test_canonical_path_uses_base_dir', 'test_load_canonical_missing_returns_none', 'test_parse_csv_reads_rows']. Target in the blueprint: 0.6.

## Findings
- **redundant** (0.5): frc-scheduler-server: test_canonical_filename_encodes_shape killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold. Evidence: `execute/frc-scheduler-server/relevance.json`
- **redundant** (0.5): frc-scheduler-server: test_canonical_path_uses_base_dir killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold. Evidence: `execute/frc-scheduler-server/relevance.json`
- **redundant** (0.5): frc-scheduler-server: test_load_canonical_missing_returns_none killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold. Evidence: `execute/frc-scheduler-server/relevance.json`
- **redundant** (0.5): frc-scheduler-server: test_parse_csv_reads_rows killed none of 25 sampled mutants in this run. Route: escalate: below confidence threshold. Evidence: `execute/frc-scheduler-server/relevance.json`

## Tests
| test | category | old | new | class | action |
|---|---|---|---|---|---|
| test_canonical_filename_encodes_shape | unit | na | pass | behavior-change | accept as candidate |
| test_canonical_path_uses_base_dir | unit | na | pass | behavior-change | accept as candidate |
| test_load_canonical_missing_returns_none | unit | na | pass | behavior-change | accept as candidate |
| test_parse_csv_reads_rows | unit | na | pass | behavior-change | accept as candidate |

## Draft VEX statements (for Product Security)
| vulnerability | status | basis |
|---|---|---|
| none | | |

## Upgrade path
Not applicable: the change brought the fixed version, or no advisory is open at head.

## Recommended action
**Advisory.** Accept the listed candidate tests into the overlay; act on the findings by routing; confirm the VEX drafts with Product Security.

## Promotions and retirements
Promotions: none yet; promotion needs a survived version change or a caught regression (section 8.3).

Retirement proposals, for this change. Advisory: a person approves, a retired test is kept and re-run once on the next change, nothing is deleted.

| test | file | class | reason | rewrite | priority | evidence |
|---|---|---|---|---|---|---|
| test_canonical_filename_encodes_shape | test_frc_scheduler_server_unit.py | redundant | redundant-no-kills |  | low | test_canonical_filename_encodes_shape killed none of 25 sampled mutants in this run |
| test_canonical_path_uses_base_dir | test_frc_scheduler_server_unit.py | redundant | redundant-no-kills |  | low | test_canonical_path_uses_base_dir killed none of 25 sampled mutants in this run |
| test_load_canonical_missing_returns_none | test_frc_scheduler_server_unit.py | redundant | redundant-no-kills |  | low | test_load_canonical_missing_returns_none killed none of 25 sampled mutants in this run |
| test_parse_csv_reads_rows | test_frc_scheduler_server_unit.py | redundant | redundant-no-kills |  | low | test_parse_csv_reads_rows killed none of 25 sampled mutants in this run |

## Artifacts
- tests as a patch against the overlay layout: `packet/frc-scheduler-server/tests.patch`
- verdicts and logs: `execute/frc-scheduler-server/results.json`, `execute/frc-scheduler-server/{new,new-rerun,old}/`
- facts: `analyze/frc-scheduler-server/facts.json`, API diff, call sites, advisories, fix diff
- generation provenance: `generate/frc-scheduler-server/manifest.json`, every prompt and response under `generate/frc-scheduler-server/model-calls/`
- stage 0 record: `selfcheck/selfcheck.json`
- attestation: `attest/frc-scheduler-server/statement.json` (after stage attest)
