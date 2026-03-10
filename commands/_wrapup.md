# Wrap Up

**Purpose:** End-of-session command to persist context for future sessions. Updates CURRENT_WORK.md, detects stale knowledge, and captures structured learnings so the next session doesn't re-research what you just figured out.

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

Update `.project/CURRENT_WORK.md` to reflect the session's work. CURRENT_WORK.md is a **thin index** — pointers to specs/plans, not duplicated content. Keep it small so session boot stays cheap.

- **Active table** — update status and phase for active items. Add new rows for work started this session. Each row should point to its spec/plan location.
- **Move completed items** from "Active" to "Recently Completed" with date. The entry is just the item name + location pointer — detail lives in the spec/plan.
- **Prune "Recently Completed"** — keep only the 3 most recent entries. Move older entries to `.project/PAST_WORK.md` (prepend them, newest first). Create the file if it doesn't exist.
- **Prune "Session Notes"** — keep only the 3 most recent sessions. Drop older notes (they're preserved in git history; important bits should already be in learnings).
- **Small fixes without specs** — one-line entries are fine (e.g., `| 2026-03-06 | Fixed init.sh return codes | — |`). Don't create specs just for index completeness.
- **Update "Up Next"** if priorities shifted

### Step 3. Check Knowledge Staleness

Check whether this session's code changes affect files covered by existing knowledge artifacts.

1. **Read `.project/file-knowledge-map.md`** — if it doesn't exist, create it with the standard header and empty table, then proceed to step 2:
   ```markdown
   # File-Knowledge Map

   > Maps source files to the learnings and docs that cover them.
   > Maintained by `/_wrapup`. Used by `/_wrapup` staleness check.

   | Source File | Knowledge Artifact | Last Verified |
   |---|---|---|
   ```

2. **Rebuild if empty** — if the map has no data rows (only headers), scan all project learnings and backfill the map:
   - Read each learning file in `.project/learnings/` (skip `index.md`)
   - **Primary source:** Extract file paths from `## Key Files` sections
   - **Fallback:** If a learning has no `## Key Files` section, scan its body for references to project files (relative paths like `src/foo.ts`, `commands/bar.md`, etc.). Include paths that clearly refer to files in the repo — skip vague references.
   - Add one row per file: `| {source-file-path} | learnings/{filename}.md | {today's date} |`
   - If any learnings lacked a `## Key Files` section but had file references found via fallback, add a `## Key Files` section to those learnings listing the paths you mapped (keeps them as the source of truth going forward)
   - Report: "Rebuilt file-knowledge map from {N} learnings ({M} file entries)"

3. **Get changed files** — use the git diff/log output from Step 1 to identify source files changed this session.

4. **Cross-reference** — check if any changed files appear in the file-knowledge map's "Source File" column.

5. **If matches found**, present them to the user:
   ```
   These knowledge artifacts cover files you changed this session:
   - learnings/20260301-auth-bug.md (covers src/auth/login.ts, src/auth/middleware.ts)
   - docs/api-layer.md (covers src/api/routes.ts)

   Do any of these need updating, or are they still current?
   ```

6. **Based on user response:**
   - **Still current** → update the `Last Verified` date for those entries in the file-knowledge map
   - **Needs updating** → update the artifact now while you're still in context, then update `Last Verified`
   - **Mixed** → handle each artifact individually

### Step 4. Capture Learnings

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

   **Standard format:**
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
   [Relevant file paths — list every source file this learning covers.
   Include files you changed, debugged, or discovered something about.]
   ```

   **For gotchas with multiple failure modes**, replace "What Didn't Work" / "What Works" with a structured table:
   ```markdown
   ## Symptoms & Fixes

   | Symptom | Cause | Fix |
   |---|---|---|
   | [Observable symptom 1] | [Root cause] | [Solution] |
   | [Observable symptom 2] | [Root cause] | [Solution] |
   ```
   Use the table format when there are 2+ distinct failure modes. For simple single-issue gotchas, the prose format is fine.

3. **Update the learning index** — Add a row to `{learnings-dir}/index.md`:
   ```
   | YYYY-MM-DD | type | tags | one-line summary | filename.md |
   ```

4. **Update the file-knowledge map** — If the learning has a `## Key Files` section and is project-specific, add entries to `.project/file-knowledge-map.md`:
   ```
   | {source-file-path} | learnings/{filename}.md | {today's date} |
   ```
   Add one row per file listed in `## Key Files`. Create the map file if it doesn't exist.

5. **Clean up orphaned entries** — If `.project/file-knowledge-map.md` exists, scan for entries pointing to knowledge artifacts that no longer exist. Remove orphaned rows.

6. **If a learning is critical enough for always-loaded** (dangerous to miss, applies to every session):
   - Recommend adding it to CLAUDE.md: "This seems critical enough for CLAUDE.md — should I add it?"
   - Only add with user approval

**Learning types:**
- `environment` — Machine/tooling facts (Python version, CLI quirks)
- `gotcha` — Pitfalls, failures, things that don't work
- `pattern` — Conventions, what works, decisions and rationale

**Consider escalating to an agent:** If this session involved extended debugging (3+ cycles of hypothesis → test → failure) in a specific domain, suggest creating a domain-expert agent rather than just a learning: "This debugging session was complex enough that a domain-expert agent might be more valuable than a learning. Want me to create an agent spec in `agents/` for [domain area]?"

### Step 4.5. Distill Learnings (if threshold exceeded)

After capturing new learnings, check whether the learnings directory needs distillation.

1. **Count learning files** in `.project/learnings/` (exclude `index.md` and `file-knowledge-map.md`).

2. **If count ≤ 20**, skip this step entirely.

3. **If count > 20**, run distillation:

   a. **Read all learning files** and categorize each as:
      - **Stable** — confirmed patterns, domain facts, recurring gotchas. Indicators: created >3 days ago, referenced or re-confirmed in multiple sessions, describes a permanent characteristic of the codebase.
      - **Provisional** — recent discoveries, single-session findings, things that might change. Keep these in learnings.

   b. **Determine promotion targets** for stable learnings:
      - Domain knowledge, data model facts, architectural patterns → `docs/ARCHITECTURE.md` (create if needed, add `Read docs/ARCHITECTURE.md before starting work.` to CLAUDE.md)
      - Critical gotchas that affect every session → CLAUDE.md directly
      - Stable conventions/patterns → project docs or CLAUDE.md, whichever fits

   c. **Present the promotion plan** to the user:
      ```
      Learnings distillation triggered ({N} files, threshold is 20).

      Promote to docs/ARCHITECTURE.md:
      - {learning}: {one-line summary}
      - ...

      Promote to CLAUDE.md:
      - {learning}: {one-line summary}

      Keep as provisional ({M} files):
      - {learning}: {reason}
      - ...

      Proceed?
      ```

   d. **On approval:**
      - Write promoted content into target docs (merge with existing content, don't duplicate)
      - Delete promoted learning files
      - Remove their rows from `index.md`
      - Clean up any orphaned entries in `file-knowledge-map.md`

   e. **Fast-boot declaration** — if the project's CLAUDE.md doesn't already declare a fast-boot path (per `rules/context-loading.md` Step 0), suggest adding one:
      ```
      The learnings are now distilled into durable docs. Want me to add a
      fast-boot declaration to CLAUDE.md so new sessions skip the learnings
      scan and just read CLAUDE.md + ARCHITECTURE.md?
      ```

### Step 5. Update Docs (if applicable)

If the session involved changes that affect documented behavior:
- Architecture changes → update relevant docs
- New commands/features → update relevant docs
- Only update docs that already exist

### Step 6. Report

```
Wrap-up complete:
- CURRENT_WORK.md: [what changed]
- Staleness: [artifacts flagged and resolved, or "no stale artifacts" or "no index yet"]
- Learnings: [what was captured, or "none this session"]
- Distillation: [N learnings promoted, M remaining / "not needed (N files, threshold 20)" / "skipped"]
- Docs: [which files updated, or "none needed"]
```

If `--quick` was passed, only do Steps 1, 2, and 6 (skip staleness check, learnings, and docs).

If `--blurb` was passed, proceed to Step 8 after committing.

### Step 7. Commit

1. Stage the files that were updated
2. Commit with message: `chore: wrap-up session context`
3. Do NOT push unless the user asks

### Step 8. Generate Reload Blurb (only with `--blurb`)

If `--blurb` was passed, generate a compact reload blurb after wrap-up completes. This blurb is designed to be pasted into a fresh session after `/clear`.

#### 8a. Gather context

- Run `git branch --show-current` and `git status --porcelain`
- Review the conversation for active work and current status
- Check `.project/active/` for directories with `plan.md` or `spec.md`

#### 8b. Write handoff file

Write a targeted context file to `.project/handoffs/{feature-slug}.md`. This file contains **only** the context the next session needs for this specific work stream — not a dump of all project activity.

- **Feature slug**: derived from the feature/task name (kebab-case). Use `general` if the session wasn't focused on a specific feature.
- **Create `.project/handoffs/` directory** if it doesn't exist.

**Handoff file template:**
```markdown
# Session Handoff: {Feature/Task Name}

**Written:** {date}
**Branch:** `{branch}`
**Status:** {current status — what phase, what's done, what's next}

## Context
{2-5 sentences: what this work stream is, what was accomplished this session, where it stands now}

## Key Decisions
{Bulleted list of decisions made this session that the next session needs to know. Omit section if none.}

## Gotchas
{Anything that would trip up the next session — failed approaches, non-obvious constraints, environment issues. Omit section if none.}

## Key Files
- `.project/active/{feature}/plan.md` — plan with progress checkboxes
- `.project/active/{feature}/spec.md` — requirements
- {other key source files relevant to this stream}

---
*Delete this file after reading.*
```

**Handoff file rules:**
- Max ~50 lines. This is a context bootstrap, not documentation.
- Only include information relevant to **this work stream**. Do not summarize other streams.
- Only reference files that exist.

#### 8c. Compose the blurb

**If mid-flow on a feature:**
```
I'm picking up where a previous session left off.

**Branch:** `{branch}` ({clean/dirty})
**Working on:** {feature/task — what it is and current status}

Read `.project/handoffs/{feature-slug}.md` for full session context, then delete it.
Also read any spec/plan files it references.

Only read `.project/CURRENT_WORK.md` if you're clearly missing project context not covered above.

Then ask me what I'd like to work on.
```

**If between features / no active work:**
```
I'm picking up where a previous session left off.

**Branch:** `{branch}` ({clean/dirty})
**Status:** {brief summary — e.g. "just finished X, nothing actively in progress"}

Read `.project/handoffs/general.md` for session context, then delete it.

Only read `.project/CURRENT_WORK.md` if you're clearly missing project context not covered above.

Then ask me what I'd like to work on.
```

#### 8d. Blurb rules

5-15 lines, directive, no sensitive info, concrete file paths, only reference files that exist.

#### 8e. Output

Present inside a fenced code block with "Copy this into your next session:" above.

---

**Related Commands:**
- `/_blurb` — standalone reload blurb (without wrap-up)
- `/_cycle` — the main workflow pipeline

**Last Updated**: 2026-03-10
