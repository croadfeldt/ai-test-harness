# Post-analysis of run 50ec3b2446fe

**In plain terms.** This run met 8 of 11 goals from the blueprint. Not met: Test strength measured by mutation and coverage delta. Every verdict below points at the file it was measured from.

Packages: frc-scheduler-server.

| id | goal | measurement | verdict |
|---|---|---|---|
| G1 | Nothing merges without a person | harness produced patches and drafts only; no git push, no VEX published | **met** |
| G2 | Every kept test was compiled and run in the sandbox before a reviewer sees it | 4 tests ran on head, again for flakes, and on base; 0 flaky | **met** |
| G3 | A test that passes on both versions is not presented as CVE evidence | 0 fix-pinning confirmed; pass-on-both CVE tests are classified test-bug and excluded from VEX 'fixed' | **met** |
| G4 | Stage 0 passed before evidence was produced | 22 of 22 register checks; sandbox probe skipped; model probe skipped | **met** |
| G5 | Generated tests ran with no network, no secrets, read-only root, disposable container | {'capabilities': 'all dropped', 'disposable': True, 'limits': {'cpus': '2', 'memory': '2g', 'pids': 512, 'timeout_s': 900}, 'network': 'none', 'no_new_privilege | **met** |
| G6 | Every accepted test carries a provenance record and a signed attestation | 4 records; envelopes verified locally: [True]; signer is a development key | **met (development signer)** |
| G7 | Every advisory on the work item has a CVE-targeted test attempt and a draft VEX statement | no advisory on the work item (the application's own code, or packages with no known vulnerability) | **not applicable** |
| G8 | The run surfaces a finding the PR diff does not show | frc-scheduler-server: ['frc-scheduler-server: test_canonical_filename_encodes_shape killed none of 25 sa', 'frc-scheduler-server: test_canonical_path_uses_base_ | **met** |
| G9 | Packet within 2 hours of trigger for depth 0 and 1 | intake 2026-09-15T20:02:45+00:00 -> packet 2026-09-15T20:29:42+00:00 | **see measurement** |
| G10 | Every number in the packet points at a file in the work directory | packet sections cite artifact paths; attestation subjects are the patch and the manifest digests | **met** |
| G11 | Test strength measured by mutation and coverage delta | frc-scheduler-server: score 0.04 on 25 sampled mutants; coverage delta: no baseline overlay suite yet | **not met (target 0.6 on sampled mutants)** |
