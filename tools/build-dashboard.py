#!/usr/bin/env python3
"""site/dashboard/index.html: every run the harness made, over time, for three readers. Rendered from the
run indexes and evaluation rows of the example runs and of the runs store (RUNS_STORE or --store), with
the same data the stories and documents 11 and 12 are rendered from, so it cannot disagree with them."""
import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness" / "src"))
from harness.stages.evaluate import aggregate, rows_for, verdict  # noqa: E402
from harness.util import read_json  # noqa: E402

SITE = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else ROOT / "site"
STORE = os.environ.get("RUNS_STORE") or (sys.argv[sys.argv.index("--store") + 1] if "--store" in sys.argv else None)
REPO_URL = os.environ.get("SITE_REPO_URL", "https://github.com/croadfeldt/ai-test-harness/blob/main")


def run_dirs() -> list[tuple[Path, str]]:
    out = [(p, f"examples/{p.parent.name}/{p.name}") for p in sorted((ROOT / "examples").glob("*/*/")) if (p / "run-index.json").exists()]
    if STORE and Path(STORE).is_dir():
        out += [(p, f"store/{p.parent.name}/{p.name}") for p in sorted(Path(STORE).glob("runs/*/*/")) if (p / "run-index.json").exists()]
    return out


def collect() -> dict:
    runs, rows = [], []
    for d, ref in run_dirs():
        idx = read_json(d / "run-index.json")
        pl = read_json(d / "triage" / "pipeline.json") if (d / "triage" / "pipeline.json").exists() else {"findings": []}
        pk = idx.get("packages", [])
        rv = [p.get("review") for p in pk if p.get("review")]
        runs.append({"ref": ref, "run_id": idx.get("run_id"), "repository": idx.get("repository"), "ecosystem": idx.get("ecosystem"), "mode": idx.get("mode"),
                     "started": idx.get("started"), "model": idx.get("model"),
                     "packages": len(pk), "tests_ran": sum((p["tests"].get("ran") or 0) for p in pk), "accepted": sum((p["tests"].get("accepted") or 0) for p in pk),
                     "proven": sum((p["tests"].get("proven") or 0) for p in pk), "goals_met": (idx.get("goals") or {}).get("met"), "goals_total": sum((idx.get("goals") or {}).values()) if idx.get("goals") else None,
                     "pipeline_findings": len(pl.get("findings", [])), "pipeline_security": sum(1 for f in pl.get("findings", []) if f.get("severity") == "security"),
                     "pipeline_rules": sorted({f.get("rule") for f in pl.get("findings", []) if f.get("rule")}),
                     "reviewer_accepted": sum((r.get("accepted") or 0) for r in rv), "reviewer_rejected": sum((r.get("rejected") or 0) for r in rv), "merged": any(r.get("outcome") for r in rv),
                     "page": f"runs/{ref[len('examples/'):]}/index.html" if ref.startswith("examples/") else None})
        # a store entry carries its evaluation rows as published; an example run is read in full
        ev = d / "evaluation.json"
        for r in (read_json(ev).get("rows", []) if ev.exists() else rows_for(d)):
            r["ref"] = ref; rows.append(r)
    agg = aggregate(rows)
    for g in agg:
        g["reads_as"] = verdict(g)
    return {"generated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "runs": sorted(runs, key=lambda r: r.get("started") or ""), "rows": rows, "aggregate": agg}


JS = r'''const D = JSON.parse(document.getElementById('data').textContent);
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function fill(sel, values) { const el = $(sel); [...new Set(values.filter(Boolean))].sort().forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = v; el.appendChild(o); }); el.addEventListener('change', render); }
fill('#f-repo', D.runs.map(r => r.repository)); fill('#f-eco', D.runs.map(r => r.ecosystem)); fill('#f-model', D.runs.map(r => r.model)); fill('#f-set', D.rows.map(r => r.prompt_set));
function pick() { return { repo: $('#f-repo').value, eco: $('#f-eco').value, model: $('#f-model').value, set: $('#f-set').value }; }
function runOk(r, f) { return (!f.repo || r.repository === f.repo) && (!f.eco || r.ecosystem === f.eco) && (!f.model || r.model === f.model); }
function rowOk(r, f) { return (!f.repo || r.run.startsWith('') ) && (!f.eco || r.language === f.eco) && (!f.model || r.model === f.model) && (!f.set || r.prompt_set === f.set); }
function sum(a, k) { return a.reduce((n, x) => n + (x[k] || 0), 0); }
function pill(t, good) { return '<span class="pill ' + (good === true ? 'good' : good === false ? 'warn' : '') + '">' + esc(t) + '</span>'; }
function render() {
  const f = pick(); const runs = D.runs.filter(r => runOk(r, f));
  const rows = D.rows.filter(r => rowOk(r, f) && (!f.repo || runs.some(x => x.run_id === r.run_id)));
  const tiles = [['runs', runs.length, 'runs'], ['tests ran', sum(runs, 'tests_ran'), 'in the sealed sandbox'], ['accepted', sum(runs, 'accepted'), 'by triage'], ['fixes proven', sum(runs, 'proven'), 'fail on vulnerable, pass on fixed'],
                 ['reviewer accepted', sum(runs, 'reviewer_accepted'), 'merged by a person'], ['pipeline findings', sum(runs, 'pipeline_findings'), sum(runs, 'pipeline_security') + ' security-class']];
  $('#tiles').innerHTML = tiles.map(([l, v, s]) => '<div class="tile"><b>' + esc(v) + '</b>' + esc(l) + '<br><span>' + esc(s) + '</span></div>').join('');
  const byMonth = {}; runs.forEach(r => { const m = (r.started || '').slice(0, 7) || 'undated'; const b = byMonth[m] ||= { runs: 0, accepted: 0, proven: 0 }; b.runs++; b.accepted += r.accepted || 0; b.proven += r.proven || 0; });
  const months = Object.keys(byMonth).sort(); const svg = $('#trend'); const W = 800, H = 160, pad = 28; const max = Math.max(1, ...months.map(m => byMonth[m].accepted));
  const bw = months.length ? (W - 2 * pad) / months.length : 0; let out = '';
  months.forEach((m, i) => { const b = byMonth[m]; const x = pad + i * bw; const h1 = (b.accepted / max) * (H - 2 * pad); const h2 = (b.proven / max) * (H - 2 * pad);
    out += `<rect x="${x + bw * .15}" y="${H - pad - h1}" width="${bw * .35}" height="${h1}" fill="var(--accent-soft)" stroke="var(--accent)"/>`;
    out += `<rect x="${x + bw * .5}" y="${H - pad - h2}" width="${bw * .35}" height="${h2}" fill="var(--accent)"/>`;
    out += `<text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle">${esc(m)} · ${b.runs} run${b.runs === 1 ? '' : 's'}</text>`;
    out += `<text x="${x + bw / 2}" y="${H - pad - Math.max(h1, h2) - 4}" text-anchor="middle">${b.accepted} accepted, ${b.proven} proven</text>`; });
  svg.innerHTML = out || '<text x="400" y="80" text-anchor="middle">no runs match</text>';
  const agg = {}; rows.forEach(r => { const k = [r.prompt_set, r.model, r.language, r.package].join('|'); const g = agg[k] ||= { prompt_set: r.prompt_set, model: r.model, language: r.language, package: r.package, runs: 0, kept: 0, accepted: 0, for_review: 0, proven: 0, cov: [], mut: [], ra: 0, rr: 0, calls: 0, minutes: 0 };
    g.runs++; g.kept += r.kept || 0; g.accepted += r.accepted || 0; g.for_review += r.for_review || 0; g.proven += r.proven || 0; if (r.covered_lines != null) g.cov.push(r.covered_lines); if (r.mutation_score != null) g.mut.push(r.mutation_score); g.ra += r.reviewer_accepted || 0; g.rr += r.reviewer_rejected || 0; g.calls += r.model_calls || 0; g.minutes += r.minutes || 0; });
  const reads = g => g.ra ? 'accepted by a reviewer' : g.proven ? 'proves fixes' : g.accepted ? 'characterizes' : g.for_review ? 'finds behaviour changes' : g.kept ? 'not fit: none accepted' : 'not fit';
  $('#eval tbody').innerHTML = Object.values(agg).sort((a, b) => (a.language + a.package + a.model + a.prompt_set).localeCompare(b.language + b.package + b.model + b.prompt_set)).map(g => '<tr><td>' + esc(g.prompt_set) + '</td><td>' + esc(g.model) + '</td><td>' + esc(g.language) + '</td><td>' + esc(g.package) + '</td><td>' + g.runs + '</td><td>' + g.kept + '</td><td>' + g.accepted + '</td><td>' + g.for_review + '</td><td>' + g.proven + '</td><td>' + (g.cov.length ? Math.round(g.cov.reduce((a, b) => a + b, 0) / g.cov.length) : '-') + '</td><td>' + (g.mut.length ? (g.mut.reduce((a, b) => a + b, 0) / g.mut.length).toFixed(2) : '-') + '</td><td>' + (g.ra || g.rr ? g.ra + ' / ' + g.rr : 'no review yet') + '</td><td>' + g.calls + '</td><td>' + g.minutes.toFixed(1) + '</td><td>' + pill(reads(g), g.ra || g.proven ? true : g.accepted || g.for_review ? null : false) + '</td></tr>').join('') || '<tr><td colspan="15">no package runs match</td></tr>';
  $('#pipe tbody').innerHTML = runs.filter(r => r.pipeline_findings != null && r.pipeline_rules.length).map(r => '<tr><td>' + esc(r.repository) + '</td><td>' + (r.page ? '<a href="../' + esc(r.page) + '">' + esc(r.run_id) + '</a>' : esc(r.run_id)) + '</td><td>' + esc((r.started || '').slice(0, 10)) + '</td><td>' + r.pipeline_findings + '</td><td>' + r.pipeline_security + '</td><td>' + esc(r.pipeline_rules.join(', ')) + '</td></tr>').join('') || '<tr><td colspan="6">no pipeline findings in the runs that match (runs before the pipeline questions were asked carry none)</td></tr>';
  $('#runs tbody').innerHTML = runs.slice().reverse().map(r => '<tr><td>' + esc((r.started || '').slice(0, 16).replace('T', ' ')) + '</td><td>' + (r.page ? '<a href="../' + esc(r.page) + '">' + esc(r.repository) + '</a>' : esc(r.repository)) + '</td><td>' + esc(r.ecosystem) + '</td><td>' + esc(r.mode) + '</td><td>' + esc(r.model) + '</td><td>' + r.packages + '</td><td>' + r.tests_ran + '</td><td>' + r.accepted + '</td><td>' + r.proven + '</td><td>' + (r.goals_met != null ? r.goals_met + ' of ' + r.goals_total : '-') + '</td><td>' + r.pipeline_findings + '</td><td>' + (r.merged ? pill('merged', true) : '') + '</td></tr>').join('');
}
render();
'''


def page(data: dict) -> str:
    css = (ROOT / "tools" / "site.css").read_text()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Test Harness dashboard</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@500;700;900&family=Red+Hat+Text:ital,wght@0,400;0,500;1,400&family=Red+Hat+Mono&display=swap">
<style>{css}
.dash {{ padding: 2rem 2.5rem; max-width: 80rem; }}
.dash h1 {{ font-family: var(--display); margin: 0 0 .25rem; }}
.dash h2 {{ font-family: var(--display); margin: 2rem 0 .5rem; }}
.who {{ color: var(--muted); font-size: .9rem; margin: 0 0 1rem; }}
.filters {{ display: flex; flex-wrap: wrap; gap: .75rem; margin: 1rem 0; align-items: end; }}
.filters label {{ font-size: .75rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); display: grid; gap: .25rem; }}
.filters select {{ font: inherit; padding: .3rem .5rem; border: 1px solid var(--rule); border-radius: 4px; background: var(--ground); color: var(--ink); }}
.tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); gap: .75rem; }}
.tile {{ border: 1px solid var(--rule); border-radius: 4px; padding: .9rem 1rem; background: var(--panel); }}
.tile b {{ display: block; font-family: var(--display); font-size: 1.8rem; font-variant-numeric: tabular-nums; }}
.tile span {{ font-size: .8rem; color: var(--muted); }}
.chart {{ width: 100%; height: 12rem; margin: .5rem 0 0; }}
.chart text {{ font-size: .65rem; fill: var(--muted); font-family: var(--mono); }}
.tbl {{ overflow-x: auto; }}
table.res {{ border-collapse: collapse; width: 100%; font-size: .85rem; }}
table.res th, table.res td {{ border-bottom: 1px solid var(--rule); padding: .4rem .6rem; text-align: left; vertical-align: top; font-variant-numeric: tabular-nums; }}
table.res th {{ font-weight: 500; color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; }}
.pill {{ display: inline-block; padding: .05rem .5rem; border-radius: 999px; font-family: var(--mono); font-size: .72rem; border: 1px solid var(--rule); }}
.pill.good {{ background: var(--accent-soft); border-color: var(--accent); }}
.pill.warn {{ background: var(--human-soft); border-color: var(--human); }}
.foot {{ color: var(--muted); font-size: .8rem; margin-top: 2rem; }}
@media (max-width: 700px) {{ .dash {{ padding: 1rem; }} }}
</style></head><body><main class="dash" id="main">
<div class="eyebrow"><a href="../index.html">AI Test Harness</a> · <a href="../runs/index.html">Every run</a></div>
<h1>Dashboard</h1>
<p class="who">Every run the harness has made, from the example runs in the repository and the runs store. Rendered from the same run indexes the stories are written from. Generated {html.escape(data['generated'])}.</p>
<div class="filters">
  <label>Repository <select id="f-repo"><option value="">all</option></select></label>
  <label>Language <select id="f-eco"><option value="">all</option></select></label>
  <label>Model <select id="f-model"><option value="">all</option></select></label>
  <label>Prompt set <select id="f-set"><option value="">all</option></select></label>
