# claude-kit

Default Claude Code is a wonderful tool but isn't perfect, especially as work gets more complex. This is a toolkit to make it better. Structured development workflows, cross-session memory, and autonomous execution modes.

## Quick Start

```bash
# Install globally
git clone https://github.com/dkroshow/claude-kit.git ~/claude-kit
cd ~/claude-kit
./setup.sh

# Or initialize any project
cd your-project
~/claude-kit/init.sh
```

`setup.sh` creates symlinks from `~/.claude/` to the repo's commands, agents, rules, skills, and hooks. If you previously used `agentic-project-init`, it automatically detects and replaces that installation.

`init.sh` copies the project template to `.project/`, creating the directory structure for specs, plans, backlog, and learnings.

## Methodology

Claude Code out of the box tends to dive straight into code. That works for small fixes, but as tasks grow in complexity — touching multiple files, requiring architectural decisions, spanning multiple sessions — you start losing context, repeating mistakes, and getting inconsistent results.

claude-kit addresses this with three ideas:

**1. A full development lifecycle.** Claude Code's built-in plan mode is imperfect, as it doesn't reliably persist across sessions, there's no requirements step, and no audit. Instead, `/_cycle` covers the full loop — requirements with acceptance criteria, phased implementation with quality gates after each phase, and a final audit that maps every requirement to implemented code. It scales to the task: skip the ceremony for one-file fixes, get full rigor for complex features.

**2. Persistent memory across sessions.** Claude Code sessions are ephemeral — when context compresses or you start fresh, discoveries are lost. `/_wrapup` captures structured learnings (gotchas, patterns, environment facts) that future sessions automatically retrieve. You stop re-debugging the same issues.

**3. Autonomous execution with guardrails.** `/_cycle --ralph` runs the full pipeline end-to-end, replacing human checkpoints with agent-driven validation — scope verification, design review, test enforcement, and requirement mapping. It stops only when something actually needs your attention.

Supporting this is `/_research` for deep codebase exploration before committing to a design.

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
| `/_quality` | Run full quality standard on demand | Fixes + report |

### Flags

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

## Autonomous Mode

### `--ralph`

Autonomous with agent-driven validation:
- Explore agent validates scope assessment
- Validation agents check risky design decisions
- Tests must pass before phase advances (backpressure)
- Agents verify requirement-to-code mapping and test adequacy

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
