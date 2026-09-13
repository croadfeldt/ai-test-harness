# Workflows, process maps, and RACI

**For:** everyone who will touch the harness. Each item below has a trigger, a process map, a RACI, its
inputs and outputs, and a service level. Diagrams are Mermaid and render on GitHub and in the slide deck.

## Roles

| Code | Role | Who |
|---|---|---|
| **HT** | Harness Team | Owns the pipeline, adapters, prompts, and the relevance engine |
| **PT** | Product Team | Owns the repository the change lands in; reviews packets for depth 0 and 1 |
| **PS** | Product Security | Reviews `security` findings, confirms VEX statements, owns embargo |
| **SCS** | Supply Chain Security | Reviews `suspicious` findings, owns the pre-flight gates and the merge block |
| **QE** | Quality Engineering | Co-reviews promotions to the standard suite, owns test conventions |
| **PLAT** | Platform | Konflux, OpenShift, Testing Farm, Trusted Artifact Signer, Trustify operators |
| **LEG** | Legal | License review for reused components and upstream contributions |
| **SPO** | Executive Sponsor | Funds phases, resolves cross-team disputes, receives the quarterly report |

RACI: **R** does the work. **A** owns the outcome, exactly one per row. **C** is consulted before.
**I** is informed after.

## Summary RACI across all workflows

| Workflow | HT | PT | PS | SCS | QE | PLAT | LEG | SPO |
|---|---|---|---|---|---|---|---|---|
| 0 Self-verification | R/A | | | I | | C | | |
| 1 Intake and inventory | R/A | I | I | C | | C | | |
| 2 Analysis and risk scoring | R/A | C | C | C | | | | |
| 3 Test generation | R/A | C | | | C | | | |
| 4 Execution and validation | R/A | I | | | | C | | |
| 5 Triage | R/A | I | C | C | | | | |
| 6 Review and merge | C | R/A | C | C | C | | | I |
| 7 Feedback and prompt evaluation | R/A | C | | | C | | | I |
| 8 Promotion to standard suite | R | A | | | C | | | |
| 9 Test retirement | R | A | | | C | | | |
| 10 CVE-targeted tests and VEX | R | I | A | C | | I | | |
| 11 Provenance and SLSA attestation | R | I | C | C | | A | | |
| 12 Prompt and model change | R/A | I | C | C | C | I | | I |
| 13 New ecosystem adapter | R/A | C | | | C | C | C | |
| 14 Reusing an open source component | R/A | | C | C | | C | C | |
| 15 Quarterly report | R | C | C | C | C | | | A |
| F1 Description fidelity (future) | R/A | C | C | C | | | | |
| F2 Malicious change detection (future) | R | C | A | C | | | | I |

---

## 0. Self-verification

**Trigger.** Every harness PipelineRun, before intake.

```mermaid
flowchart LR
    R[PipelineRun starts] --> SC[Run every self-check in the failure register]
    SC --> SB[Probe the sandbox: no network, no env, read-only, offline install]
    SB --> M[Probe the model endpoint: id, reasoning and sampling settings]
    M --> OK{All pass?}
    OK -- yes --> REC[selfcheck record written, attested with the run] --> S1[Stage 1]
    OK -- no --> STOP[Stop. No evidence produced. Harness Team notified]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Maintain the register and its self-checks | HT | HT | QE | SCS |
| Run self-checks | HT (automated) | HT | | |
| Act on a failing check | HT on-call | HT | PLAT | SCS |
| Add an entry for a new failure mode | HT | HT | QE, PS, SCS | |

**Outputs.** `selfcheck.json`: every check, its register id, pass or fail. **Service level.** Under
two minutes. A failing check blocks the run; there is no override.

---

## 1. Intake and inventory

**Trigger.** Konflux snapshot ready; PR opened or updated; lockfile or SBOM diff; scheduled rescan.

```mermaid
flowchart LR
    T[Trigger] --> H[Hermeto graph + SBOM]
    H --> M[Mobster: diff vs last known-good]
    M --> PF{Pre-flight gates:\nMalicious Packages,\nGuardDog, Capslock}
    PF -- hit --> SUS[Mark suspicious,\nnotify SCS, continue in sandbox only]
    PF -- clean --> WL[Work list:\npackage, versions, depth,\nreachable, preflight]
    SUS --> WL
    WL --> A2[Stage 2]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Configure triggers per repo | HT | HT | PT, PLAT | |
