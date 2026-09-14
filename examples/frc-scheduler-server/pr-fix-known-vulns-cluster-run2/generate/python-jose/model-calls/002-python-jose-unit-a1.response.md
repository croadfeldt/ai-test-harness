```python
import pytest
from jose import jwt, jwe, jws, JWTError
from jose.exceptions import (
    ExpiredSignatureError,
    JWSSignatureError,
    JWKError,
    JOSEError,
)
from jose.utils import base64url_encode, base64url_decode, ensure_binary


def _make_token(claims, key=b"secret", algorithm="HS256"):
    return jwt.encode(claims, key, algorithm=algorithm)


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    claims = {"sub": "user-1", "data": 42}
    token = _make_token(claims)
    assert jwt.decode(token, b"secret", algorithms=["HS256"]) == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """Decoding with the wrong key raises JWTError."""
    token = _make_token({"sub": "user-1"})
    with pytest.raises(JWTError):
        jwt.decode(token, b"other", algorithms=["HS256"])


def test_jwt_decode_expired_raises_expired_signature_error():
    """A token whose exp is in the past raises ExpiredSignatureError."""
    token = _make_token({"sub": "u", "exp": 1})
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, b"secret", algorithms=["HS256"])


def test_jwt_get_unverified_header_returns_alg():
    """get_unverified_header returns the header dict with the alg."""
    token = _make_token({"sub": "u"})
    assert jwt.get_unverified_header(token) == {"alg": "HS256", "typ": "JWT"}


def test_jwt_get_unverified_claims_returns_claims():
    """get_unverified_claims returns the claims without verification."""
    token = _make_token({"sub": "u", "x": 7})
    assert jwt.get_unverified_claims(token) == {"sub": "u", "x": 7}


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    key = b"A" * 32
    jwe_str = jwe.encrypt(b"hello world", key)
    assert jwe.decrypt(jwe_str, key) == b"hello world"


def test_jwe_wrong_key_raises_jwk_error():
    """Decrypting with a different key raises JWKError."""
    jwe_str = jwe.encrypt(b"hello", b"A" * 32)
    with pytest.raises(JWKError):
        jwe.decrypt(jwe_str, b"B" * 32)


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    payload = b"payload-data"
    token = jws.sign(payload, b"secret", algorithm="HS256")
    assert jws.verify(token, b"secret", ["HS256"]) == payload


def test_jws_verify_wrong_key_raises_signature_error():
    """jws.verify with the wrong key raises JWSSignatureError."""
    token = jws.sign(b"payload", b"secret", algorithm="HS256")
    with pytest.raises(JWSSignatureError):
        jws.verify(token, b"wrong", ["HS256"])


def test_base64url_roundtrip_and_ensure_binary():
    """base64url encode/decode roundtrip and ensure_binary coercion."""
    data = b"abc" * 10
    assert base64url_decode(base64url_encode(data)) == data
    assert ensure_binary("text") == b"text"
    assert ensure_binary(b"raw") == b"raw"
```