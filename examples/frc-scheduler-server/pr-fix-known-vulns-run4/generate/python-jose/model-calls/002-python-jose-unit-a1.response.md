```python
import pytest
from jose import jwt, jwe, jws, JWTError, JWSError, JWSSignatureError, ExpiredSignatureError
from jose.constants import Algorithms
from jose.utils import base64url_encode, base64url_decode, ensure_binary, timedelta_total_seconds
from datetime import timedelta


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims dict."""
    key = b"secret"
    claims = {"sub": "1234567890", "name": "John Doe"}
    token = jwt.encode(claims, key, algorithm=Algorithms.HS256)
    result = jwt.decode(token, key, algorithms=[Algorithms.HS256])
    assert result == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "1"}, b"key1", algorithm=Algorithms.HS256)
    with pytest.raises(JWTError):
        jwt.decode(token, b"key2", algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the alg and typ fields."""
    token = jwt.encode({"sub": "1"}, b"key", algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_decode_expired_raises_expired_signature_error():
    """jwt.decode raises ExpiredSignatureError when exp is in the past."""
    token = jwt.encode({"sub": "1", "exp": 0}, b"key", algorithm=Algorithms.HS256)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, b"key", algorithms=[Algorithms.HS256])


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    key = b"secret"
    payload = b"hello world"
    token = jws.sign(payload, key, algorithm=Algorithms.HS256)
    result = jws.verify(token, key, algorithms=[Algorithms.HS256])
    assert result == payload


def test_jws_get_unverified_claims():
    """jws.get_unverified_claims returns the payload without verification."""
    key = b"secret"
    payload = b"test payload"
    token = jws.sign(payload, key, algorithm=Algorithms.HS256)
    claims = jws.get_unverified_claims(token)
    assert claims == payload


def test_base64url_encode_decode_roundtrip():
    """base64url_encode then base64url_decode returns the original bytes."""
    data = b"hello world"
    encoded = base64url_encode(data)
    decoded = base64url_decode(encoded)
    assert decoded == data


def test_ensure_binary():
    """ensure_binary converts str to bytes and leaves bytes unchanged."""
    assert ensure_binary("hello") == b"hello"
    assert ensure_binary(b"hello") == b"hello"


def test_timedelta_total_seconds():
    """timedelta_total_seconds returns the total seconds of a timedelta."""
    assert timedelta_total_seconds(timedelta(seconds=90)) == 90
    assert timedelta_total_seconds(timedelta(hours=1, minutes=30)) == 5400


def test_jwt_encode_with_headers():
    """jwt.encode includes custom headers in the token header."""
    key = b"secret"
    claims = {"sub": "1"}
    token = jwt.encode(claims, key, algorithm=Algorithms.HS256, headers={"kid": "key1"})
    header = jwt.get_unverified_header(token)
    assert header["kid"] == "key1"
    assert header["alg"] == "HS256"
```