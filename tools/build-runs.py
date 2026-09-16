#!/usr/bin/env python3
"""One page per run, rendered from the run's records: the process from start to finish (what each stage
read, did and wrote), the results per package, the assessment, and every artifact behind it, linked to
the repository. Plus an index of runs. Everything rendered is escaped; nothing from a record is treated
as markup. Called by build-site.py; `python3 tools/build-runs.py [site-dir]` builds it alone."""
import html
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness" / "src"))
from harness import story as story_mod  # noqa: E402
EXAMPLES = ROOT / "examples"
SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site"
REPO_URL = os.environ.get("SITE_REPO_URL", "https://github.com/croadfeldt/ai-test-harness/blob/main")
CSS = (ROOT / "tools" / "site.css").read_text() + """
.run-hero { padding: 2.25rem 2.5rem 1rem; }
.facts { display: flex; flex-wrap: wrap; gap: .5rem 1.5rem; font-family: var(--mono); font-size: .8rem; color: var(--muted); }
.facts b { color: var(--ink); font-weight: 500; }
.verdict { background: var(--accent-soft); border-left: 4px solid var(--accent); padding: 1rem 1.25rem; margin: 1rem 2.5rem; border-radius: 0 4px 4px 0; }
.timeline { list-style: none; margin: 0; padding: 0 2.5rem; display: grid; gap: .75rem; }
.stage { display: grid; grid-template-columns: 6.5rem minmax(0, 1fr); gap: 1rem; border: 1px solid var(--rule); border-radius: 4px; padding: .9rem 1.1rem; background: var(--panel); }
.stage.absent { opacity: .55; }
.stage-id { font-family: var(--display); font-weight: 700; font-size: .95rem; }
.stage-id small { display: block; font-family: var(--mono); font-weight: 400; font-size: .7rem; color: var(--muted); }
.stage-body { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: .75rem 1.25rem; }
.stage-body h4 { margin: 0 0 .25rem; font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; color: var(--accent-ink); font-weight: 500; }
.stage-body p, .stage-body ul { margin: 0; font-size: .9rem; }
.stage-body ul { padding-left: 1.1rem; }
.pkg { padding: 0 2.5rem; margin-top: 2rem; }
.pkg h2 { font-family: var(--display); }
.tbl { overflow-x: auto; }
table.res { border-collapse: collapse; width: 100%; font-size: .85rem; }
table.res th, table.res td { border-bottom: 1px solid var(--rule); padding: .4rem .6rem; text-align: left; vertical-align: top; }
table.res th { font-weight: 500; color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; }
.pill { display: inline-block; padding: .05rem .5rem; border-radius: 999px; font-family: var(--mono); font-size: .72rem; border: 1px solid var(--rule); }
.pill.good { background: var(--accent-soft); border-color: var(--accent); }
.pill.warn { background: var(--human-soft); border-color: var(--human); }
.artifacts { padding: 0 2.5rem 2.5rem; columns: 2; column-gap: 2rem; font-size: .85rem; }
.artifacts h3 { break-after: avoid; font-size: .8rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 1rem 0 .25rem; }
.artifacts ul { margin: 0; padding-left: 1rem; }
details summary { cursor: pointer; }
.story { padding: 0 2.5rem; }
.story h2 { font-family: var(--display); margin-top: 2rem; }
.story table.res td:first-child { white-space: nowrap; font-weight: 500; }
.story ul { padding-left: 1.2rem; }
.story li { margin: .3rem 0; }
.five td:first-child { width: 5rem; color: var(--accent-ink); font-family: var(--display); font-weight: 700; }
.catalogue h3 { font-size: .8rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 1.25rem 0 .25rem; }
.catalogue li { margin: .2rem 0; }
.catalogue code { font-size: .8rem; }
pre.rec { background: var(--code-bg); padding: .75rem; overflow-x: auto; font-size: .75rem; }
@media (max-width: 700px) { .stage { grid-template-columns: 1fr; } .artifacts { columns: 1; } .run-hero, .timeline, .pkg, .artifacts { padding-left: 1rem; padding-right: 1rem; } .verdict { margin: 1rem; } }
"""
e = html.escape


