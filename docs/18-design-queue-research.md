# Research notes for the design queue

**What this is.** The [design queue](17-design-queue.md) lists what the business-case review changed in the
promise. Before building any of it I researched each item: what the code already has, what the industry
does, and what contradicts the plan as written. This page is the result, written for the engineer who
picks an item up. Q1 is worked to a design. The rest are notes with sources. Nothing here is built.

Every claim about the harness below is checked against the published run
`examples/frc-scheduler-server/pr-fix-known-vulns-235b` (python-jose 3.3.0 to 3.4.0 on the 235B model).
Every claim about another tool carries its source.

## Q1. The three-state output contract: design against the code as it is

**The promise.** Every function a change reaches ends in exactly one state: validated, for your
environment, or stated gap with its reason. Nothing is silent. Carried in the run story, the pull
request text, the run index and the dashboard.

### What the run already knows

| Fact | Where it is today | Shape |
|---|---|---|
| Which symbols the application reaches in a dependency | `analyze/<pkg>/call-sites.json` | `sites[]` with `symbol`, `file`, `line`, `in_test`. Granularity is mixed: a module (`jose.jwt`), a class (`jose.JWTError`), a function (`jose.jwt.decode`). |
| Which symbols a first-party change touched | `analyze/<pkg>/api-diff.json` when base and head differ | `changes[]` with `symbol`, `kind` added/changed/removed, `breaking`. A rescan with no change has no diff; scope is then the package's public API. |
| The public API with file and start line | `analyze/<pkg>/api.new.json` | `symbols[]` with `qualname`, `kind`, `file`, `line`. No end line, in Python or Go. |
| Per-test outcome on both versions | `execute/<pkg>/results.json` | `tests[]` with `status`, `versions.old/new`, `verdict`, `category`. `symbols_exercised` is what the model said it targeted, not what was measured. |
| Lines executed | `execute/<pkg>/new/coverage.json` | Per file, for the whole run. Not per test. |
| Mutants and who killed them | `execute/<pkg>/mutation/mutation.json` | `mutants[]` with `file`, `line`, `status`, `killed_by`; `per_test` with `killed` and `unique`. 25 sampled of 139 sites on the example. |
| Triage verdict per test | `triage/<pkg>/triage.json` | `tests[]` with `class`, `confidence`, `action`; `summary.tests_accept`. |
| What the team's suite references | `analyze/<pkg>/facts.json` `upstream_tests` | Counts of test files referencing the package and the changed symbols. Not coverage. |

### What a dry run of the contract says about the published run

I computed the accounting by hand on the example, using the start line of each public symbol and the
next symbol's start as its span. Five call-site symbols are reached. Two are not behaviours: `jose.jwt`
is a module import, and `jose.JWTError` is a re-export whose definition is `jose.exceptions.JWTError`
(the call-site symbol does not match any API symbol, so re-exports need resolving). The three functions:

| Reached function | Lines executed by kept tests | Mutants sampled in its span | State under the contract |
|---|---|---|---|
| `jose.jwt.encode` (lines 26 to 67) | 5 | 0 | stated gap: executed, strength not shown |
| `jose.jwt.decode` (68 to 181) | 14 | 0 | stated gap: executed, strength not shown |
| `jose.jwt.get_unverified_header` (182 to 201) | 4 | 0 | stated gap: executed, strength not shown |

The four mutants placed in `jose/jwt.py` sit at lines 260 to 357, inside the private helpers `decode`
calls, and three were killed. So the published run, which the evaluation table reads as "proves fixes: 1
fix-pinning confirmed", would under the contract report zero validated functions and three gaps. That
is the honest reading and it exposes two design requirements, not one:

1. **Mutant sampling must be stratified over the reached symbols**, or almost every reached function
   will land in "strength not shown" by construction. Today the sample is uniform over the package's
   139 sites; 25 draws reached none of the three functions the application calls.
2. **A function's strength evidence must include the private helpers it calls.** The behaviour of
   `decode` lives in `_validate_claims` and friends. A span bounded by the public symbol misses the
   lines where breakage would be caught. The unit of strength is the public symbol plus its same-module
   private callees (a static call closure within the file, which the parser gives cheaply).

### The contract, defined

**Unit of accounting.** A reached behaviour: for a dependency, each distinct call-site symbol outside
test files that resolves to a public function, method or class of the package, with re-exports resolved
to their definition; a bare module import is not a unit. For a first-party change, each added or changed
public symbol. For a rescan with no change, every public symbol, with those beyond the budget recorded
as `out-of-budget` gaps rather than dropped.

**States and the evidence each requires.**

