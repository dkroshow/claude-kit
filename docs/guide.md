# Building Production Codebases with Claude Code

A practical guide for developers who want to ship professional-grade software with Claude Code, not just vibe code.

## Who This Is For

You're a developer using Claude Code and you've noticed the gap: the model is excellent at writing code, but your multi-day features still fall apart. Context gets lost between sessions. Requirements drift without anyone noticing. The AI builds the wrong thing because it forgot what you agreed on yesterday.

claude-kit fixes the persistence problem. It gives Claude Code a structured workspace where specs, plans, and session context survive across sessions and compactions. Everything else -- the code generation, the debugging, the refactoring -- the model handles natively.

---

## What Vanilla Claude Code Gets Wrong

Claude Code ships with real capabilities: extended thinking, sub-agents, auto-memory, plan mode, CLAUDE.md, and rules. For single-session tasks, it's genuinely good. The problems start when work spans multiple sessions.

**Sessions are ephemeral.** When context compacts or you start a new conversation, the model loses the thread. It doesn't know what you decided yesterday, what phase of implementation you're in, or which requirements you've already verified. Auto-memory helps, but it captures fragments -- not the structured state needed to resume complex work.

**Without artifacts, requirements drift.** When the spec lives only in chat history, nobody can audit whether the implementation actually satisfies it. Code review becomes "looks good to me" instead of "FR-1 maps to `handler.py:45`, VERIFIED." You can't trace a requirement to its implementation because the requirement was never written down.

**Better models don't fix discipline problems.** Each new Claude release is dramatically better at code generation. But "better at coding" doesn't help when the model doesn't know where you left off, what you agreed to build, or what's already been tested. Persistence and structure are process problems, not intelligence problems.

---

## The 10 Commands

claude-kit ships 10 commands organized into four groups: the build pipeline, session continuity, project management, and quality.

### The Build Pipeline

The core cycle is **spec -> plan -> implement -> audit**. `/_cycle` is the recommended entry point -- it assesses your task, recommends the right level of process, and runs through the appropriate phases. The individual commands (`/_spec`, `/_plan`, `/_implement`, `/_audit`) can also be invoked standalone when you want manual control.

#### `/_cycle` -- The Recommended Entry Point

**Creates:** `spec.md`, `plan.md`, code changes (varies by tier)

The cycle command is the orchestrator. You describe what you want to build, and it assesses the task complexity, recommends a tier, and runs the appropriate phases -- stopping only at natural interaction points (scope approval, design decisions, plan approval, significant deviations).

**Three tiers:**
- **Quick** (1-2 files, clear change) -- Implements directly, then audits. No spec or plan files created.
- **Standard** (2-5 files, moderate complexity) -- Spec -> Plan -> Implement -> Audit. The full pipeline, streamlined.
- **Complex** (5+ files, architectural impact) -- Same phases as Standard but with more research cycles, deeper analysis, and more user checkpoints throughout.

**Flags:**
- `--ralph` -- Autonomous with agent-driven validation. Spawns validation agents at key checkpoints: scope validation (Phase 0), design review (Phase 2), test enforcement (Phase 3), and requirement mapping (Phase 4).

**When to use:** Any non-trivial task. This is the default entry point.

**When to skip:** Bug fixes with clear root cause (just fix it), or when you specifically want to run individual pipeline commands for fine-grained control.

#### `/_spec` -- Define Requirements

**Creates:** `.project/active/{feature-name}/spec.md`

The spec command captures *what* you're building and *why*. It walks you through scoping, asks clarifying questions, distinguishes your stated requirements from inferences, and produces a document with business goals, functional requirements, acceptance criteria in given/when/then format, and scope boundaries.

**When to use:** Any feature that touches multiple files or has ambiguous requirements. The spec becomes the contract that implementation audits against. Also used standalone when `/_cycle` handles requirements inline but you want a more thorough, interactive requirements process.

#### `/_plan` -- Technical Design + Phased Implementation

**Creates:** `.project/active/{feature-name}/plan.md`

The plan command is a merged design+plan -- it researches the codebase, produces a technical design, and creates a phased implementation strategy in a single document. It explores existing patterns and integration points, presents alternatives when design decisions are needed, and breaks implementation into testable phases with test-first approach, specific file changes with `file:line` references, and validation steps.

The plan self-evaluates against a REFLECT checklist covering design completeness, design quality, and implementation readiness before presenting to you.

**When to use:** Any implementation that will take more than one session, or where the technical approach needs research and design. The plan is what the next session reads to know where to resume and *why* things are structured the way they are.