def load(p: Path):
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except json.JSONDecodeError:
        return None


def link(run_rel: str, path: str, text: str | None = None) -> str:
    return f'<a href="{e(REPO_URL)}/examples/{e(run_rel)}/{e(path)}"><code>{e(text or path)}</code></a>'


def plain_terms(md: str) -> str:
    m = re.search(r"\*\*In plain terms\.\*\*\s*(.+?)(?:\n\n|\Z)", md, re.S)
    return (m.group(1) if m else md.strip().splitlines()[0]).strip()


def pill(text, good=None):
    cls = "good" if good is True else ("warn" if good is False else "")
    return f'<span class="pill {cls}">{e(str(text))}</span>'


def verify_statement(run: Path, pkg: str) -> str:
    env, pub = run / "attest" / pkg / "statement.dsse.json", run / "attest" / pkg / "signer.pub.pem"
    if not (env.exists() and pub.exists()):
        return "no envelope"
    try:
        from harness.stages.attest import verify
        return "verified at build" if verify(env, pub) else "signature did not verify"
    except Exception as ex:  # cryptography missing on the build machine, for instance
        return f"not checked at build ({type(ex).__name__})"


STAGE_TEXT = {
    "selfcheck": ("0", "Self-verification", "the harness's own code and the failure register"),
    "intake": ("1", "Intake", "the repository at base and head, its dependency manifest"),
    "analyze": ("2", "Analysis", "the work list; package source, advisories, the application's call sites"),
    "generate": ("3", "Generation", "the fact bundle per package; the model; the sealed sandbox for baseline runs"),
    "execute": ("4", "Validation execution", "the candidate tests; the environments at head, base or the fixed candidate"),
    "triage": ("5", "Triage", "every verdict and finding from stage 4"),
    "packet": ("6", "Packet", "triage, the tests, the advisories"),
    "attest": ("attest", "Attestation", "the manifest, the tests, the results; UDLM's chain code"),
    "assess": ("assess", "Assessment", "every record the run wrote, against the blueprint's goals"),
    "propose": ("propose", "Test pull request", "the packet and the records"),
    "feedback": ("7", "Feedback", "the pull request as a person decided it"),
}


def inline(text: str) -> str:
    out = e(str(text))
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    return re.sub(r"(https?://[^\s)]+)", r'<a href="\1">\1</a>', out)


def story_section(sec: dict, rel: str, cls: str = "") -> str:
    parts = [f'<h2>{e(sec["title"])}</h2>']
    parts += [f"<p>{inline(x)}</p>" for x in sec.get("paragraphs", [])]
    if sec.get("bullets"):
        parts.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in sec["bullets"]) + "</ul>")
    if sec.get("table"):
        cols = sec["table"]["columns"]
        head = "".join(f"<th>{e(c)}</th>" for c in cols) if any(cols) else ""
        body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in sec["table"]["rows"])
        parts.append(f'<div class="tbl"><table class="res {cls}">{("<tr>" + head + "</tr>") if head else ""}{body}</table></div>')
    for g in sec.get("groups", []):
        parts.append(f"<h3>{e(g['title'])}</h3><ul>" + "".join(f"<li>{link(rel, path)}: {e(why)}</li>" for path, why in g["items"]) + "</ul>")
    return "".join(parts)


def story_blocks(st: dict, rel: str) -> dict[str, str]:
    """The story's sections rendered to HTML, keyed by title, so the page can place them."""
    out = {}
    for sec in st["sections"]:
        cls = "five" if sec["title"].startswith("Who, what") else ""
        out[sec["title"]] = story_section(sec, rel, cls)
    return out


