# Reading the artifacts

**For:** anyone handed a run of the harness. One section per role; each names the one file to open first,
what it says, and what to do with it. A run is a directory; every stage writes into its own
subdirectory, and every number in a packet points at a file in that directory.

## The shape of a run

```
<run>/
  README.md                the story: who, what, why, where, when; outcome, decisions, actions; the records in plain terms
  run.json                 what was run, with what tools, on which repository (by name, never a path)
  run-index.json           what the run holds: stages, packages, headline numbers, and where every file is, each labelled with its reader
  selfcheck/               stage 0: every register check, the sandbox probe, the model probe
  intake/                  the dependency graph at base and head, the SBOM, known vulnerabilities, the work list
  analyze/<package>/       facts: API surface and diff, call sites, advisories, the risk score, the fix diff
  generate/<package>/      the candidate tests, the manifest, every prompt and response under model-calls/
  execute/<package>/       verdicts per test on head, re-run and base; coverage; mutation/; relevance.json
  triage/<package>/        every verdict and finding classified, with confidence and a route
  packet/<package>/        packet.md, the tests as a patch, the draft VEX, pull-request.md (what the test pull request carries)
  attest/<package>/        the provenance record per test, the signed statement, the UDLM records
  assess/                  the run against the blueprint's eleven goals
  propose/<package>/       the test pull request the harness opened, and what it put on the branch
  feedback/<package>/      what a person accepted, edited or rejected; the realized records; a signed statement
```

## One story, three layers

A run produces a lot of files. They are there for a reason, and the reason is written down, but a
reader should never need them to understand what happened. Every run tells one story in three layers,
each written by the harness from its own records so they cannot disagree.

1. **The story.** `README.md` at the top of the run: who did the work and who decided, what was
   tested, why it earned the budget it got, where it ran, when; the outcome in the packet's plain terms;
   the decisions the harness made (what it cut, what it accepted, what it escalated); the actions it
   took and the ones it did not take by design; the UDLM records as one plain sentence each; and every
   file in the folder with the reader it is for. The site shows the same story at the top of each run
   page. Start here whoever you are.
2. **The pull request.** Tests reach a repository only through a pull request that a person merges.
   `packet/<package>/pull-request.md` is the text and the file list that pull request carries, written
   at packet time whether or not the run went on to open one, so a reader sees exactly what a reviewer
   would be asked to accept. `packet.md` beside it is the reviewer's brief: the verdict per test, the
   findings, the draft VEX statements.
3. **The evidence.** Everything else is proof and replay: the sealed sandbox runs, every prompt and
   response, the signed statements, the sealed records. Each of those files carries a label in
   `run-index.json` saying who it is for and why it exists; the appendix at the end of this document
   is that same table.