#### `/_implement` -- Execute the Plan

**Reads:** `plan.md`, `spec.md`
**Produces:** Code changes, updated plan with completion notes

The implement command reads the plan and spec before writing any code. It offers codebase exploration, confirms scope, then executes phase by phase -- starting with tests, validating as it goes, and checking off plan items. When something deviates from the plan, it stops and asks.

After each phase, two verification steps run automatically:
1. **Code Quality Gate** -- runs tests, linting, type checking, and formatting per your CLAUDE.md config.
2. **Per-Phase Audit** -- checks completion accuracy, deviation justification, and test coverage.

After all phases complete, it writes implementation notes directly into `plan.md`: what actually changed, issues encountered, deviations and why.

#### `/_audit` -- Final Cross-Phase Verification

The audit command performs final verification of the complete implementation. Since per-phase checks run during `/_implement` after each phase, this final audit focuses on higher-level concerns:

1. **Requirement Coverage** -- maps each FR/AC from spec.md to implemented code with `file:line` references
2. **Cross-Phase Integration** -- do the phases work together correctly?
3. **Test Adequacy** -- is overall test coverage sufficient? Any systemic gaps?

**When to use:** After implementation, before considering a feature complete.

### Session Continuity

These commands solve the persistence problem directly.

#### `/_wrapup` -- End-of-Session Context Persistence

**Updates:** `.project/CURRENT_WORK.md`, auto-memory, learnings, relevant docs

This is the single most important command in the system. Run it before closing Claude Code. It reviews what happened in the session, updates `CURRENT_WORK.md` with current status, captures key learnings to the learnings archive, updates any affected docs, and commits the changes.

The next session auto-loads MEMORY.md and is instructed (via the `context-loading` rule) to read `CURRENT_WORK.md` before starting non-trivial work.

**Learnings capture:** When you discover a gotcha, pattern, or environment quirk, `/_wrapup` asks whether it's project-specific (`.project/learnings/`) or machine-wide (`~/.claude/learnings/`). Learnings are indexed and automatically surfaced in future sessions via the memory retrieval system.

**Flags:**
- `--blurb` -- After wrapping up, generates a compact reload blurb you can copy-paste into a fresh session. Use `/_blurb` standalone if you've already wrapped up.
- `--quick` -- Just updates CURRENT_WORK.md status, skips full review.

**Cost:** 30 seconds. **Saves the next session:** 10+ minutes of re-orientation.

#### `/_blurb` -- Reload Blurb for Fresh Sessions

**Produces:** Copyable text block

Generates a compact directive for a fresh Claude session. Contains branch state, active work, key files to read, and gotchas. Designed to be pasted after `/clear` or into a new session.

### Project Management

#### `/_status` -- Status, Backlog, and Work Lifecycle

**Subcommands:**
- `/_status` -- Full status report with gap analysis and recommendations
- `/_status current` -- What's active right now
- `/_status backlog` -- Prioritized upcoming work
- `/_status history` -- Completed work log
- `/_status close [item]` -- Archive completed items to `.project/completed/`
- `/_status decompose <epic>` -- Break an epic into backlog items

Your backlog, epics, active work, and completion tracking live in `.project/` -- the same place Claude already reads from. No external tools, no context-switching.

### Quality

#### `/_research` -- Persistent Exploration

**Creates:** `.project/research/{topic}.md`

Deep codebase and topic exploration that produces a standalone document with `file:line` references, architecture insights, and recommendations. The 20-minute exploration investment pays off every time someone needs to understand that code area.

**When to use:** Before speccing a feature in an unfamiliar area. When exploration should become a document rather than ephemeral chat.

#### `/_quality` -- Automated Quality Checks

Runs all quality checks (tests, linting, formatting, type checking) per your CLAUDE.md config, categorizes issues by risk level, fixes low-risk issues directly, and documents medium/high-risk issues for your approval.

**When to use:** After implementation, before committing.

---

## The Memory System

claude-kit has a layered memory system that builds on Claude Code's native capabilities.

### Layer 1: Native Auto-Memory

Claude Code's built-in `MEMORY.md` (at `~/.claude/projects/*/memory/MEMORY.md`). Automatic, always loaded. `/_wrapup` updates it with session-level decisions and gotchas.

### Layer 2: Structured Learnings

Deliberate knowledge capture via `/_wrapup`:

- **Project learnings** at `.project/learnings/` -- project-specific gotchas, patterns, environment quirks
- **Global learnings** at `~/.claude/learnings/` -- machine-wide knowledge that applies across projects