def stage_cards(idx: dict, run: Path, rel: str) -> str:
    st = idx["stages"]; pk = idx["packages"]
    cards = []
    for key, (num, name, reads) in STAGE_TEXT.items():
        s = st.get(key, {}); present = s.get("present"); sm = s.get("summary") or {}
        did, wrote = [], []
        if key == "selfcheck" and present:
            did.append(f"{sm.get('checks')} register checks, {'all passed' if sm.get('passed') else 'a failure stopped the run'}; sandbox probe {sm.get('sandbox')}; model probe {sm.get('model')}.")
            wrote.append(link(rel, "selfcheck/selfcheck.json"))
        elif key == "intake" and present:
            did.append(f"Resolved {sm.get('packages_at_head')} packages at head and {sm.get('packages_at_base')} at base with {e(str(sm.get('resolver') or ''))}; "
                       f"looked every version up in OSV: {sm.get('with_advisories_at_head')} with advisories at head; {sm.get('changed')} changed; work list of {sm.get('work_list_rows')} rows.")
            wrote += [link(rel, "intake/worklist.json"), link(rel, "intake/graph.new.json"), link(rel, "intake/sbom.new.cdx.json"), link(rel, "intake/vulns.json")]
        elif key == "analyze" and present:
            rows = load(run / "analyze" / "summary.json") or {}
            items = [i for i in rows.get("items", []) if any(p["package"] == i["package"] for p in pk)]
            did.append(f"{len(items)} package(s) analyzed: " + "; ".join(f"{e(i['package'])} score {i['score']}, budget {i['budget']}, {i['vulns']} advisories, {i['breaking']} breaking changes" for i in items) + ".")
            wrote += [link(rel, f"analyze/{p['package']}/facts.json") for p in pk]
        elif key == "generate" and present:
            did.append(f"Model {e(str(sm.get('model') or (idx.get('model') or '')))}, mode {e(str(sm.get('mode') or idx.get('generation_mode') or ''))}.")
            for p in [q for q in pk if "generate/manifest.json" in q["files"]]:
                m = load(run / "generate" / p["package"] / "manifest.json") or {}
                calls = len(list((run / "generate" / p["package"] / "model-calls").glob("*.prompt.md"))) + len(list((run / "generate" / p["package"] / "model-calls").glob("*.messages.json")))
                kept = sum(len(f.get("tests", [])) for f in m.get("files", []))
                disc = "; ".join(f"{d.get('category')}{(' ' + d['issue']) if d.get('issue') else ''}: {d.get('reason')}" for d in m.get("discarded", []))
                did.append(f"{e(p['package'])}: {kept} tests kept in {len(m.get('files', []))} file(s), {calls} model calls" + (f"; discarded: {e(disc)}" if disc else "") + ".")
                wrote += [link(rel, f"generate/{p['package']}/manifest.json"), link(rel, f"generate/{p['package']}/tests/", "tests/"), link(rel, f"generate/{p['package']}/model-calls/", "model-calls/")]
        elif key == "execute" and present:
            for p in [q for q in pk if "execute/results.json" in q["files"]]:
                r = load(run / "execute" / p["package"] / "results.json") or {}
                c = r.get("counts", {}); runs = ", ".join(r.get("runs", {}).keys()); tg = r.get("target", {})
                did.append(f"{e(p['package'])}: sandbox runs {e(runs)} on {e(str(tg.get('class')))} (image {e(str(tg.get('image_digest') or 'digest not recorded'))[:26]}); "
                           f"{c.get('total')} tests, {c.get('pass_on_new')} pass on head, {c.get('flaky')} flaky, {c.get('fix_pinning_confirmed')} fix-pinning confirmed; "
                           f"{r.get('coverage_summary', {}).get('covered_lines_in_target')} lines of the package covered.")
                mut = load(run / "execute" / p["package"] / "mutation" / "mutation.json") or {}
                if mut.get("status") == "ran":
                    did.append(f"Mutation: {mut.get('sites')} sites on executed lines, {mut.get('sampled')} sampled, {mut.get('killed')} killed, score {mut.get('score')}.")
                elif mut:
                    did.append(f"Mutation: {e(str(mut.get('status')))}, {e(str(mut.get('reason') or ''))}.")
                rv = load(run / "execute" / p["package"] / "relevance.json") or {}
                if rv:
                    did.append(f"Relevance: {rv.get('examined', {}).get('generated')} generated and {rv.get('examined', {}).get('application')} application tests examined; "
                               f"{rv.get('counts', {}).get('obsolete')} obsolete, {rv.get('counts', {}).get('redundant')} redundant proposed, horizon {e(str(rv.get('horizon')))}.")
                wrote += [link(rel, f"execute/{p['package']}/results.json"), link(rel, f"execute/{p['package']}/new/", "new/"), link(rel, f"execute/{p['package']}/mutation/mutation.json"), link(rel, f"execute/{p['package']}/relevance.json")]
        elif key == "triage" and present:
            for p in [q for q in pk if "triage/triage.json" in q["files"]]:
                t = load(run / "triage" / p["package"] / "triage.json") or {}; sm2 = t.get("summary", {})
                did.append(f"{e(p['package'])}: {sm2.get('findings')} findings, {sm2.get('tests_accept')} tests to accept, {sm2.get('tests_discard_or_regenerate')} to discard or regenerate, {sm2.get('escalated')} escalated to a person (threshold {t.get('threshold')}).")
                wrote.append(link(rel, f"triage/{p['package']}/triage.json"))
        elif key == "packet" and present:
            for p in [q for q in pk if "packet/packet.json" in q["files"]]:
                pj = load(run / "packet" / p["package"] / "packet.json") or {}
                did.append(f"{e(p['package'])}: {len(pj.get('tests_in_patch', []))} accepted tests in the patch; VEX drafts {e(json.dumps(pj.get('vex_statements', {})))}.")
                wrote += [link(rel, f"packet/{p['package']}/packet.md"), link(rel, f"packet/{p['package']}/tests.patch"), link(rel, f"packet/{p['package']}/vex.openvex.json")]
        elif key == "attest" and present:
            for p in [q for q in pk if "attest/attest.json" in q["files"]]:
                a = load(run / "attest" / p["package"] / "attest.json") or {}; u = load(run / "attest" / p["package"] / "udlm" / "index.json") or {}
                did.append(f"{e(p['package'])}: {a.get('records')} provenance records; statement {e(str(a.get('result')))}, key {e(str(a.get('keyid') or ''))[:19]}, {e(verify_statement(run, p['package']))}; "
                           f"UDLM records {'sealed' if u.get('sealed') else 'unsealed'}, schema problems {(u.get('schema_validation') or {}).get('count', 'not checked')}.")
                wrote += [link(rel, f"attest/{p['package']}/statement.dsse.json"), link(rel, f"attest/{p['package']}/MANIFEST.json"), link(rel, f"attest/{p['package']}/udlm/", "udlm/")]
        elif key == "assess" and present:
            did.append(f"{sm.get('met')} goals met, {sm.get('not_met')} not met, {sm.get('not_applicable')} not applicable, {sm.get('other')} measured without a target.")
            wrote.append(link(rel, "assess/assess.md"))
        elif key == "propose" and present:
            for p in [q for q in pk if "propose/proposal.json" in q["files"]]:
                pr = load(run / "propose" / p["package"] / "proposal.json") or {}
                did.append(f"{e(p['package'])}: {e(str(pr.get('status')))}; branch {e(str(pr.get('branch') or ''))}, {len(pr.get('files', []))} files, commit {'signed' if pr.get('signed') else 'unsigned'}"
                           + (f"; <a href=\"{e(pr['pull_request'])}\">{e(pr['pull_request'])}</a>" if pr.get("pull_request") else "") + ".")
                wrote.append(link(rel, f"propose/{p['package']}/proposal.json"))
        elif key == "feedback" and present:
            for p in [q for q in pk if "feedback/acceptance.json" in q["files"]]:
                f = load(run / "feedback" / p["package"] / "acceptance.json") or {}; c = f.get("counts", {})
                did.append(f"{e(p['package'])}: {e(str(f.get('outcome')))}; {c.get('accepted')} accepted, {c.get('edited')} edited, {c.get('rejected')} rejected; "
                           f"{(f.get('records') or {}).get('requested_and_realized', 0)} requested and realized records; acceptance statement signed.")
                wrote += [link(rel, f"feedback/{p['package']}/acceptance.json"), link(rel, f"feedback/{p['package']}/decisions.jsonl")]
        if not present:
            did.append("did not run in this run.")
        cards.append(f'<li class="stage{"" if present else " absent"}"><div class="stage-id">{e(name)}<small>stage {e(num)}</small></div><div class="stage-body">'
                     f'<div><h4>Read</h4><p>{e(reads)}</p></div><div><h4>Did</h4><ul>{"".join(f"<li>{d}</li>" for d in did)}</ul></div>'
                     f'<div><h4>Wrote</h4><p>{" · ".join(wrote) or "nothing"}</p></div></div></li>')
    return "".join(cards)


