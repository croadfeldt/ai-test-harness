# Post-analysis of run 5f493a6b7288

**In plain terms.** This run met 9 of 11 goals from the blueprint. Not met: Test strength measured by mutation and coverage delta. Every verdict below points at the file it was measured from.

Packages: python-jose.

| id | goal | measurement | verdict |
|---|---|---|---|
| G1 | Nothing merges without a person | harness produced patches and drafts only; no git push, no VEX published | **met** |
| G2 | Every kept test was compiled and run in the sandbox before a reviewer sees it | 7 tests ran on head, again for flakes, and on base; 0 flaky | **met** |
| G3 | A test that passes on both versions is not presented as CVE evidence | 0 fix-pinning confirmed; pass-on-both CVE tests are classified test-bug and excluded from VEX 'fixed' | **met** |
| G4 | Stage 0 passed before evidence was produced | 19 of 19 register checks; sandbox probe skipped; model probe skipped | **met** |
| G5 | Generated tests ran with no network, no secrets, read-only root, disposable container | {'disposable': 'the task pod', 'limits': {'cpus': '2', 'memory': '2g', 'pids': 512, 'timeout_s': 900}, 'network': 'deny-all NetworkPolicy on the task pod (claim | **met** |
| G6 | Every accepted test carries a provenance record and a signed attestation | 0 records; envelopes verified locally: [True]; signer is a development key | **met (development signer)** |
| G7 | Every advisory on the work item has a CVE-targeted test attempt and a draft VEX statement | python-jose: {'CVE-2024-29370': 'under_investigation', 'CVE-2024-33663': 'under_investigation', 'CVE-2024-33664': 'under_investigation'} | **met** |
| G8 | The run surfaces a finding the PR diff does not show | python-jose: ['python-jose: a code path raised the same internal error on both versions during '] | **met** |
| G9 | Packet within 2 hours of trigger for depth 0 and 1 | intake 2026-09-13T23:06:40+00:00 -> packet 2026-09-14T00:08:59+00:00 | **see measurement** |
| G10 | Every number in the packet points at a file in the work directory | packet sections cite artifact paths; attestation subjects are the patch and the manifest digests | **met** |
| G11 | Test strength measured by mutation and coverage delta | python-jose: score 0.48 on 25 sampled mutants; coverage delta: no baseline overlay suite yet | **not met (target 0.6 on sampled mutants)** |
