# Plan: Targeted Session Handoff

**Status:** Complete
**Created:** 2026-03-10
**Last Updated:** 2026-03-10

---

## TL;DR

Replace the blurb's "read CURRENT_WORK.md" pattern with targeted handoff files. When `/_wrapup --blurb` or `/_blurb` runs, it writes `.project/handoffs/{feature-slug}.md` with only the current stream's context, then generates a blurb pointing to that file. Update `context-loading.md` to prefer handoff files when present. 2 phases: handoff file generation, then context-loading integration.

---

## Source Documents
- **Spec:** `.project/active/targeted-handoff/spec.md`

## Research Findings

### Files to Modify
- `commands/_wrapup.md:222-252` — Step 8 (Generate Reload Blurb), blurb template
- `commands/_blurb.md:1-75` — Standalone blurb command, same template
- `rules/context-loading.md:1-5` — "Before Starting Non-Trivial Work" section

### Reusable Patterns
- Both `_wrapup.md` Step 8 and `_blurb.md` share nearly identical blurb templates — keep them in sync
- Feature slug convention already exists in `.project/active/{feature-name}/` directories

### Integration Points
- `context-loading.md` is loaded as a global rule into every session — changes here affect all projects
- `_wrapup.md` Step 7 commits files — handoff files in `.project/handoffs/` will be committed too (acceptable, they're small and self-cleaning)

## Design Decisions

### Decision 1: Handoff file naming
**Context:** Need unique names per work stream to avoid collision between concurrent sessions.
**Options:** timestamp-based (`SESSION_HANDOFF_20260310.md`), feature-slug-based (`{feature-slug}.md`), UUID-based
**Chosen:** Feature-slug-based
**Rationale:** Readable, predictable, matches existing `.project/active/` naming. For between-features sessions, use `general.md`.

### Decision 2: Handoff file location
**Context:** Where to put handoff files.
**Options:** `.project/` root, `.project/handoffs/` subdirectory
**Chosen:** `.project/handoffs/`
**Rationale:** Keeps `.project/` root clean, allows multiple handoff files to coexist, easy to glob for cleanup.

---

## Implementation Strategy

### Phasing Rationale
Phase 1 does the core work (handoff file + blurb templates). Phase 2 updates the context-loading rule. Separated because Phase 1 is self-contained and testable on its own.

### Phase 1: Handoff File Generation + Blurb Templates
#### Goal
Update `_wrapup.md` and `_blurb.md` to write a handoff file and point the blurb at it.

#### Test Approach
Manual: run `/_wrapup --blurb` and `/_blurb` and verify output. Reference: AC-1, AC-2, AC-3, AC-4, AC-6.

#### Changes Required
- [ ] `commands/_wrapup.md`: Update Step 8 — add handoff file writing substep before blurb composition, update blurb template
- [ ] `commands/_blurb.md`: Add handoff file writing step, update blurb template to match
- [ ] Both: Define handoff file content template (what goes in, what stays out)

#### Validation
**Manual:**
- [ ] Blurb template references specific handoff file path
- [ ] Blurb includes "delete after reading" instruction
- [ ] Blurb gates CURRENT_WORK.md with "only read if missing context"
- [ ] Handoff file template is scoped to current stream only

### Phase 2: Context-Loading Integration
#### Goal
Update `context-loading.md` so new sessions that start from a blurb use the handoff file instead of CURRENT_WORK.md.

#### Test Approach
Manual: verify rule text. Reference: AC-5.

#### Changes Required
- [ ] `rules/context-loading.md`: Update "Before Starting Non-Trivial Work" to check for handoff files first

#### Validation
**Manual:**
- [ ] Rule prioritizes handoff file when present
- [ ] CURRENT_WORK.md read is gated (not automatic when handoff exists)

---

## Implementation Notes

### Phase 1 Completion
**Completed:** 2026-03-10
**Changes Made:**
- Modified `commands/_wrapup.md:234-319` — rewrote Step 8 with substeps 8a-8e: gather context, write handoff file, compose blurb, rules, output
- Rewrote `commands/_blurb.md` — added Step 2 (Write Handoff File) before blurb composition, updated templates

**Per-Phase Audit:**
- Completion Accuracy: All items complete. Both files have identical handoff file template and blurb templates.
- Deviations: None.
- Test Coverage: Manual verification — templates are consistent between both commands.

### Phase 2 Completion
**Completed:** 2026-03-10
**Changes Made:**
- Modified `rules/context-loading.md:1-8` — added step 1 (check for handoff file), shifted CURRENT_WORK.md to step 2 with "only if no handoff" qualifier, renumbered remaining steps

**Per-Phase Audit:**
- Completion Accuracy: All items complete.
- Deviations: None.
- Test Coverage: Manual verification of rule text.
