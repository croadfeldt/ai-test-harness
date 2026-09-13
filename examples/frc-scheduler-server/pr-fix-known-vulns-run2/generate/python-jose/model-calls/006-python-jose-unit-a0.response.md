```python
import pytest
from jose import jwt, jwe, jws, jwk, utils
from jose.constants import Algorithms
from jose.exceptions import (
    JWTError,
    ExpiredSignatureError,
    JWSSignatureError,
    JWKError,
)
from cryptography.hazmat.primitives.asymmetric import rsa as _rsa


def _rsa_key():
    return _rsa.generate_private_key(public_exponent=65537, key_size=2048)


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    key = "secret"
    claims = {"sub": "1234567890", "name": "Alice", "iat": 1700000000}
    token = jwt.encode(claims, key, algorithm=Algorithms.HS256)
    assert jwt.decode(token, key, algorithms=[Algorithms.HS256]) == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "x"}, "right", algorithm=Algorithms.HS256)
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong", algorithms=[Algorithms.HS256])


def test_jwt_decode_expired_raises_expired_signature_error():
    """jwt.decode of an expired token raises ExpiredSignatureError."""
    token = jwt.encode({"exp": 1}, "k", algorithm=Algorithms.HS256)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, "k", algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the alg header."""
    token = jwt.encode({"a": 1}, "k", algorithm=Algorithms.HS256)
    assert jwt.get_unverified_header(token)["alg"] == "HS256"


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    key = _rsa_key()
    ct = jwe.encrypt(b"hello world", key, algorithm=Algorithms.RSA_OAEP_256)
    assert jwe.decrypt(ct, key) == b"hello world"


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    key = _rsa_key()
    token = jws.sign(b"payload", key, algorithm=Algorithms.RS256)
    assert jws.verify(token, key, [Algorithms.RS256]) == b"payload"


def test_jws_verify_wrong_key_raises_signature_error():
    """jws.verify with a different key raises JWSSignatureError."""
    token = jws.sign(b"p", _rsa_key(), algorithm=Algorithms.RS256)
    with pytest.raises(JWSSignatureError):
        jws.verify(token, _rsa_key(), [Algorithms.RS256])


def test_jwk_construct_and_get_key():
    """jwk.construct builds a key and jwk.get_key returns its class."""
    key = _rsa_key()
    obj = jwk.construct(key, algorithm=Algorithms.RS256)
    assert jwk.get_key(Algorithms.RS256) is type(obj)


def test_jwk_construct_unknown_algorithm_raises_jwk_error():
    """jwk.construct with an unregistered algorithm raises JWKError."""
    with pytest.raises(JWKError):
        jwk.construct(b"not-a-key", algorithm="NOTREAL")


def test_utils_base64url_roundtrip():
    """utils.base64url_encode then base64url_decode is the identity."""
    data = b"hello \x00 world"
    assert utils.base64url_decode(utils.base64url_encode(data)) == data
```