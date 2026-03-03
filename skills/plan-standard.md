---
name: plan-standard
description: Plan document format, design review checklist, and quality standards
---

# Plan Document Standard

Defines the format, review dimensions, and quality criteria for plan documents. Referenced by `/_plan` and `/_cycle`.

## REFLECT Checklist

Critically evaluate design and plan against these dimensions before finalizing:

**Design Completeness:**
- [ ] **Spec compliance** — Does every requirement have a design element? Are acceptance criteria addressable?
- [ ] **Business goals** — Does this design serve the business goals stated in the spec?
- [ ] **Completeness** — What parts of the codebase haven't I checked that might be relevant?
- [ ] **Edge cases** — What could go wrong? What failure modes exist?

**Design Quality:**
- [ ] **Pattern consistency** — Does the design follow existing codebase patterns? Am I reusing existing utilities?
- [ ] **Abstraction quality** — Are abstractions at the right level? Would a new developer understand quickly?
- [ ] **Duplication avoidance** — Does this duplicate existing functionality? Opportunities to consolidate?
- [ ] **Data structure clarity** — Are data structures well-defined and traceable?

**Implementation Readiness:**
- [ ] **Route safety** — Are all routes/endpoints explicit? Are fallback behaviors safe?
- [ ] **Assumptions** — What am I assuming? Do these assumptions need validation?
- [ ] **Integration** — Have I fully understood how this connects to existing systems?
- [ ] **Risks & dependencies** — What are the risks, trade-offs, and dependency constraints?

## Plan Document Template

Write to `.project/active/{feature-name}/plan.md`:

```markdown
# Plan: [Feature Name]

**Status:** Draft
**Owner:** [Git Username]
**Created:** [Date]
**Last Updated:** [Date]

---

## TL;DR
[5-10 lines: what we're building, key technical approach, number of phases]

---

## Source Documents
- **Spec:** `.project/active/{feature-name}/spec.md`

## Research Findings
### Files Analyzed
[List with brief descriptions and file:line references]
### Reusable Patterns
[Patterns found with file:line references]
### Integration Points
[How this connects to existing systems]

## Design Decisions (if applicable)
### Decision 1: [Topic]
**Context:** [Why this decision matters]
**Options Considered:** [2-3 options with trade-offs]
**Chosen:** [Selected option]
**Rationale:** [Why]

## Technical Design
### Architecture Overview
[High-level components and relationships]

### [Component 1]
**Purpose:** [What it does]
**Location:** [File path]
**Key interfaces:** [Functions/classes with signatures]
**Dependencies:** [What it uses]
**Data flow:** [Input -> processing -> output]

### Error Handling
[Approach]

---

## Implementation Strategy

### Phasing Rationale
[Why this sequence de-risks and builds incrementally]

### Overall Validation Approach
- Each phase starts with tests (where applicable)
- Each phase has automated + manual validation
- Continuous verification ensures no regressions

### Phase 1: [Name]
#### Goal
[What this accomplishes and why it's first]
#### Test Approach
Reference: spec.md acceptance criteria AC-1, AC-2
#### Changes Required
- [ ] [File 1]: [Specific change with file:line ref]
- [ ] [File 2]: [Specific change]
#### Validation
**Automated:**
- [ ] Tests pass
- [ ] Code quality checks clean
**Manual:**
- [ ] [Verification step]
**What We Know Works:** [Specific functionality verified]

### Phase 2: [Name]
[Same structure]

---

## Risk Management
[Risks and mitigations]

---

## Implementation Notes
[TO BE FILLED DURING IMPLEMENTATION]

### Phase 1 Completion
**Completed:** [Timestamp]
**Changes Made:**
- Created `path/to/new_file.ext` with main_function()

**Per-Phase Audit:**
- Completion Accuracy: [All items complete? Placeholders?]
- Deviations: [What changed from plan and why]
- Test Coverage: [What's tested, what needs manual verification]

**Issues Encountered:**
- [Issue and how it was resolved]

---

**Status**: Draft -> In Progress -> Complete
```

## Planning Quality Criteria

A good plan:
- Is grounded in concrete codebase research with file:line references
- Explains interfaces, data flows, and WHY decisions were made
- Documents alternatives considered
- De-risks early: tackle hardest/riskiest parts first when possible
- Uses test-first approach: each phase starts with test stencils
- Prefers small batches: 3-5 focused phases over 1-2 mega-phases
- Each phase should be completable in one session
- "What We Know Works" after each phase builds confidence incrementally
- Never uses placeholder values

## Checkbox Conventions

- File changes get checkboxes
- Validation steps get checkboxes
- Keep it minimal — checkboxes for actions, not details
