# Post-analysis of run 76a3fa863e76

Packages: python-jose. 9 of 11 goals met.

| id | goal | measurement | verdict |
|---|---|---|---|
| G1 | Nothing merges without a person | harness produced patches and drafts only; no git push, no VEX published | **met** |
| G2 | Every kept test was compiled and run in the sandbox before a reviewer sees it | 11 tests ran on head, again for flakes, and on base; 0 flaky | **met** |
| G3 | A test that passes on both versions is not presented as CVE evidence | 2 fix-pinning confirmed; pass-on-both CVE tests are classified test-bug and excluded from VEX 'fixed' | **met** |
| G4 | Stage 0 passed before evidence was produced | 15 of 15 register checks; sandbox probe skipped; model probe skipped | **met** |
| G5 | Generated tests ran with no network, no secrets, read-only root, disposable container | {'capabilities': 'all dropped', 'disposable': True, 'limits': {'cpus': '2', 'memory': '2g', 'pids': 512, 'timeout_s': 900}, 'network': 'none', 'no_new_privilege | **met** |
| G6 | Every accepted test carries a provenance record and a signed attestation | 7 records; envelopes verified locally: [True]; signer is a development key | **met (development signer)** |
| G7 | Every advisory on the work item has a CVE-targeted test attempt and a draft VEX statement | python-jose: {'CVE-2024-29370': 'under_investigation', 'CVE-2024-33663': 'under_investigation', 'CVE-2024-33664': 'fixed'} | **met** |
| G8 | The run surfaces a finding the PR diff does not show | python-jose: ['python-jose: a code path raised the same internal error on both versions during ', 'python-jose: a code path raised the same internal error on bo | **met** |
| G9 | Packet within 2 hours of trigger for depth 0 and 1 | intake 2026-09-12T01:42:29+00:00 -> packet 2026-09-13T01:31:59+00:00 | **see measurement** |
| G10 | Every number in the packet points at a file in the work directory | packet sections cite artifact paths; attestation subjects are the patch and the manifest digests | **met** |
| G11 | Test strength measured by mutation and coverage delta | mutation testing and a baseline overlay suite are not in this slice | **not applicable** |
