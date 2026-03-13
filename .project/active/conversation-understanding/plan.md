# Conversation Understanding — Plan

**Spec:** `spec.md` (same directory)
**Date:** 2026-03-13
**Revision:** 2 (post-audit)

---

## TL;DR

Three phases: (1) build `conversation_state.py` with phase detection + health analysis, enhance parser for compression events, (2) build `understand.py` CLI exposing structured state as JSON, (3) test against mobile-terminal corpus (61 transcripts, 232MB). Works from JSONL directly (like gauge.py), no DB dependency for live monitoring.

---

## Architecture

```
understand.py (new CLI)
  ├── imports gauge.extract_usage() + compute_metrics()  → context pressure
  ├── imports parser.parse_transcript()                   → messages + tool calls
  ├── conversation_state.py (new)                        → phase detection, health, activity
  └── outputs JSON for james meta-agent consumption
```

**Key decision:** Works from JSONL files directly (same as gauge.py), not Postgres. Rationale:
- JSONL has complete data including entries the DB doesn't store
- No DB dependency for live monitoring
- James meta-agent needs real-time state, not historical queries
- Postgres remains the search/analytics backend (search.py)

---

## Audit Findings (incorporated)

1. **Phase detection overhaul:** Real sessions are iterative loops, not linear pipelines. Collapsed from 7 phases to 4 validated ones: exploration, planning, implementation, idle. Setup/research distinction is impossible in practice. Debugging/review had zero signal in corpus testing.
2. **Schema migration:** Schema lives in James repo (`~/Code/james/src/db/schema.sql`). Use raw `ALTER TABLE` from Python for now (no TypeScript dependency). Schema.sql update is a separate PR in James.
3. **Test infrastructure:** None exists. Use pytest (add to requirements.txt). Create `conversation-logger/tests/`.
4. **Compression events:** `compact_boundary` JSONL structure: `{type: "system", subtype: "compact_boundary", content: "Conversation compacted", timestamp: ..., uuid: ...}`.

---

## Phase 1: Conversation State Module + Parser Enhancement

**Goal:** Build core analysis logic and capture compression events

- [x] **1a. Create `clogs/conversation_state.py`**
- [x] **1b. Enhance `parser.py` for compression events**
- [x] **1c. Schema + db.py changes for compression columns**

### 1a. New file: `clogs/conversation_state.py`

Core analysis module. All functions operate on parsed data (output of `parse_transcript()`).

**`detect_phase(messages)` → dict**

Analyzes the last 20 messages (with their embedded tool_calls) using a sliding window:

| Phase | Signal | Confidence |
|-------|--------|-----------|
| `idle` | Last message timestamp > 5 min ago | high |
| `exploration` | Read/Grep/Glob > 60% of recent tool calls, Edit/Write < 20% | high if >10 tools, medium otherwise |
| `planning` | Skill/TaskCreate tool calls present, or text-heavy assistant messages with low tool activity | medium |
| `implementation` | Edit/Write/Bash > 50% of recent tool calls | high if >5 tools, medium otherwise |

Returns: `{"current": "implementation", "confidence": "high"}`

Fallback: if no pattern matches, return `{"current": "unknown", "confidence": "low"}`

Key insight from audit: sessions bounce between phases rapidly (57-82% transition rate). The window approach captures what's happening *right now*, not the session's overall phase.

**`assess_health(messages, tool_results)` → dict**

Inputs: parsed messages (with embedded tool_calls) + tool_results dict from parser.

- `error_rate`: fraction of last 10 tool calls where `tool_results[tool_use_id].is_error == True`
- `retry_loops`: count of consecutive tool calls with same `tool_name` + same `input` (within last 10)
- `last_activity`: ISO timestamp of most recent message
- `idle_seconds`: seconds between now and last_activity
- `stuck`: boolean — `error_rate > 0.5 OR retry_loops >= 3`

**`summarize_activity(messages)` → dict**

Scans all messages in the session (not just recent window):

