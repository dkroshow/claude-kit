# Spec: Claude Code Session Resolver

**Status:** Approved
**Created:** 2026-03-08
**Complexity:** MEDIUM

---

## TL;DR

Build a general-purpose session resolver that accurately maps an execution context (tmux pane, Claude tool call, explicit PID) to the correct Claude Code session UUID. The current gauge uses "newest JSONL by mtime" which fails when multiple Claude sessions run in the same project. The resolver uses process-level signals (lsof anchor UUIDs, tmux pane mapping, PPID walking) to disambiguate.

---

## Business Goals

### Why This Matters

Multiple Claude sessions in the same project (common with tmux) all report the same session's metrics because the gauge picks the newest JSONL by mtime. The session resolver provides accurate per-session identification, which is a prerequisite for the meta-agent and real-time monitoring UI.

### Success Criteria

- [ ] SC-1: Given multiple Claude sessions in the same project, each session is resolved to its own unique JSONL transcript
- [ ] SC-2: The resolver works from inside Claude tool calls (PPID walk) and from external scripts (tmux pane / explicit PID)
- [ ] SC-3: The gauge uses the resolver and shows correct per-session metrics

### Priority

Prerequisite for meta-agent session management. Direct enhancement to context-gauge.

---

## Problem Statement

### Current State

`gauge.py` identifies sessions by picking the newest JSONL file by mtime in the project directory. All concurrent sessions in the same project report the same session's metrics.

### Desired Outcome

Each execution context (tmux pane, tool call, explicit PID) resolves to the correct Claude Code session UUID and JSONL transcript.

---

## Scope

### In Scope

- Session resolver module (`session.py`) with PID detection, process context extraction, and session resolution
- CLI interface for manual use and debugging
- Integration into gauge.py (replace `find_current_transcript` / `find_all_transcripts`)
- JSON output for machine consumption

### Out of Scope

- Modifications to Claude Code itself
- Real-time monitoring daemon (consumer responsibility)
- Database integration
- Non-macOS support (lsof/ps behavior differences)

---

## Requirements

### Functional Requirements

1. **FR-1**: Find Claude PID from: explicit PID, tmux pane, TMUX_PANE env var, or PPID walk
2. **FR-2**: Extract process context (CWD, anchor UUID, project slug, TTY) from Claude PID via lsof/ps
3. **FR-3**: Resolve session by filtering JSONL candidates using sibling anchor exclusion, then ranking by mtime
4. **FR-4**: Fall back gracefully: history.jsonl → newest JSONL by mtime
5. **FR-5**: Resolve all active sessions across tmux panes
6. **FR-6**: CLI with --pane, --pid, --all, --json flags

### Non-Functional Requirements

- All subprocess calls timeout after 5 seconds
- No caching — always reflects current state
- Graceful degradation when tmux/lsof unavailable
- No new dependencies beyond Python stdlib

---

## Acceptance Criteria

- [ ] **AC-1** (FR-1): `python3 session.py` from inside a Claude tool call finds the correct Claude PID via PPID walk
- [ ] **AC-2** (FR-2): Process context includes correct CWD and anchor UUID
- [ ] **AC-3** (FR-3): With multiple sessions in the same project, each resolves to its own transcript
- [ ] **AC-4** (FR-4): When lsof/PID detection fails, falls back to history.jsonl then newest-by-mtime
- [ ] **AC-5** (FR-5): `--all` shows distinct sessions per tmux pane
- [ ] **AC-6** (FR-6): `--json` outputs valid JSON; `--pane` and `--pid` work correctly
- [ ] **AC-7**: `gauge.py` uses the resolver and produces correct per-session metrics

---

## Related Artifacts

- **Research source:** `.claude/plans/purring-rolling-rainbow.md`
- **Plan:** `.project/active/session-resolver/plan.md`
- **Depends on:** `conversation-logger/clogs/gauge.py`
