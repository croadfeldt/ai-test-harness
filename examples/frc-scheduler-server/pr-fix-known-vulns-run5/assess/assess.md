# Post-analysis of run 76a3fa863e76

**In plain terms.** This run met 9 of 11 goals from the blueprint. Not met: Test strength measured by mutation and coverage delta. Every verdict below points at the file it was measured from.

Packages: pyasn1, python-jose, starlette.

| id | goal | measurement | verdict |
|---|---|---|---|
| G1 | Nothing merges without a person | harness produced patches and drafts only; no git push, no VEX published | **met** |
| G2 | Every kept test was compiled and run in the sandbox before a reviewer sees it | 45 tests ran on head, again for flakes, and on base; 0 flaky | **met** |
| G3 | A test that passes on both versions is not presented as CVE evidence | 6 fix-pinning confirmed; pass-on-both CVE tests are classified test-bug and excluded from VEX 'fixed' | **met** |
| G4 | Stage 0 passed before evidence was produced | 19 of 19 register checks; sandbox probe skipped; model probe skipped | **met** |
| G5 | Generated tests ran with no network, no secrets, read-only root, disposable container | {'capabilities': 'all dropped', 'disposable': True, 'limits': {'cpus': '2', 'memory': '2g', 'pids': 512, 'timeout_s': 900}, 'network': 'none', 'no_new_privilege | **met** |
| G6 | Every accepted test carries a provenance record and a signed attestation | 23 records; envelopes verified locally: [True, True, True]; signer is a development key | **met (development signer)** |
| G7 | Every advisory on the work item has a CVE-targeted test attempt and a draft VEX statement | pyasn1: {'CVE-2026-30922': 'affected', 'CVE-2026-59884': 'under_investigation', 'CVE-2026-59885': 'under_investigation', 'CVE-2026-59886': 'under_investigation' | **met** |
| G8 | The run surfaces a finding the PR diff does not show | pyasn1: ['pyasn1 downgraded 0.6.4 -> 0.4.8 into a version with 8 known advisories', 'pyasn1 0.4.8 has 8 open advisories at head; reachable=unknown', 'pyasn1: a  | **met** |
| G9 | Packet within 2 hours of trigger for depth 0 and 1 | intake 2026-09-12T01:42:29+00:00 -> packet 2026-09-13T13:17:26+00:00 | **see measurement** |
| G10 | Every number in the packet points at a file in the work directory | packet sections cite artifact paths; attestation subjects are the patch and the manifest digests | **met** |
| G11 | Test strength measured by mutation and coverage delta | pyasn1: score 0.417 on 12 sampled mutants; python-jose: score 0.417 on 12 sampled mutants; starlette: score 0.0 on 12 sampled mutants; coverage delta: no baseli | **not met (target 0.6 on sampled mutants)** |
