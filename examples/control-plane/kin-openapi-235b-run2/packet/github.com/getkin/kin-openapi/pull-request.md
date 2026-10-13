# Tests for github.com/getkin/kin-openapi v0.139.0: 0 candidate(s), 0 fix-pinning confirmed

This change leaves github.com/getkin/kin-openapi at v0.139.0, which has 4 known vulnerabilities the application is exposed to. The harness could not prove any of the 4 with a test; that is stated, not hidden. Accept the 0 candidate tests if they look right, act on the findings below, and send the draft VEX statements to Product Security.

| | |
|---|---|
| Package | github.com/getkin/kin-openapi v0.139.0 v0.139.0 |
| Tests proposed | 0 file(s); 4 ran, 0 pass on head, 0 fix-pinning confirmed |
| Provenance | MANIFEST.json, in-toto statement, DSSE envelope (key sha256:acfb1ae5a1b7), UDLM records, all in the same directory |
| Commit | signed at propose time when [propose].sign is on |
| Run | 8e6fa6151887 |
| Accounted for | 5 behaviours reached: 0 validated, 0 for your environment, 5 stated gaps. |

Files this pull request carries:

- `tests/packet.md`
- `tests/vex.openvex.json`
- `tests/MANIFEST.json`
- `tests/statement.json`
- `tests/statement.dsse.json`
- `tests/signer.pub.pem`
- `tests/udlm/`

Not covered:

- `github.com/getkin/kin-openapi/openapi3.Loader`: no kept test names or executes this behaviour
- `github.com/getkin/kin-openapi/openapi3.NewLoader`: no kept test names or executes this behaviour
- `github.com/getkin/kin-openapi/openapi3.T`: no kept test names or executes this behaviour
- `github.com/getkin/kin-openapi/openapi3filter.AuthenticationInput`: no kept test names or executes this behaviour
- `github.com/getkin/kin-openapi/openapi3filter.Options`: no kept test names or executes this behaviour

Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.