| State | Requires | Evidence recorded |
|---|---|---|
| `validated` | At least one kept test (passes on head, consistent across the repeat runs, triage class not `test-bug`) executed a line inside the unit's span or its private callees, and at least one sampled mutant inside that closure was killed by a test that executed the unit. | test ids, lines executed of lines in closure, mutants sampled and killed in closure, old/new verdicts |
| `for-your-environment` | A test exists for the unit whose run was refused by the testbed for a declared need (Q2, Q3), or whose declaration names a need the harness does not provide (network, machine). Until Q2 and Q3 land this state is populated only from execute verdicts whose error matches an environment pattern (permission denied, operation not permitted, name resolution, missing device). | test ids, the declaration, the refusal |
| `stated-gap` | Everything else, with exactly one reason code. | reason, and whatever partial evidence exists |

**Reason codes for a gap**, in the order they are checked: `pipeline-cannot-validate` (a P-rule says
the repository's CI cannot run or validate the proposed tests), `no-test-generated` (no kept test names
or executes the unit), `did-not-build` (every candidate for the unit failed to compile or collect),
`flaky` (the only tests for the unit disagreed with themselves), `failed-on-head` (the tests for the unit
are wrong, class `test-bug`), `executed-not-checked` (lines ran, no mutant in the closure was killed),
`strength-not-sampled` (lines ran, no mutant was placed in the closure; a sampling failure the harness
owns, see requirement 1), `out-of-budget`. A unit the team's own suite references carries
`team_suite_references: true` as evidence; it does not change the state, because the harness has not
measured the team's coverage.

**Nothing silent.** Every unit appears exactly once. The counts in the roll-up sum to the number of
units. A unit with no state is a harness defect and fails the new assessment goal.

### Where it lands

- **New module** `stages/account.py`, run at the end of triage, since it needs execute, mutate and triage.
  Writes `triage/<pkg>/accounting.json` (units with state, reason, evidence) and `triage/accounting.json`
  (counts per package and in total).
- **`model.ApiSymbol` gains `end_line`.** Python: `ast` nodes carry `end_lineno` since 3.8. Go: the
  helper has `fset.Position(x.End()).Line`. Both are one-line changes in the extractors. Private callees
  within the file come from the same parse.
- **Per-test line attribution.** Python: coverage.py dynamic contexts, `[run] dynamic_context =
  test_function` in a `.coveragerc` the sandbox writes into `/work`, then `coverage json --show-contexts`
  (the option exists: "Show contexts for covered lines"), which labels each executed line with the tests
  that ran it. One run, no extra cost. Go: `go test -coverprofile` is per package; for the kept tests
  only (a handful), rerun each with `-run '^Name$' -count=1 -coverprofile` inside the same sandbox.
  Until this lands, the first iteration attributes execution from the aggregate coverage and strength
  from `killed_by`, which is already per test.
- **Mutation sampling** in `mutate.py`: allocate the sample across the reached units' closures first,
  remainder over the package. The team's mutant budget is unchanged; its placement changes.
- **Story** gains a section "What was accounted for": the three counts, then the gaps with reasons.
  **Pull request text** gains a short "Not covered" list (the full report with line notes is Q6).
  **Run index** carries the three counts per package; **dashboard** tiles show validated, for your
  environment, gaps beside the existing accepted and proven. **Catalogue** entries for the two new files.
- **Assessment** gains G13: every reached unit has exactly one state and the counts sum. **Blueprint**
  gains principle 14 beside 12 and 13, in the three-page blueprint and the reference; the specification
  gains R23. The evaluation table gains a "validated" column, which will read lower than "accepted" and
  should.

### Order of work

1. PR A: `end_line`, resolution of re-exports, `account.py` from the data that exists, story, pull
   request text, index, dashboard, G13, principle 14, R23, catalogue, tests on the example runs (every
   call-site symbol appears exactly once; the python-jose example yields three `strength-not-sampled`
   gaps, which is the test that the contract tells the truth).
2. PR B: coverage contexts in the Python sandbox, closures from private callees, stratified mutant
   sampling. Rerun the python-jose example and publish the before and after.
3. PR C: Go per-test attribution.

### What changes in the published numbers

Expect "validated" to be small at first, smaller than "accepted" on every published run, because the
sampling never aimed at the reached functions. That is the finding, not a regression: the number the
table showed was never the number the case promised. Once sampling is stratified, validated should
approach accepted on Python; on Go it stays near zero until the model rung changes, and the contract
will say so.

## Q2, Q3, Q4. Declared needs, testbed failure, repeat counts

