```python
import pytest
from jose import jwt, JWTError
from jose.constants import Algorithms
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
import time

def test_jwt_encode_returns_string_with_hs256():
    """Asserts that jwt.encode returns a JWT string with HS256 algorithm."""
    payload = {"sub": "1234567890", "name": "John Doe"}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

def test_jwt_decode_valid_token_returns_claims():
    """Asserts that jwt.decode returns the claims set for a valid token."""
    payload = {"sub": "1234567890"}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    claims = jwt.decode(token, secret, algorithms=[Algorithms.HS256])
    assert claims == payload

def test_jwt_decode_with_invalid_signature_raises_JWTError():
    """Asserts that jwt.decode raises JWTError when signature is invalid."""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.invalid"
    with pytest.raises(JWTError):
        jwt.decode(token, "secret", algorithms=[Algorithms.HS256])

def test_jwt_decode_with_expired_token_raises_ExpiredSignatureError():
    """Asserts that jwt.decode raises ExpiredSignatureError when exp is in the past."""
    payload = {"exp": int(time.time()) - 100}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, secret, algorithms=[Algorithms.HS256])

def test_jwt_get_unverified_header_returns_headers_dict():
    """Asserts that get_unverified_header returns the header part of the token."""
    payload = {"sub": "1234567890"}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert isinstance(header, dict)
    assert header["alg"] == Algorithms.HS256
    assert header["typ"] == "JWT"

def test_jwt_get_unverified_claims_returns_payload_without_verification():
    """Asserts that get_unverified_claims returns the payload without verification."""
    payload = {"sub": "1234567890", "admin": True}
    secret = "secret"
    token = jwt.encode(payload, secret, algorithm=Algorithms.HS256)
    claims = jwt.get_unverified_claims(token)
    assert claims == payload

def test_jwt_encode_with_rsa_key_uses_RS256_by_default():
    """Asserts that jwt.encode with RSA key defaults to RS256 algorithm."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    payload = {"sub": "1234567890"}
    token = jwt.encode(payload, private_key, algorithm=Algorithms.RS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == Algorithms.RS256

def test_jwt_decode_with_rsa_key_verifies_signature():
    """Asserts that jwt.decode verifies signature using RSA public key."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    payload = {"sub": "1234567890"}
    token = jwt.encode(payload, private_key, algorithm=Algorithms.RS256)
    claims = jwt.decode(token, public_key, algorithms=[Algorithms.RS256])
    assert claims == payload

def test_jwt_encode_with_none_algorithm():
    """Asserts that jwt.encode with 'none' algorithm produces an unsigned token."""
    payload = {"sub": "1234567890"}
    token = jwt.encode(payload, key=None, algorithm=Algorithms.NONE)
    parts = token.split(".")
    assert len(parts) == 3
    assert parts[2] == ""  # Signature is empty

def test_jwt_decode_with_none_algorithm_accepts_unsigned_token():
    """Asserts that jwt.decode accepts unsigned token when 'none' is allowed."""
    payload = {"sub": "1234567890"}
    token = jwt.encode(payload, key=None, algorithm=Algorithms.NONE)
    claims = jwt.decode(token, key=None, algorithms=[Algorithms.NONE])
    assert claims == payload
```