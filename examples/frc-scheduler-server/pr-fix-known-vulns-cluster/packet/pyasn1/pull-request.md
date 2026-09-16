# Tests for pyasn1 0.4.8: 0 candidate(s), 0 fix-pinning confirmed

This change moves pyasn1 from 0.6.4 to 0.4.8, a version with 4 known vulnerabilities. That is a downgrade. The harness could not prove any of the 4 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

| | |
|---|---|
| Package | pyasn1 0.6.4 -> 0.4.8 |
| Tests proposed | 0 file(s); 0 ran, 0 pass on head, 0 fix-pinning confirmed |
| Provenance | MANIFEST.json, in-toto statement, DSSE envelope, UDLM records, all in the same directory |
| Commit | signed at propose time when [propose].sign is on |
| Run | 3d9fa72b859b |

Files this pull request carries:

- `tests/packet.md`
- `tests/vex.openvex.json`
- `tests/MANIFEST.json`
- `tests/statement.json`
- `tests/statement.dsse.json`
- `tests/signer.pub.pem`
- `tests/udlm/`

Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.
