#!/usr/bin/env python3
"""Build a single-page HTML site from the docs and blueprint files.

Usage: python3 tools/build-site.py [output-path]
Default output: site/index.html (ignored by git). Requires python-markdown.
Mermaid blocks become <pre class="mermaid"> so any Mermaid-aware host renders them.
"""
import html
import re
import sys
from pathlib import Path

import markdown
from markdown.extensions.toc import TocExtension

ROOT = Path(__file__).resolve().parent.parent
# The evidence roll-up is generated from the run records on every build, so the site never shows a stale number.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("rollup", ROOT / "tools" / "rollup.py"); _rollup = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_rollup)
_rollup.main(write=str(ROOT / "docs" / "11-evidence-rollup.md"))
_spec_c = _ilu.spec_from_file_location("catalogue", ROOT / "tools" / "catalogue.py"); _cat = _ilu.module_from_spec(_spec_c); _spec_c.loader.exec_module(_cat)
_cat.main()
DOCS = sorted((ROOT / "docs").glob("*.md"))
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site" / "index.html"

DECK_CSS = """
body { margin: 0; background: #F5F7F6; color: #1A222B; font-family: "Red Hat Text", "Helvetica Neue", Arial, sans-serif; }
@media (prefers-color-scheme: dark) { body { background: #12181D; color: #E4EAE7; } .slide { background: #181F25; border-color: #2C363C; } .nav a { color: #8AD6D1; } }
.deck { max-width: 62rem; margin: 0 auto; padding: 2rem 1rem 4rem; }
.nav { font-size: .85rem; margin-bottom: 1rem; } .nav a { color: #0A4F4D; }
.slide { background: #fff; border: 1px solid #D3DAD7; border-radius: 6px; padding: 2rem 2.5rem; margin: 0 0 1.5rem; min-height: 14rem; position: relative; }
.slide h1 { font-family: "Red Hat Display", "Helvetica Neue", Arial, sans-serif; font-size: 1.7rem; margin: 0 0 1rem; letter-spacing: -.01em; }
.slide h2 { font-size: 1.15rem; font-weight: 500; color: #5A6772; margin: 0 0 1rem; }
.slide .n { position: absolute; right: 1rem; bottom: .6rem; font-size: .75rem; color: #5A6772; font-variant-numeric: tabular-nums; }
.slide table { border-collapse: collapse; width: 100%; font-size: .92rem; } .slide th, .slide td { text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #D3DAD7; }
.slide .mermaid { background: transparent; }
.slide p, .slide li { line-height: 1.55; } .slide pre { background: #E8EDEB; padding: .8rem; border-radius: 4px; overflow-x: auto; font-size: .82rem; }
"""


def render_deck(md_path: Path, out_path: Path, decks: list[tuple[str, str]]) -> None:
    """A slide deck as one scrolling page: every '---' becomes a card, Mermaid blocks render."""
    text = md_path.read_text()
    if text.startswith("---\n"):
        text = text.split("\n---\n", 1)[1]           # drop the Marp front matter
    slides = [s for s in text.split("\n---\n") if s.strip()]
    cards = []
    for i, s in enumerate(slides, 1):
        s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
        body, _ = convert(s, f"s{i}")
        cards.append(f'<section class="slide">{body}<span class="n">{i} / {len(slides)}</span></section>')
    title = re.search(r"^title:\s*(.+)$", md_path.read_text(), re.M)
    title = title.group(1).strip() if title else md_path.stem
    nav = " · ".join(f'<a href="{n}.html">{t}</a>' for n, t in decks)
    out_path.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@700;900&family=Red+Hat+Text:wght@400;500&display=swap">
