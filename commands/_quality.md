# Quality Command

**Purpose:** Run comprehensive code quality checks with risk-based triage
**Input:** Optional feature name or file paths to focus on
**Output:** Quality report with categorized issues and fixes

## Overview

Run all available quality checks (tests, linting, type checking, formatting) and triage results by risk level. Fix low-risk issues directly, flag medium/high-risk issues for user decision.

When invoked:
- If feature/paths provided: focus checks on those areas
- If no arguments: run project-wide quality checks

## Process

### Stage 1: Discover Available Checks

1. **Read CLAUDE.md** for project-specific test, lint, and quality commands
2. Identify what's available: test suite, linter, type checker, formatter
3. If no quality commands are documented, check for common patterns (package.json scripts, Makefile targets, pyproject.toml)

### Stage 2: Run All Checks

Run all available checks and capture output:
- **Test suite** — run per CLAUDE.md conventions
- **Linting** — run per CLAUDE.md conventions
- **Type checking** — run if applicable
- **Formatting** — run if applicable

### Stage 3: Categorize Issues

Triage each issue by risk:

**Low-risk** (fix directly):
- Formatting inconsistencies
- Unused imports
- Missing trailing newlines
- Whitespace issues

**Medium-risk** (present to user):
- Test failures in non-critical paths
- Linting warnings in changed code
- Type errors in peripheral code

**High-risk** (stop and present):
- Test failures in business logic
- Security-related warnings
- Interface/contract changes
- Regression indicators

### Stage 4: Fix Low-Risk Issues

Apply fixes for low-risk issues directly. Document what was fixed.

### Stage 5: Document Medium/High-Risk Issues

For each medium/high-risk issue, present:
```
**[Risk Level]**: [Description]
**File:** [path:line]
**Impact:** [Why this matters]
**Suggested fix:** [What to do]
```

### Stage 6: Completion Report

```
## Quality Report

**Checks Run:** [list]
**Issues Found:** [count by risk level]

### Fixed (Low-Risk)
- [fix 1]
- [fix 2]

### Needs Attention
- [medium/high risk issues]

### All Clear
- [checks that passed clean]
```

If a feature is actively being implemented, write the report to `.project/active/{feature-name}/` for traceability.

---

**Related Commands:**
- During implementation: `/_implement` runs quality gate per phase
- After implementation: `/_audit` for requirement-level verification

**Last Updated**: 2026-03-02
