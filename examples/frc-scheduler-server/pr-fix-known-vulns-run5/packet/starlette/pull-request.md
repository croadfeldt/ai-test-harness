# Tests for starlette 0.41.3: 6 candidate(s), 2 fix-pinning confirmed

This change leaves starlette at 0.41.3, which has 7 known vulnerabilities the application is exposed to. The harness proved 1 of the 7 with a test that fails on the vulnerable version and passes on the fixed one; the other 6 are unproven and marked so. Accept the 6 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

| | |
|---|---|
| Package | starlette 0.41.3 0.41.3 |
| Tests proposed | 2 file(s); 18 ran, 10 pass on head, 2 fix-pinning confirmed |
| Provenance | MANIFEST.json, in-toto statement, DSSE envelope (key sha256:4f2defc2e375), UDLM records, all in the same directory |
| Commit | signed at propose time when [propose].sign is on |
| Run | 76a3fa863e76 |

Files this pull request carries:

- `overlays/python/starlette/0.41.x/test_starlette_cve_cve_2026_54283.py`
- `overlays/python/starlette/0.41.x/test_starlette_unit.py`
- `overlays/python/starlette/0.41.x/packet.md`
- `overlays/python/starlette/0.41.x/vex.openvex.json`
- `overlays/python/starlette/0.41.x/MANIFEST.json`
- `overlays/python/starlette/0.41.x/statement.json`
- `overlays/python/starlette/0.41.x/statement.dsse.json`
- `overlays/python/starlette/0.41.x/signer.pub.pem`
- `overlays/python/starlette/0.41.x/udlm/`

Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.
