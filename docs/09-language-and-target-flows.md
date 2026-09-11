# Harness creation and execution flows by language and target

**For:** engineers building or operating adapters. This is the document that says exactly what happens
for Go versus Rust, and on a Kubernetes pod versus a bare-metal machine.

## The contract that makes this manageable

Every language adapter produces the same artifact, and every execution target consumes it. That is the
whole trick. The adapter knows the language. The provisioner knows the machine. Neither knows the other.

```mermaid
flowchart LR
    subgraph Adapter[Language adapter]
        R[resolve_graph] --> E[extract_api] --> D[api_diff] --> B[build] --> GEN[generate tests]
    end
    GEN --> ART[(Harness artifact:\nOCI image + tmt plan\n+ expected-results manifest)]
    ART --> P{Execution target}
    P --> K8S[Kubernetes / OpenShift pod]
    P --> POD[Podman container]
    P --> VM[Virtual machine]
    P --> BM[Bare metal]
    K8S --> RES[(results.json, coverage,\nmutation, logs, attestation)]
    POD --> RES
    VM --> RES
    BM --> RES
```

The harness artifact is:

| Part | Content |
|---|---|
| OCI image | Pinned base for the ecosystem, Hermeto-prefetched dependencies, the package under test at old and new versions, the generated tests, the overlay and standard tests, the runner script |
| tmt plan | Declares how to execute, what to collect, resource limits, and which target classes are acceptable. Runs unchanged on every target because tmt is the engine behind Testing Farm |
| Expected-results manifest | What each test asserts, which are differential, which are CVE-targeted, so the collector can classify without re-reading source |

Results come back in one schema regardless of target, and the attestation names the target class and
the provisioner so that provenance is complete.

## Choosing a target

```mermaid
flowchart TB
    S[Work item] --> Q1{Needs hardware, specific\narch, or measured performance?}
    Q1 -- yes --> BM[Bare metal via Testing Farm]
    Q1 -- no --> Q2{Needs a full OS: systemd,\nkernel modules, SELinux,\nRPM install, multiple users?}
    Q2 -- yes --> VM[Virtual machine via Testing Farm]
    Q2 -- no --> Q3{Running inside the\nKonflux pipeline?}
    Q3 -- yes --> K8S[Kubernetes pod with gVisor or Kata]
    Q3 -- no --> POD[Podman on a runner or a developer machine]
```

| Target | When | Isolation | Provisioner | Cost |
|---|---|---|---|---|
| Kubernetes / OpenShift | Default for every Konflux run | RuntimeClass gVisor or Kata (OpenShift sandboxed containers), deny-all NetworkPolicy, no service account token, resource limits, pod deleted after run | Tekton TaskRun inside the harness PipelineRun | Lowest |
| Podman | Developer reproducing a review packet locally; CI runners outside Konflux; air-gapped environments | Rootless, `--network=none`, read-only rootfs, dropped capabilities, gVisor or crun-krun runtime for depth 1 and deeper | The runner script, same image | Low |
| Virtual machine | Package is RPM-delivered, needs OS services, SELinux policy, kernel interfaces, or multi-user behavior | Fresh VM from a golden image, no outbound network after the image is pulled, snapshot discarded after run | tmt provision through Testing Farm (Artemis) | Medium |
| Bare metal | Drivers, firmware interfaces, accelerator libraries, architecture-specific code (aarch64, ppc64le, s390x), performance-sensitive packages where virtualization skews results | Machine reprovisioned and wiped after every run; network isolated at the switch or by Testing Farm policy | tmt provision through Testing Farm (Beaker pool) | Highest, so risk score must justify it |

## Creation flows by language

Each flow below is the adapter's implementation of the interface in
[blueprint/adapter-interface.md](../blueprint/adapter-interface.md). Tools marked "verify" were not in
the landscape research and need confirmation before adoption.

### Go

