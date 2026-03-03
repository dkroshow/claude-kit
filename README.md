# claude-kit

A best-in-class Claude Code management toolkit. Structured development workflows, cross-session memory, and autonomous execution modes.

## Quick Start

```bash
# Install globally
git clone <repo-url> ~/claude-kit
cd ~/claude-kit
./setup.sh

# Initialize any project
cd your-project
~/claude-kit/init.sh
```

`setup.sh` creates symlinks from `~/.claude/` to the repo's commands, agents, rules, skills, and hooks. If you previously used `agentic-project-init`, it automatically detects and replaces that installation.

`init.sh` copies the project template to `.project/`, creating the directory structure for specs, plans, backlog, and learnings.

## Commands

### Build Pipeline

| Command | Purpose | Artifact |
|---------|---------|----------|
| `/_cycle` | Tiered workflow orchestrator (recommended entry point) | `spec.md`, `plan.md`, code |
| `/_spec` | Requirements definition with acceptance criteria | `spec.md` |
| `/_plan` | Technical design + phased implementation planning | `plan.md` |
| `/_implement` | Execute plan with per-phase validation | Code + updated `plan.md` |
| `/_audit` | Final cross-phase verification | Structured report |

### Session Continuity

| Command | Purpose | Artifact |
|---------|---------|----------|
| `/_wrapup` | Persist session context + capture learnings | `CURRENT_WORK.md`, learnings |
| `/_blurb` | Generate reload blurb for next session | Copyable text block |

### Project Management & Quality

| Command | Purpose | Artifact |
|---------|---------|----------|
| `/_status` | Status, backlog, history, close, decompose | `.project/` updates |
| `/_research` | Deep codebase exploration | `.project/research/*.md` |
| `/_quality` | Code quality checks (lint, test, format) | Fixes + report |

### Flags

- `/_cycle --yolo` — Autonomous, best-judgment defaults, no human gates
- `/_cycle --ralph` — Autonomous with agent-driven validation at every phase
- `/_wrapup --blurb` — Wrap up + generate reload blurb
- `/_wrapup --quick` — Just update CURRENT_WORK.md

## Workflow

```
Bug fix?           → Just fix it
1-2 files?         → /_cycle (Quick tier)
2-5 files?         → /_cycle (Standard tier)
5+ files?          → /_cycle (Complex tier)
Manual control?    → /_spec → /_plan → /_implement → /_audit
End of session?    → /_wrapup
```

`/_cycle` assesses your task and recommends the right tier. You can override.

## Memory System

Two complementary layers work alongside Claude Code's native auto-memory:

1. **Native auto-memory** — Claude Code's built-in MEMORY.md (automatic, always loaded)
2. **Structured learnings** — `.project/learnings/` (project) + `~/.claude/learnings/` (global)
   - Captured deliberately via `/_wrapup`
   - Three types: `environment`, `gotcha`, `pattern`
   - Retrieved automatically via context-loading rule decision tree
   - Deep search via memory agent when many matches exist

MEMORY.md is your quick-reference card. Learnings are your knowledge base. They complement, not compete.

## Autonomous Modes

### `--yolo`

Runs the full pipeline with best-judgment defaults. Presents information but doesn't wait for approval. Only stop is the final summary.

### `--ralph`

Autonomous with agent-driven validation:
- **Phase 0:** Explore agent validates scope assessment
- **Phase 2:** Validation agents check risky design decisions
- **Phase 3:** Tests must pass before phase advances (backpressure)
- **Phase 4:** Agents verify requirement-to-code mapping and test adequacy

## Repo Structure

```
claude-kit/
├── commands/          # 10 command files (symlinked to ~/.claude/commands/)
├── agents/            # Sub-agents (memory retrieval)
├── rules/             # Auto-loaded rules (context-loading, workflow accountability)
├── skills/            # Document standards (spec, plan, implement templates)
├── hooks/             # Silent infrastructure (transcript capture)
├── project-template/  # Template for .project/ (copied by init.sh)
├── docs/              # Production guide
│   └── guide.md       # Full documentation
├── setup.sh           # Global install (with agentic-project-init takeover)
├── init.sh            # Per-project init
└── uninstall.sh       # Clean removal (--global, --project, --all)
```

## Uninstall

```bash
~/claude-kit/uninstall.sh --global    # Remove symlinks from ~/.claude/
~/claude-kit/uninstall.sh --project   # Remove .project/ from current project
~/claude-kit/uninstall.sh --all       # Both
```

## Documentation

See [docs/guide.md](docs/guide.md) for the full production guide covering all commands, the memory system, autonomous modes, best practices, and setup details.

## License

MIT
