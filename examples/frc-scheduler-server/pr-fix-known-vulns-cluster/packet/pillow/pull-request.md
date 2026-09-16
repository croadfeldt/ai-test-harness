# Tests for pillow 12.3.0: 0 candidate(s), 0 fix-pinning confirmed

This change updates pillow from 11.0.0 to 12.3.0, which closes 17 known vulnerabilities. The harness could not prove any of the 17 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

| | |
|---|---|
| Package | pillow 11.0.0 -> 12.3.0 |
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