```mermaid
flowchart LR
    R[Hermeto gomod\n+ go mod graph] --> E[gopls symbol export\n+ go doc]
    E --> D[gorelease / apidiff]
    D --> RCH[govulncheck reachability\n+ Capslock capabilities]
    RCH --> G[Generate: testing + testify,\nnative fuzz targets]
    G --> B[go vet, go build -mod=vendor]
    B --> ART[(Artifact)]
```

| Step | Tool |
|---|---|
| Resolve | Hermeto `gomod`, `go mod graph` for depth |
| API surface | `go doc -all`, gopls |
| API diff | gorelease, apidiff |
| Reachability and capabilities | govulncheck, Capslock |
| Test framework | `testing`, testify |
| Coverage | `go test -cover -coverprofile` |
| Mutation | gremlins `--only-diff` |
| Fuzz | `go test -fuzz` native targets |
| Build | `go build`, `go vet`, offline with vendored or module cache from Hermeto |

### Python

```mermaid
flowchart LR
    R[Hermeto pip\n+ pipdeptree] --> E[griffe API dump\n+ CLDK Jedi/PyCG call graph]
    E --> D[griffe check]
    D --> RCH[CLDK reachability\n+ dep-scan]
    RCH --> G[Generate: pytest,\nhypothesis properties,\nAtheris fuzz targets]
    G --> B[Offline venv from\nprefetched wheels, import check]
    B --> ART[(Artifact)]
```

| Step | Tool |
|---|---|
| Resolve | Hermeto `pip`, pipdeptree |
| API surface and call graph | griffe, CodeLLM-Devkit (Jedi, PyCG) |
| API diff | `griffe check` |
| Reachability | CodeLLM-Devkit, dep-scan |
| Test framework | pytest, hypothesis for properties |
| Coverage | coverage.py |
| Mutation | mutmut, or cosmic-ray for distributed runs |
| Fuzz | Atheris via OSS-Fuzz-gen |
| Build | Offline virtualenv from Hermeto-prefetched wheels and sdists |

### Java and Kotlin

```mermaid
flowchart LR
    R[Hermeto maven or\nGradle offline cache] --> E[CLDK codeanalyzer-java:\nsymbol table + call graph\nover source and jars]
    E --> D[japicmp on old vs new jar]
    D --> RCH[CLDK reachability\nacross transitive jars]
    RCH --> G[Generate: JUnit 5,\nMockito, Jazzer fuzz targets,\nRandoop regression oracles]
    G --> B[mvn -o or gradle --offline,\ncompile + test-compile]
    B --> ART[(Artifact)]
```

| Step | Tool |
|---|---|
| Resolve | Hermeto `maven` (experimental), Gradle dependency cache |
| API surface and call graph | CodeLLM-Devkit codeanalyzer-java, which walks JAR, EAR, WAR and their dependencies |
| API diff | japicmp, Revapi as alternative |
| Reachability | CodeLLM-Devkit |
| Test framework | JUnit 5, Mockito; Kotlin via kotlin-test on JUnit 5 |
| Coverage | JaCoCo |
| Mutation | PIT |
| Fuzz | Jazzer via OSS-Fuzz-gen |
| Random oracles | Randoop, cheap regression tests for dependencies |
| Build | Maven or Gradle offline |

### Rust

```mermaid
flowchart LR
    R[Hermeto cargo\n+ cargo metadata] --> E[rustdoc JSON]
    E --> D[cargo-semver-checks]
    D --> RCH[dep-scan atom\nreachability]
    RCH --> G[Generate: cargo test,\nproptest properties,\ncargo-fuzz targets]
    G --> B[cargo build --offline,\ncargo clippy]
    B --> ART[(Artifact)]
```

