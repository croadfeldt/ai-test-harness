"""PyPI metadata: summary, keywords, classifiers, project URLs, and the long description.

The long description is release-notes-grade text from outside. It is written to a file whose name
says untrusted and is shown to reviewers, never used as instructions.
"""
from __future__ import annotations

from pathlib import Path

from ..util import http_json, read_json, write_json

PYPI_API = "https://pypi.org/pypi"


def metadata(name: str, version: str, cache_dir: Path | None = None) -> dict | None:
    key = f"{name}-{version}.json"
    if cache_dir and (cache_dir / "pypi" / key).exists():
        return read_json(cache_dir / "pypi" / key)
    data = http_json(f"{PYPI_API}/{name}/{version}/json")
    if data is None:
        return None
    info = data.get("info", {})
    urls = data.get("urls", [])
    slim = {
        "name": info.get("name"),
        "version": info.get("version"),
        "summary": info.get("summary") or "",
        "keywords": info.get("keywords") or "",
        "classifiers": info.get("classifiers") or [],
        "project_urls": info.get("project_urls") or {},
        "requires_python": info.get("requires_python"),
        "requires_dist": info.get("requires_dist") or [],
        "upload_time": urls[0].get("upload_time_iso_8601") if urls else None,
        "description": info.get("description") or "",
        "description_content_type": info.get("description_content_type"),
        "yanked": any(u.get("yanked") for u in urls),
    }
    if cache_dir:
        write_json(cache_dir / "pypi" / key, slim)
    return slim
