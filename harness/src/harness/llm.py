"""Model client: OpenAI-compatible chat completions, which is what vLLM on OpenShift AI serves and
what the capability map's classification runtime (OGX Responses API) is compatible with.

Every call is recorded: endpoint, model id, prompt digest, response digest, token usage, latency.
That record goes into the test manifest so a run can be replayed and a prompt change can be traced.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .util import HarnessError, sha256_text, write_json

from . import config as _config


@dataclass
class ModelConfig:
    base_url: str
    model: str
    api_key: str | None
    temperature: float | None = 0.2         # None: the server's own sampling defaults apply (set temperature = "default")
    max_tokens: int = 6000                  # per call; reasoning tokens count against it on vLLM, so thinking runs raise it
    timeout_s: int = 1800
    _label: str = "local"
    no_think: bool = False    # Qwen3 soft switch in the prompt; ignored by LM Studio for qwen3.8
    reasoning_effort: str | None = "none"   # the parameter LM Studio honors; unset with HARNESS_MODEL_REASONING=default
    frequency_penalty: float = 0.3          # discourages the repetition loops a 27B falls into on long literals
    presence_penalty: float = 0.0           # Qwen's own advice against repetition inside thinking; sent only when set
    top_p: float | None = None              # sent only when set; a served model's own generation_config is the usual source
    top_k: int | None = None
    repetition_penalty: float | None = None
    chat_template_kwargs: dict | None = None  # vLLM: {"enable_thinking": false}; LM Studio ignores it

    EFFORTS = ("low", "medium", "high", "xhigh")   # what a vLLM thinking run accepts; "none" is LM Studio's off switch

    @property
    def thinking(self) -> bool:
        return bool(self.chat_template_kwargs and self.chat_template_kwargs.get("enable_thinking"))

    def cap(self, max_tokens: int | None) -> int:
        """Token cap for one call: the caller's cap, times four when the model reasons in-band."""
        base = max_tokens or self.max_tokens
        return base * 4 if self.thinking else base

    @property
    def label(self) -> str:
        return self._label

    @property
    def endpoint_digest(self) -> str:
        return _config.endpoint_digest(self.base_url)

    @classmethod
    def from_env(cls) -> "ModelConfig":
        """Environment variables first, then harness.local.toml, then the example defaults."""
        base = _config.get("model", "base_url", "HARNESS_MODEL_BASE_URL")
        if not base:
            raise HarnessError("no model endpoint configured: set HARNESS_MODEL_BASE_URL or [model].base_url in harness/harness.local.toml")
        base = base.rstrip("/")
        key_env = _config.get("model", "api_key_env", None, "") or "HARNESS_MODEL_API_KEY"
        api_key = os.environ.get(key_env) or os.environ.get("HARNESS_MODEL_API_KEY")
        model = _config.get("model", "name", "HARNESS_MODEL") or discover_model(base, api_key)
        reasoning = str(_config.get("model", "reasoning", "HARNESS_MODEL_REASONING", "none"))
        thinking = str(_config.get("model", "thinking", "HARNESS_MODEL_THINKING", "off"))
        temperature = _config.get("model", "temperature", "HARNESS_MODEL_TEMPERATURE", 0.2)
        cfg = cls(base_url=base, model=model, api_key=api_key,
                  max_tokens=int(_config.get("model", "max_tokens", "HARNESS_MODEL_MAX_TOKENS", 6000)),
                  temperature=None if str(temperature) == "default" else float(temperature),
                  timeout_s=int(_config.get("model", "timeout", "HARNESS_MODEL_TIMEOUT", 1800)),
                  presence_penalty=float(_config.get("model", "presence_penalty", "HARNESS_MODEL_PRESENCE_PENALTY", 0.0)),
                  frequency_penalty=float(_config.get("model", "frequency_penalty", "HARNESS_MODEL_FREQUENCY_PENALTY", 0.3)),
                  top_p=_opt(_config.get("model", "top_p", "HARNESS_MODEL_TOP_P", None), float),
                  top_k=_opt(_config.get("model", "top_k", "HARNESS_MODEL_TOP_K", None), int),
                  repetition_penalty=_opt(_config.get("model", "repetition_penalty", "HARNESS_MODEL_REPETITION_PENALTY", None), float),
                  no_think=os.environ.get("HARNESS_MODEL_NO_THINK", "0") == "1",
                  reasoning_effort=None if reasoning == "default" else reasoning,
                  chat_template_kwargs=None if thinking == "default" else {"enable_thinking": thinking == "on"})
        cfg._label = str(_config.get("model", "label", "HARNESS_MODEL_LABEL", "local"))
        return cfg


