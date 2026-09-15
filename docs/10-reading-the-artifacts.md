# Reading the artifacts

**For:** anyone handed a run of the harness. One section per role; each names the one file to open first,
what it says, and what to do with it. A run is a directory; every stage writes into its own
subdirectory, and every number in a packet points at a file in that directory.

## The shape of a run

```
<run>/
  run.json                 what was run, with what tools, on which repository (by name, never a path)
  selfcheck/               stage 0: every register check, the sandbox probe, the model probe
  intake/                  the dependency graph at base and head, the SBOM, known vulnerabilities, the work list
  analyze/<package>/       facts: API surface and diff, call sites, advisories, the risk score, the fix diff
  generate/<package>/      the candidate tests, the manifest, every prompt and response under model-calls/
  execute/<package>/       verdicts per test on head, re-run and base; coverage; mutation/; relevance.json
  triage/<package>/        every verdict and finding classified, with confidence and a route
  packet/<package>/        packet.md, the tests as a patch, the draft VEX
  attest/<package>/        the provenance record per test, the signed statement, the UDLM records
  assess/                  the run against the blueprint's eleven goals
  propose/<package>/       the test pull request the harness opened, and what it put on the branch
  feedback/<package>/      what a person accepted, edited or rejected; the realized records; a signed statement
```

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
