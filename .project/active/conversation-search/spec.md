# Spec: Conversation Search Integration

**Status:** Draft
**Created:** 2026-03-07
**Complexity:** MEDIUM

---

## TL;DR

The conversation logger already stores all Claude session transcripts in PostgreSQL with full-text search. But no Claude session knows about it. This feature makes past conversations discoverable and searchable by: (1) adding a CLI interface to search.py, (2) teaching the memory agent to search past conversations, and (3) documenting the conversation DB in the rules so sessions know it exists.

---

## Business Goals

### Why This Matters
Past Claude sessions contain valuable context — decisions made, approaches tried, bugs debugged. Right now this knowledge is locked in a database that no session knows about. Making it searchable closes the loop: conversations get logged, and future sessions can retrieve relevant history.

### Success Criteria
- [ ] Any Claude session can search past conversations via a shell command
- [ ] The memory retrieval workflow automatically considers past conversations when relevant
- [ ] Sessions know the conversation DB exists without being explicitly told

---

## Problem Statement

### Current State
- Conversation logger writes to PostgreSQL (james DB, port 5434)
- `search.py` has `search_messages()`, `session_summary()`, `recent_sessions()`, analytics functions
- All are library functions — no CLI interface
- No rule or CLAUDE.md tells sessions the DB exists
- Memory agent only searches `.project/learnings/` and `~/.claude/learnings/`

### Desired Outcome
- `python3 ~/claude-kit/conversation-logger/clogs/search.py "query"` returns results
- Memory agent includes conversation search when checking prior knowledge
- Context-loading rules reference conversation DB as a retrieval source

---

## Scope

### In Scope
1. CLI interface for search.py (search, recent sessions, session detail)
2. Memory agent update to search conversations
3. Context-loading rule update to include conversation DB
4. Global rule or CLAUDE.md snippet documenting the DB

### Out of Scope
- Feedback table patterns (recommendation #4 — separate feature)
- Schema changes to the james DB
- Changes to the parser or ingestion pipeline
- Embedding-based semantic search (future work noted in CURRENT_WORK.md)

---

## Requirements

### Functional Requirements

1. **FR-1**: search.py is callable as a CLI tool with subcommands: `search <query>`, `recent [--project SLUG]`, `session <id>`
2. **FR-2**: CLI output is human-readable but also parseable by Claude (structured text, not raw JSON dumps)
3. **FR-3**: [INFERRED] CLI handles connection errors gracefully (DB might not be running)
4. **FR-4**: Memory agent searches conversation history when checking prior knowledge for a task
5. **FR-5**: Context-loading rules document the conversation DB as a retrieval source
6. **FR-6**: [INFERRED] A global rule tells all Claude sessions about the conversation DB and how to use it

---

## Acceptance Criteria

### Core Functionality
- [ ] **AC-1** (FR-1): **Given** the james DB is running, **when** `python3 ~/claude-kit/conversation-logger/clogs/search.py search "reconciliation"` is run, **then** matching messages are displayed with session context, timestamps, and content previews
- [ ] **AC-2** (FR-1): **Given** the james DB is running, **when** `python3 ~/claude-kit/conversation-logger/clogs/search.py recent` is run, **then** recent sessions are listed with project, branch, date, and first prompt
- [ ] **AC-3** (FR-1): **Given** the james DB is running, **when** `python3 ~/claude-kit/conversation-logger/clogs/search.py session <id>` is run, **then** session summary with message/tool counts is displayed
- [ ] **AC-4** (FR-3): **Given** the james DB is NOT running, **when** any CLI subcommand is run, **then** a clear error message is shown (not a traceback)
- [ ] **AC-5** (FR-4): **Given** a memory agent is spawned, **when** it searches for prior knowledge, **then** it also searches claude_messages for relevant past conversations
- [ ] **AC-6** (FR-5, FR-6): **Given** a new Claude session starts in any project, **when** context-loading rules are applied, **then** the session knows the conversation DB exists and how to query it

### Quality & Integration
- [ ] Existing search.py library functions remain unchanged (CLI is additive)
- [ ] No new dependencies beyond what's already in requirements.txt

---

## Related Artifacts

- **Prior spec:** `.project/active/conversation-logger/spec.md`
- **Plan:** `.project/active/conversation-search/plan.md` (to be created)

---

**Next Steps:** After approval, proceed to plan.
