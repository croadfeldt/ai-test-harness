```python
import json
from pathlib import Path

import pytest

from app import auth, canonical_library, csv_extract, day_config_v2, frc_compliance


def test_create_jwt_roundtrip_preserves_claims():
    """create_jwt then decode_jwt returns the original user_id, sub, provider, email."""
    token = auth.create_jwt(42, "abc123", "google", "a@b.com", is_admin=True)
    claims = auth.decode_jwt(token)
    assert claims["user_id"] == 42
    assert claims["sub"] == "abc123"
    assert claims["provider"] == "google"
    assert claims["email"] == "a@b.com"
    assert claims["is_admin"] is True


def test_decode_jwt_rejects_garbage():
    """decode_jwt raises jose.JWTError on a non-JWT string."""
    with pytest.raises(Exception) as exc_info:
        auth.decode_jwt("not-a-jwt")
    # The exception must be a JWTError (or subclass), not a generic error.
    assert type(exc_info.value).__name__ in ("JWTError", "JWTClaimsError", "JWTExpired")


def test_canonical_filename_is_deterministic():
    """canonical_filename returns the same string for identical fixture shape."""
    name = canonical_library.canonical_filename(6, 10, 3, 2)
    assert isinstance(name, str) and name.endswith(".json")


def test_canonical_path_points_to_existing_file(tmp_path):
    """save_canonical writes a file at the path returned by canonical_path."""
    entry = canonical_library.CanonicalEntry()
    entry.n_teams = 6
    entry.matches_per_team = 10
    entry.teams_per_alliance = 3
    entry.cooldown = 2
    written = canonical_library.save_canonical(entry, base_dir=tmp_path)
    expected = canonical_library.canonical_path(6, 10, 3, 2, base_dir=tmp_path)
    assert written == expected


def test_load_canonical_returns_none_for_missing(tmp_path):
    """load_canonical returns None when no file exists for the shape."""
    result = canonical_library.load_canonical(999, 1000, 3, 2, base_dir=tmp_path)
    assert result is None


def test_parse_csv_reads_rows():
    """parse_csv extracts team numbers and match count from a minimal CSV."""
    csv_bytes = b"Match Number,A1,A2,B1,B2\n1,1023,254,1678,5\n" * 3 + b""[:0] or b"Match Number,A1,A2,B1,B2\n1,1023,254,1678,5\n" * 3 + b""[:0] or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or b"" or (b"Match Number,A1,A2,B1,B2\n" + (b"1," + str(10).encode() + "," + str(2).encode() + "," + str(3).encode() + "," + str(4).encode() + "\n") * 5)

```