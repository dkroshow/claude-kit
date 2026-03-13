# Research: Integrating Quality Review Into Implementation

**Date:** 2026-03-13
**Status:** Complete
**Researcher:** Claude

---

## TL;DR

Code quality checks (`/_quality`, `/simplify`) currently run as post-hoc passes, forcing large batch rewrites. The fix is to embed quality review directly into the per-phase implementation loop — specifically by enriching `implement-standard.md` with simplify's review criteria and adding a self-review step to `/_cycle` Phase 3. This makes every implementation phase produce clean code the first time, rather than writing it twice. Three integration layers work together: a global rule for baseline behavior, enriched standards for structured workflows, and an optional agent-verified pass for `--ralph` mode.

---

## Research Question

How can `/_quality` and `/simplify` be integrated into the implementation workflow so code is generated at higher quality from the start, rather than requiring post-hoc overhauls?

## Methodology

- Read all workflow commands: `/_cycle`, `/_implement`, `/_quality`
- Read quality standards: `implement-standard.md`, `plan-standard.md`
- Read simplify agent definition (code-simplifier plugin)
- Analyzed hooks infrastructure for auto-trigger options
- Reviewed session 12 notes for real-world simplify impact
- Mapped the gap between what quality gates check and what simplify catches

## Findings

### 1. Current Quality Infrastructure

**`/_quality`** (`commands/_quality.md`): Standalone command that runs external tools (tests, linters, type checkers, formatters), triages issues by risk level, auto-fixes low-risk issues. Designed to run *after* implementation.

**`/simplify`** (code-simplifier plugin at `~/.claude/plugins/.../code-simplifier/`): Agent that reviews recently modified code for clarity, redundancy, naming, structure, over-engineering. Applies subjective code review, not just mechanical checks. Also designed to run *after* code is written.

**`implement-standard.md`** (`skills/implement-standard.md`): Defines the per-phase quality gate used by `/_implement` and `/_cycle`. Currently includes:
- Run tests, linting, type checking, formatting
- Triage issues by risk
- Per-phase audit: completion accuracy, deviation justification, test coverage
- Code quality rules: no mocks without real validation, no silent stubs, no TODOs

### 2. The Gap

The implement standard's quality gate runs **external tools** (linters, tests) and checks **completeness** (no TODOs, no stubs). What it does NOT do is the **subjective code review** that simplify provides:

- Reducing unnecessary complexity and nesting
- Eliminating redundant code and abstractions
- Improving variable/function naming
- Consolidating related logic
- Removing unnecessary comments
- Checking abstraction quality and balance
- Spotting duplicate reads, unnecessary iterations, extractable constants

**Evidence from session 12:** Simplify caught three real issues the quality gate missed: double file read (parsing JSONL twice), unextracted tool name constants, and incorrect reverse iteration in health assessment (`CURRENT_WORK.md:43`).

### 3. Why Post-Hoc Fails

1. **Context loss** — by the time simplify runs, the implementation context has been flushed from working memory
2. **Batch size** — reviewing an entire feature's diff at once is harder than reviewing one phase at a time
3. **Wasted effort** — code is written once then rewritten, doubling token spend and wall time
4. **Compounding** — poor patterns in Phase 1 get copied into Phase 2-N, then all must be fixed

### 4. Available Integration Points

| Point | Mechanism | Pros | Cons |
|-------|-----------|------|------|
| Global rule | `rules/` file loaded every session | Always active, zero ceremony | No structured checklist, relies on model discipline |
| implement-standard.md | Enriched quality gate | Part of existing flow, per-phase | Only active during `/_cycle`/`/_implement` |
| `/_cycle` Phase 3 loop | Self-review step after each phase | Explicit, auditable | Adds latency per phase |
| `--ralph` agent | Spawn simplify agent for verification | Independent review, catches blind spots | Slowest option, token-heavy |
| Hooks | Shell command on file edit | Automatic trigger | Hooks are shell commands, can't invoke skills; would need to be a linter-like tool |

### 5. What simplify Actually Checks (Distilled)

From the code-simplifier agent definition, the actionable review criteria:

1. **Redundancy**: Duplicate logic, repeated reads/computations, copy-paste patterns
2. **Abstraction level**: Over-abstraction (premature helpers) or under-abstraction (inline repetition)
3. **Naming**: Variables/functions that don't communicate intent
4. **Nesting depth**: Deep conditionals that could be flattened (early returns, guard clauses)
5. **Dead code**: Unused variables, unreachable branches, commented-out code
6. **Constants**: Magic strings/numbers that should be extracted
7. **Data flow**: Unnecessary intermediate variables, convoluted transformations
8. **Separation of concerns**: Functions doing too many things

## Conclusions

The fix is a **three-layer approach** that embeds quality review at different granularities:

### Layer 1: Global Rule (Always Active)
A new rule file that instructs Claude to re-read code it just wrote and apply simplify-like review. This is the lightest touch — it applies to ALL coding work, not just `/_cycle`. It's a behavioral instruction, not a structured checklist.

### Layer 2: Enriched Implement Standard (Structured Workflows)
Add the distilled simplify criteria to `implement-standard.md` as part of the per-phase quality gate. This makes the review checklist explicit and auditable within `/_cycle` and `/_implement`.

### Layer 3: Agent-Verified Review (--ralph Mode)
In `/_cycle`'s Phase 3, when `--ralph` is active, spawn the code-simplifier agent after each implementation phase to independently review the code. This catches blind spots that self-review misses.

## Open Questions

1. **Performance impact**: Does per-phase self-review add meaningful latency to `/_cycle`? Likely small compared to implementation itself, but worth monitoring.
2. **Rule compliance**: Will a global rule be followed consistently, or does it need to be more structural? May need to test across several sessions.
3. **Simplify skill existence**: The `/simplify` skill appears in the skill list but has no local definition file in `skills/` — it's coming from the code-simplifier plugin. Should there also be a local skill definition for consistency with the `/_quality` command?

## Recommendations

| # | Recommendation | Evidence (file:line or verified behavior) |
|---|---|---|
| 1 | Add a global rule `rules/code-quality.md` that instructs Claude to re-read and refine code after writing each logical chunk | No such rule exists in `rules/` (only context-loading, workflow-accountability, conversation-history). Session 12 notes confirm simplify catches issues the base implementation misses (`CURRENT_WORK.md:43`) |
| 2 | Enrich `implement-standard.md` Code Quality Gate with simplify's review criteria (redundancy, naming, nesting, constants, dead code, separation of concerns) | Current quality gate (`implement-standard.md:12-18`) only covers external tool checks (tests, lint, types, formatting) — no subjective code review criteria |
| 3 | Add a "Code Review" self-check step to `/_cycle` Phase 3, after the quality gate and before the per-phase audit | `_cycle.md:211` runs quality gate then goes straight to per-phase audit — no review of code quality itself |
| 4 | In `--ralph` mode, spawn code-simplifier agent after each phase as an independent reviewer | `--ralph` already spawns validation agents for scope, requirements, and test adequacy (`_cycle.md:251-255`) but not for code quality |
| 5 | Create a local `skills/simplify-standard.md` that distills the review criteria from the code-simplifier plugin into a referenceable standard (like implement-standard.md) | Review criteria currently only exist in plugin agent definition (`~/.claude/plugins/.../code-simplifier/agents/code-simplifier.md`), not accessible as a project-level standard |

---

**Next Steps:** `/_spec` to define requirements for the changes, or implement directly since the changes are well-scoped edits to existing files.
