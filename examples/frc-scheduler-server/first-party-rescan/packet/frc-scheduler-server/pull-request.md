# Tests for frc-scheduler-server 2ad04243861b: 4 candidate(s), 0 fix-pinning confirmed

This is the application's own code, frc-scheduler-server, at commit 2ad04243861b. No known vulnerability applies to it, so there is nothing to prove; the tests below characterize what the code does today. Accept the 4 candidate tests if they look right, act on the findings below.

| | |
|---|---|
| Package | frc-scheduler-server (the application's own code) |
| Tests proposed | 1 file(s); 4 ran, 4 pass on head, 0 fix-pinning confirmed |
| Provenance | MANIFEST.json, in-toto statement, DSSE envelope (key sha256:4f2defc2e375), UDLM records, all in the same directory |
| Commit | signed at propose time when [propose].sign is on |
| Run | 50ec3b2446fe |
| Accounted for | 40 behaviours reached: 0 validated, 0 for your environment, 40 stated gaps. |

Files this pull request carries:

- `tests/test_frc_scheduler_server_unit.py`
- `tests/packet.md`
- `tests/vex.openvex.json`
- `tests/MANIFEST.json`
- `tests/statement.json`
- `tests/statement.dsse.json`
- `tests/signer.pub.pem`
- `tests/udlm/`

Not covered:

- `app.auth.create_jwt`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.auth.decode_jwt`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.auth.get_current_user`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.auth.require_auth`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.auth.upsert_user`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.auth.google_login_url`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.auth.google_exchange_code`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.auth.apple_login_url`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.auth.apple_exchange_code`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.canonical_library.canonical_filename`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.canonical_library.canonical_path`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.canonical_library.CanonicalEntry`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.canonical_library.CanonicalEntry.to_dict`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.canonical_library.CanonicalEntry.from_dict`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.canonical_library.load_canonical`: lines ran, no mutant inside them was killed
- `app.canonical_library.save_canonical`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.canonical_library.list_canonicals`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.csv_extract.parse_csv`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.day_config_v2.validate_v2`: no kept test names or executes this behaviour
- `app.day_config_v2.is_v2_shape`: no kept test names or executes this behaviour
- `app.day_config_v2.migrate_v1_to_v2`: no kept test names or executes this behaviour
- `app.day_config_v2.downgrade_v2_to_v1`: no kept test names or executes this behaviour
- `app.day_config_v2.materialize_v2`: no kept test names or executes this behaviour
- `app.day_config_v2.normalize_to_v2`: no kept test names or executes this behaviour
- `app.db.utcnow`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.db.init_db`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.db.get_session`: lines ran, no mutant was placed inside them; a sampling gap the harness owns
- `app.frc_compliance.compute_deviations`: no kept test names or executes this behaviour
- `app.frc_compliance.is_competition_approved`: no kept test names or executes this behaviour
- `app.frc_compliance.build_audit_record`: no kept test names or executes this behaviour
- and 10 more in `triage/frc-scheduler-server/accounting.json`

Proposed by the AI Test Harness. The packet in the same directory has the findings, the verdict per test, and the draft VEX statements for Product Security. Nothing here is merged by the harness; a person decides.
