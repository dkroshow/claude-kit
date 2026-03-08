---
type: pattern
tags: context-window, compression, tokens, gauge, meta-agent
created: 2026-03-07
---

# Context Window Compression Thresholds

## What

Claude Code automatically compresses conversation context when the context window fills. Empirical analysis of 1,502 transcripts reveals consistent compression behavior with predictable thresholds.

## Context

Analyzed all JSONL transcripts across all projects to understand compression patterns. Found 57 compression events. Each assistant message in JSONL contains a `usage` block — total context size = `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`.

## Key Numbers

| Metric | Value |
|---|---|
| Hard ceiling | ~170K tokens (0 sessions exceeded this) |
| Median compression trigger | ~165K tokens |
| Post-compression size | ~30-43K tokens |
| Typical drop | ~120-130K tokens |
| Context growth | Varies widely, ~100-1400 tokens/turn typical |

## What Works

- **Default threshold of 165K** is a good conservative estimate for when compression will trigger
- **Last N turns burn rate** (not session average) is more predictive — early turns inflate the average due to system prompt setup
- **Compression detection**: any turn where `total_input[i] < total_input[i-1] - 1000` indicates a compression event
- **JSONL is the reliable data source** — written live during session, no DB dependency needed

## Project Slug Derivation

Claude Code's project slug is the **full absolute path** with `/` replaced by `-`:
- `/Users/kd/claude-kit` → `-Users-kd-claude-kit`
- NOT relative to HOME (the hook's fallback `sed` command strips HOME, but Claude Code itself uses the full path)

## Key Files

- `conversation-logger/clogs/gauge.py` — context gauge utility
- `.project/active/context-gauge/spec.md` — requirements
- `.project/active/context-gauge/plan.md` — design and implementation notes