def package_sections(idx: dict, run: Path, rel: str) -> str:
    out = []
    for p in [q for q in idx["packages"] if "execute/results.json" in q["files"]]:
        pkg = p["package"]
        t = load(run / "triage" / pkg / "triage.json") or {}
        r = load(run / "execute" / pkg / "results.json") or {}
        by_name = {x["name"]: x for x in r.get("tests", [])}
        rows = []
        for x in t.get("tests", []) or [{"name": y["name"], "category": y["category"], "versions": y["versions"], "verdict": y["verdict"], "class": "", "action": ""} for y in r.get("tests", [])]:
            v = x.get("versions", {})
            rows.append(f"<tr><td><code>{e(x['name'])}</code></td><td>{e(str(x.get('category')))}</td><td>{pill(v.get('old', '-'))}</td><td>{pill(v.get('new', '-'), v.get('new') == 'pass')}</td>"
                        f"<td>{e(str(x.get('verdict') or by_name.get(x['name'], {}).get('verdict', '')))}</td><td>{e(str(x.get('action') or ''))}</td></tr>")
        findings = "".join(f"<tr><td>{pill(f.get('class'))}</td><td>{f.get('confidence')}</td><td>{e(str(f.get('summary')))}</td><td>{e(str(f.get('routing')))}</td></tr>" for f in t.get("findings", []))
        vex = load(run / "packet" / pkg / "vex.openvex.json") or {}
        vex_rows = "".join(f"<tr><td>{e(', '.join(a for a in s.get('vulnerability', {}).get('aliases', []) if a.startswith('CVE-')) or s.get('vulnerability', {}).get('name', ''))}</td>"
                           f"<td>{pill(s.get('status'), s.get('status') == 'fixed')}</td><td>{e(str(s.get('status_notes') or ''))[:200]}</td></tr>" for s in vex.get("statements", []))
        mut = load(run / "execute" / pkg / "mutation" / "mutation.json") or {}
        mut_rows = "".join(f"<tr><td><code>{e(tn)}</code></td><td>{len(d.get('killed', []))}</td><td>{len(d.get('unique', []))}</td></tr>" for tn, d in (mut.get("per_test") or {}).items())
        rv = load(run / "execute" / pkg / "relevance.json") or {}
        rv_rows = "".join(f"<tr><td><code>{e(q['test'])}</code></td><td>{e(q['reason'])}</td><td>{e(q['text'])}</td></tr>" for q in rv.get("proposals", []))
        m = load(run / "generate" / pkg / "manifest.json") or {}
        disc = "".join(f"<li>{e(str(d.get('category')))}{(' ' + e(d['issue'])) if d.get('issue') else ''}: {e(str(d.get('reason')))}{(' (' + e(str(d.get('last_problem')))[:160] + ')') if d.get('last_problem') else ''}</li>" for d in m.get("discarded", []))
        packet_md = (run / "packet" / pkg / "packet.md").read_text() if (run / "packet" / pkg / "packet.md").exists() else ""
        verdict = f'<div class="verdict"><strong>In plain terms.</strong> {e(plain_terms(packet_md))}</div>' if packet_md else ""
        sec = [f'<section class="pkg" id="pkg-{e(pkg)}"><h2>{e(pkg)} {e(str(p.get("old_version") or ""))} {"→" if p.get("old_version") and p.get("old_version") != p.get("new_version") else ""} {e(str(p.get("new_version") or ""))}</h2>', verdict]
        if rows:
            sec.append(f'<h3>Tests, one row each</h3><div class="tbl"><table class="res"><tr><th>Test</th><th>Category</th><th>Old</th><th>New</th><th>Verdict</th><th>Action</th></tr>{"".join(rows)}</table></div>')
        if findings:
            sec.append(f'<h3>Findings</h3><div class="tbl"><table class="res"><tr><th>Class</th><th>Confidence</th><th>Finding</th><th>Route</th></tr>{findings}</table></div>')
        if vex_rows:
            sec.append(f'<h3>Draft VEX statements, for Product Security</h3><div class="tbl"><table class="res"><tr><th>Vulnerability</th><th>Status</th><th>Basis</th></tr>{vex_rows}</table></div>')
        if mut_rows:
            sec.append(f'<h3>Mutation: which test killed what</h3><p>{mut.get("sites")} sites, {mut.get("sampled")} sampled, {mut.get("killed")} killed, score {mut.get("score")}.</p><div class="tbl"><table class="res"><tr><th>Test</th><th>Mutants killed</th><th>Killed only by this test</th></tr>{mut_rows}</table></div>')
        if rv_rows:
            sec.append(f'<h3>Retirement proposals</h3><div class="tbl"><table class="res"><tr><th>Test</th><th>Reason</th><th>Evidence</th></tr>{rv_rows}</table></div>')
        if disc:
            sec.append(f'<h3>Discarded during generation</h3><ul>{disc}</ul>')
        sec.append("</section>")
        out.append("".join(sec))
    return "".join(out)


