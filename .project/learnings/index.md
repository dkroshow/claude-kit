# Learning Index

> Scanned by Claude at session start for relevant prior knowledge.
> See individual files for full context.

| Date | Type | Tags | Summary | File |
|------|------|------|---------|------|
| 2026-03-06 | pattern | memory, staleness, wrapup, design-decision | Detect knowledge staleness at write time (wrapup) not read time (session start) | 20260306-staleness-at-write-time.md |
| 2026-03-07 | gotcha | conversation-logger, jsonl, postgresql, hooks, parser | JSONL streaming format, NUL bytes, async hook spam, content classification | 20260307-conversation-logger-implementation.md |
| 2026-03-07 | pattern | context-window, compression, tokens, gauge, meta-agent | Compression triggers at ~165K tokens, drops to ~30-43K; project slug = full path with / replaced by - | 20260307-context-window-compression.md |
| 2026-03-08 | gotcha | session-resolver, claude-code, lsof, tmux, process, macOS | Anchor UUIDs only in Claude ≤2.1.66; pgrep -P fails on macOS; slug-to-path reversal is ambiguous | 20260308-session-resolver-signals.md |
| 2026-03-13 | pattern | conversation-understanding, phase-detection, meta-agent, heuristics | Real CC sessions are iterative loops not pipelines; 4 validated phases (exploration, planning, implementation, idle); must separate live vs historical idle detection | 20260313-phase-detection-heuristics.md |
| 2026-03-13 | gotcha | wrapup, staleness, file-knowledge-map, prompt-instructions | Staleness check always reports "no map" — three compounding gaps: no bootstrap, narrow rebuild, optional Key Files | 20260313-file-knowledge-map-bootstrap-bug.md |
