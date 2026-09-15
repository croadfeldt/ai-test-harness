"""UDLM records from a run. Blueprint section 8.2: the provenance record IS a UDLM record, and the
signed in-toto statement is its projection, with the record's integrity head as the subject.

What is emitted, per package, under attest/<package>/udlm/:
- Vulnerability, one discovered record per vulnerability (CVE), the harness as the discovery source.
- SoftwarePackage, one discovered record per purl the evidence is about.
- Job, the harness run: requested and realized, carrying model, prompt digests, tool versions, the
  sandbox image and its digest, and the execution target.
- TestEvidence.VulnerabilityCheck.AiTestHarness (or TestEvidence for non-CVE tests, bound at the
  base), one INTENT record per accepted candidate: the harness proposes; a reviewer's acceptance
  becomes the realized record later, by a human act this stage cannot perform.
- VexStatement, one intent record per vulnerability: the draft for Product Security.

Sealing uses UDLM's own chain code (registry/tools/integrity_chain.py from a local checkout named
in the config), so the head is UDLM's by construction. Without that checkout, records are written
unsealed and the statement says so. Handles and uuids are deterministic from stable keys, so a
re-run of the same inputs yields the same entities. Nothing about the machine is recorded.
"""
from __future__ import annotations

import re
import sys
import uuid
from pathlib import Path

import yaml

from .. import __version__, config
from ..util import log, now_iso, read_json, write_json

CONFORMS = "udlm/0.1"
TYPE_ROOT = "https://udlm.dev/registry/udlm/0.1/class"
VERSIONS = {"Vulnerability": "0.2.1", "SoftwarePackage": "0.2.1", "Job": "1.0.0",
            "TestEvidence": "0.2.0", "TestEvidence.VulnerabilityCheck.AiTestHarness": "0.1.0", "VexStatement": "0.1.0"}
NS = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")   # RFC 4122 URL namespace


def _seal_fn():
    repo = config.get("udlm", "repo", "HARNESS_UDLM_REPO")
    if not repo:
        return None, "no UDLM checkout configured ([udlm].repo); records unsealed"
    p = Path(repo)
    root = p if p.is_absolute() else (config.HERE / p).resolve()
    tools = root / "registry" / "tools"
    if not (tools / "integrity_chain.py").exists():
        return None, "UDLM checkout has no registry/tools/integrity_chain.py; records unsealed"
    sys.path.insert(0, str(tools))
    from integrity_chain import head_for  # noqa: E402
    return head_for, None


def _schema():
    repo = config.get("udlm", "repo", "HARNESS_UDLM_REPO")
    if not repo:
        return None
    p = Path(repo); root = p if p.is_absolute() else (config.HERE / p).resolve()
    s = root / "registry" / "state-record.schema.json"
    return s if s.exists() else None


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:63]


def entity_uuid(kind: str, key: str) -> str:
    """Deterministic from a stable key (so a re-run names the same entity), shaped as the v4 uuid the
    schema requires: the version and variant nibbles are set on a uuid5 digest."""
    b = bytearray(uuid.uuid5(NS, f"udlm:{kind}:{key}").bytes)
    b[6] = (b[6] & 0x0F) | 0x40
    b[8] = (b[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(b)))


def z(ts: str) -> str:
    """UDLM timestamps are RFC 3339 in UTC with a Z; the harness records +00:00."""
    if not ts:
        return now_iso().replace("+00:00", "Z")
    return ts.replace("+00:00", "Z") if ts.endswith("+00:00") else ts


def record_uuid() -> str:
    if hasattr(uuid, "uuid7"):
        return str(uuid.uuid7())
    import time, secrets
    ms = int(time.time() * 1000)
    return f"{ms >> 16:08x}-{ms & 0xffff:04x}-7{secrets.token_hex(2)[1:]}-{8 + secrets.randbelow(4):x}{secrets.token_hex(2)[1:]}-{secrets.token_hex(6)}"


