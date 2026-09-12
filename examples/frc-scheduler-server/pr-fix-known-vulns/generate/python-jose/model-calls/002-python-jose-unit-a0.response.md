```python
"""Unit tests for python-jose 3.4.0 public API used by the application."""

import pytest
from jose import jwt, jwe, jws, jwk, utils, constants, exceptions


def test_jwt_encode_decode_roundtrip():
    """jwt.encode with HS256 produces a token that jwt.decode verifies and returns the original claims."""
    key = "secret-key-for-testing"
    claims = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
    token = jwt.encode(claims, key, algorithm="HS256")
    decoded = jwt.decode(token, key, algorithms=["HS256"])
    assert decoded["sub"] == "1234567890"
    assert decoded["name"] == "John Doe"
    assert decoded["iat"] == 1516239022


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode raises JWTError when the key does not match the token's signature."""
    token = jwt.encode({"sub": "test"}, "correct-key", algorithm="HS256")
    with pytest.raises(exceptions.JWTError):
        jwt.decode(token, "wrong-key", algorithms=["HS256"])


def test_jwt_get_unverified_header_returns_algorithm():
    """jwt.get_unverified_header returns the header dict including the algorithm field."""
    token = jwt.encode({"sub": "test"}, "key", algorithm="HS256")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims_returns_claims_without_verification():
    """jwt.get_unverified_claims returns the claims dict without verifying the signature."""
    token = jwt.encode({"sub": "abc", "custom": "value"}, "key", algorithm="HS256")
    claims = jwt.get_unverified_claims(token)
    assert claims["sub"] == "abc"
    assert claims["custom"] == "value"


def test_jwt_decode_expired_token_raises_expired_signature_error():
    """jwt.decode raises ExpiredSignatureError when the token's exp claim is in the past."""
    token = jwt.encode({"sub": "test", "exp": 1516239022}, "key", algorithm="HS256")
    with pytest.raises(exceptions.ExpiredSignatureError):
        jwt.decode(token, "key", algorithms=["HS256"])


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt and jwe.decrypt roundtrip preserves the original plaintext."""
    key = "0" * 64  # 256-bit key for A256GCM
    plaintext = "Hello, JWE world!"
    jwe_str = jwe.encrypt(plaintext, key, encryption="A256GCM", algorithm="dir")
    decrypted = jwe.decrypt(jwe_str, key)
    assert decrypted == plaintext


def test_jws_sign_verify_roundtrip():
    """jws.sign and jws.verify roundtrip preserves the original payload."""
    key = "signing-key"
    payload = b"test payload data"
    token = jws.sign(payload, key, algorithm="HS256")
    verified = jws.verify(token, key, algorithms=["HS256"])
    assert verified is True


def test_jws_verify_wrong_key_raises_jwt_error():
    """jws.verify raises JWTError when the key does not match the signature."""
    token = jws.sign(b"payload", "correct-key", algorithm="HS256")
    with pytest.raises(exceptions.JWTError):
        jws.verify(token, "wrong-key", algorithms=["HS256"])


def test_utils_base64url_encode_decode_roundtrip():
    """utils.base64url_encode and utils.base64url_decode roundtrip preserves the original bytes."""
    data = b"Hello, World! This is a test."
    encoded = utils.base64url_encode(data)
    decoded = utils.base64url_decode(encoded)
    assert decoded == data


def test_constants_algorithms_has_hs256():
    """constants.Algorithms.HS256 is the string 'HS256'."""
    assert constants.Algorithms.HS256 == "HS256"
```