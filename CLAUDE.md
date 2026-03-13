# claude-kit — Claude Code Management Toolkit

Structured development workflows, cross-session memory, and autonomous execution modes for Claude Code.

## What This Is

A globally-installed toolkit (`~/claude-kit/`) that provides commands, rules, hooks, skills, and agents to any Claude Code project via symlinks from `~/.claude/`.

## Cross-Project Role

claude-kit provides **CLI infrastructure** consumed by other repos via subprocess. It is NOT imported as a library.

Key CLIs exposed by `conversation-logger/clogs/`:
- `gauge.py --all --json` — context window metrics for active CC sessions
- `search.py search "query"` — full-text search across conversation history
- `session.py --all --json` — resolve active CC sessions to transcript files
- `understand.py --all --json` — structured conversation state (phase, health, context, activity, intent) for active sessions

## Setup

```bash
./setup.sh    # Symlinks commands/rules/hooks/skills/agents into ~/.claude/
./init.sh     # (Run in a project dir) Copies .project/ template
```

## Key Directories

- `commands/` — slash commands (`/_cycle`, `/_spec`, `/_plan`, etc.)
- `rules/` — global rules loaded into every session
- `hooks/` — Claude Code hooks (conversation logging)
- `skills/` — skill definitions
- `agents/` — agent definitions (memory agent, etc.)
- `conversation-logger/` — transcript ingestion, search, gauge, session resolution
