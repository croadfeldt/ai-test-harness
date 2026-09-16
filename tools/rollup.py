#!/usr/bin/env python3
"""The evidence so far, as one table read from the run records under examples/, never typed by hand.

Usage: python3 tools/rollup.py [--write docs/11-evidence-rollup.md]
Every number comes from a file a reader can open: execute/summary.json, triage/summary.json,
execute/<package>/mutation/mutation.json, attest/summary.json, assess/assess.json, propose/ and
feedback/ summaries, intake/worklist.json and packet/summary.json for the time to packet. A run that
lacks a stage shows a dash for it.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"


def load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def run_rows(run: Path) -> list[dict]:
    wl = load(run / "intake" / "worklist.json")
    if not wl:
        return []
    tri = {r["package"]: r for r in (load(run / "triage" / "summary.json") or {"packages": []})["packages"]}
    att = {r["package"]: r for r in (load(run / "attest" / "summary.json") or {"packages": []})["packages"]}
    gen = load(run / "generate" / "summary.json") or {}
    prop = {r["package"]: r for r in (load(run / "propose" / "summary.json") or {"packages": []})["packages"]}
    fb = {r["package"]: r for r in (load(run / "feedback" / "summary.json") or {"packages": []})["packages"]}
    ass = load(run / "assess" / "assess.json")
    # The results file is the truth: one row per execute/<package>/results.json, however the package name nests.
    rows = []
    for res_path in sorted((run / "execute").rglob("results.json")) if (run / "execute").is_dir() else []:
        pkg = str(res_path.parent.relative_to(run / "execute"))
        res = load(res_path) or {}
        e = res.get("counts", {})
        target = (res.get("target") or {}).get("class", "-")
        mut = load(run / "execute" / pkg / "mutation" / "mutation.json") or {}
        udlm_dir = run / "attest" / pkg / "udlm"
        records = "-"
        if udlm_dir.is_dir():
            import yaml
            records = sum(sum(1 for d in yaml.safe_load_all(f.read_text()) if d) for f in udlm_dir.glob("*.yaml"))
        fbp = load(run / "feedback" / pkg / "acceptance.json") or {}
        rows.append({
            "run": f"{run.parent.name}/{run.name}", "package": pkg, "ecosystem": wl.get("ecosystem", "python"), "mode": wl.get("mode"),
            "target": target, "model": (gen.get("model") or "-"),
            "tests": e.get("total", 0), "pass_on_head": e.get("pass_on_new", 0), "proven": e.get("fix_pinning_confirmed", 0),
            "accepted": tri.get(pkg, {}).get("tests_accept", "-"),
            "mutation": (f"{mut['score']:.2f} ({mut.get('killed')}/{mut.get('valid', mut.get('sampled'))})" if mut.get("status") == "ran" and mut.get("score") is not None else ("n/a" if mut.get("status") == "skipped" else "-")),
            "records": records, "signed": "yes" if att.get(pkg, {}).get("result") == "PASSED" else "-",
            "goals": f"{ass['summary']['met']} met" if ass else "-",
            "proposed": "PR" if prop.get(pkg, {}).get("pull_request") else ("branch" if prop.get(pkg, {}).get("branch") else "-"),
            "accepted_by_review": (f"{fbp['counts']['accepted'] + fbp['counts']['edited']}/{sum(fbp['counts'].values())}" if fbp.get("counts") else "-"),
        })
    return rows


def main(write: str | None = None) -> str:
    runs = sorted(p for p in EXAMPLES.glob("*/*/") if (p / "intake").is_dir())
    rows = [r for run in runs for r in run_rows(run)]
    hdr = ["Run", "Package", "Lang", "Target", "Model", "Tests", "Pass on head", "Proven", "Accepted", "Mutation", "UDLM records", "Signed", "Goals", "Proposed", "Accepted by review"]
    keys = ["run", "package", "ecosystem", "target", "model", "tests", "pass_on_head", "proven", "accepted", "mutation", "records", "signed", "goals", "proposed", "accepted_by_review"]
    lines = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows:
        cells = [str(r[k]) for k in keys]
        cells[0] = f"[{r['run']}](https://croadfeldt.github.io/ai-test-harness/runs/{r['run']}/)"   # the run's own page, start to finish
        lines.append("| " + " | ".join(cells) + " |")
    totals = {"runs": len({r["run"] for r in rows}), "packages": len(rows), "tests": sum(r["tests"] for r in rows),
              "proven": sum(r["proven"] for r in rows), "accepted": sum(r["accepted"] for r in rows if isinstance(r["accepted"], int)),
              "signed": sum(1 for r in rows if r["signed"] == "yes")}
    doc = f"""# The evidence so far

**For:** anyone deciding whether this is worth their time. Every number below is read from a run's records
under `examples/` by `tools/rollup.py`; nothing here is typed by hand, and a run that lacks a stage shows a dash.

**In plain terms.** {totals['runs']} runs with executed tests, {totals['packages']} package rows, {totals['tests']} generated tests run in a
sealed sandbox, {totals['proven']} tests proving a vulnerability closed or open by failing on the vulnerable version and
passing on the fixed one, {totals['accepted']} tests accepted by triage as candidates, {totals['signed']} signed attestations. "Proven"
counts tests, so one vulnerability may carry two. Mutation is the share of sampled mutants the accepted tests killed,
target 0.6. "Accepted by review" is what a person kept after the harness proposed, from stage 7. Time from
trigger to packet is on each run's own assessment (goal G9), because several of these runs were re-attested
days later and the records would say so.

{chr(10).join(lines)}

How to read any one of these runs, file by file, is in [10-reading-the-artifacts.md](10-reading-the-artifacts.md).
The story behind each run is on its example page: [frc-scheduler-server](../examples/frc-scheduler-server/README.md)
(Python) and [control-plane](../examples/control-plane/README.md) (Go).
"""
    if write:
        Path(write).write_text(doc)
    return doc


if __name__ == "__main__":
    out = main(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--write" else None)
    if len(sys.argv) < 2:
        print(out)
