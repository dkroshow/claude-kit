# Trigger Table

> Maps file patterns to relevant agents and knowledge artifacts.
> Consulted during context-loading when modifying files.
>
> **How it works:** When you're about to modify files, check this table.
> If the files match a pattern, load the suggested agent and/or knowledge artifact
> before starting work.
>
> **Format:** File patterns use glob syntax. Use `—` for empty agent/artifact columns.

| File Pattern | Agent | Knowledge Artifact | Notes |
|---|---|---|---|
| `agents/memory.md` | — | `rules/context-loading.md` | Memory agent + context loading are tightly coupled |
| `rules/context-loading.md` | memory | `agents/memory.md` | Retrieval decision tree, references memory agent |
| `commands/_wrapup.md` | — | `skills/plan-standard.md` | Wrapup captures learnings, maintains file-knowledge map |
| `commands/_cycle.md` | — | `commands/_spec.md`, `commands/_plan.md`, `commands/_implement.md` | Orchestrates the full pipeline |
| `commands/_implement.md` | — | `skills/implement-standard.md` | Implementation quality gates |
| `commands/_spec.md` | — | `skills/spec-standard.md` | Spec template and conventions |
| `commands/_plan.md` | — | `skills/plan-standard.md` | Plan template and REFLECT checklist |
| `skills/*.md` | — | — | Standards referenced by commands — check which commands import them |
| `hooks/**` | — | — | Transcript capture infrastructure |
| `init.sh` | — | `project-template/**` | Copies templates to .project/, protects user data files |
| `setup.sh` | — | — | Creates symlinks from ~/.claude/ to repo |
| `project-template/**` | — | `init.sh` | Templates — init.sh copies these and protects some as user data |