| Resolve graph and SBOM | HT (automated) | HT | PLAT | |
| Run pre-flight gates | HT (automated) | HT | SCS | |
| Handle a pre-flight hit | SCS | SCS | HT | PT, PS |

**Inputs.** Snapshot, previous SBOM, gate databases. **Outputs.** Work list, SBOM diff, pre-flight
findings. **Service level.** Work list within 10 minutes of trigger.

---

## 2. Analysis and risk scoring

**Trigger.** Work list row.

```mermaid
flowchart TB
    W[Work list row] --> API[API surface: CLDK / language tooling]
    W --> DIFF[Source diff + API contract diff]
    W --> CS[Our call sites]
    W --> UT[Upstream tests]
    W --> VULN[Known CVEs + affected symbols]
    W --> SA[Static analysis]
    W --> NOTES[Release notes: untrusted]
    API & DIFF & CS & UT & VULN & SA & NOTES --> RS[Risk score]
    RS --> BUD[Generation budget]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Extract facts with tools | HT (automated) | HT | | |
| Maintain risk score weights | HT | HT | PS, SCS, PT | |
| Override budget for a package | PT or PS | HT | | |

**Outputs.** Fact bundle per row, risk score, budget. **Service level.** 15 minutes per row at depth 0
and 1.

---

## 3. Test generation

**Trigger.** Fact bundle with a nonzero budget.

```mermaid
flowchart LR
    FB[Fact bundle] --> P[Prompt: facts as data]
    P --> LLM[Model]
    LLM --> C{Compiles?}
    C -- no, retry < N --> P
    C -- no, retry = N --> LOG[Log and drop]
    C -- yes --> BASE{Passes on baseline?}
    BASE -- no --> P
    BASE -- yes --> IMP{Adds coverage or\nkills a new mutant?}
    IMP -- no --> DROP[Discard]
    IMP -- yes --> CAND[Candidate test + manifest entry]
```

Runs once per category: unit, functional, negative, CVE-targeted, fuzz, harness code.

| Step | R | A | C | I |
|---|---|---|---|---|
| Own prompts and acceptance criteria | HT | HT | QE, PT | |
| Generate and self-repair | HT (automated) | HT | | |
| Decide the ecosystem's idiomatic framework | HT | HT | QE, PT | |
| Label proposed production fixes | HT (automated) | HT | PT | |

**Outputs.** Candidate tests, JSON manifest, proposed fixes as separate patches. **Service level.**
Within budget; never exceeds the per-item token and time caps.

---

## 4. Execution and validation

**Trigger.** Candidate tests exist.

```mermaid
flowchart LR
    C[Candidates] --> SB[Sandbox: no network,\nno secrets, gVisor/Kata]
    SB --> S1[1 Compile]
    S1 --> S2[2 Run]
    S2 --> S3[3 Flake re-run]
    S3 --> S4[4 Coverage]
    S4 --> S5[5 Mutation, diff-scoped]
    S5 --> S6[6 Differential old vs new]
    S6 --> S7[7 Relevance check on existing tests]
    S7 --> RES[(results.json)]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Sandbox image and runtime policy | PLAT | PLAT | HT, SCS | |
| Execute the gauntlet | HT (automated) | HT | | |
| Select execution target | HT (automated by rules) | HT | PLAT, PT | |
| Bare-metal reservation | PLAT | PLAT | HT | PT |

**Outputs.** results.json, coverage, mutation score, differential diff, relevance findings.
**Service level.** Depth 0 and 1 complete within 60 minutes; fuzzing time-boxed.

---

## 5. Triage

**Trigger.** results.json.

