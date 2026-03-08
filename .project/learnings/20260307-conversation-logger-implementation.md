---
type: gotcha
tags: conversation-logger, jsonl, postgresql, hooks, parser
created: 2026-03-07
---

# Conversation Logger Implementation Gotchas

## What
Key discoveries from building the JSONL-to-PostgreSQL conversation logger.

## JSONL Streaming Format
Assistant messages are split across **multiple JSONL lines** sharing the same `message.id`. Each line contains one content block (text, thinking, tool_use). Parser must group by `message.id` and merge all content blocks before storage.

## NUL Bytes in Tool Results
Some tool results contain `\x00` (NUL) bytes that PostgreSQL text columns reject with `ValueError`. All text fields must be stripped via `_strip_nul()` before insertion. Affected ~8 of 454 transcripts.

## Hook Notification Spam
Claude Code hooks registered with `async: true` show "Async hook Stop completed" notifications to the user after every prompt. Fix: register hooks as synchronous but background the actual work in the shell script (`python3 ... & disown`). Hook returns instantly, work runs silently.

## Content Classification
Raw JSONL has lots of noise: `<command-*>` tags, `<local-command-caveat>`, expanded skill prompts, `[Request interrupted]`, terminal control characters (`\x15` NAK). Use `is_tool_result` (tool result vs real user message) and `is_human` (real conversational message vs noise) booleans for filtering.

## Schema Location
Schema lives in James DB (`/Users/kd/Code/james/src/db/schema.sql`) as single source of truth for all database tables. Code lives in claude-kit.

## Key Files
- `conversation-logger/clogs/parser.py` — JSONL parser with chunk merging
- `conversation-logger/clogs/db.py` — PostgreSQL upserts with NUL stripping
- `conversation-logger/hooks/on-assistant-turn.sh` — Stop hook (real-time ingestion)
- `setup.sh` — hook registration (lines ~206-243)
