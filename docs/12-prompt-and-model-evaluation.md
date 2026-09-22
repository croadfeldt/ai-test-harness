# Prompt and model evaluation

**For:** anyone deciding which model or prompt set to run, and anyone asking whether the harness's results can be trusted. Generated from the example runs by `tools/prompt-eval.py`; the same table for any set of runs comes from `harness evaluate`.

Fitness for purpose is measured, never assumed. Each line is one prompt set with one model on one package, summed over the runs that
used them. Ground truth in order of strength: a reviewer's decision on the test pull request, the sandbox's verdicts (a fix proven means
the test fails on the vulnerable version and passes on the fixed one), triage's acceptance. Cost is model calls and minutes of model time.

Generated 2026-09-22T21:18:36+00:00 from 16 package run(s).

| Prompt set | Model | Language | Package | Runs | Generated | Kept | Accepted | Proven | Mutation | Reviewer accepted / rejected | Calls | Minutes | Reads as |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 (unrecorded) | qwen3-235b | go | github.com/getkin/kin-openapi | 2 | 12 | 8 | 0 | 0 | - | no review yet | 552 | 319.1 | not fit: tests ran, none accepted |
| v1 (unrecorded) | qwen38-27b | go | github.com/getkin/kin-openapi | 2 | 5 | 5 | 0 | 0 | 0.0 | no review yet | 423 | 69.1 | not fit: tests ran, none accepted |
| v1 (unrecorded) | qwen38-27b | python | frc-scheduler-server | 1 | 4 | 4 | 4 | 0 | 0.04 | no review yet | 6 | 2.5 | characterizes: 4 tests accepted by triage, nothing proven |
| v1 (unrecorded) | qwen/qwen3.8-27b | python | pyasn1 | 1 | 16 | 16 | 10 | 2 | 0.42 | no review yet | 135 | 42.5 | proves fixes: 2 fix-pinning confirmed |
| v1 (unrecorded) | qwen/qwen3.8-27b | python | python-jose | 8 | 115 | 106 | 25 | 4 | 0.43 | no review yet | 642 | 247.9 | proves fixes: 4 fix-pinning confirmed |
| v1 (unrecorded) | qwen38-27b | python | python-jose | 1 | 10 | 10 | 7 | 3 | 0.25 | 7 / 0 | 102 | 7.8 | accepted by a reviewer: 7 tests |
| v1 (unrecorded) | qwen/qwen3.8-27b | python | starlette | 1 | 18 | 18 | 6 | 2 | 0.0 | no review yet | 249 | 68.9 | proves fixes: 2 fix-pinning confirmed |

## The runs behind each line

| Run | Prompt set (digest) | Model | Package | Generated | Kept | Accepted | Proven |
|---|---|---|---|---|---|---|---|
| kin-openapi-235b | v1 (unrecorded) (none) | qwen3-235b | github.com/getkin/kin-openapi | 8 | 4 | 0 | 0 |
| kin-openapi-235b-run2 | v1 (unrecorded) (none) | qwen3-235b | github.com/getkin/kin-openapi | 4 | 4 | 0 | 0 |
| kin-openapi-cluster | v1 (unrecorded) (none) | qwen38-27b | github.com/getkin/kin-openapi | 4 | 4 | 0 | 0 |
| kin-openapi-run1 | v1 (unrecorded) (none) | qwen38-27b | github.com/getkin/kin-openapi | 1 | 1 | 0 | 0 |
| first-party-rescan | v1 (unrecorded) (none) | qwen38-27b | frc-scheduler-server | 4 | 4 | 4 | 0 |
| pr-fix-known-vulns-run5 | v1 (unrecorded) (none) | qwen/qwen3.8-27b | pyasn1 | 16 | 16 | 10 | 2 |
| pr-fix-known-vulns | v1 (unrecorded) (none) | qwen/qwen3.8-27b | python-jose | 16 | 16 | 0 | 0 |
| pr-fix-known-vulns-cluster | v1 (unrecorded) (none) | qwen/qwen3.8-27b | python-jose | 14 | 14 | 10 | 2 |
| pr-fix-known-vulns-cluster-run2 | v1 (unrecorded) (none) | qwen/qwen3.8-27b | python-jose | 16 | 7 | 0 | 0 |
| pr-fix-known-vulns-cluster-run3 | v1 (unrecorded) (none) | qwen/qwen3.8-27b | python-jose | 14 | 14 | 8 | 0 |
| pr-fix-known-vulns-run2 | v1 (unrecorded) (none) | qwen/qwen3.8-27b | python-jose | 17 | 17 | 0 | 0 |
| pr-fix-known-vulns-run3 | v1 (unrecorded) (none) | qwen/qwen3.8-27b | python-jose | 14 | 14 | 0 | 0 |
| pr-fix-known-vulns-run4 | v1 (unrecorded) (none) | qwen/qwen3.8-27b | python-jose | 13 | 13 | 0 | 0 |
| pr-fix-known-vulns-run5 | v1 (unrecorded) (none) | qwen/qwen3.8-27b | python-jose | 11 | 11 | 7 | 2 |
| pr-fix-known-vulns-run6 | v1 (unrecorded) (none) | qwen38-27b | python-jose | 10 | 10 | 7 | 3 |
| pr-fix-known-vulns-run5 | v1 (unrecorded) (none) | qwen/qwen3.8-27b | starlette | 18 | 18 | 6 | 2 |

A prompt set or a model that does not reach the outcome a package needs (a proven fix for an advisory, an accepted characterization
otherwise) is not fit for that purpose, whatever it scores elsewhere. The harness records the set's name and digest in every manifest,
so any line here can be traced to the exact words and the exact model that produced it.
