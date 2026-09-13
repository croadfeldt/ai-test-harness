# Contributing

## Two rules, in order

1. **Quality of results.** A verdict is only worth publishing when the evidence behind it is real and
   traceable. Nothing here trades correctness for readability.
2. **Communication.** A result nobody can read loses its value, its context, and the chance to be
   shared. So everything a person reads is written to be understood.

## How everything here is written

The second rule applies to every document, packet, assessment, commit message, pull request, and page
in this repository, and to the harness's own outputs.

- **Plain English, easily readable.** A reviewer who is not a specialist should follow it.
- **Concise over detail.** Say what was found and what to do. Leave out what does not change a
  decision.
- **Detail only where it adds a quantitative result.** A number earns its place when it changes what
  the reader does; then it goes in a short table, not a sentence.
- **Lead with the verdict.** The first line says what happened. Evidence follows.
- **Name a file only when the reader must open it.** Tool names and internal labels stay out of prose.

A packet that takes a minute to read and tells a reviewer what to do is the whole point of the harness.
Writing that fails this rule is a defect, the same as a test that fails.

## Changes

Work on a branch, open a pull request to `main`. CI runs the harness's stage 0 self-checks and unit
tests. The site republishes from `main` on merge.

## The failure register

When the generator fails in a new way, write the register entry and its self-check first (blueprint
section 17), watch the check fail, then fix it.
