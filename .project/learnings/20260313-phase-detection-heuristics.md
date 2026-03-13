---
type: pattern
tags: conversation-understanding, phase-detection, meta-agent, heuristics
created: 2026-03-13
---

# CC Conversation Phase Detection: What Works and What Doesn't

## What
Validated phase detection heuristics against 61 real Claude Code transcripts (232MB, mobile-terminal project). Real sessions are iterative loops, not linear pipelines.

## What Didn't Work
- **7-phase model** (setup, research, planning, implementation, debugging, review, idle) — too granular. Setup and research are indistinguishable (both Read/Grep/Glob). Debugging had zero error-retry sequences in 4 tested transcripts. Review (git/commit) was never observed.
- **Linear pipeline assumption** — sessions bounce between phases rapidly (57-82% of turns involve phase transitions). A session doing "explore → implement → explore → implement" is the norm.
- **Idle detection for historical analysis** — every completed session looks "idle" if you check wall-clock time. Must separate live monitoring (check time) from historical analysis (check tool patterns).

## What Works
- **4-phase model**: exploration (Read/Grep/Glob >60%), planning (Skill/TaskCreate >=2), implementation (Edit/Write/Bash >50%), idle (>5min gap, live only)
- **Sliding window** (last 20 messages): captures current activity, not session-level average
- **`live` parameter**: callers specify whether session is active. `--all` mode sets `live=True`; `--file` sets `live=False`.
- **"unknown" fallback**: Bash-heavy sessions without Edit/Write don't match any phase cleanly. Return `{"current": "unknown", "confidence": "low"}` rather than force-fitting.

## Key Files
- `conversation-logger/clogs/conversation_state.py` — detect_phase(), assess_health(), summarize_activity(), extract_intent()
- `conversation-logger/clogs/understand.py` — CLI interface
- `.project/active/conversation-understanding/spec.md` — requirements
- `.project/active/conversation-understanding/plan.md` — plan with audit findings
