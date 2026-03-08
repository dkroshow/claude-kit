# Plan: Context Gauge

**Status:** Draft
**Created:** 2026-03-07

---

## TL;DR

Standalone Python script (`conversation-logger/clogs/gauge.py`) that reads the current session's JSONL transcript and reports context window utilization. No DB required — reads the JSONL file directly. Auto-detects current session via CWD → project slug → newest `.jsonl`. Computes: current context size, remaining capacity, burn rate, estimated turns remaining. Two phases: core gauge logic, then documentation/integration.

---

## Source Documents
- **Spec:** `.project/active/context-gauge/spec.md`

## Research Findings

### Files Analyzed
- `conversation-logger/clogs/parser.py:1-304` — JSONL parsing, usage extraction from `message.usage` block
- `conversation-logger/clogs/search.py:1-290` — CLI patterns (argparse, formatters), analytics queries
- `conversation-logger/hooks/on-assistant-turn.sh` — CWD-to-slug mapping: `sed "s|$HOME/||; s|/|-|g; s|^|-|"`
- 1,502 transcripts analyzed for compression thresholds

### Reusable Patterns
- CWD → project slug derivation (from hooks, deterministic)
- `_fmt_tokens()` in `search.py:184` for human-readable token formatting
- JSONL line-by-line parsing pattern from `parser.py:146-164`

### Integration Points
- Standalone — no integration with existing modules needed
- Future meta-agent will call via `python3 gauge.py [--json]`
- Could be invoked from hooks, rules, or agent prompts

### Empirical Data (from research phase)
- **Compression threshold**: median 165K, hard ceiling 170K (0 sessions exceeded 170K)
- **Post-compression**: drops to ~30-43K tokens
- **Default threshold**: 165,000 tokens (conservative, covers majority of compression events)
- **Context formula**: `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`

## Design Decisions

### Decision 1: Standalone script vs search.py integration
**Context:** Could add a `gauge` subcommand to search.py or create a new file
**Options:** Add to search.py | New standalone script
**Chosen:** New standalone script `gauge.py`
**Rationale:** search.py is DB-focused; gauge.py reads JSONL directly with no DB dependency. Different data source, different concern. Keeps both simple.

### Decision 2: JSONL-only vs DB-backed
**Context:** Token data exists in both JSONL (live) and PostgreSQL (after ingestion)
**Options:** Read from DB | Read from JSONL file
**Chosen:** Read from JSONL file directly
**Rationale:** JSONL is written live during the session. DB ingestion happens on hooks (after each turn), so there's a lag. JSONL is always available, even if DB is down. No dependency on PostgreSQL.

### Decision 3: Burn rate calculation window
**Context:** Need to estimate tokens/turn for projection. Could use all turns or a sliding window.
**Options:** All turns | Last N turns | Weighted recent
**Chosen:** Last 10 turns (configurable)
**Rationale:** Recent burn rate is more predictive than session average. Early turns (system prompt setup) inflate the average. 10 turns gives a stable signal without too much lag.

## Technical Design

### Architecture Overview

```
gauge.py (standalone CLI)
  ├── find_current_transcript(cwd)  → JSONL path
  │     └── CWD → slug → newest .jsonl in ~/.claude/projects/<slug>/
  ├── extract_usage(jsonl_path)     → list of usage records
  │     └── Scan JSONL for assistant entries with message.usage
  └── compute_metrics(usage_data)   → metrics dict
        └── Current size, remaining, burn rate, turns estimate
```

### Component: `find_current_transcript(cwd)`
**Purpose:** Auto-detect current session's JSONL file
**Location:** `conversation-logger/clogs/gauge.py`
**Key interface:**
```python
def find_current_transcript(cwd: str = None) -> str:
    """Returns path to newest JSONL in the project dir for given CWD."""
```
**Algorithm:**
1. `cwd` defaults to `os.getcwd()`
2. Derive slug: replace `$HOME/` prefix, replace `/` with `-`, prepend `-`
3. Glob `~/.claude/projects/<slug>/*.jsonl`
4. Return newest by mtime

### Component: `extract_usage(jsonl_path)`
**Purpose:** Parse JSONL and extract per-turn usage data
**Location:** `conversation-logger/clogs/gauge.py`
**Key interface:**
```python
def extract_usage(jsonl_path: str) -> list[dict]:
    """Returns list of {total_input, output, timestamp} per assistant turn."""
```
**Logic:** Read line-by-line, parse JSON, filter `type == "assistant"`, extract `message.usage` fields, compute `total_input = input_tokens + cache_read + cache_creation`.

