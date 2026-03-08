# Plan: Claude Code Session Resolver

**Status:** Complete
**Created:** 2026-03-08

---

## TL;DR

New module `conversation-logger/clogs/session.py` (~200 lines) that resolves Claude Code execution contexts to session UUIDs using process-level signals. Then modify `gauge.py` to use it, removing ~60 lines of duplicated detection logic.

---

## Source Documents

- **Spec:** `.project/active/session-resolver/spec.md`
- **Research:** `.claude/plans/purring-rolling-rainbow.md`

## Key Findings from Investigation

1. No session ID env var — Claude exports only `CLAUDECODE=1`
2. lsof reveals a "process anchor" — each Claude PID has an open fd to `~/.claude/tasks/<uuid>/`
   - **UPDATE**: Only works for Claude ≤v2.1.66. Newer versions (v2.1.68+) don't keep tasks/ open.
3. tmux pane → Claude PID mapping works via `tmux list-panes` + process tree walk
   - **UPDATE**: `pgrep -P` fails silently on macOS. Use `ps -eo pid,ppid,comm | awk` instead.
4. PPID walk works inside tool calls — walk up from `os.getpid()` to find `claude` process
5. history.jsonl logs every user message with `sessionId` + `project` + `timestamp`
6. macOS stat gives nanosecond mtime precision for sub-second disambiguation
7. JSONL birth time (file creation) distinguishes sessions created by the same process

## Design Decisions

### Decision 1: Sibling anchor exclusion for multi-session disambiguation
**Context:** Multiple Claude sessions in the same project produce JSONL files in the same directory.
**Chosen:** Use lsof to find each Claude process's anchor UUID, exclude other processes' anchors from candidates.
**Rationale:** Anchors are the only process-specific signal. Combined with mtime ranking, this reliably identifies the correct session.

### Decision 2: No caching
**Context:** Could cache resolved session for performance.
**Chosen:** Always re-resolve.
**Rationale:** Sessions can change (/clear), processes can die. Resolver must reflect current state. Performance is fine (single lsof + ps call).

---

## Implementation Strategy

### Phase 1: Session Resolver Module
#### Goal
Working `session.py` with PID detection, context extraction, session resolution, and CLI.

#### Changes Required
- [x] Create `conversation-logger/clogs/session.py` with:
  - `find_claude_pid(pane, pid)` — resolution chain: explicit PID → pane → $TMUX_PANE → PPID walk
  - `get_process_context(claude_pid)` — lsof/ps extraction of CWD, anchor UUID, project slug, TTY
  - `resolve_session(pid, pane, project_dir)` — main entry point with sibling exclusion + mtime ranking + fallbacks
  - `resolve_all_sessions()` — all active sessions via tmux
  - CLI with argparse: --pane, --pid, --all, --json

#### Validation
- [x] `python3 session.py` auto-detects current session (AC-1, AC-2)
- [x] `python3 session.py --json` outputs valid JSON (AC-6)
- [x] `python3 session.py --all` lists distinct sessions (AC-5)

### Phase 2: Gauge Integration
#### Goal
Replace gauge.py's detection logic with session resolver calls.

#### Changes Required
- [x] Modify `gauge.py`: import and use `session.resolve_session` / `session.resolve_all_sessions`
- [x] Remove `find_current_transcript()` and `find_all_transcripts()` from gauge.py
- [x] Keep `extract_usage()` and `compute_metrics()` unchanged
- [x] Deduplicate sessions in `--all` mode (multiple PIDs → same session)

#### Validation
- [x] `python3 gauge.py` shows correct context % for this session (AC-7)
- [x] `python3 gauge.py --all` still works

---

## Risk Management

- **lsof unavailable**: Falls back to history.jsonl, then newest-by-mtime (graceful degradation)
- **Anchor UUID limitation**: Anchor reflects first session, not current after /clear. Mitigated by sibling exclusion (we exclude others' anchors, not match our own)
- **Newer Claude versions lack anchors**: v2.1.68+ don't keep `~/.claude/tasks/` open. Anchor exclusion only helps for older versions.

---

## Implementation Notes

### Phase 1 Completion
**Completed:** 2026-03-08
**Changes Made:**
- Created `conversation-logger/clogs/session.py` (230 lines)
- Functions: `find_claude_pid`, `get_process_context`, `resolve_session`, `resolve_all_sessions`, CLI

**Deviations from original plan:**
- `pgrep -P` doesn't work on macOS — replaced with `ps -eo pid,ppid,comm | awk` filtering
- Anchor UUIDs only present in Claude ≤v2.1.66; current v2.1.71 lacks them. Kept as optional signal.
- Added `_session_from_history()` as intermediate fallback between anchors and pure mtime

**Known Limitations:**
- Multiple Claude processes in the same project without anchors all resolve to the newest JSONL by mtime (same session). This is a fundamental upstream limitation — Claude Code doesn't expose session ID per-process in newer versions.
- Primary use case (PPID walk from inside tool call) works correctly — correctly finds the calling Claude PID and project.

### Phase 2 Completion
**Completed:** 2026-03-08
**Changes Made:**
- Removed `find_current_transcript()` and `find_all_transcripts()` from gauge.py (~60 lines)
- Replaced with `resolve_session()` and `resolve_all_sessions()` calls
- Added session deduplication in `--all` mode
- Added `time` import for age filtering
