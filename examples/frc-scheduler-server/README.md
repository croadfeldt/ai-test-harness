# Example: frc-scheduler-server

**Target.** A FastAPI service I run for FRC event scheduling. Python 3.12, 15 pinned direct
dependencies, 62 packages resolved, about 30k lines of first-party code.

**What this example proves so far.** Stages 1 and 2 of the blueprint (intake, analysis, risk
scoring) on two triggers: a scheduled rescan of `main`, and a dependency-fix pull request. Every file
under `rescan/` and `pr-fix-known-vulns/` was written by `harness intake` and `harness analyze`. I did
not edit any of them. The `cache/` directories (downloaded wheels, OSV and PyPI responses) are
git-ignored; rerunning the commands recreates them.

## The two runs

| Run | Trigger | Command |
|---|---|---|
| `rescan/` | Scheduled rescan of `main` at `2ad04243` | `harness intake --repo frc-scheduler-server --head main --python-version 3.12 --workdir rescan` then `harness analyze --workdir rescan --python-version 3.12` |
| `pr-fix-known-vulns/` | Branch `deps/fix-known-vulns` (`cfa8f4a3`), which bumps python-jose, python-multipart, Pillow and weasyprint to versions with published fixes | `harness intake --repo frc-scheduler-server --base main --head deps/fix-known-vulns --python-version 3.12 --workdir pr-fix-known-vulns` then `harness analyze --workdir pr-fix-known-vulns --python-version 3.12` |

Intake resolved the full graph for the project's interpreter (from its Containerfile) with wheels
only, in about thirty seconds. Analysis took about ten seconds per run after downloads were cached.

## What the rescan found (`rescan/analyze/summary.json`)

Seven of 62 packages carry known vulnerabilities at `main`. Four are direct pins, three are
transitive and were not on anyone's list:

| Package | Depth | Reachable | Advisories | Risk | Budget |
|---|---|---|---|---|---|
| python-jose 3.3.0 | 1 | true, 8 references in `app/auth.py` including `jwt.decode` | 5 | 80 | full, CVE-targeted |
| starlette 0.41.3 | 2 (via fastapi) | true, imported directly by the app | 14 | 80 | full, CVE-targeted |
| weasyprint 63.1 | 1 | true | 6 | 80 | full, CVE-targeted |
| pillow 11.0.0 | 1 | unknown, no first-party import; reached through pdfplumber, pytesseract, weasyprint | 34 | 65 | full, CVE-targeted |
| python-multipart 0.0.12 | 1 | unknown, no first-party import; FastAPI declares it as an optional extra and the app has three upload endpoints | 16 | 65 | full, CVE-targeted |
| ecdsa 0.19.2 | 2 (via python-jose) | unknown | 2 | 65 | full, CVE-targeted |
| pdfminer-six 20231228 | 2 (via pdfplumber) | unknown | 4 | 65 | full, CVE-targeted |

The reachability column is the honest one: a first-party reference is proof, and absence of one is
only reported as `false` when nothing in the graph depends on the package. Everything else is
`unknown`, which the blueprint treats as reachable. Call-graph reachability arrives with a later slice.

## What the PR run found (`pr-fix-known-vulns/analyze/summary.json`)

The pull request changes four direct pins. Intake saw five changed rows, because bumping python-jose
to 3.4.0 made pip resolve **pyasn1 from 0.6.4 down to 0.4.8**. That version has eight advisories and
114 removed public symbols. A reviewer reading the PR diff would not see it. The harness did, scored
it 90, and gave it a full budget with CVE-targeted tests. See
`pr-fix-known-vulns/analyze/pyasn1/facts.json`.

| Package | Change | Advisories at head | API diff (added / removed / changed, breaking) | Notes |
|---|---|---|---|---|
| python-jose | 3.3.0 to 3.4.0 | 0 | 0 breaking | none of the 5 symbols the app uses changed |
| python-multipart | 0.0.12 to 0.0.31 | 0 | +76 / -69 / 0, 69 breaking | package renamed its import root; both roots present |
| pillow | 11.0.0 to 12.3.0 | 0 | +34 / -6 / 43, 10 breaking | |
| weasyprint | 63.1 to 70.0 | 0 | +172 / -75 / 68, 129 breaking | 60 files changed, +8641 / -5522 lines |
| pyasn1 | **0.6.4 down to 0.4.8** | **8** | +68 / -114 / 4, 118 breaking | transitive; pulled by python-jose and rsa |
| starlette | unchanged | 14 | | the PR did not touch fastapi, so starlette stays vulnerable |
| ecdsa, pdfminer-six | unchanged | 2, 4 | | same |

So the harness's verdict on this PR is: four exposures closed, one regression introduced, three
exposures left open. That is the review packet's one-page summary, once stage 6 exists.

## What each output file is

```
run.json                             harness and tool versions, the exact command
intake/graph.{old,new}.json          62 packages with depth, parents, hard and optional edges
intake/sbom.new.cdx.json             CycloneDX 1.5 SBOM of the head graph
intake/vulns.json                    every OSV entry, with aliases, fixed versions, references
intake/worklist.json                 63 rows (one first-party, 62 packages): change, depth, reachable, pre-flight
analyze/<package>/api.{old,new}.json public API surface from the wheel, tool-derived
analyze/<package>/api-diff.json      added / removed / changed with a breaking flag and reason
analyze/<package>/call-sites.json    every first-party reference, file and line, test files flagged
analyze/<package>/vulns.json         advisories for the head version
analyze/<package>/notes.untrusted.md maintainer text from PyPI, marked untrusted
analyze/<package>/facts.json         the bundle stage 3 consumes: everything above plus the risk score and budget
analyze/summary.json                 one row per analyzed package
```

## Limits of this slice, stated plainly

- **API diff counts every public symbol**, including modules an application never imports. The
  breaking counts above are upper bounds. The number that matters is breaking changes intersected
  with the app's call sites, which `facts.json` makes possible and stage 3 will use. For python-jose
  that intersection is zero.
- **Advisories rarely name symbols.** `symbols_named_by_advisories` is false for all seven packages,
  so the exposure test in stage 3 has to locate the vulnerable code path from the fix commit or the
  advisory text, which is untrusted input.
- **Pre-flight gates** ran the OpenSSF Malicious Packages check through OSV. GuardDog was not
  installed on the machine that produced these runs; the work list records that as `not_installed`
  rather than `clean`.
- **Static analysis** did not run; bandit was not installed. Recorded as `not_run`.
- **No sandbox and no model** were involved. Nothing from any package was executed. Stages 1 and 2
  only read metadata and source.
- **Sensitivity** is a keyword match over the package's own description. It is a prior, not a finding.

## Next for this example

Stage 3 generates tests for the seven vulnerable packages and the five changed ones, starting with
the exposure test for `jwt.decode` and the fix-pinning tests for each advisory. Stage 4 runs them in a
sandbox against both versions. The post-analysis then checks the run against the blueprint's core
goals: did it produce evidence a reviewer could act on, did it catch the pyasn1 regression before a
human would have, and is every claim traceable to a file in this directory.
