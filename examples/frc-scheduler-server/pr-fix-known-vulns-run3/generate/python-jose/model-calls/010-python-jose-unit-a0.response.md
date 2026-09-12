```python
import pytest
import jose
from jose import jwt, jwe, jws, jwk, utils, constants
from jose.exceptions import (
    JOSEError,
    JWSError,
    JWSSignatureError,
    JWSAlgorithmError,
    JWTError,
    JWTClaimsError,
    ExpiredSignatureError,
    JWKError,
    JWEError,
    JWEParseError,
    JWEInvalidAuth,
    JWEAlgorithmUnsupportedError,
)


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    key = b"secret-key-for-testing"
    claims = {"sub": "1234567890", "name": "Test User", "iat": 1516239022}
    token = jwt.encode(claims, key, algorithm="HS256")
    decoded = jwt.decode(token, key, algorithms=["HS256"])
    assert decoded == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    key = b"correct-key"
    wrong_key = b"wrong-key"
    claims = {"sub": "1234567890"}
    token = jwt.encode(claims, key, algorithm="HS256")
    with pytest.raises(JWTError):
        jwt.decode(token, wrong_key, algorithms=["HS256"])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the header dict without verification."""
    key = b"test-key"
    claims = {"sub": "1234567890"}
    token = jwt.encode(claims, key, algorithm="HS256")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims():
    """jwt.get_unverified_claims returns claims without signature verification."""
    key = b"test-key"
    claims = {"sub": "1234567890", "name": "Test"}
    token = jwt.encode(claims, key, algorithm="HS256")
    unverified = jwt.get_unverified_claims(token)
    assert unverified == claims


def test_jwt_expired_token_raises_expired_signature_error():
    """jwt.decode raises ExpiredSignatureError for expired tokens."""
    key = b"test-key"
    claims = {"sub": "1234567890", "exp": 1516239022}  # past timestamp
    token = jwt.encode(claims, key, algorithm="HS256")
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, key, algorithms=["HS256"])


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    key = b"0" * 32  # 256-bit key for A256GCM
    plaintext = b"Hello, JWE!"
    jwe_str = jwe.encrypt(plaintext, key, encryption="A256GCM", algorithm="dir")
    decrypted = jwe.decrypt(jwe_str, key)
    assert decrypted == plaintext


def test_jwe_decrypt_wrong_key_raises_jwe_error():
    """jwe.decrypt with wrong key raises JWEError."""
    key = b"0" * 32
    wrong_key = b"1" * 32
    plaintext = b"secret data"
    jwe_str = jwe.encrypt(plaintext, key, encryption="A256GCM", algorithm="dir")
    with pytest.raises(JWEError):
        jwe.decrypt(jwe_str, wrong_key)


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    key = b"test-key"
    payload = b"some payload data"
    token = jws.sign(payload, key, algorithm="HS256")
    verified = jws.verify(token, key, algorithms=["HS256"])
    assert verified == payload


def test_jws_verify_wrong_key_raises_jwt_error():
    """jws.verify with wrong key raises JWTError."""
    key = b"correct-key"
    wrong_key = b"wrong-key"
    payload = b"some payload"
    token = jws.sign(payload, key, algorithm="HS256")
    with pytest.raises(JWTError):
        jws.verify(token, wrong_key, algorithms=["HS256"])


def test_utils_base64url_roundtrip():
    """utils.base64url_encode then base64url_decode returns original bytes."""
    data = b"Hello, World! This is a test."
    encoded = utils.base64url_encode(data)
    decoded = utils.base64url_decode(encoded)
    assert decoded == data
```