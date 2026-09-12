```python
import pytest
from jose import jwt, jwe, jws, jwk, utils, constants
from jose.exceptions import (
    JWTError,
    ExpiredSignatureError,
    JWSSignatureError,
    JWKError,
)


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode with HS256 returns the original claims."""
    token = jwt.encode({"sub": "u1", "n": 7}, "secret", algorithm="HS256")
    assert jwt.decode(token, "secret", algorithms=["HS256"]) == {"sub": "u1", "n": 7}


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError (the app's catch-all)."""
    token = jwt.encode({"a": 1}, "key1", algorithm="HS256")
    with pytest.raises(JWTError):
        jwt.decode(token, "key2", algorithms=["HS256"])


def test_jwt_decode_expired_raises_expired_signature_error():
    """jwt.decode of an expired token raises ExpiredSignatureError."""
    token = jwt.encode({"exp": 1}, "k", algorithm="HS256")
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, "k", algorithms=["HS256"])


def test_jwt_get_unverified_header_returns_alg():
    """jwt.get_unverified_header returns the alg header without verification."""
    token = jwt.encode({"x": 1}, "k", algorithm="HS256")
    assert jwt.get_unverified_header(token)["alg"] == "HS256"


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt with a 256-bit key returns the plaintext."""
    key = b"0" * 32
    jwe_str = jwe.encrypt(b"hello", key, algorithm="dir", encryption="A256GCM")
    assert jwe.decrypt(jwe_str, key) == b"hello"


def test_jwe_wrong_key_raises_jwk_error():
    """jwe.decrypt with a wrong key raises JWKError."""
    jwe_str = jwe.encrypt(b"hello", b"0" * 32, algorithm="dir", encryption="A256GCM")
    with pytest.raises(JWKError):
        jwe.decrypt(jwe_str, b"1" * 32)


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify with HS256 returns the original payload."""
    token = jws.sign(b"payload", "k", algorithm="HS256")
    assert jws.verify(token, "k", ["HS256"]) == b"payload"


def test_jws_verify_wrong_key_raises_jws_error():
    """jws.verify with a wrong key raises JWSError (signature failure)."""
    token = jws.sign(b"payload", "k1", algorithm="HS256")
    with pytest.raises(JWSSignatureError):
        jws.verify(token, "k2", ["HS256"])


def test_base64url_roundtrip():
    """base64url_encode then base64url_decode returns the original bytes."""
    data = b"abc" * 10
    assert utils.base64url_decode(utils.base64url_encode(data)) == data


def test_long_to_base64_roundtrip():
    """long_to_base64 then base64_to_long returns the original integer."""
    n = 123456789
    assert utils.base64_to_long(utils.long_to_base64(n)) == n
```