def goals_table(run: Path, rel: str) -> str:
    a = load(run / "assess" / "assess.json")
    if not a:
        return ""
    rows = "".join(f"<tr><td>{e(g['id'])}</td><td>{e(g['goal'])}</td><td>{e(str(g['measurement']))[:220]}</td><td>{pill(g['verdict'], g['verdict'].startswith('met'))}</td>"
                   f"<td>{' '.join(link(rel, ref, ref.split('/')[-1]) for ref in g.get('evidence_ref', [])[:2])}</td></tr>" for g in a["goals"])
    return f'<section class="pkg"><h2>The run against the blueprint\'s goals</h2><div class="tbl"><table class="res"><tr><th>Id</th><th>Goal</th><th>Measured</th><th>Verdict</th><th>From</th></tr>{rows}</table></div></section>'



def page(idx: dict, run: Path, rel: str, owner: str) -> str:
    facts = [("repository", idx.get("repository")), ("language", idx.get("ecosystem")), ("mode", idx.get("mode")), ("base", (idx.get("base") or "")[:12]), ("head", (idx.get("head") or "")[:12]),
             ("model", idx.get("model")), ("started", idx.get("started")), ("harness", idx.get("harness_version")), ("run", idx.get("run_id"))]
    facts_html = "".join(f"<span>{e(k)} <b>{e(str(v))}</b></span>" for k, v in facts if v)
    st = story_mod.build(run, idx)
    blocks = story_blocks(st, rel)
    def block(title, wrap="story"):
        return f'<section class="{wrap}">{blocks[title]}</section>' if title in blocks else ""
    plain = "".join(f"<div class=\"verdict\">{inline(x)}</div>" for x in st["sections"][0].get("paragraphs", []))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(idx.get('repository') or owner)} run {e(str(idx.get('run_id') or run.name))}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@500;700;900&family=Red+Hat+Text:ital,wght@0,400;0,500;1,400&family=Red+Hat+Mono&display=swap">
