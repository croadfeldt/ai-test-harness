```python
import pytest
from jose import jwt, jwe, jws, JWTError, ExpiredSignatureError, JWSSignatureError
from jose.constants import Algorithms
from jose.utils import base64url_encode, base64url_decode

SECRET = "test-secret-key-12345"


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    claims = {"sub": "user1", "name": "Alice"}
    token = jwt.encode(claims, SECRET, algorithm=Algorithms.HS256)
    decoded = jwt.decode(token, SECRET, algorithms=[Algorithms.HS256])
    assert decoded["sub"] == "user1"
    assert decoded["name"] == "Alice"


def test_jwt_decode_wrong_key_raises():
    """jwt.decode with a different key raises JWSSignatureError."""
    token = jwt.encode({"sub": "u"}, SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(JWSSignatureError):
        jwt.decode(token, "wrong-key", algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the alg and typ fields."""
    token = jwt.encode({"a": 1}, SECRET, algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims():
    """jwt.get_unverified_claims returns claims without signature check."""
    token = jwt.encode({"x": 42}, SECRET, algorithm=Algorithms.HS256)
    claims = jwt.get_unverified_claims(token)
    assert claims["x"] == 42


def test_jwt_expired_token_raises():
    """jwt.decode raises ExpiredSignatureError for an expired token."""
    from datetime import datetime, timedelta

    now = datetime(2000, 1, 1)  # fixed past time to ensure expiry relative to now is not needed; use explicit exp in past relative to decode time — but decode uses current time. Use a far-past exp.
    exp_past = int(datetime(1990, 1, 1).timestamp()) if hasattr(datetime(1990, 1, 1), 'timestamp') else None

    # Simpler: set exp to a fixed past epoch value (e.g., year 2000) which is always in the past at test run time (post-2000). This is deterministic for any run after year 2000. We accept that constraint. The task says no time-of-day dependence; using a fixed past epoch is fine as long as it's always in the past. We'll use year 2000.

    import time as _time

    # Use a fixed past timestamp: Jan 1 2000 UTC ≈ 946684800. This is always in the past for any realistic test run. We'll hardcode it as an integer constant derived from a known value to avoid importing datetime at module level complexity. Actually we can just use a literal int.

    # Let's just use a literal: Jan 1 2000 UTC = 946684800 seconds since epoch. This is deterministic and always in the past (assuming tests run after year 2000).

    exp_val = 946684800

    token = jwt.encode({"exp": exp_val}, SECRET, algorithm=Algorithms.HS256)

    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, SECRET, algorithms=[Algorithms.HS256])


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns True for valid signature."""
    payload = b"hello world"
    token = jws.sign(payload, SECRET, algorithm=Algorithms.HS256)
    result = jws.verify(token, SECRET, [Algorithms.HS256])
    assert result is True


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    plaintext = b"secret message"

```