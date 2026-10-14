---
marp: true
theme: default
paginate: false
title: AI Test Harness, in two slides
description: One slide on the problem, the answer and where it sits in delivery; one on how it works, inputs through to outputs
style: |
  section { padding: 28px 52px; font-family: "Red Hat Text", "Overpass", "Open Sans", sans-serif; font-size: 20px; color: #151515; line-height: 1.4; }
  section h1 { color: #EE0000; text-align: center; font-size: 36px; font-weight: 600; margin: 0 0 18px; }
  section p { margin: 0 0 14px; }
  section table { display: table; border-collapse: collapse; width: 100%; font-size: 13px; line-height: 1.25; margin: 0; }
  section th, section td { border: 1px solid #c7c7c7; background: #f0f0f0; padding: 5px 8px; text-align: left; vertical-align: top; }
  section th { font-weight: 700; }
  section h3, section h4 { text-align: center; font-weight: 700; font-size: 14px; letter-spacing: .02em; padding: 5px 8px; margin: 0; text-transform: uppercase; }
  section h3 { background: #EE0000; color: #fff; }
  section h4 { background: #d2d2d2; color: #151515; }

  /* slide one: the comic floats left with its source line, the words wrap beside it, the delivery strip clears below */
  section.one p:first-of-type { float: left; width: 240px; margin: 2px 40px 10px 0; font-size: 11px; color: #6a6e73; line-height: 1.3; }
  section.one img { display: block; width: 240px; border: 1px solid #151515; margin-bottom: 4px; }
  section.one h2 { clear: both; color: #EE0000; font-size: 15px; font-weight: 600; margin: 10px 0 8px; padding-top: 12px; border-top: 1px solid #d2d2d2; }
  section.one table th { font-weight: 600; background: #f0f0f0; vertical-align: middle; width: 9%; }
  section.one table th:nth-child(even) { border: 0; background: #fff; text-align: center; color: #6a6e73; width: 1.5%; padding: 0; }
  section.one table th:nth-child(7) { background: #EE0000; color: #fff; border-color: #EE0000; width: 16%; }
  section.one table th:nth-child(9) { border: 2px solid #151515; width: 15%; }
  section.one table th:nth-child(13) { width: 14%; }
  section.one table th em { display: block; font-style: normal; font-weight: 400; font-size: 11px; color: #4f5255; margin-top: 2px; }
  section.one table th:nth-child(7) em { color: #ffd6d6; }
  section.one p:last-of-type { font-size: 12px; color: #4f5255; margin-top: 8px; }

  /* slide two: a heading and a paragraph pinned on the left, the layered diagram flowing on the right */
  section.two h2 { position: absolute; left: 52px; top: 200px; width: 340px; color: #EE0000; font-size: 24px; font-weight: 600; margin: 0; }
  section.two > p:first-of-type { position: absolute; left: 52px; top: 290px; width: 340px; font-size: 19px; line-height: 1.35; margin: 0; }
  section.two h3, section.two h4, section.two table, section.two p { margin-left: 440px; width: calc(100% - 440px); box-sizing: border-box; }
  section.two p:not(:first-of-type) { text-align: center; color: #6a6e73; font-size: 14px; line-height: 1; margin-top: 2px; margin-bottom: 2px; }
  section.two table th, section.two table td { text-transform: uppercase; }
  section.two table em { display: block; text-transform: none; font-style: italic; font-size: 12px; color: #4f5255; }
  section.two table code { font-family: "Red Hat Mono", monospace; text-transform: none; background: none; color: #151515; padding: 0; }
  section.two table:nth-of-type(3) td:last-child { text-align: right; font-weight: 700; }
  section.two table:nth-of-type(3) tr:nth-child(1) td:last-child { color: #3e8635; }
  section.two table:nth-of-type(3) tr:nth-child(3) td:last-child { color: #6a6e73; }
---

<!-- _class: one -->

# AI Test Harness

![w:240](xkcd-1172-workflow.png)
“Workflow” by Randall Munroe, xkcd.com/1172. Licensed CC BY-NC 2.5, creativecommons.org/licenses/by-nc/2.5. Unchanged.

Most of what a product ships is code its own team never wrote. Dependencies move, advisories land, and the tests that would prove a change is safe never get written, so the gate runs on trust.

The AI Test Harness writes those tests, runs them sealed on both sides of every change, and puts the evidence on the pull request: a signed record anyone can verify, an answer for every known vulnerability, and a plain account of what is proven, what is handed to you, and what is still a gap.

## Where it sits in your delivery flow

| Code | → | Pull request | → | Your CI | + | AI Test Harness *tests both versions, signs the evidence* | → | Gate *decides on evidence; either side can say no* | → | Merge | → | Build and release *signed records and VEX travel with it* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

An advisory or a dependency bump enters the same flow as a change, so a fix is proven the same way a feature is.

---

<!-- _class: two -->

# AI Test Harness

## From a change to evidence at the gate

The harness reads a change and everything it touches, writes the tests nobody will write by hand, and runs them sealed on both versions. Every behaviour the change reaches ends in one of three states. The evidence lands on the pull request, where a person and the gate decide.

### What it reads

| 1. Your change | 2. Your dependencies | 3. Known vulnerabilities | 4. Your existing tests |
|---|---|---|---|
| code before and after | every package, both versions | public advisories | what is already covered |
| what your code actually uses | how deep the change goes | what is already known to be wrong | what your pipeline can run |

▼

#### What it does

| Writes tests from facts, never guesses | Breaks the code on purpose to see if they notice | Runs them sealed, both versions, several times |
|---|---|---|

▼

#### Every behaviour the change reaches ends in one of three states

| Reached | What happened | State |
|---|---|---|
| `decode()` | the test catches the breakage | **Validated** |
| `upload()` | needs your network, not the sealed box | **Handed to you** |
| `native()` | no test survived scoring | **Named gap, with its reason** |

▼

### What you get, on the pull request

| The tests and their evidence | An answer per known vulnerability | A signed record anyone can verify |
|---|---|---|
| *a person decides to merge* | *a draft VEX your security team confirms* | *in-toto, SLSA, OpenVEX* |
