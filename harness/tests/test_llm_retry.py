"""GF-025: a transport failure is retried; the model's own refusal is not."""
import io
import json
import urllib.error
from pathlib import Path

import pytest

from harness import llm
from harness.llm import Model, ModelConfig


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def sse(text: str) -> bytes:
    chunk = {"model": "m", "choices": [{"delta": {"content": text}, "finish_reason": "stop"}], "usage": {"completion_tokens": 3}}
    return f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n".encode()


def test_reset_then_success_is_one_call_with_a_retry(tmp_path, monkeypatch):
    attempts = []

    def fake_urlopen(req, timeout=None):
        attempts.append(1)
        if len(attempts) == 1:
            raise ConnectionResetError(104, "Connection reset by peer")
        return FakeResponse(sse("ok"))

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(llm, "RETRY_PAUSE_S", 0)
    m = Model(ModelConfig(base_url="http://x/v1", model="m", api_key=None, retries=2), tmp_path)
    text, rec = m.chat("s", "u", "t")
    assert text == "ok" and len(attempts) == 2 and rec["transport_retries"] == 1


def test_a_refusal_from_the_model_is_final(tmp_path, monkeypatch):
    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 400, "bad request", {}, io.BytesIO(b"unknown field"))

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    m = Model(ModelConfig(base_url="http://x/v1", model="m", api_key=None, retries=2), tmp_path)
    with pytest.raises(llm.HarnessError):
        m.chat("s", "u", "t")