```mermaid
flowchart TB
    R[results.json] --> LOG[Summarize logs]
    LOG --> CLS[Classifier agent:\nevidence, verdict, confidence]
    CLS --> CONF{Confidence above threshold?}
    CONF -- no --> ESC[Escalate to human]
    CONF -- yes --> ROUTE{Class}
    ROUTE --> TB[test-bug: back to generation]
    ROUTE --> BC[behavior-change: note]
    ROUTE --> UC[undocumented-change: flag]
    ROUTE --> DF[defect: issue + reproducer]
    ROUTE --> SEC[security: PS]
    ROUTE --> SUS[suspicious: SCS, block]
    ROUTE --> OB[obsolete / redundant: retirement proposal]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Classify with confidence | HT (automated) | HT | | |
| Set confidence thresholds | HT | HT | PS, SCS | PT |
| Handle escalations | HT on-call | HT | PT | |
| Handle `security` | PS | PS | HT | PT |
| Handle `suspicious` | SCS | SCS | HT, PS | PT, SPO if blocking a release |

**Outputs.** Classified findings, issues opened, merge block state. **Service level.** Classification
within 15 minutes; `suspicious` acknowledged by SCS within one business day.

---

## 6. Review and merge

**Trigger.** Review packet posted.

```mermaid
sequenceDiagram
    participant H as Harness
    participant PR as Pull request
    participant PT as Product Team reviewer
    participant SCS as Supply Chain Security
    participant PS as Product Security
    H->>PR: Review packet + attestation
    alt suspicious or security open
        PR-->>PT: Merge blocked
        SCS->>PR: Resolve or confirm suspicious
        PS->>PR: Resolve or confirm security
    end
    PT->>PR: Approve / edit / reject each test
    PT->>PR: Approve / reject retirements and promotions
    PT->>PR: Merge when policy allows
    PR-->>H: Decisions captured for feedback
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Post the packet | HT (automated) | HT | | PT |
| Review tests, retirements, promotions | PT | PT | QE, HT | |
| Clear a merge block | SCS or PS | SCS or PS | PT | SPO |
| Merge | PT | PT | | HT |
| Mark a packet "harness error" | PT | PT | | HT |

**Service level.** Packet within 2 hours of trigger for depth 0 and 1. Review turnaround is the
product team's normal PR SLA.

---

## 7. Feedback and prompt evaluation

**Trigger.** Reviewer decision recorded; regression caught by an overlay test.

```mermaid
flowchart LR
    D[Reviewer decisions] --> LAB[Labeled examples]
    REG[Regression caught] --> TAG[Tag the test]
    LAB --> EVAL[Eval suite]
    TAG --> METRICS[Quarterly metrics]
    EVAL --> PROMPT[Prompt change PR]
    PROMPT --> GATE{Benchmarks pass?}
    GATE -- yes --> MERGE[Merge prompt change]
    GATE -- no --> PROMPT
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Curate labeled examples | HT | HT | QE | |
| Maintain benchmark suite (BUMP, TDD-Bench, Hamster, eval-dev-quality) | HT | HT | QE | |
| Approve prompt change | HT | HT | PT | SPO |

---

## 8. Promotion to the standard suite

**Trigger.** An `accepted` test meets the promotion criteria.

```mermaid
flowchart LR
    ACC[Accepted test] --> CRIT{Unique mutant kill AND\nsurvived 2 bumps or caught a regression AND\nasserts behavior we depend on?}
    CRIT -- no --> WAIT[Stay accepted]
    CRIT -- yes --> PROP[Harness proposes promotion]
    PROP --> R1[Reviewer 1: PT]
    R1 --> R2[Reviewer 2: PT or QE]
    R2 --> STD[Move to standard/, state = standard,\nrecord updated, attestation regenerated]
```

Two human approvals because the standard suite targets SLSA Source L4 and the harness is not a
trusted person.

| Step | R | A | C | I |
|---|---|---|---|---|
| Evaluate criteria and propose | HT (automated) | HT | | PT |
| First approval | PT | PT | | |
| Second approval | PT or QE | PT | HT | |
| Update record and attestation | HT (automated) | PLAT | | |

---

## 9. Test retirement

**Trigger.** Relevance check flags `obsolete` or `redundant`.

```mermaid
flowchart LR
    RC[Relevance finding] --> EV[Attach evidence:\nremoved symbol, deleted lines,\ncovering tests, mutant history]
    EV --> KIND{Target replaced,\nnot removed?}
    KIND -- yes --> REW[Send to generator as rewrite candidate]
    KIND -- no --> PROP[Propose retirement in packet]
    REW --> PROP
    PROP --> APP{Human approves?}
    APP -- no --> KEEP[Keep, note reason]
    APP -- yes --> RET[State = retired,\nrecord keeps reason]
    RET --> SAFE[One safety re-run on next bump]
    SAFE --> STILL{Still guards something?}
    STILL -- yes --> REST[Restore to accepted]
    STILL -- no --> DROP[Drop from execution, record kept]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Detect and propose | HT (automated) | HT | | PT |
