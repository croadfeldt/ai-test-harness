# Ecosystem adapter interface

Every language ecosystem is supported by one adapter that implements the eight functions below. The
pipeline, the agents, triage, provenance, and the review packet call these functions and nothing else
that is language-specific. An adapter is a container image plus a small Python or Go package that
exposes this interface over a JSON-on-stdio protocol so that adapters can be written in any language.

## Functions

```text
resolve_graph(source_dir, lockfiles, hermeto_output) -> DependencyGraph
    Returns every package with name, version, purl, depth, parents, and the path to its prefetched
    source or artifact. Uses Hermeto output when present, falls back to the native resolver.

extract_api(package_dir, version) -> ApiSurface
    Returns exported symbols with signatures, types, docstrings, file, and line. Tool-derived only.

api_diff(old_surface, new_surface) -> ApiDiff
    Returns added, removed, and changed symbols, with a breaking flag per change, using the
    ecosystem's contract-diff tool.

build(package_dir, deps_dir, tests_dir, target) -> BuildResult
    Compiles or imports the package and the tests offline. Returns success, diagnostics, and the
    harness artifact reference (OCI digest + tmt plan) when successful.

run_tests(artifact, selection, target, limits) -> TestResults
    Executes the tmt plan on the given target and returns results in the common schema: per-test
    status, duration, output, and the differential pairing when two versions were run.

coverage(artifact, results) -> CoverageReport
    Line and branch coverage per file and per test, normalized to the common report format.

mutate(artifact, scope, sample) -> MutationReport
    Runs the ecosystem's mutation tool on the given scope (diff-only by default) with a bounded
    sample and returns per-mutant kill status attributed to tests.

fuzz(artifact, targets, time_budget) -> FuzzReport
    Runs fuzz targets for the time budget and returns crashes with minimized reproducers.
```

## Common schemas

All return types are JSON documents with schemas kept in this directory. `TestResults` is the schema
every execution target must produce, whether the run happened in a Kubernetes pod, a Podman container,
a VM, or on bare metal.

```yaml
# TestResults (abbreviated)
run_id: string
artifact_digest: string
target: { class: k8s | podman | vm | baremetal, provisioner: string, identity: string }
package: { purl: string, old_version: string, new_version: string }
tests:
  - id: string
    category: unit | functional | negative | cve | fuzz | harness
    status: pass | fail | error | skip | flaky
    duration_ms: int
    versions: { old: pass|fail|error|na, new: pass|fail|error|na }
    output_ref: string
    symbols_exercised: [string]
coverage_ref: string
mutation_ref: string
fuzz_ref: string
```

## What the opinionated implementation asks of an adapter today

The implementation in `harness/` calls the functions above through a Python module per ecosystem.
Beyond graph, API, and call sites, each module carries a test toolkit with one name per concern, so a
stage never branches on the language:

| Concern | Functions |
|---|---|
| Prompting | `SYSTEM`, `CATEGORY_TASK`, `prompt_preamble(facts)`, `collection_hint(version)` |
| Reading a response | `extract_code`, `compile_check`, `test_names`, `imports_ok`, `weak_assertions`, `drop_tests` |
| Naming | `test_file_name`, `file_header`, `import_roots`, `dep_roots`, `is_test_file` |
| Environments | `requirements(graph)`, `prefetch(requirements, ...)`, `fixed_candidate(workdir, package)` |
| Running and reading back | `run_tests(env, tests_dir, out_dir, cover, label)`, `parse_results`, `coverage_for` |
| Existing tests | `symbol_refs`, `skipped_tests`; `MUTATION` says whether a mutation engine is wired |

Python and Go both implement the table; the Go half is a small program on go/ast (`gohelper`).

## Adding an adapter

1. Pick tools for each function from the [language flows](../docs/09-language-and-target-flows.md).
2. Pass the license and activity check in workflow 14.
3. Implement the eight functions against a benchmark repository for the ecosystem.
4. Build the pinned sandbox image with Platform.
5. Pilot on one product repository, then enable by default.
