# Implement Command

**Purpose:** Execute approved implementation plan with understanding and validation
**Input:** `.project/active/{feature-name}/plan.md` (plus spec.md)
**Output:** Code changes, updated plan with progress

## Overview

Execute implementation according to approved plan with careful validation and progress tracking.

**Do NOT blindly follow the plan.** Before implementing, you must thoroughly understand:
- The design rationale (WHY things are structured this way)
- The spec requirements (WHAT outcomes are expected)
- The codebase context (HOW this integrates with existing code)

**Quality standard:** Read `skills/implement-standard.md` for quality gates, per-phase audit criteria, implementation notes format, and code quality rules.

When invoked:
- If feature name provided: proceed to implementation
- If no feature: ask "Which feature should I implement?"

## Process

### Stage 0: Understanding Before Action

**This stage is mandatory. Do not skip to implementation.**

1. **Read Plan Document**: `.project/active/{feature-name}/plan.md` fully
   - Understand the architecture and component relationships
   - Understand WHY decisions were made
   - Note integration points and patterns to follow

2. **Read Spec Document**: `.project/active/{feature-name}/spec.md` fully
   - Understand the business goals and success criteria
   - Note all requirements and acceptance criteria

3. **Check prior learnings:**
   - Read `.project/learnings/index.md` and `~/.claude/learnings/index.md` if they exist
   - Scan for entries related to the components being implemented
   - Read any relevant learning files (especially gotchas and failures)

4. **Offer Codebase Exploration**:
   ```
   Before I begin implementing, would you like me to explore any parts of
   the codebase to deepen my understanding?

   Or say "proceed" to start implementation.
   ```

### Stage 1: Plan Analysis & Scope Confirmation

1. **Check Progress**: Look for existing checkmarks in plan.md
2. **Confirm Scope** — ALWAYS ask unless user specified:
   ```
   I've read the plan. Please choose execution approach:

   **Available Phases:**
   - Phase 1: [What it accomplishes]
   - Phase 2: [What it accomplishes]

   Choose:
   1. **One-by-one** (implement one phase, get approval, proceed)
   2. **Multiple phases** (specify which phases)
   3. **All phases** (implement all without stopping)

   Default: one-by-one for safety
   ```

### Stage 2: Sequential Implementation

1. **Start with Tests** — Implement test stencil first if provided
2. **Execute Changes** — Use Read, Edit, Write tools systematically
3. **Think Critically** — As you implement, continuously ask:
   - Does this serve the business goals in the spec?
   - Does this follow the design rationale?
   - Am I catching edge cases the plan might have missed?
4. **Verify Each Change** — Test as you go
5. **Update Progress** — Check off in plan
6. **Handle Deviations** — Use the deviation format from the implement standard

### Stage 3: Phase Completion & Validation

1. **Code Quality Gate** — Run mechanical checks and inline code review per the implement standard
2. **Per-Phase Audit** — Answer the three audit questions from the implement standard
3. **Update Plan Document** — Add implementation notes per the implement standard format
4. **Synchronize Status**:
   - Mark spec status: "Implementation In Progress" or "Complete"
   - Update CURRENT_WORK.md if it exists
5. **Checkpoint with User** if failures, audit issues, or deviations

## Guidelines

### Environment
- ALWAYS read CLAUDE.md for environment and command conventions first
- Follow project-specific setup, test, and quality check commands

### Understanding
- Understand WHY before implementing WHAT
- Adapt when implementation reveals plan issues
- Think critically about edge cases as you code

### Progress Tracking
- Check off completed items in plan immediately
- Add detailed implementation notes to plan
- Document deviations, issues, solutions

### Error Handling
- STOP immediately if reality differs significantly from plan
- NEVER dismiss issues or skip validations without approval
- Get approval before significant deviations

---

**Related Commands:**
- Before implement: `/_plan`
- After implement: `/_audit` for final verification

**Last Updated**: 2026-03-02
