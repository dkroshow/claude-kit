# Blurb

**Purpose:** Generate a compact reload blurb for a fresh Claude Code session. Designed to be pasted after `/clear` or into a new session.

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
- Read `.project/CURRENT_WORK.md` for current state

### Step 2. Compose the Blurb

**If mid-flow on a feature** (the default assumption):
```
I'm picking up where a previous session left off.

**Branch:** `{branch}` ({clean/dirty})
**Working on:** {feature/task — what it is and current status}
**Current phase:** {phase N of plan / "implementation complete, needs X" / "no formal plan"}

Read these files to get oriented:
- `.project/CURRENT_WORK.md` — active work, recent decisions, session notes
- `.project/active/{feature}/plan.md` — plan with progress checkboxes
- {any other key files, e.g. spec.md, a specific source file}

{1-2 lines of gotchas or key decisions from this session, if any}

Then ask me what I'd like to work on.
```

**If between features / no active work:**
```
I'm picking up where a previous session left off.

**Branch:** `{branch}` ({clean/dirty})
**Status:** {brief summary — e.g. "just finished X, nothing actively in progress"}

Read `.project/CURRENT_WORK.md` for context on recent work and what's up next.

Then ask me what I'd like to work on.
```

### Step 3. Output

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

**Last Updated**: 2026-03-02
