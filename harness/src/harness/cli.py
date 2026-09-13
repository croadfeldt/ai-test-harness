"""Command line entry point. One subcommand per stage, each reading and writing the work directory."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .util import HarnessError, log, now_iso, tool_version, write_json


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
        "command": [Path(a).name if "/" in a else a for a in sys.argv[1:]],
        "tools": {"python": sys.version.split()[0], "pip": tool_version([sys.executable, "-m", "pip", "--version"]),
                  "git": tool_version(["git", "--version"])},
        "args": {k: public(k, v) for k, v in vars(args).items() if k != "func"},
    })


def cmd_intake(a: argparse.Namespace) -> int:
    from . import config
    from .stages.intake import intake
    repo = config.target_repo(str(a.repo) if a.repo else None)
    a.repo = repo
    a.manifest = a.manifest or config.get("target", "manifest", None, "requirements.txt")
    a.python_version = a.python_version or config.get("target", "python_version", None, None)
    _record_run(a.workdir, a)
    wl = intake(repo=repo, head=a.head, base=a.base, manifest=a.manifest, workdir=a.workdir,
                ecosystem=a.ecosystem, python_version=a.python_version)
    print(a.workdir / "intake" / "worklist.json")
    return 0


def cmd_analyze(a: argparse.Namespace) -> int:
    from .stages.analyze import analyze
    analyze(workdir=a.workdir, select=a.select, all_rows=a.all, python_version=a.python_version)
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


def cmd_triage(a: argparse.Namespace) -> int:
    from .stages.triage import triage
    triage(workdir=a.workdir, select=a.select); print(a.workdir / "triage" / "summary.json"); return 0


def cmd_packet(a: argparse.Namespace) -> int:
    from .stages.packet import packet
    packet(workdir=a.workdir, select=a.select); print(a.workdir / "packet" / "summary.json"); return 0


def cmd_attest(a: argparse.Namespace) -> int:
    from .stages.attest import attest
    attest(workdir=a.workdir, select=a.select); print(a.workdir / "attest" / "summary.json"); return 0


def cmd_assess(a: argparse.Namespace) -> int:
    from .stages.assess import assess
    assess(workdir=a.workdir); print(a.workdir / "assess" / "assess.md"); return 0


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
    s.add_argument("--repo", type=Path, default=None, help="target repository on this machine (default: [target].repo in harness.local.toml)")
    s.add_argument("--head", default="HEAD", help="ref of the incoming change (default HEAD)")
    s.add_argument("--base", default=None, help="ref of the last known-good state; omit for a rescan of --head")
    s.add_argument("--manifest", default=None, help="dependency manifest path inside the repo (default from config: requirements.txt)")
    s.add_argument("--ecosystem", default="python", choices=["python"])
    s.add_argument("--python-version", default=None, help="resolve for this interpreter version, e.g. 3.12")
    s.add_argument("--workdir", type=Path, required=True)
    s.set_defaults(func=cmd_intake)

    s = sub.add_parser("analyze", help="stage 2: facts, API diff, call sites, vulnerabilities, risk score")
    s.add_argument("--workdir", type=Path, required=True)
    s.add_argument("--select", nargs="*", default=None, help="only these packages")
    s.add_argument("--all", action="store_true", help="analyze unchanged rows too")
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

    for name, fn, help_ in (("triage", cmd_triage, "stage 5: classify every verdict and finding with confidence and routing"),
                            ("packet", cmd_packet, "stage 6: review packet, tests as an overlay patch, draft OpenVEX"),
                            ("attest", cmd_attest, "provenance records, in-toto test-result statement, signed DSSE envelope"),
                            ("assess", cmd_assess, "post-analysis: the run against the blueprint's core goals")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--workdir", type=Path, required=True)
        if name != "assess":
            s.add_argument("--select", nargs="*", default=None)
        s.set_defaults(func=fn)

    a = p.parse_args(argv)
    try:
        return a.func(a)
    except HarnessError as e:
        log(f"error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
