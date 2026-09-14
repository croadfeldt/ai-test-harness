"""Ecosystem adapters. One per language, each implementing blueprint/adapter-interface.md."""
from __future__ import annotations

from . import go as _go
from . import python as _python

ADAPTERS = {"python": _python, "go": _go}


def get(ecosystem: str):
    try:
        return ADAPTERS[ecosystem]
    except KeyError:
        raise ValueError(f"no adapter for ecosystem {ecosystem!r}; have {sorted(ADAPTERS)}") from None
