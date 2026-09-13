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

## The A/B ladder on python-jose: runs 1 to 5

Same package, same model, same sandbox, same categories. Each run changes the generator only, and each
directory is kept as produced.

| | Run 1 baseline (`pr-fix-known-vulns/`) | Run 2 (`-run2/`) | Run 3 (`-run3/`) |
|---|---|---|---|
| Generator change | none | weak-assertion gate, dependency imports allowed, one advisory per call, streaming with loop abort | fix diff and version-only symbols in the CVE prompt, advisories grouped by CVE, collection required on both versions, crash-on-fixed repair |
| Model calls, finished cleanly | 4 of 4, 13 min each | 8 of 8, 1 to 2 min each | 12 of 12, 0.5 to 2 min each |
| Generate through execute, wall time | 22 min | 15 min | 20 min |
| Tests kept, flaky | 16, 0 | 17, 0 | 14, 0 |
| Unit candidates, package lines covered | 6, 542 | 7, 590 | 8, 560 |
| CVE files that collect on both versions | 10 of 10 | 10 of 10 | 6 of 6 (a first pass had 0 of 6: imports of names new in 3.4.0) |
| CVE fix-pinning confirmed | 0 of 10 | 0 of 10 | 0 of 6 |

Run 4 (`-run4/`) changed one variable against run 3: the CVE tests came from the tool-using stage 3
(`--mode agent`), with search, read, list-API, and a sandbox run against both versions as tools, and a
budget of 14 calls per issue. Every issue used its whole budget and submitted. 13 tests, 7 unit
candidates, 0 flaky, 0 of 6 confirmed. What the traces showed, now register entries GF-013 to GF-015:

- On the algorithm-confusion issue the agent spent 12 calls reading source and ran its test once, on
  the last call. That single run showed the fixed version raising the exact error the fix introduced.
  The trigger was right; the test expected a different exception class and never made the old version
  accept the input. One turn short of proof, with no budget left.
- On both compression-bomb issues the agent ran its test eleven times and got the same internal error
  on both versions every time, the JWE encryption defect against cryptography 50.0.1 noted above. The
  repetition was the signal, and nothing acted on it.

Run 5 (`-run5/`) holds everything from run 4 and adds the three corrections: reads are capped until a
test has run and calls are reserved for a run and a submit; a fixed-version failure carrying text the
fix diff added is reported to the agent as "fix reached, expect this exception on new"; an identical
run result is reported as a blocked path and recorded as a candidate defect for triage. Stage 0 ran
first, all fifteen register checks passing.

**Run 5 result: 2 of 6 CVE tests confirmed as fix-pinning.** 11 tests, 5 unit candidates, 0 flaky,
640 package lines covered.

| Issue | Agent | Differential verdict |
|---|---|---|
| CVE-2024-33664, JWE compression bomb | 4 turns, 3 tool calls: two reads, one run, submit | **Confirmed.** Both tests fail on 3.3.0 ("DID NOT RAISE JWEError") and pass on 3.4.0. |
| CVE-2024-33663, algorithm confusion | 13 tool calls; the read cap fired once and forced a test run | Passes on both versions: the input does not reach the vulnerable behavior. Not confirmed. |
| CVE-2024-29370, JWE bomb, second advisory | 13 tool calls, ten runs | Blocked on both versions: the agent went through `jwe.encrypt`, which raises an internal error against cryptography 50.0.1 on both versions. Recorded as a candidate defect for triage. |

The confirmed test is worth reading (`run5/generate/python-jose/tests/test_python_jose_cve_cve_2024_33664.py`).
The library's own encrypt path is broken in this dependency set, so the agent assembled the compact JWE
by hand: a `dir`/`A256GCM`/`zip=DEF` header, 300 KB compressed with zlib, encrypted with the
cryptography library's AES-GCM, base64url-joined. On 3.3.0 `jwe.decrypt` inflates it and returns; on
3.4.0 the new `JWE_SIZE_LIMIT` check raises. That is the fix, proven, in a test that runs with plain
`pytest` and imports only the package and its declared dependency.

