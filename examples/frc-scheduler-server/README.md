# Example: frc-scheduler-server

**Target.** A FastAPI service I run for FRC event scheduling. Python 3.12, 15 pinned direct
dependencies, 63 packages resolved, about 30k lines of first-party code.

**What this example proves so far.** Stages 1 and 2 of the blueprint (intake, analysis, risk
scoring) on two triggers: a scheduled rescan of `main`, and a dependency-fix pull request. Every file
under `rescan/` and `pr-fix-known-vulns/` was written by `harness intake` and `harness analyze`. I did
not edit any of them. The `cache/` directories (downloaded wheels, OSV and PyPI responses) and the raw
`api.old.json` / `api.new.json` surfaces (about 100k lines of public symbols) are git-ignored;
rerunning the commands recreates them. `api-diff.json` and `facts.json` carry what a reviewer needs.

## The two runs

| Run | Trigger | Command |
|---|---|---|
| `rescan/` | Scheduled rescan of `main` at `2ad04243` | `harness intake --repo frc-scheduler-server --head main --python-version 3.12 --workdir rescan` then `harness analyze --workdir rescan --python-version 3.12` |
| `pr-fix-known-vulns/` | Branch `deps/fix-known-vulns` (`cfa8f4a3`), which bumps python-jose, python-multipart, Pillow and weasyprint to versions with published fixes | `harness intake --repo frc-scheduler-server --base main --head deps/fix-known-vulns --python-version 3.12 --workdir pr-fix-known-vulns` then `harness analyze --workdir pr-fix-known-vulns --python-version 3.12` |

Intake resolved the full graph inside the project's own interpreter image (Python 3.12, from its
Containerfile), wheels only, in under a minute. Resolving on the host had silently dropped greenlet,
because pip evaluates environment markers for the interpreter it runs under; the sandbox install then
failed, which is how the gap was found. Analysis took about ten seconds per run after downloads were cached.

## What the rescan found (`rescan/analyze/summary.json`)

Seven of 63 packages carry known vulnerabilities at `main`. Four are direct pins, three are
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

## Stages 3 and 4 on python-jose: the fixed-script baseline (`pr-fix-known-vulns/generate`, `execute`)

Model: `qwen/qwen3.8-27b` at 8-bit on a Mac through LM Studio, reasoning off (`reasoning_effort: none`,
recorded in every call). Categories requested: CVE and unit. Every prompt and response is under
`generate/python-jose/model-calls/`.

| Step | Result |
|---|---|
| CVE generation, one call, 9 min, 3976 tokens | 10 tests: a fix-pinning and an exposure test for each of the 5 advisories on 3.3.0. The model read the advisories correctly: two algorithm-confusion (OpenSSH ECDSA key accepted as an HMAC secret), three JWE compression bomb. |
| Unit generation, three calls, 4 tests cut | 6 tests kept covering the five symbols `app/auth.py` uses: encode/decode round trip, wrong key, invalid token, expiry, unverified header. 542 lines of the package covered. |
| Execute: head, head re-run, base | 16 tests, 12 pass on head, 0 flaky. Sandbox runs of 22 to 24 seconds each. |
| Differential verdict | **0 of 10 CVE tests confirmed as fix-pinning.** 6 pass on both 3.3.0 and 3.4.0, 4 fail on both. |

Why the CVE tests failed to prove anything, from the test source:

- The six that pass on both versions assert `pytest.raises((JOSEError, Exception))`. Any error
  satisfies that, and the crafted JWE was malformed enough to raise on both versions. A catch-all
  assertion cannot distinguish vulnerable from fixed.
- The four that fail on both invented EC key coordinates (`"x": "M1111..."`) because the generator's
  import allowlist blocked `cryptography`, which python-jose itself depends on, so the model had no way
  to make real key material. The library rejected the key before reaching the vulnerable path.

Both are harness gaps, not findings against the package, and both are now gates in the generator: a
test with a catch-all `raises` or no assertion is sent back as weak, and tests may import the
package's declared dependencies. This run is kept unchanged as the baseline that the next run, and the
tool-using agentic variant of stage 3, have to beat on the same numbers: fix-pinning confirmed,
target lines covered, tests cut, tokens and minutes spent.

What the run did prove: the compile, baseline, and differential gates work as specified. A reviewer
would have seen six characterization tests worth keeping and a clear statement that no advisory was
proven fixed, rather than ten green-looking CVE tests.

Two more harness corrections came out of this run: the old-version environment for the differential is
the base commit's own resolved graph (swapping one package inside the head graph produced a set pip
could not satisfy), and the model client sends `reasoning_effort: none`, because the first attempt
spent 6000 tokens per call on hidden reasoning and returned empty content.

## What each output file is

```
run.json                             harness and tool versions, the exact command
intake/graph.{old,new}.json          63 packages with depth, parents, hard and optional edges
intake/sbom.new.cdx.json             CycloneDX 1.5 SBOM of the head graph
intake/vulns.json                    every OSV entry, with aliases, fixed versions, references
intake/worklist.json                 64 rows (one first-party, 63 packages): change, depth, reachable, pre-flight
analyze/<package>/api.{old,new}.json public API surface from the wheel, tool-derived
analyze/<package>/api-diff.json      added / removed / changed with a breaking flag and reason
analyze/<package>/call-sites.json    every first-party reference, file and line, test files flagged
analyze/<package>/vulns.json         advisories for the head version
analyze/<package>/notes.untrusted.md maintainer text from PyPI, marked untrusted
analyze/<package>/facts.json         the bundle stage 3 consumes: everything above plus the risk score and budget
analyze/summary.json                 one row per analyzed package
generate/<package>/tests/            candidate pytest files, header says generated and unreviewed
generate/<package>/manifest.json     per file: tests kept and cut, attempts, model, prompt/response digests, baseline coverage
generate/<package>/model-calls/      every prompt and response verbatim, with usage, latency, reasoning setting
execute/<package>/results.json       TestResults: per test old/new status and verdict; coverage summary; sandbox isolation record
execute/<package>/{new,new-rerun,old}/  junit.xml, coverage.json, logs, sandbox.json per run
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

Rerun stage 3 on python-jose with the two new gates and compare against the baseline above. Then the
tool-using variant of stage 3, where the model can read the fix diff between 3.3.0 and 3.4.0 instead
of guessing a trigger from an advisory summary. Then pyasn1 and starlette. Stages 5 through 7, the
attestation, and the post-analysis against the blueprint's core goals follow.