| Step | Tool |
|---|---|
| Resolve | Hermeto `cargo`, `cargo metadata` |
| API surface | rustdoc JSON output |
| API diff | cargo-semver-checks |
| Reachability | dep-scan with atom (Rust support added 2026) |
| Test framework | built-in `cargo test`, proptest |
| Coverage | cargo-llvm-cov |
| Mutation | cargo-mutants `--in-diff` |
| Fuzz | cargo-fuzz; harness generation is ours, OSS-Fuzz-gen does not cover Rust |
| Build | `cargo build --offline` from the Hermeto vendor directory |

### JavaScript and TypeScript

```mermaid
flowchart LR
    R[Hermeto npm / pnpm / yarn] --> E[API Extractor report\n+ CLDK ts-morph]
    E --> D[API Extractor diff]
    D --> RCH[CLDK reachability\n+ LavaMoat capability policy]
    RCH --> G[Generate: Vitest or Jest,\nfast-check properties,\nJazzer.js fuzz targets]
    G --> B[tsc --noEmit,\noffline install from cache]
    B --> ART[(Artifact)]
```

| Step | Tool |
|---|---|
| Resolve | Hermeto `npm`, `pnpm`, `yarn` |
| API surface | API Extractor, CodeLLM-Devkit ts-morph |
| API diff | API Extractor report diff |
| Reachability and capabilities | CodeLLM-Devkit, LavaMoat per-package capability policy |
| Test framework | Vitest or Jest, fast-check for properties |
| Coverage | c8 or istanbul |
| Mutation | StrykerJS |
| Fuzz | Jazzer.js (verify current maintenance) |
| Build | `tsc --noEmit`, offline install from the prefetched cache |

### C and C++

```mermaid
flowchart LR
    R[Hermeto generic or rpm\n+ mock buildroot] --> E[clang AST export\n+ CLDK clang analyzer]
    E --> D[libabigail abidiff]
    D --> RCH[Fuzz Introspector\nreachability]
    RCH --> G[Generate: GoogleTest or Catch2,\nlibFuzzer targets via OSS-Fuzz-gen]
    G --> B[CMake or Autotools or\nrpmbuild in mock, offline]
    B --> ART[(Artifact)]
```

| Step | Tool |
|---|---|
| Resolve | Hermeto `generic` and `rpm`, mock buildroot for RPM-delivered code |
| API surface | clang AST dump, CodeLLM-Devkit clang analyzer |
| ABI and API diff | libabigail abidiff (Red Hat maintained) |
| Reachability | Fuzz Introspector |
| Test framework | GoogleTest or Catch2 |
| Coverage | gcov, llvm-cov |
| Mutation | mull (LLVM-based, verify license and activity) |
| Fuzz | libFuzzer and AFL++ targets via OSS-Fuzz-gen |
| Build | CMake, Autotools, or `rpmbuild` inside mock, all offline |

C and C++ is the ecosystem most likely to need the VM and bare-metal targets, because so much of it is
RPM-delivered and kernel-adjacent.

## Execution flows by target

### Kubernetes and OpenShift (default)

```mermaid
sequenceDiagram
    participant IS as integration-service
    participant PR as Harness PipelineRun
    participant TR as Tekton TaskRun
    participant POD as Sandbox pod (gVisor/Kata)
    participant REG as Internal registry
    participant COL as Collector task
    IS->>PR: Snapshot ready
    PR->>REG: Pull harness artifact by digest
    PR->>TR: Execute task with RuntimeClass, deny-all NetworkPolicy, no SA token
    TR->>POD: Start, mount artifact read-only, emptyDir for output
    POD->>POD: compile, run, flake re-run, coverage, mutation, differential
    POD-->>TR: results.json + logs + coverage (emptyDir)
    TR->>COL: Hand off results
    COL->>COL: Classify, build attestation, sign via TAS
    COL-->>PR: Review packet, attestation
    Note over POD: Pod deleted. Nothing persists.
```

Controls: RuntimeClass `gvisor` or `kata` required for depth 1 and deeper by admission policy;
NetworkPolicy deny-all on the namespace; `automountServiceAccountToken: false`; read-only root
filesystem; CPU, memory, and `activeDeadlineSeconds` limits; the signing step runs in a separate task
that never shares a pod with test execution, which is what SLSA Build L3 requires.

