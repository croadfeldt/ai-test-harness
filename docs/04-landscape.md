# Landscape: Existing Open Source Work Relevant to the AI Test Harness

**Status:** v0.1
**Date:** 2026-09-11
**Companion to:** [03-blueprint.md](03-blueprint.md)
**Decision record:** [05-capability-map.md](05-capability-map.md) turns this inventory into one primary and one fallback per capability, including the orchestration, sandbox, and attestation choices.

This document records what already exists in the open source world that the harness can reuse, learn
from, or must avoid. It was compiled from three research passes on 2026-09-11 covering Red Hat projects,
IBM and IBM Research projects, and the wider ecosystem. Every project listed was verified by fetching its
repository or paper page on that date. Star counts, release versions, and activity dates are as of that
date.

---

## 1. Headline findings

1. **Nobody has shipped the whole thing.** There is no maintained open source project, from Red Hat, IBM,
   or anyone else, that takes arbitrary incoming source code plus its transitive dependencies and generates,
   executes, and validates unit and functional tests end to end. The pieces exist. The assembly does not.
2. **IBM Research has published the closest blueprint but not the code.** ASTER (unit tests), SAINT
   (service-level integration tests), and Sakura (multi-agent functional tests from natural language) are
   the most relevant papers of 2025 and 2026. The tools ship inside watsonx Code Assistant and are not open
   source. The one reusable IBM component is CodeLLM-Devkit, an Apache-2.0 program analysis SDK.
3. **Red Hat's supply chain substrate is mature and is the natural home.** Konflux, Hermeto, Conforma,
   Mobster, Trustify, and Trustify Dependency Analytics already resolve transitive graphs, produce SBOMs,
   prefetch dependencies for hermetic builds, and gate releases on policy. The harness should be a Konflux
   integration test step, not a new pipeline.
4. **Red Hat's AI code-analysis work is in security triage, not test generation.** sast-ai-workflow,
   Aegis AI, and Konveyor Kai are production-shaped patterns for "LLM agent reasons over code with
   confidence scoring." QualityFlow is the only Red Hat repo that generates test code, and it is early stage.
5. **The best-known open LLM test generator is dead.** Qodo-Cover (formerly Cover-Agent), the open
   reimplementation of Meta's TestGen-LLM, is AGPL-3.0 and its README now says "please fork." The maintained
   permissive alternatives are narrower: CoverUp for Python, TestSpark for Java and Kotlin inside an IDE,
   Pynguin as a hybrid search-plus-LLM tool for Python.
6. **Mutation testing is solved per ecosystem.** PIT, StrykerJS, cargo-mutants, mutmut, cosmic-ray, and
   gremlins all shipped releases in 2026. LLM-generated mutants are research grade only.
7. **Differential testing of dependency upgrades exists only at distro scale.** Debian autopkgtest, Rust
   Crater, Julia PkgEval, and R revdepcheck run reverse-dependency tests on upgrades. Nothing generic and
   cross-ecosystem does this for an application. This is the harness's clearest gap to fill.
8. **Reachability is strongest for Go.** govulncheck is the reference. OWASP dep-scan with atom is the
   broadest multi-language open option. CodeLLM-Devkit covers Java (including transitive jars), Python, and
   TypeScript.

---

## 2. Red Hat projects

### 2.1 AI-assisted test generation and code analysis