**What the industry does.** Debian's autopkgtest puts the declaration on the test (`needs-internet`,
`isolation-container`, `isolation-machine`, `flaky`, `skippable`) and reports a testbed failure at the
run level, exit 16, apart from test failures. Bazel does the same split: tags on the target
(`requires-network`, `block-network`, `exclusive`, `local`), statuses `PASSED, FLAKY, TIMEOUT, FAILED,
REMOTE_FAILURE`, exit codes 32 and 36 for environment failures, and a `TEST_INFRASTRUCTURE_FAILURE_FILE`
that "should only be used to report failures originating from the testing infrastructure." tmt puts the
isolation choice on the plan, not the test (`provision: local | container | virtual | connect`), lets
tests declare `require`, `recommend`, `duration`, `tag` and `adjust` rules, and reports `pass, fail,
info, warn, error, skip` where `error` means "human inspection is needed to investigate whether it was
a test bug, infrastructure error or a real test failure." Testing Farm keeps a request-level `error`
state for provisioning and environment failures, apart from "tests failed."

**Enforcement precedents.** pytest-socket fails any test that touches a socket when `--disable-socket`
is set, with `--allow-hosts` for localhost and per-test `@pytest.mark.enable_socket`. pytest-remotedata
marks tests `remote_data`, skips them by default, and with `remote_data_strict` fails unmarked tests that
reach the internet. Go has no marker: `//go:build integration` files are invisible to `go test` without
`-tags`, and `t.Skip` under `testing.Short()` is the convention; `go test -json` carries no skip reason
field, the reason is in the preceding `output` events; always pass `-count=1` or repeat runs replay the
cache.

**Interchange formats.** JUnit XML has `skipped`, `failure`, `error`; pytest already routes fixture and
setup problems to `error` and assertion failures to `failure`. CTRF has `passed, failed, skipped,
pending, other`, plus `retries` and `flaky` per test. Neither has an infrastructure-failure status.

**Repeat counts.** TestGen-LLM: "a test that does not pass on every one of five executions is deemed
flaky." Bazel: three attempts for targets marked flaky, one otherwise. CoverUp repeats and prompts the
model for a correction when a test is flaky; its default count is undocumented.

**Kata and gVisor on OpenShift.** The sandboxed containers operator installs RuntimeClass `kata`;
"Nested virtualization is not supported," so Kata needs bare-metal worker nodes; `kata-remote` offloads
to a cloud VM and "is not yet fully supported." gVisor has no CRI-O handler on OpenShift and no Red Hat
support, though its `systrap` platform would run on VM workers. A pod naming a RuntimeClass that does
not exist enters `Failed` with an event before any test code runs. Tekton podTemplate supports
`runtimeClassName`.

**What this changes in the plan.**

1. **Split "the environment refused" into two events.** Refusal of a *declared* need the harness said it
   would provide is a testbed failure. Use of an *undeclared* need is a defect in the test's
   declaration, which is what pytest-socket and pytest-remotedata do, and the test fails. The design
   sentence "a test that fails because the testbed refused something is never a defect" would otherwise
   turn every undeclared network call into a non-defect.
2. **Testbed failure lives at the run level in every precedent.** Keep `testbed-failure` as the harness's
   internal class, and define its export: JUnit `<error type="testbed-failure">`, CTRF `other` with a
   label, and a run-level flag in the results and the story. Do not expect consumers to tell it apart on
   their own.
3. **"Skip with a structured reason" is the interoperable answer when the need is known up front.** If
   the sandbox knows it cannot honour `network` or `machine`, report `skipped` with the reason and route
   to "for your environment." Reserve `testbed-failure` for "we tried to provide it and it broke."
