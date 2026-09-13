```python
import pytest
from starlette.responses import Response, JSONResponse, PlainTextResponse
from starlette.datastructures import URL, QueryParams, Headers
from starlette.routing import compile_path, replace_params
from starlette.requests import cookie_parser
from starlette.convertors import IntegerConvertor, StringConvertor
from starlette.exceptions import HTTPException
from starlette.authentication import SimpleUser, UnauthenticatedUser, has_required_scope


def test_response_render_bytes():
    """Response.render returns the exact bytes for a bytes content."""
    r = Response(b"hello")
    assert r.render(b"hello") == b"hello"


def test_response_render_str_utf8():
    """Response.render encodes a str content as UTF-8 bytes."""
    r = Response("héllo")
    assert r.render("héllo") == "héllo".encode("utf-8")


def test_json_response_render():
    """JSONResponse.render serializes a dict to a JSON byte string."""
    r = JSONResponse({"a": 1, "b": [2, 3]})
    assert r.render({"a": 1, "b": [2, 3]}) == b'{"a":1,"b":[2,3]}'


def test_plain_text_response_media_type():
    """PlainTextResponse sets the content-type header to text/plain."""
    r = PlainTextResponse("hi")
    assert r.headers["content-type"] == "text/plain; charset=utf-8"


def test_response_set_cookie_header():
    """Response.set_cookie produces a Set-Cookie header with the given key/value."""
    r = Response()
    r.set_cookie("session", "abc123", max_age=60)
    assert r.headers["set-cookie"] == "session=abc123; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=60; path=/; samesite=lax"


def test_url_parse():
    """URL parses a full URL into its component parts."""
    u = URL("https://example.com:8080/path?x=1&y=2#frag")
    assert u.scheme == "https"
    assert u.netloc == "example.com:8080"
    assert u.path == "/path"
    assert u.query == b"x=1&y=2"
    assert u.fragment == "frag"


def test_query_params_get():
    """QueryParams retrieves the first value for a given key."""
    qp = QueryParams("a=1&b=2&a=3")
    assert qp.get("a") == "1"
    assert qp.getlist("a") == ["1", "3"]


def test_headers_case_insensitive():
    """Headers lookup is case-insensitive."""
    h = Headers(raw=[(b"Content-Type", b"application/json")])
    assert h["content-type"] == "application/json"
    assert h["CONTENT-TYPE"] == "application/json"


def test_compile_path_integer():
    """compile_path compiles a path with an integer convertor into a regex."""
    pattern, path_format, convertors = compile_path("/{id:int}")
    assert path_format == "/{id}"
    assert "id" in convertors
    assert isinstance(convertors["id"], IntegerConvertor)
    m = pattern.match("/42")
    assert m is not None
    assert m.group("id") == "42"


def test_cookie_parser():
    """cookie_parser parses a Cookie header string into a dict."""
    result = cookie_parser("a=1; b=2; c=hello")
    assert result == {"a": "1", "b": "2", "c": "hello"}
```