`run-index.json` at the top of every run says which stages wrote, which packages the run holds, the
headline numbers, and where each file is, so a reader or a renderer never has to know this layout by
heart. The site renders one page per run from it: what each stage read, did and wrote, the results per
package, the assessment, and every artifact linked, at
[croadfeldt.github.io/ai-test-harness/runs](https://croadfeldt.github.io/ai-test-harness/runs/).

Three rules hold everywhere. The harness never merges, publishes or deletes; every file is a proposal.
A test is "proven" only when it fails on the vulnerable version and passes on the fixed one, both runs
kept. "Unproven" is stated, never hidden behind a green test.

## If you are reviewing the change

Open `packet/<package>/packet.md`. Read the first paragraph: the verdict in plain words, what the change
did, what was proven, what was not, what to do. Then:

| Section | What it tells you | What to do |
|---|---|---|
| Tests | one row per test: outcome on the old and new version, its class, and the action | accept, edit or reject each; the rows say which are evidence and which are characterization |
| Findings | anything the run surfaced that the diff does not show, with a route | act on the route; a `suspicious` finding blocks the merge until Supply Chain Security clears it |
| Draft VEX statements | one per advisory, with the basis | forward to Product Security; do not publish |
| Promotions and retirements | tests that earned promotion, and existing tests the change makes obsolete or redundant, with evidence | approve or decline; nothing is deleted |
| Artifacts | where every number came from | open the file if you doubt a number |

The tests themselves are `packet/<package>/tests.patch`, in the layout of the overlay repository, or under
`tests/` for the application's own code. In the pipeline's loop the same content arrives as a pull
request on the overlay repository with this packet as its text; review it like any contributor's.
Budget about a minute per package.

## If you are Product Security

Open `packet/<package>/vex.openvex.json`. Each statement's `status` is a draft: `fixed` only when a
fix-pinning test proved it, `affected` when the advisory is open at head and the application reaches the
package, `under_investigation` otherwise; the basis is in the statement. For any `fixed`, the proof is the
test named in the basis and its two runs, `execute/<package>/old/` and `new/` (or `fixed-candidate/`),
logs included. A `blocked on both versions` verdict in `execute/<package>/results.json` is a reproducer
for a possible defect in the package itself, worth a look on its own.

## If you are Supply Chain Security or an auditor

Open `attest/<package>/`. `statement.dsse.json` is the in-toto test-result statement signed as a DSSE
envelope; `signer.pub.pem` verifies it, and `attest.json` says which key (a development key today,
Trusted Artifact Signer in Konflux). Its subjects are the patch, the provenance record and each evidence
record's head, so a signature check binds all three. `MANIFEST.json` is the provenance record per test:
the model and endpoint by label and digest, the prompt and response digests, the sandbox image digest,
the verdicts. `udlm/` holds the same facts as sealed records: the vulnerability, the package, the run as
a job, one test-evidence record per accepted test, the draft VEX; `udlm/index.json` says whether they
sealed and validated. After a person accepted the pull request, `feedback/<package>/` adds the requested
and realized records for what landed and a signed acceptance statement naming the merge commit.

To verify a statement on this machine:

```
cd harness && .venv/bin/python -c "from pathlib import Path; from harness.stages.attest import verify; \
print(verify(Path('<run>/attest/<package>/statement.dsse.json'), Path('<run>/attest/<package>/signer.pub.pem')))"
```

## If you lead the engineering team

Open `assess/assess.md`: eleven goals from the blueprint, each with the measurement, the verdict and the
file it was measured from. Whether a run can be trusted is answered there, not in the packet. Then
`execute/summary.json` for the counts, `execute/<package>/mutation/mutation.json` for how strong the
accepted tests are (score, and which test killed which mutant), and `execute/<package>/relevance.json`
for what the change makes obsolete or redundant among the tests you already have. The roll-up across
every run is [11-evidence-rollup.md](11-evidence-rollup.md).

## If you are the developer who ran it

You are lifecycle A (blueprint 5.0). Read the packet, keep the tests that look right from
`tests.patch`, drop or edit the rest, and run again if you changed the code; your pull request carries
the tests and the records. Two things to know: `generate/<package>/manifest.json` lists what was
discarded and why, with the last problem the model was sent back for; and `generate/<package>/scratch/`
holds every attempt that ran in the sandbox, so a cut test can be recovered.

## If you want to know why the harness did something

`generate/<package>/model-calls/` has every prompt and every response, numbered, with the call's settings
and token counts; for the tool-using variant, every tool call and result as the model saw it.
`selfcheck/selfcheck.json` is stage 0: which register checks ran and what the probes found.
`run.json` names the tools and versions. Nothing about the machine, the network or the account that ran
it is recorded: endpoints appear as a label and a digest, repositories by name.

## Appendix: every file, its reader, its reason

Six audiences: everyone; reviewers (the developer or team that owns the change); Product Security;
Supply Chain Security and auditors; the person who ran the harness; and tools, for files kept as proof
and replay that nobody is expected to read. Paths are shown without the package directory; in a run
they sit under `<stage>/<package>/`.

<!-- catalogue:start -->

Generated from `harness/src/harness/runindex.py` by `tools/catalogue.py`; the run index carries the same
label on every file it lists, and the story at the top of each run groups the files by it.

**Everyone**

| File | What it is for |
|---|---|
| `README.md` | The story of this run: who, what, why, where, when, the outcome, the decisions and the actions. |
| `assess/assess.md` | The run against the blueprint's eleven goals, each with the measurement and the file it came from. |

**Reviewers (the developer or team that owns the change)**

| File | What it is for |
|---|---|
| `intake/worklist.json` | The work list: every package at base and head, what changed, what is reachable, what carries advisories. |
| `analyze/facts.json` | The fact bundle for one package: versions, API diff, call sites, advisories, the risk score and the budget it earned. |
| `analyze/api-diff.json` | Every added, removed or changed public symbol between the two versions, with a breaking flag. |
| `generate/tests/` | The candidate test files as generated, before any decision. |
| `execute/results.json` | The verdict per test: outcome on head, on the re-run and on the other version, coverage, and how each was judged. |
| `execute/mutation/mutation.json` | How strong the accepted tests are: which mutants of the package's source they killed, and the score. |
| `execute/relevance.json` | Which existing tests this change makes obsolete or redundant, proposed with evidence; nothing is deleted. |
| `triage/triage.json` | Every verdict and finding classified, with a confidence and a route; below the threshold a person decides. |
| `packet/packet.md` | The review packet: the verdict in plain terms, one row per test, the findings, the VEX drafts, the retirements, the recommended action. |
| `packet/tests.patch` | The accepted tests as a patch in the layout they will live in. |
| `packet/pull-request.md` | The text and the file list the test pull request carries, whether or not one was opened. |
| `propose/pull-request.md` | The pull request's text as posted. |

**Product Security**

| File | What it is for |
|---|---|
| `intake/vulns.json` | Known vulnerabilities for every package version in either graph, from OSV, including malicious-package reports. |
| `analyze/vulns.json` | The advisories on this package's versions, with the symbols they name and the fixed versions. |
| `analyze/fixed-candidate.json` | When the change left a vulnerable version in place: the environment the harness resolved with the fixed version, and what had to move. |
| `packet/vex.openvex.json` | One draft VEX statement per advisory, with its basis; a proposal for Product Security, never published by the harness. |

**Supply Chain Security and auditors**

| File | What it is for |
|---|---|
| `run.json` | What was run, with which tool versions, on which repository by name. |
| `selfcheck/selfcheck.json` | Stage 0: every failure-register check and the sandbox and model probes, before any evidence was produced. |
| `intake/sbom.new.cdx.json` | The software bill of materials at head, CycloneDX. |
| `generate/model-calls/` | Every prompt and every response, numbered, with the call's settings; the full transcript of what the model saw and said. |
| `attest/MANIFEST.json` | The provenance record per accepted test: model, prompt and response digests, sandbox image digest, verdicts. |
| `attest/statement.json` | The in-toto test-result statement; its subjects are the patch, the record and each evidence record's head. |
| `attest/statement.dsse.json` | The statement signed as a DSSE envelope. |
| `attest/signer.pub.pem` | The public key that verifies the envelope. |
| `attest/attest.json` | Which key signed, whether it verified locally, and what the run could not back. |
| `attest/udlm/` | The same facts as sealed UDLM records: the vulnerability, the package, the run, each accepted test, the draft VEX. |
| `propose/proposal.json` | The branch, the commit, the files and the pull request the harness opened; the signature status. |
| `feedback/acceptance.json` | What a person accepted, edited or rejected on the pull request, and who and when. |
| `feedback/acceptance-statement.dsse.json` | The signed acceptance statement naming the merge commit and each realized record. |
| `feedback/udlm/` | The requested and realized records for every accepted test: the reviewer's act, and the test as it landed. |

**The person who ran the harness**

| File | What it is for |
|---|---|
| `analyze/source-diff.patch` | The package's own source diff between the versions; the model reads it to find the fix. |
| `analyze/notes.untrusted.md` | Package metadata and description as published upstream; untrusted text, kept for context. |
| `generate/manifest.json` | What was generated: every file, every test, what was cut and discarded and why, the model, the prompt and response digests. |
| `generate/manifest.agent.json` | The tool-using agent's traces: every tool call per advisory, and the budget it had. |

**Tools (kept for replay and proof; not meant to be read)**

| File | What it is for |
|---|---|
| `run-index.json` | What this run holds: stages, packages, headline numbers, and where every file is; the renderers read it. |
| `intake/graph.new.json` | The dependency graph at head as the ecosystem's own resolver produced it. |
| `intake/graph.old.json` | The dependency graph at base. |
| `analyze/api.new.json` | The public API surface at head, extracted by tools. |
| `analyze/api.old.json` | The public API surface at base. |
| `analyze/call-sites.json` | Every place the application references this package. |
| `generate/scratch/` | Every attempt that ran in the sandbox during generation, with its output; not committed. |
| `execute/new/` | The sealed run on head: the run script, the junit report, coverage, logs. |
| `execute/new-rerun/` | The second run on head, to catch flakes. |
| `execute/old/` | The run on the base version, for the differential. |
| `execute/fixed-candidate/` | The run on the resolved fixed version, for the differential when the change did not move the package. |
| `execute/mutation/mutants/` | Each sampled mutant: the mutated file and its sealed run. |
| `packet/packet.json` | The packet's facts in structured form. |
| `assess/assess.json` | The assessment in structured form. |
| `feedback/decisions.jsonl` | One labeled example per test for prompt evaluation: the decision with the prompt and response digests behind it. |

<!-- catalogue:end -->
