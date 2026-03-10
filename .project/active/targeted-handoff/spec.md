# Spec: Targeted Session Handoff

**Status:** Draft
**Created:** 2026-03-10
**Complexity:** LOW

---

## TL;DR

CURRENT_WORK.md accumulates session notes from multiple parallel work streams. When `/_wrapup --blurb` or `/_blurb` generates a reload blurb, it tells the new Claude to read CURRENT_WORK.md — loading all streams into context regardless of relevance. Fix this by writing a targeted handoff file (`.project/handoffs/{feature-slug}.md`) containing only the active stream's context, and pointing the blurb at that specific file. The new session reads it and deletes it. Multiple concurrent sessions can each write their own handoff file without collision.

---

## Business Goals

### Why This Matters

Context window tokens are a finite resource (~165K before compression). Loading irrelevant session notes from other work streams wastes tokens that could be used for actual work. As projects accumulate history, CURRENT_WORK.md grows and the waste compounds.

### Success Criteria

- [ ] New sessions load only the context relevant to their work stream
- [ ] Context handoff stays compact (targeted file < 50 lines)
- [ ] CURRENT_WORK.md continues to work as a project-wide index unchanged

---

## Problem Statement

### Current State

`/_wrapup --blurb` and `/_blurb` generate a reload blurb that says "Read `.project/CURRENT_WORK.md`". CURRENT_WORK.md contains active items, recently completed items, up-next priorities, and session notes from the last 3 sessions — potentially across unrelated work streams. The new Claude reads all of it.

### Desired Outcome

The blurb points to a targeted handoff file that contains only the context the next session needs for the specific work stream being handed off. The new session reads the handoff file, deletes it, and optionally reads CURRENT_WORK.md only if it needs broader project context.

---

## Scope

### In Scope

- Writing a targeted handoff file during `/_wrapup --blurb` and `/_blurb`
- Updating blurb template to point at the handoff file instead of CURRENT_WORK.md
- Instruction for the new session to delete the handoff file after reading
- Updating `context-loading.md` so the handoff file takes precedence over CURRENT_WORK.md when present

### Out of Scope

- Restructuring CURRENT_WORK.md format
- Changing how `/_wrapup` writes session notes
- New infrastructure or tooling

### Edge Cases & Considerations

- Session not mid-flow on any feature (between-features handoff) — handoff file uses a generic slug (e.g., `general.md`), contains just status + what's up next
- Handoff file left behind if new session forgets to delete — harmless; next wrapup for the same stream overwrites it, and stale files in `handoffs/` can be pruned periodically
- Multiple concurrent sessions — each writes its own file keyed by feature slug, no collision

---

## Requirements

### Functional Requirements

1. **FR-1**: `/_wrapup --blurb` writes `.project/handoffs/{feature-slug}.md` containing only the context relevant to the current work stream (what was worked on, current status, key decisions, gotchas)
2. **FR-2**: The blurb template points to the specific handoff file instead of `CURRENT_WORK.md` as the primary context source
3. **FR-3**: The blurb instructs the new session to delete the handoff file after reading
4. **FR-4**: `/_blurb` standalone writes the same handoff file
5. **FR-5**: [INFERRED] `context-loading.md` updated so that when a handoff file exists and is referenced by the blurb, the new session reads it instead of CURRENT_WORK.md
6. **FR-6**: [INFERRED] CURRENT_WORK.md referenced in blurb with gating language: "Only read if you're clearly missing project context not covered above"

---

## Acceptance Criteria

### Core Functionality

- [ ] **AC-1** (FR-1): **Given** a session that worked on feature X, **when** `/_wrapup --blurb` runs, **then** `.project/handoffs/{feature-slug}.md` is written containing only feature X context (not other streams' session notes)
- [ ] **AC-2** (FR-2): **Given** a generated blurb, **when** the blurb is read, **then** it points to the specific handoff file as primary context
- [ ] **AC-3** (FR-3): **Given** a generated blurb, **when** the blurb is read, **then** it includes an instruction to delete the handoff file after reading
- [ ] **AC-4** (FR-4): **Given** `/_blurb` is run standalone, **when** it completes, **then** it produces the same handoff file and blurb format as `/_wrapup --blurb`
- [ ] **AC-5** (FR-5): **Given** a handoff file referenced by the blurb exists, **when** a new session starts, **then** it reads the handoff file instead of CURRENT_WORK.md
- [ ] **AC-6** (FR-6): **Given** a generated blurb, **when** CURRENT_WORK.md is referenced, **then** it's gated with "only read if you're clearly missing project context"

---

## Related Artifacts

- **Plan:** `.project/active/targeted-handoff/plan.md` (to be created)

---

**Next Steps:** After approval, proceed to plan.
