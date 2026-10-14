"""Declared needs: what a test needs from its testbed, said up front, verified by the sandbox (blueprint stage 4).

Four tiers, the ladder Debian's autopkgtest and Google's test sizes already use:

    none       the test touches nothing outside the process; runs sealed (the default when nothing is declared)
    localhost  the test opens local ports or services; runs sealed, loopback allowed
    network    the test needs the real network; the harness never runs it, it is proposed to the team with the
               declaration and proves itself in their pipeline
    machine    the test needs a real kernel, a device or native code the container cannot promise; a Kata
               testbed where the cluster has one, else proposed to the team the same way

A need the testbed does not provide is a skip with a structured reason, never a failure: the test is
withheld from the sealed run, recorded as `skipped` with its need, and the accounting puts the behaviour
it targets in the state "for your environment". A need the test did NOT declare and then used is a defect
in the test (pytest-socket's rule): the Python sandbox's conftest raises `HarnessUndeclaredNeed` on the
first connection a `none` test opens, and the verdict names it. Go tests meet the sealed network
instead and are judged by the error they report.

Declaration syntax: Python `@pytest.mark.needs("network")`; Go `// harness:needs network` on the line
above `func TestX`. What the testbed provides is the team's setting: `[sandbox] provides` in the
configuration or `HARNESS_PROVIDES`, default `none, localhost`.
"""
from __future__ import annotations

from . import config

NEEDS = ("none", "localhost", "network", "machine")
DEFAULT_PROVIDES = ("none", "localhost")
UNDECLARED = "undeclared need"          # the verdict prefix
LOOPBACK = {"127.0.0.1", "::1", "localhost", "0.0.0.0", "::"}


def provided() -> set[str]:
    """What this testbed provides, as the team configured it. `none` is always provided."""
    raw = config.get("sandbox", "provides", env="HARNESS_PROVIDES", default=list(DEFAULT_PROVIDES))
    items = [x.strip() for x in raw.split(",")] if isinstance(raw, str) else list(raw)
    out = {x for x in items if x in NEEDS}
    out.add("none")
    return out


def normalize(need: str | None) -> str:
    return need if need in NEEDS else "none"


def withheld(declared: dict[str, str], provides: set[str] | None = None) -> dict[str, str]:
    """The tests whose declared need this testbed does not provide: test name -> need."""
    provides = provides if provides is not None else provided()
    return {name: normalize(need) for name, need in declared.items() if normalize(need) not in provides}


def allowed(need: str, host: str) -> bool:
    """The sandbox's rule for a connection attempt by a test with this declaration."""
    need = normalize(need)
    if need in ("network", "machine"):
        return True
    if need == "localhost":
        return host in LOOPBACK or host.startswith("127.")
    return False


def skip_verdict(need: str) -> str:
    return f"needs {need}: not provided in this testbed; proposed for your environment, where it proves itself"


# The conftest the Python sandbox lays beside the tests: registers the marker and enforces the rule.
CONFTEST = '''"""Written by the AI Test Harness beside the generated tests: declared needs (blueprint stage 4).

A test declares what it needs with @pytest.mark.needs("none" | "localhost" | "network" | "machine").
Nothing declared means none. A test that opens a connection it did not declare fails with
HarnessUndeclaredNeed: the test is wrong about itself, and the verdict says so."""
import socket

import pytest

LOOPBACK = {"127.0.0.1", "::1", "localhost", "0.0.0.0", "::"}


class HarnessUndeclaredNeed(Exception):
    pass


def pytest_configure(config):
    config.addinivalue_line("markers", "needs(kind): what this test needs from its testbed: none, localhost, network or machine")


def _host(address):
    try:
        return address[0] if isinstance(address, tuple) else str(address)
    except Exception:
        return str(address)


@pytest.fixture(autouse=True)
def _harness_declared_needs(request):
    marker = request.node.get_closest_marker("needs")
    need = marker.args[0] if marker and marker.args else "none"
    if need in ("network", "machine"):
        yield
        return
    original_connect, original_connect_ex = socket.socket.connect, socket.socket.connect_ex

    def guard(fn):
        def wrapped(self, address, *a, **kw):
            host = _host(address)
            if need == "localhost" and (host in LOOPBACK or str(host).startswith("127.")):
                return fn(self, address, *a, **kw)
            raise HarnessUndeclaredNeed(f"undeclared need: the test opened a connection to {host!r} but declared {need!r}; "
                                        "declare @pytest.mark.needs(\\"network\\") or \\"localhost\\", or remove the connection")
        return wrapped

    socket.socket.connect, socket.socket.connect_ex = guard(original_connect), guard(original_connect_ex)
    try:
        yield
    finally:
        socket.socket.connect, socket.socket.connect_ex = original_connect, original_connect_ex
'''

PROMPT_RULE = ("Every test must say what it needs from the machine it runs on, with one of four words: none (the default; the test "
               "touches nothing outside the process), localhost (opens local ports), network (needs the real network), machine "
               "(needs a real kernel, a device or native code a container cannot promise). The harness runs none and localhost "
               "tests sealed, with no network; a none test that opens a connection is a defect. network and machine tests are not "
               "run here: they are proposed to the team with the declaration and prove themselves in the team's own pipeline. "
               "Prefer none. Declare with: {syntax}.")

SYNTAX = {"python": '@pytest.mark.needs("network") on the test function (the harness registers the marker)',
          "go": '// harness:needs network on the line above func TestX'}
