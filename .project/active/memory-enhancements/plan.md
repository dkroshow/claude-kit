# Plan: Memory System Enhancements

**Status:** Draft
**Created:** 2026-03-05
**Last Updated:** 2026-03-05

---

## TL;DR

Enhance the memory system across 3 phases: (1) create project templates for file-knowledge index and trigger tables, (2) add staleness detection, index maintenance, symptom-cause-fix format, and agent creation guidance to `/_wrapup`, (3) add knowledge gap detection to the memory agent and trigger table reference to context-loading. All changes are markdown instruction files — no executable code beyond an `init.sh` update. 3 phases, ~7 files touched.

---

## Source Documents
- **Spec:** `.project/active/memory-enhancements/spec.md`

## Research Findings

### Files Analyzed
- `commands/_wrapup.md` (151 lines) — 7-step wrapup flow, Step 3 handles learning capture with template
- `agents/memory.md` (57 lines) — memory retrieval agent with 3-section output format
- `rules/context-loading.md` (52 lines) — 4-step decision tree + retrieval tiers
- `project-template/` — 6 existing template files (CURRENT_WORK.md, learnings/index.md, etc.)
- `init.sh` (217 lines) — template copier with USER_DATA_FILES protection list
- `commands/_implement.md` — references learning checks in Stage 0 (pattern to maintain)

### Reusable Patterns
- Learning template at `_wrapup.md:48-72` — existing YAML frontmatter + sections format we extend
- `init.sh:76-81` USER_DATA_FILES array — pattern for protecting user data files from `--force` overwrites
- Memory agent output format at `memory.md:38-48` — 3-section structure we add a 4th section to
- Context-loading decision tree at `context-loading.md:12-29` — step-based format we insert into

### Integration Points
- `_wrapup.md` Step 1 already runs `git diff --stat` — staleness check reuses this git data
- Learning template's `## Key Files` section is already defined — file-knowledge index derives from it
- `--quick` flag skips to Steps 2 and 5 — new staleness step must respect this

## Design Decisions

### Decision 1: Wrapup Step Ordering
**Context:** Adding staleness detection to wrapup requires choosing where in the flow it goes.
**Options:**
1. New Step 3 between "Update CURRENT_WORK.md" and "Capture Learnings" (renumber downstream)
2. Fold into existing Step 1 (Review What Changed)
3. Fold into Step 3 (Capture Learnings)

**Chosen:** Option 1 — new dedicated Step 3
**Rationale:** Staleness is a distinct concern from reviewing changes or capturing learnings. It needs to happen AFTER we know what files changed (Step 1) but BEFORE we capture new learnings (old Step 3), because stale artifacts might need updating first. A dedicated step keeps the wrapup flow clean and each step single-purpose. Renumbering is safe — no other commands reference wrapup steps by number.

### Decision 2: File-Knowledge Index as User Data
**Context:** Should `init.sh --force` overwrite the file-knowledge-map.md?
**Chosen:** Protect it as user data (add to USER_DATA_FILES)
**Rationale:** Like `learnings/index.md`, the file-knowledge map accumulates project-specific data over time. Overwriting it would lose the staleness tracking history.

---

## Technical Design

### Architecture Overview

```
Project Templates (Phase 1)          Wrapup Enhancements (Phase 2)
┌─────────────────────────┐          ┌────────────────────────────┐
│ file-knowledge-map.md   │◄─────────│ Step 3: Staleness Check    │
│ trigger-table.md        │          │ Step 4: Index Maintenance   │
│ init.sh update          │          │ Step 4: SCF Format Option   │
└─────────────────────────┘          │ Step 4: Agent Creation      │
                                     └────────────────────────────┘
Memory & Context (Phase 3)
┌─────────────────────────┐
│ memory.md: Gap Detection │
│ context-loading: Triggers │
└─────────────────────────┘
```

All changes are to markdown instruction files consumed by Claude. No shell scripts, no executable code beyond adding 1 line to `init.sh`.

### Wrapup New Step Ordering
- Step 1: Review What Changed (existing, unchanged)
- Step 2: Update CURRENT_WORK.md (existing, unchanged)
- **Step 3: Check Knowledge Staleness (NEW)**
- Step 4: Capture Learnings (was Step 3, enhanced with index maintenance + SCF format + agent creation guidance)
- Step 5: Update Docs (was Step 4, unchanged)
- Step 6: Report (was Step 5, enhanced to include staleness findings)
- Step 7: Commit (was Step 6, unchanged)
- Step 8: Generate Reload Blurb (was Step 7, unchanged)

`--quick` mode: Steps 1, 2, 6, 7 only (skips Steps 3-5, same as before but renumbered)

### Error Handling
- Missing file-knowledge-map.md → staleness check skipped silently
- Missing trigger-table.md → context-loading trigger check skipped silently
- Empty learnings indexes → memory agent reports clearly, adds knowledge gap flag

---

## Implementation Strategy

### Phasing Rationale

Phase 1 creates the template artifacts that Phase 2's wrapup instructions reference. Phase 3 is independent lightweight changes to supporting files. This order ensures we never reference files that don't have defined formats yet.

### Overall Validation Approach
- Each phase: manually review the markdown for clarity, consistency, and no broken references
- After all phases: read through the complete wrapup flow end-to-end to ensure coherence
- Verify backward compatibility: check that missing new files don't break existing flows

### Phase 1: Project Templates
#### Goal
Create the two new template files and protect the index in init.sh. These define the formats that wrapup will use.

#### Test Approach
Reference: spec.md AC-5, AC-8

