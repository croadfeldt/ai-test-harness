```python
import pytest
from pydantic import ValidationError

from app import auth, canonical_library, csv_extract, day_config_v2


def test_decode_jwt_rejects_garbage_token():
    """decode_jwt raises on a non-JWT string instead of returning a dict."""
    with pytest.raises(Exception):
        auth.decode_jwt("not-a-valid-jwt-token")


def test_decode_jwt_rejects_oversized_token():
    """decode_jwt raises on an oversized token rather than hanging or succeeding."""
    with pytest.raises(Exception):
        auth.decode_jwt("A" * 100000)


def test_validate_v2_rejects_non_dict_input():
    """validate_v2 raises ValidationError when given a non-dict input."""
    with pytest.raises(ValidationError):
        day_config_v2.validate_v2("not a dict")


def test_validate_v2_rejects_empty_dict():
    """validate_v2 raises ValidationError for an empty dict lacking required fields."""
    with pytest.raises(ValidationError):
        day_config_v2.validate_v2({})


def test_parse_csv_rejects_binary_blob():
    """parse_csv raises on binary data that is not valid CSV text."""
    with pytest.raises(Exception):
        csv_extract.parse_csv(b"\x00\x01\x02\xff" * 100)
```