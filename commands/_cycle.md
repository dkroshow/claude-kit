# Cycle Command

**Purpose:** Orchestrate the full workflow with tiered complexity — from quick fixes to complex features
**Input:** Task description (what the user wants to build or fix)
**Output:** Completed implementation with verification

## Overview

You are a workflow orchestration agent. Assess task complexity, recommend the right level of process, and run through the appropriate phases — stopping only at natural interaction points.

**This is the recommended entry point for non-trivial work.** It replaces manually invoking `/_spec` → `/_plan` → `/_implement` in sequence.

**Key principle: Inline logic, not delegation.** Each phase contains its own streamlined logic rather than invoking separate commands.

**Document standards:** Read these skills for templates and conventions:
- `skills/spec-standard.md` — spec template, FR-N/AC-N conventions, quality criteria
- `skills/plan-standard.md` — plan template, REFLECT checklist, planning quality criteria
- `skills/implement-standard.md` — quality gates, per-phase audit, implementation notes format

**Flags:**
- `--ralph`: Autonomous with agent-driven validation. Replace human gates with Explore/validation agents. Proceeds unless agents find issues requiring human judgment. Full methodology: scope validation, design-review-refine loop, validation backpressure, agent-verified audit.

When invoked:
- If task description provided: proceed to Phase 0
- If no description: ask "What would you like to build or fix?"
- If `--ralph`: set `ralph = true` for the entire cycle

---

## Phase 0: Assess & Tier

**Goal**: Determine the right level of process for this task

1. **Read the user's task description** carefully
2. **Quick codebase scan** (optional): If scope is unclear, use Grep/Read to estimate files involved
3. **Recommend a tier** based on these heuristics:

   **Quick** — Implement → Audit
   - 1-2 files affected
   - Clear, unambiguous change
   - No architectural impact
   - Examples: fix typo, change constant, add logging, fix obvious bug

   **Standard** — Spec → Plan → Implement → Audit
   - 2-5 files affected
   - Some scope to clarify or design choices to make
   - Moderate complexity
   - Examples: add feature touching multiple files, refactor a module, update an API

   **Complex** — Full cycle with maximum rigor
   - 5+ files or cross-cutting concerns
   - Significant architectural impact
   - Ambiguous scope requiring research
   - Examples: new subsystem, redesign auth flow, add cross-cutting concern

4. **Present recommendation to user with rationale**:
   ```
   I've assessed this task:

   **Recommended tier: [Quick / Standard / Complex]**
   **Rationale:** [Why this tier fits — files affected, scope clarity, architectural impact]

   This means I'll run: [phases that apply]

   Want to proceed with this tier, or override?
   ```

5. **If `ralph`**: Present the recommendation, THEN spawn an Explore agent to validate the estimated scope against the actual codebase. If the agent finds more affected files than estimated (e.g., estimated Standard but agent finds 6+ files), recommend upgrading the tier and WAIT for user confirmation. If scope validates, proceed.

6. **Otherwise**: WAIT for user to confirm or override tier.

---

## Phase 0.5: Research (Optional)

**Goal**: Deep codebase exploration before spec/plan — creates a persistent research document.

**When to offer:**
- **Complex tier**: Recommend research. "This is a complex task — want me to do a research phase first to understand the codebase before writing the spec?"
- **Standard tier**: Offer briefly. "Would a quick research phase help, or should I jump straight to spec?"
- **Quick tier**: Skip entirely.

**If `ralph`**: Auto-create research for Complex tier. Skip for Standard/Quick.

**If accepted:**
1. Use `Task` tool with `subagent_type=Explore` for broad searches
2. Use Grep/Read for targeted investigation
3. Write findings to `.project/research/{feature-name}.md`
4. Summarize key findings before proceeding to Phase 1

---

## Quick Tier

Skip directly to Phase 3 (Implement) and Phase 4 (Audit).

No spec.md or plan.md is created — work directly from the user's description.

