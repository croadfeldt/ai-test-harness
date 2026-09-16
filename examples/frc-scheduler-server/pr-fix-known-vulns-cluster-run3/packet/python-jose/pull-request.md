# Tests for python-jose 3.4.0: 8 candidate(s), 0 fix-pinning confirmed

This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness could not prove any of the 3 with a test; that is stated, not hidden. Accept the 8 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

| | |
|---|---|
| Package | python-jose 3.3.0 -> 3.4.0 |
| Tests proposed | 1 file(s); 14 ran, 14 pass on head, 0 fix-pinning confirmed |
| Provenance | MANIFEST.json, in-toto statement, DSSE envelope (key sha256:2b291bb6fc3c), UDLM records, all in the same directory |
| Commit | signed at propose time when [propose].sign is on |
| Run | 333f5fa69d50 |

Files this pull request carries:

- `overlays/python/python-jose/3.4.x/test_python_jose_unit.py`
- `overlays/python/python-jose/3.4.x/packet.md`
- `overlays/python/python-jose/3.4.x/vex.openvex.json`
- `overlays/python/python-jose/3.4.x/MANIFEST.json`
- `overlays/python/python-jose/3.4.x/statement.json`
- `overlays/python/python-jose/3.4.x/statement.dsse.json`
- `overlays/python/python-jose/3.4.x/signer.pub.pem`
- `overlays/python/python-jose/3.4.x/udlm/`

Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.