#### Changes Required
- [x] Create `project-template/file-knowledge-map.md` with header, format docs, and empty table (FR-1, FR-15)
- [x] Create `project-template/trigger-table.md` with header, format docs, and example entries (FR-10, FR-11, FR-16)
- [x] Update `init.sh:76-81` — add `file-knowledge-map.md` to USER_DATA_FILES array (Design Decision 2)

#### Validation
**Manual:**
- [x]Template files have clear format documentation and match spec examples
- [x]`init.sh --dry-run` would show new files being copied
- [x]`file-knowledge-map.md` is in the protected list

**What We Know Works:** Template formats are defined and protected from overwrite.

### Phase 2: Wrapup Command Enhancements
#### Goal
The core change — add staleness detection, index maintenance, symptom-cause-fix format, and agent creation guidance to `/_wrapup`. This is the largest phase.

#### Test Approach
Reference: spec.md AC-1 through AC-6, AC-10, AC-11

#### Changes Required
- [x]Add new Step 3 "Check Knowledge Staleness" to `commands/_wrapup.md` — cross-reference session's changed files against file-knowledge index, flag stale artifacts, offer to update or re-verify (FR-2, FR-3, FR-4, FR-5, FR-6)
- [x]Enhance Step 4 (was Step 3) learning capture — after creating a learning with `## Key Files`, update `file-knowledge-map.md` with entries mapping those files to the learning (FR-7)
- [x]Add orphan cleanup to Step 4 — check index for entries pointing to deleted learnings, remove them (FR-8)
- [x]Add symptom-cause-fix table format option to Step 4 gotcha template — "For gotchas with multiple failure modes, use the table format instead" (FR-14)
- [x]Add agent creation guidance to end of Step 4 — "If this session involved extended debugging (3+ hypothesis-test-fail cycles), suggest creating a domain-expert agent" (FR-13)
- [x]Update Step 6 (was Step 5) report to include staleness findings
- [x]Update `--quick` skip logic for new step numbers
- [x]Update `--blurb` step reference for new numbering
- [x]Update Last Updated date

#### Validation
**Manual:**
- [x]Read through entire wrapup flow end-to-end — is it coherent and not too long?
- [x]Verify `--quick` mode still skips correctly with new numbering
- [x]Verify `--blurb` reference is correct
- [x]Staleness check gracefully handles missing index
- [x]Learning capture includes index maintenance instructions
- [x]SCF format is clearly presented as optional, not forced

**What We Know Works:** Wrapup captures staleness, maintains the index, offers structured debugging format, and suggests agent creation when appropriate.

### Phase 3: Memory Agent & Context Loading
#### Goal
Lightweight updates: add knowledge gap detection to memory agent output and trigger table reference to context-loading.

#### Test Approach
Reference: spec.md AC-7, AC-9

#### Changes Required
- [x]Update `agents/memory.md` output section — add knowledge gap flag when nothing relevant is found (FR-12)
- [x]Update `rules/context-loading.md` — add trigger table reference to the decision tree, between Steps 2-3 (FR-9)

#### Validation
**Manual:**
- [x]Memory agent output format is clear with 4th section for gaps
- [x]Context-loading trigger table reference is conditional ("if exists")
- [x]Existing flows still work when trigger-table.md doesn't exist

**What We Know Works:** Memory agent flags knowledge gaps. Context-loading suggests relevant agents/specs when trigger table exists.

---

## Risk Management

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Wrapup becomes too verbose | Medium | Medium | Keep additions concise, use "if applicable" guards, don't repeat format docs inline |
| File-knowledge index gets stale from manual learning edits | Low | Low | Document that index is maintained by wrapup; manual edits may need manual index updates |
| Trigger table format unclear to users | Low | Low | Include concrete example entries in template |
| Step renumbering causes confusion | Low | Low | No other commands reference wrapup steps by number — verified |

---

## Implementation Notes

### Phase 1 Completion
**Completed:** 2026-03-05

**Changes Made:**
- Created `project-template/file-knowledge-map.md` — empty index with format docs
- Created `project-template/trigger-table.md` — template with format docs and example row
- Updated `init.sh` — added `file-knowledge-map.md` and `trigger-table.md` to USER_DATA_FILES array, updated help text

**Per-Phase Audit:**
- Completion Accuracy: All items complete
- Deviations: Also protected trigger-table.md as user data (not in original plan but same rationale)
- Test Coverage: Manual review — formats match spec examples, init.sh protection works

### Phase 2 Completion
**Completed:** 2026-03-05

**Changes Made:**
- Rewrote `commands/_wrapup.md` — added Step 3 (staleness check), enhanced Step 4 (index maintenance, SCF format, orphan cleanup, agent creation guidance), renumbered Steps 5-8, updated report format, updated --quick and --blurb references

**Per-Phase Audit:**
- Completion Accuracy: All items complete
- Deviations: None — followed plan exactly
- Test Coverage: Full read-through of wrapup flow, verified no other commands reference wrapup steps by number, verified --quick and --blurb references correct

### Phase 3 Completion
**Completed:** 2026-03-05

**Changes Made:**
- Updated `agents/memory.md` — added Knowledge Gap section to output format when no relevant learnings found
- Updated `rules/context-loading.md` — added trigger table reference to Step 3 of decision tree, conditional on file existence

**Per-Phase Audit:**
- Completion Accuracy: All items complete
- Deviations: Placed trigger table check in Step 3 (specific component/file) rather than as a standalone step — more natural since trigger tables are file-pattern-based
- Test Coverage: Manual review — conditional "if it exists" phrasing ensures backward compatibility

---

**Status**: Complete
