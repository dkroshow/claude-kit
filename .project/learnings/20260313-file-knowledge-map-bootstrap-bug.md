---
type: gotcha
tags: [wrapup, staleness, file-knowledge-map, prompt-instructions]
created: 2026-03-13
---

# File-Knowledge-Map Staleness Check Always Reports "No Map"

## What

The `/_wrapup` Step 3 staleness check never actually ran in most projects — it always reported "no map" and skipped.

## Context

User noticed staleness feature consistently doing nothing across sessions. Traced through the wrapup instructions to find three compounding gaps.

## Symptoms & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| "No map" when file doesn't exist | Step 3 said "skip entirely" if file missing — no bootstrap path | Changed to create the file with standard header, then proceed to rebuild |
| "No map" when file exists but is empty | Rebuild only scanned `## Key Files` sections in learnings | Added fallback: scan learning bodies for file path references |
| Learnings never have `## Key Files` | Template marked it "if applicable" — Claudes rarely included it | Made Key Files a standard section with explicit instructions to always list files |

## Key Files

- commands/_wrapup.md
- .project/file-knowledge-map.md
- project-template/file-knowledge-map.md
