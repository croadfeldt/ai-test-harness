# Capability map: what fills each capability, and what orchestrates it

**For:** engineers and architects choosing components. Companion to the [landscape](04-landscape.md),
which is the full inventory. This document is the decision: for every capability the harness needs, a
primary choice, a fallback, and the reason. Research date 2026-09-11.

## Two facts that reshape the choices

1. **in-toto already has a vetted Test Result predicate.** `https://in-toto.io/attestation/test-result/v0.1`
   carries a result (PASSED, WARNED, FAILED), configuration descriptors, a URL, and lists of passed,
   warned, and failed tests. It is on the vetted list, not a draft. The harness emits this predicate,
   extended through its configuration descriptors, rather than inventing one. That answers open
   question 14 in the blueprint.
2. **Konflux already runs an LLM inside a Tekton task for dependency PRs.** `konflux-ci/deptriage` is a
   Go CLI that classifies semver impact and asks Gemini or Claude for impact analysis of dependency
   pull requests, with secret redaction and retry logic, shipped as an image with its own `.tekton/`
   pipeline and updated the day of this research. It is the precedent for the harness's intake and
   analysis steps and possibly an input to them.

Also worth knowing: Llama Stack was renamed OGX (Open GenAI Stack) in April 2026 and is GA in
OpenShift AI 3.5 with the OpenAI-compatible Responses API. IBM's Agent Communication Protocol was
absorbed into A2A, which joined the Linux Foundation's Agentic AI Foundation alongside MCP in August
2026. MCP and A2A are the only two agent protocols worth designing for.

## The decision table

| Capability | Primary | Fallback | Why |
|---|---|---|---|
| Pipeline and workflow engine | **Tekton on Konflux.** Agent steps are ordinary Tasks; execution steps set `runtimeClassName: kata` | Argo Workflows 4.x, only if fuzz fan-out reaches thousands of jobs | Tekton Chains and Conforma give provenance for free. A second engine adds nothing but a second engine. |
| Agent runtime for test generation | **Claude Agent SDK** in a one-shot container step, tools behind the MCP gateway, OpenTelemetry via environment variables | Google ADK (model-agnostic, native OTel GenAI spans) or LangGraph | The file-editing, compile, run, repair loop is production grade and the Kubernetes hosting pattern is documented. Vendor-bound to Claude, which the fallback covers. |
| Agent runtime for high-volume classification | **OGX Responses API on OpenShift AI 3.5** serving Granite or other open models through Red Hat AI Inference Server | Direct vLLM plus a thin LangGraph step | Red Hat-supported, cheap tokens, MCP connectors, TrustyAI guardrails, MLflow tracing built in. |
| Tool access governance for agents | **Kuadrant MCP gateway** (Red Hat, Tech Preview in OpenShift AI 3.4 and 3.5): identity-scoped, auditable tool calls | IBM ContextForge MCP Gateway (richer plugins, not the Red Hat product path) | Every agent call to git, registries, Trustify, or test runners passes one auditable chokepoint. |
| Sandbox for generated tests and untrusted code | **OpenShift sandboxed containers (Kata)** plus the **Red Hat build of Agent Sandbox**, with an egress allowlist (OpenShell or NetworkPolicy plus proxy) | gVisor RuntimeClass or OpenSandbox on Kata where Red Hat support is not required | Red Hat's own July 2026 benchmark shows Kata plus an application-layer egress control is the only combination that stops both a kernel escape and prompt-injection exfiltration. |
| Inner sandbox around the agent's shell | **Anthropic sandbox-runtime** (seccomp, bubblewrap) inside the Kata pod | None needed | Cheap inner ring. Not a substitute for the VM boundary. |
| Attestation generation | **Tekton Chains** emitting in-toto `test-result/v0.1` and `vulns` predicates, signed through Trusted Artifact Signer | **in-toto witness** wrapping test commands, with its network-trace attestor | The vetted predicate plus Chains covers the standard case. Witness adds command, environment, and network evidence when Chains is too coarse. |
| Attestation verification | **Conforma** at release, **Kyverno ImageValidatingPolicy** at admission | Sigstore policy-controller; Chainloop as an evidence ledger | slsa-verifier is unmaintained. Kyverno 1.19 checks attestation predicates with CEL and is common on OpenShift. |
| VEX authoring | **vexctl (OpenVEX)** with `vexctl attest`, plus CycloneDX VEX for Trustify ingestion | gocsaf for CSAF publication; Chainloop's OpenVEX and CSAF evidence types | OpenVEX is the simplest machine-authored format and attests through Sigstore. CSAF is the PSIRT publication format; convert at publication time. |
| Dependency graph, SBOM, hermetic prefetch | **Hermeto, Mobster, Trustify, Trustify Dependency Analytics** | Syft and Grype, deps.dev for graphs without local resolution | Already Konflux's tooling. Hermeto is GPL-3.0, invoked as a tool, never vendored. |
| Reachability and call graphs | **CodeLLM-Devkit** (Java including transitive jars, Python, TypeScript), **govulncheck** and **Capslock** (Go), **dep-scan with atom** (Rust, .NET, others) | Fuzz Introspector for C and C++ harness reachability | Best per-language coverage available under permissive licenses. Unknown means "reachable." |
| API contract diff | **gorelease, japicmp, cargo-semver-checks, griffe, API Extractor, libabigail abidiff** | Revapi for Java | Cheapest "where did the contract change" signal. |
| Pre-flight gates | **GuardDog, OpenSSF Malicious Packages, Capslock** | packj (AGPL, avoid) | Cheap static and database checks before anything executes. |
| Mutation testing | **gremlins, mutmut or cosmic-ray, PIT, cargo-mutants, StrykerJS** | go-mutesting fork for Go | All shipped releases in 2026. Diff-scoped runs keep cost bounded. |
| Fuzz harness generation | **OSS-Fuzz-gen** with Fuzz Introspector for C, C++, Java, Python | PromeFuzz (MIT, research) for C and C++; Rust harness generation is ours | Google's production framework. Rust is the gap we fill. |
| Test framework and runners | **The ecosystem's own:** `go test`, pytest, JUnit 5, `cargo test`, Vitest or Jest, GoogleTest or Catch2 | None | The native-first principle. Tests that need a special runner do not get run. |
| OS-level and hardware execution | **tmt** plans on **Testing Farm** (VMs via Artemis, bare metal via Beaker) | Direct Podman on a runner | Same plan runs on every target. |
| LLM observability | **Langfuse** self-hosted (MIT, Helm, air-gap capable) fed by OpenTelemetry GenAI semantic-convention spans | OpenShift AI MLflow tracing (built into 3.5); Phoenix (Elastic License caveat) | Standard span attributes mean Langfuse, MLflow, and Tempo all work without re-instrumentation. |
| Prompt and eval regression | **promptfoo** in a Tekton step (MIT, has a Claude Agent SDK provider) | DeepEval for pytest-style evals; Inspect with its Kubernetes sandbox provider for offline agent benchmarks | Declarative, diffable eval configs gate every prompt change. Promptfoo was acquired by OpenAI in March 2026 with a commitment to keep the OSS core; watch governance. |
| Guardrails on agent input and output | **TrustyAI Guardrails Orchestrator** with OGX (Tech Preview) | Granite Guardian as a detector | Guards prompts against injected content from untrusted dependency source. Tool-level guardrails are not yet covered. |
| Model serving for open models | **Red Hat AI Inference Server** (vLLM; CUDA, ROCm, TPU, Spyre; s390x, ppc64le) | RamaLama for developer machines | Serves Granite 4.x for classification when a fully open model stack is required. |
| Agent configuration hardening | **harness-eval**, **prodsec-skills** | | Red Hat community tooling built for exactly this. |

