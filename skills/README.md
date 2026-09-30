# Skills

Agent Skills the harness ships: packaged instructions a coding agent loads when a task matches, so the
harness is one instruction away from the developer's own assistant.

| Skill | For | What it does |
|---|---|---|
| [`ai-test-harness`](ai-test-harness/SKILL.md) | Claude Code and any agent runtime that reads the Agent Skills format | Runs the harness on the change in front of the developer, reads the story, proposes the tests through a pull request, and keeps the rules: sealed sandbox only, nothing merged, unproven stated as unproven |

Install in Claude Code by copying `ai-test-harness/` into `.claude/skills/` of a repository (or `~/.claude/skills/`
for every repository). The harness's own prompt sets (`harness/prompts/`) are skill-shaped too, named,
versioned and measured; publishing them in this format is planned once the evaluation table has ranked
more than one.
