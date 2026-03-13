# Conversation Understanding — Spec

**Status:** Draft
**Date:** 2026-03-12
**Tier:** Complex

---

## Problem Statement

Claude Code conversations are captured in PostgreSQL via conversation-logger, but the data is flat and unanalyzed. An agent monitoring conversations has no way to answer: "What is this session doing? Is it stuck? Should I intervene?" The raw data needs structured understanding before the james meta-agent can act on it.

## Business Goals

1. Enable the james meta-agent to monitor active Claude Code sessions intelligently
2. Surface actionable conversation state (phase, health, errors, intent) without human interpretation
3. Provide the infrastructure layer that james consumes via subprocess/CLI

## Scope

### In Scope
- Enhanced JSONL parsing to capture currently-ignored entry types
- Conversation state extraction (phase detection, error/stuck analysis, intent summary)
- New CLI tool (`understand.py`) exposing structured conversation state
- Schema additions for new data (compression events, progress entries)
- Test suite using mobile-terminal corpus (61 transcripts, 232MB)

### Out of Scope
- The monitoring agent itself (lives in james `src/agent/`)
- Telegram notifications or UI
- Real-time streaming (batch/poll is sufficient for v1)
- Subagent transcript ingestion (separate, smaller effort)
- Natural language summaries (LLM-powered summarization is a future enhancement)

---

## Functional Requirements

### FR-1: Enhanced JSONL Parsing
Parse entry types currently ignored by `parser.py`:

- **FR-1a:** `progress` entries — extract `bash_progress` (command output streaming), `agent_progress` (subagent lifecycle events)
- **FR-1b:** `system.compact_boundary` — extract compression events with timestamps
- **FR-1c:** `file-history-snapshot` — extract file modification tracking data

### FR-2: Schema Extensions
Add database support for newly parsed data:

- **FR-2a:** New `claude_events` table for compression events, or additional columns on `claude_sessions`
- **FR-2b:** Session-level compression count and last compression timestamp
- **FR-2c:** Preserve backward compatibility — existing queries must not break

### FR-3: Conversation State Extraction
A function/CLI that analyzes a session and returns structured state:

- **FR-3a:** **Phase detection** — classify conversation into: setup, research, planning, implementation, debugging, review, idle/waiting. Based on tool call patterns and message content heuristics (not LLM inference).
- **FR-3b:** **Health indicators** — error rate (recent tool failures), retry loops (same tool+input repeated), permission blocks, idle time since last message
- **FR-3c:** **Context pressure** — current context size, compression count, estimated turns remaining (leverage existing gauge.py logic)
- **FR-3d:** **Activity summary** — files touched (read/edited/created), tools used (with counts), commands run (bash)
- **FR-3e:** **Intent extraction** — first human message + most recent human message as proxy for task intent (simple, no LLM)

### FR-4: CLI Interface
New CLI tool exposing conversation state:

- **FR-4a:** `python3 understand.py <session-id>` — human-readable state output
- **FR-4b:** `python3 understand.py <session-id> --json` — machine-readable JSON output for meta-agent consumption
- **FR-4c:** `python3 understand.py --all --json` — all active sessions (modified in last 24h)
- **FR-4d:** `python3 understand.py --file <path.jsonl>` — analyze a JSONL file directly (for testing)

### FR-5: Test Coverage
- **FR-5a:** Unit tests for enhanced parsing (progress, compact_boundary, file-history-snapshot)
- **FR-5b:** Unit tests for phase detection heuristics
- **FR-5c:** Integration test against mobile-terminal corpus — parse all 61 transcripts, verify state extraction produces valid output
- **FR-5d:** Regression tests ensuring existing parser behavior unchanged

---

## Acceptance Criteria

- **AC-1:** `parser.py` extracts compression events from JSONL files containing `compact_boundary` entries
- **AC-2:** `understand.py <session-id> --json` returns valid JSON with fields: `phase`, `health`, `context`, `activity`, `intent`
- **AC-3:** Phase detection correctly classifies at least 3 distinct phases across the mobile-terminal corpus
- **AC-4:** Health indicators detect error loops when a tool fails 3+ times consecutively
- **AC-5:** Context pressure metrics match `gauge.py` output for the same session
- **AC-6:** All 61 mobile-terminal transcripts parse without errors
- **AC-7:** Existing `search.py`, `gauge.py`, `session.py` functionality unaffected
- **AC-8:** `--json` output is stable enough for james to consume via subprocess

---

## Non-Functional Requirements

- **NFR-1:** Parsing a 21MB JSONL file completes in under 5 seconds
- **NFR-2:** No new Python dependencies beyond psycopg2-binary
- **NFR-3:** CLI follows existing patterns (same arg style as search.py, gauge.py)

---

## Resolved Decisions

1. **Compression events** → Columns on `claude_sessions` (`compression_count`, `last_compressed_at`). Simple, sufficient for v1.
2. **Progress entries** → Parse agent spawning events only. Skip bash output (53% of JSONL, not useful for monitoring). Do NOT store in database — analyze from JSONL at query time.
3. **Phase detection** → Rule-based heuristics on tool call patterns. Deterministic and testable.
4. **Context pressure** → Import `gauge.py` functions directly (`extract_usage`, `compute_metrics`). Do not reimplement.
