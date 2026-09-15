# Tests for python-jose 3.4.0: 7 candidate(s), 3 fix-pinning confirmed

This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness proved 2 of the 3 with a test that fails on the vulnerable version and passes on the fixed one; the other 1 is unproven and marked so. Accept the 7 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

| | |
|---|---|
| Package | python-jose 3.3.0 -> 3.4.0 |
| Tests proposed | 3 file(s); 10 ran, 9 pass on head, 3 fix-pinning confirmed |
| Provenance | MANIFEST.json, in-toto statement, DSSE envelope (key sha256:4f2defc2e375), UDLM records, all in the same directory |
| Commit | unsigned (no signing key configured; see [propose].sign) |
| Run | 76a3fa863e76 |

Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.