## Orchestration options considered and set aside

| Option | Why not primary |
|---|---|
| kagent (CNCF Sandbox) | Agents as long-lived cluster CRDs. The harness is per-PipelineRun batch work. Over-scoped unless we later want agents as first-class Kubernetes objects. |
| Dapr Agents (GA March 2026) | Durable execution is attractive for long generation loops, but it adds a Dapr control plane and sidecars to Konflux clusters. |
| CrewAI, OpenAI Agents SDK, Microsoft Agent Framework | Sound frameworks. CrewAI's role-play abstraction adds little to a deterministic pipeline. OpenAI's SDK is awkward with Claude or Granite as the primary model. Microsoft's has the best OTel story but Azure gravity. |
| BeeAI Framework and Agent Stack (IBM Research, now Linux Foundation) | Useful as an A2A hosting layer. The harness does not need agents exposed as services. |
| Kubeflow Pipelines | Duplicates Tekton. |
| lightspeed-core | Product-assistant oriented, not CI oriented. Its architecture (service layer over OGX, MCP with service-account tokens) is the Red Hat-blessed pattern to copy. |

## Sandboxing options considered

| Option | Status |
|---|---|
| OpenShift sandboxed containers 1.12 (Kata, April 2026) | Primary. Confidential containers on bare metal GA. |
| Red Hat build of Agent Sandbox (Tech Preview, July 2026) | Primary for interactive, stateful agent sandboxes. Warm pools cut cold start. Kata via one template field. |
| Kata Containers 4.x upstream | Consumed through the operator. |
| gVisor (release 20260907) | Fallback where KVM is unavailable. No Red Hat support statement found. |
| OpenSandbox (Alibaba, March 2026, Apache-2.0) | Viable vendor-neutral SDK over Kata. Less Red Hat alignment. |
| E2B, Daytona | E2B is commercial with an Apache-2.0 runtime that expects its own control plane. Daytona moved core development private in June 2026 and is now AGPL. Both set aside. |

## IBM and Red Hat projects that inform this map

- **konflux-ci/deptriage**: LLM-in-Tekton dependency PR triage. Reuse its secret redaction, retry, and
  classification patterns; consider its output as harness input.
- **konflux-ci/agent-plugins**: Claude Code skills for Konflux. Packaging pattern.
- **konflux-ci/kait-task**: Tekton task calling an AI triage service on CI failures. Archived July
  2026. Historical precedent only.
- **Red Hat cloud-native agent blueprint** (July 2026): Agent Sandbox plus OpenShell, Kuadrant MCP
  gateway, SPIFFE identity, MLflow and OTel tracing, TrustyAI guardrails. Adopted as the harness's
  runtime architecture, with Tekton steps mapped onto "agent as a workload" pods.
- **IBM ALTK** (Agent Lifecycle Toolkit): pre- and post-LLM and tool checks. Candidate source of
  output-validation components. License not yet verified.
- **IBM ContextForge MCP Gateway** 1.0 (April 2026): fallback to Kuadrant.
- **Lightwell** (IBM and Red Hat, May 2026): no public repository or tooling found as of the research
  date despite press references to an open source project. The harness sits squarely in Lightwell's
  stated remit of validating and testing fixes across open source at volume. Position it as
  Lightwell-aligned infrastructure and revisit when tooling is published.

## Not found

- A Tekton Hub or Artifact Hub catalog task that invokes an LLM. The harness authors its own tasks.
- Firecracker as a VMM option in OpenShift sandboxed containers.
- A Red Hat support statement for gVisor on OpenShift.
- Public Lightwell tooling.
