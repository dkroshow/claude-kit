# Spec: Claude Conversation Logger

**Status:** Draft
**Owner:** dkroshow
**Created:** 2026-03-03T07:12:07Z
**Complexity:** HIGH
**Branch:** TBD

---

## TL;DR

Claude Code stores conversation transcripts as flat JSONL files under `~/.claude/projects/`. These files contain rich structured data — prompts, responses, tool calls, token usage, timestamps — but are impractical to query across sessions or projects. This spec defines a system that automatically ingests all Claude Code conversations into PostgreSQL (the existing `james` database) in near real-time via Claude Code hooks. The database becomes a queryable foundation for memory retrieval, analytics, and meta-agent work (agents that read and reason about past sessions).

---

## Business Goals

### Why This Matters

Current conversation storage is scattered across dozens of JSONL files with no indexing beyond filenames. Finding "what did I discuss about authentication last week" requires parsing raw files. Cross-session patterns, cost trends, and tool usage analytics are invisible. Most critically, agents cannot programmatically access conversation history — which blocks the goal of having agents manage Claude Code sessions.

A relational database with full-text search transforms conversation history from dead files into a live, queryable knowledge base.

### Success Criteria

- [ ] Every Claude Code session across all projects is automatically logged to PostgreSQL
- [ ] Messages appear in the database within seconds of occurring (near real-time)
- [ ] Past conversations are searchable by content, project, date range, and tool usage
- [ ] Token usage and cost data is tracked per-session and per-turn
- [ ] Existing transcript history is backfilled into the database
- [ ] Meta-agents can query the database to reason about past sessions

### Priority

New work item. Companion to claude-kit (which lays hooks groundwork but scoped out Postgres). Supersedes the stalled memory-architecture work for the conversation storage layer.

---

## Problem Statement

### Current State

