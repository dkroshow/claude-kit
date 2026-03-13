# Code Quality — Write It Right The First Time

## After Writing Each Logical Chunk of Code

Before moving on to the next piece of work, re-read the code you just wrote and check for:

1. **Redundancy** — Am I reading the same data twice? Computing the same thing in multiple places? Copy-pasting patterns that should be a shared function?
2. **Naming** — Do variable and function names communicate intent? Would someone unfamiliar understand what this does from names alone?
3. **Nesting depth** — Can deep conditionals be flattened with early returns or guard clauses?
4. **Constants** — Are there magic strings or numbers that should be named constants?
5. **Dead code** — Unused variables, unreachable branches, commented-out code?
6. **Separation of concerns** — Is any function doing too many things? Could it be split for clarity?
7. **Abstraction balance** — Am I over-abstracting (premature helpers for one-time use) or under-abstracting (inline repetition that obscures intent)?

Fix issues inline as you find them. This is not a separate pass — it's part of writing the code.

## What This Is NOT

- Not a license to refactor surrounding code that wasn't part of the task
- Not an invitation to add comments, docstrings, or type annotations beyond what's needed
- Not a reason to over-engineer or add unnecessary error handling
- Just: re-read what you wrote, fix what's sloppy, move on
