```python
import pytest
from jose import jwt, jwe, jws, jwk, utils, constants, exceptions
from jose import JWTError


def test_jwt_encode_decode_roundtrip():
    """jwt.encode then jwt.decode returns the original claims."""
    claims = {"sub": "user1", "name": "Alice"}
    token = jwt.encode(claims, "secret", algorithm="HS256")
    assert jwt.decode(token, "secret", algorithms=["HS256"]) == claims


def test_jwt_decode_wrong_key_raises_jwt_error():
    """jwt.decode with a wrong key raises JWTError."""
    token = jwt.encode({"sub": "u"}, "key1", algorithm="HS256")
    with pytest.raises(JWTError):
        jwt.decode(token, "key2", algorithms=["HS256"])


def test_jwt_get_unverified_header():
    """jwt.get_unverified_header returns the header dict without verification."""
    token = jwt.encode({"a": 1}, "s", algorithm="HS256")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"


def test_jwt_get_unverified_claims():
    """jwt.get_unverified_claims returns claims without signature verification."""
    token = jwt.encode({"x": 42}, "s", algorithm="HS256")
    assert jwt.get_unverified_claims(token) == {"x": 42}


def test_jwe_encrypt_decrypt_roundtrip():
    """jwe.encrypt then jwe.decrypt returns the original plaintext."""
    key = "0" * 64  # 256-bit key for A256GCM
    plaintext = b"hello world"
    jwe_str = jwe.encrypt(plaintext, key, algorithm="dir", encryption="A256GCM")
    assert jwe.decrypt(jwe_str, key) == plaintext


def test_jws_sign_verify_roundtrip():
    """jws.sign then jws.verify returns the original payload."""
    payload = b"some payload"
    token = jws.sign(payload, "secret", algorithm="HS256")
    assert jws.verify(token, "secret", ["HS256"]) == payload


def test_jws_verify_wrong_key_raises():
    """jws.verify with a wrong key raises JWSSignatureError."""
    token = jws.sign(b"data", "key1", algorithm="HS256")
    with pytest.raises(exceptions.JWSSignatureError):
        jws.verify(token, "key2", ["HS256"])


def test_base64url_encode_decode_roundtrip():
    """utils.base64url_encode then base64url_decode returns original bytes."""
    data = b"test data \x00\x01\x02"
    encoded = utils.base64url_encode(data)
    assert utils.base64url_decode(encoded) == data


def test_long_to_base64_and_back():
    """utils.long_to_base64 then base64_to_long returns the original integer."""
    n = 12345678901234567890
    b64 = utils.long_to_base64(n)
    assert utils.base64_to_long(b64) == n


def test_jwk_construct_hmac_key():
    """jwk.construct creates a key object that can sign and verify."""
    key = jwk.construct("mysecret", "HS256")
    token = jws.sign(b"payload", key, algorithm="HS256")
    assert jws.verify(token, key, ["HS256"]) == b"payload"
```