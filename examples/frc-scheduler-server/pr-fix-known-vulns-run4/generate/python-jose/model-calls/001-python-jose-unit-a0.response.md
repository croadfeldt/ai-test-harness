```python
import pytest
from jose import jwt, jwe, jws, jwk, utils
from jose.constants import Algorithms
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

SECRET = b"test-secret-key"


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    claims = {"sub": "user1", "name": "Alice"}
    token = jwt.encode(claims, SECRET, algorithm=Algorithms.HS256)
    decoded = jwt.decode(token, SECRET, algorithms=[Algorithms.HS256])
    assert decoded == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "u"}, SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(JWTError):
        jwt.decode(token, b"wrong-key", algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the alg header without verification."""
    token = jwt.encode({"sub": "u"}, SECRET, algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_expired_claims_raise_expired_signature_error():
    """jwt.decode with an expired token raises ExpiredSignatureError."""
    import time
    claims = {"sub": "u", "exp": int(time.time()) - 100}
    token = jwt.encode(claims, SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, SECRET, algorithms=[Algorithms.HS256])


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    plaintext = b"hello world"
    key = b"0" * 32
    jwe_str = jwe.encrypt(plaintext, key, encryption=Algorithms.A256GCM, algorithm=Algorithms.DIR)
    decrypted = jwe.decrypt(jwe_str, key)
    assert decrypted == plaintext


def test_jwe_decrypt_wrong_key_raises_jwe_invalid_auth():
    """jwe.decrypt with a wrong key raises JWEInvalidAuth."""
    key1 = b"0" * 32
    key2 = b"1" * 32
    jwe_str = jwe.encrypt(b"data", key1, encryption=Algorithms.A256GCM, algorithm=Algorithms.DIR)
    with pytest.raises(JWEInvalidAuth):
        jwe.decrypt(jwe_str, key2)


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    payload = b"some payload"
    token = jws.sign(payload, SECRET, algorithm=Algorithms.HS256)
    verified = jws.verify(token, SECRET, algorithms=[Algorithms.HS256])
    assert verified == payload


def test_jws_verify_wrong_key_raises_jws_signature_error():
    """jws.verify with a wrong key raises JWSSignatureError."""
    token = jws.sign(b"payload", SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(JWSSignatureError):
        jws.verify(token, b"wrong", algorithms=[Algorithms.HS256])


def test_jwk_construct_and_get_key():
    """jwk.construct creates a key object and jwk.get_key returns the registered class."""
    key_obj = jwk.construct(SECRET, algorithm=Algorithms.HS256)
    assert key_obj is not None
    key_class = jwk.get_key(Algorithms.HS256)
    assert key_class is not None


def test_utils_base64url_roundtrip():
    """utils.base64url_encode then base64url_decode returns the original bytes."""
    data = b"test data for base64url"
    encoded = utils.base64url_encode(data)
    decoded = utils.base64url_decode(encoded)
    assert decoded == data
```