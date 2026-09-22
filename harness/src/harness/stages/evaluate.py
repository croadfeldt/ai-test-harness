"""Fitness for purpose, measured: the same jobs, run per prompt set and per model, scored by what the
sandbox and the reviewers said. A model or a prompt is never assumed to be good enough; this table is
where it proves it. Reads finished run directories, writes evaluation.json and evaluation.md.

Ground truth, in order of strength: a reviewer's decision on the test pull request (stage 7), the
sandbox's verdicts (fix-pinning confirmed, pass on head, mutation kills), triage's acceptance. Cost:
model calls and wall-clock minutes from the manifests.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..util import now_iso, read_json, write_json

COLUMNS = ["prompt set", "model", "language", "package", "runs", "generated", "kept", "accepted", "proven", "pass on head",
           "mutation score", "reviewer accepted", "reviewer rejected", "model calls", "minutes"]


def _minutes(gen_dir: Path) -> float:
    total = 0.0
    for f in gen_dir.glob("model-calls/*.json"):
        try:
            rec = read_json(f)
        except Exception:
            continue
        if isinstance(rec, dict):
            total += float(rec.get("latency_s") or 0)
    return round(total / 60, 1)


def rows_for(run: Path) -> list[dict]:
    idx_path = run / "run-index.json"
    if not idx_path.exists():
        return []
    idx = read_json(idx_path)
    out = []
    for p in idx.get("packages", []):
        if "generate/manifest.json" not in p.get("files", {}):
            continue
        m = read_json(run / p["files"]["generate/manifest.json"])
        ps = m.get("prompt_set") or {"name": "v1 (unrecorded)", "digest": None}
        t = p.get("tests") or {}; mut = p.get("mutation") or {}; rv = p.get("review") or {}
        calls = len(list((run / "generate" / p["package"] / "model-calls").glob("*.json")))
        out.append({"prompt_set": ps.get("name"), "prompt_digest": ps.get("digest"), "model": (m.get("model") or {}).get("id") or idx.get("model"),
                    "endpoint": (m.get("model") or {}).get("endpoint"), "language": idx.get("ecosystem"), "package": p["package"], "run": run.name,
                    "run_id": idx.get("run_id"), "mode": m.get("mode"),
                    "generated": t.get("generated") or 0, "kept": t.get("ran") or 0, "accepted": t.get("accepted") or 0, "proven": t.get("proven") or 0,
                    "pass_on_head": t.get("pass_on_head") or 0, "mutation_score": mut.get("score"),
                    "reviewer_accepted": rv.get("accepted"), "reviewer_rejected": rv.get("rejected"), "reviewer_edited": rv.get("edited"),
                    "model_calls": calls, "minutes": _minutes(run / "generate" / p["package"])})
    return out


def aggregate(rows: list[dict]) -> list[dict]:
    """One line per prompt set, model, language and package, summed over runs; ratios recomputed."""
    groups: dict[tuple, dict] = {}
    for r in rows:
        k = (r["prompt_set"], r["model"], r["language"], r["package"])
        g = groups.setdefault(k, {"prompt_set": k[0], "model": k[1], "language": k[2], "package": k[3], "runs": 0, "generated": 0, "kept": 0, "accepted": 0,
                                  "proven": 0, "pass_on_head": 0, "mutation": [], "reviewer_accepted": 0, "reviewer_rejected": 0, "model_calls": 0, "minutes": 0.0,
                                  "run_names": []})
        g["runs"] += 1; g["run_names"].append(r["run"])
        for f in ("generated", "kept", "accepted", "proven", "pass_on_head", "model_calls"):
            g[f] += r[f] or 0
        g["minutes"] = round(g["minutes"] + (r["minutes"] or 0), 1)
        if r["mutation_score"] is not None:
            g["mutation"].append(r["mutation_score"])
        g["reviewer_accepted"] += r["reviewer_accepted"] or 0
        g["reviewer_rejected"] += r["reviewer_rejected"] or 0
    out = []
    for g in groups.values():
        g["mutation_score"] = round(sum(g["mutation"]) / len(g["mutation"]), 2) if g["mutation"] else None
        del g["mutation"]
        out.append(g)
    return sorted(out, key=lambda g: (g["language"], g["package"], g["model"], g["prompt_set"]))


def verdict(g: dict) -> str:
    """Fit for purpose on this package, in one phrase: what the numbers say, not a guess."""
    if g["reviewer_accepted"]:
        return f"accepted by a reviewer: {g['reviewer_accepted']} tests"
    if g["proven"]:
        return f"proves fixes: {g['proven']} fix-pinning confirmed"
    if g["accepted"]:
        return f"characterizes: {g['accepted']} tests accepted by triage, nothing proven"
    if g["kept"]:
        return "not fit: tests ran, none accepted"
    if g["generated"]:
        return "not fit: nothing survived the baseline"
    return "not fit: nothing generated"


def to_markdown(agg: list[dict], rows: list[dict]) -> str:
    lines = ["# Prompt and model evaluation", "",
             "Fitness for purpose is measured, never assumed. Each line is one prompt set with one model on one package, summed over the runs that",
             "used them. Ground truth in order of strength: a reviewer's decision on the test pull request, the sandbox's verdicts (a fix proven means",
             "the test fails on the vulnerable version and passes on the fixed one), triage's acceptance. Cost is model calls and minutes of model time.", "",
             f"Generated {now_iso()} from {len(rows)} package run(s).", "",
             "| Prompt set | Model | Language | Package | Runs | Generated | Kept | Accepted | Proven | Mutation | Reviewer accepted / rejected | Calls | Minutes | Reads as |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in agg:
        rv = f"{g['reviewer_accepted']} / {g['reviewer_rejected']}" if (g["reviewer_accepted"] or g["reviewer_rejected"]) else "no review yet"
        lines.append(f"| {g['prompt_set']} | {g['model']} | {g['language']} | {g['package']} | {g['runs']} | {g['generated']} | {g['kept']} | {g['accepted']} | {g['proven']} | "
                     f"{g['mutation_score'] if g['mutation_score'] is not None else '-'} | {rv} | {g['model_calls']} | {g['minutes']} | {verdict(g)} |")
    lines += ["", "## The runs behind each line", "", "| Run | Prompt set (digest) | Model | Package | Generated | Kept | Accepted | Proven |", "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["language"], r["package"], r["model"], r["run"])):
        lines.append(f"| {r['run']} | {r['prompt_set']} ({(r['prompt_digest'] or 'none')[:19]}) | {r['model']} | {r['package']} | {r['generated']} | {r['kept']} | {r['accepted']} | {r['proven']} |")
    lines += ["", "A prompt set or a model that does not reach the outcome a package needs (a proven fix for an advisory, an accepted characterization",
              "otherwise) is not fit for that purpose, whatever it scores elsewhere. The harness records the set's name and digest in every manifest,",
              "so any line here can be traced to the exact words and the exact model that produced it.", ""]
    return "\n".join(lines)


def evaluate(runs: list[Path], out: Path) -> dict:
    rows = [r for run in runs for r in rows_for(run)]
    agg = aggregate(rows)
    out.mkdir(parents=True, exist_ok=True)
    rec = {"generated": now_iso(), "runs": [str(r) for r in runs], "rows": rows, "aggregate": agg}
    write_json(out / "evaluation.json", rec)
    (out / "evaluation.md").write_text(to_markdown(agg, rows))
    return rec
