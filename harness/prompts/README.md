# Prompt sets

Every text the harness says to a model is under source control here, named and digested. The
defaults, set `v1`, live next to the code that uses them: each adapter's system prompt and category
tasks, and the agent's rules. A set in this directory overrides any of those parts by key and leaves
the rest alone. Every manifest records the active set's name and digest, so a result is always
traceable to the exact words that produced it.

Keys: `system.python`, `system.go`, `task.<unit|functional|negative|cve>.<python|go>`, `agent.rules`.

Select a set with `HARNESS_PROMPT_SET=<name>` or `[model].prompt_set` in `harness.local.toml`.
Compare sets on one job with `harness bench --workdir <run> --prompt-sets v1 <name>`; score any
finished runs with `harness evaluate --runs <dir>... --out <dir>`. A set that does not beat `v1` on
the evaluation table does not become the default: fitness for purpose is measured, never assumed.
