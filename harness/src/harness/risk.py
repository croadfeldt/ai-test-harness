"""Risk score and generation budget. Blueprint section 6.2 (depth policy) and 6.3 (score inputs).

The score is deliberately simple and every contribution is listed in `reasons` so a reviewer can see
why an item got the budget it did. Weights live here and nowhere else.
"""
from __future__ import annotations

import math

from .model import RiskScore

SENSITIVE_TERMS = {
    "auth": "authentication", "jwt": "authentication", "oauth": "authentication", "jose": "authentication",
    "crypto": "cryptography", "cipher": "cryptography", "tls": "cryptography", "ssl": "cryptography",
    "hash": "cryptography", "sign": "cryptography",
    "parse": "parsing", "parser": "parsing", "xml": "parsing", "yaml": "parsing", "json": "parsing",
    "html": "parsing", "pdf": "parsing", "image": "parsing", "imaging": "parsing", "multipart": "parsing",
    "upload": "parsing", "form": "parsing", "template": "parsing",
    "http": "network", "request": "network", "socket": "network", "client": "network", "server": "network",
    "asgi": "network", "wsgi": "network",
    "pickle": "serialization", "serial": "serialization", "marshal": "serialization",
    "subprocess": "process-execution", "exec": "process-execution", "shell": "process-execution",
    "sql": "data-access", "database": "data-access", "orm": "data-access",
}

FULL, REDUCED, SNAPSHOT = "full", "reduced", "snapshot"


def sensitivity(name: str, summary: str, keywords: str, classifiers: list[str]) -> list[str]:
    text = " ".join([name, summary, keywords, " ".join(classifiers)]).lower()
    found = set()
    for term, category in SENSITIVE_TERMS.items():
        if term in text:
            found.add(category)
    return sorted(found)


def score(*, depth: int, change: str, reachable: str, vuln_count: int, high_severity: bool, vulns_fixed: int = 0,
          breaking_changes: int, changed_symbols: int, lines_changed: int, sensitive: list[str],
          preflight_hit: bool, new_package: bool) -> RiskScore:
    reasons: list[str] = []
    s = 0
    if preflight_hit:
        reasons.append("pre-flight gate hit: maximum score, route to suspicious")
        s = 100
    else:
        if reachable == "true":
            s += 35; reasons.append("reachable from first-party code (+35)")
        elif reachable == "unknown":
            s += 20; reasons.append("reachability unknown, treated as reachable (+20)")
        if vuln_count:
            s += 25; reasons.append(f"{vuln_count} known vulnerabilit{'y' if vuln_count == 1 else 'ies'} for this version (+25)")
            if high_severity:
                s += 10; reasons.append("at least one advisory carries a severity rating (+10)")
        if breaking_changes:
            s += 15; reasons.append(f"{breaking_changes} breaking API change(s) (+15)")
        elif changed_symbols:
            s += 5; reasons.append(f"{changed_symbols} changed API symbol(s), none breaking (+5)")
        if lines_changed:
            pts = min(10, int(math.log10(lines_changed + 1) * 3))
            s += pts; reasons.append(f"{lines_changed} source lines changed (+{pts})")
        if sensitive:
            s += 10; reasons.append(f"sensitive domain: {', '.join(sensitive)} (+10)")
        if new_package:
            s += 10; reasons.append("new package in the graph (+10)")
        s = min(s, 99)

    # Depth policy, section 6.2.
    if preflight_hit:
        level = SNAPSHOT
        reasons.append("suspicious: sandbox characterization only until Supply Chain Security clears it")
    elif depth == 0:
        level = FULL
    elif depth == 1 and change in ("bumped", "added"):
        level = FULL; reasons.append("depth 1 version change: full generation by policy")
    elif depth >= 2 and (reachable == "true" or s >= 60):
        level = FULL; reasons.append("transitive but reachable or high risk: full generation")
    elif depth >= 2:
        level = SNAPSHOT; reasons.append("transitive, not reachable, below threshold: characterization snapshot")
    elif s >= 60:
        level = FULL
    elif s >= 30:
        level = REDUCED
    else:
        level = SNAPSHOT

    counts = {FULL: {"unit": 10, "functional": 5, "negative": 5, "fuzz_minutes": 10, "mutation_sample": 200},
              REDUCED: {"unit": 4, "functional": 2, "negative": 2, "fuzz_minutes": 0, "mutation_sample": 50},
              SNAPSHOT: {"unit": 0, "functional": 0, "negative": 0, "fuzz_minutes": 0, "mutation_sample": 0}}[level]
    budget = {"level": level, **counts, "cve_targeted": vuln_count > 0 or vulns_fixed > 0,
              "cve_fix_pinning": vulns_fixed,
              "functional_at_call_sites": depth == 1 and reachable == "true"}
    if vuln_count:
        reasons.append("known vulnerability: CVE-targeted tests and a draft VEX regardless of depth")
    if vulns_fixed:
        reasons.append(f"{vulns_fixed} advisor{'y' if vulns_fixed == 1 else 'ies'} on the replaced version: fix-pinning tests, then a VEX 'fixed' statement")
    return RiskScore(score=s, reasons=reasons, budget=budget, inputs={
        "depth": depth, "change": change, "reachable": reachable, "vuln_count": vuln_count,
        "high_severity": high_severity, "breaking_changes": breaking_changes, "changed_symbols": changed_symbols,
        "lines_changed": lines_changed, "sensitive": sensitive, "preflight_hit": preflight_hit, "vulns_fixed": vulns_fixed,
        "new_package": new_package})