Two observations for the register. The second bomb advisory is the same fix as the first, and a
confirmed test for one should count as evidence for the other; that pairing belongs to triage. And the
agent that solved it used three tool calls, while the one that did not used thirteen: the budget rules
from GF-013 kept the failures cheap, they did not make the model smarter.

What run 3 shows in the failure messages on the fixed version:

- **The algorithm-confusion trigger is now right and the assertion is wrong.** The fix-pinning test
  fails on 3.4.0 with the library's own new error, "the specified key is an asymmetric key ... and
  should not be used as an HMAC secret". The check the fix added fired. The test expected a different
  exception class, and two repair rounds did not converge.
- **The compression-bomb tests cannot be built through the library on this graph.** `jwe.encrypt`
  raises an internal error (`module 'lib' has no attribute 'RAND_bytes'`) on both 3.3.0 and 3.4.0
  against cryptography 50.0.1, the version the application resolves. That is a defect finding for the
  review packet, low severity because the application never calls JWE, and it means a bomb token has
  to be assembled with the cryptography library directly, which this model did not manage.
- The third pair is a plain test bug (decoding bytes as UTF-8).

Conclusion for the fixed-script generator with a 27B model: it produces good characterization tests
for the symbols the application uses, first time, every run. It does not produce a confirmed
fix-pinning test in three tries, and the harness says so instead of shipping green tests. Run 4 added
tools; run 5 added the corrections run 4 exposed, and produced the first confirmed fix-pinning tests.

## Stages 5, 6, attestation, and post-analysis on run 5 (`-run5/triage`, `packet`, `attest`, `assess`)

The back half of the pipeline ran on run 5's outputs. No model was involved in any of it.

- **Triage** (`triage/python-jose/triage.json`): 7 tests to accept (5 unit, 2 confirmed CVE), 4 to
  discard or regenerate, 2 findings. One finding is the JWE encryption defect, routed at 0.8 because
  stage 4 corroborates it with tests blocked on both versions. The other is the agent's blocked-path
  note on the key-confusion issue, which stage 4 does not corroborate (those tests pass on both
  versions), so triage escalates it at 0.4 instead of routing it. A deterministic signal has to back
  an agent's claim before it becomes a finding.
- **Packet** (`packet/python-jose/packet.md`): one page, the seven accepted tests as a patch against
  `overlays/python/python-jose/3.4.x/`, and a draft OpenVEX document with one statement per
  vulnerability: CVE-2024-33664 `fixed`, backed by the two confirmed tests; CVE-2024-33663 and
  CVE-2024-29370 `under_investigation`. Every statement is a draft for Product Security. The packet
  recommends: advisory, accept the candidates, route the findings, confirm the VEX drafts.
- **Attestation** (`attest/python-jose/`): a provenance record per accepted test in the shape of
  `blueprint/manifest.schema.yaml`, an in-toto Statement whose subjects are the patch and the record
  digests and whose predicate is the vetted `test-result/v0.1` type carrying the harness record, and a
  DSSE envelope. Signed with a local Ed25519 development key and verified; the statement's
  `unverified` list says so, along with the missing mutation score, the missing coverage baseline,
  and the fact that the harness ran from a checkout rather than a built image.
- **Post-analysis** (`assess/assess.md`): eleven goals from the blueprint, each measured from the
  run's files. Nine met, one measured without a target yet (time to packet, since the trigger was
  manual), one not applicable (mutation score). Verdicts cite the file they came from.

## pyasn1: the downgrade, proven (`-run5/{analyze,generate,execute,triage,packet,attest}/pyasn1`)

The PR's python-jose bump made pip resolve pyasn1 from 0.6.4 down to 0.4.8, a version with eight
advisories. The full pipeline ran on it with the same model and the tool-using stage 3. Because this is
a downgrade, the roles flip: the new version is the vulnerable one (register entry GF-016).

| Issue | Agent | Differential | VEX draft |
|---|---|---|---|
| CVE-2026-30922, unbounded recursion | 7 calls: a 5000-deep nested SEQUENCE fed to the BER decoder | **Exposure confirmed**: passes on 0.6.4, fails on 0.4.8 | `affected` |
| CVE-2026-59884, long-form tag ids | 13 calls, 7 runs | passes on both | `under_investigation` |
| CVE-2026-59885, quadratic OID decode | 13 calls, 7 runs | blocked: `ValueError` on both | `under_investigation` |
| CVE-2026-59886, REAL conversion | 13 calls, 7 runs | passes on both | `under_investigation` |

