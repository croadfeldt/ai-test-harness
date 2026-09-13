#!/usr/bin/env python3
"""Remove local-install details from committed example records: endpoint addresses become the
endpoint's label plus a digest of the address, absolute repository paths become the repository's
name, and tool version strings lose their local path. Test file digests, verdicts, and every other
recorded fact are untouched. Attestations that covered rewritten records are re-signed by running
`harness attest` again on the affected run.

Usage: python3 tools/redact-local-details.py <mapping.toml> <path>...
mapping.toml:
  [endpoints]   "http://host:port/v1" = "label"
  [paths]       "/abs/path/to/repo" = "repo-name"
"""
import hashlib, re, sys, tomllib
from pathlib import Path

mapping = tomllib.loads(Path(sys.argv[1]).read_text())
endpoints = mapping.get("endpoints", {}); paths = mapping.get("paths", {})
def digest(url): return "sha256:" + hashlib.sha256(url.rstrip("/").encode()).hexdigest()[:16]

changed = 0
for root in map(Path, sys.argv[2:]):
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file() and p.suffix in (".json", ".md", ".txt", ".patch", ".yaml", ".yml", ".py")]
    for f in files:
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        new = text
        for url, label in endpoints.items():
            # JSON: "endpoint": "<url>"  ->  "endpoint": "<label>", "endpoint_digest": "<digest>"
            new = re.sub(r'"endpoint": "%s/?"' % re.escape(url), f'"endpoint": "{label}", "endpoint_digest": "{digest(url)}"', new)
            new = re.sub(r'"model_endpoint": "%s/?"' % re.escape(url), f'"model_endpoint": "{label}", "model_endpoint_digest": "{digest(url)}"', new)
            new = new.replace(url, label)
        for p, name in paths.items():
            new = new.replace(p + "/", "").replace(p, name)
        new = re.sub(r'"pip": "(pip [0-9.]+) from [^"]*"', r'"pip": "\1"', new)
        if new != text:
            f.write_text(new); changed += 1
print(f"rewrote {changed} file(s)")
