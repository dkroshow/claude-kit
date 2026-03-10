# Research Command

**Purpose:** Deep codebase and topic exploration with persistent documentation
**Input:** Research question or area to investigate
**Output:** `.project/research/{topic}.md`

## Overview

You are a research specialist agent. Conduct thorough investigation of codebases, technologies, or approaches, then document findings as a persistent research artifact.

When invoked:
- If topic provided: proceed to research
- If no topic: ask "What would you like me to research?"

## Process

### Stage 1: Context Gathering

1. **Read CLAUDE.md** for project structure and conventions
2. **Check existing research** in `.project/research/` — avoid duplicating prior work
3. **Check prior learnings:**
   - Read `.project/learnings/index.md` and `~/.claude/learnings/index.md` if they exist
   - Prior learnings may already answer parts of the research question
4. **Clarify scope** with user if the question is broad

### Stage 2: Parallel Research

1. **Spawn exploration agents** for broad codebase searches:
   - Use `Task` tool with `subagent_type=Explore` for codebase exploration
   - Use `Task` tool with `subagent_type=general-purpose` for web research if needed
   - Run multiple agents in parallel when investigating independent areas

2. **Direct investigation** for targeted questions:
   - Use Grep/Read for specific file/pattern searches
   - Read relevant source files fully before spawning agents

### Stage 3: Analysis & Synthesis

1. **Collect results** from all research threads
2. **Identify patterns**: What's consistent across findings?
3. **Note contradictions**: Where do findings conflict?
4. **Draw conclusions**: What does this mean for the project?
5. **Identify gaps**: What remains unknown?

### Stage 4: Document Creation

Write to `.project/research/{topic}.md`:

```markdown
# Research: [Topic]

**Date:** [YYYY-MM-DD]
**Status:** Complete | Partial | Needs Follow-up
**Researcher:** Claude

---

## TL;DR
[5-10 lines summarizing key findings and conclusions]

---

## Research Question
[What we set out to understand]

## Methodology
[What was investigated and how]

## Findings

### [Finding Area 1]
[Details with file:line references where applicable]

### [Finding Area 2]
[Details]

## Conclusions
[What this means for the project]

## Open Questions
[What remains unknown or needs further investigation]

## Recommendations

[Each recommendation must cite source evidence confirming the gap exists]

| # | Recommendation | Evidence (file:line or verified behavior) |
|---|---|---|
| 1 | ... | ... |

---

**Next Steps:** [e.g., `/_spec` to define requirements, `/_plan` to design]
```

## Guidelines

- Read CLAUDE.md first for project context
- Read existing files before spawning agents (give agents targeted prompts)
- Wait for all agents to complete before synthesizing
- Include file:line references for codebase findings
- For each recommendation, verify the gap exists in source code before including it
- Keep the document useful for someone who hasn't seen the research process

---

**Related Commands:**
- After research: `/_spec` to define requirements, `/_plan` to design
- During `/_cycle`: Research is available as Phase 0.5

**Last Updated**: 2026-03-02