Each learning is a markdown file with YAML frontmatter (type, tags, created date) and structured sections (What, Context, What Didn't Work, What Works, Key Files). An index file tracks all entries.

Three learning types:
- **environment** -- system/tool facts (e.g., "Python 3.9.1 on this machine, no union type syntax")
- **gotcha** -- pitfalls and failures (e.g., "`gh` is not GitHub CLI here, use curl")
- **pattern** -- reusable approaches (e.g., "PR splitting: base branch with file, then feature branch on top")

### Layer 3: Memory Retrieval

The `context-loading` rule includes a decision tree that determines when to check learnings:

1. **Trivial task?** Skip retrieval
2. **First task in session?** Scan both indexes
3. **Specific component?** Check index for tag matches
4. **Debugging?** Check for `gotcha` type entries

For deep searches (many potential matches), the memory agent (`agents/memory.md`) performs semantic retrieval across both indexes and returns a synthesized brief.

### How It Differs from Native Auto-Memory

| | Native MEMORY.md | Structured Learnings |
|---|---|---|
| **Storage** | Single file, auto-loaded | Individual files with index |
| **Capture** | Automatic by Claude | Deliberate via `/_wrapup` |
| **Structure** | Freeform | YAML frontmatter + sections |
| **Scope** | Per-project | Per-project + cross-project |
| **Retrieval** | Always loaded (200 line limit) | On-demand via decision tree |
| **Best for** | Quick reference, recent decisions | Detailed knowledge, failure analysis |

They complement each other. MEMORY.md is your quick-reference card. Learnings are your knowledge base.

---

## Autonomous Execution Mode

### `--ralph` Mode

`/_cycle --ralph` runs autonomously with agent-driven validation at key checkpoints:

| Phase | What `--ralph` adds |
|-------|-------------------|
| Phase 0 (Assess) | Spawns Explore agent to validate scope assessment |
| Phase 2 (Plan) | Design-review-refine loop: validation agents check risky REFLECT items |
| Phase 3 (Implement) | Validation backpressure: tests must pass before phase advances (2-attempt limit) |
| Phase 4 (Audit) | Spawns agents to verify requirement-to-code mapping, cross-phase integration, test adequacy |

**When to use:** When you want autonomous execution with automated reviewers replacing human gates. Stops only when agents find issues, tests fail after 2 attempts, or deviations affect spec requirements.

---

## The .project/ Directory

After initialization and use, your project develops this structure:

```
.project/
├── CURRENT_WORK.md          # What's active, recently completed, up next
├── epic_template.md          # Template for new epics
├── README.md                 # Workflow overview
│
├── active/                   # In-progress features
│   └── {feature-name}/       # One directory per feature
│       ├── spec.md           # Requirements (from /_spec or /_cycle)
│       └── plan.md           # Design + phased plan (from /_plan or /_cycle)
│
├── backlog/                  # Planned work
│   ├── BACKLOG.md            # Prioritized epic list
│   └── epic_*.md             # Individual epic definitions
│
├── completed/                # Archived features (moved from active/)
│   ├── CHANGELOG.md          # Completion log
│   └── {YYYYMMDD}_{name}/    # Archived feature directories
│
├── research/                 # Exploration documents
│   └── {topic}.md            # Research output (from /_research)
│
├── learnings/                # Project-specific knowledge
│   ├── index.md              # Learning index table
│   └── *.md                  # Individual learning files
│
└── captures/                 # Transcript captures (from hooks)
```

### Lifecycle

A feature flows through the directory structure:

1. **Backlog:** Epic defined in `backlog/epic_*.md`, listed in `BACKLOG.md`
2. **Active:** Feature directory created in `active/{feature-name}/` with spec and plan
3. **Completed:** Archived via `/_status close` to `completed/{date}_{name}/`

`CURRENT_WORK.md` tracks the live state across all of these. It's the file `/_wrapup` updates and the file the next session reads first.

---

## Workflow Decision Tree

Not every change needs the full pipeline.

**Bug fix with clear root cause?**
Just fix it. Read the code, fix the bug, run tests, done.

**Small change (1-2 files, clear requirements)?**
`/_cycle` with Quick tier -- implements directly, then audits.

**Non-trivial task (not sure how much process it needs)?**
`/_cycle` -- It assesses complexity and recommends the right tier (Quick / Standard / Complex). This is the recommended default for most work.

**Want manual control over individual phases?**
`/_spec` -> `/_plan` -> `/_implement` -> `/_audit`

**Complex feature in an unfamiliar codebase?**
`/_research` -> `/_cycle` (Complex tier)

**Resuming work from a previous session?**
Read `CURRENT_WORK.md` and the active feature's `plan.md`. Pick up where the checkboxes stop.

**End of session?**
`/_wrapup`. Every time.

---

## What Claude Code Handles Natively

Understanding what's native helps you avoid redundant work.

**Built-in plan mode** (`/plan`) creates an ephemeral implementation plan. It works for single-session tasks but disappears when the session ends. `/_plan` creates a persistent `plan.md` that survives across sessions and tracks progress with checkboxes. Use built-in plan mode for quick explorations; use `/_plan` for anything multi-session.

**Sub-agents** (Task tool with Explore, Plan, general-purpose types) handle parallel research and analysis. The commands in this repo use sub-agents internally -- `/_research` spawns Explore agents, `/_plan` uses them for codebase analysis. You don't need to manage sub-agents directly.

**Auto-memory** (`MEMORY.md`) persists distilled knowledge across sessions. It's auto-loaded every session. `/_wrapup` writes to it. claude-kit's structured learnings complement it, not replace it.

**CLAUDE.md and rules** auto-load every session. The `context-loading` rule tells Claude to read `CURRENT_WORK.md` before starting non-trivial work. This is how the boot sequence works: native auto-loading triggers a rule that reads project state.

---

## Best Practices

### Write a Good CLAUDE.md

Your project's `CLAUDE.md` is auto-loaded every session. Include:

- **Test commands** -- how to run tests, lint, type check
- **Build commands** -- how to build, run, deploy
- **Project conventions** -- naming patterns, directory structure, key abstractions

### Spec-Driven Development

The spec is your contract. Without `spec.md`, code review devolves into "looks good to me." With it, you get traceability:

> FR-1: System shall parse JSONL transcripts -> `analyzer.py:45-67`, VERIFIED
> FR-2: System shall classify tool_use events -> `classifier.py:12-89`, VERIFIED
> FR-3: System should support incremental indexing -> Not found, GAP

That traceability is what `/_audit` checks against. It's only possible because the spec exists as a persistent artifact.

### Wrap Up Every Session

`/_wrapup` takes 30 seconds. It saves the next session 10+ minutes of re-orientation. This is especially critical for multi-day features where you might not touch the code for a week.

### Use Research Docs for Future-You

When you spend 20 minutes exploring a codebase area, `/_research` turns that into a document. Next month when you need to touch that code again, you read the research instead of re-exploring from scratch.

### One Feature = One Directory

`.project/active/{feature-name}/` keeps spec and plan together. When you need to understand the full picture of a feature, it's one `ls`.

---

## Setup

### Global Installation

```bash
git clone <repo-url> ~/claude-kit
cd ~/claude-kit
./setup.sh
```

This creates symlinks from `~/.claude/` to the repo:
- `~/.claude/commands/` -> `commands/`
- `~/.claude/agents/` -> `agents/`
- `~/.claude/rules/` -> `rules/`
- `~/.claude/skills/` -> `skills/`
- `~/.claude/hooks/` -> `hooks/`

If you previously used `agentic-project-init`, `setup.sh` automatically detects and removes stale symlinks and metadata from that installation.

### Per-Project Initialization

```bash
cd your-project
~/claude-kit/init.sh
```

This copies the project template to `.project/`, creating the directory structure for specs, plans, backlog, and learnings. User data files (CURRENT_WORK.md, BACKLOG.md, etc.) are protected -- they won't be overwritten if they already exist.

### Uninstall

```bash
~/claude-kit/uninstall.sh --global    # Remove symlinks from ~/.claude/
~/claude-kit/uninstall.sh --project   # Remove .project/ from current project
~/claude-kit/uninstall.sh --all       # Both
```

---

## Quick Reference

| Command | Purpose | Artifact |
|---------|---------|----------|
| `/_cycle` | Tiered workflow orchestrator (recommended entry point) | `spec.md`, `plan.md`, code |
| `/_spec` | Define requirements and acceptance criteria | `spec.md` |
| `/_plan` | Technical design + phased implementation planning | `plan.md` |
| `/_implement` | Execute plan with per-phase validation | Code + updated `plan.md` |
| `/_audit` | Final cross-phase verification | Structured report |
| `/_wrapup` | End-of-session context persistence | Updated `CURRENT_WORK.md`, learnings |
| `/_blurb` | Generate reload blurb for fresh session | Copyable text block |
| `/_research` | Deep codebase exploration | `.project/research/*.md` |
| `/_status` | Project management and status | `.project/` updates |
| `/_quality` | Code quality checks | Fixes + report |
