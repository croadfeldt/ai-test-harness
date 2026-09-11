"""OSV.dev lookups: known vulnerabilities and OpenSSF Malicious Packages entries (MAL- ids).

Advisory text is untrusted data. It is stored verbatim for the reviewer and never fed to a model as
instructions.
"""
from __future__ import annotations

from pathlib import Path

from ..model import Vulnerability
from ..util import http_json, read_json, write_json

OSV_API = "https://api.osv.dev/v1"


def _cached(cache_dir: Path | None, vuln_id: str) -> dict | None:
    if cache_dir and (cache_dir / "osv" / f"{vuln_id}.json").exists():
        return read_json(cache_dir / "osv" / f"{vuln_id}.json")
    return None


def fetch_vuln(vuln_id: str, cache_dir: Path | None = None) -> dict | None:
    hit = _cached(cache_dir, vuln_id)
    if hit is not None:
        return hit
    data = http_json(f"{OSV_API}/vulns/{vuln_id}")
    if data is not None and cache_dir:
        write_json(cache_dir / "osv" / f"{vuln_id}.json", data)
    return data


def query_ids(pairs: list[tuple[str, str]], ecosystem: str = "PyPI") -> dict[tuple[str, str], list[str]]:
    """One batch call: (name, version) -> list of OSV ids."""
    out: dict[tuple[str, str], list[str]] = {}
    for start in range(0, len(pairs), 500):
        chunk = pairs[start:start + 500]
        body = {"queries": [{"package": {"name": n, "ecosystem": ecosystem}, "version": v} for n, v in chunk]}
        resp = http_json(f"{OSV_API}/querybatch", body) or {"results": []}
        for pair, result in zip(chunk, resp.get("results", [])):
            out[pair] = sorted(v["id"] for v in (result or {}).get("vulns", []))
    return out


def to_vulnerability(data: dict, package: str) -> Vulnerability:
    pkg_norm = package.lower().replace("_", "-")
    fixed: list[str] = []
    symbols: list[str] = []
    for aff in data.get("affected", []):
        name = (aff.get("package") or {}).get("name", "").lower().replace("_", "-")
        if name and name != pkg_norm:
            continue
        for rng in aff.get("ranges", []):
            for ev in rng.get("events", []):
                if "fixed" in ev:
                    fixed.append(ev["fixed"])
        eco = aff.get("ecosystem_specific") or {}
        for imp in eco.get("imports", []):
            symbols.extend(imp.get("symbols", []))
        symbols.extend(eco.get("symbols", []))
    sev = None
    for s in data.get("severity", []):
        sev = f"{s.get('type')}: {s.get('score')}"
        break
    if sev is None:
        sev = (data.get("database_specific") or {}).get("severity")
    return Vulnerability(
        id=data["id"],
        aliases=sorted(data.get("aliases", [])),
        summary=(data.get("summary") or data.get("details", ""))[:300],
        severity=sev,
        fixed_versions=sorted(set(fixed)),
        affected_symbols=sorted(set(symbols)),
        references=[r.get("url") for r in data.get("references", []) if r.get("url")][:10],
        malicious=data["id"].startswith("MAL-"),
    )


def lookup(pairs: list[tuple[str, str]], cache_dir: Path | None = None,
           ecosystem: str = "PyPI") -> dict[tuple[str, str], list[Vulnerability]]:
    ids = query_ids(pairs, ecosystem)
    out: dict[tuple[str, str], list[Vulnerability]] = {}
    for pair, id_list in ids.items():
        vulns = []
        for vid in id_list:
            data = fetch_vuln(vid, cache_dir)
            if data:
                vulns.append(to_vulnerability(data, pair[0]))
        out[pair] = vulns
    return out
