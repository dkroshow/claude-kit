# Research: Conversation Understanding for Agent Monitoring

**Date:** 2026-03-12
**Scope:** What's needed to enable an agent to read, understand, and act on active Claude Code conversations

---

## Current State

### Data Pipeline (Working)
- **Source:** JSONL transcripts at `~/.claude/projects/<slug>/<uuid>.jsonl`
- **Ingestion:** Real-time via hooks (`on-assistant-turn.sh`, `on-session-end.sh`) + bulk `backfill.py`
- **Parser:** `clogs/parser.py` — merges streaming chunks, extracts text/thinking/tool_use, classifies noise
- **Storage:** PostgreSQL (`claude_sessions`, `claude_messages`, `claude_tool_calls`)
- **Query:** `search.py` (full-text), `gauge.py` (context metrics), `session.py` (session resolution)

### Data Volume
| Metric | Count |
|--------|-------|
| Sessions | 594 |
| Messages | 86,855 |
| Tool calls | 40,634 |
| Tool results captured | 40,633 (99.997%) |
| Human messages (conversational) | 27,101 (31%) |
| Tool result messages (noise) | 39,703 (46%) |

### Test Corpus
- **mobile-terminal project:** 61 JSONL files, 232MB, 53 already in Postgres
- **claude-kit project:** 19 JSONL files, 11.5MB
- Largest single transcript: 21MB (808d7db6, mobile-terminal)

---

## What the Parser Captures Well

1. **User messages** — plain text + structured content blocks
2. **Assistant messages** — text, thinking, tool_use (streaming chunks merged by `message.id`)
3. **Tool results** — linked back via `tool_use_id`, error flag preserved
4. **Session metadata** — project, branch, version, model, timestamps
5. **Token usage** — input, output, cache read/creation per turn
6. **Turn duration** — from `system.turn_duration` entries
7. **Classification** — `is_human`, `is_tool_result`, `is_sidechain` booleans

## What the Parser Ignores

| Entry Type | % of JSONL | What It Contains | Value for Monitoring |
|------------|-----------|------------------|---------------------|
| `progress` | ~53% | bash_progress (streaming output), agent_progress (subagent spawning), hook events | **High** — bash output reveals what commands are running; agent_progress shows subagent lifecycle |
| `file-history-snapshot` | ~3% | File modification tracking with backup refs | **Medium** — shows which files were modified per turn |
| `system.compact_boundary` | rare | Context compression events | **Critical** — marks when conversation was compressed, essential for monitoring |
| `system.stop_hook_summary` | ~1% | Hook execution metadata | **Low** — operational, not conversational |

## What's Missing for Agent Understanding

### 1. Conversation State Machine
No concept of "what phase is this conversation in?" Conversations follow patterns:
- **Setup:** User describes task, Claude reads files/explores
- **Research:** Claude searches codebase, reads docs
- **Planning:** Claude proposes approach, user confirms
- **Implementation:** Claude writes/edits code, runs tests
- **Debugging:** Error → read → fix → retry loops
- **Review:** Final checks, commit, cleanup
- **Idle/Waiting:** Awaiting user input

Detectable from: tool call patterns, message content, time gaps between messages.

### 2. Intent/Task Extraction
No module answers "what is this conversation trying to accomplish?" The first human message often contains the task, but intent can shift mid-conversation.

### 3. Error/Stuck Detection
No detection of:
- Tool call failures (repeated errors on same tool)
- Retry loops (same action attempted multiple times)
- Permission blocks (user denying tool calls)
- Long idle periods (waiting for user input)
- Context window pressure (approaching compression threshold)

Data IS available — `claude_tool_calls.is_error` + patterns in tool call sequences.

### 4. Tool Chain Analysis
No analysis of tool call patterns:
- Read → Edit → Read (verify) cycles
- Bash error → fix → retry patterns
- Agent spawning patterns
- File modification graphs (which files touched, in what order)

### 5. Compression Events
`compact_boundary` entries are ignored by the parser. These mark when CC compressed the conversation, which is critical for:
- Understanding context window pressure
- Knowing that earlier context may be lost
- Gauging session health

### 6. Subagent Tracking
`is_sidechain` is stored but never analyzed. Subagent transcripts exist as separate JSONL files in `<session-uuid>/subagents/agent-*.jsonl` but are explicitly skipped by `backfill.py`.

---

## Architecture Decision

Per James VISION.md cross-project architecture:

| Layer | Repo | What Goes Here |
|-------|------|---------------|
| **Parsing/Understanding Infrastructure** | claude-kit | Enhanced parser, conversation state extraction, structured query APIs |
| **Agent Decision-Making/Actions** | james (`src/agent/`) | Monitoring loop, action triggers, Telegram notifications, CC session interaction |
| **Session Control** | mobile-terminal | HTTP API for reading output, sending commands (already exists) |

**Boundary:** claude-kit provides CLI tools and Python functions. James calls them via subprocess. No cross-repo imports.

---

## Recommended Approach

### Phase 1: Enhanced Data Capture (claude-kit)
- Parse `progress` entries (bash output, agent lifecycle)
- Parse `compact_boundary` events
- Ingest subagent transcripts (currently skipped)
- Add new DB columns/tables as needed

### Phase 2: Conversation State Extraction (claude-kit)
- Build a `conversation_state()` function that returns structured state for a session
- Inputs: session_id or JSONL path
- Outputs: phase, intent summary, tool patterns, error count, stuck indicators, context pressure
- Expose as CLI: `python3 understand.py <session-id>`

### Phase 3: Monitoring Agent (james)
- Polling loop that periodically calls claude-kit tools
- Decision logic: when to alert, when to intervene
- Action execution via mobile-terminal API + Telegram notifications
- Integration with james orchestrator

### Testing Strategy
- **Unit tests:** Parse individual JSONL entries, verify state extraction
- **Integration tests:** Run against mobile-terminal corpus (232MB, 61 sessions)
- **Live test:** Monitor an active session, verify state detection accuracy
