# Project Management

This folder contains project planning, tracking, and documentation.

---

## Workflow

### 1. Collect & Prioritize

- Accumulate needs in `backlog/BACKLOG.md`
- Create epics with outcomes, goals, and known work items
- Prioritize using P0-P3 levels

### 2. Execute

Iterate through items using the claude-kit pipeline:

| Step | Command | Output |
|------|---------|--------|
| **Spec** | `/_spec` | `spec.md` — requirements + acceptance criteria |
| **Plan** | `/_plan` | `plan.md` — design + phased implementation |
| **Implement** | `/_implement` | Code changes with per-phase validation |
| **Audit** | `/_audit` | Cross-phase verification |

Or use `/_cycle` to orchestrate automatically with tiered complexity.

### 3. Clean Up

1. Run `/_wrapup` to persist context and prune completed items to `PAST_WORK.md`
2. Move archived spec/plan folders to `completed/` with date prefix
3. Use `/_status close [item]` to automate

---

## Folder Structure

```
.project/
├── CURRENT_WORK.md           # Active work tracking (pruned to recent)
├── PAST_WORK.md              # Archive of completed work
├── backlog/
│   ├── BACKLOG.md            # Prioritized epic list
│   └── epic_*.md             # Epic definitions
├── active/
│   └── {item_name}/          # Work-in-progress items
│       ├── spec.md
│       └── plan.md
├── completed/
│   └── {date}_{item_name}/   # Archived spec/plan folders
├── research/                 # Deep investigations
└── learnings/
    ├── index.md              # Learning index (scanned by Claude)
    └── {date}-{topic}.md     # Individual learning files
```

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `/_cycle` | Tiered workflow orchestrator (recommended entry point) |
| `/_spec` | Feature requirements definition |
| `/_plan` | Technical design + implementation planning |
| `/_implement` | Execute plan with per-phase validation |
| `/_audit` | Final cross-phase verification |
| `/_wrapup` | Persist session context + capture learnings |
| `/_blurb` | Generate reload blurb for next session |
| `/_research` | Deep codebase exploration |
| `/_status` | Project management and status |

---

**Last Updated**: Template
