---
type: pattern
tags: [memory, staleness, wrapup, design-decision]
created: 2026-03-06
---

# Staleness Detection: Write Time > Read Time

## What

Knowledge staleness should be detected at write time (during `/_wrapup`) rather than read time (session start). This catches stale artifacts when you're in context to fix them immediately, avoids session-start latency, and requires no shell scripts or hooks.

## Context

Considered a session-start hook (inspired by the "Codified Context" paper, arxiv 2602.20478) but rejected it: startup latency, complexity of shell script parsing, and the user isn't in context to fix stale artifacts when starting a new task. The wrapup already touches git and knowledge artifacts, making it the natural checkpoint.

## What Works

`/_wrapup` Step 3 cross-references `git diff --name-only` against `.project/file-knowledge-map.md`, flags stale artifacts, and prompts the user to update or re-verify them in the same session.

## Key Files

- commands/_wrapup.md
- .project/file-knowledge-map.md
- rules/context-loading.md