<style>{CSS}</style></head><body>
<main id="main">
<header class="run-hero"><div class="eyebrow"><a href="../../index.html">All runs</a> · <a href="../../../index.html">AI Test Harness</a></div>
<h1>{e(idx.get('repository') or owner)}: {e(run.name)}</h1>
<p class="lede">{e(st["subtitle"])} The same story opens the run's folder as <a href="{e(REPO_URL)}/examples/{e(rel)}/README.md">README.md</a>; the example's write-up is on its <a href="{e(REPO_URL)}/examples/{e(owner)}/README.md">example page</a>.</p>
<div class="facts">{facts_html}</div></header>
{plain}
{block("Who, what, why, where, when")}
{block("Decisions the harness made")}
{block("Actions it took")}
{block("Actions it did not take, by design")}
<section class="pkg"><h2>How it happened, stage by stage</h2><p>What each stage read, did and wrote, with the file behind every number.</p></section>
<ol class="timeline">{stage_cards(idx, run, rel)}</ol>
{package_sections(idx, run, rel)}
{block("The records, in plain terms")}
{goals_table(run, rel)}
<section class="story catalogue"><details><summary><h2 style="display:inline">What is in this folder, and who it is for</h2></summary>{blocks.get("What is in this folder, and who it is for", "")}</details></section>
<footer class="foot">Rendered by <code>tools/build-runs.py</code> from <code>run-index.json</code> and the files it names, with the story from <code>harness/src/harness/story.py</code>. Every value is escaped; nothing here is executed or trusted.</footer>
</main></body></html>"""


def main() -> None:
    runs = sorted(p for p in EXAMPLES.glob("*/*/") if (p / "run-index.json").exists())
    rows = []
    for run in runs:
        idx = load(run / "run-index.json"); owner = run.parent.name; rel = f"{owner}/{run.name}"
        out = SITE / "runs" / owner / run.name / "index.html"; out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(idx, run, rel, owner))
        pk = idx["packages"]
        tests = sum((p["tests"].get("ran") or 0) for p in pk); proven = sum((p["tests"].get("proven") or 0) for p in pk); acc = sum((p["tests"].get("accepted") or 0) for p in pk)
        stages = [s for s, v in idx["stages"].items() if v.get("present")]
        rows.append(f"<tr><td><a href=\"{e(owner)}/{e(run.name)}/index.html\">{e(rel)}</a></td><td>{e(str(idx.get('ecosystem')))}</td><td>{e(str(idx.get('mode')))}</td>"
                    f"<td>{e(', '.join(p['package'] for p in pk)) or '-'}</td><td>{tests}</td><td>{proven}</td><td>{acc}</td><td>{e(str((idx.get('goals') or {}).get('met', '-')))}</td><td>{len(stages)} of {len(idx['stages'])}</td></tr>")
    index = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AI Test Harness runs</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@500;700;900&family=Red+Hat+Text:ital,wght@0,400;0,500;1,400&family=Red+Hat+Mono&display=swap">
<style>{CSS}</style></head><body><main id="main">
<header class="run-hero"><div class="eyebrow"><a href="../index.html">AI Test Harness</a></div><h1>Every run, start to finish</h1>
<p class="lede">One page per run. Each opens with the story in plain terms (who, what, why, where, when, the decisions, the actions), then the stage-by-stage account, the results per package, the records in plain terms, and every file by the reader it is for. The roll-up of the numbers is document 11 on the main page.</p></header>
<section class="pkg"><div class="tbl"><table class="res"><tr><th>Run</th><th>Language</th><th>Mode</th><th>Packages</th><th>Tests ran</th><th>Proven</th><th>Accepted</th><th>Goals met</th><th>Stages</th></tr>{"".join(rows)}</table></div></section>
</main></body></html>"""
    (SITE / "runs").mkdir(parents=True, exist_ok=True)
    (SITE / "runs" / "index.html").write_text(index)
    print(f"wrote {len(runs)} run pages under {SITE / 'runs'}")


if __name__ == "__main__":
    main()
