# Plan Command

**Purpose:** Technical design and phased implementation planning
**Input:** Spec document at `.project/active/{feature-name}/spec.md`
**Output:** `.project/active/{feature-name}/plan.md`

## Overview

You are a specialist planning agent. Create lean, executable plans that cover:
1. **Technical design** — architecture, components, decisions with rationale
2. **Phasing & ordering** — break work into logical, testable phases
3. **Test-first** — start each phase by writing tests
4. **Continuous validation** — verify progress at every step

**Quality standard:** Read `skills/plan-standard.md` for the plan template, REFLECT checklist, and quality criteria.

**Flags:**
- `--codex`: Run Codex CLI review after plan is written. Codex independently reviews the plan against the spec, then Claude incorporates valid findings before presenting.

When invoked:
- If feature name provided: proceed to planning
- If no feature: ask "Which feature should I plan?" and request feature name in `.project/active/`
- If `--codex`: set `codex_review = true` for the session

## Process

### Step 1: Read & Assess

1. **Read Input Documents Fully**:
   - `.project/active/{feature-name}/spec.md`
   - CLAUDE.md for project conventions

2. **Check prior learnings:**
   - Read `.project/learnings/index.md` and `~/.claude/learnings/index.md` if they exist
   - Scan for entries related to the feature being planned
   - Read any relevant learning files (especially failure knowledge and gotchas)
   - Plan should account for known issues

3. **Critical Feasibility Assessment**:
   - Will this work with the current codebase?
   - What are the highest risks?
   - What assumptions might be wrong?

If inputs missing or unclear, STOP and ask for clarification.

### Step 2: Research Codebase

1. **Analyze existing code**:
   - Use `Task` tool with `subagent_type=Explore` for broad searches
   - Use Grep/Read for targeted investigation
   - Find: patterns, utilities, integration points, testing approaches

2. **Draft technical design**:
   - Architecture overview
   - Component details (purpose, location, interfaces, dependencies)
   - Design decisions with rationale (if alternatives exist)

3. **Self-evaluate** using the REFLECT checklist from the plan standard.

4. **Present design decisions to user if needed** → WAIT.

### Step 3: Phase Strategy & Approval

1. **Design Phase Structure** following these principles:
   - **De-risk early**: Tackle hardest/riskiest parts first when possible
   - **Test-first**: Each phase starts with writing tests
   - **Incremental validation**: Each phase produces verifiable output
   - **Logical dependencies**: Respect build order
   - **Small batches**: Prefer 3-5 phases over 1-2 mega-phases

2. **Present strategy for approval** with phase breakdown, risks, and critical assessment.

3. **Wait for user approval**.

### Step 4: Write Plan Document

For each approved phase, write:
1. **Test approach** (referencing spec AC-N)
2. **Changes required** (file:line specifics)
3. **Validation steps** (how to verify this phase works)

Write to `.project/active/{feature-name}/plan.md` using the plan document template from the standard.

### Step 5: Codex Review

1. **If `codex_review`**: Run Codex CLI to independently review the plan:
   ```bash
   codex exec --full-auto --ephemeral \
     -m gpt-5.4 -c reasoning_effort=xhigh \
     "Review the implementation plan at .project/active/{feature-name}/plan.md against the spec at .project/active/{feature-name}/spec.md. Identify: technical mistakes, gaps in spec coverage, phase ordering issues, missing dependencies, and implementation risks. Be specific and actionable — for each issue, reference the relevant plan section and explain what's wrong and how to fix it." \
     2>/dev/null
   ```
   - Read the Codex review output from stdout
   - Evaluate each finding against your codebase knowledge — Codex lacks full context, so some findings may not apply
   - Revise plan.md incorporating valid findings
   - Present the plan to user noting which changes came from Codex review

2. **If not `codex_review`**: Present the plan to user, then offer:
   ```
   Want me to run a Codex review on this plan before we proceed? (/_plan --codex)
   ```

## Guidelines

### Core Principles
- **Avoid duplication**: Reference spec extensively, don't repeat component details
- **De-risk early**: Hardest/riskiest parts first when possible
- **Test-first**: Every phase starts with test approach
- **Continuous validation**: Explicit "What We Know Works" after each phase
- **Small batches**: 3-5 focused phases

### When to Get User Approval
- After presenting phase strategy
- If plan scope seems too large (suggest breaking up)
- If technical approach is unclear

---

**Related Commands:**
- Before plan: `/_spec` or `/_research`
- After plan: `/_implement` to execute

**Last Updated**: 2026-03-02
