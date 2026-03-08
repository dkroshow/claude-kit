# Spec: Context Gauge

**Status:** Draft
**Created:** 2026-03-07
**Complexity:** LOW-MEDIUM

---

## TL;DR

Build a utility that reads the current Claude session's JSONL transcript and reports context window utilization metrics. Each assistant message in the JSONL contains a `usage` block with token counts — the sum of `input_tokens + cache_read_input_tokens + cache_creation_input_tokens` equals the total prompt size (context consumed) for that turn. Empirical analysis of 1,502 transcripts shows compression triggers at ~165K tokens (hard ceiling ~170K). The utility computes current size, remaining capacity, burn rate, and estimated turns until compression. Exposed as a CLI so any session or the future meta-agent can call it.

---

## Business Goals

### Why This Matters

Context compression in Claude Code is silent — when the context window fills (~165-170K tokens), the system automatically compresses prior messages, dropping ~120-130K tokens. This destroys working context without warning. A meta-agent needs to anticipate compression to trigger wrapups, persist state, or warn the user before context loss.

### Success Criteria

- [ ] Any session can check its own context utilization with a single CLI command
- [ ] Output is machine-parseable for meta-agent consumption AND human-readable
- [ ] Metrics are accurate (based on actual API usage data, not estimates)

### Priority

Prerequisite for meta-agent context management. Builds directly on the conversation logger infrastructure (which captures the token data).

---

## Problem Statement

### Current State

Token usage data is captured per-message in PostgreSQL and exists in live JSONL transcripts, but there's no way to query "how full is my current context window?" The data is there — it's just not surfaced.

### Desired Outcome

A CLI command that reports current context utilization with actionable metrics: how much is used, how much remains, how fast it's growing, and when compression will likely occur.

---

## Scope

### In Scope

- CLI utility to report context metrics for the current (or specified) session
- Current session detection (newest JSONL in project dir)
- Metrics: context size, remaining capacity, burn rate, estimated turns remaining
- Both human-readable and machine-parseable output (JSON flag)
- Configurable compression threshold (default from empirical data)

### Out of Scope

- Real-time monitoring / background daemon
- Automatic wrapup triggering (meta-agent responsibility)
- Modifications to conversation logger, hooks, or DB schema
- Embedding into Claude Code itself
- Historical analytics (already covered by search.py)

### Edge Cases & Considerations

- Session has no assistant messages yet (no usage data available)
- JSONL file is being actively written to (read what's there so far)
- Multiple project dirs — need to identify the right one
- Post-compression state: context drops then regrows — gauge should reflect current state, not peak

---

## Requirements

### Functional Requirements

1. **FR-1**: Report current context size (total input tokens from most recent assistant message)
2. **FR-2**: Report remaining capacity (threshold minus current size)
3. **FR-3**: Report burn rate (average tokens added per turn over recent N turns)
4. **FR-4**: Report estimated turns remaining before compression threshold
5. **FR-5**: Detect current session automatically (newest JSONL in project dir)
6. **FR-6**: Support `--json` flag for machine-parseable output
7. **FR-7**: [INFERRED] Accept explicit session path as alternative to auto-detection
8. **FR-8**: [INFERRED] Use empirical compression threshold of 165,000 tokens as default, allow override via `--threshold`

### Non-Functional Requirements

- Fast execution (reads single JSONL file, no DB required)
- No new dependencies beyond Python stdlib + existing clogs modules
- Standalone script — does not require PostgreSQL to be running

---

## Acceptance Criteria

### Core Functionality

- [ ] **AC-1** (FR-1, FR-2): **Given** an active session with assistant messages, **when** `context-gauge` is run, **then** it reports current context size and remaining capacity in tokens
- [ ] **AC-2** (FR-3, FR-4): **Given** a session with 5+ assistant turns, **when** `context-gauge` is run, **then** it reports burn rate and estimated turns remaining
- [ ] **AC-3** (FR-5): **Given** the user is in a project directory, **when** `context-gauge` is run without arguments, **then** it finds and reads the newest JSONL transcript for that project
- [ ] **AC-4** (FR-6): **Given** `--json` flag, **when** `context-gauge` is run, **then** output is valid JSON with all metrics as numeric fields
- [ ] **AC-5** (FR-7): **Given** an explicit JSONL path, **when** `context-gauge --file <path>` is run, **then** it uses that file instead of auto-detection

### Edge Cases

- [ ] **AC-6**: **Given** a session with no assistant messages, **when** `context-gauge` is run, **then** it reports "no usage data" gracefully
- [ ] **AC-7**: **Given** a post-compression session, **when** `context-gauge` is run, **then** it reports current (post-drop) context size, not the pre-compression peak

### Quality & Integration

- [ ] Existing tests continue to pass
- [ ] No new dependencies added

---

## Related Artifacts

- **Research:** Empirical analysis performed in conversation (1,502 transcripts, 57 compression events)
- **Plan:** `.project/active/context-gauge/plan.md` (to be created)
- **Depends on:** `conversation-logger/clogs/parser.py` (JSONL format knowledge)

---

**Next Steps:** After approval, proceed to plan.
