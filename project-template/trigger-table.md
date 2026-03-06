# Trigger Table

> Maps file patterns to relevant agents and knowledge artifacts.
> Consulted during context-loading when modifying files.
> Populate this per-project as you build agents and documentation.
>
> **How it works:** When you're about to modify files, check this table.
> If the files match a pattern, load the suggested agent and/or knowledge artifact
> before starting work.
>
> **Format:** File patterns use glob syntax. Use `—` for empty agent/artifact columns.

| File Pattern | Agent | Knowledge Artifact | Notes |
|---|---|---|---|
| _Example:_ `src/auth/**` | _auth-agent_ | _docs/auth-system.md_ | _Session handling, OAuth flows_ |