### Podman

```mermaid
flowchart LR
    A[Pull artifact by digest] --> B["podman run --rm --network=none\n--read-only --cap-drop=all\n--userns=auto --runtime=runsc or krun\n--memory --cpus --timeout"]
    B --> C[Runner script executes the tmt plan]
    C --> D[Results written to a mounted output dir]
    D --> E[Optional: collector container\nclassifies and, on CI runners, signs]
```

Podman is the developer's reproduction path. A review packet includes the exact `podman run` line and
the artifact digest, so any engineer can replay the run on a laptop and get the same results.json. On CI
runners outside Konflux the same image runs with the same flags and the collector signs; on a laptop
there is no signing and the attestation is marked `replay, unsigned`.

### Virtual machine (Testing Farm)

```mermaid
sequenceDiagram
    participant PR as Harness PipelineRun
    participant TF as Testing Farm API
    participant AR as Artemis provisioner
    participant VM as Fresh VM (RHEL / Fedora / CentOS Stream)
    participant COL as Collector task
    PR->>TF: Submit tmt plan + artifact digest + target class
    TF->>AR: Provision from golden image, arch, distro
    AR->>VM: Boot, attach, pull artifact from internal registry
    VM->>VM: Disable outbound network, run tmt plan
    VM-->>TF: results.json, coverage, logs, journal
    TF-->>PR: Results
    PR->>COL: Classify, attest, sign
    Note over VM: VM destroyed. Snapshot not kept.
```

Use for RPM-delivered packages, anything that touches systemd, SELinux, kernel interfaces, or multiple
users, and for distro matrix runs (RHEL 9, RHEL 10, Fedora, CentOS Stream). tmt's provision step selects
the image; the plan is the same one that ran on Kubernetes.

### Bare metal (Testing Farm, Beaker pool)

```mermaid
sequenceDiagram
    participant PR as Harness PipelineRun
    participant TF as Testing Farm API
    participant BK as Beaker
    participant HW as Physical host
    participant COL as Collector task
    PR->>TF: Submit tmt plan + artifact digest + hardware requirements
    TF->>BK: Reserve host matching arch, device, or performance class
    BK->>HW: Reprovision from clean image
    HW->>HW: Pull artifact, isolate network, run tmt plan
    HW-->>TF: results.json, coverage, logs, hardware telemetry
    TF-->>PR: Results
    PR->>COL: Classify, attest, sign
    BK->>HW: Wipe and return to pool
```

Use only when the risk score or the package class demands it: drivers, firmware interfaces, accelerator
and GPU libraries, architecture-specific code, and packages whose failure mode is performance. Every
bare-metal run is logged with its hardware identity in the attestation, and the wipe is verified before
the host returns to the pool.

## Language and target matrix

| | Kubernetes | Podman | VM | Bare metal |
|---|---|---|---|---|
| Go | Default | Replay | Rarely: cgo with system libs | Arch-specific builds |
| Python | Default | Replay | C extensions against system libs; RPM-packaged Python | Rarely |
| Java, Kotlin | Default | Replay | Rarely | Rarely |
| Rust | Default | Replay | Rarely: system FFI | Arch-specific, embedded targets |
| JavaScript, TypeScript | Default | Replay | Rarely: native addons | Rarely |
| C, C++ | Default for pure libraries | Replay | RPM-delivered, systemd, SELinux, kernel-adjacent | Drivers, firmware, accelerators, performance |

## What the adapter interface guarantees

Adding a language means implementing eight functions: `resolve_graph`, `extract_api`, `api_diff`,
`build`, `run_tests`, `coverage`, `mutate`, `fuzz`. Adding a target means implementing one provisioner
that accepts a tmt plan and an artifact digest and returns results in the common schema. The pipeline,
the agents, the triage, the provenance, and the review packet do not change for either.
