# Current Work

**Last Updated**: 2026-03-07 (session 3)

---

## Active

_No active items._

---

## Recently Completed

| Date | Item | Location |
|---|---|---|
| 2026-03-07 | Conversation search integration (CLI + rules + memory agent) | `.project/active/conversation-search/` |
| 2026-03-07 | Schema sync: `is_tool_result`/`is_human` in James schema.sql | `/Users/kd/Code/james/src/db/schema.sql` |
| 2026-03-07 | Conversation Logger (full implementation) | `conversation-logger/`, `.project/active/conversation-logger/` |

---

## Up Next

1. Build meta-agent that manages Claude sessions (conversation-logger is a prerequisite)
2. Consider adding subsystem specification template/workflow (docs/ based)
3. Consider embedding-based semantic retrieval for learnings at scale

---

## Session Notes

### 2026-03-07 (session 3)
- Added CLI to search.py: `search`, `recent`, `session` subcommands via argparse
- Created `rules/conversation-history.md` — global rule so all sessions know the conversation DB exists
- Updated `rules/context-loading.md` — conversation history as Tier 2 retrieval source, added to "Don't Re-Research" list
- Extended `agents/memory.md` — suggests conversation search when learnings have gaps
- Full Standard-tier cycle: spec + plan at `.project/active/conversation-search/`

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