</div>
<h2>For leadership: what went through, what was proven, what a person acted on</h2>
<div class="tiles" id="tiles"></div>
<svg class="chart" id="trend" viewBox="0 0 800 160" preserveAspectRatio="none" role="img" aria-label="runs, accepted tests and proven fixes by month"></svg>
<h2>For engineering: which model and prompt set is fit for which job</h2>
<div class="tbl"><table class="res" id="eval"><thead><tr><th>Prompt set</th><th>Model</th><th>Language</th><th>Package</th><th>Runs</th><th>Kept</th><th>Accepted</th><th>For review</th><th>Proven</th><th>Covered lines</th><th>Mutation</th><th>Reviewer accepted / rejected</th><th>Calls</th><th>Minutes</th><th>Reads as</th></tr></thead><tbody></tbody></table></div>
<h2>For pipeline owners: what the harness found about the CI it ran in</h2>
<div class="tbl"><table class="res" id="pipe"><thead><tr><th>Repository</th><th>Run</th><th>Started</th><th>Findings</th><th>Security</th><th>Rules</th></tr></thead><tbody></tbody></table></div>
<h2>Every run</h2>
<div class="tbl"><table class="res" id="runs"><thead><tr><th>Started</th><th>Repository</th><th>Language</th><th>Mode</th><th>Model</th><th>Packages</th><th>Tests ran</th><th>Accepted</th><th>Proven</th><th>Goals met</th><th>Pipeline findings</th><th>Reviewed</th></tr></thead><tbody></tbody></table></div>
<p class="foot">Rendered by <code>tools/build-dashboard.py</code>. A run reaches this page through <code>harness publish</code> into the runs store, or by being kept under <code>examples/</code>. Nothing here is computed that a run's own files do not hold.</p>
<script id="data" type="application/json">{json.dumps(data).replace('</', '<\\/')}</script>
<script>
""" + JS + """</script>
</main></body></html>"""


def main() -> Path:
    data = collect()
    out = SITE / "dashboard" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(data))
    (SITE / "dashboard" / "data.json").write_text(json.dumps(data, indent=1))
    print(f"wrote {out}: {len(data['runs'])} runs, {len(data['rows'])} package runs")
    return out


if __name__ == "__main__":
    main()