class Emitter:
    def __init__(self, workdir: Path, pkg: str):
        self.workdir, self.pkg = workdir, pkg
        self.estate = str(config.get("udlm", "estate", "HARNESS_UDLM_ESTATE", "example"))
        self.tenant = str(config.get("udlm", "tenant_uuid", "HARNESS_UDLM_TENANT", "00000000-0000-4000-8000-000000000000"))
        self.provider = str(config.get("udlm", "provider_handle", None, f"{self.estate}/providers/ai-test-harness"))
        self.clock = str(config.get("udlm", "time_source", None, "harness-clock"))
        self.head_for, self.seal_note = _seal_fn()
        self.records: dict[str, list[dict]] = {}
        self.refs: dict[str, str] = {}   # key -> URF handle reference

    # ---- record scaffolding
    def base(self, rt: str, state: str, res: str, ent: str, handle: str, at: str, fields: dict, **extra) -> dict:
        d = {"record_type": rt, "state": state, "entity_uuid": ent, "record_uuid": record_uuid(), "tenant_uuid": self.tenant,
             "conforms_to": CONFORMS, "resource_type": res, "type_version": VERSIONS[res],
             "type_ref": f"{TYPE_ROOT}/{res}/{VERSIONS[res]}", "handle": handle, "at": z(at), "time_source": self.clock, "fields": fields}
        d.update(extra)
        return d

    def prov(self, field: str, kind: str, who: str, at: str) -> dict:
        return {field: [{"source": {"kind": kind, "id": who}, "operation_type": "set", "sequence": 1, "timestamp": z(at)}]}

    def seal(self, rec: dict) -> dict:
        if self.head_for:
            rec["integrity"] = {"head": self.head_for(rec, None), "previous": None, "algorithm": "sha256-jcs"}
        return rec

    def add(self, name: str, rec: dict) -> dict:
        self.records.setdefault(name, []).append(rec)
        return rec

    # ---- builders
    def vulnerability(self, cve: str, group: list[dict], at: str) -> str:
        key = f"vulnerability/{slug(cve)}"
        if key in self.refs:
            return self.refs[key]
        handle = f"{self.estate}/knowledge/{key}"
        refs = sorted({r for v in group for r in v.get("references", [])})[:10]
        ranges = sorted({f"<{f}" for v in group for f in v.get("fixed_versions", [])})
        sev = next((v.get("severity") for v in group if v.get("severity")), None)
        fields = {"id": cve, "references": refs}
        if sev: fields["severity"] = str(sev)[:80]
        if ranges: fields["affected_ranges"] = ranges
        rec = self.base("discovered_record", "Discovered", "Vulnerability", entity_uuid("vulnerability", cve), handle, at, fields,
                        origin="discovered-derived", provenance=self.prov("fields.id", "discovery", self.provider, at),
                        metadata={"description": f"Also known as {', '.join(sorted({v['id'] for v in group}))}."})
        self.add("vulnerability", self.seal(rec))
        self.refs[key] = f"estate/{handle}"
        return self.refs[key]

    def package(self, purl: str, name: str, version: str, at: str) -> str:
        key = f"software-package/{slug(name + '-' + version)}"
        if key in self.refs:
            return self.refs[key]
        handle = f"{self.estate}/knowledge/{key}"
        rec = self.base("discovered_record", "Discovered", "SoftwarePackage", entity_uuid("software-package", purl), handle, at,
                        {"purl": purl, "name": name, "version": version, "type": purl.split(":")[1].split("/")[0]},
                        origin="discovered-derived", provenance=self.prov("fields.purl", "discovery", self.provider, at))
        self.add("software-package", self.seal(rec))
        self.refs[key] = f"estate/{handle}"
        return self.refs[key]

    def job(self, run: dict, wl: dict, gen: dict, results: dict, selfcheck: dict, subject_refs: list[str]) -> str:
        run_id = wl["run_id"]
        handle = f"{self.estate}/jobs/ai-test-harness-run-{slug(run_id)}"
        ent = entity_uuid("job", run_id)
        fields = {"definition_ref": f"estate/{self.estate}/automation/ai-test-harness-pipeline",
                  "parameters": {"repository": wl["source_dir"], "base": (wl.get("old_manifest") or "").split("@")[-1] or None,
                                 "head": wl["new_manifest"].split("@")[-1], "mode": wl["mode"]},
                  "targets": subject_refs, "max_execution_time": "PT3H", "on_max_exceeded": "terminate", "trigger": "manual"}
        fields["parameters"] = {k: v for k, v in fields["parameters"].items() if v is not None}
        started = run.get("started") or wl["created"]; done = results.get("generated") or now_iso()
        req_id = record_uuid()
        req = self.base("requested_record", "Requested", "Job", ent, handle, started, fields, intent_ref=record_uuid())
        req["record_uuid"] = req_id
        self.add("job", req)
        m = gen.get("model", {}); tools = run.get("tools", {})
        real = self.base("realized_record", "Realized", "Job", ent, handle, done, fields, requested_ref=req_id, provider=self.provider,
                         outputs={"started_at": z(started), "completed_at": z(done),
                                  "results": {"status": "COMPLETED", "run_id": run_id, "harness_version": __version__,
                                              "model_id": m.get("id", ""), "model_endpoint": m.get("endpoint", ""), "model_endpoint_digest": m.get("endpoint_digest", ""),
                                              "model_reasoning": "off" if (m.get("temperature") is not None) else "unknown",
                                              "tool_versions": {k: v for k, v in tools.items() if v},
                                              "sandbox_image": results["target"].get("identity", ""),
                                              "sandbox_image_digest": results["target"].get("image_digest") or "unknown",
                                              "execution_target": "Container",
                                              "selfcheck": {"passed": selfcheck.get("passed"), "checks": len(selfcheck.get("checks", []))},
                                              "tests_produced": results["counts"]["total"], "fix_pinning_confirmed": results["counts"]["fix_pinning_confirmed"],
                                              "flaky": results["counts"]["flaky"]}},
                         process={"execution_state": "COMPLETED",
                                  "affected_entities": [{"entity_uuid": entity_uuid("software-package", results["package"]["purl"]),
                                                         "effect_type": "read", "effect_description": "downloaded and ran the package in a sealed sandbox on two versions"}]})
        self.add("job", self.seal(real))
        return f"estate/{handle}"

    def vex(self, cve: str, statement: dict, vuln_ref: str, pkg_ref: str, evidence_refs: list[str], at: str) -> str:
        handle = f"{self.estate}/knowledge/vex-statement/{slug(cve + '-' + self.pkg)}"
        fields = {"vulnerability_ref": vuln_ref, "software_package_ref": pkg_ref, "status": statement["status"],
                  "status_notes": statement.get("status_notes", "")[:300], "evidence_refs": evidence_refs}
        rec = self.base("intent_record", "Intent", "VexStatement", entity_uuid("vex-statement", f"{cve}:{self.pkg}"), handle, at, fields,
                        origin="declared", provenance=self.prov("fields.status", "provider", self.provider, at))
        self.add("vex-statement", rec)
        return f"estate/{handle}"

    def evidence(self, rec_in: dict, facts: dict, result_row: dict, pkg_ref: str, job_ref: str, vuln_ref: str | None, vex_ref: str | None, at: str) -> dict:
        name = rec_in["test_id"].split("::")[1]
        is_cve = rec_in["category"] == "cve"
        res = f"TestEvidence.VulnerabilityCheck.AiTestHarness" if is_cve else "TestEvidence"
        handle = f"{self.estate}/knowledge/test-evidence/{slug(self.pkg + '-' + name)}"
        cat_map = {"cve": "security", "unit": "unit", "functional": "functional", "negative": "negative", "fuzz": "fuzz", "harness": "integration"}
        outcome = {"pass": "passed", "fail": "failed", "error": "error", "skip": "skipped", "flaky": "error"}.get(result_row.get("versions", {}).get("new", ""), "error")
        fields = {"test_id": rec_in["test_id"], "subject_ref": pkg_ref, "category": cat_map.get(rec_in["category"], "integration"),
                  "result": {"outcome": outcome, "duration_ms": int(result_row.get("duration_ms", 0)), "format": "junit-xml",
                             "report_ref": f"execute/{self.pkg}/new/junit.xml"},
                  "job_ref": job_ref, "file_path": rec_in["file"], "file_digest": rec_in["file_sha256"]}
        if is_cve:
            fields.update({"vulnerability_ref": vuln_ref, "vulnerability_role": rec_in["vulnerability"]["role"],
                           "version_range": rec_in["target"]["version_range"], "source_version": rec_in["generated_from"]["source_ref"],
                           "call_sites": rec_in["target"].get("call_sites", []), "validation": rec_in["validation"]})
            if vex_ref: fields["vex_statement_ref"] = vex_ref
        rec = self.base("intent_record", "Intent", res, entity_uuid("test-evidence", rec_in["test_id"]), handle, at, fields,
                        origin="declared", provenance=self.prov("fields.result", "provider", self.provider, at))
        # An intent record is proposed by its author and, per RHY-006, carries no provider block; it is
        # sealed like any record so the statement can name its head.
        self.add("test-evidence", self.seal(rec))
        return rec

    def acceptance(self, intent: dict, decision: dict, pr: dict, overlay_provider: str) -> tuple[dict, dict]:
        """A person accepted a candidate: the merge is the request (the reviewer, an actor, asks that
        the candidate become part of the suite) and the test as it landed is the realized record,
        provided by the overlay repository. Two records, one entity, per RHY-006; the intent stays."""
        fields = dict(intent["fields"])
        at = pr["merged_at"]
        req = self.base("requested_record", "Requested", intent["resource_type"], intent["entity_uuid"], intent["handle"], at, fields,
                        intent_ref=intent["record_uuid"], origin="declared",
                        provenance=self.prov("fields.test_id", "actor", pr["merged_by"], at))
        req = self.seal(req)
        self.add("test-evidence", req)
        outputs = {"accepted_at": z(at), "accepted_by": pr["merged_by"], "pull_request": pr["url"], "merge_commit": pr["merge_commit"],
                   "decision": decision["decision"], "path": decision["path"], "file_digest": decision.get("merged_digest"),
                   "edited": decision["decision"] == "edited"}
        real = self.base("realized_record", "Realized", intent["resource_type"], intent["entity_uuid"], intent["handle"], at, fields,
                         requested_ref=req["record_uuid"], provider=overlay_provider, outputs=outputs,
                         provenance=self.prov("outputs", "actor", pr["merged_by"], at))
        real = self.seal(real)
        self.add("test-evidence", real)
        return req, real

    # ---- output
    def write(self, out_dir: Path) -> dict:
        out_dir.mkdir(parents=True, exist_ok=True)
        index = {"generated": now_iso(), "estate": self.estate, "sealed": self.head_for is not None, "seal_note": self.seal_note,
                 "files": {}, "heads": {}}
        for name, recs in self.records.items():
            path = out_dir / f"{name}.yaml"
            with path.open("w") as f:
                f.write(f"# UDLM {name} records emitted by ai-test-harness {__version__} from run artifacts; every value is a fact from the run.\n")
                for i, r in enumerate(recs):
                    f.write("---\n" if i == 0 else "\n---\n")
                    yaml.safe_dump(r, f, sort_keys=False, allow_unicode=True, width=110)
            index["files"][name] = path.name
            for r in recs:
                if "integrity" in r:
                    index["heads"][r["handle"] + "@" + r["state"].lower()] = r["integrity"]["head"]
        schema = _schema()
        if schema:
            import json, jsonschema
            sch = json.loads(schema.read_text())
            # UDLM's schemas reference each other by their published $id; preload every schema in
            # the checkout so resolution never leaves this machine.
            store = {}
            for sf in schema.parent.glob("*.schema.json"):
                doc = json.loads(sf.read_text())
                if "$id" in doc:
                    store[doc["$id"]] = doc
                store[sf.as_uri()] = doc
            resolver = jsonschema.RefResolver(base_uri=sch.get("$id", schema.as_uri()), referrer=sch, store=store)
            validator = jsonschema.Draft202012Validator(sch, resolver=resolver)
            problems = []
            for name, recs in self.records.items():
                for r in recs:
                    for e in validator.iter_errors(r):
                        problems.append(f"{name}:{r['handle']}:{'/'.join(str(p) for p in e.path)}: {e.message[:120]}")
            index["schema_validation"] = {"schema": "registry/state-record.schema.json", "problems": problems[:40], "count": len(problems)}
        else:
            index["schema_validation"] = {"schema": None, "note": "no UDLM checkout configured; records not validated"}
        write_json(out_dir / "index.json", index)
        return index