def _opt(value, cast):
    """A knob that is sent only when set: absent, empty or "default" means the server decides."""
    return None if value in (None, "", "default") else cast(value)


def _headers(api_key: str | None) -> dict:
    h = {"Content-Type": "application/json", "User-Agent": "ai-test-harness/0.1"}
    if api_key:
        h["Authorization"] = f"Bearer {api_key}"
    return h


def discover_model(base_url: str, api_key: str | None) -> str:
    req = urllib.request.Request(f"{base_url}/models", headers=_headers(api_key))
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        raise HarnessError(f"model endpoint {base_url} not reachable: {e}") from e
    ids = [m["id"] for m in data.get("data", [])]
    if not ids:
        raise HarnessError(f"model endpoint {base_url} lists no models")
    return ids[0]


def _safe(tag: str) -> str:
    """A call tag becomes a file name; a Go module path carries slashes."""
    return tag.replace("/", "_")


class Model:
    def __init__(self, cfg: ModelConfig, record_dir: Path):
        self.cfg, self.record_dir, self.calls = cfg, record_dir, 0
        self.thinking_unsupported = False
        record_dir.mkdir(parents=True, exist_ok=True)

    def chat(self, system: str, user: str, tag: str, max_tokens: int | None = None) -> tuple[str, dict]:
        if self.cfg.no_think:
            system = "/no_think\n" + system
        body = {"model": self.cfg.model, "max_tokens": self.cfg.max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if self.cfg.chat_template_kwargs:
            body["chat_template_kwargs"] = self.cfg.chat_template_kwargs
        self._reasoning_fields(body)
        self._sampling(body)
        body["stream"] = True
        body["stream_options"] = {"include_usage": True}
        body["max_tokens"] = self.cfg.cap(max_tokens)
        req = urllib.request.Request(f"{self.cfg.base_url}/chat/completions", data=json.dumps(body).encode(),
                                     headers=_headers(self.cfg.api_key))
        t0 = time.time()
        text, usage, finish, model_id = "", {}, None, self.cfg.model
        try:
            with urllib.request.urlopen(req, timeout=self.cfg.timeout_s) as r:
                for line in r:
                    line = line.decode().strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    chunk = json.loads(payload)
                    model_id = chunk.get("model", model_id)
                    if chunk.get("usage"):
                        usage = chunk["usage"]
                    for ch in chunk.get("choices", []):
                        text += (ch.get("delta") or {}).get("content") or ""
                        finish = ch.get("finish_reason") or finish
                    if len(text) > 1500 and _looping(text):
                        finish = "loop_detected"
                        break
        except Exception as e:
            body_text = ""
            if hasattr(e, "read"):
                try:
                    body_text = e.read().decode(errors="replace")[:600]
                except Exception:
                    body_text = ""
            raise HarnessError(f"model call failed ({tag}): {e} {body_text}".strip()) from e
        text, stripped = strip_think(text)
        thinking_fallback = False
        if self.cfg.thinking and (reasoning_leak(text) or finish == "loop_detected") and not getattr(self, "_in_fallback", False):
            # GF-019: the serving layer is not separating reasoning from the answer. Retry once with
            # thinking off and say so in the record; the endpoint is reported as not supporting thinking.
            self._in_fallback = True
            try:
                saved = self.cfg.chat_template_kwargs
                self.cfg.chat_template_kwargs = {"enable_thinking": False}
                text2, rec2 = self.chat(system, user, tag + "-nothink", max_tokens)
            finally:
                self.cfg.chat_template_kwargs = saved
                self._in_fallback = False
            rec2["thinking_fallback"] = {"from_call": self.calls + 1, "reason": "reasoning leaked into content" if reasoning_leak(text) else finish}
            self.thinking_unsupported = True
            write_json(self.record_dir / f"{rec2['call']:03d}-{tag}-nothink.json", rec2)
            self.calls += 1
            write_json(self.record_dir / f"{self.calls:03d}-{_safe(tag)}.json", {"tag": tag, "call": self.calls, "finish_reason": finish,
                       "reasoning_leak": reasoning_leak(text), "response_chars": len(text), "superseded_by": rec2["call"]})
            (self.record_dir / f"{self.calls:03d}-{_safe(tag)}.response.md").write_text(text)
            return text2, rec2
        self.calls += 1
        record = {"tag": tag, "call": self.calls, "endpoint": self.cfg.label, "endpoint_digest": self.cfg.endpoint_digest, "model": model_id,
                  "temperature": self.cfg.temperature, "reasoning_effort": self.cfg.reasoning_effort,
                  "frequency_penalty": self.cfg.frequency_penalty, "presence_penalty": self.cfg.presence_penalty, "max_tokens": self.cfg.cap(max_tokens),
                  "chat_template_kwargs": self.cfg.chat_template_kwargs, "thinking": self.cfg.thinking,
                  "prompt_sha256": sha256_text(system + "\n---\n" + user),
                  "response_sha256": sha256_text(text), "usage": usage, "response_chars": len(text), "think_chars_stripped": stripped,
                  "latency_s": round(time.time() - t0, 1), "finish_reason": finish}
        (self.record_dir / f"{self.calls:03d}-{_safe(tag)}.prompt.md").write_text(f"# system\n\n{system}\n\n# user\n\n{user}\n")
        (self.record_dir / f"{self.calls:03d}-{_safe(tag)}.response.md").write_text(text)
        write_json(self.record_dir / f"{self.calls:03d}-{_safe(tag)}.json", record)
        return text, record


    def _reasoning_fields(self, body: dict) -> None:
        """reasoning_effort is LM Studio's off switch ("none") and vLLM's depth knob (low, medium, high,
        xhigh) at once. With thinking requested through the chat template only a depth is sent; "none"
        would be rejected outright, and the template already governs. A presence penalty goes out only
        when configured: it is the lever for repetition inside a thinking block."""
        eff = self.cfg.reasoning_effort
        if eff and (not self.cfg.thinking or eff in self.cfg.EFFORTS):
            body["reasoning_effort"] = eff

    def _sampling(self, body: dict) -> None:
        """The sampling fields, or none of them when temperature is "default": then the server's own
        settings for the model apply (a Thinking-only model ships its recommended sampling with it)."""
        if self.cfg.temperature is None:
            return
        body["temperature"] = self.cfg.temperature
        if self.cfg.frequency_penalty:
            body["frequency_penalty"] = self.cfg.frequency_penalty
        if self.cfg.presence_penalty:
            body["presence_penalty"] = self.cfg.presence_penalty
        for key in ("top_p", "top_k", "repetition_penalty"):
            if getattr(self.cfg, key) is not None:
                body[key] = getattr(self.cfg, key)

    def chat_tools(self, messages: list[dict], tools: list[dict], tag: str, max_tokens: int = 1500) -> tuple[dict, dict]:
        """One agent turn: full message history plus tool schemas, non-streaming. Returns the assistant
        message (content and/or tool_calls) and the call record."""
        # Streamed, like chat(): a proxy in front of the model (an OpenShift route) closes idle
        # connections after ~30 s, and a non-streamed agent turn is silent for longer than that.
        body = {"model": self.cfg.model, "max_tokens": self.cfg.cap(max_tokens),
                "messages": messages, "tools": tools, "tool_choice": "auto", "stream": True, "stream_options": {"include_usage": True}}
        self._sampling(body)
        self._reasoning_fields(body)
        if self.cfg.chat_template_kwargs:
            body["chat_template_kwargs"] = self.cfg.chat_template_kwargs
        req = urllib.request.Request(f"{self.cfg.base_url}/chat/completions", data=json.dumps(body).encode(),
                                     headers=_headers(self.cfg.api_key))
        t0 = time.time()
        content, calls_acc, usage, finish, model_id = "", {}, {}, None, self.cfg.model
        try:
            with urllib.request.urlopen(req, timeout=self.cfg.timeout_s) as r:
                for line in r:
                    line = line.decode().strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    chunk = json.loads(payload)
                    model_id = chunk.get("model", model_id)
                    if chunk.get("usage"):
                        usage = chunk["usage"]
                    for ch in chunk.get("choices", []):
                        delta = ch.get("delta") or {}
                        content += delta.get("content") or ""
                        for tc in delta.get("tool_calls") or []:
                            idx = tc.get("index", 0)
                            acc = calls_acc.setdefault(idx, {"id": tc.get("id") or f"call-{idx}", "type": "function",
                                                             "function": {"name": "", "arguments": ""}})
                            if tc.get("id"):
                                acc["id"] = tc["id"]
                            fn = tc.get("function") or {}
                            if fn.get("name"):
                                acc["function"]["name"] += fn["name"]
                            acc["function"]["arguments"] += fn.get("arguments") or ""
                        finish = ch.get("finish_reason") or finish
        except Exception as e:
            body = ""
            if hasattr(e, "read"):
                try:
                    body = e.read().decode(errors="replace")[:600]
                except Exception:
                    body = ""
            raise HarnessError(f"model call failed ({tag}): {e} {body}".strip()) from e
        content, stripped = strip_think(content)
        msg = {"role": "assistant", "content": content}
        if calls_acc:
            msg["tool_calls"] = [calls_acc[i] for i in sorted(calls_acc)]
        choice = {"finish_reason": finish}
        self.calls += 1
        record = {"tag": tag, "call": self.calls, "endpoint": self.cfg.label, "endpoint_digest": self.cfg.endpoint_digest, "model": model_id,
                  "temperature": self.cfg.temperature, "reasoning_effort": self.cfg.reasoning_effort,
                  "messages_sha256": sha256_text(json.dumps(messages, sort_keys=True)), "usage": usage,
                  "latency_s": round(time.time() - t0, 1), "finish_reason": choice.get("finish_reason"), "think_chars_stripped": stripped,
                  "tool_calls": [{"name": c["function"]["name"], "arguments": c["function"]["arguments"][:500]} for c in (msg.get("tool_calls") or [])]}
        (self.record_dir / f"{self.calls:03d}-{_safe(tag)}.messages.json").write_text(json.dumps(messages, indent=1))
        (self.record_dir / f"{self.calls:03d}-{_safe(tag)}.response.json").write_text(json.dumps(msg, indent=1))
        write_json(self.record_dir / f"{self.calls:03d}-{_safe(tag)}.json", record)
        return msg, record


def strip_think(text: str) -> tuple[str, int]:
    """Remove in-band reasoning a serving layer failed to separate: <think>...</think> blocks, and an
    unterminated <think> that runs to the end. Returns the answer and the characters removed."""
    import re
    before = len(text)
    text = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.S)
    text = re.sub(r"<think>.*$", "", text, flags=re.S)
    # Qwen's template opens the block in the prompt, so a served response can carry reasoning with
    # only the closing tag: everything up to the first </think> is reasoning.
    if "</think>" in text and "<think>" not in text:
        text = re.sub(r"^.*?</think>\s*", "", text, count=1, flags=re.S)
    return text, before - len(text)


def reasoning_leak(text: str) -> bool:
    """GF-019. True when a response is reasoning prose rather than an answer: long, no code fence,
    and opening the way chain-of-thought does."""
    if not text or "```" in text:
        return False
    head = text.lstrip()[:200].lower()
    return len(text) > 600 and any(head.startswith(p) for p in ("we need", "we must", "the user", "let me", "let's", "first,", "okay", "i need"))


def _looping(text: str, window: int = 120, repeats: int = 4) -> bool:
    """True when the last `window` characters already occur `repeats` times in the last 3000."""
    tail, recent = text[-window:], text[-3000:]
    return recent.count(tail) >= repeats


def extract_python(text: str) -> str | None:
    """The single python code block from a response, or the whole text if it parses."""
    import re
    m = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    if m:
        return max(m, key=len)
    return text if text.strip().startswith(("import", "from", "#", '"""')) else None
