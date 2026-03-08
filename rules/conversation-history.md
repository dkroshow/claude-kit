# Conversation History Access

All Claude sessions are logged to PostgreSQL and searchable via full-text search.

## Quick Reference

```bash
# Search past conversations
python3 ~/claude-kit/conversation-logger/clogs/search.py search "query terms"

# Recent sessions (optionally filter by project)
python3 ~/claude-kit/conversation-logger/clogs/search.py recent
python3 ~/claude-kit/conversation-logger/clogs/search.py recent --project -Users-kd-Code-james

# Session details (message count, tokens, tool calls)
python3 ~/claude-kit/conversation-logger/clogs/search.py session <session-uuid>

# Context window gauge (how full is the current session's context?)
python3 ~/claude-kit/conversation-logger/clogs/gauge.py
python3 ~/claude-kit/conversation-logger/clogs/gauge.py --json  # machine-parseable
```

## When to Use

- **Debugging:** Search for past error messages, stack traces, or failure patterns
- **Continuity:** Find what was discussed or decided in prior sessions about a topic
- **Context recovery:** When CURRENT_WORK.md or learnings don't cover something you know was discussed before

## Details

- **Database:** james (PostgreSQL on port 5434)
- **Tables:** `claude_sessions`, `claude_messages`, `claude_tool_calls`
- **Search:** Full-text search via `search_vector` (tsvector) on `claude_messages`
- **Requires:** PostgreSQL running (`docker compose up -d` in james repo if needed)
