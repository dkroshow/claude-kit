# Spec: Memory System Enhancements

**Status:** Implementation Complete
**Created:** 2026-03-03
**Complexity:** MEDIUM
**Informed by:** "Codified Context: Infrastructure for AI Agents in a Complex Codebase" (arxiv 2602.20478)

---

## TL;DR

Enhance claude-kit's memory system with proactive staleness detection and smarter retrieval. During `/_wrapup`, cross-reference the session's git changes against a file-to-knowledge index to flag learnings or docs that may be stale — catching staleness at write time when you're still in context to fix it. Supporting improvements add knowledge gap detection, file-pattern trigger tables for automatic agent/spec routing, structured debugging knowledge format, and reactive agent creation guidance.

---

## Business Goals

### Why This Matters

The memory system captures and retrieves knowledge well, but has gaps in two areas:
1. **Staleness** — outdated learnings/docs silently mislead. There's no mechanism to detect when source code has changed but covering knowledge artifacts haven't been updated.
2. **Surfacing** — retrieval is manual (decision tree requires the agent to decide). There's no automatic routing based on which files are being touched, no explicit signal when knowledge is missing for an area.

### Success Criteria

- [ ] Stale knowledge artifacts are flagged during `/_wrapup` when you're in context to fix them
- [ ] Zero noise when all knowledge artifacts are current
- [ ] Knowledge gaps are explicitly called out for substantive task areas
- [ ] File-pattern trigger tables route to relevant agents/specs automatically
- [ ] Debugging knowledge has a structured, scannable format option
- [ ] `/_wrapup` suggests agent creation after extended debugging sessions

### Priority

Medium — these are quality-of-life improvements to an existing system, not blockers.

---

## Problem Statement

### Current State

- No staleness detection: if a learning references `src/auth.ts` and that file is refactored, nothing warns that the learning may need updating
- Memory retrieval is reactive: the decision tree relies on the agent recognizing when to check learnings
- No file-pattern routing: the agent must know which agents/specs are relevant for a given area
- Debugging gotchas are stored as prose, making multi-symptom failures harder to scan
- No guidance for when a debugging session warrants creating a domain-expert agent vs. just capturing a learning

### Desired Outcome

- Staleness caught at write time during `/_wrapup`, when you're in context to act on it
- Automatic routing suggestions based on files being modified
- Explicit knowledge gap signals
- Structured debugging knowledge format
- Clear heuristic for when to escalate a learning into an agent

---

## Scope

### In Scope

1. **Staleness detection in `/_wrapup`** — cross-reference session changes against file-to-knowledge index
2. **Context-loading rule updates** — trigger table reference
3. **Memory agent update** — knowledge gap detection output
4. **Wrapup command updates** — index maintenance, agent creation guidance, symptom-cause-fix format
5. **Learning template update** — optional symptom-cause-fix section for gotchas
6. **Trigger table template** — `.project/trigger-table.md` in project template
7. **File-knowledge index** — `.project/file-knowledge-map.md` in project template

### Out of Scope

- MCP-based retrieval service
- Subsystem specification template/workflow (separate feature)
- Embedding-based semantic search
- Changes to the memory agent's core retrieval algorithm
- Session-start hooks or shell scripts for staleness detection (handled in `/_wrapup` instead)
- Auto-fixing stale artifacts (detection and prompt to update, not auto-fix)

### Edge Cases & Considerations

- Projects with no learnings yet: staleness check skips silently (no index = nothing to check)
- Files referenced in learnings that have been deleted: flag as stale (the learning references something that no longer exists)
- Multiple learnings covering the same file: flag each stale one
- `--quick` wrapup skips staleness check (only updates CURRENT_WORK.md)

---

## Requirements

### Functional Requirements

#### Staleness Detection (in `/_wrapup`)

1. **FR-1**: A file-to-knowledge index at `.project/file-knowledge-map.md` mapping source file paths to the learnings/docs that cover them
2. **FR-2**: During `/_wrapup` (full mode, not `--quick`), a new step cross-references the session's changed files (`git diff --name-only` and recent commits) against the file-knowledge index
3. **FR-3**: When changed files are found in the index, `/_wrapup` flags the covering knowledge artifacts and asks the user: "These knowledge artifacts cover files you changed this session — do they need updating?" with the list of artifacts and which files triggered them
4. **FR-4**: If the user confirms an artifact is still current, update its `Last Verified` date in the index
5. **FR-5**: If the user says an artifact needs updating, prompt to update it in the same session
6. **FR-6**: Skip staleness check silently when the index file doesn't exist

#### Index Maintenance

7. **FR-7**: `/_wrapup` maintains the file-knowledge index when creating or updating learnings — adds/updates entries mapping source files from the learning's `## Key Files` section to the learning filename
8. **FR-8**: `/_wrapup` checks the index for orphaned entries (learnings that no longer exist) and cleans them up

#### Context-Loading Updates

9. **FR-9**: `context-loading.md` references `.project/trigger-table.md`: "If modifying files, check the trigger table for relevant agents and specs to load"

#### Trigger Tables

10. **FR-10**: A trigger table template at `.project/trigger-table.md` with file-glob-to-agent/spec mappings that projects populate
11. **FR-11**: The trigger table format maps file patterns (globs) to recommended agents and/or knowledge artifacts to load

