---
name: spec-standard
description: Specification document format, conventions, and quality standards
---

# Spec Document Standard

Defines the format, conventions, and quality criteria for specification documents. Referenced by `/_spec` and `/_cycle`.

## Scoping Presentation Template

Present scope to user for approval before writing the spec:

```
## What I Heard You Say
[Quote or closely paraphrase the user's original request, capturing ALL details]

## Business Goals & Priorities
**Why this matters:** [The user's motivation/need in 1-2 sentences]
**Success looks like:** [Qualitative outcome from user's perspective]
**Priority:** [If mentioned or can be inferred]

## Functional Scope (What We're Building)
Based on what you described:
- [Core functionality 1 — from user's request]
- [Core functionality 2 — from user's request]

## What's NOT Included
- [Explicit exclusion if mentioned]
- [Reasonable boundary based on scope]

## Questions
[Any clarifications needed about business requirements]

## Codebase Investigation Offer
Would you like me to investigate any parts of the codebase to help:
- Identify existing patterns we should follow?
- Discover integration points or dependencies?
- Add implementation-specific requirements?

Just let me know which areas to explore, or say "no investigation needed" to proceed with the spec.
```

## Spec Document Template

Write to `.project/active/{feature-name}/spec.md`:

```markdown
# Spec: [Feature Name]

**Status:** Draft
**Owner:** [Git Username]
**Created:** [Date/Time]
**Complexity:** [LOW | MEDIUM | HIGH]
**Branch:** [Branch name if applicable]

---

## TL;DR
[5-10 lines summarizing: what problem this solves, what we're building, key constraints]

---

## Business Goals

### Why This Matters
[1-2 paragraphs explaining the user need or project goal this addresses]

### Success Criteria
- [ ] [Success criterion 1]
- [ ] [Success criterion 2]

### Priority
[Relative priority and any dependencies on other work]

---

## Problem Statement

### Current State
[What exists now that's insufficient]

### Desired Outcome
[What we want to achieve]

---

## Scope

### In Scope
- [What this feature includes]

### Out of Scope
- [What this feature does NOT include]

### Edge Cases & Considerations
- [Important edge case to handle]

---

## Requirements

### Functional Requirements

> Requirements below are from user's request unless marked [INFERRED] or [FROM INVESTIGATION]

1. **FR-1**: [Requirement from user]
2. **FR-2**: [Requirement from user]
3. **FR-3**: [INFERRED] [Requirement implied by user's request]

### Non-Functional Requirements (if applicable)

- [Performance, security, or other quality requirements if user specified]

---

## Acceptance Criteria

### Core Functionality
- [ ] **AC-1** (FR-1): **Given** [precondition], **when** [action], **then** [expected result]
- [ ] **AC-2** (FR-2): **Given** [precondition], **when** [action], **then** [expected result]

### Quality & Integration
- [ ] Existing tests continue to pass

---

## Related Artifacts

- **Research:** `.project/research/{file}.md` (if exists)
- **Plan:** `.project/active/{feature-name}/plan.md` (to be created)

---

**Next Steps:** After approval, proceed to `/_plan`
```

## Requirement Conventions

- **FR-N identifiers**: Functional requirements numbered FR-1, FR-2, etc.
- **AC-N identifiers**: Acceptance criteria numbered AC-1, AC-2, etc., cross-referenced to FR-N
- **Given/When/Then format**: All acceptance criteria use this structure
- **Source marking**: Requirements from user are unmarked; inferred ones marked `[INFERRED]`; from codebase investigation marked `[FROM INVESTIGATION]`

## Complexity Assessment

- **LOW**: Clear scope, limited surfaces, straightforward implementation
- **MEDIUM**: Multiple integrations, needs careful design planning
- **HIGH**: Significant scope, many surfaces, needs research and staged implementation

## Quality Criteria

A good spec:
- Captures EVERY detail the user provides
- Distinguishes user requirements from inferences
- Problem statement explains "why" without prescribing "how"
- Scope boundaries prevent feature creep
- Requirements are traceable to user's request
- Edge cases identified but solutions deferred to design
- Does NOT add implementation-specific requirements without user's explicit request
