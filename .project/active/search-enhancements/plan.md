# Plan: search.py Enhancements — Messages & CWD Auto-Detection

**Status:** Complete
**Created:** 2026-03-10
**Last Updated:** 2026-03-10

---

## TL;DR

Two additive changes to `search.py`: (1) a `get_session_messages()` function + `--messages`/`--verbose` flags on the `session` subcommand to dump conversation content, and (2) CWD-to-slug auto-detection in `cmd_recent()` when `--project` is omitted. Single file change (search.py), two phases, no new dependencies.

---

## Source Documents
- **Spec:** `.project/active/search-enhancements/spec.md`

## Research Findings

### Files Analyzed
- `conversation-logger/clogs/search.py:43-59` — `session_summary()` query pattern (JOIN claude_sessions, returns dict)
- `conversation-logger/clogs/search.py:214-232` — `cmd_recent()` uses `args.project` passed to `recent_sessions()`
- `conversation-logger/clogs/search.py:235-250` — `cmd_session()` metadata-only display
- `conversation-logger/clogs/search.py:253-277` — argparse setup with subparsers
- `conversation-logger/clogs/db.py:31` — `get_connection()` returns psycopg2 connection

### Reusable Patterns
- All library functions follow: get_connection → try/cursor/execute/fetchall → finally conn.close() (`search.py:23-38`)
- CLI formatters `_fmt_timestamp()` and `_fmt_tokens()` at `search.py:174-192`
- Message table has `role`, `content`, `timestamp`, `is_tool_result` columns (from DB schema in `db.py:215-232`)

### Integration Points
- `cmd_session()` already calls `session_summary()` — messages extend this path
- `cmd_recent()` already accepts `project_slug` param — CWD detection feeds into existing parameter
- Project slug convention: `os.getcwd().replace("/", "-")` (confirmed in `session.py:172-173`, learning `20260307-context-window-compression.md`)

## Design Decisions

### Decision 1: Message filtering approach
**Context:** Need to skip tool results by default but include with `--verbose`
**Options:** (a) Filter in SQL with WHERE clause, (b) Filter in Python after fetch
**Chosen:** Filter in SQL
**Rationale:** Tool results can be very large (file contents, command output). Fetching them from DB just to discard wastes memory. SQL WHERE is simpler and more efficient.

### Decision 2: CWD detection — import vs inline
**Context:** `session.py` has `get_process_context()` which derives project_slug, but it does much more (PID walk, tmux detection)
**Options:** (a) Import and call session.py function, (b) Inline the one-liner `os.getcwd().replace("/", "-")`
**Chosen:** Inline one-liner
**Rationale:** The slug derivation is a single string operation. Importing session.py pulls in process detection machinery that's irrelevant here. If the convention ever changes, it's a one-line fix in both places.

---

## Technical Design

### Architecture Overview

No new components. Two additions to existing search.py:

```
search.py
  ├── get_session_messages()    ← NEW library function
  ├── cmd_session()             ← MODIFIED: --messages/--verbose handling
  └── cmd_recent()              ← MODIFIED: CWD auto-detection fallback
```

### Function: get_session_messages()
**Purpose:** Fetch conversation messages for a session
**Location:** `search.py` (new function, after `session_summary()`)
**Signature:** `get_session_messages(session_id: str, include_tool_results: bool = False, limit: Optional[int] = None) -> List[Dict]`
**Query:** SELECT role, content, timestamp FROM claude_messages WHERE session_id = (subquery) AND (NOT is_tool_result OR include flag) ORDER BY timestamp
**Returns:** List of dicts with keys: role, content, timestamp

### Modification: cmd_session()
**Purpose:** Display messages when `--messages` flag is set
**Format per message:**
```
[HH:MM:SS] user:
  <content, indented>

[HH:MM:SS] assistant:
  <content, indented, truncated at 2000 chars unless --verbose>
```

### Modification: cmd_recent()
**Purpose:** Auto-detect project when `--project` not specified
**Logic:** `if not args.project: args.project = os.getcwd().replace("/", "-")`

### Error Handling
- `get_session_messages()` follows existing try/finally/conn.close() pattern
- No new error modes — DB connection errors already handled by outer try/except in `__main__`

---

## Implementation Strategy

### Phasing Rationale
Phase 1 (messages) is the higher-value feature and is self-contained. Phase 2 (CWD) is a 3-line change that depends on nothing.

### Phase 1: --messages flag
#### Goal
Add `get_session_messages()` function and `--messages`/`--verbose` flags to `session` subcommand.
#### Test Approach
Reference: AC-1, AC-2, AC-3
Manual testing against live DB.
#### Changes Required
- [ ] `search.py`: Add `get_session_messages()` function after `session_summary()`
- [ ] `search.py`: Add `--messages`, `--verbose`, `--limit` args to session subparser
- [ ] `search.py`: Extend `cmd_session()` to call `get_session_messages()` and format output
#### Validation
**Manual:**
- [ ] `search.py session <uuid>` still shows metadata only (no regression)
- [ ] `search.py session <uuid> --messages` shows user + assistant messages
- [ ] `search.py session <uuid> --messages --verbose` includes tool results
- [ ] `search.py session <uuid> --messages --limit 5` caps at 5 messages

### Phase 2: CWD auto-detection
#### Goal
`search.py recent` infers project from CWD when `--project` is omitted.
#### Test Approach
Reference: AC-4, AC-5
Manual testing from different directories.
#### Changes Required
- [ ] `search.py`: Add `import os` (if not already present)
- [ ] `search.py`: In `cmd_recent()`, add CWD fallback when `args.project` is None
#### Validation
**Manual:**
- [ ] `search.py recent` from claude-kit dir shows claude-kit sessions
- [ ] `search.py recent --project <explicit>` still uses the explicit value
- [ ] `search.py recent --project ""` or similar edge cases handled gracefully

---

## Risk Management
- **Large message content:** Mitigated by `--limit` flag and content truncation in non-verbose mode
- **Slug format change:** Low risk — convention is stable and used across multiple tools

---

## Implementation Notes

### Phase 1 Completion
**Completed:** 2026-03-10
**Changes Made:**
- Added `get_session_messages()` at `search.py:66-89` — follows existing try/finally/conn.close() pattern
- Added `--messages`, `--verbose`, `--limit` args to session subparser at `search.py:327-329`
- Extended `cmd_session()` at `search.py:283-307` — message display with role/timestamp, truncation, empty-list handling
- Added `import os` at `search.py:15`

**Per-Phase Audit:**
- Completion Accuracy: All items complete, no placeholders
- Deviations: Used `COALESCE(m.is_tool_result, false)` for NULL safety (not in plan but necessary)
- Test Coverage: Manual — verified messages display, tool result filtering, limit, no-messages regression

### Phase 2 Completion
**Completed:** 2026-03-10
**Changes Made:**
- Added CWD auto-detection at `search.py:242-246` — `if project is None: project = os.getcwd().replace("/", "-")`

**Per-Phase Audit:**
- Completion Accuracy: All items complete
- Deviations: Used `is None` instead of `not` per REFLECT agent recommendation
- Test Coverage: Manual — verified auto-detection from claude-kit dir, explicit --project override
