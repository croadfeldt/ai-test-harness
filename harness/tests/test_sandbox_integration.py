"""Proves the sandbox's isolation claims with a real container. Skipped when podman is absent."""
import shutil
from pathlib import Path

import pytest

from harness import sandbox

pytestmark = pytest.mark.skipif(shutil.which("podman") is None, reason="podman not installed")

PROBE = '''
import os, socket, pytest

def test_no_network():
    """Outbound connections fail inside the sandbox."""
    s = socket.socket(); s.settimeout(3)
    with pytest.raises(OSError):
        s.connect(("1.1.1.1", 443))

def test_no_secrets_in_env():
    """No credential-shaped variables reach the sandbox."""
    assert not [k for k in os.environ if any(x in k.upper() for x in ("TOKEN", "SECRET", "PASSWORD", "KEY"))]

def test_rootfs_read_only():
    """The container root filesystem cannot be written."""
    with pytest.raises(OSError):
        open("/usr/harness-probe", "w")

def test_target_package_importable():
    """The package under test is installed from the wheelhouse."""
    import six
    assert six.PY3
'''


def test_sandbox_isolation(tmp_path: Path):
    wheelhouse = sandbox.prefetch_wheelhouse(["six==1.17.0"], "3.12", tmp_path / "wh")
    tests = tmp_path / "tests"; tests.mkdir()
    (tests / "test_probe.py").write_text(PROBE)
    s = sandbox.run_tests(wheelhouse=wheelhouse, requirements=["six==1.17.0"], tests_dir=tests,
                          out_dir=tmp_path / "out", cover=["six"], label="probe")
    assert not s["install_failed"], (tmp_path / "out" / "stdout.log").read_text()[-2000:]
    results = sandbox.parse_junit(Path(s["junit"]))
    assert {k.split("::")[-1]: v["status"] for k, v in results.items()} == {
        "test_no_network": "pass", "test_no_secrets_in_env": "pass", "test_rootfs_read_only": "pass",
        "test_target_package_importable": "pass"}
    cov = sandbox.coverage_for(Path(s["coverage"]), ["six"])
    assert cov["covered_lines_in_target"] > 0
