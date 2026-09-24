"""Command line entry point. One subcommand per stage, each reading and writing the work directory."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .util import HarnessError, log, now_iso, read_json, tool_version, write_json


def _record_run(workdir: Path, args: argparse.Namespace) -> None:
    """The run record names things, never local paths: the repository by name, the work directory by its last segment."""
    def public(k, v):
        if k == "repo":
            return Path(v).name if v else None
        if isinstance(v, Path):
            return v.name
        return v
    write_json(workdir / "run.json", {
        "harness_version": __version__, "started": now_iso(),
        # Only an argument that is a path on this machine is shortened; a branch name such as deps/x is kept.
        "command": [Path(a).name if "/" in a and Path(a).exists() else a for a in sys.argv[1:]],
        "tools": {"python": sys.version.split()[0], "pip": tool_version([sys.executable, "-m", "pip", "--version"]),
                  "git": tool_version(["git", "--version"])},
        "args": {k: public(k, v) for k, v in vars(args).items() if k != "func"},
    })


def _ecosystem_and_manifest(ecosystem: str | None, manifest: str | None) -> tuple[str, str]:
    """The configured manifest belongs to the configured ecosystem. An ecosystem named on the command
    line takes its own default manifest unless one is named too; otherwise a Go run on a machine
    configured for a Python repository would look for requirements.txt."""
    from . import config
    default_manifest = {"go": "go.mod", "python": "requirements.txt"}
    if ecosystem:
        return ecosystem, manifest or default_manifest[ecosystem]
    ecosystem = config.get("target", "ecosystem", "HARNESS_TARGET_ECOSYSTEM", "python")
    return ecosystem, manifest or config.get("target", "manifest", None, default_manifest[ecosystem])


def cmd_intake(a: argparse.Namespace) -> int:
    from . import config
    from .stages.intake import intake
    repo = config.target_repo(str(a.repo) if a.repo else None, a.workdir)
    a.repo = repo
    a.ecosystem, a.manifest = _ecosystem_and_manifest(a.ecosystem, a.manifest)
    a.python_version = a.python_version or config.get("target", "python_version", None, None)
    _record_run(a.workdir, a)
    wl = intake(repo=repo, head=a.head, base=a.base, manifest=a.manifest, workdir=a.workdir,
                ecosystem=a.ecosystem, python_version=a.python_version)
    print(a.workdir / "intake" / "worklist.json")
    return 0


def cmd_analyze(a: argparse.Namespace) -> int:
    from .stages.analyze import analyze
    analyze(workdir=a.workdir, select=a.select, all_rows=a.all, python_version=a.python_version, repo=str(a.repo) if a.repo else None, target=a.target)
    print(a.workdir / "analyze" / "summary.json")
    return 0


def cmd_selfcheck(a: argparse.Namespace) -> int:
    from . import selfcheck
    rec = selfcheck.run(a.workdir, a.python_version, probes=not a.no_probes, sandbox_only=a.sandbox_only)
    if a.workdir:
        print(a.workdir / "selfcheck" / "selfcheck.json")
    return 0 if rec["passed"] else 3


def cmd_generate(a: argparse.Namespace) -> int:
    from .stages.generate import generate
    generate(workdir=a.workdir, select=a.select, categories=a.categories, python_version=a.python_version, mode=a.mode)
    print(a.workdir / "generate" / "summary.json")
    return 0


def cmd_execute(a: argparse.Namespace) -> int:
    from .stages.execute import execute
    execute(workdir=a.workdir, select=a.select, python_version=a.python_version)
    print(a.workdir / "execute" / "summary.json")
    return 0


def cmd_mutate(a: argparse.Namespace) -> int:
    from .stages.mutate import mutate
    mutate(workdir=a.workdir, select=a.select, python_version=a.python_version, sample=a.sample)
    print(a.workdir / "execute" / "mutation-summary.json"); return 0


def cmd_relevance(a: argparse.Namespace) -> int:
    from .stages.relevance import relevance
    relevance(workdir=a.workdir, select=a.select, python_version=a.python_version, repo=str(a.repo) if a.repo else None)
    print(a.workdir / "execute" / "relevance-summary.json"); return 0


def cmd_triage(a: argparse.Namespace) -> int:
    from .stages.triage import triage
    triage(workdir=a.workdir, select=a.select); print(a.workdir / "triage" / "summary.json"); return 0


def cmd_packet(a: argparse.Namespace) -> int:
    from .stages.packet import packet
    packet(workdir=a.workdir, select=a.select); print(a.workdir / "packet" / "summary.json"); return 0


def cmd_attest(a: argparse.Namespace) -> int:
    from .stages.attest import attest
    attest(workdir=a.workdir, select=a.select); print(a.workdir / "attest" / "summary.json"); return 0


def cmd_propose(a: argparse.Namespace) -> int:
    from .stages.propose import propose
    propose(workdir=a.workdir, select=a.select, overlay_repo_path=str(a.overlay_repo) if a.overlay_repo else None,
            push=not a.no_push, open_pr=not (a.no_pr or a.no_push))
    print(a.workdir / "propose" / "summary.json"); return 0


def cmd_feedback(a: argparse.Namespace) -> int:
    from .stages.feedback import feedback
    feedback(workdir=a.workdir, select=a.select, overlay_repo_path=str(a.overlay_repo) if a.overlay_repo else None)
    print(a.workdir / "feedback" / "summary.json"); return 0


def cmd_assess(a: argparse.Namespace) -> int:
    from .stages.assess import assess
    assess(workdir=a.workdir); print(a.workdir / "assess" / "assess.md"); return 0


def cmd_run(a: argparse.Namespace) -> int:
    """Every stage in order on one change: what a trigger calls. Stops at the first failure with the
    stage named; the work directory keeps what ran. Never merges; --propose opens the test pull request."""
    from . import config
    from .stages.analyze import analyze
    from .stages.assess import assess
    from .stages.attest import attest
    from .stages.execute import execute
    from .stages.generate import generate
    from .stages.intake import intake
    from .stages.mutate import mutate
    from .stages.packet import packet
    from .stages.relevance import relevance
    from .stages.triage import triage
    a.ecosystem, a.manifest = _ecosystem_and_manifest(a.ecosystem, a.manifest)
    a.python_version = a.python_version or config.get("target", "python_version", None, None)
    repo = config.target_repo(str(a.repo) if a.repo else None, a.workdir)
    a.repo = repo
    _record_run(a.workdir, a)
    steps = [("intake", lambda: intake(repo=repo, head=a.head, base=a.base, manifest=a.manifest, workdir=a.workdir, ecosystem=a.ecosystem, python_version=a.python_version)),
             ("analyze", lambda: analyze(workdir=a.workdir, select=a.select, all_rows=False, python_version=a.python_version, repo=None, target=a.target)),
             ("generate", lambda: generate(workdir=a.workdir, select=a.select, categories=a.categories, python_version=a.python_version or "3.12", mode=a.mode)),
             ("execute", lambda: execute(workdir=a.workdir, select=a.select, python_version=a.python_version or "3.12")),
             ("mutate", lambda: mutate(workdir=a.workdir, select=a.select, python_version=a.python_version or "3.12")),
             ("relevance", lambda: relevance(workdir=a.workdir, select=a.select, repo=None, python_version=a.python_version or "3.12")),
             ("triage", lambda: triage(workdir=a.workdir, select=a.select)),
             ("packet", lambda: packet(workdir=a.workdir, select=a.select)),
             ("attest", lambda: attest(workdir=a.workdir, select=a.select)),
             ("assess", lambda: assess(workdir=a.workdir))]
    for name, step in steps:
        log(f"== {name}")
        step()
        from . import runindex, story
        story.write(a.workdir, read_json(runindex.update(a.workdir)))
    if a.propose:
        from .stages.propose import propose
        propose(workdir=a.workdir, select=a.select, overlay_repo_path=a.overlay_repo, push=True, open_pr=True)
    print(a.workdir / "README.md")
    return 0


def cmd_evaluate(a: argparse.Namespace) -> int:
    from .stages.evaluate import evaluate
    rec = evaluate([Path(r) for r in a.runs], a.out)
    print(a.out / "evaluation.md"); print(f"{len(rec['aggregate'])} line(s) from {len(rec['rows'])} package run(s)"); return 0


def cmd_bench(a: argparse.Namespace) -> int:
    from .stages.bench import bench
    out = bench(base=a.workdir, prompt_sets=a.prompt_sets, select=a.select, categories=a.categories, mode=a.mode, python_version=a.python_version)
    print(out / "evaluation.md"); return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="harness", description="AI Test Harness: opinionated implementation of the blueprint")
    p.add_argument("--version", action="version", version=f"harness {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("selfcheck", help="stage 0: run every failure-register self-check plus the sandbox and model probes")
    s.add_argument("--workdir", type=Path, default=None)
    s.add_argument("--python-version", default="3.12")
    s.add_argument("--no-probes", action="store_true", help="register checks only; skip the sandbox and model probes")
    s.add_argument("--sandbox-only", action="store_true", help="only the sandbox probe, run from inside the execute pod")
    s.set_defaults(func=cmd_selfcheck)

    s = sub.add_parser("intake", help="stage 1: resolve graphs at base and head, diff, pre-flight, work list")
    s.add_argument("--repo", default=None, help="target repository: a path on this machine or a git URL (https, ssh, file); default [target].repo in harness.local.toml")
    s.add_argument("--head", default="HEAD", help="ref of the incoming change (default HEAD)")
    s.add_argument("--base", default=None, help="ref of the last known-good state; omit for a rescan of --head")
    s.add_argument("--manifest", default=None, help="dependency manifest path inside the repo (default from config: requirements.txt)")
    s.add_argument("--ecosystem", default=None, choices=["python", "go"], help="default from config: [target].ecosystem, else python")
    s.add_argument("--python-version", default=None, help="resolve for this interpreter version, e.g. 3.12")
    s.add_argument("--workdir", type=Path, required=True)
    s.set_defaults(func=cmd_intake)

    s = sub.add_parser("analyze", help="stage 2: facts, API diff, call sites, vulnerabilities, risk score")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--repo", default=None, help="the target repository, path or URL (must be the one intake ran on; default: the clone intake made, else config)")
    s.add_argument("--select", nargs="*", default=None, help="only these packages")
    s.add_argument("--all", action="store_true", help="analyze unchanged rows too")
    s.add_argument("--target", default="dependencies", choices=["dependencies", "first-party", "all"],
                   help="what to test: the dependency graph (default), the repository's own code, or both")
    s.add_argument("--python-version", default=None)
    s.set_defaults(func=cmd_analyze)

    s = sub.add_parser("generate", help="stage 3: model writes tests per fact bundle; compile, baseline run, repair")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--select", nargs="*", default=None, help="only these packages")
    s.add_argument("--categories", nargs="*", default=None, choices=["unit", "functional", "negative", "cve"])
    s.add_argument("--mode", default="fixed", choices=["fixed", "agent"], help="fixed: one-shot prompt with repair loop; agent: tool-using loop for CVE tests")
    s.add_argument("--python-version", default="3.12")
    s.set_defaults(func=cmd_generate)

    s = sub.add_parser("execute", help="stage 4: run candidates in the sandbox on head, re-run for flakes, differential on old")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--select", nargs="*", default=None)
    s.add_argument("--python-version", default="3.12")
    s.set_defaults(func=cmd_execute)

    s = sub.add_parser("mutate", help="stage 4 step 5: mutation testing of the passing tests on coverage-scoped mutants")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--select", nargs="*", default=None)
    s.add_argument("--python-version", default="3.12")
    s.add_argument("--sample", type=int, default=25)
    s.set_defaults(func=cmd_mutate)

    s = sub.add_parser("relevance", help="stage 4 step 7: which existing tests this change makes obsolete or redundant; proposals only")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--repo", default=None, help="the target repository, path or URL (must be the one intake ran on; default: the clone intake made, else config)")
    s.add_argument("--select", nargs="*", default=None)
    s.add_argument("--python-version", default="3.12")
    s.set_defaults(func=cmd_relevance)

    for name, fn, help_ in (("triage", cmd_triage, "stage 5: classify every verdict and finding with confidence and routing"),
                            ("packet", cmd_packet, "stage 6: review packet, tests as an overlay patch, draft OpenVEX"),
                            ("attest", cmd_attest, "provenance records, in-toto test-result statement, signed DSSE envelope"),
                            ("assess", cmd_assess, "post-analysis: the run against the blueprint's core goals")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--workdir", type=Path, required=True)
        if name != "assess":
            s.add_argument("--select", nargs="*", default=None)
        s.set_defaults(func=fn)

    s = sub.add_parser("run", help="every stage on one change, in order: what a pull request trigger, a schedule or a person calls")
    s.add_argument("--repo", default=None, help="the target repository: a path or a git URL; default [target].repo")
    s.add_argument("--head", default="HEAD", help="the change: a branch, a tag, a commit, or a full ref such as refs/pull/123/head")
    s.add_argument("--base", default=None, help="the last known-good ref (the pull request's base branch); omit for a rescan of --head")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--ecosystem", default=None, choices=["python", "go"])
    s.add_argument("--manifest", default=None)
    s.add_argument("--python-version", default=None)
    s.add_argument("--target", default="dependencies", choices=["dependencies", "first-party", "all"])
    s.add_argument("--select", nargs="*", default=None, help="only these packages; default every changed or vulnerable row")
    s.add_argument("--categories", nargs="*", default=None, choices=["unit", "functional", "negative", "cve"])
    s.add_argument("--mode", default="agent", choices=["fixed", "agent"])
    s.add_argument("--propose", action="store_true", help="afterwards, open the test pull request on the overlay repository ([propose].repo)")
    s.add_argument("--overlay-repo", default=None)
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("evaluate", help="stage 7: fitness for purpose, measured: prompt sets and models scored on finished runs by sandbox verdicts and reviewer decisions")
    s.add_argument("--runs", nargs="+", required=True, help="finished run directories")
    s.add_argument("--out", type=Path, required=True, help="where evaluation.json and evaluation.md go")
    s.set_defaults(func=cmd_evaluate)

    s = sub.add_parser("bench", help="stage 7: the same job under several prompt sets, one variable at a time, then evaluate")
    s.add_argument("--workdir", type=Path, required=True, help="a run that has finished intake and analyze; each prompt set gets a sibling directory")
    s.add_argument("--prompt-sets", nargs="+", required=True, help="names in harness/prompts/ or paths; v1 is the code's own texts")
    s.add_argument("--select", nargs="*", default=None)
    s.add_argument("--categories", nargs="*", default=None)
    s.add_argument("--mode", default="agent", choices=["fixed", "agent"])
    s.add_argument("--python-version", default=None)
    s.set_defaults(func=cmd_bench)

    s = sub.add_parser("propose", help="lifecycle B: the accepted tests, packet and records as a pull request on the overlay repository; never the default branch")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--select", nargs="*", default=None)
    s.add_argument("--overlay-repo", type=Path, default=None, help="local checkout of the test overlay repository (default: [propose].repo)")
    s.add_argument("--no-push", action="store_true", help="build the branch locally only; nothing leaves this machine")
    s.add_argument("--no-pr", action="store_true", help="push the branch but do not open the pull request")
    s.set_defaults(func=cmd_propose)

    s = sub.add_parser("feedback", help="stage 7: read the test pull request's decision back; accepted candidates become realized records")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--select", nargs="*", default=None)
    s.add_argument("--overlay-repo", type=Path, default=None, help="local checkout of the test overlay repository (default: [propose].repo)")
    s.set_defaults(func=cmd_feedback)

    a = p.parse_args(argv)
    try:
        rc = a.func(a)
        if getattr(a, "workdir", None) and Path(a.workdir).is_dir():
            from . import runindex, story
            if getattr(a, "workdir", None) and (Path(a.workdir) / "intake").exists() and a.func is not cmd_bench:
                idx = runindex.update(Path(a.workdir))   # every stage leaves the run's index and its story current
                story.write(Path(a.workdir), read_json(idx))
        return rc
    except HarnessError as e:
        log(f"error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
