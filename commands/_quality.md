# Quality Command

**Purpose:** Run the full quality standard against your codebase on demand
**Input:** Optional feature name or file paths to focus on
**Output:** Fixes + structured report

## Overview

Standalone entry point for `skills/simplify-standard.md`. Runs both mechanical checks (tests, lint, types, format) and the 8 code review dimensions, with risk-based triage.

While `/_cycle` runs this automatically per phase, `/_quality` lets you run it independently — across an entire project, on specific files, or before a release.

## Process

1. **Read CLAUDE.md** for project-specific test, lint, and quality commands
2. **Determine scope** — if paths/feature provided, focus there; otherwise run project-wide
3. **Run the full simplify standard** per `skills/simplify-standard.md`:
   - Mechanical checks (tests, lint, types, formatting)
   - Code review (redundancy, abstraction, naming, nesting, dead code, constants, data flow, separation of concerns)
   - Risk triage: fix low-risk directly, present medium/high-risk to user
4. **Report:**

```
## Quality Report

**Scope:** [project-wide / specific paths]
**Checks Run:** [list]
**Issues Found:** [count by risk level]

### Fixed (Low-Risk)
- [fix 1]

### Needs Attention
- [medium/high risk issues with file:line, impact, suggested fix]

### All Clear
- [checks that passed clean]
```

---

**Related:**
- During implementation: `/_cycle` runs this per phase via `implement-standard.md`
- After implementation: `/_audit` for requirement-level verification
- Native `/simplify` reviews recently changed files using the same standard
