```python
import pytest
from starlette.responses import Response, JSONResponse, PlainTextResponse
from starlette.datastructures import URL, QueryParams, Headers
from starlette.requests import cookie_parser
from starlette.routing import compile_path, replace_params
from starlette.convertors import IntegerConvertor, StringConvertor
from starlette.exceptions import HTTPException
from starlette.authentication import SimpleUser, UnauthenticatedUser, AuthCredentials


def test_response_status_and_body():
    """Response stores status_code and renders str content to utf-8 bytes."""
    r = Response(content="hello", status_code=201)
    assert r.status_code == 201
    assert r.body == b"hello"


def test_response_default_status_and_empty_body():
    """A Response with no content defaults to status 200 and empty body."""
    r = Response()
    assert r.status_code == 200
    assert r.body == b""


def test_json_response_renders_json():
    """JSONResponse renders a dict to a JSON byte string."""
    r = JSONResponse({"a": 1, "b": [2, 3]})
    assert r.body == b'{"a":1,"b":[2,3]}'


def test_plain_text_response_media_type():
    """PlainTextResponse sets the text/plain media type."""
    r = PlainTextResponse("hi")
    assert r.media_type == "text/plain"
    assert r.body == b"hi"


def test_url_parse_components():
    """URL parses scheme, host, port, path, query and fragment."""
    u = URL("https://example.com:8080/path?x=1&y=2#frag")
    assert u.scheme == "https"
    assert u.host == "example.com"
    assert u.port == 8080
    assert u.path == "/path"
    assert u.query == b"x=1&y=2"
    assert u.fragment == "frag"


def test_query_params_first_value():
    """QueryParams.get returns the first value for a repeated key."""
    qp = QueryParams("a=1&a=2&b=3")
    assert qp.get("a") == "1"
    assert qp.get("b") == "3"
    assert qp.get("missing") is None


def test_headers_case_insensitive_lookup():
    """Headers lookup is case-insensitive on the key."""
    h = Headers(raw=[(b"Content-Type", b"application/json")])
    assert h["content-type"] == "application/json"
    assert h["CONTENT-TYPE"] == "application/json"


def test_cookie_parser_parses_pairs():
    """cookie_parser splits a Cookie header into a dict of pairs."""
    assert cookie_parser("a=1; b=2") == {"a": "1", "b": "2"}


def test_compile_path_integer_convertor():
    """compile_path builds a regex and convertor map for typed params."""
    pattern, path_format, convertors = compile_path("/items/{item_id:int}")
    assert convertors["item_id"] == IntegerConvertor()
    assert pattern.match("/items/42").group("item_id") == "42"


def test_replace_params_substitutes_values():
    """replace_params substitutes path params into the path string."""
    path, params = replace_params(
        "/items/{item_id:int}",
        {"item_id": IntegerConvertor()},
        {"item_id": "42"},
    )
    assert path == "/items/42"
    assert params == {"item_id": "42"}


def test_http_exception_attributes():
    """HTTPException carries status_code and detail."""
    e = HTTPException(status_code=404, detail="Not Found")
    assert e.status_code == 404
    assert e.detail == "Not Found"


def test_simple_user_authenticated():
    """SimpleUser is authenticated; UnauthenticatedUser is not."""
    creds = AuthCredentials(scopes=["read"])
    su = SimpleUser(creds, "alice")
    assert su.is_authenticated is True
    assert su.display_name == "alice"
    assert su.auth_scopes == ["read"]
    uu = UnauthenticatedUser(creds)
    assert uu.is_authenticated is False
    assert uu.display_name is None
```