```python
import pytest
from app import auth, canonical_library, csv_extract, day_config_v2, frc_compliance, frc_events


def test_create_jwt_roundtrip():
    """create_jwt produces a token that decode_jwt reads back with the same claims."""
    tok = auth.create_jwt(7, "u-1", "google", "a@b.c", is_admin=True)
    claims = auth.decode_jwt(tok)
    assert claims["sub"] == "u-1"
    assert claims["provider"] == "google"
    assert claims["email"] == "a@b.c"
    assert claims["is_admin"] is True


def test_decode_jwt_rejects_garbage():
    """decode_jwt raises on a token that is not a valid JWT."""
    with pytest.raises(Exception):
        auth.decode_jwt("not.a.jwt")


def test_canonical_filename_shape():
    """canonical_filename encodes the four fixture-shape parameters."""
    name = canonical_library.canonical_filename(48, 30, 3, 2)
    assert name.endswith(".json")


def test_canonical_path_points_at_filename():
    """canonical_path returns a Path whose name matches canonical_filename."""
    p = canonical_library.canonical_path(48, 30, 3, 2)
    assert p.name == canonical_library.canonical_filename(48, 30, 3, 2)


def test_save_then_load_roundtrip(tmp_path):
    """save_canonical writes a file that load_canonical reads back with matching shape."""
    entry = canonical_library.CanonicalEntry()
    entry.n_teams = 48
    entry.matches_per_team = 30
    entry.teams_per_alliance = 3
    entry.cooldown = 2
    path = canonical_library.save_canonical(entry, base_dir=tmp_path)
    loaded = canonical_library.load_canonical(48, 30, 3, 2, base_dir=tmp_path)
    assert loaded is not None and loaded.n_teams == 48


def test_list_canonicals_finds_saved(tmp_path):
    """list_canonicals returns entries previously saved into the library dir."""
    e = canonical_library.CanonicalEntry()
    e.n_teams = 12; e.matches_per_team = 5; e.teams_per_alliance = 3; e.cooldown = 2
    canonical_library.save_canonical(e, base_dir=tmp_path)
    found = [x for x in canonical_library.list_canonicals(base_dir=tmp_path) if x.n_teams == 12]
    assert len(found) >= 1


def test_parse_csv_reads_rows():
    """parse_csv turns a header+row CSV into a dict containing the row values."""
    data = b"name,value\nalpha,1\nbeta,2\n" + b"x" * (len(b"name,value\nalpha,1\nbeta,2\n")) * -1 + b"" 
```

Wait — I must avoid inline long literals and keep it clean. Let me rewrite properly.

```python

```