| Approve retirement of a generated test | PT | PT | QE | |
| Approve retirement of a human-written test | PT | PT | QE, original author if known | |
| Safety re-run and restore | HT (automated) | HT | | PT |

Retirement proposals never block a merge.

---

## 10. CVE-targeted tests and VEX

**Trigger.** Trustify Dependency Analytics, OSV, or govulncheck reports a vulnerability for a package
version in the graph.

```mermaid
flowchart TB
    CVE[Vulnerability reported] --> LOC[Locate vulnerable symbols:\nadvisory, fix commit, OSV data]
    LOC --> RCH{Reachable from our code?}
    RCH -- yes --> EXP[Exposure test at our call site]
    RCH -- no --> NA[Reachability record]
    EXP & NA --> FIX[Fix-pinning test:\nfails on vulnerable, passes on fixed]
    FIX --> VEX[Draft VEX in CSAF:\naffected / not_affected / fixed]
    VEX --> EMB{Public and fixed?}
    EMB -- no --> RESTRICT[Restricted visibility,\nembargo process]
    EMB -- yes --> PS[Product Security review]
    RESTRICT --> PS
    PS -- confirmed --> TR[Publish to Trustify]
    PS -- rejected --> REDO[Back to harness with reason]
    TR --> PROM[Fix-pinning test promoted to standard]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Generate exposure and fix-pinning tests | HT (automated) | HT | PS | |
| Draft VEX | HT (automated) | HT | | PS |
| Apply embargo and restricted visibility | PS | PS | HT | SCS |
| Confirm or reject VEX | PS | PS | HT, PT | SCS |
| Publish to Trustify | PS | PS | PLAT | PT |
| Promote fix-pinning test | HT | PT | PS | |

**Service level.** Draft VEX within 4 hours of the vulnerability appearing in the graph. Product
Security confirmation per its own SLA.

---

## 11. Provenance and SLSA attestation

**Trigger.** Every harness PipelineRun.

```mermaid
flowchart LR
    RUN[Harness PipelineRun] --> PROV[Konflux SLSA Build provenance]
    RUN --> PRED[Test-evidence predicate:\nevery test produced, promoted, retired,\nevery draft VEX]
    PROV & PRED --> SIGN[Sign: Trusted Artifact Signer,\nkeys never in the sandbox]
    SIGN --> STORE[Attach to artifact, store in Rekor]
    STORE --> CONF[Conforma: verify provenance + predicate vs policy]
    CONF --> VSA[Verification Summary Attestation]
    VSA --> REL{Release policy}
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Define the test-evidence predicate schema | HT | HT | PS, SCS, PLAT | |
| Generate and sign attestations | HT (automated) | PLAT | | |
| Write Conforma policies | SCS | SCS | HT, PS, PT | |
| Verify and emit VSA | PLAT (automated) | PLAT | | PT |
| Measure and report SLSA level achieved | HT | PLAT | SCS | SPO |

---

## 12. Prompt and model change management

**Trigger.** A prompt file changes, or a model version is upgraded.

```mermaid
flowchart LR
    CH[Prompt or model change PR] --> BENCH[Run benchmark suite]
    BENCH --> CMP{Metrics within tolerance\nof current baseline?}
    CMP -- no --> REJ[Reject or iterate]
    CMP -- yes --> REV[Code review as for any source]
    REV --> MERGE[Merge, record model + prompt hash\nin every subsequent attestation]
    MERGE --> WATCH[Watch acceptance rate for 2 weeks]
    WATCH --> RB{Degraded?}
    RB -- yes --> ROLL[Roll back]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Propose change | HT | HT | | |
| Run benchmarks | HT (automated) | HT | QE | |
| Review | HT (second engineer) | HT | PS, SCS for triage prompts | PT |
| Roll back | HT | HT | | PT, SPO |

---

## 13. Adding an ecosystem adapter

**Trigger.** Roadmap phase or a product team request.

```mermaid
flowchart LR
    REQ[Request] --> TOOLS[Select tools per interface function:\nresolve, extract_api, api_diff, build,\nrun_tests, coverage, mutate, fuzz]
    TOOLS --> LIC[License and activity check]
    LIC --> IMPL[Implement adapter]
    IMPL --> IMG[Pinned sandbox image]
    IMG --> BENCH[Run on a benchmark repo]
    BENCH --> PILOT[Pilot on one product repo]
    PILOT --> GA[Enable by default]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Tool selection | HT | HT | QE, PT | |
