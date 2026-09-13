```python
import pytest
from starlette.datastructures import URL, QueryParams, Headers
from starlette.responses import Response, JSONResponse, PlainTextResponse
from starlette.routing import compile_path, replace_params
from starlette.authentication import SimpleUser, UnauthenticatedUser
from starlette.requests import cookie_parser
from starlette.convertors import IntegerConvertor, StringConvertor
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.applications import Starlette
from starlette.routing import request_response
from starlette.background import BackgroundTask
from starlette.datastructures import State
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse


def test_url_parse_components():
    """URL parses scheme, netloc, path, and query from a full URL string."""
    url = URL("https://example.com:8080/path/to?x=1&y=2")
    assert url.scheme == "https"
    assert url.netloc == "example.com:8080"
    assert url.path == "/path/to"
    assert url.query == b"x=1&y=2"


def test_query_params_get_all():
    """QueryParams.get_all returns all values for a repeated key."""
    qp = QueryParams("a=1&a=2&b=3")
    assert qp.get_all("a") == ["1", "2"]
    assert qp.get_all("b") == ["3"]


def test_headers_case_insensitive_lookup():
    """Headers lookup is case-insensitive."""
    h = Headers(raw=[(b"Content-Type", b"text/html")])
    assert h["content-type"] == "text/html"
    assert h["CONTENT-TYPE"] == "text/html"


def test_compile_path_integer_convertor():
    """compile_path extracts integer convertor for {id:int} pattern."""
    regex, path_format, convertors = compile_path("/items/{item_id:int}")
    assert "item_id" in convertors
    assert isinstance(convertors["item_id"], IntegerConvertor)
    assert convertors["item_id"].regex == r"\d+"


def test_replace_params_substitutes_values():
    """replace_params substitutes path parameters into the path string."""
    _, _, convertors = compile_path("/items/{item_id:int}")
    new_path, new_params = replace_params(
        "/items/{item_id:int}", convertors, {"item_id": "42"}
    )
    assert new_path == "/items/42"
    assert new_params == {"item_id": "42"}


def test_simple_user_authenticated():
    """SimpleUser is authenticated by default; UnauthenticatedUser is not."""
    su = SimpleUser("alice")
    assert su.is_authenticated is True
    assert su.display_name == "alice"
    uu = UnauthenticatedUser()
    assert uu.is_authenticated is False


def test_cookie_parser_basic():
    """cookie_parser parses a simple Cookie header string."""
    result = cookie_parser("session=abc123; theme=dark")
    assert result == {"session": "abc123", "theme": "dark"}


def test_response_status_and_body():
    """Response stores status_code and renders content to bytes."""
    r = Response(content=b"hello", status_code=200)
    assert r.status_code == 200
    assert r.body == b"hello"


def test_json_response_renders_json():
    """JSONResponse renders a dict to a JSON byte string."""
    r = JSONResponse({"key": "value", "num": 42})
    assert r.body == b'{"key":"value","num":42}'
    assert r.media_type == "application/json"


def test_base_http_middleware_dispatch():
    """BaseHTTPMiddleware.dispatch calls the inner app and returns its response."""
    async def inner_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    mw = BaseHTTPMiddleware(inner_app)

    async def fake_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    sent = []

    async def fake_send(msg):
        sent.append(msg)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
    }

    import asyncio
    asyncio.run(mw(scope, fake_receive, fake_send))
    assert sent[0]["status"] == 200
    assert sent[1]["body"] == b"ok"
```