Claude Code stores transcripts at `~/.claude/projects/<slug>/<uuid>.jsonl`. Each line is a JSON object with types: `user`, `assistant`, `system`, `progress`, `file-history-snapshot`. The data is rich:
- User prompts with timestamps and working directory
- Assistant responses with token usage (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`), model name, and stop reason
- Tool use blocks with tool name, input parameters, and corresponding tool results
- Session metadata (git branch, Claude Code version, session ID)
- Turn duration tracking

But it's trapped in flat files. No cross-session search, no aggregation, no programmatic access for agents.

### Desired Outcome

All conversation data flows into PostgreSQL automatically. The database supports:
1. **Memory retrieval** — "What did I discuss about X?" via full-text search across all sessions
2. **Analytics** — Token spend by day/project/model, tool usage frequency, session patterns
3. **Meta-agent work** — Agents query conversation history to extract patterns, resume context, and eventually manage sessions

---

## Scope

### In Scope

- **PostgreSQL schema** added to the `james` database — sessions, messages, tool calls, tool results, token usage tables
- **Full-text search** on message content using James's existing `tsvector` pattern
- **Near real-time ingestion** via Claude Code hooks (`Stop`, `UserPromptSubmit`) running async Python scripts
- **Batch safety net** via `SessionEnd` hook to catch anything missed
- **Backfill script** to ingest all existing JSONL transcripts across all projects
- **Idempotent ingestion** — re-running on the same transcript doesn't create duplicates (upsert on message UUID)
- **All projects, all sessions** — not scoped to a single repo
- **Agent-readable schema** — designed for programmatic querying by meta-agents, not just human SQL
- **Connection via psycopg2** — Python ingestion scripts connecting to `james` database on localhost:5434

### Out of Scope

- UI/dashboard (mobile-terminal integration is a separate downstream effort)
- Semantic/vector search (relational + full-text search first; embedding layer could come later)
- MCP server or Claude Code tool integration (direct SQL access for now)
- Storage optimization / content omission analysis (deferred to implementation; plenty of storage available)
- Modifying mobile-terminal to consume this data
- Modifying claude-kit itself (this is a companion project)

### Edge Cases & Considerations

- **Crashed sessions**: `SessionEnd` hook may not fire if Claude Code crashes or is force-killed. The backfill script doubles as a periodic catch-up mechanism.
- **Compacted transcripts**: `PreCompact` fires before context compaction mid-session. Post-compaction, earlier messages may be summarized in the JSONL. The `Stop` hook captures messages before compaction happens, so near-real-time ingestion avoids data loss.
- **Large tool results**: File contents, command output, and search results can be very large (tens of KB per tool result). Store full content for now (storage is plentiful); deeper omission analysis during implementation.
- **Sidechain messages**: Some messages are marked `isSidechain: true` (subagent work). These should be stored but flagged.
- **Subagent transcripts**: Stored in `<uuid>/subagents/` subdirectories. Include in ingestion with a parent session reference.
- **JSONL format stability**: The transcript format is not an officially documented stable API. Schema and parser should be resilient to missing or new fields.
- **Concurrent sessions**: Multiple Claude Code sessions can run simultaneously. Each has its own session ID and transcript file — no conflict.

---

## Requirements

### Functional Requirements

> Requirements below are from user's request unless marked [INFERRED] or [FROM INVESTIGATION]

1. **FR-1**: The system MUST store all user prompts with timestamps in PostgreSQL
2. **FR-2**: The system MUST store all assistant responses with timestamps in PostgreSQL
3. **FR-3**: The system MUST capture conversations from all Claude Code sessions across all projects
4. **FR-4**: The system MUST ingest conversations in near real-time (within seconds of each message)
5. **FR-5**: The system MUST support efficient lookup of past conversations (the primary motivation)
6. **FR-6**: The system MUST enable memory retrieval use cases (search by content, context, patterns)
7. **FR-7**: The system MUST enable analytics use cases (token usage, cost tracking, tool usage trends)
8. **FR-8**: The system MUST enable meta-agent use cases (programmatic access for agents to read and reason about past sessions)
9. **FR-9**: [INFERRED] The system MUST store tool calls and tool results as structured data (tool name, inputs, outputs)
10. **FR-10**: [INFERRED] The system MUST track token usage per assistant turn (input, output, cache read, cache creation tokens)
11. **FR-11**: [INFERRED] The system MUST support full-text search on message content
12. **FR-12**: [INFERRED] The system MUST backfill existing transcript history into the database
13. **FR-13**: [INFERRED] Ingestion MUST be idempotent — re-processing a transcript does not create duplicate records
14. **FR-14**: [INFERRED] The schema MUST be agent-readable — designed for programmatic querying, not just human SQL
15. **FR-15**: [FROM INVESTIGATION] The system MUST use Claude Code hooks as the ingestion mechanism (SessionEnd, Stop, UserPromptSubmit)
16. **FR-16**: [FROM INVESTIGATION] The schema MUST follow James database conventions (UUID primary keys, `created_at`/`updated_at` timestamps, `tsvector` for full-text search)
17. **FR-17**: [FROM INVESTIGATION] Hook scripts MUST run asynchronously (`async: true`) to avoid slowing down Claude Code conversations
18. **FR-18**: [FROM INVESTIGATION] The system MUST store session-level metadata (project path, git branch, Claude Code version, model, duration)

### Non-Functional Requirements

- **NFR-1**: Hook-triggered ingestion must not perceptibly slow down the Claude Code experience (async execution)
- **NFR-2**: The parser must be resilient to missing or unexpected fields in JSONL entries (forward-compatible)
- **NFR-3**: The backfill script must be safe to run multiple times (idempotent via upsert)
- **NFR-4**: Python 3.9.1 compatibility required (no `X | Y` union syntax, use `Optional[X]`)

---

## Acceptance Criteria

### Core Functionality

- [ ] **AC-1** (FR-1, FR-2): **Given** a Claude Code session is active, **when** the user sends a prompt and Claude responds, **then** both messages appear in the `messages` table within 10 seconds with correct timestamps
- [ ] **AC-2** (FR-3): **Given** Claude Code sessions exist across multiple projects, **when** the ingestion system is running, **then** all sessions from all projects are captured (verified by comparing session count in DB vs JSONL file count)
- [ ] **AC-3** (FR-4): **Given** a `Stop` hook fires after an assistant turn, **when** the hook script executes, **then** the latest messages are written to PostgreSQL before the next user prompt
- [ ] **AC-4** (FR-5, FR-6, FR-11): **Given** conversations are stored in PostgreSQL, **when** a user searches for a keyword, **then** full-text search returns matching messages ranked by relevance across all sessions
- [ ] **AC-5** (FR-7, FR-10): **Given** token usage is stored per turn, **when** querying for cost analytics, **then** results can be aggregated by day, project, and model with accurate cost estimates
- [ ] **AC-6** (FR-8, FR-14): **Given** the schema is agent-readable, **when** a meta-agent queries for past sessions about a topic, **then** it receives structured results including session context (project, branch, timestamps) and message content
- [ ] **AC-7** (FR-9): **Given** an assistant response includes tool calls, **when** the message is ingested, **then** each tool call is stored as a separate record with tool name, input parameters, and corresponding result
- [ ] **AC-8** (FR-12, FR-13): **Given** existing JSONL transcripts under `~/.claude/projects/`, **when** the backfill script runs, **then** all historical sessions are ingested, and running it again produces no duplicates
- [ ] **AC-9** (FR-15, FR-17): **Given** hooks are configured in `~/.claude/settings.json`, **when** Claude Code runs normally, **then** ingestion hooks fire asynchronously without perceptible delay to the user
- [ ] **AC-10** (FR-16): **Given** the James database has existing tables, **when** the conversation logger schema is applied, **then** new tables follow James conventions (UUID PKs, timestamptz, tsvector) and coexist without conflicts
- [ ] **AC-11** (FR-18): **Given** a completed session, **when** querying the `sessions` table, **then** the record includes project path, git branch, Claude Code version, model, start/end timestamps, and aggregate token counts

### Quality & Integration

- [ ] James database existing tables and queries continue to function unchanged
- [ ] Hook scripts handle malformed or incomplete JSONL entries gracefully (log warning, skip entry, don't crash)
- [ ] Backfill script provides progress output (files processed, records inserted, errors encountered)

---

## Related Artifacts

- **Research:** Conducted in-session (Claude Code hooks, transcript format, James/Galaxy database analysis)
- **Plan:** `.project/active/conversation-logger/plan.md` (to be created)
- **claude-kit:** This repo — conversation logger lives here as part of the toolkit
- **James database:** `/Users/kd/Code/james/` — target database (`james` on localhost:5434)
- **Mobile-terminal:** `/Users/kd/Code/mobile-terminal/` — future downstream consumer
- **Existing hooks:** `~/claude-kit/hooks/` — `precompact-capture.sh`, `capture.sh`, `parse-transcript.py`, `query-transcript.py`

---

**Next Steps:** After approval, proceed to `/_plan`
