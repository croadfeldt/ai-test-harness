```python
import pytest
from jose import jwt, JWTError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import time


def test_jwt_encode_with_hmac_returns_valid_jwt():
    """Asserts that encoding with HMAC produces a valid JWT string with three parts."""
    secret = "secret"
    payload = {"sub": "1234567890", "name": "John Doe", "iat": 1234567890}
    token = jwt.encode(payload, secret, algorithm="HS256")
    assert isinstance(token, str)
    parts = token.split(".")
    assert len(parts) == 3


def test_jwt_decode_with_valid_hmac_token_returns_claims():
    """Asserts that decoding a valid HMAC-signed JWT returns the original claims."""
    secret = "secret"
    payload = {"sub": "1234567890", "name": "John Doe", "iat": 1234567890}
    token = jwt.encode(payload, secret, algorithm="HS256")
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    assert decoded == payload


def test_jwt_decode_with_invalid_signature_raises_JWTError():
    """Asserts that decoding a JWT with invalid signature raises JWTError."""
    secret = "secret"
    bad_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxMjM0NTY3ODkwfQ."
        "BADSIG"
    )
    with pytest.raises(JWTError):
        jwt.decode(bad_token, secret, algorithms=["HS256"])


def test_jwt_decode_with_expired_token_raises_ExpiredSignatureError():
    """Asserts that decoding an expired JWT raises ExpiredSignatureError."""
    secret = "secret"
    payload = {"exp": int(time.time()) - 100}
    token = jwt.encode(payload, secret, algorithm="HS256")
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, secret, algorithms=["HS256"])


def test_jwt_get_unverified_header_returns_headers_dict():
    """Asserts that get_unverified_header returns the correct header part."""
    secret = "secret"
    headers = {"kid": "test_kid", "typ": "JWT"}
    payload = {"sub": "1234567890"}
    token = jwt.encode(payload, secret, algorithm="HS256", headers=headers)
    header = jwt.get_unverified_header(token)
    assert isinstance(header, dict)
    assert header["kid"] == "test_kid"
    assert header["alg"] == "HS256"


def test_jwt_get_unverified_claims_returns_payload_without_verification():
    """Asserts that get_unverified_claims returns the payload without signature check."""
    secret = "secret"
    payload = {"sub": "1234567890", "admin": True}
    token = jwt.encode(payload, secret, algorithm="HS256")
    claims = jwt.get_unverified_claims(token)
    assert claims == payload


def test_jwt_decode_with_invalid_algorithm_raises_JWSError():
    """Asserts that using an unsupported algorithm raises JWSError."""
    secret = "secret"
    payload = {"sub": "1234567890"}
    token = jwt.encode(payload, secret, algorithm="HS256")
    with pytest.raises(jwt.JWSError):
        jwt.decode(token, secret, algorithms=["RS256"])


def test_jwt_encode_with_numeric_claims_preserves_types():
    """Asserts that numeric claim values like exp are preserved as integers."""
    secret = "secret"
    payload = {"sub": "1234567890", "exp": 1234567890}
    token = jwt.encode(payload, secret, algorithm="HS256")
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    assert isinstance(decoded["exp"], int)
    assert decoded["exp"] == 1234567890


def test_jwt_decode_with_audience_checks_aud_claim():
    """Asserts that audience validation works when 'aud' is present."""
    secret = "secret"
    payload = {"sub": "1234567890", "aud": "test_audience"}
    token = jwt.encode(payload, secret, algorithm="HS256")
    decoded = jwt.decode(token, secret, algorithms=["HS256"], audience="test_audience")
    assert decoded["aud"] == "test_audience"


def test_jwt_decode_with_mismatched_audience_raises_JWTClaimsError():
    """Asserts that mismatched audience raises JWTClaimsError."""
    secret = "secret"
    payload = {"sub": "1234567890", "aud": "test_audience"}
    token = jwt.encode(payload, secret, algorithm="HS256")
    with pytest.raises(jwt.JWTClaimsError):
        jwt.decode(token, secret, algorithms=["HS256"], audience="wrong_audience")
```