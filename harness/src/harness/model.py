"""Data model shared by every stage. Every stage reads and writes these as JSON.

The field names follow blueprint/adapter-interface.md and docs/03-blueprint.md stage 1 and 2.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Package:
    name: str
    version: str
    purl: str
    depth: int                       # 0 = first-party, 1 = direct, 2+ = transitive
    direct: bool
    parents: list[str] = field(default_factory=list)
    import_names: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    optional_requires: list[str] = field(default_factory=list)   # declared under an extra or a false marker
    download_url: str | None = None


@dataclass
class DependencyGraph:
    ecosystem: str
    source_dir: str
    manifest: str
    manifest_digest: str
    resolver: str
    python_version: str | None
    packages: dict[str, Package] = field(default_factory=dict)   # keyed by normalized name

    def roots(self) -> list[Package]:
        return [p for p in self.packages.values() if p.direct]


@dataclass
class Vulnerability:
    id: str
    aliases: list[str]
    summary: str
    severity: str | None                # OSV/CVSS vector or score text as published; not normalized
    fixed_versions: list[str]
    affected_symbols: list[str]         # only when the advisory names them; usually empty
    references: list[str]
    malicious: bool                     # OpenSSF Malicious Packages entry (MAL- id)


@dataclass
class Preflight:
    status: str                         # clean | hit | not_run
    findings: list[dict] = field(default_factory=list)
    tools: dict[str, str] = field(default_factory=dict)   # tool -> "ran"/"not_installed"


@dataclass
class WorkItem:
    package: str
    purl: str
    old_version: str | None
    new_version: str | None
    depth: int
    change: str                         # first_party | added | removed | bumped | unchanged
    reachable: str                      # "true" | "false" | "unknown"  (unknown is treated as reachable)
    reachable_evidence: list[str]
    preflight: Preflight
    vulns_old: list[str]
    vulns_new: list[str]
    parents: list[str]


@dataclass
class WorkList:
    run_id: str
    created: str
    mode: str                           # rescan | diff
    source_dir: str
    old_manifest: str | None
    new_manifest: str
    items: list[WorkItem]


@dataclass
class ApiSymbol:
    module: str
    qualname: str
    kind: str                           # module | function | class | method
    signature: str
    doc: str
    file: str
    line: int


@dataclass
class ApiChange:
    symbol: str
    kind: str                           # added | removed | changed
    breaking: bool
    old_signature: str | None
    new_signature: str | None
    reason: str


@dataclass
class CallSite:
    symbol: str
    file: str
    line: int
    in_test: bool
    context: str


@dataclass
class RiskScore:
    score: int
    inputs: dict
    reasons: list[str]
    budget: dict


@dataclass
class FactBundle:
    package: str
    purl: str
    old_version: str | None
    new_version: str | None
    depth: int
    change: str
    import_names: list[str]
    api_old_ref: str | None
    api_new_ref: str | None
    api_diff_ref: str | None
    api_diff_summary: dict
    source_diff_summary: dict
    call_sites_ref: str
    call_sites_summary: dict
    upstream_tests: dict
    vulns_ref: str
    vulns_summary: dict
    notes_ref: str | None
    static_analysis: dict
    sensitivity: list[str]
    risk: RiskScore
    generated: str
