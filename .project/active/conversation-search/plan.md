# Plan: Conversation Search Integration

**Status:** Draft
**Created:** 2026-03-07

---

## TL;DR

Make past Claude conversations searchable from any session. Three phases: (1) Add CLI interface to search.py with `search`, `recent`, `session` subcommands using argparse, (2) Update context-loading rules and add a global rule documenting the conversation DB, (3) Extend the memory agent to search past conversations. No new dependencies — uses existing psycopg2 and search functions.

---

## Source Documents
- **Spec:** `.project/active/conversation-search/spec.md`

## Research Findings

### Files Analyzed
- `conversation-logger/clogs/search.py:1-164` — 6 library functions, all return list-of-dicts or dict
- `conversation-logger/clogs/db.py:1-257` — `get_connection()` at line 31, DSN at line 21
- `agents/memory.md:1-60` — memory retrieval agent, searches learnings only
- `rules/context-loading.md:1-52` — retrieval decision tree, dual-index retrieval, 3 tiers

### Reusable Patterns
- All search functions return `list[dict]` with column names as keys — CLI just needs formatting
- `get_connection()` already handles DSN via env var fallback (`db.py:32`)
- Memory agent already has a clear "Process" section with numbered steps — easy to extend

### Integration Points
- CLI: search.py already imported by nothing external — adding `__main__` is purely additive
- Rules: context-loading.md has a clear "Don't Re-Research" section listing sources — add conversation DB there
- Memory agent: Step 4 in the Process section handles ambiguous matches with Grep — add a step for conversation search via Bash

## Design Decisions

### Decision 1: CLI framework
**Context:** Need subcommands (search, recent, session) with flags
**Options:** argparse vs sys.argv manual parsing vs click
**Chosen:** argparse
**Rationale:** stdlib, no new deps, handles subcommands well

### Decision 2: Where to document the DB reference
**Context:** Sessions need to know the conversation DB exists. Could go in a global rule, CLAUDE.md, or both.
**Chosen:** New global rule file `rules/conversation-history.md`
**Rationale:** Rules in `~/claude-kit/rules/` are loaded into all sessions via the kit's init system. A dedicated file keeps it focused and easy to find. No CLAUDE.md exists in this repo to add to.

### Decision 3: How the memory agent searches conversations
**Context:** The memory agent has Read/Grep/Glob tools only. It can't run Bash to call the CLI.
**Chosen:** Add instructions for the memory agent to tell the main agent to search conversations, rather than searching directly. The main agent (which has Bash) runs the CLI command.
**Rationale:** The memory agent's tool set is intentionally limited. Rather than expanding it, we document in context-loading.md that conversation search is a Tier 2 retrieval action the main agent performs directly.

---

## Technical Design

### Architecture Overview

```
Claude Session
  ├── context-loading.md (knows conversation DB exists)
  ├── conversation-history.md (global rule: DB details + CLI usage)
  ├── memory agent (suggests conversation search when relevant)
  └── search.py CLI (executes searches)
        └── search.py library functions (unchanged)
              └── PostgreSQL (james DB)
```

### Component 1: CLI Interface
**Purpose:** Make search.py callable from command line
**Location:** `conversation-logger/clogs/search.py` — append `if __name__ == "__main__"` block
**Key interfaces:**
- `python3 search.py search <query> [--limit N]` — full-text search
- `python3 search.py recent [--project SLUG] [--limit N]` — recent sessions
- `python3 search.py session <session-id>` — session detail
**Output format:** Structured text with clear headers, one result per block, fields on separate lines

### Component 2: Global Rule
**Purpose:** Tell all Claude sessions about the conversation DB
**Location:** `rules/conversation-history.md` (new file)
**Content:** DB location, CLI command examples, when to use it

### Component 3: Context-Loading Update
**Purpose:** Integrate conversation search into the retrieval decision tree
**Location:** `rules/context-loading.md` — add to "Don't Re-Research" section and retrieval tiers

### Component 4: Memory Agent Update
**Purpose:** Remind memory agent that conversation history is a source
**Location:** `agents/memory.md` — add note about conversation search

### Error Handling
- CLI wraps all DB calls in try/except for `psycopg2.OperationalError` — prints friendly message if DB is down
- Non-zero exit code on errors

---

## Implementation Strategy

### Phasing Rationale
Phase 1 (CLI) is the foundation — everything else references it. Phase 2 (rules/docs) makes it discoverable. Phase 3 (memory agent) integrates it into the automated workflow.

### Phase 1: CLI Interface
#### Goal
Add argparse-based CLI to search.py so it's callable from any shell.
#### Test Approach
Reference: AC-1, AC-2, AC-3, AC-4
Manual testing against live DB.
#### Changes Required
- [ ] `conversation-logger/clogs/search.py`: Add `main()` function with argparse subcommands
- [ ] `conversation-logger/clogs/search.py`: Add `if __name__ == "__main__"` block
- [ ] `conversation-logger/clogs/search.py`: Add formatting helpers for CLI output
- [ ] `conversation-logger/clogs/search.py`: Add error handling for DB connection failures
#### Validation
**Manual:**
- [ ] `python3 search.py search "test"` returns formatted results
- [ ] `python3 search.py recent` lists recent sessions
- [ ] `python3 search.py session <id>` shows session detail
- [ ] DB-down scenario shows friendly error

### Phase 2: Rules & Documentation
#### Goal
Make conversation DB discoverable to all Claude sessions via rules.
#### Test Approach
Reference: AC-6
Read the files and verify they contain correct CLI paths and DB info.
#### Changes Required
- [ ] Create `rules/conversation-history.md`: global rule with DB details and CLI usage
- [ ] Update `rules/context-loading.md`: add conversation DB to "Don't Re-Research" section and retrieval tiers
#### Validation
**Manual:**
- [ ] Rules contain correct CLI path and examples
- [ ] Context-loading references are consistent with the new rule

### Phase 3: Memory Agent Update
#### Goal
Extend memory agent to include conversation history in its retrieval output.
#### Test Approach
Reference: AC-5
Review the agent definition and verify conversation search is referenced.
#### Changes Required
- [ ] Update `agents/memory.md`: add conversation search step and output section
#### Validation
**Manual:**
- [ ] Memory agent instructions reference conversation search
- [ ] Output template includes conversation history section

---

## Risk Management
- **DB not running:** Handled by error catching in Phase 1. Rules note DB availability as a prerequisite.
- **Large result sets:** CLI uses `--limit` with sensible defaults (already in library functions).
- **DSN exposure in rules:** DSN is already in db.py. Rules reference the CLI command, not the DSN directly.

---

## Implementation Notes
[TO BE FILLED DURING IMPLEMENTATION]
