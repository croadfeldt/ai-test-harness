```python
import pytest
from jose import jwt, jwe, jws, JWTError, ExpiredSignatureError, JWSError
from jose.constants import Algorithms
from jose.utils import base64url_encode, base64url_decode, ensure_binary

SECRET = b"unit-test-secret-key-0123456789"


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    claims = {"sub": "user1", "name": "Alice"}
    token = jwt.encode(claims, SECRET, algorithm=Algorithms.HS256)
    assert jwt.decode(token, SECRET, algorithms=[Algorithms.HS256]) == claims


def test_jwt_decode_wrong_key_raises_jwterror():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "u"}, SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(JWTError):
        jwt.decode(token, b"wrong-secret-key-0123456789012345", algorithms=[Algorithms.HS256])


def test_jwt_decode_expired_raises_expiredsignatureerror():
    """jwt.decode of an expired token raises ExpiredSignatureError."""
    token = jwt.encode({"exp": 1000}, SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, SECRET, algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header_returns_alg():
    """jwt.get_unverified_header returns the alg from the header."""
    token = jwt.encode({"sub": "u"}, SECRET, algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"


def test_jwt_get_unverified_claims_returns_claims():
    """jwt.get_unverified_claims returns the claims without verification."""
    token = jwt.encode({"sub": "u", "x": 42}, SECRET, algorithm=Algorithms.HS256)
    assert jwt.get_unverified_claims(token) == {"sub": "u", "x": 42}


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    key = b"A" * 32  # 256-bit key for A256GCM
    plaintext = b"hello world"
    jwe_str = jwe.encrypt(plaintext, key, encryption=Algorithms.A256GCM, algorithm=Algorithms.DIR)
    assert jwe.decrypt(jwe_str, key) == plaintext


def test_jwe_get_unverified_header_returns_enc():
    """jwe.get_unverified_header returns the enc from the header."""
    key = b"B" * 32
    jwe_str = jwe.encrypt(b"data", key, encryption=Algorithms.A256GCM, algorithm=Algorithms.DIR)
    header = jwe.get_unverified_header(jwe_str)
    assert header["enc"] == "A256GCM"


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    payload = b"some payload"
    token = jws.sign(payload, SECRET, algorithm=Algorithms.HS256)
    assert jws.verify(token, SECRET, [Algorithms.HS256]) == payload


def test_jws_get_unverified_claims_returns_payload():
    """jws.get_unverified_claims returns the payload without verification."""
    payload = b"test payload"
    token = jws.sign(payload, SECRET, algorithm=Algorithms.HS256)
    assert jws.get_unverified_claims(token) == payload


def test_base64url_encode_decode_roundtrip():
    """base64url_encode then base64url_decode returns the original bytes."""
    data = b"hello \x00\x01\x02"
    encoded = base64url_encode(data)
    assert base64url_decode(encoded) == data


def test_ensure_binary_converts_str_to_bytes():
    """ensure_binary converts a str to bytes and leaves bytes unchanged."""
    assert ensure_binary("abc") == b"abc"
    assert ensure_binary(b"abc") == b"abc"
```