```python
import pytest
from jose import jwt, jwe, jws, jwk, utils, constants, exceptions
from jose.exceptions import JWTError, ExpiredSignatureError, JWSSignatureError
from cryptography.hazmat.primitives.asymmetric import rsa as _rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta, timezone


def _rsa_key():
    key = _rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def test_jwt_encode_hs256_structure():
    """jwt.encode with HS256 produces a 3-part token with alg HS256."""
    token = jwt.encode({"sub": "u1"}, "secret", algorithm="HS256")
    assert token.count(".") == 2
    assert jwt.get_unverified_header(token)["alg"] == "HS256"


def test_jwt_decode_roundtrip_hs256():
    """jwt.decode returns the original claims for a valid HS256 token."""
    claims = {"sub": "u1", "name": "Alice"}
    token = jwt.encode(claims, "secret", algorithm="HS256")
    assert jwt.decode(token, "secret", algorithms=["HS256"]) == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "u1"}, "secret", algorithm="HS256")
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong", algorithms=["HS256"])


def test_jwt_decode_expired_raises_expired_signature_error():
    """jwt.decode raises ExpiredSignatureError when exp is in the past."""
    past = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
    token = jwt.encode({"sub": "u1", "exp": past}, "secret", algorithm="HS256")
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, "secret", algorithms=["HS256"])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the header dict without verification."""
    token = jwt.encode({"a": 1}, "secret", algorithm="HS256")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims():
    """jwt.get_unverified_claims returns the claims dict without verification."""
    claims = {"sub": "u1", "custom": "val"}
    token = jwt.encode(claims, "secret", algorithm="HS256")
    assert jwt.get_unverified_claims(token) == claims


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    key = _rsa_key()
    plaintext = b"hello world"
    jwe_str = jwe.encrypt(plaintext, key)
    assert jwe.decrypt(jwe_str, key) == plaintext


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    key = _rsa_key()
    payload = b"some payload"
    token = jws.sign(payload, key, algorithm="RS256")
    assert jws.verify(token, key, ["RS256"]) == payload


def test_jws_verify_wrong_key_raises_signature_error():
    """jws.verify with a different key raises JWSSignatureError."""
    key1 = _rsa_key()
    key2 = _rsa_key()
    token = jws.sign(b"data", key1, algorithm="RS256")
    with pytest.raises(JWSSignatureError):
        jws.verify(token, key2, ["RS256"])


def test_utils_base64url_roundtrip():
    """utils.base64url_encode then base64url_decode returns the original bytes."""
    data = b"test data \x00\x01\x02"
    encoded = utils.base64url_encode(data)
    assert utils.base64url_decode(encoded) == data
```