- `files_read`: deduplicated list of `file_path` from Read tool inputs
- `files_edited`: deduplicated list of `file_path` from Edit/Write tool inputs
- `commands_run`: list of Bash `command` inputs (first 80 chars), last 20 commands
- `tools_used`: `{tool_name: count}` across all messages
- `agents_spawned`: count of Task/Agent tool calls

**`extract_intent(messages)` → dict**

- `initial_prompt`: content of first message where `is_human == True` (truncated 500 chars)
- `latest_prompt`: content of most recent `is_human == True` message (truncated 500 chars)
- `turn_count`: total count of `is_human == True` messages

### 1b. Enhance `parser.py`

Add to `parse_transcript()`:
- Collect entries where `type == "system"` and `subtype == "compact_boundary"` (currently only `turn_duration` is captured)
- Count them → add `compression_count` to the `session` dict
- Find latest timestamp → add `last_compressed_at` to `session` dict
- Add `events` list to return dict: `[{"type": "compression", "timestamp": "...", "uuid": "..."}]`

Changes are additive — existing return keys (`session`, `messages`, `tool_results`) unchanged. New key `events` added.

### 1c. Schema + db.py

**Schema:** Run `ALTER TABLE` directly via Python (no James dependency):
```sql
ALTER TABLE claude_sessions ADD COLUMN IF NOT EXISTS compression_count INTEGER DEFAULT 0;
ALTER TABLE claude_sessions ADD COLUMN IF NOT EXISTS last_compressed_at TIMESTAMPTZ;
```

**db.py changes:**
- Add `compression_count` and `last_compressed_at` to `upsert_session()` INSERT + ON CONFLICT UPDATE
- Populate from `session` dict (parser now provides these)

**`ingest_transcript()` flow** (no changes needed — parser output flows through automatically):
parser.parse_transcript() → session dict has compression fields → upsert_session() writes them

**Test approach:**
- Unit test `detect_phase()` with synthetic tool call sequences for each phase
- Unit test `assess_health()` with error/retry scenarios
- Unit test compression event extraction with real JSONL snippet
- Verify existing parse_transcript() output unchanged (backward compat)

**Acceptance criteria:** AC-1, AC-4, AC-7

---

## Phase 2: CLI Interface (`understand.py`)

**Goal:** Expose conversation state as a CLI tool

- [x] **2a. Create `clogs/understand.py`**

### 2a. New file: `clogs/understand.py`

CLI following same patterns as gauge.py:

```
python3 understand.py --file <path.jsonl>         # explicit file (primary for testing)
python3 understand.py --all --json                 # all active sessions
python3 understand.py <session-id> --json          # by session ID (resolves via session.py)
```

**Import pattern** (same as gauge.py line 26):
```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
from session import resolve_session, resolve_all_sessions
from gauge import extract_usage, compute_metrics
from parser import parse_transcript
from conversation_state import detect_phase, assess_health, summarize_activity, extract_intent
```

**Execution flow:**
1. Resolve JSONL path (--file, session resolver, or --all)
2. `parse_transcript(path)` → messages, tool_calls, tool_results, events
3. `extract_usage(path)` + `compute_metrics()` → context pressure
4. `detect_phase(messages)` → phase
5. `assess_health(messages, tool_results)` → health
6. `summarize_activity(messages)` → activity
7. `extract_intent(messages)` → intent
8. Merge context metrics + compression data from parser
9. Output JSON or human-readable

**JSON output schema:**
```json
{
  "session_id": "uuid",
  "project_slug": "...",
  "phase": {"current": "implementation", "confidence": "high"},
  "health": {
    "error_rate": 0.05,
    "retry_loops": 0,
    "idle_seconds": 45,
    "stuck": false
  },
  "context": {
    "current_size": 89000,
    "threshold": 165000,
    "pct_used": 53.9,
    "remaining": 76000,
    "burn_rate": 3200,
    "est_turns_remaining": 23,
    "compression_count": 0,
    "total_turns": 15
  },
  "activity": {
    "files_read": ["src/foo.py", "src/bar.py"],
    "files_edited": ["src/foo.py"],
    "commands_run": ["npm test", "git status"],
    "tools_used": {"Read": 8, "Edit": 3, "Bash": 4},
    "agents_spawned": 1
  },
  "intent": {
    "initial_prompt": "Fix the login bug...",
    "latest_prompt": "Now run the tests",
    "turn_count": 5
  }
}
```