So the harness's verdict on this pull request, end to end: it closes one python-jose exposure with
proof, leaves two python-jose advisories unproven, and **introduces a proven denial-of-service
exposure through a package the PR never mentions**. The packet for pyasn1 says `affected`, backed by
two tests a reviewer can run with plain pytest, and the attestation carries the record.

The eight pyasn1 unit tests are weak: the application has no call sites into pyasn1, so the model fell
back to asserting that classes are subclasses and functions are callable. They pass every gate and
prove nothing. That is register entry GF-017.

## starlette: vulnerable at head, unchanged by the PR, proven against a fixed candidate

starlette 0.41.3 arrives through fastapi, the app imports it directly, and it carries seven open
advisories the PR does not touch. There is no old-versus-new to compare, so the harness resolved a
**fixed-candidate environment**: pinning starlette to 1.3.1 alone is unsatisfiable because fastapi
0.115.5 pins it, so the harness let fastapi move and resolved fastapi 0.141.1 with starlette 1.3.1.
That is the upgrade path, and it is a section of the packet.

| Issue | Agent | Differential (head 0.41.3 vs candidate 1.3.1) | VEX draft |
|---|---|---|---|
| CVE-2026-48817, non-standard HTTP method reaches an endpoint | 13 calls, 7 runs | **Exposure confirmed**: fails at head, passes on the candidate | `affected`, with evidence |
| CVE-2025-54121, multipart size; CVE-2026-54282, path re-parsed as authority | 13 calls each | fail on both: test bug | `affected` (reachable, no test evidence) |
| CVE-2025-62727, Range merging; CVE-2026-54283, form field limit; CVE-2026-48710, Host header | 12 to 13 calls each | pass on both: no trigger | `affected` (reachable, no test evidence) |
| CVE-2026-48818, UNC path in StaticFiles | 13 calls | blocked: `RuntimeError` on both | `affected` (reachable, no test evidence) |

18 tests, 6 accepted (4 unit, 2 confirmed CVE), 0 flaky, 848 package lines covered. The confirmed pair
was first mis-judged: pytest parametrized it, stage 4 matched ids exactly, and the proof was filed as
an uncategorized test. That is register entry GF-018; the rerun above is after the fix.

## Mutation testing on python-jose's accepted tests (`-run5/execute/python-jose/mutation/`)

12 mutants sampled from 157 sites on the 640 package lines the tests execute. 5 killed, 7 survived:
**score 0.42 against the blueprint's target of 0.6.** The confirmed fix-pinning test killed a mutant
in the base64 helper; the round-trip test killed five and was the only test with a unique kill. The
survivors sit in the cryptography backend and the JWE path, which the accepted tests barely touch.
Post-analysis goal G11 now reads "not met" instead of "not applicable", which is the honest state.

## The pull request, end to end

Three packages through every stage, one model, one sandbox, stage 0 passing first.

| Package | What the PR did to it | Proven | Left unproven | VEX |
|---|---|---|---|---|
| python-jose | bumped 3.3.0 to 3.4.0 | 1 exposure closed (JWE bomb) | 2 | 1 fixed, 2 under investigation |
| pyasn1 | downgraded 0.6.4 to 0.4.8, unmentioned | 1 exposure introduced (unbounded recursion) | 3 | 1 affected with evidence, 3 under investigation |
| starlette | untouched, 7 open advisories | 1 exposure at head (method handling) | 6 | 7 affected, 1 with evidence; upgrade path: fastapi 0.141.1 |

Post-analysis: 9 of 11 goals met, one measured without a target, and the mutation-score goal not met. Three signed attestations, verified. Everything a reviewer needs is in `run5/packet/`.

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

Mutation testing for the strength gate, the relevance engine for retirements, a stronger model as the
next ladder variable, and the Tekton wrapping so stage 0 through attestation run as one PipelineRun.
