```python
import pytest
from jose import jwt, jwe, jws, jwk, JWTError, ExpiredSignatureError
from jose.exceptions import JWSSignatureError
from jose.constants import Algorithms
from jose.utils import base64url_encode, base64url_decode, ensure_binary


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    key = b"secret-key-for-testing"
    claims = {"sub": "user123", "name": "Alice"}
    token = jwt.encode(claims, key, algorithm=Algorithms.HS256)
    decoded = jwt.decode(token, key, algorithms=[Algorithms.HS256])
    assert decoded["sub"] == "user123"
    assert decoded["name"] == "Alice"


def test_jwt_decode_wrong_key_raises():
    """jwt.decode with a wrong key raises JWSSignatureError."""
    token = jwt.encode({"sub": "u"}, b"correct-key", algorithm=Algorithms.HS256)
    with pytest.raises(JWSSignatureError):
        jwt.decode(token, b"wrong-key", algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the alg and typ fields."""
    token = jwt.encode({"sub": "x"}, b"k", algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims():
    """jwt.get_unverified_claims returns claims without signature verification."""
    token = jwt.encode({"sub": "abc", "custom": 42}, b"k", algorithm=Algorithms.HS256)
    claims = jwt.get_unverified_claims(token)
    assert claims["sub"] == "abc"
    assert claims["custom"] == 42


def test_jwt_expired_token_raises():
    """jwt.decode raises ExpiredSignatureError for an expired token."""
    import time
    key = b"exp-key"
    claims = {"sub": "u", "exp": int(time.time()) - 100}
    token = jwt.encode(claims, key, algorithm=Algorithms.HS256)
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, key, algorithms=[Algorithms.HS256])


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns True for a valid signature."""
    key = b"jws-secret"
    payload = b"hello world"
    token = jws.sign(payload, key, algorithm=Algorithms.HS256)
    assert jws.verify(token, key, [Algorithms.HS256]) is True


def test_jws_verify_invalid_signature():
    """jws.verify raises JWSSignatureError for a tampered token."""
    key = b"jws-secret"
    token = jws.sign(b"data", key, algorithm=Algorithms.HS256)
    # Tamper with the signature part
    parts = token.split(b".")
    parts[2] = b"invalidsig"
    tampered = b".".join(parts)
    with pytest.raises(JWSSignatureError):
        jws.verify(tampered, key, [Algorithms.HS256])


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    key = b"A" * 32  # 256-bit key for A256GCM
    plaintext = b"secret message"
    jwe_str = jwe.encrypt(plaintext, key, algorithm=Algorithms.DIR, encryption=Algorithms.A256GCM)
    decrypted = jwe.decrypt(jwe_str, key)
    assert decrypted == plaintext


def test_base64url_encode_decode_roundtrip():
    """base64url_encode then base64url_decode returns the original bytes."""
    data = b"test data \x00\x01\x02"
    encoded = base64url_encode(data)
    decoded = base64url_decode(encoded)
    assert decoded == data


def test_ensure_binary_coerces_str_to_bytes():
    """ensure_binary converts a str to bytes and leaves bytes unchanged."""
    assert ensure_binary("hello") == b"hello"
    assert ensure_binary(b"world") == b"world"
```