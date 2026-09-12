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

DEFAULT_BASE_URL = "https://qwen36-27b.llm.ocp.roadfeldt.com/v1"


@dataclass
class ModelConfig:
    base_url: str
    model: str
    api_key: str | None
    temperature: float = 0.2
    max_tokens: int = 6000
    timeout_s: int = 1800
    no_think: bool = False    # Qwen3 soft switch in the prompt; ignored by LM Studio for qwen3.8
    reasoning_effort: str | None = "none"   # the parameter LM Studio honors; unset with HARNESS_MODEL_REASONING=default
    frequency_penalty: float = 0.3          # discourages the repetition loops a 27B falls into on long literals

    @classmethod
    def from_env(cls) -> "ModelConfig":
        base = os.environ.get("HARNESS_MODEL_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        model = os.environ.get("HARNESS_MODEL") or discover_model(base, os.environ.get("HARNESS_MODEL_API_KEY"))
        return cls(base_url=base, model=model, api_key=os.environ.get("HARNESS_MODEL_API_KEY"),
                   temperature=float(os.environ.get("HARNESS_MODEL_TEMPERATURE", "0.2")),
                   no_think=os.environ.get("HARNESS_MODEL_NO_THINK", "0") == "1",
                   reasoning_effort=(None if os.environ.get("HARNESS_MODEL_REASONING", "none") == "default"
                                     else os.environ.get("HARNESS_MODEL_REASONING", "none")))


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


class Model:
    def __init__(self, cfg: ModelConfig, record_dir: Path):
        self.cfg, self.record_dir, self.calls = cfg, record_dir, 0
        record_dir.mkdir(parents=True, exist_ok=True)

    def chat(self, system: str, user: str, tag: str, max_tokens: int | None = None) -> tuple[str, dict]:
        if self.cfg.no_think:
            system = "/no_think\n" + system
        body = {"model": self.cfg.model, "temperature": self.cfg.temperature, "max_tokens": self.cfg.max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "chat_template_kwargs": {"enable_thinking": False}}
        if self.cfg.reasoning_effort:
            body["reasoning_effort"] = self.cfg.reasoning_effort
        body["stream"] = True
        body["stream_options"] = {"include_usage": True}
        body["frequency_penalty"] = self.cfg.frequency_penalty
        if max_tokens:
            body["max_tokens"] = max_tokens
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
            raise HarnessError(f"model call failed ({tag}): {e}") from e
        self.calls += 1
        record = {"tag": tag, "call": self.calls, "endpoint": self.cfg.base_url, "model": model_id,
                  "temperature": self.cfg.temperature, "reasoning_effort": self.cfg.reasoning_effort,
                  "frequency_penalty": self.cfg.frequency_penalty, "max_tokens": max_tokens or self.cfg.max_tokens,
                  "prompt_sha256": sha256_text(system + "\n---\n" + user),
                  "response_sha256": sha256_text(text), "usage": usage, "response_chars": len(text),
                  "latency_s": round(time.time() - t0, 1), "finish_reason": finish}
        (self.record_dir / f"{self.calls:03d}-{tag}.prompt.md").write_text(f"# system\n\n{system}\n\n# user\n\n{user}\n")
        (self.record_dir / f"{self.calls:03d}-{tag}.response.md").write_text(text)
        write_json(self.record_dir / f"{self.calls:03d}-{tag}.json", record)
        return text, record


    def chat_tools(self, messages: list[dict], tools: list[dict], tag: str, max_tokens: int = 1500) -> tuple[dict, dict]:
        """One agent turn: full message history plus tool schemas, non-streaming. Returns the assistant
        message (content and/or tool_calls) and the call record."""
        body = {"model": self.cfg.model, "temperature": self.cfg.temperature, "max_tokens": max_tokens,
                "messages": messages, "tools": tools, "tool_choice": "auto",
                "frequency_penalty": self.cfg.frequency_penalty}
        if self.cfg.reasoning_effort:
            body["reasoning_effort"] = self.cfg.reasoning_effort
        req = urllib.request.Request(f"{self.cfg.base_url}/chat/completions", data=json.dumps(body).encode(),
                                     headers=_headers(self.cfg.api_key))
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.cfg.timeout_s) as r:
                data = json.loads(r.read().decode())
        except Exception as e:
            raise HarnessError(f"model call failed ({tag}): {e}") from e
        choice = data["choices"][0]
        msg = choice["message"]
        self.calls += 1
        record = {"tag": tag, "call": self.calls, "endpoint": self.cfg.base_url, "model": data.get("model", self.cfg.model),
                  "temperature": self.cfg.temperature, "reasoning_effort": self.cfg.reasoning_effort,
                  "messages_sha256": sha256_text(json.dumps(messages, sort_keys=True)), "usage": data.get("usage", {}),
                  "latency_s": round(time.time() - t0, 1), "finish_reason": choice.get("finish_reason"),
                  "tool_calls": [{"name": c["function"]["name"], "arguments": c["function"]["arguments"][:500]} for c in (msg.get("tool_calls") or [])]}
        (self.record_dir / f"{self.calls:03d}-{tag}.messages.json").write_text(json.dumps(messages, indent=1))
        (self.record_dir / f"{self.calls:03d}-{tag}.response.json").write_text(json.dumps(msg, indent=1))
        write_json(self.record_dir / f"{self.calls:03d}-{tag}.json", record)
        return msg, record


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