#### Memory Agent — Knowledge Gap Detection

12. **FR-12**: When the memory agent finds no relevant learnings for a substantive task, it explicitly flags: "No prior knowledge exists for [area]. Consider creating a learning or subsystem doc after this work."

#### Wrapup Enhancements

13. **FR-13**: `/_wrapup` Step 3 adds guidance: "If this session involved extended debugging (3+ cycles of hypothesis-test-fail) in a specific domain, suggest creating a domain-expert agent rather than just a learning"
14. **FR-14**: `/_wrapup` Step 3 learning template for `gotcha` type offers an optional symptom-cause-fix table format as a replacement for the prose "What Didn't Work" / "What Works" sections when there are multiple failure modes

#### Project Template

15. **FR-15**: `project-template/` includes an empty `file-knowledge-map.md` with header/format documentation
16. **FR-16**: `project-template/` includes a `trigger-table.md` template with format documentation and example entries

---

### Non-Functional Requirements

- All changes must be backward-compatible: projects without the new files continue to work unchanged
- Staleness check in `/_wrapup` should not add significant overhead to the wrapup flow

---

## Acceptance Criteria

### Staleness Detection
- [ ] **AC-1** (FR-1, FR-2, FR-3): **Given** the file-knowledge index maps `src/auth.ts` to `learnings/20260301-auth-bug.md`, **when** `/_wrapup` runs and `src/auth.ts` was changed this session, **then** wrapup flags the learning and asks the user if it needs updating
- [ ] **AC-2** (FR-2): **Given** no source files covered by the index were changed this session, **when** `/_wrapup` runs, **then** no staleness prompt appears
- [ ] **AC-3** (FR-4): **Given** a flagged artifact is confirmed still current by the user, **when** wrapup proceeds, **then** the `Last Verified` date is updated in the index
- [ ] **AC-4** (FR-6): **Given** the file-knowledge index doesn't exist, **when** `/_wrapup` runs, **then** the staleness check is skipped silently

### Index Maintenance
- [ ] **AC-5** (FR-7): **Given** a learning is created via `/_wrapup` with `## Key Files` listing `src/api.ts` and `src/routes.ts`, **when** wrapup completes, **then** the file-knowledge index contains entries mapping both paths to the learning filename
- [ ] **AC-6** (FR-8): **Given** a learning file has been deleted but its entries remain in the index, **when** `/_wrapup` runs, **then** the orphaned entries are removed

### Context-Loading
- [ ] **AC-7** (FR-9): **Given** `.project/trigger-table.md` exists with a mapping `src/auth/**` → `auth-agent`, **when** modifying `src/auth/login.ts`, **then** context-loading suggests loading `auth-agent`

### Trigger Tables
- [ ] **AC-8** (FR-10, FR-11): **Given** the trigger table template, **when** a project populates it with file patterns and agents, **then** the format is parseable and entries map globs to agent/spec names

### Knowledge Gap Detection
- [ ] **AC-9** (FR-12): **Given** a substantive task involving the "payments" module, **when** the memory agent finds no relevant learnings, **then** it outputs a knowledge gap flag naming the area

### Wrapup Enhancements
- [ ] **AC-10** (FR-13): **Given** a session with 3+ debug cycles in a specific domain, **when** `/_wrapup` runs, **then** it suggests creating a domain-expert agent for that area
- [ ] **AC-11** (FR-14): **Given** a gotcha learning with multiple failure modes, **when** `/_wrapup` captures it, **then** it uses the symptom-cause-fix table format

### Quality & Integration
- [ ] Existing hook infrastructure continues to work
- [ ] Projects without the new template files work unchanged

---

## File-Knowledge Index Format

```markdown
# File-Knowledge Map

> Maps source files to the learnings and docs that cover them.
> Maintained by `/_wrapup`. Used by `/_wrapup` staleness check.

| Source File | Knowledge Artifact | Last Verified |
|---|---|---|
| src/auth/login.ts | learnings/20260301-auth-session-bug.md | 2026-03-01 |
| src/auth/middleware.ts | learnings/20260301-auth-session-bug.md | 2026-03-01 |
| src/api/routes.ts | docs/api-layer.md | 2026-02-28 |
```

## Trigger Table Format

```markdown
# Trigger Table

> Maps file patterns to relevant agents and knowledge artifacts.
> Consulted during context-loading when modifying files.
> Populate this per-project.

| File Pattern | Agent | Knowledge Artifact | Notes |
|---|---|---|---|
| src/auth/** | auth-agent | docs/auth-system.md | Session handling, OAuth flows |
| src/api/** | — | docs/api-layer.md | REST conventions, middleware chain |
| tests/** | test-agent | — | Test patterns, fixtures |
```

## Symptom-Cause-Fix Format (for gotcha learnings)

When a gotcha has multiple failure modes, replace the "What Didn't Work" / "What Works" prose sections with:

```markdown
## Symptoms & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| Auth fails silently | Token expiry not checked | Add expiry check in middleware |
| 500 on refresh | Stale session reference | Clear session cache on token refresh |
```

For simple gotchas (single issue), the prose format remains the default.

---

## Related Artifacts

- **Research:** Analysis of arxiv 2602.20478 (in conversation history)
- **Plan:** `.project/active/memory-enhancements/plan.md` (to be created)

---

**Next Steps:** After approval, proceed to `/_plan`
