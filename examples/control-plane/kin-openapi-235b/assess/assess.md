# Post-analysis of run dc0d1712bc6d

**In plain terms.** This run met 9 of 11 goals from the blueprint. Every verdict below points at the file it was measured from.

Packages: github.com/getkin/kin-openapi.

| id | goal | measurement | verdict |
|---|---|---|---|
| G1 | Nothing merges without a person | harness produced patches and drafts only; no git push, no VEX published | **met** |
| G2 | Every kept test was compiled and run in the sandbox before a reviewer sees it | 4 tests ran on head, again for flakes, and on base; 0 flaky | **met** |
| G3 | A test that passes on both versions is not presented as CVE evidence | 0 fix-pinning confirmed; pass-on-both CVE tests are classified test-bug and excluded from VEX 'fixed' | **met** |
| G4 | Stage 0 passed before evidence was produced | 22 of 22 register checks; sandbox probe skipped; model probe skipped | **met** |
| G5 | Generated tests ran with no network, no secrets, read-only root, disposable container | {'build_cache': 'per environment on the shared workspace', 'disposable': 'the task pod', 'limits': {'cpus': '2', 'memory': '4g', 'pids': 1024, 'timeout_s': 1200 | **met** |
| G6 | Every accepted test carries a provenance record and a signed attestation | 0 records; envelopes verified locally: [True]; signer is a development key | **met (development signer)** |
| G7 | Every advisory on the work item has a CVE-targeted test attempt and a draft VEX statement | github.com/getkin/kin-openapi: {'CVE-2026-73501': 'affected', 'CVE-2026-73502': 'affected', 'CVE-2026-76905': 'affected', 'CVE-2026-77354': 'affected'} | **met** |
| G8 | The run surfaces a finding the PR diff does not show | github.com/getkin/kin-openapi: ['github.com/getkin/kin-openapi v0.139.0 has 8 open advisories at head; reachable=', 'github.com/getkin/kin-openapi: a code path  | **met** |
| G9 | Packet within 2 hours of trigger for depth 0 and 1 | intake 2026-09-18T04:51:52+00:00 -> packet 2026-09-18T06:17:43+00:00 | **see measurement** |
| G10 | Every number in the packet points at a file in the work directory | packet sections cite artifact paths; attestation subjects are the patch and the manifest digests | **met** |
| G11 | Test strength measured by mutation and coverage delta | github.com/getkin/kin-openapi: no passing tests or no coverage; coverage delta: no baseline overlay suite yet | **not applicable** |