4. **The `machine` tier has no supported runtime on a VM-hosted OpenShift cluster.** Define it either as a
   VM provisioned outside the cluster (tmt `virtual` or `connect`, Testing Farm's Artemis model) or as an
   admitted-unavailable tier that yields "for your environment" by construction on such clusters. Fail
   fast at scheduling with the RuntimeClass `nodeSelector` rather than at sandbox start.
5. **Five repeats before proposal**, matching the published Meta number; carry `retries` and `flaky` in
   the per-test record so the repeat result exports in CTRF's own fields.
6. **For Go, prefer `t.Skip` guarded by an environment check over build tags** for any test the ledger
   must see, and parse `output` events for the reason.

Sources: [autopkgtest spec](https://salsa.debian.org/ci-team/autopkgtest/-/raw/master/doc/README.package-tests.rst),
[autopkgtest manual](https://manpages.debian.org/testing/autopkgtest/autopkgtest.1.en.html),
[Bazel test encyclopedia](https://bazel.build/reference/test-encyclopedia),
[Bazel test status](https://raw.githubusercontent.com/bazelbuild/bazel/master/src/main/protobuf/test_status.proto),
[Bazel exit codes](https://bazel.build/run/scripts), [tmt tests](https://tmt.readthedocs.io/en/stable/spec/tests.html),
[tmt results](https://tmt.readthedocs.io/en/stable/spec/results.html),
[tmt provision](https://tmt.readthedocs.io/en/stable/plugins/provision.html),
[Testing Farm results](https://docs.testing-farm.io/Testing%20Farm/0.1/test-results.html),
[pytest-socket](https://github.com/miketheman/pytest-socket), [pytest-remotedata](https://github.com/astropy/pytest-remotedata),
[pytest skipping](https://docs.pytest.org/en/stable/how-to/skipping.html),
[pytest junitxml source](https://raw.githubusercontent.com/pytest-dev/pytest/main/src/_pytest/junitxml.py),
[go build constraints](https://pkg.go.dev/cmd/go#hdr-Build_constraints), [test2json](https://pkg.go.dev/cmd/test2json),
[CTRF status](https://ctrf.io/docs/specification/status), [JUnit XML](https://github.com/testmoapp/junitxml),
[TestGen-LLM](https://arxiv.org/abs/2402.09171), [CoverUp](https://github.com/plasma-umass/CoverUp),
[OpenShift sandboxed containers](https://docs.redhat.com/en/documentation/openshift_sandboxed_containers/1.9/html-single/user_guide/user_guide),
[Kubernetes RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/),
[gVisor platforms](https://gvisor.dev/docs/architecture_guide/platforms/), [Tekton pod templates](https://tekton.dev/docs/pipelines/podtemplates/).

## Q6, Q7, Q12. Reporting on the pull request, the gate, reviewer time

**GitHub.** Check runs carry up to 50 annotations per request (`path`, `start_line`, `end_line`,
`annotation_level` notice/warning/failure, `message` up to 64 KB), more by updating the run; conclusions
`success, failure, neutral, skipped, action_required, timed_out, cancelled, stale`. "Write permission
for the REST API to interact with checks is only available to GitHub Apps"; a token can only post commit
statuses (`error, failure, pending, success`, no annotations). Inside Actions, `GITHUB_TOKEN` is an App
installation token, so a workflow can create check runs with `checks: write`; `::error file=,line=`
workflow commands annotate without the API but cap at 10 per level per step and 50 per job. Branch
protection requires checks by name: "Required status checks must have a successful, skipped, or neutral
status before collaborators can make changes," and rulesets expect the same App to have "recently
submitted a check run." Code scanning accepts any SARIF 2.1.0 but needs Code Security on private
repositories, fails only on error, critical or high, and leaves persistent alerts to dismiss.

**GitLab.** The code quality report (`description`, `check_name`, `fingerprint`, `severity`,
`location.path`, `location.lines.begin`) shows in the MR widget on all tiers and as diff-gutter markers
on Ultimate only. External status checks are Ultimate only and "fail if they stay in the pending state
for more than two minutes." On every tier the enforceable gate is "Pipelines must succeed," which
"requires the existence of a successful pipeline," so the harness job must itself fail the pipeline.

**Tekton and Konflux.** Task results are limited to 4 KB by the termination message, 1.5 MB with sidecar
logs. Konflux ADR-0030 defines the `TEST_OUTPUT` result: `result` in `SUCCESS, FAILURE, WARNING, SKIPPED,
ERROR` plus `successes`, `failures`, `warnings`, `note`. The integration service reports each scenario's
status to the forge as a check run or commit status, pass or fail, and `WARNING` passes. Conforma reads
`TEST_OUTPUT` from the build attestation or signed test-result attestations (`predicate.result`,
`predicate.timestamp`, `predicate.configuration[0].name`) at release time, with rules `no_failed_tests`,
`no_erred_tests`, `no_skipped_tests`.

**Reviewer time.** GitHub: the issue timeline carries `reviewed` (with `submitted_at`),
`review_requested`, `ready_for_review` and `convert_to_draft` events; the pull request has `created_at`
and `merged_at`. GitLab: notes with `created_at` and `system`, approvals with `approved_at`, reviewer
`state`, and resource state events. Vendors disagree on the start: LinearB measures pickup from PR
creation and review time from first review activity to merge; Swarmia from review request to first
review; Faros from ready-for-review to approval. Pick one and state it.

**Precedents for a "not covered" view.** Codecov posts `codecov/patch` ("only measures lines adjusted
in the pull request") with `target`, `threshold` and `informational`, and a comment of the form "Patch
coverage is 76.3% with 14 lines in your changes missing coverage" plus a files table. Coveralls lists
"NEW UNCOVERED LINES." SonarQube's gate applies only new-code conditions in pull request analysis and
decorates with a status, a summary comment and inline annotations. None of them annotate code outside
the diff.

**What this changes in the plan.**

1. **The harness needs a GitHub App identity to annotate**, or must ride the Actions token when it runs
   as a workflow. From Tekton or Konflux it calls the Checks API itself with App credentials or falls
   back to commit statuses and a comment. This is the bot account question already on Chris's list,
   now with a reason.
2. **"For your environment" cannot map to `neutral` if it is meant to hold a merge.** Neutral and
   skipped both pass branch protection. The verdict check's conclusion is `success` or `failure` as the
   team's policy decides; the three states go in the summary text.
3. **One stable check name per repository**, for example `ai-test-harness / verdict`, or nothing can
   require it.
4. **Annotate within the diff first.** Every precedent scopes to changed lines, and GitHub shows
   annotations outside the diff only on the Checks tab. The "Not covered" section in the pull request
   body carries the whole list; annotations go on the lines of unchecked behaviours that are inside the
   change, in batches of 50.
5. **Print the threshold and the measured value in the same sentence** in the check summary, the way
   Codecov's status does, to avoid the "red cross but green gate" confusion documented in its issues.
6. **On GitLab Free and Premium the harness job fails the pipeline itself**; the code quality artifact
   is the inline channel and works on every tier for the widget.
7. **In Konflux, emit `TEST_OUTPUT`** in the ADR-0030 shape so Conforma can gate at release, and post
   the full verdict to the forge from the task.
8. **Reviewer time definition:** from the harness's pull request becoming ready for review to the first
   review activity (pickup), and to merge or close (review time), with bots excluded, which is Swarmia's
   definition with LinearB's end point. Computed from the timeline in `feedback.py`.

Sources: [GitHub check runs](https://docs.github.com/en/rest/checks/runs),
[using the Checks API](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-checks),
[commit statuses](https://docs.github.com/en/rest/commits/statuses),
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches),
[workflow commands](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands),
[SARIF support](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning),
[issue timeline](https://docs.github.com/en/rest/issues/timeline),
[GitLab code quality](https://docs.gitlab.com/ci/testing/code_quality/),
[GitLab status checks](https://docs.gitlab.com/user/project/merge_requests/status_checks/),
[GitLab merge checks](https://docs.gitlab.com/user/project/merge_requests/auto_merge/),
[Tekton tasks](https://tekton.dev/docs/pipelines/tasks/), [Konflux ADR-0030](https://konflux-ci.dev/architecture/ADR/0030-tekton-results-naming-convention/),
[Konflux integration service](https://konflux-ci.dev/architecture/core/integration-service/),
[Conforma release.test](https://conforma.dev/docs/policy/packages/release_test.html),
[Conforma test attestations](https://conforma.dev/docs/policy/packages/release_test_attestation.html),
[Codecov statuses](https://docs.codecov.com/docs/commit-status), [Coveralls notifications](https://docs.coveralls.io/app-notifications),
[SonarQube quality gates](https://docs.sonarsource.com/sonarqube-server/2026.1/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates),
[LinearB review time](https://linearb.helpdocs.io/article/f3dzgrpt4a-review-time-metric),
[Swarmia time to review](https://help.swarmia.com/features/metrics/pull-request-cycle-time/time-to-review).

## Q5, Q13, Q17. Behaviour worklist, reachability, oracle quality

**Nothing off the shelf enumerates behaviours.** No tool in Python or Go produces a per-function list of
return paths, error paths and parameter ranges. The parsers give the nodes; the enumeration is ours to
write, which the plan already assumed. What the parsers give: Python `ast` has `Return`, `Raise`,
`FunctionDef.args` with annotations, `Try` and `ExceptHandler`, and `end_lineno` on every node since 3.8.
Go has `ast.ReturnStmt`, `FuncType.Results`, and `go/types` signatures; `go/ssa` reduces every function
to blocks ending in `If`, `Jump`, `Return` or `Panic`, which is the return and error path inventory at
IR level.

**Where the parser falls short.** Python `ast` misses implicit `None` fall-through, exceptions raised by
callees, and raises inside `with` blocks and comprehensions; codeanalyzer-python's control-flow graph at
analysis level 3 models raises and is the better base than a hand-rolled visitor. Parameter ranges are
not in Python source: only `Annotated[int, Ge(0), Le(100)]` with annotated-types markers carries bounds,
and few codebases use it. So the Python "range" column is the declared type plus the boundaries the type's
domain implies (zero, negative, empty, `None`, maximum), not something read from source. Go types carry
no ranges either.

**Reachability, Go.** govulncheck's recipe is documented and reproducible from `golang.org/x/tools`:
`ssa.NewProgram` with `InstantiateGenerics`, `cha.CallGraph` as the initial graph, `vta.CallGraph` over
it, then a second vta pass, then `DeleteSyntheticNodes`. Entry points: for `main` packages only `main`
and `init`; for library packages, exported functions; generic entry functions are skipped (open TODO).
govulncheck itself exposes only findings and call stacks for vulnerable symbols, not the graph, and its
graph package is internal, so the recipe must be rebuilt; vta is "in experimental phase." Reflection and
function pointers are handled conservatively.

**Reachability, Python.** Every precise call-graph generator is dead: PyCG archived November 2023 (its
paper claimed 99 percent precision and 70 percent recall, so it missed edges even when alive); the
Jarvis fork archived March 2026; pytype archived, last supported Python 3.12. CodeLLM-Devkit's Python
backend (Jedi plus a def-use pass, "sound-leaning and over-approximate") is the only maintained option
beyond call sites and import roots. CLDK is Apache-2.0, release 1.5.0 July 2026, offline, and covers
Java, Python and TypeScript; Go support is an open issue from September 2026 with a contributor guide
and no backend. OWASP dep-scan lists Go reachability through its `golem` plugin (go/packages with SSA),
Python through atom; atom's own slice spec lists Java, JavaScript and TypeScript for reachables and says
"repeated runs could yield slightly varying results." Neither publishes precision or recall.

**Checked coverage.** Defined as "the dynamic slice of covered statements that actually influence an
oracle," computed by backward dynamic slicing from each assertion with JavaSlicer. Java only, including
the 2023 host-checked-coverage extension; no Python or Go slicer exists, and building one means a
tracer-based dependency tracker. The honest substitute with evidence behind it is state field coverage
(Molina, Aguirre, Gorla, ASE 2025): the share of an object's fields an oracle may read, statically
computed from the test's AST and the class's field list, which "strongly correlates with the oracles'
fault-detection ability, measured by mutation score." Assertion density is cheap but measures production
asserts, not test oracles.

**Condition and boundary enumeration.** Hypothesis `from_type` builds strategies from annotations and
honours annotated-types bounds; its ghostwriter emits starting-point tests. CrossHair `cover` uses Z3 to
find inputs that distinguish paths from type annotations, the closest thing to automatic partitioning
for Python. For Go, `rapid` biases generation to edge cases and `gomcdc` (released this month) measures
unique-cause and masking MC/DC from Go tests. No Python MC/DC tool works from source; py-mcdc takes
hand-written boolean expressions.

**What this changes in the plan.**

1. **Behaviour worklist, Python:** build on `ast` for signatures, explicit returns and raises, plus a
   control-flow pass (Scalpel's or codeanalyzer-python's) for implicit paths; bounds come from the type's
   domain, labelled as inferred. **Go:** `go/types` for signatures, `go/ssa` for `Return` and `Panic`
   sites and error-result paths.
2. **Reachability, Go:** reimplement govulncheck's cha-then-vta recipe from `x/tools` in the Go helper,
   restricting entry points to `main` packages for applications. **Python:** call sites and import roots
   stay the primary signal; CLDK's over-approximate graph is the one upgrade worth trying, and it should
   be measured against call sites on the reference jobs before it is trusted.
3. **Do not promise checked coverage.** Q17 becomes "oracle strength measure": mutation score as the
   primary, state field coverage as the cheap static companion, both labelled for what they are.
4. **Boundary and partition tests:** give the model the type-domain boundaries as inputs to try, and
   consider CrossHair `cover` as a path-input generator for Python functions with annotations.

Sources: [CLDK](https://github.com/codellm-devkit/python-sdk), [CLDK Go issue](https://github.com/codellm-devkit/python-sdk/issues/422),
[codeanalyzer-python](https://github.com/codellm-devkit/codeanalyzer-python), [Python ast](https://docs.python.org/3/library/ast.html),
[PyCG](https://github.com/vitsalis/PyCG), [Jarvis fork](https://github.com/nuanced-dev/jarviscg), [pytype](https://github.com/google/pytype),
[Scalpel](https://github.com/SMAT-Lab/Scalpel), [go/callgraph](https://pkg.go.dev/golang.org/x/tools/go/callgraph),
[vta](https://pkg.go.dev/golang.org/x/tools/go/callgraph/vta), [govulncheck internals](https://go.googlesource.com/vuln/+/refs/heads/master/internal/vulncheck/utils.go),
[govulncheck entry points](https://go.googlesource.com/vuln/+/refs/heads/master/internal/vulncheck/entries.go),
[atom slices](https://github.com/AppThreat/atom/blob/main/specification/docs/slices.md), [dep-scan reachability](https://depscan.readthedocs.io/reachability-analysis/),
[checked coverage](https://dl.acm.org/doi/10.1109/ICST.2011.32), [oracle metrics survey](https://arxiv.org/pdf/2212.06118),
[host checked coverage](https://arxiv.org/abs/2308.00316), [state field coverage](https://arxiv.org/abs/2510.03071),
[Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html), [CrossHair cover](https://crosshair.readthedocs.io/en/latest/cover.html),
[rapid](https://pkg.go.dev/pgregory.net/rapid), [gomcdc](https://pkg.go.dev/github.com/shrydev2020/gomcdc/v2).

## Q8, Q9, Q11. The team's configuration, planning to a budget, reference jobs

**Configuration in the team's repository.** Every surveyed tool keeps a file in the repository, and none
of them puts defaults or reasons in it. The file holds overrides; defaults live in the vendor's
documentation and a published schema. Renovate is the strongest model: fourteen accepted file locations,
a documentation table per option with `type` and `default`, a published JSON schema, a validator
(`renovate-config-validator`, non-zero exit on warnings), presets (`extends: ["config:recommended"]`) and
automated "config migration" pull requests when the format changes. Codecov's `codecov.yml` separates a
`project` status from a `patch` status ("only measures lines adjusted in the pull request"), each with
`target`, `threshold` and `informational`. Dependabot has no official schema after an issue open since
2020. SonarQube keeps the quality gate server-side and read-only; the repository file carries analysis
parameters only. Allstar puts policy at the organisation with repository opt-out, the opposite direction
from "the team owns every number."

**Measuring throughput.** OpenAI-compatible responses carry token counts (`usage`, and with
`stream_options.include_usage` a final usage chunk) and no timing; the client owns the clock. llama.cpp
adds a `timings` object per response (`prompt_per_second`, `predicted_per_second`) and `/metrics` gauges
that average over all slots. vLLM exposes Prometheus histograms (`time_to_first_token_seconds`,
`request_time_per_output_token_seconds`) and, behind a flag, per-request `tokens_per_second`, null when
`n > 1`. On OpenShift AI the vLLM runtime is annotated for scraping but only works with user workload
monitoring enabled.

**Planning to a budget.** No CI tool measures model throughput and scales work; the planner is novel.
The closest precedent is mutation testing: Stryker and PIT run the suite once and derive per-mutant
timeouts as measured time times a factor plus a constant (Stryker 1.5 and 5 seconds, PIT 1.25 and 4
seconds). Everything else is a fixed cap: Bazel's four size buckets, CIFuzz's 600-second default that
"should scale with project size," go test's ten minutes, EvoSuite's 60-second search budget. Hypothesis
turns its wall-clock deadline off in CI because timing there is noisy.

**Reference jobs.** For Python and Go with a vulnerable version, a fixed version and a test that fails
then passes: Vul4Py (100 Python vulnerabilities, each with an exploit oracle that must fail then pass and
a project-native functional oracle that must pass on both; the pair rejected 15 of 119 patches an
exploit-only oracle accepted) and PatchEval (1,000 CVEs in Go, JavaScript and Python, 230 with sandboxes
for security and functionality tests; the only Go source found). Vul4J and Defects4J are Java; ARVO and
SEC-bench are C and C++; CVEfixes has fix commits and no tests; BugsInPy is functional bugs, and only 67
percent reproduced three years on. TDD-Bench Verified (449 Python instances, Apache-2.0) scores
fail-to-pass plus coverage of the gold change. Benchmarks decay and leak: Claude Code solved 851 of 854
Defects4J bugs with leakage through cached dependencies and pre-installed reference patches, and 62
percent of its test-adequate patches differed from the developer's fix; SWE-bench-Live exists because
SWE-bench is in training data.

**What this changes in the plan.**

1. **Q8:** the team's file holds overrides, as everywhere else. The harness ships a schema with `default`
   and `description` per field (Renovate style), a validator, and writes a *resolved* configuration into
   every run showing each effective value, its source (default or the team's file) and the reason. That
   resolved file is where "every number, its default and the reason" lives, and the run story links it.
   When a default changes, the harness opens a migration pull request the way Renovate does.
2. **Q9:** the probe times single-sample streamed requests itself and reads the server's own `timings` or
   per-request metrics when offered; it must probe at the concurrency it will use, since server averages
   hide it. The plan applies slack the way Stryker and PIT do, measured times a factor plus a constant,
   rather than fitting the budget exactly, and the budget is the team's number, as CIFuzz leaves it.
3. **Q11:** a reference job's known answer is two-sided, fail-to-pass and pass-to-pass, or it will accept
   regressions. Score against the behavioural oracle, not patch equality. Expect decay: rebuild the
   reference jobs' environments as sealed images and re-verify them on a schedule. Seed the pool from
   Vul4Py and PatchEval for Python and Go, and let pilot teams add their own on their own services,
   which are the only jobs guaranteed not to be in any model's training data.

Sources: [Renovate options](https://docs.renovatebot.com/configuration-options/), [Renovate presets](https://docs.renovatebot.com/config-presets/),
[Renovate validator](https://docs.renovatebot.com/config-validation/), [Codecov statuses](https://docs.codecov.com/docs/commit-status),
[Dependabot options](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference),
[Dependabot schema issue](https://github.com/dependabot/dependabot-core/issues/1927),
[SonarQube analysis parameters](https://docs.sonarsource.com/sonarqube-server/latest/analyzing-source-code/analysis-parameters/configuration-overview/),
[Allstar](https://github.com/ossf/allstar/blob/main/README.md), [OpenAI streaming](https://developers.openai.com/cookbook/examples/how_to_stream_completions),
[llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md), [vLLM metrics](https://docs.vllm.ai/en/latest/design/metrics/),
[vLLM per-request metrics](https://docs.vllm.ai/en/stable/features/per_request_metrics/),
[OpenShift AI model serving](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.16/html-single/serving_models/index),
[Stryker configuration](https://stryker-mutator.io/docs/stryker-js/configuration/), [PIT options](https://pitest.org/quickstart/commandline/),
[CIFuzz](https://google.github.io/oss-fuzz/getting-started/continuous-integration/), [Hypothesis settings](https://hypothesis.readthedocs.io/en/latest/reference/api.html),
[Vul4Py](https://arxiv.org/abs/2608.00692), [PatchEval](https://arxiv.org/abs/2511.11019), [TDD-Bench Verified](https://github.com/IBM/TDD-Bench-Verified),
[Vul4J](https://github.com/tuhh-softsec/vul4j), [CVEfixes](https://github.com/secureIT-project/CVEfixes), [BugsInPy reproduction](https://par.nsf.gov/biblio/10515105-reproducing-improving-bugsinpy-dataset),
[Defects4J saturation](https://github.com/ASSERT-KTH/defects4j-saturation), [SWE-bench-Live](https://arxiv.org/abs/2505.23419).

## What the research changes in the queue

Changes to make in the [design queue](17-design-queue.md) once Chris agrees:

| Item | Change |
|---|---|
| Q1 | Add stratified mutant sampling over reached units and the private-callee closure as requirements, not options; the dry run shows the contract reports zero validated functions without them. |
| Q2 | Add the fifth declared state, `skipped` with a structured reason, for needs known unmet up front. Define `machine` as a VM outside the cluster or an admitted-unavailable tier. Split undeclared use (a test defect) from refused declared need (testbed failure). |
| Q3 | Testbed failure is a run-level flag plus a per-test class; define the JUnit and CTRF export mapping. |
| Q4 | Five repeats before proposal; record `retries` and `flaky` per test. |
| Q5 | Python ranges are inferred from the type's domain, not read; use a control-flow pass for implicit paths. |
| Q6 | Annotations within the diff only; the full list in the pull request body; 50 per request. |
| Q7 | Needs a GitHub App identity (the bot account item); `neutral` does not hold a merge; one stable check name; print threshold and value together; emit Konflux `TEST_OUTPUT`. |
| Q8 | Overrides in the team's file, schema with defaults and descriptions, resolved configuration written per run, migration pull requests. |
| Q9 | Client-side timing at run concurrency; slack factor plus constant, not exact fit. |
| Q11 | Two-sided known answers; sealed, re-verified environments; seed from Vul4Py and PatchEval; pilot teams' own jobs. |
| Q12 | Define reviewer time as ready-for-review to first review activity and to merge, bots excluded. |
| Q13 | Go: rebuild govulncheck's recipe from x/tools; Python: call sites and import roots, CLDK as the measured upgrade. |
| Q17 | Rename to "oracle strength measure": mutation score primary, state field coverage as the static companion; checked coverage is not buildable without a slicer. |
