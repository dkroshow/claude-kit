# Status Command

**Purpose:** Project management — status reporting, backlog management, and work lifecycle
**Input:** Optional subcommand (default: full status report)
**Output:** Status report, updated project files, or backlog changes

## Usage

```
/_status                    # Full status report with gap analysis
/_status current            # What's active right now
/_status backlog            # Prioritized upcoming work
/_status history            # Completed work log
/_status close [item]       # Archive completed items
/_status decompose <epic>   # Break epic into backlog items
```

## Subcommand: (default) — Full Status Report

**Goal**: Comprehensive project status with gap analysis and recommendations.

### Process

1. **Read project files**:
   - `.project/CURRENT_WORK.md` — active work
   - `.project/backlog/BACKLOG.md` — upcoming work
   - Scan `.project/active/*/` — active items with spec/plan status
   - Scan `.project/completed/` — recent completions
   - `git log --oneline -10` — recent commits

2. **Analyze gaps**:
   - Items in active/ without spec.md or plan.md
   - Items with plan.md but unchecked phases
   - Stale items (no progress indicators)
   - Backlog items ready to start

3. **Present report**:
   ```
   ## Project Status

   ### Active Work
   | Item | Phase | Progress | Blockers |
   |------|-------|----------|----------|
   | [item] | [phase] | [X/Y phases] | [none/desc] |

   ### Recently Completed
   - [date]: [item] — [summary]

   ### Backlog (Top 3)
   1. [P1] [epic] — [summary]
   2. [P2] [epic] — [summary]

   ### Gap Analysis
   - [gaps found, if any]

   ### Recommendations
   - [suggested next actions]
   ```

---

## Subcommand: current

**Goal**: Quick view of what's active right now.

1. Read `.project/CURRENT_WORK.md`
2. Read active item specs/plans for status
3. Present concise summary of current work, phase, and blockers

---

## Subcommand: backlog

**Goal**: Prioritized view of upcoming work.

1. Read `.project/backlog/BACKLOG.md`
2. Read individual epic files if they exist
3. Present prioritized list with effort estimates and dependencies

---

## Subcommand: history

**Goal**: Completed work log.

1. Read `.project/PAST_WORK.md`
2. Scan `.project/completed/` for archived spec/plan folders
3. Present chronological summary of completed work

---

## Subcommand: close [item]

**Goal**: Archive a completed item with proper cleanup.

### Process

1. **Identify the item** — match `[item]` against `.project/active/` directories
2. **Confirm with user** what will be moved
3. **Archive**:
   - Move item directory: `git mv .project/active/{item} .project/completed/{YYYYMMDD}_{item}`
   - Update `.project/CURRENT_WORK.md` — move from active to recently completed
   - Prune recently completed if >3 entries — overflow to `.project/PAST_WORK.md`
   - Update `.project/backlog/BACKLOG.md` if item was part of an epic
4. **Check epic completion** — if all items in an epic are done:
   - Move epic file to completed/
   - Update backlog
   - Present completion summary

---

## Subcommand: decompose <epic>

**Goal**: Break an epic into actionable backlog items.

### Process

1. **Read the epic file** at `.project/backlog/epic_{name}.md` or `.project/backlog/{name}.md`
2. **If epic has no items yet**: Analyze the epic's goals and propose a breakdown:
   ```
   Based on the epic goals, here's a proposed breakdown:

   **Items:**
   1. [Item name] — [what it accomplishes] ([effort estimate])
   2. [Item name] — [what it accomplishes] ([effort estimate])
   3. [Item name] — [what it accomplishes] ([effort estimate])

   **Dependencies:**
   Item 2 depends on Item 1
   Item 3 can run in parallel with Item 2

   **Total estimated effort:** [X days]

   Want me to write these into the epic file?
   ```
3. **Wait for user feedback** — adjust as needed
4. **Update the epic file** with the approved breakdown
5. **Update BACKLOG.md** with item list under the epic

---

## Guidelines

- Read `.project/` files before making any changes
- Always confirm before moving/archiving files
- Keep reports concise — surface the important information
- Use `git mv` for archiving to preserve history
- Update all affected files atomically (CURRENT_WORK, BACKLOG, PAST_WORK)

---

**Related Commands:**
- `/_cycle` — start working on a backlog item
- `/_wrapup` — persist session context after work

**Last Updated**: 2026-03-02
