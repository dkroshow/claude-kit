---
name: implement-standard
description: Implementation quality gates, audit checklist, and progress tracking standards
---

# Implementation Standard

Defines quality gates, per-phase audit criteria, progress tracking format, and code quality rules. Referenced by `/_implement` and `/_cycle`.

## Code Quality Gate

Run per CLAUDE.md and project conventions after each implementation phase:

### Mechanical Checks
- **Test suite** — all tests pass, no regressions
- **Linting** — no violations
- **Type checking** — no type errors (if applicable)
- **Formatting** — clean

Triage issues by risk:
- **Low-risk** (formatting, unused imports): fix directly
- **Medium/high-risk** (test failures in business logic, interface changes): flag to user before proceeding

### Code Review (Inline)

After mechanical checks pass, re-read the code you just wrote and review per `skills/simplify-standard.md`:

1. **Redundancy** — duplicate logic, repeated computations, copy-paste patterns
2. **Naming** — do names communicate intent?
3. **Nesting** — can deep conditionals be flattened with early returns?
4. **Constants** — magic strings/numbers that should be extracted
5. **Dead code** — unused variables, unreachable branches, commented-out code
6. **Separation of concerns** — functions doing too many things

Fix issues inline before proceeding. This is part of the quality gate, not a separate pass.

## Per-Phase Audit

After completing each implementation phase, ask yourself these three questions:

1. **Completion Accuracy**: Are all items from this phase completed as specified? Any placeholder code, TODOs, or partial implementations?
2. **Deviation Justification**: For any deviations from the plan, are they reasonable? Document the rationale.
3. **Test Coverage**: What's tested? What's mocked? What gaps exist that need manual verification?

If audit reveals issues: STOP and present to user before moving to next phase.

## Implementation Notes Format

After completing each phase, add to plan.md under "Implementation Notes":

```markdown
### Phase [N] Completion
**Completed:** [Date/Time]
**Changes Made:**
- Created `path/to/new_file.ext` with main_function()
- Modified `path/to/existing.ext:45` to add parameter
- Added tests in `tests/test_feature.ext`

**Per-Phase Audit:**
- Completion Accuracy: [All items complete? Placeholders?]
- Deviations: [What changed from plan and why]
- Test Coverage: [What's tested, what needs manual verification]

**Issues Encountered:**
- [Issue and how it was resolved]
```

## Code Quality Rules

**NEVER write:**
- Mock tests that don't validate real behavior
- `skip`, `pass`, `TODO` without failing loudly
- Stub functions with hardcoded returns
- Code allowing silent failures

**ALWAYS ensure:**
- Tests validate actual functionality
- Incomplete code raises errors or fails explicitly
- Test assertions check real behavior
- Failures are immediate and obvious

## Deviation Handling

When implementation diverges from the plan:

```
Issue in Phase [N]:
Expected: [plan says]
Found: [actual]
Impact: [why matters]

How should I proceed?
```

## Progress Tracking

**After each phase:**
- Check off completed items in plan immediately
- Add implementation notes to plan
- Document deviations, issues, solutions
- Update status in linked spec/plan/epic
- Update CURRENT_WORK.md if it exists