def emit(workdir: Path, pkg: str) -> dict:
    """Build every UDLM record for one package's run and write them under attest/<pkg>/udlm/."""
    from .generate import _group_advisories
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    vdoc = read_json(workdir / "analyze" / pkg / "vulns.json")
    manifest = read_json(workdir / "attest" / pkg / "MANIFEST.json")["records"]
    results = read_json(workdir / "execute" / pkg / "results.json")
    vex = read_json(workdir / "packet" / pkg / "vex.openvex.json")
    wl = read_json(workdir / "intake" / "worklist.json")
    gen = read_json(workdir / "generate" / pkg / "manifest.json")
    run = read_json(workdir / "run.json") if (workdir / "run.json").exists() else {}
    selfcheck = read_json(workdir / "selfcheck" / "selfcheck.json") if (workdir / "selfcheck" / "selfcheck.json").exists() else {}
    at = results.get("generated") or now_iso()
    em = Emitter(workdir, pkg)
    head_version = facts["new_version"] or facts["old_version"]
    pkg_ref = em.package(facts["purl"], pkg, head_version, at)
    job_ref = em.job(run, wl, gen, results, selfcheck, [pkg_ref])
    # vulnerabilities: one record per CVE, from advisories on either version
    seen = set(); vulns_all = [v for v in vdoc.get("vulns_old", []) + vdoc["vulns"] if not (v["id"] in seen or seen.add(v["id"]))]
    groups = _group_advisories(vulns_all)
    vuln_refs = {cve: em.vulnerability(cve, grp, at) for cve, grp in groups.items()}
    by_name = {t["name"]: t for t in results["tests"]}
    # evidence first (VEX references it), then VEX with the evidence refs
    ev_recs = []
    cve_of_test = {}
    for r in manifest:
        name = r["test_id"].split("::")[1]
        cve = r.get("vulnerability", {}).get("id") or None
        cve_of_test[name] = cve
        vref = vuln_refs.get(cve) if cve else None
        ev = em.evidence(r, facts, by_name.get(name, {}), pkg_ref, job_ref, vref, None, at)
        ev_recs.append((name, cve, ev))
    for st in vex["statements"]:
        cve = st["vulnerability"]["name"]
        ev_refs = [f"estate/{ev['handle']}" for name, c, ev in ev_recs if c == cve]
        vref = vuln_refs.get(cve) or em.vulnerability(cve, [{"id": cve, "aliases": st["vulnerability"].get("aliases", []), "references": [], "fixed_versions": []}], at)
        vex_ref = em.vex(cve, st, vref, pkg_ref, ev_refs, at)
        for name, c, ev in ev_recs:
            if c == cve and "vulnerability_ref" in ev["fields"]:
                ev["fields"]["vex_statement_ref"] = vex_ref
                if em.head_for:
                    ev.pop("integrity", None); em.seal(ev)
    index = em.write(workdir / "attest" / pkg / "udlm")
    n = sum(len(v) for v in em.records.values())
    log(f"    {pkg}: {n} UDLM record(s) in {len(em.records)} file(s); sealed={index['sealed']}; schema problems={index.get('schema_validation', {}).get('count', 'n/a')}")
    return index