<style>{DECK_CSS}</style>
<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
mermaid.initialize({{ startOnLoad: true, theme: matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "neutral", securityLevel: "strict" }});</script>
</head><body><div class="deck"><div class="nav"><a href="../">AI Test Harness</a> · decks: {nav} · <a href="{md_path.name}">markdown source</a></div>
{"".join(cards)}</div></body></html>
""")

AUDIENCES = [
    ("exec", "Executive", "CEO, managing director, board", ["00", "11"], "5 min"),
    ("fund", "Funding decision", "CTO, VP Engineering, CISO", ["00", "01", "11", "07"], "20 min"),
    ("build", "Build or run it", "Engineer, architect, security analyst", ["02", "03", "05", "06", "09", "10", "bp", "hi", "ex"], "2 h"),
    ("proof", "See it work", "Anyone who wants the evidence", ["11", "10", "ex", "hi"], "15 min"),
    ("public", "Public", "Journalist, student, customer", ["00", "08"], "10 min"),
]

MERMAID_RE = re.compile(r"```mermaid\n(.*?)\n```", re.S)
DOCLINK_RE = re.compile(r"\]\((?:\./|\.\./docs/)?(\d\d)-[a-z0-9-]+\.md(?:#([^)]+))?\)")
BPLINK_RE = re.compile(r"\]\((?:\.\./)?blueprint/([a-z0-9.-]+)\)")


def slugify_for(prefix):
    def slugify(value, separator):
        value = re.sub(r"[^\w\s-]", "", value).strip().lower()
        value = re.sub(r"[\s_-]+", separator, value)
        return f"{prefix}-{value}"
    return slugify


def convert(text, prefix):
    diagrams = []

    def stash(m):
        diagrams.append(m.group(1))
        return f"\n\nMERMAIDBLOCK{len(diagrams) - 1}\n\n"

    text = MERMAID_RE.sub(stash, text)
    text = DOCLINK_RE.sub(lambda m: f"](#{m.group(1)}-{m.group(2)})" if m.group(2) else f"](#doc-{m.group(1)})", text)
    text = BPLINK_RE.sub(lambda m: f"](#bp-{re.sub(r'[^a-z0-9]+', '-', m.group(1))})", text)
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "attr_list",
                    TocExtension(slugify=slugify_for(prefix), toc_depth="1-3")],
    )
    out = md.convert(text)
    for i, d in enumerate(diagrams):
        out = out.replace(f"<p>MERMAIDBLOCK{i}</p>",
                          f'<div class="diagram"><pre class="mermaid">{html.escape(d)}</pre></div>')
    out = re.sub(r"<table>", '<div class="table-wrap"><table>', out)
    out = out.replace("</table>", "</table></div>")
    return out, md.toc_tokens


def first_h1(text):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Untitled"


sections, nav = [], []
for path in DOCS:
    num = path.name[:2]
    text = path.read_text()
    title = first_h1(text)
    body, toc = convert(text, num)
    body = re.sub(r"<h1[^>]*>.*?</h1>", "", body, count=1)
    sub = "".join(f'<li><a href="#{t["id"]}">{html.escape(t["name"])}</a></li>'
                  for t in (toc[0]["children"] if toc else []) if t["level"] == 2)
    nav.append(f'<li data-doc="{num}"><a href="#doc-{num}"><span class="num">{num}</span>{html.escape(title)}</a>'
               f'<ul class="sub">{sub}</ul></li>')
    sections.append(f'<section class="doc" id="doc-{num}"><div class="eyebrow">Document {num}</div>'
                    f'<h1>{html.escape(title)}</h1>{body}</section>')

# The implementation and the example write-ups, as documents after the docs
for extra_num, extra_path, extra_title in (("hi", ROOT / "harness" / "README.md", "The implementation"),
                                            ("ex", ROOT / "examples" / "frc-scheduler-server" / "README.md", "Example: frc-scheduler-server")):
    text = extra_path.read_text()
    body, toc = convert(text, extra_num)
    body = re.sub(r"<h1[^>]*>.*?</h1>", "", body, count=1)
    sub = "".join(f'<li><a href="#{t["id"]}">{html.escape(t["name"])}</a></li>'
                  for t in (toc[0]["children"] if toc else []) if t["level"] == 2)
    nav.append(f'<li data-doc="{extra_num}"><a href="#doc-{extra_num}"><span class="num">{extra_num}</span>{html.escape(extra_title)}</a>'
               f'<ul class="sub">{sub}</ul></li>')
    sections.append(f'<section class="doc" id="doc-{extra_num}"><div class="eyebrow">{"Layer 2" if extra_num == "hi" else "Layer 3"}</div>'
                    f'<h1>{html.escape(extra_title)}</h1>{body}</section>')

# Blueprint files
bp_parts = []
for path in sorted((ROOT / "blueprint").iterdir()):
    anchor = "bp-" + re.sub(r"[^a-z0-9]+", "-", path.name)
    if path.suffix == ".md":
        body, _ = convert(path.read_text(), anchor)
        body = re.sub(r"<h1[^>]*>.*?</h1>", "", body, count=1)
        bp_parts.append(f'<h2 id="{anchor}"><code>blueprint/{path.name}</code></h2>{body}')
    else:
        lang = path.suffix.lstrip(".")
        bp_parts.append(f'<h2 id="{anchor}"><code>blueprint/{path.name}</code></h2>'
                        f'<pre><code class="language-{lang}">{html.escape(path.read_text())}</code></pre>')
nav.append('<li data-doc="bp"><a href="#doc-bp"><span class="num">bp</span>Blueprint files</a></li>')
sections.append('<section class="doc" id="doc-bp"><div class="eyebrow">Machine-readable</div>'
                '<h1>Blueprint files</h1><p>The contract, the schema, the attestation predicate, and the '
                'pipeline skeleton, exactly as they sit in the repository.</p>' + "".join(bp_parts) + "</section>")

readme = (ROOT / "README.md").read_text()
para = re.search(r"## The one-paragraph version\n\n(.*?)\n\n## ", readme, re.S).group(1).replace("\n", " ")

aud_cards = "".join(
    f'<button class="aud" type="button" id="aud-{key}" data-docs="{" ".join(docs)}">'
    f'<span class="aud-name">{name}</span><span class="aud-who">{who}</span><span class="aud-time">{time}</span></button>'
    for key, name, who, docs, time in AUDIENCES)

CSS = (ROOT / "tools" / "site.css").read_text()
JS = (ROOT / "tools" / "site.js").read_text()

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Test Harness</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@500;700;900&family=Red+Hat+Text:ital,wght@0,400;0,500;1,400&family=Red+Hat+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
const dark = matchMedia("(prefers-color-scheme: dark)").matches;
mermaid.initialize({{ startOnLoad: true, theme: dark ? "dark" : "neutral", securityLevel: "strict" }});
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="shell">
<nav class="rail" aria-label="Documents">
  <div class="brand"><a href="#top">AI Test Harness</a><span class="status">Working draft, Sept 2026</span></div>
  <button class="menu-toggle" type="button" id="menu-toggle" aria-expanded="false" aria-controls="rail-list">Contents</button>
  <div id="rail-list" class="rail-list">
    <div class="rail-label">Start here, by audience</div>
    <div class="aud-list">{aud_cards}</div>
    <div class="rail-label">Documents</div>
    <ol class="docs">{"".join(nav)}</ol>
    <div class="rail-label">Runs</div>
    <ul class="docs decks"><li><a href="runs/index.html"><span class="num">14</span>Every run, start to finish</a></li></ul>
    <div class="rail-label">Presentations</div>
    <ul class="docs decks"><li><a href="slides/executive.html"><span class="num">5m</span>Executives</a></li><li><a href="slides/funding.html"><span class="num">15m</span>Funding decision</a></li><li><a href="slides/builder.html"><span class="num">30m</span>Build or run it</a></li><li><a href="slides/public.html"><span class="num">10m</span>Readers</a></li></ul>
    <div class="rail-foot"><a href="https://github.com/croadfeldt/ai-test-harness">Repository on GitHub</a>. Diagram sources under <a href="diagrams/">diagrams/</a>.</div>
  </div>
</nav>
<main id="main">
  <header class="hero" id="top">
    <div class="eyebrow">Blueprint and working draft</div>
    <h1>Tests for every piece of code we ship, including the code we did not write</h1>
    <p class="lede">{html.escape(para)}</p>
    <p class="byline">Chris Roadfeldt. A blueprint, a working implementation, and real runs. Pick an audience in the rail to see the recommended reading path.</p>
  </header>
  <section class="doc" id="doc-read"><div class="eyebrow">Start here</div>
    <h1>How to read a run</h1>
    <p>Every run tells one story in three layers. Each layer is written by the harness from its own records, so they never disagree.</p>
    <ol>
      <li><strong>The story.</strong> Every run folder opens with a <code>README.md</code>: who, what, why, where, when; the outcome in plain terms; the decisions the harness made; the actions it took and the ones it did not take by design; the UDLM records in plain terms; and every file with the reader it is for. The same story is the top of each page under <a href="runs/index.html">Runs</a>.</li>
      <li><strong>The pull request.</strong> Tests reach a repository only through a pull request a person merges. <code>packet/&lt;package&gt;/pull-request.md</code> shows the text and the file list that pull request carries, whether or not one was opened; a review packet sits beside it with the verdict per test, the findings and the draft VEX statements.</li>
      <li><strong>The evidence.</strong> Everything else in the folder is the proof and the replay: sandbox runs, prompts and responses, signed statements, sealed records. Each file is labelled with its audience and its reason in the run's index and in <a href="#doc-10">document 10</a>, so nothing is there without saying why.</li>
    </ol>
    <p>The nearest complete example: <a href="runs/frc-scheduler-server/pr-fix-known-vulns-run6/index.html">frc-scheduler-server, run 6</a>, which went from a dependency bump through a test pull request to a person's merge and the realized records.</p>
  </section>
  {"".join(sections)}
  <footer class="foot">Documentation and blueprint files are licensed under Apache-2.0. Built from the repository markdown by <code>tools/build-site.py</code>.</footer>
</main>
</div>
<script>{JS}</script>
</body>
</html>
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
DECKS = [("executive", "Executives"), ("funding", "Funding decision"), ("builder", "Build or run it"), ("public", "Readers"), ("deck", "Full deck")]
slides_out = OUT.parent / "slides"
slides_out.mkdir(exist_ok=True)
for name, label in DECKS:
    src = ROOT / "slides" / f"{name}.md"
    if src.exists():
        render_deck(src, slides_out / f"{name}.html", [(n, l) for n, l in DECKS if (ROOT / "slides" / f"{n}.md").exists()])
        (slides_out / f"{name}.md").write_text(src.read_text())
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB), {len(DOCS)} docs")

# One page per run, from the run indexes, plus the runs index.
_spec2 = _ilu.spec_from_file_location("build_runs", ROOT / "tools" / "build-runs.py"); _runs = _ilu.module_from_spec(_spec2)
_runs.SITE = OUT.parent
_spec2.loader.exec_module(_runs); _runs.SITE = OUT.parent; _runs.main()
