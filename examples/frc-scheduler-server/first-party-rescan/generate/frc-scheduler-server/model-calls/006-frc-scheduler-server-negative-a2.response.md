```python
import pytest
from pydantic import ValidationError

from app.auth import create_jwt, decode_jwt
from app.csv_extract import parse_csv
from app.day_config_v2 import validate_v2


def test_decode_jwt_rejects_garbage_token():
    """decode_jwt raises a specific exception for a non-JWT string."""
    with pytest.raises(Exception) as exc_info:
        decode_jwt("not-a-jwt-token")
    # Must be a specific, documented exception (e.g. jose.JWTError or similar)
    assert not isinstance(exc_info.value, (ValueError, TypeError)), \
        f"Expected a specific JWT exception, got {type(exc_info.value).__name__}"


def test_decode_jwt_rejects_oversized_token():
    """decode_jwt raises a specific exception for an oversized token."""
    oversized = "a" * 100_000 + "." + "b" * 100_000 + "." + "c" * 100_000
    with pytest.raises(Exception) as exc_info:
        decode_jwt(oversized)
    assert not isinstance(exc_info.value, (ValueError, TypeError)), \
        f"Expected a specific JWT exception, got {type(exc_info.value).__name__}"


def test_parse_csv_rejects_binary_blob():
    """parse_csv raises a specific exception for non-CSV binary data."""
    binary = b"\x89PNG\r\n\x1a\n" + b"\x00" * 512
    with pytest.raises(Exception) as exc_info:
        parse_csv(binary)
    assert not isinstance(exc_info.value, (ValueError, TypeError)), \
        f"Expected a specific parse exception, got {type(exc_info.value).__name__}"


def test_validate_v2_rejects_non_dict_input():
    """validate_v2 raises ValidationError when given a non-dict input."""
    with pytest.raises(ValidationError):
        validate_v2("not a dict")


def test_validate_v2_rejects_missing_required_fields():
    """validate_v2 raises ValidationError when required V2 fields are absent."""
    with pytest.raises(ValidationError):
        validate_v2({})


def test_create_jwt_rejects_non_int_user_id():
    """create_jwt raises TypeError when user_id is not an int."""
    with pytest.raises(TypeError):
        create_jwt(user_id="not-an-int", sub="user@example.com", provider="google", email=None)


def test_decode_jwt_rejects_empty_string():
    """decode_jwt raises a specific exception for an empty string token."""
    with pytest.raises(Exception) as exc_info:
        decode_jwt("")
    assert not isinstance(exc_info.value, (ValueError, TypeError)), \
        f"Expected a specific JWT exception, got {type(exc_info.value).__name__}"


def test_parse_csv_rejects_empty_bytes():
    """parse_csv raises a specific exception for empty input."""
    with pytest.raises(Exception) as exc_info:
        parse_csv(b"")


def test_validate_v2_rejects_wrong_type_for_blocks():
    """validate_v2 raises ValidationError when blocks is not a list of dicts."""
    bad = {"version": 2, "days": [{"blocks": "not-a-list"}]} if False else {"version": 2} | {"days": [{"blocks": "oops"}]} if False else None

# Simpler approach: build minimal invalid V2 dict directly.

def _bad_v2_dict() -> dict:  # helper to avoid inline complexity in tests above if needed.

# Re-do the last two tests cleanly.

# --- Clean re-implementation of the last two tests ---

# We already have 7 tests above; let's just keep the file at exactly those and ensure they're correct.

# Actually the file above has issues. Let me rewrite cleanly below.

```

Wait — I need to output exactly one Python file. Let me redo this properly.

```python

import pytest

from app.auth import create_jwt, decode_jwt  
from app.csv_extract import parse_csv  
from app.day_config_v2 import validate_v2  
from pydantic import ValidationError  

  
def test_decode_jwt_rejects_garbage_token():  
    """decode_jwt raises a specific JWT-related exception for non-JWT input."""  
    with pytest.raises(Exception) as excinfo:  
        decode_jwt("garbage-not-a-jwt")  
    # The raised exception must NOT be a bare ValueError or TypeError; it should be  
    # something like jose.JWTError / jwt.InvalidTokenError / similar domain-specific type.  
    assert type(excinfo.value).__name__ not in ("ValueError", "TypeError"), (  
        f"Expected domain-specific JWT error, got {type(excinfo.value).__name__}"  
    )  

  
def test_decode_jwt_rejects_oversized_token():  
    """decode_jwt raises a specific JWT-related exception for an oversized token."""  
    big = ("A" * 50_000 + "." + "B" * 50_000 + "." + "C" * 50_000)  
    with pytest.raises(Exception) as excinfo:  
        decode_jwt(big)  
    assert type(excinfo.value).__name__ not in ("ValueError", "TypeError"), (  
        f"Expected domain-specific JWT error, got {type(excinfo.value).__name__}"  
    )  

  
def test_parse_csv_rejects_binary_blob():  
    """parse_csv raises a specific parsing exception for binary (non-text) input."""  
    blob = b"\x89PNG\r\n\x1a\n\xda\xed\xad\xfe\xbe\xef\xff\xfe\xfd\xfc" * 64  
    with pytest.raises(Exception) as excinfo:  
        parse_csv(blob)  
    # Should be UnicodeDecodeError / csv.Error / ValueError-from-csv — but NOT bare TypeError.  
    assert type(excinfo.value).__name__ != "TypeError", (  
        f"Expected parsing/decode error, got {type(excinfo.value).__name__}"  
    )  

  
def test_validate_v2_raises_validation_error_on_non_dict():  
"""validate_v2 raises pydantic.ValidationError when input is not a dict.""" 
with pytest.raises(ValidationError): 
validate_v2("this is not a dict") 

 
def test_validate_v2_raises_validation_error_on_empty_dict(): 
"""validate_v2 raises pydantic.ValidationError when required V2 fields are missing.""" 
with pytest.raises(ValidationError): 
validate_v2({}) 

```