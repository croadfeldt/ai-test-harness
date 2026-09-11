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
DOCS = sorted((ROOT / "docs").glob("*.md"))
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site" / "index.html"

AUDIENCES = [
    ("exec", "Executive", "CEO, managing director, board", ["00"], "5 min"),
    ("fund", "Funding decision", "CTO, VP Engineering, CISO", ["00", "01", "07"], "20 min"),
    ("build", "Build or run it", "Engineer, architect, security analyst", ["02", "03", "05", "06", "09", "bp"], "2 h"),
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

page = f"""<title>AI Test Harness</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@500;700;900&family=Red+Hat+Text:ital,wght@0,400;0,500;1,400&family=Red+Hat+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
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
    <div class="rail-foot">Diagrams are Mermaid. Slide deck and sources live in the repository.</div>
  </div>
</nav>
<main id="main">
  <header class="hero" id="top">
    <div class="eyebrow">Blueprint and working draft</div>
    <h1>Tests for every piece of code we ship, including the code we did not write</h1>
    <p class="lede">{html.escape(para)}</p>
    <p class="byline">Chris Roadfeldt. A design, not yet running code. Pick an audience in the rail to see the recommended reading path.</p>
  </header>
  {"".join(sections)}
  <footer class="foot">Documentation and blueprint files are licensed under Apache-2.0. Built from the repository markdown by <code>tools/build-site.py</code>.</footer>
</main>
</div>
<script>{JS}</script>
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB), {len(DOCS)} docs")
