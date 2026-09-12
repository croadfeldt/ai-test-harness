```python
import datetime
import pytest
from jose import jwt, jws, jwe, jwk, utils, constants
from jose.exceptions import (
    JWTError,
    JWTClaimsError,
    ExpiredSignatureError,
    JWSError,
    JWSSignatureError,
    JWEError,
    JWKError,
)

SECRET = b"unit-test-secret-key"
ALG = constants.Algorithms.HS256


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    claims = {"sub": "user-1", "data": 42}
    token = jwt.encode(claims, SECRET, algorithm=ALG)
    assert jwt.decode(token, SECRET, algorithms=[ALG]) == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "u"}, SECRET, algorithm=ALG)
    with pytest.raises(JWTError):
        jwt.decode(token, b"other-secret", algorithms=[ALG])


def test_jwt_decode_expired_raises_expired_signature_error():
    """jwt.decode of an expired token raises ExpiredSignatureError."""
    past = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)).timestamp())
    token = jwt.encode({"exp": past}, SECRET, algorithm=ALG)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, SECRET, algorithms=[ALG])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the alg header without verification."""
    token = jwt.encode({"sub": "u"}, SECRET, algorithm=ALG)
    assert jwt.get_unverified_header(token)["alg"] == "HS256"


def test_jwt_get_unverified_claims():
    """jwt.get_unverified_claims returns claims without verification."""
    token = jwt.encode({"sub": "u", "x": 1}, SECRET, algorithm=ALG)
    assert jwt.get_unverified_claims(token) == {"sub": "u", "x": 1}


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    payload = b"hello world"
    token = jws.sign(payload, SECRET, algorithm=ALG)
    assert jws.verify(token, SECRET, algorithms=[ALG]) == payload


def test_jws_verify_wrong_key_raises_jws_error():
    """jws.verify with a wrong key raises JWSError."""
    token = jws.sign(b"payload", SECRET, algorithm=ALG)
    with pytest.raises(JWSError):
        jws.verify(token, b"wrong-key", algorithms=[ALG])


def test_jwk_construct_hmac_key():
    """jwk.construct builds a key object for an HMAC algorithm."""
    key = jwk.construct(SECRET, algorithm=ALG)
    assert key.algorithm == ALG


def test_utils_base64url_roundtrip():
    """base64url_encode then base64url_decode returns the original bytes."""
    data = b"abc123"
    assert utils.base64url_decode(utils.base64url_encode(data)) == data


def test_utils_timedelta_total_seconds():
    """timedelta_total_seconds returns the total seconds of a timedelta."""
    assert utils.timedelta_total_seconds(datetime.timedelta(seconds=90)) == 90
```