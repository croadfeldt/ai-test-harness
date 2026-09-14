```python
import pytest
from jose import jwt, jws, jwe, jwk, constants, exceptions, utils
from cryptography.hazmat.primitives.asymmetric import rsa as _rsa
from cryptography.hazmat.primitives import serialization


def _rsa_key():
    key = _rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def test_jwt_encode_decode_roundtrip_hs256():
    """jwt.encode with HS256 then jwt.decode returns the original claims."""
    key = b"secret-key-for-testing"
    claims = {"sub": "1234567890", "name": "Alice", "iat": 1516239022}
    token = jwt.encode(claims, key, algorithm="HS256")
    decoded = jwt.decode(token, key, algorithms=["HS256"])
    assert decoded["sub"] == "1234567890"
    assert decoded["name"] == "Alice"
    assert decoded["iat"] == 1516239022


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "x"}, b"correct-key", algorithm="HS256")
    with pytest.raises(exceptions.JWTError):
        jwt.decode(token, b"wrong-key", algorithms=["HS256"])


def test_jwt_get_unverified_header_returns_alg():
    """jwt.get_unverified_header returns the header dict with alg field."""
    token = jwt.encode({"a": 1}, b"k", algorithm="HS256")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims_returns_claims():
    """jwt.get_unverified_claims returns the claims without verification."""
    token = jwt.encode({"foo": "bar", "n": 42}, b"k", algorithm="HS256")
    claims = jwt.get_unverified_claims(token)
    assert claims["foo"] == "bar"
    assert claims["n"] == 42


def test_jwt_decode_expired_token_raises_expired_signature_error():
    """jwt.decode raises ExpiredSignatureError when exp is in the past."""
    token = jwt.encode({"exp": 1000000000}, b"k", algorithm="HS256")
    with pytest.raises(exceptions.ExpiredSignatureError):
        jwt.decode(token, b"k", algorithms=["HS256"])


def test_jws_sign_verify_roundtrip_hs256():
    """jws.sign then jws.verify returns the original payload."""
    key = b"jws-secret"
    payload = b"hello world"
    token = jws.sign(payload, key, algorithm="HS256")
    result = jws.verify(token, key, ["HS256"])
    assert result == payload


def test_jws_verify_wrong_key_raises_jws_signature_error():
    """jws.verify with a wrong key raises JWSSignatureError."""
    token = jws.sign(b"data", b"key1", algorithm="HS256")
    with pytest.raises(exceptions.JWSSignatureError):
        jws.verify(token, b"key2", ["HS256"])


def test_jws_get_unverified_header():
    """jws.get_unverified_header returns the JWS header dict."""
    token = jws.sign(b"payload", b"k", algorithm="HS256")
    header = jws.get_unverified_header(token)
    assert header["alg"] == "HS256"


def test_jwk_construct_rsa_key():
    """jwk.construct builds a key object from PEM bytes for RS256."""
    pem = _rsa_key()
    key = jwk.construct(pem, "RS256")
    assert key.algorithm == "RS256"


def test_utils_base64url_roundtrip():
    """utils.base64url_encode then base64url_decode returns original bytes."""
    data = b"test-data-12345"
    encoded = utils.base64url_encode(data)
    decoded = utils.base64url_decode(encoded)
    assert decoded == data
```