# Current Work

**Last Updated**: 2026-03-07 (session 2)

---

## Active

_No active items._

---

## Recently Completed

| Date | Item | Location |
|---|---|---|
| 2026-03-07 | Schema sync: `is_tool_result`/`is_human` in James schema.sql | `/Users/kd/Code/james/src/db/schema.sql` |
| 2026-03-07 | Conversation Logger (full implementation) | `conversation-logger/`, `.project/active/conversation-logger/` |
| 2026-03-06 | CURRENT_WORK.md index format + PAST_WORK.md | — |
| 2026-03-06 | Memory system enhancements | `.project/active/memory-enhancements/` |

---

## Up Next

1. Build meta-agent that manages Claude sessions (conversation-logger is a prerequisite)
2. Consider adding subsystem specification template/workflow (docs/ based)
3. Consider embedding-based semantic retrieval for learnings at scale

---

## Session Notes

### 2026-03-07 (session 2)
- Added `is_tool_result` and `is_human` columns to James `schema.sql` — schema file now matches live DB
- Change is in James repo (`/Users/kd/Code/james/src/db/schema.sql`), not committed yet (other uncommitted James changes present)

### 2026-03-07 (session 1)
- Built conversation-logger: parser, db, backfill, hooks, search — full 5-phase plan
- Schema lives in James DB (recommended over claude-kit as single source of truth)
- Key discoveries: assistant JSONL entries split across multiple lines sharing `message.id`; NUL bytes in tool results crash PostgreSQL; `async: true` hooks cause notification spam
- Added `is_tool_result` and `is_human` columns for content classification
- Hooks use synchronous registration + `& disown` to avoid notification noise
- Backfill: 454 sessions, ~61K messages, ~29K tool calls, ~20K real human messages

### 2026-03-06 (session 2)
- Reworked CURRENT_WORK.md as thin index (pointers, not content)
- Added PAST_WORK.md archive, removed CHANGELOG.md
- Decision: no backfill, populates naturally

### 2026-03-06 (session 1)
- Staleness detection at wrapup time (write time), not session start
- Subsystem specs belong in docs/, not .project/ (deferred)
- Trigger table populated for claude-kit
