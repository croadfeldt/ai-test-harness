---
marp: true
theme: default
paginate: false
title: AI Test Harness, in two slides
description: One slide on the value and the invitation to co-engineer; one on the flow, the data it reads and why
---

<!-- _class: lead -->
<style scoped>
section { font-size: 23px; padding: 50px 70px; }
h1 { font-size: 1.6em; margin-bottom: 0.4em; }
p { margin: 0.45em 0; }
</style>

# How do you know a change is safe when most of what you ship is code your team never wrote?

**You don't. The AI Test Harness gives you the evidence.**

**Every change arrives with proof.** Tests run on both sides of the change and a signed record, on the pull request, for your code and every package you depend on. The gate decides on evidence, not trust.

**Known vulnerabilities get an answer, not a claim.** Proven fixed, proven exposed, or shown unreachable, each backed by a test anyone can rerun and a VEX draft that rests on it.

**A test suite that grows where none existed.** The tests nobody writes by hand get written, run and scored. The ones that earn their keep join your suite, and the review time they cost is measured on every run.

**Proof that travels with the product.** Signed records your customers, auditors and regulators can verify. No silent coverage: every behaviour a change reaches is validated, handed to you, or named as a gap with its reason.

Built in the open, with the teams that use it. Bring a project and shape what it proves next.

---

# How it works: what it reads, what it does, what you get

```mermaid
flowchart LR
    subgraph IN[What it reads, and why]
        direction TB
        R[Your code, before and after the change<br/><i>what changed</i>]
        G[Every package you depend on<br/><i>which ones moved, and how deep</i>]
        A[Public vulnerability advisories<br/><i>what is already known to be wrong</i>]
        API[What your code actually uses<br/><i>what changed underneath you</i>]
        CI[The tests and checks you already have<br/><i>what is already covered</i>]
    end
    subgraph DO[What it does]
        direction TB
        S0[Checks itself before it starts]
        S1[Decides what to test first, by risk]
        S2[Gathers facts about the change; never guesses]
        S3[Writes tests, then breaks the code on purpose to see if they notice]
        S4[Runs them sealed off from the network, on both versions, several times]
        S5[Sorts every result: proven, handed to you, or a named gap]
        S0 --> S1 --> S2 --> S3 --> S4 --> S5
    end
    subgraph OUT[What you get]
        direction TB
        PK[A pull request with the tests and their evidence<br/><i>a person decides to merge</i>]
        VX[An answer for each known vulnerability<br/><i>a draft your security team confirms</i>]
        REC[A signed record anyone can verify<br/><i>open standards, no lock-in</i>]
        FB[What it learned, fed into the next run<br/><i>your decisions teach it</i>]
    end
    IN --> S1
    S5 --> PK --> FB
    S5 --> VX
    S5 --> REC
    FB -.-> S0
```

Everything it reads is a fact from a tool, treated as untrusted. Everything it tells you points to the file it was measured from.
