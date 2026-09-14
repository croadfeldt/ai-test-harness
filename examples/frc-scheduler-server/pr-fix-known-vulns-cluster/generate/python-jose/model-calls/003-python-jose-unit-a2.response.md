```python
import datetime

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

import jose
from jose import jwt, jwe, jws, jwk, utils
from jose.constants import Algorithms
from jose.exceptions import (
    ExpiredSignatureError,
    JOSEError,
    JWSError,
    JWTClaimsError,
    JWTError,
)

SECRET = b"unit-test-secret-key-0123456789"


def test_jwt_encode_decode_roundtrip_hmac():
    """jwt.encode then jwt.decode with the same key returns the original claims."""
    claims = {"sub": "user-1", "data": "abc"}
    token = jwt.encode(claims, SECRET, algorithm=Algorithms.HS256)
    assert jwt.decode(token, SECRET, algorithms=[Algorithms.HS256]) == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """Decoding a token with the wrong key raises JWTError."""
    token = jwt.encode({"sub": "x"}, SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(JWTError):
        jwt.decode(token, b"other-secret-key-0123456789", algorithms=[Algorithms.HS256])


def test_jwt_decode_expired_raises_expired_signature_error():
    """A token whose exp is in the past raises ExpiredSignatureError."""
    past = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).timestamp())
    token = jwt.encode({"exp": past}, SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, SECRET, algorithms=[Algorithms.HS256])


def test_jwt_decode_audience_mismatch_raises_jwt_claims_error():
    """A token whose aud does not match the expected audience raises JWTClaimsError."""
    token = jwt.encode({"aud": "app-a"}, SECRET, algorithm=Algorithms.HS256)
    with pytest.raises(JWTClaimsError):
        jwt.decode(token, SECRET, algorithms=[Algorithms.HS256], audience="app-b")


def test_jwt_get_unverified_header_returns_alg_and_typ():
    """get_unverified_header returns the alg and typ of an encoded token."""
    token = jwt.encode({"sub": "u"}, SECRET, algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims_returns_claims_without_verification():
    """get_unverified_claims returns the claims even for an unverified token."""
    token = jwt.encode({"sub": "u", "n": 42}, SECRET, algorithm=Algorithms.HS256)
    assert jwt.get_unverified_claims(token) == {"sub": "u", "n": 42}


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    payload = b"hello jws"
    token = jws.sign(payload, SECRET, algorithm=Algorithms.HS256)
    assert jws.verify(token, SECRET, [Algorithms.HS256]) == payload


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    plaintext = b"secret message"
    token = jwe.encrypt(plaintext, SECRET)
    assert jwe.decrypt(token, SECRET) == plaintext


def test_jwk_construct_rsa_key():
    """jwk.construct builds a key object that exposes the requested algorithm."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    obj = jwk.construct(key, algorithm=Algorithms.RS256)
    assert obj.algorithm == "RS256"


def test_utils_base64url_roundtrip():
    """base64url_encode then base64url_decode returns the original bytes."""
    data = b"round-trip data \x00\x01"
    assert utils.base64url_decode(utils.base64url_encode(data)) == data
```