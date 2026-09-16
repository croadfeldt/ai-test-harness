# Tests for python-jose 3.4.0: 10 candidate(s), 2 fix-pinning confirmed

This change updates python-jose from 3.3.0 to 3.4.0, which closes 3 known vulnerabilities. The harness proved 1 of the 3 with a test that fails on the vulnerable version and passes on the fixed one; the other 2 are unproven and marked so. Accept the 10 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

| | |
|---|---|
| Package | python-jose 3.3.0 -> 3.4.0 |
| Tests proposed | 2 file(s); 14 ran, 14 pass on head, 2 fix-pinning confirmed |
| Provenance | MANIFEST.json, in-toto statement, DSSE envelope (key sha256:f1695b2ad7cb), UDLM records, all in the same directory |
| Commit | signed at propose time when [propose].sign is on |
| Run | 3d9fa72b859b |

Files this pull request carries:

- `overlays/python/python-jose/3.4.x/test_python_jose_cve_cve_2024_33663.py`
- `overlays/python/python-jose/3.4.x/test_python_jose_unit.py`
- `overlays/python/python-jose/3.4.x/packet.md`
- `overlays/python/python-jose/3.4.x/vex.openvex.json`
- `overlays/python/python-jose/3.4.x/MANIFEST.json`
- `overlays/python/python-jose/3.4.x/statement.json`
- `overlays/python/python-jose/3.4.x/statement.dsse.json`
- `overlays/python/python-jose/3.4.x/signer.pub.pem`
- `overlays/python/python-jose/3.4.x/udlm/`

Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.