| Project | What it is | License | AI | Relevance |
|---|---|---|---|---|
| [QualityFlow](https://github.com/redhat-community-ai-tools/qualityflow) | Jira or GitHub issue to test plan to test code, multi-step Claude agent orchestration, LSP call-graph regression analyzer to scope tests. 116 commits, updated June 2026. | Apache-2.0 | Claude, multi-agent | The only Red Hat repo that generates test code. Requirements-driven rather than code-driven. Early stage. Reference architecture and possible starting point. |
| [Konveyor Kai](https://github.com/konveyor/kai) | Static analysis (analyzer-lsp, kantra) finds migration incidents, LLM plus RAG over past solutions generates fixes. CNCF sandbox, Red Hat led, IBM Research supports. | Apache-2.0 | Model-agnostic LLM | Best Red Hat example of "static analysis guides LLM generation." The analyzer-lsp provider model is reusable for multi-language code understanding. No test generation. |
| Konveyor agent-mesh ([blog, Apr 2026](https://www.redhat.com/en/blog/refactoring-speed-mission-agent-mesh-approach-legacy-system-modernization-red-hat-ai)) | "Harness of harnesses" for Python 2 to 3 and Java migration. Agents do dependency mapping and generate characterization tests before changing code. OpenShift AI, vLLM, OpenCode agent. | n/a | Yes | Directly validates the "characterization tests for code and its dependencies" idea. No code released. |
| [sast-ai-workflow](https://github.com/RHEcosystemAppEng/sast-ai-workflow) | LangGraph ReAct agent triages SAST findings for false positives. Confidence 0 to 100, reflection loop, FAISS embeddings, Tekton and OpenShift packaging, Langfuse observability. Companions: sast-ai-orchestrator, sast-pattern-learning. 696 commits, active. Red Hat Ecosystem App Engineering with Product Security and NVIDIA. | Apache-2.0 | Yes | Production-shaped Red Hat pattern for an LLM agent reasoning over code with confidence scoring and Tekton packaging. The harness triage stage should look like this. |
| [Aegis AI](https://github.com/RedHatProductSecurity/aegis-ai) | GenAI agent for CVE and component analysis. Integrates OSIDB, Trustify, osv.dev, CWE, MCP servers. Claude, Gemini, OpenAI, Ollama. 1,739 commits, active. | MIT | Yes | Shows how Red Hat wires an LLM agent to Trustify and SBOM data. Reusable for prioritizing dependencies with known CVEs. |
| Red Hat Research theses ([Apr 2025](https://research.redhat.com/blog/2025/04/21/choosing-llms-to-generate-high-quality-unit-tests-for-code/), [Sep 2025](https://research.redhat.com/blog/2025/09/03/student-research-yields-a-new-tool-for-benchmarking-llm-generated-unit-tests/)) | Comparison of GPT-4o, Gemini 1.5 Pro, DeepSeek-Coder for unit tests in Python, Java, Kotlin, Go. Extended MutPy with per-test mutation score to benchmark LLM tests. Masaryk University, supervised by Marek Grác. | n/a | Yes | Red Hat-affiliated evidence for evaluating generated tests by mutation analysis rather than coverage alone. No code released. |
| [Log Detective](https://github.com/fedora-copr/logdetective) | LLM plus Drain template mining explains failed RPM build logs. Koji, Copr, Packit integration. Public instance at logdetective.com. 921 commits, active. | Apache-2.0 | Yes | Nearest Red Hat production tool for LLM analysis of build and test failure output. Reusable for triaging failing generated tests. |
| [prodsec-skills](https://github.com/RedHatProductSecurity/prodsec-skills) | 138 security skills for AI coding assistants: secure development, supply chain, fuzzing, SAST, MCP and agent security. | Apache-2.0 (some CC BY) | Yes | Drop-in skills for a Claude-based harness. |
| [harness-eval](https://github.com/redhat-community-ai-tools/harness-eval) | Linter for AI coding agent setups: 108 deterministic rules for credential exfiltration chains, hook conflicts, token budget. GitHub Action, Tekton task, Claude Code plugin. | Apache-2.0 | Optional | Hardening the harness's own agent configuration. |
| [openshift-eng/ai-helpers](https://github.com/openshift-eng/ai-helpers) | Claude Code plugin marketplace from OpenShift engineering. 116 stars, 311 forks. | Apache-2.0 | Yes | Pattern for packaging harness capabilities as Claude Code plugins. |
| [code-to-docs](https://github.com/redhat-community-ai-tools/code-to-docs) | GitHub Action: PR diff in, generated doc updates out, any OpenAI-compatible LLM. | MIT | Yes | Same "diff in, artifact out, human review" loop shape. |
| [cicaddy](https://github.com/waynesun09/cicaddy) | Python framework running one-shot agentic tasks inside CI jobs with MCP tools. Individual Red Hat engineer. | Not stated | Yes | Minimal pattern for an LLM agent as a pipeline step. |
| [Krkn-AI](https://github.com/krkn-chaos/krkn-ai) | Genetic algorithm evolves chaos scenarios against Kubernetes, scored on Prometheus. Red Hat and IBM Research. | Apache-2.0 | GA plus LLM front end | Example of automatically generated resilience tests. Not source-driven. |
| [asago](https://github.com/asago-ai) | Aug 2026 community (Red Hat, IBM Research, Microsoft, NVIDIA): policy documents to risk to test scenarios to framework-specific red-team artifacts. | Apache-2.0 | Yes | AI safety tests, not software tests. The scenario-to-artifact pipeline is analogous. |
| [agentic-starter-kits](https://github.com/red-hat-data-services/agentic-starter-kits) | Behavioral test runner for AI agents with golden-query YAML and scorers. Tests are hand-written. | Apache-2.0 | Tests agents | Useful if the harness itself needs regression testing as an agent. |
| [tackle-test-generator-cli](https://github.com/konveyor/tackle-test-generator-cli) | Java unit and UI test generation via Randoop, EvoSuite, CTD. No LLM. **Archived Nov 2025.** | Apache-2.0 | No | Prior Red Hat test generation. Historical only. |

### 2.2 Supply chain, dependency analysis, hermetic builds, SBOMs

| Project | What it is | License | Relevance |
|---|---|---|---|
| [Konflux](https://github.com/konflux-ci) | Kubernetes-native software factory on Tekton: builds, SBOMs, SLSA provenance, Sigstore signing, Conforma gating. integration-service runs Tekton test pipelines on snapshots and reports to git providers. Red Hat built 2M+ artifacts on it in 2025. | Apache-2.0 | **The pipeline home for the harness.** A harness run is an integration test pipeline on a snapshot. |
| [Hermeto](https://github.com/hermetoproject/hermeto) (formerly Cachi2) | Prefetches dependencies for network-isolated builds and emits CycloneDX 1.6 or SPDX 2.3 SBOMs. gomod, maven (experimental), npm, pnpm, yarn, pip, bundler, cargo, rpm, generic. 3,105 commits, active. | **GPL-3.0-only** | Gives the harness a complete, pinned, offline dependency set and an SBOM for exactly the code under test. Copyleft matters if vendored; invoking it as a tool is fine. |
| [Conforma](https://github.com/conforma/cli) (formerly Enterprise Contract) | `ec` CLI verifies signatures, SLSA provenance, and Rego policies for Konflux artifacts. | Apache-2.0 | Policy gate where "generated tests ran and passed" can be attested and enforced. |
| [Mobster](https://github.com/konflux-ci/mobster) | SBOM lifecycle in Konflux: generation via Syft and Hermeto, augmentation, validation against Product Security guidelines, push to Trusted Profile Analyzer. | Apache-2.0 | Canonical way to produce and validate the SBOMs the harness consumes. |
| [Trustify](https://github.com/guacsec/trustify) | SBOM, VEX, and advisory store with correlation graph (Rust, PostgreSQL). Upstream of Red Hat Trusted Profile Analyzer. Contributed to OpenSSF GUAC in Aug 2025. [trustify-mcp](https://github.com/guacsec/trustify-mcp) is an MCP server. TPA 2.2 adds AIBOM ingestion and an AI "exploit intelligence" reachability feature (tech preview with NVIDIA, not confirmed open source). | Apache-2.0 | Source of truth for what is in a dependency tree and which components are vulnerable. The MCP server lets the harness agent query it directly. |
| [Trustify Dependency Analytics](https://github.com/guacsec/trustify-dependency-analytics) (formerly Exhort) | Quarkus service: SBOM of direct and transitive dependencies in, vulnerability and license analysis out, distinguishing direct from transitive. Model Cards API. Clients for JS and Java. Backs the VS Code extension and a Tekton task. | Apache-2.0 | Exact transitive-dependency risk data to drive which dependencies get generation budget. |
| [Dependency Analytics VS Code extension](https://github.com/fabric8-analytics/fabric8-analytics-vscode-extension) 1.0 (Jul 2026) | In-editor scanning of Maven, npm, Go, Python, Rust, Docker manifests including transitives. | Apache-2.0 | Developer-facing surface for the same data. |
| [Trusted Artifact Signer](https://github.com/securesign) | Sigstore midstream (Rekor, Fulcio, Cosign, Gitsign, TUF) with Kubernetes operator and model-validation-operator. | Apache-2.0 | Signing generated-test artifacts and attesting harness runs. |
| [security-data-guidelines](https://github.com/RedHatProductSecurity/security-data-guidelines) | Public spec for how Red Hat publishes SBOM and VEX data. | n/a | Format the harness must read and write. |

### 2.3 Testing infrastructure (no AI, likely substrate)

| Project | What it is | License | Relevance |
|---|---|---|---|
| [tmt](https://github.com/teemtee/tmt) | Test Management Tool: fmf metadata for defining, provisioning, running, reporting tests. Engine behind Testing Farm and Packit. 3,398 commits, active. | MIT | The harness can emit tmt plans so generated tests run on Testing Farm across RHEL, Fedora, CentOS. |
| [Testing Farm](https://gitlab.com/testing-farm) | Testing-as-a-service running tmt plans on provisioned machines. Docs mention an "AI Analysis" section for results with no detail. | Not visible | Execution target for OS-level functional tests. |
| [Packit](https://github.com/packit/packit) | Fedora packaging automation, runs tmt plans on PRs via Testing Farm. Default Fedora dist-git CI since Feb 2026. | MIT | Trigger and reporting surface for RPM-sourced intake. |

### 2.4 Platform context

- [lightspeed-core/lightspeed-stack](https://github.com/lightspeed-core/lightspeed-stack): assistant service over Llama Stack with RAG, MCP tools, shields. Developer Lightspeed generates test *plans* via chat, not test code.
- [RamaLama](https://github.com/containers/ramalama) (MIT) and Podman AI Lab: local model serving in containers. A candidate inference backend for the harness when open models are preferred.
- MCP servers, all Apache-2.0: kubernetes-mcp-server, openshift-mcp-server, trustify-mcp, insights-mcp, linux-mcp-server, konflux-devlake-mcp, jira-mcp-server. Red Hat also ships an MCP catalog and gateway on OpenShift AI.
- InstructLab archived Apr 2026. Its synthetic data work continues in Red-Hat-AI-Innovation-Team/sdg_hub. Not relevant to test generation.
- Project Lightwell (IBM and Red Hat, May 2026): AI-assisted vulnerability discovery, triage, and patch validation program. Commercial, not open source.

### 2.5 Searched for and not found at Red Hat

- Any open source project generating unit or functional tests for arbitrary incoming code with LLMs.
- Any repo named or described as an "AI test harness."
- AI features in tmt, Packit, or Konflux integration-service for test generation or selection. DevConf.US 2026 lists "AI in test failure analysis, test generation, and test selection" as a track theme, so interest exists.
- An open source release of the TPA exploit intelligence reachability feature.
- Public code for the Red Hat Research theses.

---

## 3. IBM and IBM Research

### 3.1 Test generation papers and tools

| Item | What it is | Code | Relevance |
|---|---|---|---|
| **ASTER** ([arXiv 2409.03093](https://arxiv.org/abs/2409.03093), [blog](https://research.ibm.com/blog/aster-llm-unit-testing)) | LLM plus lightweight static analysis unit test generation for Java and Python. Analyze, prompt, generate, compile, run, repair, fill coverage gaps, with mocking of external dependencies. ICSE-SEIP 2025 Distinguished Paper. Competitive with EvoSuite and CodaMOSA using GPT-4, CodeLlama, Granite, Llama. | **Not open source.** Ships in watsonx Code Assistant for Enterprise Java. `github.com/IBM/aster` is 404. `aster-test-generation/aster` holds generated artifacts only. | The closest published blueprint for the harness's core loop. Reproducible from the paper. |
| **SAINT** ([arXiv 2511.13305](https://arxiv.org/abs/2511.13305)) | Service-level integration test generation for Java REST services: static endpoint model plus operation dependency graph plus LLM agents (plan, act, reflect). ICSE 2026. IBM Research and Georgia Tech. | None listed. | Directly on point for functional test generation above the unit level. |
| **Sakura** ([arXiv 2606.00530](https://arxiv.org/abs/2606.00530)) | Multi-agent framework generating multi-class, multi-step Java tests from natural-language descriptions. Localization agent grounded by static analysis, composition agent with execution-feedback repair, supervisor. 50 to 78 percent higher compilability than Gemini CLI even with small open models. ISSTA 2026. | None listed. | Evidence that small open models suffice when guided by analysis. Pattern for spec-to-functional-test. |
| **Hamster** ([arXiv 2509.26204](https://arxiv.org/abs/2509.26204)) | Empirical study of 1.7M developer-written Java tests across 1,908 repos. Shows current generators fall short on fixtures, mocking, structured inputs. ICSE-SEIP 2026. | [Analysis scripts](https://github.com/aster-test-generation/hamster-empirical-study), license TBD. | Yardstick for what "realistic" generated tests must include. |
| **Otter, e-Otter++, TDD-Bench-Verified** ([ICML 2025](https://arxiv.org/abs/2508.06365), [Java port](https://arxiv.org/abs/2605.04320)) | Generates failing-then-passing reproduction tests from issue text. Heterogeneous prompting plus execution feedback. | [TDD-Bench-Verified](https://github.com/IBM/TDD-Bench-Verified), Apache-2.0, 449 instances. Benchmark harness only, generator not included. | Fail-before, pass-after is a usable acceptance metric for harness-generated tests. |
| **AutoRestTest** ([arXiv 2501.08600](https://arxiv.org/abs/2501.08600)) | REST API testing with semantic property dependency graph, multi-agent RL, LLM-generated values. ICSE 2025. Georgia Tech and IBM. | Not verified. | API-level functional test generation from an OpenAPI spec. |
| AlphaTrans (FSE 2025) | Repository-level code translation validated by generated tests. | Paper only. | Tangential. |

### 3.2 Code analysis for LLMs

| Project | What it is | License | Relevance |
|---|---|---|---|
| [CodeLLM-Devkit (CLDK)](https://github.com/codellm-devkit/python-sdk) ([docs](https://codellm-devkit.info/), [arXiv 2410.13007](https://arxiv.org/abs/2410.13007)) | Multilingual program analysis SDK producing LLM-ready facts: symbol tables, call graphs, reachability. Backends: WALA and JavaParser (Java), Jedi and PyCG (Python), ts-morph and Jelly (TypeScript). Analyzers for Go, Rust, C, Kotlin, Swift, IaC. Optional Neo4j graph backend. `pip install cldk`. 188 stars, 672 commits, active. [codeanalyzer-java](https://github.com/codellm-devkit/codeanalyzer-java) analyzes JAR, EAR, WAR **and their dependencies**, emitting call graphs over transitive jars. IBM blog states CLDK is used internally for test generation. | Apache-2.0 | **The most directly reusable IBM component.** Provides call graphs and reachability over incoming code and transitive dependencies to scope what to test. Example and tutorial repos are 404. |
| [Project CodeNet](https://github.com/IBM/Project_CodeNet) | 13.9M code submissions dataset. | Apache-2.0 | Training and evaluation data only. |

### 3.3 Models and orchestration

| Project | What it is | License | Relevance |
|---|---|---|---|
| [Granite Code Models](https://github.com/ibm-granite/granite-code-models) | 3B to 34B code models. **Archived Aug 24, 2026.** | Apache-2.0 | Superseded. |
| [Granite 4.0 to 4.2](https://github.com/ibm-granite/granite-4.0-language-models) | General models with FIM completion, tool calling, JSON output. 4.2 (Aug 2026) adds reasoning and agentic RL for software engineering tasks. | Apache-2.0 | Open-model option for high-volume stages if a fully open stack is required. |
| [Granite Guardian](https://github.com/ibm-granite/granite-guardian) | Risk, safety, hallucination, and function-call error detectors. | Apache-2.0 | Could gate harness LLM outputs. |
| Granite AI-BOM disclosures ([blog](https://research.ibm.com/blog/ai-bill-of-materials)) | Machine-readable model disclosures using SPDX and CycloneDX. | n/a | Model provenance for the harness's own supply chain record. |
| [Mellea](https://github.com/generative-computing/mellea) | Python library for generative programs: typed `@generative` functions, Pydantic-enforced outputs, requirement validation with automatic retry and repair, multiple backends. IBM Research Cambridge. 1.8k stars, 761 commits. | Apache-2.0 | Candidate orchestration layer for the harness's generate, validate, retry loops. |
| [watsonx Code Assistant](https://github.com/IBM/watsonx-code-assistant) | Product with `/unit-test` command. Enterprise Java edition ships ASTER. Repo is docs and samples only. | Commercial | Note only. |

### 3.4 Supply chain

- [CycloneDX/sbom-utility](https://github.com/CycloneDX/sbom-utility) and license-scanner: Go CLIs donated by IBM to CycloneDX. Apache-2.0. Validate, query, trim, patch SBOMs. No AI.
- [IBM/sbom-utilities](https://github.com/IBM/sbom-utilities): browser SBOM analyzer. Tiny. No AI.
- Konveyor: IBM Research is a supporter alongside Red Hat. See section 2.1.

### 3.5 Searched for and not found at IBM

- Open source code for ASTER, SAINT, or Sakura.
- Any IBM LLM-based mutation testing or LLM fuzz-harness generation.
- Open source components of the watsonx Code Assistant test generation feature.
- Granite 3.x or 4.x dedicated code models.
- An IBM project combining LLMs with dependency reachability or SBOM analysis.

---

## 4. Wider open source ecosystem

### 4.1 LLM and AI test generation

| Tool | Description | License | Maintainer | Activity | Languages | Relevance |
|---|---|---|---|---|---|---|
| [Qodo-Cover](https://github.com/qodo-ai/qodo-cover) (formerly Cover-Agent) | Coverage-guided LLM loop: generate, run, keep only tests that compile, pass, and raise coverage. First open reimplementation of Meta TestGen-LLM. 5.6k stars. | **AGPL-3.0** | Qodo | **Unmaintained.** README says "please fork." Commercial Qodo Cover Pro replaces it. | Python, Go, Java, any with Cobertura, JaCoCo, or lcov | The reference architecture. License and abandonment argue for reimplementing the loop, not depending on it. |
| [CoverUp](https://github.com/plasma-umass/CoverUp) | Coverage-guided LLM test generation with SlipCover. Flaky-test detection, test isolation, Docker sandbox. OpenAI, Anthropic, Bedrock. | Apache-2.0 | UMass PLASMA (Berger) | Last push Apr 2026 | Python (pytest) | Closest permissively licensed analogue for Python. Already handles flakiness and sandboxing. |
| [Pynguin](https://github.com/se2p/pynguin) | Search-based Python test generator with LLM prompting, LLMOSA algorithm, LLM type inference, LLM readability refinement. | LGPL-3.0 | Univ. of Passau | 0.46.0, Jul 2026 | Python | Best-maintained hybrid search-plus-LLM tool. Usable as a backend. |
| [CodaMOSA](https://github.com/microsoft/codamosa) | Pynguin plus LLM escape when coverage plateaus. ICSE 2023. | MIT plus LGPL base | Microsoft Research | README says build on Pynguin instead | Python | The "escape plateau" idea. |
| [TestSpark](https://github.com/JetBrains-Research/TestSpark) | IDE plugin with three backends: LLM, EvoSuite, Kex symbolic execution. | MIT | JetBrains Research | v0.4.2, Jan 2026 | Java, Kotlin | Multi-backend design is a good model. IDE-bound. |
| [TestPilot](https://github.com/githubnext/testpilot) | Doc-mining plus refine loop. | MIT | GitHub Next | **Archived Feb 2025** | JS, TS | Historical. |
| [ChatUniTest](https://github.com/ZJU-ACES-ISE/ChatUniTest) | Maven plugin reimplementing many published prompting strategies (ChatTester, SymPrompt, HITS, MuTAP, TELPA, CoverUp, TestPilot). | **No license file** | Zhejiang Univ. | Last push Jul 2025 | Java | Comparison bench. Unclear license blocks reuse. |
| [MuTAP](https://github.com/ExpertiseModel/MuTAP) | Surviving mutants fed back into the prompt so tests kill them. | None declared | Polytechnique Montréal | Last push Mar 2025 | Python | Small reference for mutation feedback in the loop. |
| [Randoop](https://github.com/randoop/randoop) | Feedback-directed random test generation. | MIT | UW (Ernst) | 4.3.4, Jun 2025, Java 8 to 24 | Java | Cheap regression oracle generation for dependencies. Complements LLM tests. |
| [EvoSuite](https://github.com/EvoSuite/evosuite) | Evolutionary JUnit generation. | LGPL-3.0 | EvoSuite team | Last push Feb 2025, Java 8 and 11 only | Java | Standard baseline but Java-version lag limits use. |
| [EvoMaster](https://github.com/WebFuzzing/EvoMaster) | Evolutionary system-level test generation for REST, GraphQL, gRPC. | LGPL-3.0 | Arcuri et al. | Very active, Sep 2026 | JVM, JS, C#, Python whitebox; any HTTP API blackbox | API-level regression suites for services whose dependencies change. |
| [Keploy](https://github.com/keploy/keploy) | eBPF record and replay generating API tests and mocks from traffic. Also markets an LLM unit test generator delivered as a GitHub App and VS Code extension. | Apache-2.0 | Keploy Inc. | v3.6.58, Sep 2026 | Language-agnostic replay | Traffic-based replay is genuinely open and useful for behavioral regression tests of upgrades. Treat the unit test generator as hosted. |
| [UTBotJava](https://github.com/UnitTestBot/UTBotJava), [UTBotCpp](https://github.com/UnitTestBot/UTBotCpp) | Symbolic execution plus fuzzing generators. | Apache-2.0 | UnitTestBot | Slowing (2025, 2024) | Java; C, C++ | Non-LLM option for C and C++ where LLM tools are weak. |
| Meta TestGen-LLM ([arXiv 2402.09171](https://arxiv.org/abs/2402.09171)), Meta ACH ([blog](https://engineering.fb.com/2025/02/05/security/revolutionizing-software-testing-llm-powered-bug-catchers-meta-ach/)) | Assured-improvement filter chain; mutation-guided LLM tests. | Paper only | Meta | 2024, 2025 | Kotlin, Java internal | Design references. |
| [Symflower eval-dev-quality](https://github.com/symflower/eval-dev-quality) | Benchmark for LLM test generation quality. Symflower itself is commercial. | MIT | Symflower | Last push May 2025 | Java, Go, Kotlin | Scoring generated test quality. |
| Diffblue Cover | Commercial RL-based deterministic Java test agent. | Commercial | Diffblue | Active | Java | Sets the bar for compile-correct deterministic Java tests. Note only. |

**Agent-based tools on Claude Code, Codex, Gemini CLI, or Aider:** no widely adopted open source project wraps
one of these specifically for test generation. What exists is skill and plugin directories, general
orchestrators with a "tester" role, and small unverified individual projects. This is a gap the harness
would fill.

### 4.2 Mutation testing

| Tool | Ecosystem | License | Activity | Note |
|---|---|---|---|---|
| [gremlins](https://github.com/go-gremlins/gremlins) | Go | Apache-2.0 | v0.6.0, Dec 2025; push Jun 2026 | Preferred Go backend. `--only-diff` for incremental. |
| [go-mutesting](https://github.com/avito-tech/go-mutesting) (Avito fork) | Go | MIT | Push Jan 2026 | Alternative with pluggable mutators. Original zimmski repo dormant. |
| [mutmut](https://github.com/boxed/mutmut) | Python | BSD-3 | 3.7.0, Jul 2026; push Sep 2026 | Fast. |
| [cosmic-ray](https://github.com/sixty-north/cosmic-ray) | Python | MIT | 8.7.0, Aug 2026 | Distributed execution, richer operators. |
| [PIT](https://github.com/hcoles/pitest) | JVM | Apache-2.0 | 1.30.0, Aug 2026 | De facto JVM scorer. |
| [cargo-mutants](https://github.com/sourcefrog/cargo-mutants) | Rust | MIT | v27.1.0, Jun 2026 | `--in-diff` for incremental. |
| [StrykerJS](https://github.com/stryker-mutator/stryker-js) | JS, TS | Apache-2.0 | v10.0.0, Aug 2026 | Also Stryker.NET 5.0.0 and Stryker4s 1.1.1 in 2026. |
| [Mutahunter](https://github.com/codeintegrity-ai/mutahunter) | Any with coverage report | **AGPL-3.0** | Dormant since Apr 2025 | Only general LLM mutation tool. Avoid. |
| [LLMorpheus](https://github.com/neu-se/llmorpheus) | JS, TS | MIT | Push Jul 2026 | LLM mutants executed through StrykerJS. Reference for plugging LLM mutants into an engine. |

### 4.3 Fuzz harness generation with LLMs

| Tool | Description | License | Activity | Languages | Relevance |
|---|---|---|---|---|---|
| [OSS-Fuzz-gen](https://github.com/google/oss-fuzz-gen) | Multi-agent LLM framework that writes, compiles, fixes, evaluates fuzz targets inside OSS-Fuzz. 30+ new bugs including CVE-2024-9143. Uses Fuzz Introspector for target selection. Models listed: Vertex, Gemini, OpenAI. | Apache-2.0 | Push Mar 2026, 1.4k stars | C, C++, Java, Python | Direct fit for incoming dependencies. Requires OSS-Fuzz build infrastructure. Rust not covered. |
| [Fuzz Introspector](https://github.com/ossf/fuzz-introspector) | Reachability of code from existing fuzz harnesses. | Apache-2.0 | Push Jul 2026 | C, C++, Python, Java, Go, Rust | The "what is not reached" signal that drives harness generation. |
| [PromeFuzz](https://github.com/pvz122/PromeFuzz) | Knowledge base plus RAG driven harness generation with sanitizer triage. CCS 2025. Claims higher coverage than OSS-Fuzz-gen. | MIT | Push Jul 2026 | C, C++ | Most recent open harness generator. |
| [PromptFuzz](https://github.com/FuzzAnything/PromptFuzz) | Coverage-guided mutation of prompts to generate fuzz drivers. | **No license file** | Push May 2026 | C, C++ | Strong baseline. Licensing gap. |
| [CKGFuzzer](https://github.com/security-pride/CKGFuzzer) | Code knowledge graph guided driver generation. ICSE 2025. | MIT | Push Feb 2025 | C, C++ | Knowledge-graph prompting pattern. |

### 4.4 Dependency behavioral and malicious-package analysis

| Tool | Description | License | Activity | Ecosystems | Relevance |
|---|---|---|---|---|---|
| [OpenSSF Package Analysis](https://github.com/ossf/package-analysis) | Runs packages in gVisor sandboxes, records strace and network, **tracks behavior changes across versions.** Results in public BigQuery. | Apache-2.0 | Push Sep 2026 | npm, PyPI, RubyGems, crates.io, Packagist | Closest existing "behavioral diff of a dependency version" pipeline. Reusable sandbox pattern. |
| [OpenSSF Malicious Packages](https://github.com/ossf/malicious-packages) | OSV-format database of malicious package reports. Feeds Dependabot malware alerts across 8 ecosystems since Jul 2026. | Apache-2.0 | Active | 8 ecosystems | Pre-flight gate before spending generation budget. |
| [GuardDog](https://github.com/DataDog/guarddog) | YARA source rules plus metadata heuristics. v3 risk model correlates capability with threat. | Apache-2.0 | v3.2.0, Aug 2026 | PyPI, npm, Go, crates.io, RubyGems, GitHub Actions, VS Code extensions | Cheap static gate. |
| [Capslock](https://github.com/google/capslock) | Static capability analysis for Go packages: network, exec, unsafe. | BSD-3 | Push Sep 2026 | Go | "What could this dependency do" signal for prioritization. |
| [LavaMoat](https://github.com/LavaMoat/LavaMoat) | Runtime sandboxing and per-package capability policies for npm. | MIT | Push Sep 2026 | JS | Behavioral capability profile at test time. |
| [OSSGadget](https://github.com/microsoft/OSSGadget) | oss-diff (diff two package versions), oss-detect-backdoor, oss-characteristics. | MIT | Push Jul 2026 | Multi via PURL | `oss-diff` feeds version-to-version diffs to test targeting. |
| [packj](https://github.com/ossillate-inc/packj) | Risky attribute audit. | AGPL-3.0 | Push Sep 2026 | npm, PyPI, RubyGems | Overlaps GuardDog. AGPL. |

### 4.5 SBOM, scoring, graph, vulnerability matching

| Tool | Description | License | Activity |
|---|---|---|---|
| [OpenSSF Scorecard](https://github.com/ossf/scorecard) | Repo security practice scoring. | Apache-2.0 | v5.5.0, Apr 2026 |
| [GUAC](https://github.com/guacsec/guac) | Graph joining SBOMs, SLSA, VEX, OSV, deps.dev, Scorecard. Trustify now lives here. | Apache-2.0 | v1.1.0, Mar 2026 |
| [Dependency-Track](https://github.com/DependencyTrack/dependency-track) | SBOM lifecycle and continuous vulnerability monitoring. | Apache-2.0 | 5.1.0, Aug 2026 |
| [Syft](https://github.com/anchore/syft), [Grype](https://github.com/anchore/grype) | SBOM generation, vulnerability matching. | Apache-2.0 | Aug 2026 |
| [OSV-Scanner](https://github.com/google/osv-scanner), [OSV-SCALIBR](https://github.com/google/osv-scalibr) | Scanner over OSV.dev; SCALIBR is the extraction library. Go call analysis via govulncheck. | Apache-2.0 | v2.5.1, Aug 2026 |
| [deps.dev](https://docs.deps.dev/) | Google-hosted dependency graphs, advisories, Scorecard data. HTTP, gRPC, BigQuery. | Apache-2.0 (API) | Push Sep 2026 |

### 4.6 API breaking-change detection

| Tool | Ecosystem | License | Activity |
|---|---|---|---|
| [gorelease and apidiff](https://pkg.go.dev/golang.org/x/exp/cmd/gorelease) | Go | BSD-3 | Sep 2026 |
| [japicmp](https://github.com/siom79/japicmp) | Java | Apache-2.0 | 0.26.2, Sep 2026 |
| [Revapi](https://github.com/revapi/revapi) | Java | Apache-2.0 | Nov 2025 |
| [cargo-semver-checks](https://github.com/obi1kenobi/cargo-semver-checks) | Rust | Apache-2.0 or MIT | v0.50.0, Aug 2026 |
| [griffe](https://github.com/mkdocstrings/griffe) | Python | ISC | Sep 2026 |
| [API Extractor](https://api-extractor.com/) | TypeScript | MIT | Active |

These are the cheapest "where did the contract change" signal to focus generated tests on changed surfaces.

### 4.7 Running tests against a new dependency version

| Tool | Description | License | Activity | Relevance |
|---|---|---|---|---|
| Debian autopkgtest and britney ([docs](https://wiki.debian.org/ContinuousIntegration/DebianSetup)) | Runs the test suites of a package and all reverse dependencies when a new version is proposed. Gates migration. | GPL-2+ | Production | The most mature open model of reverse-dependency testing on upgrade. |
| [Koschei](https://github.com/fedora-infra/koschei) | Fedora scratch rebuilds when build-dependencies change. | GPL-2.0 | Jul 2025 | Build-level, not test-level. |
| [Crater](https://github.com/rust-lang/crater) | Builds and tests crates.io against two toolchains. | None detected | Jul 2026 | Distributed differential runner design. |
| [PkgEval.jl](https://github.com/JuliaCI/PkgEval.jl), [revdepcheck](https://github.com/r-lib/revdepcheck) | Same pattern for Julia and R. | Various | 2026 | |
| [BUMP](https://github.com/chains-project/bump) | Dataset of about 570 reproducible breaking dependency updates in Java. SANER 2024. | MIT | Jun 2026 | **Ready benchmark** for whether harness-generated tests catch real breaking upgrades. |
| [Breaking-Good](https://github.com/chains-project/breaking-good) | Explains why a dependency update broke the build. KTH. | MIT | Jan 2025 | Explanation-generation pattern. |
| [OpenRewrite](https://github.com/openrewrite/rewrite) | Deterministic refactoring recipes including dependency upgrade migrations. | Apache-2.0 | Sep 2026 | Complementary: apply upgrade, then test. |
| Dependabot compatibility score, Renovate Merge Confidence | Crowd-sourced pass rates for a given version pair. | Proprietary data | Live | Signal only. Not open. |

**No maintained open source tool generically installs a candidate dependency version and runs the consuming
project's tests as a differential check across ecosystems.** This is done ad hoc with CI matrices or at
distro scale. It is the harness's clearest gap to fill.

### 4.8 Reachability

| Tool | Description | License | Activity | Languages |
|---|---|---|---|---|
| [govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) | Symbol-level static reachability of vulnerable functions. | BSD-3 | v1.8.0, Sep 2026 | Go |
| [OWASP dep-scan](https://github.com/owasp-dep-scan/dep-scan) with [atom](https://github.com/AppThreat/atom) | Reachability slicing via an intermediate representation. v6.3.0 adds Rust, Go, .NET. | MIT | Jul 2026, Sep 2026 | Java, JS, TS, Python, PHP, Rust, Go, .NET |
| CodeLLM-Devkit | See section 3.2. | Apache-2.0 | Active | Java including transitive jars, Python, TS, others |
| [Eclipse Steady](https://github.com/eclipse-steady/steady) | Static plus **test-execution-based** reachability. SAP origin. | Apache-2.0 | **Unmaintained since Dec 2023** | Java |
| Endor Labs, Snyk, Semgrep Supply Chain, Socket (Coana) | Commercial reachability. | Commercial | | |

---

## 5. Gaps the harness would fill

1. A maintained, permissively licensed, multi-language, CLI-first, agentic test generator. None exists.
2. Generic cross-ecosystem differential testing of a consuming project against a candidate dependency version.
3. Test generation for transitive dependencies scoped by reachability. The pieces (CLDK, govulncheck, dep-scan) do reachability for vulnerabilities, not for test targeting.
4. An LLM-driven triage layer that classifies generated-test failures into test bug, behavior change, defect, security, and suspicious. sast-ai-workflow is the nearest pattern but targets SAST findings.
5. Rust fuzz harness generation with LLMs.
6. Anything of this shape packaged as a Konflux integration test or a tmt plan.

---

## 6. Implications for the plan

### Reuse directly

- **Konflux integration-service** as the pipeline. **Hermeto** for hermetic dependency prefetch and SBOM. **Mobster** for SBOM lifecycle. **Conforma** to attest and gate. **Trusted Artifact Signer** to sign outputs.
- **Trustify** and **Trustify Dependency Analytics** for the transitive graph, direct-versus-transitive classification, and vulnerability data. **trustify-mcp** so the agent can query it.
- **CodeLLM-Devkit** for call graphs and reachability in Java, Python, TypeScript. **govulncheck** and **Capslock** for Go. **dep-scan with atom** for the rest.
- Per-ecosystem mutation tools: **PIT, StrykerJS, cargo-mutants, mutmut or cosmic-ray, gremlins.**
- API diff tools: **japicmp, cargo-semver-checks, griffe, gorelease, API Extractor.**
- **GuardDog, Capslock, OpenSSF Malicious Packages** as pre-flight suspicious gates. **OpenSSF Package Analysis** as the sandbox and behavioral-diff pattern.
- **OSS-Fuzz-gen** and **Fuzz Introspector** for C, C++, Java, Python fuzz harnesses.
- **tmt** to run OS-level functional tests on Testing Farm.
- **prodsec-skills** and **harness-eval** for the agent's own configuration.

### Learn from, do not depend on

- **ASTER, SAINT, Sakura** for the generation loop design. **QualityFlow** for Red Hat-flavored agent orchestration. **sast-ai-workflow** for confidence-scored triage packaged as a Tekton task. **CoverUp** for flake handling and sandboxing. **Qodo-Cover** for the assured-improvement filter, reimplemented under a permissive license.
- **Debian autopkgtest and Crater** for reverse-dependency differential testing design.
- **Log Detective** for failure-log summarization.

### Benchmark against

- **BUMP** for breaking dependency upgrades. **TDD-Bench-Verified** for fail-before, pass-after tests. **Hamster** for realism of generated tests. **eval-dev-quality** for generation quality.

### Avoid

- **Qodo-Cover, Mutahunter, packj** (AGPL, and the first two are dormant). **ChatUniTest, PromptFuzz** (no license). **Eclipse Steady, TestPilot, EvoSuite** (unmaintained or version-locked). **tackle-test-generator-cli** (archived).

### Licensing note

Hermeto is GPL-3.0-only. Invoking it as a separate tool in the pipeline is fine. Vendoring or linking its
code into the harness would make the harness GPL. Everything else recommended for direct reuse is
Apache-2.0, MIT, BSD, or ISC.

---

## 7. Sources

Primary sources were fetched on 2026-09-11 from GitHub repository pages and the GitHub REST API, arXiv
abstract pages, research.ibm.com, research.redhat.com, developers.redhat.com, redhat.com blogs, openssf.org,
pkg.go.dev, PyPI, docs.deps.dev, and project documentation sites. Individual URLs are linked inline above.
Where a claim rests on a single secondary source it is marked as unverified in the text.
