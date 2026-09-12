```python
"""Tests for python-jose 3.4.0 public API used by the application."""
import pytest
from jose import jwt, jwe, jws, jwk, JWTError
from jose.constants import Algorithms
from jose.exceptions import (
    JWSSignatureError,
    ExpiredSignatureError,
    JWTClaimsError,
    JOSEError,
)
from jose.utils import base64url_encode, base64url_decode, ensure_binary


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    key = "secret-key-12345"
    claims = {"sub": "user1", "name": "Alice"}
    token = jwt.encode(claims, key, algorithm=Algorithms.HS256)
    decoded = jwt.decode(token, key, algorithms=[Algorithms.HS256])
    assert decoded["sub"] == "user1"
    assert decoded["name"] == "Alice"


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "u"}, "correct-key", algorithm=Algorithms.HS256)
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong-key", algorithms=[Algorithms.HS256])


def test_jwt_decode_expired_raises_expired_signature_error():
    """jwt.decode of an expired token raises ExpiredSignatureError."""
    token = jwt.encode({"sub": "u", "exp": 1}, "k", algorithm=Algorithms.HS256)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, "k", algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header_returns_alg():
    """jwt.get_unverified_header returns the algorithm from the header."""
    token = jwt.encode({"sub": "x"}, "k", algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"


def test_jwt_get_unverified_claims_returns_claims():
    """jwt.get_unverified_claims returns the claims without verification."""
    token = jwt.encode({"sub": "abc", "custom": 42}, "k", algorithm=Algorithms.HS256)
    claims = jwt.get_unverified_claims(token)
    assert claims["sub"] == "abc"
    assert claims["custom"] == 42


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    key = "0" * 64  # 256-bit key for A256GCM
    plaintext = b"hello world"
    jwe_str = jwe.encrypt(plaintext, key, algorithm=Algorithms.DIR, encryption=Algorithms.A256GCM)
    decrypted = jwe.decrypt(jwe_str, key)
    assert decrypted == plaintext


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    key = "signing-key"
    payload = b"some payload data"
    token = jws.sign(payload, key, algorithm=Algorithms.HS256)
    verified = jws.verify(token, key, algorithms=[Algorithms.HS256])
    assert verified == payload


def test_jws_verify_wrong_key_raises_signature_error():
    """jws.verify with a wrong key raises JWSSignatureError."""
    token = jws.sign(b"data", "key1", algorithm=Algorithms.HS256)
    with pytest.raises(JWSSignatureError):
        jws.verify(token, "key2", algorithms=[Algorithms.HS256])


def test_base64url_encode_decode_roundtrip():
    """base64url_encode then base64url_decode returns the original bytes."""
    data = b"test data \x00\x01\x02"
    encoded = base64url_encode(data)
    decoded = base64url_decode(encoded)
    assert decoded == data


def test_ensure_binary_converts_str_to_bytes():
    """ensure_binary converts a str to bytes and passes bytes through."""
    assert ensure_binary("hello") == b"hello"
    assert ensure_binary(b"world") == b"world"
```