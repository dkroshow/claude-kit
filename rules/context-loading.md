# Context Loading

## Before Starting Non-Trivial Work

1. **Read `.project/CURRENT_WORK.md`** — active work context, recent decisions, known issues
2. **Read the relevant docs** for the area you're working in (check CLAUDE.md for pointers)
3. **Check prior learnings** — follow the decision tree below

## Memory Retrieval Decision Tree

Before starting a task, determine whether to check prior learnings:

**Step 1: Is this trivial?**
Typo fixes, formatting changes, simple renames, git operations, one-line changes.
> YES: Skip memory check entirely. Proceed with the task.
> NO: Continue to Step 2.

**Step 2: Is this the first substantive task in this session?**
> YES: Scan both `.project/learnings/index.md` and `~/.claude/learnings/index.md` for anything relevant to the project area you're about to work in. Read any matching entries.
> NO: Continue to Step 3.

**Step 3: Does the task involve a specific component, file, or area?**
The user mentions a module, service, API, file, or system by name.
> YES: Scan both learnings indexes for entries tagged with or related to that area. Read any matching entries. Also check `.project/trigger-table.md` if it exists — if the files you're about to modify match a pattern in the trigger table, load the suggested agent and/or knowledge artifact.
> NO: Continue to Step 4.

**Step 4: Is this debugging or troubleshooting?**
> YES: Scan both learnings indexes — failure knowledge is especially valuable for debugging. Look for entries of type "gotcha" or "failure."
> NO: Proceed without memory check. If you encounter something mid-task that feels like you've seen it before, you can check learnings at that point.

**Retrieval tiers:**
- **Tier 1 (Index scan)**: Read index.md — one file read, nearly free. Always do this when triggered.
- **Tier 2 (Targeted read)**: Read 1-3 matching learning files. The common case.
- **Tier 3 (Memory agent)**: If 5+ potential matches or ambiguous relevance, spawn the memory agent (`agents/memory.md`) for semantic search and synthesis.

**Dual-index retrieval:** Always check both project-level (`.project/learnings/index.md`) and global (`~/.claude/learnings/index.md`). Project-level takes precedence when entries overlap.

## After Completing Work

If you discovered something that would save a future session time:
1. Suggest running `/_wrapup` to persist context
2. Or at minimum, update `.project/CURRENT_WORK.md` with the current status

## Don't Re-Research What's Already Documented

Before exploring the codebase to understand how something works, check:
- `.project/learnings/` for prior discoveries about this area
- `~/.claude/learnings/` for machine-wide knowledge
- Project docs (often in `docs/`) for existing documentation
- `.project/research/` for previous deep investigations
- `.project/CURRENT_WORK.md` for recent work that may already cover the area
