# Tests for pyasn1 0.4.8: 10 candidate(s), 2 fix-pinning confirmed

This change moves pyasn1 from 0.6.4 to 0.4.8, a version with 4 known vulnerabilities. That is a downgrade. The harness proved 1 of the 4 with a test that fails on the vulnerable version and passes on the fixed one; the other 3 are unproven and marked so. Accept the 10 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

| | |
|---|---|
| Package | pyasn1 0.6.4 -> 0.4.8 |
| Tests proposed | 2 file(s); 16 ran, 12 pass on head, 2 fix-pinning confirmed |
| Provenance | MANIFEST.json, in-toto statement, DSSE envelope (key sha256:4f2defc2e375), UDLM records, all in the same directory |
| Commit | signed at propose time when [propose].sign is on |
| Run | 76a3fa863e76 |

Files this pull request carries:

- `overlays/python/pyasn1/0.4.x/test_pyasn1_cve_cve_2026_30922.py`
- `overlays/python/pyasn1/0.4.x/test_pyasn1_unit.py`
- `overlays/python/pyasn1/0.4.x/packet.md`
- `overlays/python/pyasn1/0.4.x/vex.openvex.json`
- `overlays/python/pyasn1/0.4.x/MANIFEST.json`
- `overlays/python/pyasn1/0.4.x/statement.json`
- `overlays/python/pyasn1/0.4.x/statement.dsse.json`
- `overlays/python/pyasn1/0.4.x/signer.pub.pem`
- `overlays/python/pyasn1/0.4.x/udlm/`

Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.
