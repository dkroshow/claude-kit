# Blurb

**Purpose:** Generate a compact reload blurb for a fresh Claude Code session. Writes a targeted handoff file with session context, then generates a blurb pointing to it. Designed to be pasted after `/clear` or into a new session.

## Usage

```
/_blurb
```

This is the standalone version. For wrap-up + blurb in one shot, use `/_wrapup --blurb`.

## Instructions

### Step 1. Gather Context

- Run `git branch --show-current` and `git status --porcelain` for branch/state
- Review the conversation for: active work, current status, session-specific gotchas
- Check `.project/active/` for directories with `plan.md` or `spec.md`

### Step 2. Write Handoff File

Write a targeted context file to `.project/handoffs/{feature-slug}.md`. This file contains **only** the context the next session needs for this specific work stream.

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

### Step 3. Compose the Blurb

**If mid-flow on a feature** (the default assumption):
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

### Step 4. Output

- Present inside a fenced code block
- Add "Copy this into your next session:" above
- Add "After pasting, `/clear` this session or start a new one." below

## Blurb Rules

- 5-15 lines
- Directive tone (tell Claude what to do, not what happened)
- No sensitive info
- Concrete file paths (only reference files that exist)
- Include gotchas only if they'd affect the next session

---

**Related Commands:**
- `/_wrapup --blurb` — full wrap-up + blurb in one shot
- `/_wrapup` — session persistence without blurb

**Last Updated**: 2026-03-10
