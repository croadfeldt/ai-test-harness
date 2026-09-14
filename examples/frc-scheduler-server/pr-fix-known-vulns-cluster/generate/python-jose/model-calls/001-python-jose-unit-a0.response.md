```python
import pytest
from jose import jwt, jwe, jws, jwk, exceptions, utils
from jose.constants import Algorithms


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    token = jwt.encode({"sub": "user1", "role": "admin"}, "secret", algorithm="HS256")
    claims = jwt.decode(token, "secret", algorithms=["HS256"])
    assert claims == {"sub": "user1", "role": "admin"}


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "u"}, "key1", algorithm="HS256")
    with pytest.raises(exceptions.JWTError):
        jwt.decode(token, "key2", algorithms=["HS256"])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the header dict without verification."""
    token = jwt.encode({"a": 1}, "k", algorithm="HS256")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_decode_expired_raises_expired_signature_error():
    """jwt.decode raises ExpiredSignatureError when exp is in the past."""
    token = jwt.encode({"exp": 1000}, "k", algorithm="HS256")
    with pytest.raises(exceptions.ExpiredSignatureError):
        jwt.decode(token, "k", algorithms=["HS256"])


def test_jwt_decode_audience_mismatch_raises_jwt_error():
    """jwt.decode raises JWTError when audience does not match."""
    token = jwt.encode({"aud": "app1"}, "k", algorithm="HS256")
    with pytest.raises(exceptions.JWTError):
        jwt.decode(token, "k", algorithms=["HS256"], audience="app2")


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    payload = b"hello world"
    token = jws.sign(payload, "secret", algorithm="HS256")
    result = jws.verify(token, "secret", ["HS256"])
    assert result == payload


def test_jws_verify_wrong_key_raises_jws_signature_error():
    """jws.verify with wrong key raises JWSSignatureError."""
    token = jws.sign(b"data", "key1", algorithm="HS256")
    with pytest.raises(exceptions.JWSSignatureError):
        jws.verify(token, "key2", ["HS256"])


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    plaintext = b"secret message"
    key = b"0" * 32
    jwe_str = jwe.encrypt(plaintext, key, algorithm="dir", encryption="A256GCM")
    result = jwe.decrypt(jwe_str, key)
    assert result == plaintext


def test_jwe_decrypt_wrong_key_raises_jwe_error():
    """jwe.decrypt with wrong key raises JWEError."""
    key1 = b"0" * 32
    key2 = b"1" * 32
    jwe_str = jwe.encrypt(b"data", key1, algorithm="dir", encryption="A256GCM")
    with pytest.raises(exceptions.JWEError):
        jwe.decrypt(jwe_str, key2)


def test_base64url_encode_decode_roundtrip():
    """utils.base64url_encode then base64url_decode returns original bytes."""
    data = b"test data \x00\x01\x02"
    encoded = utils.base64url_encode(data)
    decoded = utils.base64url_decode(encoded)
    assert decoded == data
```