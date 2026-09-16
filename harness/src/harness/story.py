"""README.md for a run: the story of what happened, for a general reader.

Written after every stage, from the run index and the records the stages wrote. It answers who, what,
why, where and when; states the outcome in plain terms; lists the decisions the harness made and the
actions it took and did not take; renders the UDLM records in plain terms; and ends with what every file
in the folder is for and who should read it. Nothing here is new information: every sentence is read
from a record, so the story cannot say more than the evidence does.

The story is a list of sections; `to_markdown` renders it for the repository, and the site renders the
same sections to HTML so the two never disagree.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from . import runindex
from .util import read_json

STAGE_NAMES = {
    "selfcheck": ("0", "Self-verification"), "intake": ("1", "Intake"), "analyze": ("2", "Analysis"),
    "generate": ("3", "Generation"), "execute": ("4", "Validation execution"), "triage": ("5", "Triage"),
    "packet": ("6", "Review packet"), "attest": ("", "Attestation"), "assess": ("", "Assessment"),
    "propose": ("", "Test pull request"), "feedback": ("7", "Feedback"),
}
AUDIENCE_NAMES = {
    "everyone": "Everyone", "reviewer": "Reviewers (the developer or team that owns the change)",
    "security": "Product Security", "audit": "Supply Chain Security and auditors",
    "developer": "The person who ran the harness", "machine": "Tools (kept for replay and proof; not meant to be read)",
}
NOT_TAKEN = [
    "It did not merge anything. Tests reach a repository only through a pull request that a person merges.",
    "It did not change production code and did not propose a fix. Fixes come from a separate fix pipeline; this harness only tests.",
    "It did not publish a VEX statement. The drafts are proposals for Product Security.",
    "It did not delete any existing test. Retirements are proposed with evidence for a person to act on.",
]


def _load(p: Path):
    return read_json(p) if p.exists() else None


def _plain_terms(md_path: Path) -> str | None:
    if not md_path.exists():
        return None
    text = md_path.read_text(encoding="utf-8")
    marker = "**In plain terms.**"
    if marker in text:
        body = text.split(marker, 1)[1]
        return body.split("\n\n", 1)[0].strip()
    return None


def _when(ts: str | None) -> str:
    if not ts:
        return "not recorded"
    return ts.replace("T", " ").replace("+00:00", " UTC").replace("Z", " UTC")


def _count(items, key, default="unspecified") -> dict[str, int]:
    out: dict[str, int] = {}
    for it in items:
        k = str(it.get(key) or default)
        out[k] = out.get(k, 0) + 1
    return out


def _phrase(counts: dict[str, int]) -> str:
    return "; ".join(f"{n} {k}" for k, n in counts.items())


# --- the five questions ---------------------------------------------------------------------------

def _who(idx: dict, workdir: Path) -> str:
    version = idx.get("harness_version")
    reviewers = []
    for p in idx["packages"]:
        rv = p.get("review") or {}
        if rv.get("outcome"):
            reviewers.append(rv["outcome"])
    who = f"The AI Test Harness {version} did the work without a person in the loop."
    if reviewers:
        who += " A person decided the result: " + "; ".join(sorted(set(reviewers))) + "."
    else:
        who += " A person decides the result; nothing in this run has been merged."
    return who


def _what(idx: dict) -> str:
    wl = (idx["stages"].get("intake") or {}).get("summary") or {}
    parts = []
    for p in idx["packages"]:
        if p.get("first_party"):
            parts.append(f"the application's own code at {idx.get('head') or 'head'}")
        elif p.get("old_version") and p.get("old_version") != p.get("new_version"):
            parts.append(f"{p['package']} {p['old_version']} to {p['new_version']}")
        else:
            parts.append(f"{p['package']} {p.get('new_version') or p.get('old_version') or ''}".strip())
    mode = idx.get("mode")
    if mode == "rescan":
        what = f"A scheduled scan of {idx.get('repository')} at {idx.get('head') or idx.get('base')}, no change under review."
        if wl.get("work_list_rows") is not None:
            what += f" {wl.get('with_advisories_at_head', 0)} of {wl['work_list_rows']} packages carry known vulnerabilities."
        return what + (f" Tests for {', '.join(parts)}." if parts else "")
    head = f"{idx.get('base')}..{idx.get('head')}" if idx.get("base") else (idx.get("head") or "")
    what = f"Tests for {', '.join(parts) if parts else 'no package yet'}"
    if wl.get("work_list_rows") is not None:
        what += f", chosen from a work list of {wl['work_list_rows']} packages, {wl.get('changed', 0)} of which this change touched"
    return what + f". Repository {idx.get('repository')}{', change ' + head if head else ''}{', mode ' + mode if mode else ''}."


def _why(idx: dict, workdir: Path) -> str:
    reasons = []
    for p in idx["packages"]:
        facts = _load(workdir / "analyze" / p["package"] / "facts.json") or {}
        rs = list((facts.get("risk") or {}).get("reasons") or [])
        vs = facts.get("vulns_summary") or {}
        if p.get("first_party"):
            reasons.append(f"{p['package']}: the application's own changed code has no tests from anyone else; the harness tests what the change added or changed.")
            continue
        short = "; ".join(r.split(" (")[0] for r in rs[:2]) if rs else "in the work list"
        if p.get("change") in ("bumped", "added") and (vs.get("count_old") or vs.get("count")):
            short += f"; {vs.get('count_old', 0)} advisories before the change, {vs.get('count', 0)} after"
        elif vs.get("count") and not any("vulnerabilit" in r for r in rs[:2]):
            short += f"; {vs['count']} known advisories at this version"
        reasons.append(f"{p['package']} (score {(facts.get('risk') or {}).get('score')}, budget {p.get('budget')}): {short}.")
    if not reasons:
        return "Every dependency change is a chance for a silent behaviour change or an unproven security fix; the harness tests the ones the risk score says matter."
    lead = "The risk score decides the budget; the two strongest reasons per package: " if len(reasons) > 1 else ""
    return lead + " ".join(reasons)


def _where(idx: dict, workdir: Path) -> str:
    parts = []
    tg = {}
    for p in idx["packages"]:
        res = _load(workdir / "execute" / p["package"] / "results.json") or {}
        tg = res.get("target") or tg
    if tg:
        parts.append(f"every test ran in a sealed sandbox ({tg.get('class', 'container')}, network {(tg.get('isolation') or {}).get('network', 'none')}, image {tg.get('identity') or 'not recorded'})")
    if idx.get("model"):
        parts.append(f"the model was {idx['model']} in {idx.get('generation_mode') or 'fixed'} mode")
    prop = [p.get("proposal") for p in idx["packages"] if p.get("proposal")]
    if prop:
        prs = [p.get("pull_request") for p in prop if p.get("pull_request")]
        parts.append("the tests were proposed to the overlay repository" + (f" as {', '.join(prs)}" if prs else ""))
    parts.append("the run's own files are in this folder")
    return "; ".join(parts).capitalize() + "."


def _when_para(idx: dict) -> str:
    st = idx["stages"]
    times = [(k, s.get("generated")) for k, s in st.items() if s.get("present") and s.get("generated")]
    times.sort(key=lambda kv: kv[1])
    start = idx.get("started") or (times[0][1] if times else None)
    last = times[-1] if times else None
    s = f"Started {_when(start)}."
    if last:
        s += f" The last stage to write was {STAGE_NAMES[last[0]][1].lower()} at {_when(last[1])}."
    return s


# --- the timeline ---------------------------------------------------------------------------------

def stage_lines(idx: dict, workdir: Path) -> list[dict]:
    """One row per stage that ran: number, name, when, and what it did in a sentence or two."""
    st = idx["stages"]; pk = idx["packages"]
    rows = []
    for key, (num, name) in STAGE_NAMES.items():
        s = st.get(key) or {}
        if not s.get("present"):
            continue
        sm = s.get("summary") or {}
        did: list[str] = []
        if key == "selfcheck":
            did.append(f"Ran {sm.get('checks')} checks from the failure register on its own code before touching the target; "
                       f"{'all passed' if sm.get('passed') else 'a failure stopped the run'}. Sandbox probe {sm.get('sandbox')}, model probe {sm.get('model')}.")
        elif key == "intake":
            did.append(f"Resolved the dependency graph at head ({sm.get('packages_at_head')} packages) and at base ({sm.get('packages_at_base')}), "
                       f"looked every version up in OSV ({sm.get('with_advisories_at_head')} with advisories at head), and wrote a work list of "
                       f"{sm.get('work_list_rows')} packages, {sm.get('changed')} of them changed by this change.")
        elif key == "analyze":
            scored = []
            for p in pk:
                facts = _load(workdir / "analyze" / p["package"] / "facts.json") or {}
                if p.get("first_party"):
                    did.append(f"{p['package']}: read the application's diff and found the symbols it added or changed.")
                else:
                    scored.append(f"{p['package']} {(facts.get('risk') or {}).get('score')} ({p.get('budget')})")
            if scored:
                how = "diffed the two versions' public API and source, found the application's call sites and read the advisories" \
                    if idx.get("mode") != "rescan" else "read each package's API and source, found the application's call sites and read the advisories"
                did.append(f"For each package, {how}; risk score and budget: {', '.join(scored)}.")
        elif key == "generate":
            for p in [q for q in pk if "generate/manifest.json" in q["files"]]:
                m = _load(workdir / "generate" / p["package"] / "manifest.json") or {}
                kept = sum(len(f.get("tests", [])) for f in m.get("files", []))
                cut = sum(len(f.get("cut", [])) for f in m.get("files", []))
                calls = len(list((workdir / "generate" / p["package"] / "model-calls").glob("*.prompt.md"))) + len(list((workdir / "generate" / p["package"] / "model-calls").glob("*.messages.json")))
                did.append(f"{p['package']}: asked the model ({m.get('model', {}).get('name') or idx.get('model')}) for tests in {calls} calls; "
                           f"kept {kept} tests in {len(m.get('files', []))} file(s), cut {cut} that did not hold up on the baseline run, "
                           f"discarded {len(m.get('discarded', []))} whole attempt(s).")
        elif key == "execute":
            for p in [q for q in pk if "execute/results.json" in q["files"]]:
                r = _load(workdir / "execute" / p["package"] / "results.json") or {}
                c = r.get("counts", {})
                did.append(f"{p['package']}: ran {c.get('total')} tests on head, again for flakes, and on the other version "
                           f"({', '.join(r.get('runs', {}).keys())}); {c.get('pass_on_new')} pass on head, {c.get('flaky')} flaky, "
                           f"{c.get('fix_pinning_confirmed')} proved a fix; {r.get('coverage_summary', {}).get('covered_lines_in_target')} lines of the package covered.")
                mut = p.get("mutation") or {}
                if mut.get("status") == "ran":
                    did.append(f"Mutation: {mut.get('killed')} of {mut.get('sampled')} sampled mutants killed, score {mut.get('score')}.")
                elif mut:
                    did.append(f"Mutation {mut.get('status')}.")
        elif key == "triage":
            for p in [q for q in pk if "triage/triage.json" in q["files"]]:
                t = (_load(workdir / "triage" / p["package"] / "triage.json") or {}).get("summary") or {}
                did.append(f"{p['package']}: classified every verdict; {t.get('tests_accept')} tests to accept, {t.get('tests_discard_or_regenerate')} to discard or regenerate, "
                           f"{t.get('findings')} finding(s), {t.get('escalated')} escalated to a person.")
        elif key == "packet":
            did.append("Wrote the review packet per package: the verdict in plain terms, the tests as a patch, the findings, the draft VEX statements, and the pull request text.")
        elif key == "attest":
            for p in [q for q in pk if q.get("attestation")]:
                did.append(f"{p['package']}: signed the in-toto statement over the patch and the records ({p['attestation'].get('result')}) and sealed the UDLM records.")
        elif key == "assess":
            g = sm
            did.append(f"Measured the run against the blueprint's goals: {g.get('met')} met, {g.get('not_met')} not met, {g.get('not_applicable')} not applicable, {g.get('other')} other.")
        elif key == "propose":
            for p in [q for q in pk if q.get("proposal")]:
                pr = p["proposal"]
                did.append(f"{p['package']}: {pr.get('status')}" + (f", {pr.get('pull_request')}" if pr.get("pull_request") else "") + ". The harness pushed one branch and opened the pull request; it merged nothing.")
        elif key == "feedback":
            for p in [q for q in pk if q.get("review")]:
                rv = p["review"]
                did.append(f"{p['package']}: read the pull request as a person left it ({rv.get('outcome')}): {rv.get('accepted')} accepted, {rv.get('edited')} edited, "
                           f"{rv.get('rejected')} rejected; wrote the requested and realized records and the signed acceptance statement.")
        when = s.get("generated") or ((_load(workdir / "intake" / "worklist.json") or {}).get("created") if key == "intake" else None)
        rows.append({"key": key, "number": num, "name": name, "when": _when(when), "did": " ".join(did) or "Ran; see the stage's files."})
    return rows


# --- decisions and actions ------------------------------------------------------------------------

def decisions(idx: dict, workdir: Path) -> list[str]:
    out = []
    for p in idx["packages"]:
        pkg = p["package"]
        m = _load(workdir / "generate" / pkg / "manifest.json") or {}
        cuts = [c for f in m.get("files", []) for c in f.get("cut", [])]
        if cuts:
            out.append(f"{pkg}: cut {len(cuts)} generated test(s) before execution: {_phrase(_count(cuts, 'reason'))}.")
        if m.get("discarded"):
            out.append(f"{pkg}: discarded {len(m['discarded'])} generation attempt(s): {_phrase(_count(m['discarded'], 'reason'))}.")
        t = _load(workdir / "triage" / pkg / "triage.json") or {}
        if t:
            acts = _count(t.get("tests", []), "action")
            out.append(f"{pkg}: triage decided per test: {_phrase(acts)}.")
            for f in t.get("findings", []):
                summary = str(f.get("summary") or "").rstrip(".")
                out.append(f"{pkg}: finding, {f.get('class')} at confidence {f.get('confidence')}: {summary}. Route: {f.get('routing')}.")
        mut = p.get("mutation") or {}
        if mut.get("status") == "ran":
            ok = (mut.get("score") or 0) >= 0.6
            out.append(f"{pkg}: mutation score {mut.get('score')} {'meets' if ok else 'is below'} the blueprint's 0.6; " + ("the tests are strong enough to catch changes in what they cover." if ok else "the packet says so, and the reviewer sees which tests killed nothing."))
        pj = _load(workdir / "packet" / pkg / "packet.json") or {}
        if pj.get("vex_statements"):
            out.append(f"{pkg}: draft VEX per advisory: " + ", ".join(f"{k} {v}" for k, v in pj["vex_statements"].items()) + ".")
        rv = p.get("review") or {}
        if rv.get("outcome"):
            out.append(f"{pkg}: the reviewer's decision, {rv['outcome']}: {rv.get('accepted')} accepted, {rv.get('edited')} edited, {rv.get('rejected')} rejected.")
    return out


def actions(idx: dict, workdir: Path) -> tuple[list[str], list[str]]:
    taken = []
    for p in idx["packages"]:
        pkg = p["package"]
        if "packet/tests.patch" in p["files"]:
            n = (p.get("tests") or {}).get("accepted")
            taken.append(f"{pkg}: wrote a review packet with {n if n is not None else 'the'} accepted test(s) as a patch, ready for a pull request.")
        if "packet/vex.openvex.json" in p["files"]:
            taken.append(f"{pkg}: drafted VEX statements for Product Security.")
        if p.get("attestation"):
            taken.append(f"{pkg}: signed the test-result statement ({p['attestation'].get('result')}).")
        pr = p.get("proposal") or {}
        if pr:
            taken.append(f"{pkg}: {pr.get('status')}" + (f" ({pr['pull_request']})" if pr.get("pull_request") else "") + ".")
        else:
            taken.append(f"{pkg}: no pull request was opened in this run; the packet holds what one would carry.")
        rv = p.get("review") or {}
        if rv.get("outcome"):
            taken.append(f"{pkg}: captured the reviewer's decision and wrote the realized records and the acceptance statement.")
    return taken, list(NOT_TAKEN)


# --- UDLM records in plain terms ------------------------------------------------------------------

def _record_sentence(r: dict) -> str:
    f = r.get("fields") or {}; o = r.get("outputs") or {}; rt = r.get("resource_type", ""); st = r.get("state")
    if rt == "Vulnerability":
        desc = (r.get("metadata") or {}).get("description") or ""
        ranges = ", ".join(f.get("affected_ranges") or []) or "versions the advisory does not pin"
        return f"{f.get('id')} is a known vulnerability affecting {ranges}. {desc}".strip()
    if rt == "SoftwarePackage":
        return f"{f.get('name')} {f.get('version')} ({f.get('type')}) is the version this change installs."
    if rt == "Job":
        pr = f.get("parameters") or {}
        if st == "Requested":
            return f"The harness was asked to run on {pr.get('repository')} from {pr.get('base')} to {pr.get('head')} in {pr.get('mode')} mode."
        if st == "Realized":
            return f"The run finished; its outputs are the records this statement seals." + (f" Result: {o.get('result') or o.get('status')}." if (o.get('result') or o.get('status')) else "")
    if rt.startswith("TestEvidence"):
        name = (f.get("test_id") or "::").split("::")[1] if "::" in (f.get("test_id") or "") else f.get("test_id")
        role = f.get("vulnerability_role")
        vuln = (f.get("vulnerability_ref") or "").rsplit("/", 1)[-1].upper()
        res = f.get("result") or {}
        outcome = res.get("outcome") if isinstance(res, dict) else res
        if st == "Intent":
            what = f"{'an' if str(role)[0] in 'aeiou' else 'a'} {role} test for {vuln}" if role else f"a {f.get('category')} test"
            return f"`{name}` is {what} in `{f.get('file_path')}`; it {outcome} on head in the sealed sandbox."
        if st == "Requested":
            return f"A person was asked to decide `{name}` on the pull request."
        if st == "Realized":
            return f"`{name}` was {o.get('decision')} by {o.get('accepted_by')} and landed at `{o.get('path')}` in merge {str(o.get('merge_commit') or '')[:12]}."
    if rt == "VexStatement":
        vuln = (f.get("vulnerability_ref") or "").rsplit("/", 1)[-1].upper()
        return f"Draft: {vuln} is `{f.get('status')}` in this package. {f.get('status_notes') or ''}".strip()
    return f"{rt} record in state {st}."


def records(idx: dict, workdir: Path) -> list[dict]:
    rows = []
    for p in idx["packages"]:
        for stage in ("attest", "feedback"):
            d = workdir / stage / p["package"] / "udlm"
            ix = _load(d / "index.json") or {}
            for kind, fname in (ix.get("files") or {}).items():
                path = d / fname
                if not path.exists():
                    continue
                with path.open(encoding="utf-8") as fh:
                    for r in yaml.safe_load_all(fh):
                        if not r:
                            continue
                        rows.append({"package": p["package"], "kind": r.get("resource_type", kind), "state": r.get("state"),
                                     "at": _when(r.get("at")), "says": _record_sentence(r), "sealed": bool(ix.get("sealed")), "file": f"{stage}/{p['package']}/udlm/{fname}"})
    return rows


# --- the story ------------------------------------------------------------------------------------

def build(workdir: Path, idx: dict | None = None) -> dict:
    idx = idx or runindex.build(workdir)
    plain = []
    for p in idx["packages"]:
        pt = _plain_terms(workdir / "packet" / p["package"] / "packet.md")
        if pt:
            plain.append(f"**{p['package']}.** {pt}")
    if not plain:
        last = [k for k, s in idx["stages"].items() if s.get("present")]
        plain.append(f"This run has not reached the review packet yet; the last stage that wrote was {STAGE_NAMES[last[-1]][1].lower() if last else 'none'}.")
    taken, not_taken = actions(idx, workdir)
    recs = records(idx, workdir)
    cat = idx.get("catalogue") or []
    by_aud: dict[str, list[dict]] = {}
    for c in cat:
        by_aud.setdefault(c["audience"], []).append(c)
    sections = [
        {"title": "In plain terms", "paragraphs": plain},
        {"title": "Who, what, why, where, when", "table": {"columns": ["", ""], "rows": [
            ["Who", _who(idx, workdir)], ["What", _what(idx)], ["Why", _why(idx, workdir)], ["Where", _where(idx, workdir)], ["When", _when_para(idx)]]}},
        {"title": "What the harness did, step by step",
         "paragraphs": ["Each stage reads what the stage before wrote and writes its own files. Stage 4 is validation execution: the tests prove themselves once, here; keeping the application honest afterwards is the job of the suite they join."],
         "table": {"columns": ["Stage", "When", "What it did"], "rows": [[f"{r['number']} {r['name']}".strip(), r["when"], r["did"]] for r in stage_lines(idx, workdir)]}},
        {"title": "Decisions the harness made", "bullets": decisions(idx, workdir) or ["No decisions yet; the run has not reached triage."]},
        {"title": "Actions it took", "bullets": taken or ["None yet."]},
        {"title": "Actions it did not take, by design", "bullets": not_taken},
    ]
    if recs:
        sections.append({"title": "The records, in plain terms",
                         "paragraphs": [f"{len(recs)} UDLM records, each a fact from this run in the estate's own language. Intent is what the harness proposed, Requested is what a person was asked to decide, Realized is what landed and who made it so. "
                                        + ("All are sealed with a content hash." if all(r['sealed'] for r in recs) else "Records marked unsealed were written without the UDLM chain code present.")],
                         "table": {"columns": ["Record", "State", "What it says", "Written"], "rows": [[r["kind"].split(".")[0], r["state"], r["says"], r["at"]] for r in recs]}})
    sections.append({"title": "What is in this folder, and who it is for",
                     "paragraphs": ["Every file exists for a reader or a tool named here. The plain-English files come first; the machine files stay because they are the proof and the replay."],
                     "groups": [{"title": AUDIENCE_NAMES.get(a, a), "items": [(c["path"], c["purpose"]) for c in by_aud[a]]} for a in AUDIENCE_NAMES if a in by_aud]})
    head = f"{idx.get('base')}..{idx.get('head')}" if idx.get("base") and idx.get("head") else (idx.get("head") or "")
    return {"title": f"Run {idx.get('run_id')}: {idx.get('repository')} {head}".strip(),
            "subtitle": "What happened, why, and what came out of it. Written by the harness from its own records; a person decides what to do with it.",
            "sections": sections}


def _cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def to_markdown(story: dict) -> str:
    out = [f"# {story['title']}", "", story["subtitle"], ""]
    for sec in story["sections"]:
        out += [f"## {sec['title']}", ""]
        for para in sec.get("paragraphs", []):
            out += [para, ""]
        if sec.get("bullets"):
            out += [f"- {b}" for b in sec["bullets"]] + [""]
        if sec.get("table"):
            cols = sec["table"]["columns"]
            out += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
            out += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in sec["table"]["rows"]] + [""]
        for g in sec.get("groups", []):
            out += [f"**{g['title']}**", ""] + [f"- `{path}`: {why}" for path, why in g["items"]] + [""]
    return "\n".join(out).rstrip() + "\n"


def write(workdir: Path, idx: dict | None = None) -> Path:
    out = workdir / "README.md"
    out.write_text(to_markdown(build(workdir, idx)), encoding="utf-8")
    return out