| License check | HT | HT | LEG | |
| Sandbox image | PLAT | PLAT | HT, SCS | |
| Pilot | HT | HT | PT | |

---

## 14. Reusing an open source component

**Trigger.** Any new dependency of the harness itself.

```mermaid
flowchart LR
    C[Candidate component] --> L{License permissive?\nApache, MIT, BSD, ISC}
    L -- copyleft --> INV[Invoke as a separate tool only,\nnever vendor or link]
    L -- none --> REJ[Reject until licensed]
    L -- yes --> ACT{Release in the last 12 months?}
    ACT -- no --> ISO[Adopt only behind the adapter interface,\nplan replacement]
    ACT -- yes --> ADOPT[Adopt, record in landscape doc]
    INV --> ADOPT
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Evaluate | HT | HT | LEG, SCS | |
| Approve copyleft-as-tool pattern | LEG | HT | | |
| Update landscape document | HT | HT | | |

---

## 15. Quarterly report

**Trigger.** End of quarter.

Content: regressions and vulnerabilities caught by harness tests that nothing else caught; VEX
statements issued; standard suite growth; tests retired; cost per work item by ecosystem; SLSA level
achieved; reviewer acceptance rate; open risks.

| Step | R | A | C | I |
|---|---|---|---|---|
| Compile | HT | SPO | PT, PS, SCS, QE | All |
| Decide next phase funding | SPO | SPO | HT | All |

---

## F1. Description fidelity (future)

**Trigger.** Any change with a human-written description.

```mermaid
flowchart LR
    D[Diff + API diff + call graph] --> AG[Agent describes the change,\ndescription withheld]
    AG --> CMP[Compare with stated description]
    CMP --> CLS{matches / incomplete /\nmismatch / undisclosed-sensitive}
    CLS --> MECH[Mechanical claim checks:\ntests added? no behavior change?\nfixes CVE? only this dep bumped?]
    MECH --> OUT[Finding in packet, feeds risk score]
    OUT --> ROUTE{mismatch or undisclosed on a dep?}
    ROUTE -- yes --> SCS[Max budget, route to SCS]
    ROUTE -- first-party --> AUTH[Back to author + second reviewer]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Build the check | HT | HT | PS, SCS | PT |
| Act on a mismatch on a dependency | SCS | SCS | HT | PT |
| Act on a mismatch on first-party code | PT | PT | | HT |

---

## F2. Malicious or vulnerable change detection (future)

**Trigger.** Any change, any party, any depth.

```mermaid
flowchart TB
    CH[Change] --> SCD[Security-control delta:\nremoved checks, weakened TLS,\ndisabled tests, build/CI/install files]
    CH --> CAP[Capability delta:\nnew network, exec, fs, env,\nreflection, crypto]
    CH --> BG[Build-graph delta:\nnew packages at any depth]
    CH --> PROV[Provenance anomalies:\nsigning, first-time contributor\non sensitive files, cadence]
    CH --> FID[Description fidelity F1]
    SCD & CAP & BG & PROV & FID --> COMB[Combine with confidence]
    COMB --> IND[malicious-indicator finding]
    IND --> GATE{Deterministic signal corroborates?}
    GATE -- yes --> BLOCK[Block merge, route]
    GATE -- no --> ADV[Advisory, route]
    BLOCK & ADV --> WHO{Party}
    WHO -- third party and deeper --> SCS[Supply Chain Security]
    WHO -- first or second party --> PS[Product Security,\nreviewer other than author]
```

| Step | R | A | C | I |
|---|---|---|---|---|
| Build the deltas | HT | HT | PS, SCS | |
| Investigate third-party indicator | SCS | SCS | HT, PS | PT |
| Investigate first- or second-party indicator | PS | PS | HT, SCS, PT lead | SPO |
| Decide block policy | SCS and PS | PS | HT, PT | SPO |
