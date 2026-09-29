"""The pipeline this change runs through, as facts: what the repository's own CI does with untrusted
code while tests run. Read from the workflow files at head, never from the platform. Each fact names
a rule, the file, what was found, and the change that would correct it; triage turns them into
findings for the pipeline's owners. The harness never edits a pipeline.

Rules (question 2 of the mission: can untrusted code reach secrets or the network while tests run):
  P-01 GitHub: pull_request_target with a checkout of the pull request's head
  P-02 GitHub: write permissions on a workflow that pull requests trigger
  P-03 GitHub: an action resolved by a mutable tag instead of a commit
  P-04 any:    a download piped to a shell
  P-05 GitHub: a job that runs the tests with repository secrets in its environment
  P-06 GitLab: a job image by a floating tag
  P-07 Tekton: a privileged step, host networking, or a step image by tag
  P-08 GitHub: a pull request job on a self-hosted runner
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

SHA = re.compile(r"@[0-9a-f]{40}$")
PIPE_TO_SHELL = re.compile(r"\b(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(ba)?sh\b")
TEST_STEP = re.compile(r"\b(pytest|go test|npm test|yarn test|make test|tox|cargo test|mvn (test|verify)|gradle(w)? test)\b")


def _fact(rule: str, file: str, found: str, change: str, severity: str = "advisory", where: str | None = None) -> dict:
    return {"rule": rule, "file": file, "where": where, "found": found, "suggested_change": change, "severity": severity}


def _load(path: Path):
    try:
        return yaml.safe_load(path.read_text(errors="replace"))
    except Exception:
        return None


def _github(path: Path, rel: str) -> list[dict]:
    doc = _load(path)
    facts: list[dict] = []
    if not isinstance(doc, dict):
        return facts
    on = doc.get("on", doc.get(True))   # YAML 1.1 reads a bare `on:` key as True
    triggers = set(on.keys()) if isinstance(on, dict) else set(on if isinstance(on, list) else [on] if on else [])
    text = path.read_text(errors="replace")
    pr_triggered = bool(triggers & {"pull_request", "pull_request_target"})
    if "pull_request_target" in triggers and re.search(r"github\.event\.pull_request\.head\.(sha|ref)", text):
        facts.append(_fact("P-01", rel, "pull_request_target checks out the pull request's own commit, so a contributor's code runs with this repository's secrets",
                           "use pull_request for anything that runs the contributor's code, and keep pull_request_target to steps that never check it out", "security"))
    perms = doc.get("permissions")
    writes = []
    if perms == "write-all":
        writes = ["write-all"]
    elif isinstance(perms, dict):
        writes = [f"{k}: write" for k, v in perms.items() if v == "write" and k in ("contents", "id-token", "packages", "actions", "deployments")]
    if pr_triggered and writes:
        facts.append(_fact("P-02", rel, f"a pull request can trigger this workflow and it holds {', '.join(writes)}",
                           "give pull request workflows read permissions and put writes in a separate workflow on the base branch", "security"))
    for job_name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        runs_on = str(job.get("runs-on", ""))
        if pr_triggered and "self-hosted" in runs_on:
            facts.append(_fact("P-08", rel, f"job {job_name} runs pull request code on a self-hosted runner ({runs_on})",
                               "run pull request jobs on hosted runners, or isolate the self-hosted runner from internal networks", "security", job_name))
        unpinned, has_test, secrets = [], False, set()
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if uses and not uses.startswith("./") and not SHA.search(uses) and not uses.startswith("docker://"):
                unpinned.append(uses)
            run = str(step.get("run") or "")
            if PIPE_TO_SHELL.search(run):
                facts.append(_fact("P-04", rel, f"job {job_name} installs by piping a download to a shell: {PIPE_TO_SHELL.search(run).group(0)[:80]}",
                                   "install from a pinned package or a checksummed download", "security", job_name))
            if TEST_STEP.search(run) or TEST_STEP.search(str(step.get("name") or "")):
                has_test = True
            for blob in (step.get("env") or {}, step.get("with") or {}):
                secrets |= set(re.findall(r"secrets\.([A-Za-z0-9_]+)", str(blob)))
        secrets |= set(re.findall(r"secrets\.([A-Za-z0-9_]+)", str(job.get("env") or "")))
        if unpinned:
            facts.append(_fact("P-03", rel, f"job {job_name} resolves {len(unpinned)} action(s) by mutable tag: {', '.join(unpinned[:4])}",
                               "pin each action to a commit SHA (owner/repo@<sha> # vN) and let a bot bump it", "advisory", job_name))
        if has_test and secrets:
            facts.append(_fact("P-05", rel, f"job {job_name} runs the tests with {len(secrets)} repository secret(s) in its environment ({', '.join(sorted(secrets)[:4])}) and network access",
                               "run the tests in a job with no secrets and no network, as the harness does; give secrets only to steps that publish", "security", job_name))
    return facts


def _gitlab(path: Path, rel: str) -> list[dict]:
    doc = _load(path)
    facts: list[dict] = []
    if not isinstance(doc, dict):
        return facts
    for job_name, job in doc.items():
        if not isinstance(job, dict) or job_name.startswith(".") or job_name in ("stages", "variables", "default", "include", "workflow"):
            continue
        image = job.get("image")
        image = image.get("name") if isinstance(image, dict) else image
        if isinstance(image, str) and ("@sha256:" not in image) and (":" not in image.rsplit("/", 1)[-1] or image.endswith(":latest")):
            facts.append(_fact("P-06", rel, f"job {job_name} runs on image {image}, a floating tag",
                               "pin the image by digest (@sha256:...)", "advisory", job_name))
        for line in [*(job.get("script") or []), *(job.get("before_script") or [])]:
            if isinstance(line, str) and PIPE_TO_SHELL.search(line):
                facts.append(_fact("P-04", rel, f"job {job_name} installs by piping a download to a shell: {PIPE_TO_SHELL.search(line).group(0)[:80]}",
                                   "install from a pinned package or a checksummed download", "security", job_name))
    return facts


def _tekton(path: Path, rel: str) -> list[dict]:
    facts: list[dict] = []
    text = path.read_text(errors="replace")
    try:
        docs = [d for d in yaml.safe_load_all(text) if isinstance(d, dict)]
    except Exception:
        return facts
    for d in docs:
        kind = d.get("kind")
        if kind not in ("Task", "Pipeline", "PipelineRun", "TaskRun", "ClusterTask"):
            continue
        name = (d.get("metadata") or {}).get("name", "?")
        blob = str(d)
        if "'privileged': True" in blob:
            facts.append(_fact("P-07", rel, f"{kind} {name} has a privileged step", "drop privileged; a sealed run needs no capabilities", "security", name))
        if "'hostNetwork': True" in blob:
            facts.append(_fact("P-07", rel, f"{kind} {name} uses host networking", "remove hostNetwork; tests should run with no network", "security", name))
        for img in re.findall(r"'image': '([^']+)'", blob):
            if "@sha256:" not in img and not img.startswith("$("):
                facts.append(_fact("P-07", rel, f"{kind} {name} runs a step image by tag: {img}", "reference step images by digest", "advisory", name))
    return facts


def inspect(repo: Path) -> dict:
    """Every CI definition the repository carries at the checked-out commit, and the facts about it."""
    systems, files, facts = [], [], []
    gh = sorted((repo / ".github" / "workflows").glob("*.y*ml")) if (repo / ".github" / "workflows").is_dir() else []
    if gh:
        systems.append("github-actions")
    for p in gh:
        rel = str(p.relative_to(repo)); files.append(rel); facts += _github(p, rel)
    gl = repo / ".gitlab-ci.yml"
    if gl.exists():
        systems.append("gitlab-ci"); files.append(".gitlab-ci.yml"); facts += _gitlab(gl, ".gitlab-ci.yml")
    tk = [p for d in (".tekton", "tekton", "deploy/tekton") if (repo / d).is_dir() for p in sorted((repo / d).rglob("*.y*ml"))]
    if tk:
        systems.append("tekton")
    for p in tk:
        rel = str(p.relative_to(repo)); files.append(rel); facts += _tekton(p, rel)
    return {"systems": systems, "files": files, "facts": facts,
            "note": "read from the repository's CI definitions at the reviewed commit; nothing here was changed by the harness" if files
                    else "no CI definition found at the reviewed commit; tests may not run on this repository's changes at all"}