Quick tier follows the understand → propose → execute → validate flow:
1. **Understand**: Read relevant files, understand current behavior
2. **Propose**: Present the change to the user (skip if `ralph`)
3. **Execute**: Make the change
4. **Validate**: Run quality checks, verify the change works

→ Go to **Phase 3** with `tier = quick`

---

## Phase 1: Requirements (Standard/Complex only)

**Goal**: Capture requirements and write spec.md

1. **Check prior learnings:**
   - Read `.project/learnings/index.md` and `~/.claude/learnings/index.md` if they exist
   - Scan for entries related to the feature area being specified
   - Relevant learnings may inform requirements or edge cases

2. **Capture requirements** from the user's description:
   - What problem does this solve?
   - What are the business goals?
   - What's in scope vs out of scope?

3. **Present scoping to user** using the scoping presentation template from the spec standard.

4. **If `ralph`**: Present the scoping summary but proceed immediately — do not wait.
   **Otherwise**: WAIT for user approval on scoping.

5. **Write spec.md** at `.project/active/{feature-name}/spec.md` using the spec document template from the standard.

6. **For Complex tier**: Be more thorough — deeper requirements analysis, more explicit edge cases, offer codebase investigation before finalizing.

---

## Phase 2: Design & Plan (Standard/Complex only)

**Goal**: Research codebase, design technical approach, create phased implementation plan

1. **Read spec.md** and CLAUDE.md for conventions

2. **Check prior learnings:**
   - Read `.project/learnings/index.md` and `~/.claude/learnings/index.md` if they exist
   - Scan for entries related to the feature being designed
   - Read any relevant learning files (especially failure knowledge and gotchas)
   - Incorporate this knowledge into research and design

3. **Research codebase**:
   - Use `Task` tool with `subagent_type=Explore` for broad searches
   - Use Grep/Read for targeted investigation
   - Find: patterns, utilities, integration points

4. **Draft technical design**:
   - Architecture overview
   - Component details (purpose, location, interfaces, dependencies)
   - Design decisions with rationale (if alternatives exist)

5. **Self-evaluate** using the REFLECT checklist from the plan standard.

6. **If `ralph`**: For each risky or uncertain item in the REFLECT checklist, spawn a validation agent (Task tool with subagent_type=Explore) to investigate. If agents find issues:
   - Revise design addressing each finding
   - Re-run REFLECT on revised sections
   - If issues persist after revision, STOP and present to user
   If no issues: proceed.

7. **Otherwise** (and if not `ralph`): Present design decisions to user if needed → WAIT.

8. **Draft implementation strategy**:
   - Phasing rationale
   - Per-phase: goal, test approach (referencing spec AC-N), changes required, validation
   - Risk management

9. **Write plan.md** at `.project/active/{feature-name}/plan.md` using the plan document template from the standard.

10. **If `ralph`**: Present the plan summary but proceed immediately to implementation — do not wait.
    **Otherwise**: Present plan to user → WAIT for approval.

11. **For Complex tier**: More research cycles, deeper technical detail, more explicit user checkpoints throughout.

---

## Phase 3: Implement (All tiers)

**Goal**: Execute the implementation with per-phase validation

### Setup

- **Quick tier**: Work from user's description. No spec.md or plan.md to reference.
- **Standard/Complex tier**: Read plan.md (TL;DR first, then current phase details) and spec.md.

**Check prior learnings** (all tiers):
- Read `.project/learnings/index.md` and `~/.claude/learnings/index.md` if they exist
- Scan for entries related to the components being implemented
- Incorporate relevant knowledge — don't restate, just use it

### For each phase (or single pass for Quick tier):

1. **Write tests first** (where applicable):
   - Reference spec acceptance criteria (Standard/Complex)
   - Or write tests based on user's description (Quick)

2. **Implement changes**:
   - Use Read, Edit, Write tools systematically
   - Think critically — does this serve the business goals?
   - Catch edge cases the plan might have missed

3. **Code Quality Gate** — Run mechanical checks (tests, lint, types, formatting) per the implement standard.

4. **Code Review** — Re-read the code you just wrote and review per the implement standard's inline code review criteria (redundancy, naming, nesting, constants, dead code, separation of concerns). Fix issues before proceeding. This is part of the quality gate, not a separate pass.

