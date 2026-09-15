```python
import json
from pathlib import Path

import pytest

from app.auth import create_jwt, decode_jwt
from app.canonical_library import (
    CanonicalEntry,
    canonical_filename,
    canonical_path,
    load_canonical,
    save_canonical,
)
from app.csv_extract import parse_csv


def test_create_jwt_roundtrip_preserves_claims():
    """create_jwt then decode_jwt returns the original user_id/sub/provider/email."""
    token = create_jwt(7, "sub-7", "google", "a@b.com", is_admin=True)
    claims = decode_jwt(token)
    assert claims["user_id"] == 7
    assert claims["sub"] == "sub-7"
    assert claims["provider"] == "google"
    assert claims["email"] == "a@b.com"


def test_decode_jwt_rejects_garbage():
    """decode_jwt raises ValueError on a non-JWT token."""
    with pytest.raises(ValueError):
        decode_jwt("not-a-jwt")


def test_canonical_filename_encodes_shape():
    """canonical_filename embeds the four shape parameters in a stable order."""
    name = canonical_filename(12, 4, 3, 2)
    assert name.startswith("12x4x3") and name.endswith(".json")


def test_canonical_path_uses_base_dir():
    """canonical_path joins base_dir with the canonical filename."""
    p = canonical_path(12, 4, 3, 2, base_dir=Path("/tmp/x"))
    assert p.parent == Path("/tmp/x") and p.name.endswith(".json")


def test_save_then_load_roundtrip(tmp_path):
    """save_canonical writes a file that load_canonical reads back with same shape."""
    entry = CanonicalEntry(n_teams=6, matches_per_team=2, teams_per_alliance=3, cooldown=1)
    path = save_canonical(entry, base_dir=tmp_path)
    loaded = load_canonical(6, 2, 3, 1, base_dir=tmp_path)
    assert loaded is not None and loaded.n_teams == 6 and path.exists()


def test_load_canonical_missing_returns_none(tmp_path):
    """load_canonical returns None when no file exists for the shape."""
    assert load_canonical(999999, 1000000, 3, 2, base_dir=tmp_path) is None


def test_parse_csv_reads_rows():
    """parse_csv turns a two-row schedule CSV into a dict with a matches list."""
    csv_bytes = b"match_number,time,a1,a2,b1,b2\n101,,1023,,4567,\n" * 2 + b"\n" * 0 + b"\n" * (len(b"\n")) * 0 + b"" 
```

Wait — I must keep it clean and under limits. Let me rewrite properly.

```python

```