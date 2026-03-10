# Spec: search.py Enhancements — Messages & CWD Auto-Detection

**Status:** Draft
**Created:** 2026-03-10
**Complexity:** LOW

---

## TL;DR

Claude sessions frequently need to read other sessions' transcripts, but `search.py session` only shows metadata and `search.py recent` requires knowing the project slug. Two additions: (1) `--messages` flag to dump conversation content from a session, and (2) CWD auto-detection on `recent` so it infers the project from the current directory.

---

## Business Goals

### Why This Matters
Claude sessions analyzing prior sessions (wrapup, research, debugging) currently must know the JSONL file path convention and read raw files. This adds friction and couples consumers to Claude Code's internal file layout. A proper CLI interface decouples retrieval from storage format.

### Success Criteria
- [ ] A Claude session can read another session's conversation via a single CLI command
- [ ] `search.py recent` in a project directory shows that project's sessions without `--project`

---

## Problem Statement

### Current State
- `search.py session <uuid>` shows metadata only (turns, tokens, timestamps) — no message content
- `search.py recent` requires `--project <slug>` to filter by project; the slug is the CWD with `/` replaced by `-`, which callers must construct manually

### Desired Outcome
- `search.py session <uuid> --messages` dumps user + assistant messages in readable format
- `search.py recent` (no flags) auto-detects the project from CWD

---

## Scope

### In Scope
1. `--messages` flag on `session` subcommand
2. `--verbose` modifier to include tool results in message output
3. CWD auto-detection for `recent` when `--project` is not specified

### Out of Scope
- New subcommands (e.g., `last`)
- JSON output mode
- Schema changes
- Changes to other CLIs (gauge.py, session.py)

### Edge Cases & Considerations
- Sessions with hundreds of messages — need a `--limit` on messages
- CWD might not be a git repo or project directory — fallback to no filter
- Tool result content can be very large — skip by default, include with `--verbose`

---

## Requirements

### Functional Requirements

1. **FR-1**: `session <uuid> --messages` displays user and assistant messages ordered by timestamp, with role labels and timestamps
2. **FR-2**: Tool results and tool calls are excluded from `--messages` output by default
3. **FR-3**: `session <uuid> --messages --verbose` includes tool results
4. **FR-4**: [INFERRED] `--messages` supports `--limit N` to cap output (default: all messages)
5. **FR-5**: `recent` with no `--project` flag auto-detects project slug from CWD
6. **FR-6**: [INFERRED] Explicit `--project` flag overrides CWD auto-detection

---

## Acceptance Criteria

### Core Functionality
- [ ] **AC-1** (FR-1): **Given** a valid session UUID, **when** `search.py session <uuid> --messages` is run, **then** user and assistant messages are displayed with role, timestamp, and content
- [ ] **AC-2** (FR-2): **Given** a session with tool calls, **when** `--messages` is run without `--verbose`, **then** tool results are not shown
- [ ] **AC-3** (FR-3): **Given** a session with tool calls, **when** `--messages --verbose` is run, **then** tool results are included in output
- [ ] **AC-4** (FR-5): **Given** CWD is `/Users/kd/claude-kit`, **when** `search.py recent` is run without `--project`, **then** results are filtered to project slug `-Users-kd-claude-kit`
- [ ] **AC-5** (FR-6): **Given** `--project` is explicitly provided, **when** `search.py recent --project foo` is run, **then** the explicit value is used regardless of CWD

### Quality & Integration
- [ ] Existing CLI subcommands and library functions remain unchanged
- [ ] No new dependencies

---

## Related Artifacts

- **Prior spec:** `.project/active/conversation-search/spec.md` (original CLI build)
- **Plan:** `.project/active/search-enhancements/plan.md` (to be created)

---

**Next Steps:** Proceed to plan.
