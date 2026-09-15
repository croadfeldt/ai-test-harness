# Example: control-plane, a Go service

**In plain terms.** The second language. The harness's Go adapter read a real Go service, resolved its
250 modules the way the Go toolchain does, checked every one against the vulnerability database, and
for the 14 that carry advisories worked out whether the service actually calls them, what it calls,
and how much testing budget each deserves. Then it took the one module the service calls directly
and that carries advisories, kin-openapi, and ran the whole pipeline on it: a fixed environment
resolved by the Go toolchain, a tool-using agent per issue, sealed runs on both versions, triage, a
packet, a signed attestation, UDLM records, and a post-analysis. One of four issues got a test, and
that test found the fixed version panicking on the same input. Every file under `rescan/` and
`kin-openapi-run1/` is harness output.

## Who should read what

| You are | Read | Time |
|---|---|---|
| Deciding whether the approach carries across languages | This page | 3 minutes |
| Reviewing the kin-openapi result | `kin-openapi-run1/packet/github.com/getkin/kin-openapi/packet.md` | 2 minutes |
| Building the Go adapter further | `harness/src/harness/adapters/go.py`, `gohelper/`, `sandbox_go.py` | 20 minutes |

## What the rescan found

A scheduled scan of `main`: 250 modules, 23 chosen by the service's own go.mod, the rest pulled in by
those. Fourteen carry known advisories.

| Module | Depth | Reachable | Advisories | Risk | Budget |
|---|---|---|---|---|---|
| github.com/getkin/kin-openapi | 1 | true | 8 | 70 | full |
| golang.org/x/crypto | 2 | unknown | 30 | 65 | full |
| github.com/gomarkdown/markdown | 2 | unknown | 4 | 55 | snapshot |
| github.com/jackc/pgx/v5 | 2 | unknown | 6 | 55 | snapshot |
| github.com/labstack/echo/v4 | 2 | unknown | 2 | 55 | snapshot |
| golang.org/x/net | 2 | unknown | 8 | 55 | snapshot |
| google.golang.org/grpc | 2 | unknown | 5 | 55 | snapshot |
| oras.land/oras-go/v2 | 2 | unknown | 10 | 55 | snapshot |
| github.com/klauspost/compress | 2 | unknown | 1 | 45 | snapshot |
| github.com/nats-io/nats-server/v2 | 1 | false | 22 | 45 | reduced |
| github.com/yuin/goldmark | 3 | unknown | 1 | 45 | snapshot |
| go.opentelemetry.io/otel | 2 | unknown | 1 | 45 | snapshot |
| golang.org/x/mod | 2 | unknown | 2 | 45 | snapshot |
| golang.org/x/text | 2 | unknown | 1 | 45 | snapshot |

The one that matters most is clear: kin-openapi is called directly from 25 places in five first-party
files, carries eight advisories, and the advisories name the versions that fix them. nats-server has
the most advisories but the service never calls it; it is a test-time dependency, and the harness
says "not reachable" rather than raising an alarm. Everything at depth 2 or deeper is "unknown"
until the Go adapter learns call-graph reachability, and the blueprint treats unknown as reachable.

## What the Go adapter does differently

| Step | Python adapter | Go adapter |
|---|---|---|
| Dependency graph | pip's resolver inside the project's interpreter image | `go list -m -json all` and `go mod graph` at the commit |
| Package source | wheel download and unpack | `go mod download` into a module cache |
| API surface and call sites | the standard-library AST | a small Go program using go/ast, built at first use |
| Contract diff | required parameters changed means breaking | any signature change means breaking; Go has no optional parameters |
| Vulnerabilities | OSV, PyPI ecosystem | OSV, Go ecosystem, keyed by module path |

Intake took 23 seconds; analysis of the 14 modules about the same.

## The full pipeline on kin-openapi (`kin-openapi-run1/`)

The service is on kin-openapi v0.139.0, which carries four issues, all fixed by v0.144.0. The change
under review left it there (a rescan of `main`), so the harness built the second environment itself:
`go get` on a scratch copy of the service raised the module to v0.144.0 and minimal version selection
moved five other modules with it; that environment is recorded and its module cache prefetched. A
tool-using agent then worked each issue with the same tools as on Python: search and read the
module's source at both versions, list the API, run a test file in the sealed sandbox against both
versions, submit.

