"""The UDLM emitter: stable identities, valid handles, one record per state, no local details."""
import re

from harness.stages import udlm_records as u

HANDLE = re.compile(r"^([a-z0-9][a-z0-9-]{0,61}[a-z0-9]/)*[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$")


def test_identities_are_stable_and_handles_valid(monkeypatch):
    assert u.entity_uuid("vulnerability", "CVE-2024-33664") == u.entity_uuid("vulnerability", "CVE-2024-33664")
    assert u.entity_uuid("vulnerability", "CVE-2024-33664") != u.entity_uuid("software-package", "CVE-2024-33664")
    assert HANDLE.match("example/knowledge/software-package/" + u.slug("python-jose-3.4.0"))
    assert u.slug("Python_Jose 3.4.0!") == "python-jose-3-4-0"
    r = u.record_uuid()
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", r)


def test_records_carry_no_machine_details(tmp_path, monkeypatch):
    monkeypatch.setattr(u.config, "get", lambda section, key, env=None, default=None: {"estate": "tt", "tenant_uuid": "00000000-0000-4000-8000-000000000000",
                                                                                      "provider_handle": "tt/providers/h", "time_source": "clock", "repo": None}.get(key, default))
    em = u.Emitter(tmp_path, "pkg")
    assert em.head_for is None and "unsealed" in em.seal_note
    ref = em.package("pkg:pypi/pkg@1.0", "pkg", "1.0", "2026-01-01T00:00:00Z")
    vref = em.vulnerability("CVE-2026-1", [{"id": "GHSA-x", "aliases": ["CVE-2026-1"], "references": ["https://osv.dev/x"], "fixed_versions": ["1.1"]}], "2026-01-01T00:00:00Z")
    assert ref.startswith("estate/tt/knowledge/software-package/") and vref.startswith("estate/tt/knowledge/vulnerability/")
    idx = em.write(tmp_path / "udlm")
    text = "".join((tmp_path / "udlm" / f).read_text() for f in idx["files"].values())
    assert "/Users/" not in text and "http://10." not in text
    for rec in em.records["vulnerability"] + em.records["software-package"]:
        assert rec["record_type"] == "discovered_record" and rec["state"] == "Discovered"
        assert HANDLE.match(rec["handle"]), rec["handle"]
