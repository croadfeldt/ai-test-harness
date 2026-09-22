```python
import pytest
from jose import jwt, JWTError
from jose.constants import Algorithms
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
import time


def test_jwt_encode_returns_string_with_hs256():
    """Asserts that jwt.encode returns a JWT string when using HS256."""
    payload = {"sub": "1234567890", "name": "John Doe"}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3


def test_jwt_decode_with_valid_token_and_key_returns_claims():
    """Asserts that jwt.decode returns the claims set when token and key are valid."""
    payload = {"sub": "1234567890", "name": "John Doe"}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    decoded = jwt.decode(token, secret, algorithms=[Algorithms.HS256])
    assert decoded == payload


def test_jwt_decode_with_invalid_signature_raises_JWTError():
    """Asserts that jwt.decode raises JWTError when signature is invalid."""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.r9XSYuJyFwQAqkZ0GrXpqsL1rBYqR3WcaVHyKkU7oBA"
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong_secret", algorithms=[Algorithms.HS256])


def test_jwt_decode_with_expired_token_raises_ExpiredSignatureError():
    """Asserts that jwt.decode raises ExpiredSignatureError when exp claim is in the past."""
    payload = {"sub": "1234567890", "exp": int(time.time()) - 100}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, secret, algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header_returns_headers_dict():
    """Asserts that get_unverified_header returns the header part of the token."""
    payload = {"sub": "1234567890"}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256, headers={"kid": "abc123"})
    header = jwt.get_unverified_header(token)
    assert isinstance(header, dict)
    assert header["alg"] == Algorithms.HS256
    assert header["kid"] == "abc123"


def test_jwt_get_unverified_claims_returns_payload_dict():
    """Asserts that get_unverified_claims returns the claims without verification."""
    payload = {"sub": "1234567890", "admin": True}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    claims = jwt.get_unverified_claims(token)
    assert claims == payload


def test_jwt_encode_with_none_algorithm_raises_JWSSignatureError():
    """Asserts that jwt.encode raises JWSSignatureError when algorithm is None."""
    with pytest.raises(jwt.JWSSignatureError):
        jwt.encode({"sub": "123"}, "secret", algorithm=None)


def test_jwt_decode_with_invalid_token_format_raises_JWSError():
    """Asserts that jwt.decode raises JWSError when token has invalid JWS format."""
    with pytest.raises(jwt.JWSError):
        jwt.decode("invalid.token.format", "secret", algorithms=[Algorithms.HS256])


def test_jwt_encode_with_rsa_key_uses_RS256_by_default():
    """Asserts that jwt.encode with RSA key defaults to RS256 algorithm."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    payload = {"sub": "123"}
    token = jwt.encode(payload, private_key, algorithm=Algorithms.RS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == Algorithms.RS256


def test_jwt_decode_with_audience_checks_aud_claim():
    """Asserts that jwt.decode validates the aud claim when audience is provided."""
    payload = {"sub": "123", "aud": "test-audience"}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    jwt.decode(token, secret, algorithms=[Algorithms.HS256], audience="test-audience")
```