"""Attestation. Blueprint sections 8.2 and 8.5.

Writes the provenance record for every test the packet accepts (manifest.schema.yaml), the in-toto
Statement with the vetted test-result/v0.1 predicate carrying the harness record in its configuration
descriptor (blueprint/test-evidence-predicate.json), and a DSSE envelope. Signing here uses a local
Ed25519 key generated on first use and kept outside the sandbox; inside Konflux, Tekton Chains and
Trusted Artifact Signer replace it, and the record says which signer was used so nobody mistakes one
for the other. Conforma verifies the statement; this stage only produces it.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from .. import __version__
from ..util import log, now_iso, read_json, sha256_file, sha256_text, write_json

PREDICATE_TYPE = "https://in-toto.io/attestation/test-result/v0.1"
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"


def _key(workdir: Path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    kdir = Path.home() / ".config" / "ai-test-harness"
    kdir.mkdir(parents=True, exist_ok=True)
    priv_path, pub_path = kdir / "signing.key", kdir / "signing.pub"
    if not priv_path.exists():
        priv = ed25519.Ed25519PrivateKey.generate()
        priv_path.write_bytes(priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        priv_path.chmod(0o600)
        pub_path.write_bytes(priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    priv = serialization.load_pem_private_key(priv_path.read_bytes(), password=None)
    pub_pem = pub_path.read_text()
    return priv, pub_pem, "sha256:" + hashlib.sha256(pub_pem.encode()).hexdigest()


def _dsse(payload: bytes, payload_type: str, priv, keyid: str) -> dict:
    def pae(t: str, p: bytes) -> bytes:
        return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(p)).encode() + b" " + p
    sig = priv.sign(pae(payload_type, payload))
    return {"payloadType": payload_type, "payload": base64.b64encode(payload).decode(),
            "signatures": [{"keyid": keyid, "sig": base64.b64encode(sig).decode()}]}


def attest_package(workdir: Path, pkg: str, run: dict, selfcheck: dict) -> dict:
    facts = read_json(workdir / "analyze" / pkg / "facts.json")
    triage = read_json(workdir / "triage" / pkg / "triage.json")
    pk = read_json(workdir / "packet" / pkg / "packet.json")
    gen = read_json(workdir / "generate" / pkg / "manifest.json")
    results = read_json(workdir / "execute" / pkg / "results.json")
    vex = read_json(workdir / "packet" / pkg / "vex.openvex.json")
    wl = read_json(workdir / "intake" / "worklist.json")
    graph_new = read_json(workdir / "intake" / "graph.new.json")
    out = workdir / "attest" / pkg
    out.mkdir(parents=True, exist_ok=True)
    mut_path = workdir / "execute" / pkg / "mutation" / "mutation.json"
    mutation = read_json(mut_path) if mut_path.exists() else None
    per_test = (mutation or {}).get("per_test", {})
    by_name = {t["name"]: t for t in results["tests"]}
    tri_by_name = {t["name"]: t for t in triage["tests"]}
    file_by_test = {t: f for f in gen["files"] for t in f["tests"]}
    tool_versions = {k: v for k, v in run.get("tools", {}).items() if v}
    records = []
    for name in pk["tests_in_patch"]:
        f = file_by_test.get(name, {}); r = by_name.get(name, {}); tr = tri_by_name.get(name, {})
        rec = {"test_id": f"{pkg}::{name}::{f.get('sha256', '')[7:19]}", "file": f.get("file"), "file_sha256": f.get("sha256"),
               "category": f.get("category", "unit"),
               "target": {"purl": facts["purl"], "version_range": f"=={facts['new_version']}" if facts["new_version"] else "",
                          "symbols": f.get("targets", [])[:20], "call_sites": facts["call_sites_summary"]["files"][:10]},
               "generated_from": {"source_ref": wl["new_manifest"], "sbom_component": facts["purl"]},
               "run": {"run_id": wl["run_id"], "model_id": f.get("model", gen.get("model", {}).get("id", "")),
                       "prompt_sha256": f.get("prompt_sha256", "agent: see manifest.agent.json"), "tool_versions": tool_versions,
                       "image": results["target"]["identity"],
                       "image_digest": results["target"].get("image_digest") or "unknown: digest not recorded at run time",
                       "execution_target": "podman"},
               "validation": {"baseline_pass": r.get("versions", {}).get("new") == "pass", "coverage_delta": 0.0,
                              "mutants_killed": len(per_test.get(name, {}).get("killed", [])),
                              "unique_mutants_killed": len(per_test.get(name, {}).get("unique", [])),
                              "flake_runs": 2, "differential": "changed" if r.get("versions", {}).get("old") != r.get("versions", {}).get("new") else "same"},
               "lifecycle": {"state": "candidate", "state_changed_at": now_iso(), "bumps_survived": 0, "regressions_caught": 0}}
        if f.get("category") == "cve":
            role = "fix-pinning" if name.endswith("fix_pinning") else "exposure"
            cve = next((st for st in vex["statements"] if any(x.lower().replace("-", "_") in name for x in st["vulnerability"]["aliases"])), None)
            rec["vulnerability"] = {"id": cve["vulnerability"]["name"] if cve else "", "role": role,
                                    "vex_statement_ref": pk["vex"], "vex_status": cve["status"] if cve else "under_investigation",
                                    "vex_justification": tr.get("action", "")}
        records.append(rec)
    manifest_path = out / "MANIFEST.json"
    write_json(manifest_path, {"package": pkg, "records": records})
    manifest_digest = sha256_file(manifest_path)
    predicate = {
        "result": "PASSED" if results["counts"]["flaky"] == 0 and not triage["summary"]["blocking"] else "WARNED",
        "configuration": [{"name": "ai-test-harness-record", "digest": {"sha256": manifest_digest[7:]}, "annotations": {
            "run": {"run_id": wl["run_id"], "pipeline_run": run.get("command", []), "harness_version": __version__,
                    "harness_image_digest": "local-dev (not a container build)", "model_id": gen.get("model", {}).get("id", ""),
                    "model_endpoint": gen.get("model", {}).get("endpoint", ""), "model_endpoint_digest": gen.get("model", {}).get("endpoint_digest", ""),
                    "execution_targets": ["podman"],
                    "selfcheck": {"passed": selfcheck.get("passed"), "checks": [c["id"] for c in selfcheck.get("checks", []) if c["status"] == "pass"],
                                  "ref": "selfcheck/selfcheck.json"}},
            "inputs": {"snapshot": wl["new_manifest"], "base": wl.get("old_manifest"), "sbom_digest": sha256_file(workdir / "intake" / "sbom.new.cdx.json"),
                       "graph_resolver": graph_new["resolver"], "build_provenance_ref": "none: not run inside Konflux"},
            "work_items": [{"purl": facts["purl"], "old_version": facts["old_version"], "depth": facts["depth"],
                            "reachable": facts["call_sites_summary"]["reachable"], "risk_score": facts["risk"]["score"] / 100,
                            "preflight": "hit" if facts["risk"]["inputs"].get("preflight_hit") else "clean"}],
            "tests_produced": [{"test_id": r["test_id"], "file_sha256": r["file_sha256"], "category": r["category"], "record_ref": f"attest/{pkg}/MANIFEST.json"} for r in records],
            "tests_promoted": [], "tests_retired": [],
            "findings": [{"class": f["class"], "confidence": f["confidence"], "evidence_ref": f["evidence_ref"], "summary": f["summary"]} for f in triage["findings"]],
            "vex_drafts": [{"vulnerability": st["vulnerability"]["name"], "status": st["status"], "evidence_test_ids": st["harness_evidence"]["tests"], "reviewed_by": None} for st in vex["statements"]],
            "metrics": {"build_success_rate": None, "mutation_score": (mutation or {}).get("score"),
                        "mutation_sample": (mutation or {}).get("sampled"), "mutation_engine": (mutation or {}).get("engine"),
                        "flake_rate": results["counts"]["flaky"] / max(1, results["counts"]["total"]),
                        "coverage_lines_in_target": results["coverage_summary"]["covered_lines_in_target"],
                        "fix_pinning_confirmed": results["counts"]["fix_pinning_confirmed"], "tests_total": results["counts"]["total"]},
            "unverified": ([] if mutation else ["mutation score: mutation testing was not run for this package"]) + [
                          "mutation engine: harness AST mutator on a bounded sample, not mutmut",
                          "coverage delta: no baseline overlay suite yet",
                           "signer: local Ed25519 development key, not Trusted Artifact Signer",
                           "harness image digest: harness ran from a checkout, not a built image"]
                          + ([] if results["target"].get("image_digest") else ["sandbox image digest: not recorded at run time; the image is pinned by tag only"])}}],
        "url": f"packet/{pkg}/packet.md",
        "passedTests": [t["name"] for t in results["tests"] if t["versions"]["new"] == "pass"],
        "warnedTests": [t["name"] for t in results["tests"] if t["status"] == "flaky"],
        "failedTests": [t["name"] for t in results["tests"] if t["versions"]["new"] in ("fail", "error")],
    }
    # UDLM records: the provenance record is a UDLM record, and its integrity head is a subject of
    # the statement (blueprint section 8.2). Emitted before the statement so the heads are known.
    from . import udlm_records
    udlm_index = udlm_records.emit(workdir, pkg)
    udlm_subjects = [{"name": f"udlm:{handle_state}", "digest": {"sha256": head[7:]}}
                     for handle_state, head in sorted(udlm_index.get("heads", {}).items()) if handle_state.endswith("@intent") and "/test-evidence/" in handle_state]
    if not udlm_index.get("sealed"):
        predicate["configuration"][0]["annotations"]["unverified"].append(f"UDLM records unsealed: {udlm_index.get('seal_note')}")
    if udlm_index.get("schema_validation", {}).get("count"):
        predicate["configuration"][0]["annotations"]["unverified"].append(
            f"UDLM records: {udlm_index['schema_validation']['count']} schema problem(s), see attest/{pkg}/udlm/index.json")
    predicate["configuration"][0]["annotations"]["udlm"] = {"records": udlm_index.get("files", {}), "sealed": udlm_index.get("sealed"),
                                                            "estate": udlm_index.get("estate"), "index_ref": f"attest/{pkg}/udlm/index.json"}
    statement = {"_type": STATEMENT_TYPE,
                 "subject": [{"name": f"packet/{pkg}/tests.patch", "digest": {"sha256": pk["patch_sha256"][7:]}},
                             {"name": f"attest/{pkg}/MANIFEST.json", "digest": {"sha256": manifest_digest[7:]}}] + udlm_subjects,
                 "predicateType": PREDICATE_TYPE, "predicate": predicate}
    stmt_path = out / "statement.json"
    write_json(stmt_path, statement)
    priv, pub_pem, keyid = _key(workdir)
    payload = json.dumps(statement, sort_keys=True, separators=(",", ":")).encode()
    env = _dsse(payload, "application/vnd.in-toto+json", priv, keyid)
    write_json(out / "statement.dsse.json", env)
    (out / "signer.pub.pem").write_text(pub_pem)
    rec = {"package": pkg, "generated": now_iso(), "manifest": f"attest/{pkg}/MANIFEST.json", "manifest_sha256": manifest_digest,
           "statement": f"attest/{pkg}/statement.json", "envelope": f"attest/{pkg}/statement.dsse.json", "keyid": keyid,
           "signer": "local Ed25519 development key (~/.config/ai-test-harness/signing.key); Trusted Artifact Signer in Konflux",
           "records": len(records), "result": predicate["result"],
           "udlm": {"index": f"attest/{pkg}/udlm/index.json", "sealed": udlm_index.get("sealed"), "subjects": len(udlm_subjects),
                    "schema_problems": udlm_index.get("schema_validation", {}).get("count")}}
    write_json(out / "attest.json", rec)
    log(f"    {pkg}: {len(records)} provenance record(s), statement {predicate['result']}, signed with {keyid[:19]}")
    return rec


def verify(envelope_path: Path, pub_pem_path: Path) -> bool:
    """Verify a DSSE envelope produced here. Conforma or cosign does this in the pipeline."""
    from cryptography.hazmat.primitives import serialization
    env = read_json(envelope_path)
    pub = serialization.load_pem_public_key(pub_pem_path.read_bytes())
    payload = base64.b64decode(env["payload"])
    pae = b"DSSEv1 " + str(len(env["payloadType"])).encode() + b" " + env["payloadType"].encode() + b" " + str(len(payload)).encode() + b" " + payload
    for s in env["signatures"]:
        try:
            pub.verify(base64.b64decode(s["sig"]), pae)
            return True
        except Exception:
            continue
    return False


def attest(*, workdir: Path, select: list[str] | None = None) -> list[dict]:
    from .. import selfcheck as sc
    sc.require(workdir, probes=False)
    run = read_json(workdir / "run.json") if (workdir / "run.json").exists() else {}
    selfcheck = read_json(workdir / "selfcheck" / "selfcheck.json")
    pk = read_json(workdir / "packet" / "summary.json")
    outs = [attest_package(workdir, p["package"], run, selfcheck) for p in pk["packages"] if not select or p["package"] in select]
    for o in outs:
        o["verified_locally"] = verify(workdir / o["envelope"], workdir / "attest" / o["package"] / "signer.pub.pem")
    from ..util import merge_summary
    merge_summary(workdir / "attest" / "summary.json", outs)
    return outs
