```python
import pytest
from jose import jwt, jws, jwe, jwk, constants, exceptions, utils
from jose.constants import Algorithms


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode with HS256 returns the original claims."""
    key = b"unit-test-secret-key"
    claims = {"sub": "1234567890", "name": "Alice", "iat": 1700000000}
    token = jwt.encode(claims, key, algorithm=Algorithms.HS256)
    assert isinstance(token, str)
    decoded = jwt.decode(token, key, algorithms=[Algorithms.HS256])
    assert decoded == claims


def test_jwt_decode_wrong_key_raises_jwterror():
    """jwt.decode with a different key raises JWTError."""
    token = jwt.encode({"sub": "x"}, b"key-one", algorithm=Algorithms.HS256)
    with pytest.raises(exceptions.JWTError):
        jwt.decode(token, b"key-two", algorithms=[Algorithms.HS256])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the alg and typ without verification."""
    token = jwt.encode({"a": 1}, b"k", algorithm=Algorithms.HS256)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims():
    """jwt.get_unverified_claims returns claims without signature verification."""
    token = jwt.encode({"sub": "abc", "custom": 42}, b"k", algorithm=Algorithms.HS256)
    claims = jwt.get_unverified_claims(token)
    assert claims["sub"] == "abc"
    assert claims["custom"] == 42


def test_jwt_decode_expired_raises_expiredsignatureerror():
    """jwt.decode raises ExpiredSignatureError when exp is in the past."""
    token = jwt.encode({"exp": 1000000000}, b"k", algorithm=Algorithms.HS256)
    with pytest.raises(exceptions.ExpiredSignatureError):
        jwt.decode(token, b"k", algorithms=[Algorithms.HS256])


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns True for a valid signature."""
    key = b"jws-secret"
    token = jws.sign(b"hello world", key, algorithm=Algorithms.HS256)
    assert isinstance(token, str)
    assert jws.verify(token, key, [Algorithms.HS256]) is True


def test_jws_verify_invalid_signature_raises():
    """jws.verify raises JWSSignatureError for a tampered token."""
    key = b"jws-secret"
    token = jws.sign(b"hello world", key, algorithm=Algorithms.HS256)
    # Tamper with the payload segment
    parts = token.split(".")
    parts[1] = "dGFtcGVyZWQ"
    tampered = ".".join(parts)
    with pytest.raises(exceptions.JWSSignatureError):
        jws.verify(tampered, key, [Algorithms.HS256])


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt with A256GCM/DIR returns the original plaintext."""
    key = b"A" * 32  # 256-bit key for A256GCM
    plaintext = b"secret message"
    jwe_str = jwe.encrypt(plaintext, key, encryption=Algorithms.A256GCM, algorithm=Algorithms.DIR)
    assert isinstance(jwe_str, str)
    decrypted = jwe.decrypt(jwe_str, key)
    assert decrypted == plaintext


def test_jwe_get_unverified_header():
    """jwe.get_unverified_header returns alg and enc without decryption."""
    key = b"B" * 32
    jwe_str = jwe.encrypt(b"data", key, encryption=Algorithms.A256GCM, algorithm=Algorithms.DIR)
    header = jwe.get_unverified_header(jwe_str)
    assert header["alg"] == "dir"
    assert header["enc"] == "A256GCM"


def test_utils_base64url_roundtrip():
    """utils.base64url_encode then base64url_decode returns the original bytes."""
    data = b"hello \x00\x01\x02 world"
    encoded = utils.base64url_encode(data)
    assert isinstance(encoded, str)
    assert utils.base64url_decode(encoded) == data
```