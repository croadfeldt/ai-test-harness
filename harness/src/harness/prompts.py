"""Prompt sets: every text the harness says to a model, under source control, named and digested.

The defaults live next to the code that uses them (the adapters' SYSTEM and CATEGORY_TASK, the agent's
rules). A prompt set overrides any of those parts by key; "v1" is the defaults untouched. Every manifest
records the set's name and digest, so a result can always be traced to the exact words that produced
it, and `harness evaluate` can compare sets on the same jobs. Nothing here is assumed fit for purpose:
a set earns its place in the evaluation table, or it does not ship.

Keys: system.<ecosystem>, task.<category>.<ecosystem>, agent.rules. Sets live in harness/prompts/<name>.toml
as quoted dotted keys, or anywhere by path; HARNESS_PROMPT_SET or [model].prompt_set selects one.
"""
from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .util import sha256_text

HERE = Path(__file__).resolve().parent.parent.parent / "prompts"
CATEGORIES = ("unit", "functional", "negative", "cve")
ECOSYSTEMS = ("python", "go")


def defaults() -> dict[str, str]:
    """The texts in the code today, keyed; imported lazily because the adapters import this module's users."""
    from .adapters import go, python
    from .stages.agent import AGENT_RULES
    out = {"agent.rules": AGENT_RULES}
    for eco, mod in (("python", python), ("go", go)):
        out[f"system.{eco}"] = mod.SYSTEM
        for cat in CATEGORIES:
            out[f"task.{cat}.{eco}"] = mod.CATEGORY_TASK[cat]
    return out


@dataclass
class PromptSet:
    name: str
    overrides: dict[str, str] = field(default_factory=dict)
    source: str | None = None

    def text(self, key: str, default: str) -> str:
        return self.overrides.get(key, default)

    @property
    def parts(self) -> dict[str, str]:
        base = defaults()
        unknown = set(self.overrides) - set(base)
        if unknown:
            raise ValueError(f"prompt set {self.name} overrides unknown keys {sorted(unknown)}; known: {sorted(base)}")
        return {k: self.overrides.get(k, v) for k, v in base.items()}

    @property
    def digest(self) -> str:
        return sha256_text(json.dumps(self.parts, sort_keys=True))

    def record(self) -> dict:
        return {"name": self.name, "digest": self.digest, "overrides": sorted(self.overrides)}


def load(name_or_path: str) -> PromptSet:
    if name_or_path in ("", "v1", "default"):
        return PromptSet("v1")
    p = Path(name_or_path)
    if not p.suffix:
        p = HERE / f"{name_or_path}.toml"
    if not p.exists():
        raise FileNotFoundError(f"no prompt set at {p}; sets live in {HERE}")
    with p.open("rb") as f:
        data = tomllib.load(f)
    name = str(data.pop("name", p.stem))
    data.pop("description", None)
    return PromptSet(name, {k: str(v) for k, v in data.items()}, source=str(p))


_ACTIVE: PromptSet | None = None


def active() -> PromptSet:
    global _ACTIVE
    if _ACTIVE is None:
        _ACTIVE = load(str(config.get("model", "prompt_set", "HARNESS_PROMPT_SET", "v1")))
    return _ACTIVE


def text(key: str, default: str) -> str:
    return active().text(key, default)
