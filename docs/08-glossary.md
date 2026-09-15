# Glossary

**For:** anyone. Plain-language definitions of the terms used in this project.

| Term | What it means here |
|---|---|
| **Attestation** | A signed statement, in a machine-readable format, that something happened: this artifact was built from this source, or these tests were run against this package and this is what they found. |
| **Call graph** | A map of which functions call which other functions. It lets us ask "does any of our code ever reach this function in that package?" |
| **Characterization test** | A test that records what code currently does, without judging whether that is correct. Useful for detecting change. |
| **Conforma** | The policy engine in Konflux that checks attestations against rules before something is released. Formerly called Enterprise Contract. |
| **CVE** | Common Vulnerabilities and Exposures. The public identifier for a known security vulnerability, for example CVE-2024-3094. |
| **CVE-targeted test** | A test written specifically to check whether a known vulnerability affects us, and to make sure it stays fixed. |
| **Dependency** | A software package our code uses. A **direct** dependency is one we chose. A **transitive** dependency is one that a dependency pulled in. |
| **Differential testing** | Running the same tests against the old and new version of something and comparing the results. It shows what changed without needing to know in advance what should happen. |
| **Fuzzing** | Feeding a program large volumes of random or semi-random input to find crashes and unexpected behavior. |
| **Functional test** | A test that exercises a package through its public interface the way a real user of it would. |
| **Hermetic build** | A build with no network access, using only dependencies fetched and pinned in advance. It guarantees the build is reproducible and that nothing was pulled in unexpectedly. |
| **Hermeto** | The tool in Konflux that pre-fetches dependencies for hermetic builds and produces the SBOM. |
| **in-toto** | An open standard for the format of attestations. SLSA provenance is an in-toto attestation. |
| **Konflux** | Red Hat's open source software factory: the build and release pipeline this harness runs on. |
| **LLM** | Large language model. The kind of AI that reads and writes text and code. |
| **Mutation testing** | Deliberately introducing small bugs into code and checking whether the tests catch them. A test suite that catches most mutants is strong. One that catches none is decoration. |
| **Negative test** | A test that gives code bad input and checks that it refuses cleanly, rather than crashing or accepting it. |
| **Overlay** | Tests we wrote for a package we do not own, stored in our own repository alongside the package's name and version, because we cannot commit into the upstream project. |
| **Provenance** | The recorded history of an artifact: what it was made from, by what process, by whom, when. |
| **RACI** | A chart of who is Responsible, Accountable, Consulted, and Informed for each step of a process. |
| **Reachability** | Whether our code can actually invoke a particular piece of a dependency. A vulnerability in code we never call is far less urgent than one in code we call on every request. |
| **Sandbox** | An isolated environment for running untrusted code, with no network, no secrets, and strict resource limits. Destroyed after use. |
| **SBOM** | Software Bill of Materials. A complete list of every package in a product, with versions. |
| **SLSA** | Supply-chain Levels for Software Artifacts. A framework of levels that describe how trustworthy the provenance of an artifact is. Build Level 3 is the highest current build level. |
| **Standard suite** | The tests we run every time, for every version. Generated tests that prove their worth are promoted here. |
| **Test retirement** | Removing a test from execution because the code it tested no longer exists or another test now covers it. Retired tests are archived, not deleted. |
| **Trustify** | The open source store for SBOMs, vulnerabilities, and VEX statements that Red Hat Trusted Profile Analyzer is built on. |
| **Unit test** | A test of one function or one small piece of code in isolation. |
| **VEX** | Vulnerability Exploitability eXchange. A statement about whether a known vulnerability actually affects a product, with the reason. "Not affected because we never call the vulnerable function" is a VEX statement. |
| Lifecycle A, the developer's inner loop | A developer runs the harness on their branch while working; the tests they keep go into their own pull request. |
| Lifecycle B, the pipeline's outer loop | The pipeline runs the harness on every change and opens a test pull request; a reader accepts or rejects against the packet. |
| Validation execution | The harness's own run of candidate tests: both versions, sealed, once, at acceptance time. Stage 4. |
| Regression execution | The suite's run of accepted tests: head only, every change, by the CI that already runs the suite. Not a harness stage. |
| Review gate | The point between validation and acceptance where a person decides: code review in lifecycle A, the test pull request in lifecycle B. Tests always arrive through a pull request. |
