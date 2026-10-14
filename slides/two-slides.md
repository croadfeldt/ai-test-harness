---
marp: true
theme: default
paginate: false
title: AI Test Harness, in two slides
description: One slide on the problem, the answer and where it sits in delivery; one on how it works, inputs through to what you get
html: true
style: |
  section { padding: 28px 52px; font-family: "Red Hat Text", "Red Hat Display", "Overpass", "Open Sans", sans-serif; font-size: 20px; color: #151515; }
  section h1 { color: #EE0000; text-align: center; font-size: 36px; font-weight: 600; margin: 0 0 18px; }
  .two { display: flex; gap: 48px; align-items: flex-start; }
  .two figure { margin: 0; flex: 0 0 300px; }
  .two figure img { width: 300px; border: 1px solid #151515; background: #fff; }
  .two figure figcaption { font-size: 12px; color: #6a6e73; margin-top: 6px; }
  .two .text { flex: 1; font-size: 20px; line-height: 1.4; padding-top: 4px; }
  .stat { flex: 0 0 300px; padding-top: 4px; }
  .statlabel { font-weight: 600; font-size: 15px; margin-bottom: 8px; }
  .bar { display: flex; flex-direction: column; height: 250px; border: 1px solid #151515; }
  .seg { display: flex; flex-direction: column; justify-content: center; padding: 0 14px; font-size: 14px; line-height: 1.2; }
  .seg b { font-size: 30px; display: block; }
  .seg.open { background: #d2d2d2; color: #151515; }
  .seg.own { background: #EE0000; color: #fff; }
  .statsrc { font-size: 11px; color: #6a6e73; margin-top: 6px; }
  .sdlc { margin-top: 22px; border-top: 1px solid #d2d2d2; padding-top: 12px; }
  .sdlclabel { color: #EE0000; font-weight: 600; font-size: 15px; margin-bottom: 8px; }
  .lane { display: flex; align-items: stretch; gap: 6px; }
  .step { flex: 1; background: #f0f0f0; border: 1px solid #c7c7c7; padding: 6px 8px; font-size: 13px; font-weight: 600; display: flex; flex-direction: column; justify-content: center; }
  .step i { display: block; font-weight: 400; font-style: normal; font-size: 11px; color: #4f5255; margin-top: 2px; }
  .step.hot { background: #EE0000; color: #fff; border-color: #EE0000; flex: 1.6; }
  .step.hot i { color: #ffd6d6; }
  .step.gate { border: 2px solid #151515; flex: 1.5; }
  .arr, .plus { align-self: center; color: #6a6e73; font-size: 16px; }
  .feed { font-size: 12px; color: #4f5255; margin-top: 8px; }
  .two .text p { margin: 0 0 16px; }
  .left { flex: 0 0 360px; font-size: 20px; line-height: 1.35; padding-top: 110px; }
  .left h2 { color: #EE0000; font-size: 24px; margin: 0 0 14px; font-weight: 600; }
  .diagram { flex: 1; font-size: 13px; line-height: 1.25; text-transform: uppercase; }
  .band { text-align: center; font-weight: 700; padding: 5px 8px; font-size: 14px; letter-spacing: .02em; }
  .band.red { background: #EE0000; color: #fff; }
  .band.grey { background: #d2d2d2; color: #151515; }
  .cols { display: flex; background: #f0f0f0; border: 1px solid #c7c7c7; }
  .cols > div { flex: 1; padding: 6px 8px; border-right: 1px solid #c7c7c7; }
  .cols > div:last-child { border-right: 0; }
  .cols b { display: block; margin-bottom: 2px; }
  .cols i { display: block; text-transform: none; font-size: 12px; color: #4f5255; }
  .rows { background: #f0f0f0; border: 1px solid #c7c7c7; padding: 4px 10px; }
  .rows > div { display: flex; align-items: center; gap: 8px; padding: 3px 0; }
  .rows .fn { font-family: "Red Hat Mono", monospace; text-transform: none; }
  .rows .st { font-weight: 700; margin-left: auto; }
  .dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
  .dot.green { background: #3e8635; } .dot.black { background: #151515; } .dot.grey { background: #8a8d90; }
  .arrow { text-align: center; line-height: 1; font-size: 16px; color: #6a6e73; margin: 1px 0; }
  .steps { background: #f0f0f0; border: 1px solid #c7c7c7; padding: 6px 10px; text-align: center; font-weight: 600; }
---

# AI Test Harness

<div class="two">
<div class="stat">
<div class="statlabel">What a typical codebase ships</div>
<div class="bar">
<div class="seg open" style="flex: 77"><b>77%</b>open source your team never wrote</div>
<div class="seg own" style="flex: 23"><b>23%</b>your own code</div>
</div>
<div class="statsrc">Source: Synopsys OSSRA 2024, share of open source in audited codebases</div>
</div>
<div class="text">

Most of what a product ships is code its own team never wrote. Dependencies move, advisories land, and the tests that would prove a change is safe never get written, so the gate runs on trust.

The AI Test Harness writes those tests, runs them sealed on both sides of every change, and puts the evidence on the pull request: a signed record anyone can verify, an answer for every known vulnerability, and a plain account of what is proven, what is handed to you, and what is still a gap.

</div>
</div>

<div class="sdlc">
<div class="sdlclabel">Where it sits in your delivery flow</div>
<div class="lane">
<div class="step">Code</div><div class="arr">→</div>
<div class="step">Pull request</div><div class="arr">→</div>
<div class="step">Your CI</div><div class="plus">+</div>
<div class="step hot">AI Test Harness<i>tests both versions, signs the evidence</i></div><div class="arr">→</div>
<div class="step gate">Gate<i>decides on evidence; either side can say no</i></div><div class="arr">→</div>
<div class="step">Merge</div><div class="arr">→</div>
<div class="step">Build and release<i>signed records and VEX travel with it</i></div>
</div>
<div class="feed">An advisory or a dependency bump enters the same flow as a change, so a fix is proven the same way a feature is.</div>
</div>

---

# AI Test Harness

<div class="two">
<div class="left">
<h2>From a change to evidence at the gate</h2>
<p>The harness reads a change and everything it touches, writes the tests nobody will write by hand, and runs them sealed on both versions. Every behaviour the change reaches ends in one of three states. The evidence lands on the pull request, where a person and the gate decide.</p>
</div>
<div class="diagram">
<div class="band red">What it reads</div>
<div class="cols">
<div><b>1. Your change</b>• code before and after<br>• what your code actually uses</div>
<div><b>2. Your dependencies</b>• every package, both versions<br>• how deep the change goes</div>
<div><b>3. Known vulnerabilities</b>• public advisories<br>• what is already known to be wrong</div>
<div><b>4. Your existing tests</b>• what is already covered<br>• what your pipeline can run</div>
</div>
<div class="arrow">▼</div>
<div class="band grey">What it does</div>
<div class="steps">Writes tests from facts, never guesses &nbsp;→&nbsp; breaks the code on purpose to see if they notice &nbsp;→&nbsp; runs them sealed, both versions, several times</div>
<div class="arrow">▼</div>
<div class="band grey">Every behaviour the change reaches ends in one of three states</div>
<div class="rows">
<div><span class="fn">[ decode() ]</span> ⟹ the test catches the breakage <span class="st">Validated</span> <span class="dot green"></span></div>
<div><span class="fn">[ upload() ]</span> ⟹ needs your network, not the sealed box <span class="st">Handed to you</span> <span class="dot black"></span></div>
<div><span class="fn">[ native() ]</span> ⟹ no test survived scoring <span class="st">Named gap, with its reason</span> <span class="dot grey"></span></div>
</div>
<div class="arrow">▼</div>
<div class="band red">What you get, on the pull request</div>
<div class="cols">
<div><b>The tests and their evidence</b><i>a person decides to merge</i></div>
<div><b>An answer per known vulnerability</b><i>a draft VEX your security team confirms</i></div>
<div><b>A signed record anyone can verify</b><i>in-toto, SLSA, OpenVEX</i></div>
</div>
</div>
</div>
