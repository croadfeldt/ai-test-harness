# The evidence so far

**For:** anyone deciding whether this is worth their time. Every number below is read from a run's records
under `examples/` by `tools/rollup.py`; nothing here is typed by hand, and a run that lacks a stage shows a dash.

**In plain terms.** 14 runs with executed tests, 16 package rows, 167 generated tests run in a
sealed sandbox, 11 tests proving a vulnerability closed or open by failing on the vulnerable version and
passing on the fixed one, 52 tests accepted by triage as candidates, 12 signed attestations. "Proven"
counts tests, so one vulnerability may carry two. Mutation is the share of sampled mutants the accepted tests killed,
target 0.6. "Accepted by review" is what a person kept after the harness proposed, from stage 7. Time from
trigger to packet is on each run's own assessment (goal G9), because several of these runs were re-attested
days later and the records would say so.

| Run | Package | Lang | Target | Model | Tests | Pass on head | Proven | Accepted | Mutation | UDLM records | Signed | Goals | Proposed | Accepted by review |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [control-plane/kin-openapi-235b](https://croadfeldt.github.io/ai-test-harness/runs/control-plane/kin-openapi-235b/) | github.com/getkin/kin-openapi | go | pod | qwen3-235b | 4 | 0 | 0 | 0 | n/a | 11 | yes | 9 met | - | - |
| [control-plane/kin-openapi-235b-run2](https://croadfeldt.github.io/ai-test-harness/runs/control-plane/kin-openapi-235b-run2/) | github.com/getkin/kin-openapi | go | pod | qwen3-235b | 4 | 0 | 0 | 0 | n/a | 11 | yes | 9 met | - | - |
| [control-plane/kin-openapi-cluster](https://croadfeldt.github.io/ai-test-harness/runs/control-plane/kin-openapi-cluster/) | github.com/getkin/kin-openapi | go | pod | qwen38-27b | 4 | 2 | 0 | 0 | 0.00 (0/25) | 11 | yes | 9 met | - | - |
| [control-plane/kin-openapi-run1](https://croadfeldt.github.io/ai-test-harness/runs/control-plane/kin-openapi-run1/) | github.com/getkin/kin-openapi | go | podman | qwen38-27b | 1 | 0 | 0 | 0 | n/a | 11 | yes | 9 met | - | - |
| [frc-scheduler-server/first-party-rescan](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/first-party-rescan/) | frc-scheduler-server | python | podman | qwen38-27b | 4 | 4 | 0 | 4 | 0.04 (1/25) | 7 | yes | 8 met | - | - |
| [frc-scheduler-server/pr-fix-known-vulns](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns/) | python-jose | python | podman | qwen/qwen3.8-27b | 16 | 12 | 0 | - | - | - | - | - | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-cluster](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-cluster/) | python-jose | python | podman | qwen/qwen3.8-27b | 14 | 14 | 2 | 10 | 0.40 (10/25) | 19 | yes | 9 met | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-cluster-run2](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-cluster-run2/) | python-jose | python | podman | qwen/qwen3.8-27b | 7 | 6 | 0 | 0 | 0.48 (12/25) | 9 | yes | 9 met | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-cluster-run3](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-cluster-run3/) | python-jose | python | podman | qwen/qwen3.8-27b | 14 | 14 | 0 | 8 | 0.44 (11/25) | 17 | yes | 9 met | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-run2](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-run2/) | python-jose | python | podman | qwen/qwen3.8-27b | 17 | 11 | 0 | - | - | - | - | - | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-run3](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-run3/) | python-jose | python | podman | qwen/qwen3.8-27b | 14 | 8 | 0 | - | - | - | - | - | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-run4](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-run4/) | python-jose | python | podman | qwen/qwen3.8-27b | 13 | 7 | 0 | - | - | - | - | - | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-run5](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-run5/) | pyasn1 | python | podman | qwen/qwen3.8-27b | 16 | 12 | 2 | 10 | 0.42 (5/12) | 21 | yes | 9 met | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-run5](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-run5/) | python-jose | python | podman | qwen/qwen3.8-27b | 11 | 9 | 2 | 7 | 0.42 (5/12) | 16 | yes | 9 met | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-run5](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-run5/) | starlette | python | podman | qwen/qwen3.8-27b | 18 | 10 | 2 | 6 | 0.00 (0/12) | 23 | yes | 9 met | - | - |
| [frc-scheduler-server/pr-fix-known-vulns-run6](https://croadfeldt.github.io/ai-test-harness/runs/frc-scheduler-server/pr-fix-known-vulns-run6/) | python-jose | python | podman | qwen38-27b | 10 | 9 | 3 | 7 | 0.25 (3/12) | 16 | yes | 9 met | PR | 7/7 |

How to read any one of these runs, file by file, is in [10-reading-the-artifacts.md](10-reading-the-artifacts.md).
The story behind each run is on its example page: [frc-scheduler-server](../examples/frc-scheduler-server/README.md)
(Python) and [control-plane](../examples/control-plane/README.md) (Go).