| Issue | Agent | Outcome |
|---|---|---|
| CVE-2026-73502, nil-pointer panic on a content parameter without a schema | 16 turns, 13 tool calls | one test submitted; it panics on v0.139.0 **and** on v0.144.0 |
| CVE-2026-76905, panic on malformed multipart | 18 turns | no file that parses; the last three submissions carried the same syntax error |
| CVE-2026-73501, authentication bypass through the default authenticator | 19 turns | no accepted file |
| CVE-2026-77354, resource exhaustion in a query parameter decoder | 18 turns | no accepted file |

The one test that ran is the finding. It builds a request against a spec whose parameter has content
but no schema and calls `ValidateParameter`; the vulnerable version panics, and so does the version
the advisory names as fixed. The harness does not call that a proof, because a fix-pinning test must
pass on the fixed version. It reports "blocked on both versions", records the reproducer, and routes
it as a defect for a person to decide: either the fix does not cover this call path, or the test
reaches the code differently from the report. The packet says so, and all four VEX drafts stay at
"affected", which is the true state of a service on v0.139.0 that calls the module from 25 places.

| What the run produced | |
|---|---|
| Tests | 1 ran on head, again for flakes, and on the fixed candidate; 0 accepted |
| Findings | 1 security (open advisories, reachable), 1 defect (same internal error on both versions, uncorroborated) |
| VEX drafts | 4, all `affected` |
| UDLM records | 11, sealed; statement signed |
| Goals | 9 met, mutation not applicable (no Go engine yet), time to packet measured |
| Generation | 26 minutes on the two-GPU server, 72 model calls, 1.15 million tokens, 42 sealed runs |

The unit file never parsed in three attempts and was discarded, as the rules require. At this model
size, with thinking off, Go syntax is the model's weak point: three of four issues and the unit file
ended on code that would not compile. The harness reported that rather than shipping it. The
stronger-model rung is the next variable, and Go is where it will show first.

## What the Go path adds under the hood

| Step | How |
|---|---|
| Environment | a scratch module whose go.mod requires every module of the service's resolved graph at that version, so selection picks exactly what the service runs with |
| Prefetch | `go mod download all` with the network on, no package code executed; the cache is then mounted read-only with `GOPROXY=off` |
| Sealed run | the same container flags as Python (no network, capabilities dropped, read-only root, limits), `go test -json` with coverage on the module under test; results become junit.xml and coverage.json so every later stage reads them unchanged |
| Gates | a Go program on go/ast: parse, package name, Test functions, imports, tests that cannot fail, and cutting a test out of a file with the imports it alone used |
| Fixed candidate | `go get module@fixed` on a copy of the service at the reviewed commit, then the graph the toolchain resolves |
| Mutation | the same helper mutates the module's source on executed lines (seven operators); the sandbox copies the module out of the read-only cache and points the scratch module at the copy with a replace directive; a mutant that does not compile is invalid, not killed. This run predates it: its one test failed on head, so there was nothing to mutate |
| Not yet | the cluster pod target (the harness image has no Go toolchain) |

## What this example fixed in the harness

The first Go analysis scanned the wrong repository for call sites: later stages took the repository
from the local configuration, which pointed at the Python example. Stages that need the repository now
accept `--repo` and refuse to run when the configured repository is not the one intake ran on.

The kin-openapi run added three more. The agent's tool call carrying a whole test file was cut off at
the per-turn output limit, echoed back as history, and the next request was rejected, which ended the
stage with the file lost; that is register entry GF-021, with a check that runs before every run. Go's
compiler errors arrive as a different kind of event from test output and were not reaching the model,
so it repaired blind for seven turns. And a Go module path has slashes, which had put the module cache
under the wrong directory and named the execute summary row by the wrong segment.

## Reproduce it

```
cd harness
export HARNESS_TARGET_REPO=../../control-plane HARNESS_TARGET_ECOSYSTEM=go
.venv/bin/harness intake   --head main --workdir out/go
.venv/bin/harness analyze  --workdir out/go
.venv/bin/harness generate --workdir out/go --select github.com/getkin/kin-openapi --categories unit cve --mode agent   # needs a model endpoint
.venv/bin/harness execute  --workdir out/go --select github.com/getkin/kin-openapi
for s in mutate relevance triage packet attest; do .venv/bin/harness $s --workdir out/go --select github.com/getkin/kin-openapi; done
.venv/bin/harness assess   --workdir out/go
```

The model was `qwen38-27b` served by vLLM on a two-GPU server, thinking off. The Go sandbox image is
`golang:1.25-bookworm`, recorded by digest.
