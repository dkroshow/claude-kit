---
name: simplify-standard
description: Unified code quality standard — mechanical checks and code review criteria
---

# Simplify Standard

The single source of truth for code quality. Combines mechanical verification with judgment-based review. Referenced by `implement-standard.md`, `/_cycle`, and the native `/simplify` command.

## Mechanical Checks

Run all available checks per CLAUDE.md and project conventions:

- **Test suite** — all tests pass, no regressions
- **Linting** — no violations
- **Type checking** — no type errors (if applicable)
- **Formatting** — clean

If no quality commands are documented in CLAUDE.md, check for common patterns (package.json scripts, Makefile targets, pyproject.toml).

### Risk Triage

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

## Code Review

After mechanical checks pass, re-read the code you wrote and check each dimension:

### 1. Redundancy
- Duplicate logic across functions or blocks
- Repeated reads/computations (e.g., parsing the same file twice)
- Copy-paste patterns that should be consolidated

### 2. Abstraction Level
- **Over-abstraction**: Helpers, utilities, or wrappers for one-time operations
- **Under-abstraction**: Repeated inline patterns that obscure the main logic
- Right level: would a new developer understand the structure quickly?

### 3. Naming
- Variables and functions communicate intent
- Names are specific enough to distinguish from similar concepts
- Consistent with surrounding codebase conventions

### 4. Nesting & Control Flow
- Deep conditionals that could use early returns or guard clauses
- Nested ternaries that should be if/else or switch
- Convoluted control flow that could be linearized

### 5. Dead Code
- Unused variables, parameters, or imports
- Unreachable branches
- Commented-out code (delete it — git has history)

### 6. Constants & Magic Values
- Magic strings or numbers that should be named constants
- Repeated literal values across multiple locations

### 7. Data Flow
- Unnecessary intermediate variables
- Convoluted transformations that could be simplified
- Data passed through layers without being used

### 8. Separation of Concerns
- Functions doing too many things
- Mixed abstraction levels within a single function
- Business logic tangled with I/O or formatting

## Applying the Standard

- Fix issues inline — this is not a separate pass
- Only review code you just wrote or modified
- Preserve functionality — change how, not what
- Prefer clarity over brevity
- Don't touch surrounding code that wasn't part of the task