**Human-readable output** (default, no --json):
```
Session: abc123...
Phase:   implementation (high confidence)
Health:  OK (error rate 5%, no retry loops, active 45s ago)
Context: 89,000 / 165,000 (53.9%) — ~23 turns remaining, burn ~3,200/turn
Activity: 2 files read, 1 edited, 3 commands, 1 agent spawned
Intent:  "Fix the login bug..." → "Now run the tests" (5 turns)
```

**Test approach:**
- Run against a known mobile-terminal transcript, verify JSON schema validates
- Test --all mode
- Test --file mode

**Acceptance criteria:** AC-2, AC-3, AC-5, AC-8

---

## Phase 3: Corpus Testing + Polish

**Goal:** Validate against full mobile-terminal corpus, fix edge cases

- [x] **3a. Create test infrastructure + integration tests** (ran inline — 59/61 parsed, 0 errors, 4 phases)
- [x] **3b. Fix edge cases found during testing** (idle-only bug fixed with live parameter)
- [x] **3c. Run schema migration + backfill compression data** (ALTER TABLE done, ingestion verified)

### 3a. Test infrastructure

Create `conversation-logger/tests/test_corpus.py` using pytest:

```
pip install pytest  (add to requirements.txt)
conversation-logger/tests/
  __init__.py
  test_corpus.py          # integration: all 61 mobile-terminal transcripts
  test_conversation_state.py  # unit: phase detection, health, activity
```

Integration test:
- Iterate all JSONL in `~/.claude/projects/-Users-kd-Code-mobile-terminal/`
- For each: parse_transcript() + all conversation_state functions
- Assert: valid output, no exceptions
- Collect phase distribution → assert 3+ distinct phases found
- Compare context metrics against gauge.py for 3 sample sessions

### 3b. Edge cases
- Empty/tiny sessions (0-2 messages)
- Sessions with only tool results (no is_human messages)
- 21MB file performance (must be < 5s)
- Multiple compression events in one session

### 3c. Schema migration + backfill
- Run ALTER TABLE on Postgres
- Re-run `python3 backfill.py` (parser now emits compression data → flows through automatically)
- Also update `~/Code/james/src/db/schema.sql` to keep it in sync (separate commit in James)

**Acceptance criteria:** AC-3, AC-5, AC-6, NFR-1

---

## Risk Management

| Risk | Mitigation |
|------|-----------|
| Phase heuristics miss edge cases | 4 validated phases only; "unknown" fallback; iterate after corpus testing |
| gauge.py import path | Same sys.path.insert pattern gauge.py uses (verified in audit) |
| 21MB JSONL too slow | parse_transcript already streams line-by-line; skip progress entries early |
| ALTER TABLE on production DB | ADD COLUMN IF NOT EXISTS with defaults — non-breaking, idempotent |
| parser return schema change | Additive only (new `events` key) — existing consumers unaffected |

---

## File Summary

| File | Action | Purpose |
|------|--------|---------|
| `clogs/conversation_state.py` | **Create** | Phase detection, health, activity, intent extraction |
| `clogs/understand.py` | **Create** | CLI interface for conversation state |
| `clogs/parser.py` | **Edit** | Add compression event extraction to parse_transcript() |
| `clogs/db.py` | **Edit** | Add compression_count + last_compressed_at to upsert_session() |
| `tests/__init__.py` | **Create** | Test package |
| `tests/test_conversation_state.py` | **Create** | Unit tests for phase/health/activity |
| `tests/test_corpus.py` | **Create** | Integration tests against mobile-terminal corpus |
| `requirements.txt` | **Edit** | Add pytest |