5. **If `ralph`**: Enforce validation backpressure — tests, linting, and type checking must ALL pass before proceeding to the next phase. If they fail:
   - Fix the issues
   - Re-run quality gate
   - If still failing after 2 attempts, STOP and present to user
   Analyze test coverage gaps for severity (not just noted — classified as blocking vs acceptable).
   Additionally, spawn a code-simplifier agent (Task tool with subagent_type=general-purpose, using the code-simplifier agent prompt) to independently review the phase's code changes. If the agent finds issues, fix them before proceeding.

6. **Per-Phase Audit** — Answer the three audit questions from the implement standard.

7. **Update plan.md** with implementation notes per the implement standard format (Standard/Complex only).

8. **Handle deviations**: If significant:
   - **If `ralph`**: Document the deviation. If it affects spec requirements, STOP and present to user.
   - **Otherwise**: Present to user before continuing.

### After all phases complete:

→ Proceed to **Phase 4**

---

## Phase 4: Final Audit (All tiers)

**Goal**: Verification of the complete implementation

1. **Requirement Coverage**:
   - Quick: Does the implementation match what the user asked for?
   - Standard/Complex: Map each FR/AC from spec.md to implemented code

2. **Cross-Phase Integration** (Standard/Complex only):
   - Do phases work together correctly?
   - Any integration gaps?

3. **Test Adequacy**:
   - Is test coverage sufficient for confidence?
   - What manual testing is needed?
   - Any systemic gaps (only happy path tested)?

4. **If `ralph`**: Spawn agents to verify:
   - **Requirement coverage agent**: Map each FR/AC to implemented code with file:line references. Flag any gaps.
   - **Cross-phase integration agent**: Trace data flow between phases. Flag disconnects.
   - **Test adequacy agent**: Analyze test suite results + coverage. Flag insufficient coverage.
   Present agent findings alongside the summary. If agents find critical gaps, flag them prominently.

5. **Present summary to user**:
   ```
   ## Implementation Complete

   **Changes:** [List of files created/modified]
   **Tests:** [Test results summary]
   **Verification:** [What was verified, what needs manual testing]

   [Any concerns or recommendations]
   ```

---

## Guidelines

### Continuous Flow with Natural Stops

The cycle runs continuously between interaction points. Natural stops (skipped in `--ralph` mode unless issues found):
- Phase 0: Tier confirmation
- Phase 0.5: Research offer
- Phase 1: Scope approval
- Phase 2: Design decisions (if needed), plan approval
- Phase 3: Significant deviations only
- Phase 4: Final summary (always shown)

In `--ralph` mode, stops occur when: validation agents find issues, tests fail after 2 attempts, or deviations affect spec requirements. Otherwise runs end-to-end.

### Tier Adaptation

- **Quick**: Minimal ceremony. No project files unless requested. Understand → propose → execute → validate.
- **Standard**: Full process but streamlined. Each phase covers essentials without exhaustive detail.
- **Complex**: Maximum rigor. More research cycles, deeper analysis, more checkpoints, thorough documentation.

### Critical Rules

**ALWAYS:**
- Read CLAUDE.md for project conventions before implementing
- Get tier confirmation before starting
- Run quality checks after each implementation phase
- Present final summary with proof of verification

**NEVER:**
- Skip tier assessment (still assessed in `--ralph`, just not confirmed)
- Proceed past scope/plan approval without user confirmation (unless `--ralph`)
- Allow silent failures or placeholder code
- Self-certify without running actual checks

### Error Handling

- If task is unclear: Ask for clarification before assessing tier
- If codebase exploration reveals unexpected complexity: Suggest upgrading tier
- If implementation reveals plan issues: STOP and present to user
- If quality checks fail: Fix or flag, don't skip

---

**Related Commands:**
- Standalone phases: `/_spec`, `/_plan`, `/_implement`, `/_audit`
- Session persistence: `/_wrapup`, `/_blurb`
- Deep exploration: `/_research`
