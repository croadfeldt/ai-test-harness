# Example: control-plane, a Go service

**In plain terms.** The second language. The harness's Go adapter read a real Go service, resolved its
250 modules the way the Go toolchain does, checked every one against the vulnerability database, and
for the 14 that carry advisories worked out whether the service actually calls them, what it calls,
and how much testing budget each deserves. This is stages 1 and 2 only; generating and running Go tests
is the next slice. Every file under `rescan/` is harness output.

## Who should read what

| You are | Read | Time |
|---|---|---|
| Deciding whether the approach carries across languages | This page | 3 minutes |
| Building the Go adapter further | `harness/src/harness/adapters/go.py` and `gohelper/` | 20 minutes |

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

## One thing this example fixed in the harness

The first Go analysis scanned the wrong repository for call sites: later stages took the repository
from the local configuration, which pointed at the Python example. Stages that need the repository now
accept `--repo` and refuse to run when the configured repository is not the one intake ran on.

## Reproduce it

```
cd harness
.venv/bin/harness intake  --repo ../../control-plane --ecosystem go --head main --workdir out/go-rescan
.venv/bin/harness analyze --repo ../../control-plane --workdir out/go-rescan
```
