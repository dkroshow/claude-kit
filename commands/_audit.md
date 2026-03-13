# Audit Command

**Purpose:** Cross-phase verification of completed implementation
**Input:** Completed implementation with plan.md and spec.md
**Output:** Audit report with requirement coverage, integration assessment, and test adequacy

## Overview

Lightweight final verification that the implementation meets the spec. Run this after `/_implement` completes all phases.

Note: Per-phase auditing happens during `/_implement` itself. This command is for the final cross-phase check.

## Process

1. **Read plan.md and spec.md** — understand what was supposed to be built

2. **Requirement Coverage**:
   - Map each FR/AC from spec.md to implemented code
   - Use `Task` tool with `subagent_type=Explore` to verify implementations exist
   - Flag any requirements without corresponding implementation

3. **Cross-Phase Integration**:
   - Do phases work together correctly?
   - Are there integration gaps between components built in different phases?
   - Does data flow correctly across phase boundaries?

4. **Test Adequacy**:
   - Are all acceptance criteria covered by tests?
   - Are there systemic gaps (e.g., only happy path tested)?
   - What manual testing is still needed?

5. **Present Report**:
   ```
   ## Audit Report

   ### Requirement Coverage
   | Requirement | Status | Location |
   |------------|--------|----------|
   | FR-1 / AC-1 | Covered | file:line |
   | FR-2 / AC-2 | Gap | [explanation] |

   ### Cross-Phase Integration
   - [Integration point]: [Status]

   ### Test Adequacy
   - [Coverage summary]
   - [Gaps identified]

   ### Recommendations
   - [Any follow-up actions needed]
   ```

---

**Related Commands:**
- Before audit: `/_implement`
- Quality standard: `skills/simplify-standard.md`

**Last Updated**: 2026-03-02