### Component: `compute_metrics(usage_data, threshold)`
**Purpose:** Compute context gauge metrics
**Location:** `conversation-logger/clogs/gauge.py`
**Key interface:**
```python
def compute_metrics(usage_data: list[dict], threshold: int = 165000) -> dict:
    """Returns dict with current_size, remaining, pct_used, burn_rate, est_turns_remaining."""
```
**Metrics:**
- `current_size`: last entry's `total_input`
- `remaining`: `threshold - current_size`
- `pct_used`: `current_size / threshold * 100`
- `burn_rate`: average delta in `total_input` over last 10 data points
- `est_turns_remaining`: `remaining / burn_rate` (if burn_rate > 0)
- `total_turns`: count of usage data points
- `compression_detected`: True if any `total_input[i] < total_input[i-1] - 1000`

### CLI Interface
```
python3 gauge.py                    # auto-detect, human output
python3 gauge.py --json             # machine-parseable
python3 gauge.py --file <path>      # explicit JSONL path
python3 gauge.py --threshold 150000 # custom threshold
```

### Output Format (human-readable)
```
Context: 46,575 / 165,000 tokens (28.2%)
Remaining: 118,425 tokens
Burn rate: ~850 tokens/turn (last 10 turns)
Est. turns remaining: ~139
Session: e10006d3-c5d5-4ff9-a57c-ea06b1f417a1
Turns: 35
```

### Output Format (JSON)
```json
{
  "current_size": 46575,
  "threshold": 165000,
  "remaining": 118425,
  "pct_used": 28.2,
  "burn_rate": 850,
  "est_turns_remaining": 139,
  "total_turns": 35,
  "compression_detected": false,
  "session_id": "e10006d3-...",
  "transcript_path": "/Users/kd/.claude/projects/..."
}
```

### Error Handling
- No JSONL found: "No transcript found for project directory: {cwd}" + exit 1
- JSONL has no assistant messages: "No usage data in transcript" + exit 1
- Malformed JSON lines: skip silently (same as parser.py)

---

## Implementation Strategy

### Phasing Rationale
Phase 1 is the entire utility — it's small enough for one phase. Phase 2 adds documentation so sessions know the tool exists.

### Phase 1: Core Gauge Utility
#### Goal
Working CLI that reports context metrics from JSONL.
#### Test Approach
Reference: AC-1 through AC-7
Manual testing against live session JSONL.
#### Changes Required
- [ ] Create `conversation-logger/clogs/gauge.py`: `find_current_transcript()`, `extract_usage()`, `compute_metrics()`, CLI with argparse
#### Validation
**Manual:**
- [ ] `python3 gauge.py` auto-detects current session and reports metrics (AC-1, AC-3)
- [ ] `python3 gauge.py --json` outputs valid JSON (AC-4)
- [ ] `python3 gauge.py --file <path>` works with explicit path (AC-5)
- [ ] Handles empty/no-data gracefully (AC-6)
- [ ] Post-compression session shows current (not peak) context size (AC-7)

### Phase 2: Documentation & Integration
#### Goal
Make the gauge discoverable to future sessions and the meta-agent.
#### Changes Required
- [ ] Update `rules/conversation-history.md`: add gauge CLI reference
- [ ] Update `.project/CURRENT_WORK.md`: record completion
#### Validation
- [ ] Rule file contains correct gauge CLI path and usage examples

---

## Risk Management
- **Newest-file heuristic**: Could pick wrong session if multiple are active simultaneously. Acceptable risk — explicit `--file` flag is the escape hatch.
- **Burn rate noise**: Short sessions or large tool results can skew the average. Mitigated by using last-10-turn window instead of session average.

---

## Implementation Notes

### Phase 1 Completion
**Completed:** 2026-03-07
**Changes Made:**
- Created `conversation-logger/clogs/gauge.py` with `find_current_transcript()`, `extract_usage()`, `compute_metrics()`, and argparse CLI

**Per-Phase Audit:**
- Completion Accuracy: All items complete, no placeholders
- Deviations: Slug derivation bug — initial version stripped HOME prefix before replacing `/` with `-`. Actual Claude Code slugs use the full absolute path (e.g., `/Users/kd/claude-kit` → `-Users-kd-claude-kit`). Fixed during implementation.
- Test Coverage: All 7 ACs validated manually against live transcripts

**Issues Encountered:**
- Slug derivation: The hook's fallback `sed` command (`s|$HOME/||`) differs from Claude Code's actual slug generation. Claude Code uses the full path. Fixed to match actual directory names.

### Phase 2 Completion
**Completed:** 2026-03-07
**Changes Made:**
- Updated `rules/conversation-history.md` with gauge CLI reference
- Updated `.project/CURRENT_WORK.md` with completion record and session notes

---

**Status**: Complete
