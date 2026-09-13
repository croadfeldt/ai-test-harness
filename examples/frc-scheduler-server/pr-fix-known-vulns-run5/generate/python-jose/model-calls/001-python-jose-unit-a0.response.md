```python
import pytest
from jose import jwt, jwe, jws, jwk, JWTError, ExpiredSignatureError, JWSSignatureError
from jose.constants import Algorithms
from jose.utils import base64url_encode, base64url_decode, ensure_binary, timedelta_total_seconds
import datetime


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    claims = {"sub": "1234567890", "name": "Alice", "iat": 1700000000}
    token = jwt.encode(claims, "secret", algorithm="HS256")
    decoded = jwt.decode(token, "secret", algorithms=["HS256"])
    assert decoded["sub"] == "1234567890"
    assert decoded["name"] == "Alice"


def test_jwt_decode_wrong_key_raises():
    """jwt.decode with wrong key raises JWSSignatureError."""
    token = jwt.encode({"sub": "test"}, "key1", algorithm="HS256")
    with pytest.raises(JWSSignatureError):
        jwt.decode(token, "key2", algorithms=["HS256"])


def test_jwt_decode_expired_raises():
    """jwt.decode with expired token raises ExpiredSignatureError."""
    token = jwt.encode({"sub": "test", "exp": 1000000000}, "secret", algorithm="HS256")
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, "secret", algorithms=["HS256"])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the header dict without verification."""
    token = jwt.encode({"sub": "test"}, "secret", algorithm="HS256")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims():
    """jwt.get_unverified_claims returns claims without signature verification."""
    token = jwt.encode({"sub": "abc", "custom": 42}, "secret", algorithm="HS256")
    claims = jwt.get_unverified_claims(token)
    assert claims["sub"] == "abc"
    assert claims["custom"] == 42


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    plaintext = b"hello world"
    key = b"0" * 32
    jwe_str = jwe.encrypt(plaintext, key, algorithm="dir", encryption="A256GCM")
    decrypted = jwe.decrypt(jwe_str, key)
    assert decrypted == plaintext


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns True for valid signature."""
    payload = b"test payload"
    key = "secret"
    token = jws.sign(payload, key, algorithm="HS256")
    assert jws.verify(token, key, ["HS256"]) is True


def test_jws_verify_wrong_key_raises():
    """jws.verify with wrong key raises JWSSignatureError."""
    token = jws.sign(b"payload", "key1", algorithm="HS256")
    with pytest.raises(JWSSignatureError):
        jws.verify(token, "key2", ["HS256"])


def test_base64url_encode_decode_roundtrip():
    """base64url_encode then base64url_decode returns original bytes."""
    data = b"test data \x00\x01\x02"
    encoded = base64url_encode(data)
    decoded = base64url_decode(encoded)
    assert decoded == data


def test_ensure_binary_and_timedelta():
    """ensure_binary coerces to bytes; timedelta_total_seconds returns float seconds."""
    assert ensure_binary("hello") == b"hello"
    assert ensure_binary(b"hello") == b"hello"
    delta = datetime.timedelta(hours=1, minutes=30)
    assert timedelta_total_seconds(delta) == 5400.0
```