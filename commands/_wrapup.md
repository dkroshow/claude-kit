# Wrap Up

**Purpose:** End-of-session command to persist context for future sessions. Updates CURRENT_WORK.md and captures structured learnings so the next session doesn't re-research what you just figured out.

## Usage

```
/_wrapup                   # full wrap-up
/_wrapup --quick           # just update CURRENT_WORK.md
/_wrapup --blurb           # full wrap-up + generate a reload blurb
/_wrapup --quick --blurb   # quick wrap-up + reload blurb
```

## Instructions

### Step 1. Review What Changed

1. **Review the conversation** to identify what was worked on, decisions made, and problems solved this session.
2. **Cross-check with git** — run `git diff --stat` and `git log --oneline -5` to validate. If the git log contains commits from another concurrent session, ignore them — only summarize your own work.
3. Read `.project/CURRENT_WORK.md` to understand the current state.
4. Briefly summarize to the user: "Here's what happened this session: [summary]"

### Step 2. Update CURRENT_WORK.md

Update `.project/CURRENT_WORK.md` to reflect the session's work:
- **Move completed items** from "Active Work" to "Recently Completed" with date and status
- **Update active items** with current status, blockers, next steps
- **Add new items** if work was started but not finished
- **Update "Up Next"** if priorities shifted

### Step 3. Capture Learnings

Check whether this session produced knowledge that would save a future session time.

**Capture a learning if you discovered:**
- A gotcha or pitfall (API quirk, data format issue, edge case)
- A pattern or convention that isn't documented
- An approach that DIDN'T work (failure knowledge — equally valuable)
- A bug fix whose root cause wasn't obvious
- A key command or workflow that's easy to forget

**For each learning worth capturing:**

1. **Ask the user**: "Is this learning project-specific or machine-wide?"
   - **Project-specific** (default): Write to `.project/learnings/`
   - **Machine-wide** (e.g., Python version, CLI tool quirks): Write to `~/.claude/learnings/`

2. **Create a learning file** at `{learnings-dir}/{YYYYMMDD}-{topic-kebab-case}.md`:
   ```markdown
   ---
   type: [environment | gotcha | pattern]
   tags: [tag1, tag2, tag3]
   created: YYYY-MM-DD
   ---

   # [Topic Title]

   ## What
   [Concise description of the learning]

   ## Context
   [When/how this was discovered]

   ## What Didn't Work
   [Approaches that failed, if applicable]

   ## What Works
   [The solution or correct approach]

   ## Key Files
   [Relevant file paths, if applicable]
   ```

3. **Update the index** — Add a row to `{learnings-dir}/index.md`:
   ```
   | YYYY-MM-DD | type | tags | one-line summary | filename.md |
   ```

4. **If a learning is critical enough for always-loaded** (dangerous to miss, applies to every session):
   - Recommend adding it to CLAUDE.md: "This seems critical enough for CLAUDE.md — should I add it?"
   - Only add with user approval

**Learning types:**
- `environment` — Machine/tooling facts (Python version, CLI quirks)
- `gotcha` — Pitfalls, failures, things that don't work
- `pattern` — Conventions, what works, decisions and rationale

### Step 4. Update Docs (if applicable)

If the session involved changes that affect documented behavior:
- Architecture changes → update relevant docs
- New commands/features → update relevant docs
- Only update docs that already exist

### Step 5. Report

```
Wrap-up complete:
- CURRENT_WORK.md: [what changed]
- Learnings: [what was captured, or "none this session"]
- Docs: [which files updated, or "none needed"]
```

If `--quick` was passed, only do Steps 2 and 5.

If `--blurb` was passed, proceed to Step 7 after committing.

### Step 6. Commit

1. Stage the files that were updated
2. Commit with message: `chore: wrap-up session context`
3. Do NOT push unless the user asks

### Step 7. Generate Reload Blurb (only with `--blurb`)

If `--blurb` was passed, generate a compact reload blurb after wrap-up completes. This blurb is designed to be pasted into a fresh session after `/clear`.

1. **Gather context**:
   - Run `git branch --show-current` and `git status --porcelain`
   - Review the conversation for active work and current status
   - Check `.project/active/` for directories with `plan.md` or `spec.md`

2. **Compose the blurb** — if mid-flow on a feature:
   ```
   I'm picking up where a previous session left off.

   **Branch:** `{branch}` ({clean/dirty})
   **Working on:** {feature/task — what it is and current status}
   **Current phase:** {phase N of plan / "implementation complete, needs X"}

   Read these files to get oriented:
   - `.project/CURRENT_WORK.md` — active work, recent decisions, session notes
   - `.project/active/{feature}/plan.md` — plan with progress checkboxes
   - {any other key files}

   {1-2 lines of gotchas or key decisions from this session, if any}

   Then ask me what I'd like to work on.
   ```

3. **Blurb rules**: 5-15 lines, directive, no sensitive info, concrete file paths, only reference files that exist.

4. **Output**: Present inside a fenced code block with "Copy this into your next session:" above.

---

**Related Commands:**
- `/_blurb` — standalone reload blurb (without wrap-up)
- `/_cycle` — the main workflow pipeline

**Last Updated**: 2026-03-02
