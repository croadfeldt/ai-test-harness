"""An ecosystem named on the command line brings its own manifest default, whatever the local config says."""
from harness import cli


def test_explicit_ecosystem_ignores_the_configured_manifest(monkeypatch):
    from harness import config
    monkeypatch.setattr(config, "get", lambda section, key, env=None, default=None: {"ecosystem": "python", "manifest": "requirements.txt"}.get(key, default))
    assert cli._ecosystem_and_manifest("go", None) == ("go", "go.mod")
    assert cli._ecosystem_and_manifest("go", "cmd/go.mod") == ("go", "cmd/go.mod")
    assert cli._ecosystem_and_manifest(None, None) == ("python", "requirements.txt")
