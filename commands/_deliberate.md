# Deliberate Command

**Purpose:** Structured multi-model deliberation — Claude and Codex iterate on a document or debate a topic in alternating rounds until they converge.
**Input:** A document to refine, or a topic/question that benefits from adversarial review
**Output:** An improved document, or a resolution summarizing the agreed position and tradeoffs

## Usage

```
/_deliberate <topic or document description>
/_deliberate --rounds 5 <topic>
/_deliberate --file path/to/document.md <topic>
```

**Flags:**
- `--rounds N`: Maximum deliberation rounds (default: 3, no cap — use as many as needed to converge)
- `--one-shot`: Single-pass review — Codex reviews once, Claude incorporates, done. No back-and-forth.
- `--file <path>`: The document to refine, or shared context for a debate (absolute path)
- `--devil`: Codex argues the opposing position even if it agrees — forces stress-testing of assumptions (Debate types only)

When invoked:
- If topic provided: proceed to setup
- If no topic: ask "What should we deliberate on?"

---

## How It Works

Claude and Codex collaborate across alternating rounds. The interaction style depends on the deliberation type. The loop terminates when both models converge, or the round limit is reached.

Claude orchestrates: it sends work to Codex, evaluates the response, and decides whether another round is needed.

---

## Phase 1: Frame

1. **Understand the topic**: Read any `--file` context. If the topic references project files, read them.

2. **Identify the deliberation type**:

   **Refinement** (most common) — Iteratively improve a document. Each round, Codex reviews the current version and identifies issues. Claude evaluates the feedback, updates the document, and sends the new version back. Converges when Codex finds no blocking issues.

   **Decision** — Choose between alternatives (e.g., "Should we use approach A or B?")

   **Analysis** — Stress-test an idea (e.g., "Is this plan sound?")

   **Diagnosis** — Converge on root cause (e.g., "Why is this failing?")

3. **State the setup** to the user:
   ```
   **Topic:** {topic}
   **Type:** {Refinement / Decision / Analysis / Diagnosis}
   **Document:** {file path, if Refinement}
   **My opening take:** {your initial assessment, 2-4 sentences}
   **Rounds:** {N}

   Starting deliberation...
   ```

---

## Phase 2: Deliberate

### Refinement Flow

For each round (1 to N):

1. **Send document to Codex for review**:
   ```bash
   codex exec --full-auto --ephemeral \
     -m gpt-5.4 -c reasoning_effort=xhigh \
     "{refinement_prompt}"
   ```

   **Codex prompt template (round 1):**
   ```
   You are reviewing a document for quality. Read the file at: {absolute_file_path}

   {If additional context files: "Also read these for context: {paths}"}

   Review the document and identify issues. For each issue, respond with:
   - **Issue:** What's wrong (reference the specific section)
   - **Suggestion:** How to fix it
   - **Severity:** BLOCKING (must fix) / MINOR (should fix) / NIT (optional)

   After listing all issues, end with:
   - **Status:** CONVERGE if no blocking issues remain, or CONTINUE if there are blockers
   ```

   **Codex prompt template (round 2+):**
   ```
   You are reviewing a document that has been revised based on your prior feedback.

   Read the updated file at: {absolute_file_path}

   Prior review rounds:
   {summary of prior issues and how they were addressed}

   Review the document again. Focus on:
   - Whether prior blocking issues were adequately resolved
   - Any new issues introduced by the revisions
   - Remaining issues from prior rounds that weren't addressed

   Use the same format: Issue / Suggestion / Severity, then Status (CONVERGE or CONTINUE).
   ```

2. **Read Codex's response** and evaluate each issue:
   - Valid blocking issues → fix in the document
   - Valid minor/nit issues → fix if straightforward, note if not
   - Invalid issues (Codex lacks context) → skip, note why

3. **Update the document** with fixes applied.

4. **Present round summary to user**:
   ```
   **Round {N}:**
   - Codex found: {count} blocking, {count} minor, {count} nit
   - Applied: {what was fixed}
   - Skipped: {what was skipped and why, if any}
   - Status: {Converging / N blockers remain}
   ```

5. **Termination**: Stop when Codex returns CONVERGE (no blockers), max rounds reached, or same issues are repeating.

### Debate Flow (Decision / Analysis / Diagnosis)

For each round (1 to N):

1. **Formulate your position** — on round 1 this is your opening position. On subsequent rounds, respond to Codex's latest output:
   - What do you agree with?
   - What do you challenge, and why?
   - What new evidence or reasoning do you add?

2. **Send to Codex**:
   ```bash
   codex exec --full-auto --ephemeral \
     -m gpt-5.4 -c reasoning_effort=xhigh \
     "{debate_prompt}"
   ```

   **Codex prompt template (round 1):**
   ```
   You are participating in a structured deliberation about: {topic}

   {If --file: "Read this file for context: {absolute_path}"}
   {If --devil: "Your role is devil's advocate. Argue against the position presented, even if you agree with it. Find weaknesses, unstated assumptions, and failure modes."}

   Claude's opening position:
   {claude_position}

   Respond with:
   1. **Agree:** Points you accept (if any)
   2. **Challenge:** Points you dispute, with reasoning
   3. **Add:** New considerations Claude missed
   4. **Status:** CONVERGE if you broadly agree and have no substantive challenges, or CONTINUE if there are unresolved disagreements
   ```

   **Codex prompt template (round 2+):**
   ```
   You are participating in a structured deliberation about: {topic}

   {If --file: "Read this file for context: {absolute_path}"}
   {If --devil: "Your role is devil's advocate. Continue to stress-test — only CONVERGE when you cannot find further substantive weaknesses."}

   Deliberation so far:
   {all prior rounds}

   Claude's latest response:
   {claude_latest}

   Respond with the same structure: Agree / Challenge / Add / Status (CONVERGE or CONTINUE)
   ```

3. **Read Codex's response** and evaluate:
   - **If Codex says CONVERGE** and you also have no substantive challenges → end deliberation
   - **If Codex says CONTINUE** or raises valid challenges → formulate your response and continue
   - **If you disagree with Codex's challenges** → rebut with evidence and continue

4. **Present round summary to user** (keep it concise):
   ```
   **Round {N}:**
   - Codex challenged: {key point}
   - Claude's response: {key point}
   - Status: {Converging / Diverging on X / New consideration raised}
   ```

### User Intervention

Between any two rounds, the user may interject with guidance, corrections, or new information. If the user speaks:
- Incorporate their input into the next round's prompt to Codex
- Adjust your own position accordingly
- Do not treat the intervention as a termination signal unless the user says to stop

### Termination Conditions (both flows)

Stop the loop when ANY of these are true:
- Both models signal CONVERGE
- Maximum rounds reached (if `--rounds` was set)
- Positions/issues have stabilized (same points repeating)
- User asks to stop

---

## Phase 3: Resolve

### Refinement Resolution

1. **Present the final state**:
   ```
   ## Refinement Complete: {document name}

   **Rounds:** {N} | **Status:** {Clean (no issues) / Minor issues remaining}

   ### Changes Made
   - {change 1 — what and why}
   - {change 2}

   ### Remaining Issues (if any)
   - {minor/nit issues not addressed, with rationale}

   The updated document is at: {file path}
   ```

### Debate Resolution

1. **Synthesize the resolution**:
   - What was agreed on
   - What tradeoffs were identified
   - Any remaining dissent (points where the models didn't converge)
   - Confidence level: **Strong** (full convergence), **Moderate** (converged with caveats), **Weak** (significant dissent remains)

2. **Present to user**:
   ```
   ## Deliberation: {topic}

   **Rounds:** {N} | **Confidence:** {Strong / Moderate / Weak}

   ### Resolution
   {The agreed position, 3-8 sentences}

   ### Key Tradeoffs
   - {tradeoff 1}
   - {tradeoff 2}

   ### Dissent
   {Points where models disagreed, or "None — full convergence"}

   ### Recommendation
   {Actionable next step based on the resolution}
   ```

3. **If the deliberation affects project artifacts** (spec, plan, architecture), offer to apply:
   ```
   Want me to update {artifact} based on this resolution?
   ```

---

## Guidelines

### What This Is Good For
- Iterating on design docs, plans, or any document that benefits from a second pair of eyes
- Architecture and design decisions with real tradeoffs
- Stress-testing plans before implementation
- Debugging hypotheses when the root cause isn't obvious
- Challenging technical assumptions you're not sure about

### What This Is NOT
- Not for requirements/spec review — use one-shot Codex review (`/_spec --codex`, `/_plan --codex`) for that. Deliberation at the spec stage risks the reviewer inventing design choices instead of validating requirements.
- Not for trivial decisions (use your judgment)
- Not a replacement for user input on product/business decisions
- Not a way to avoid reading the codebase — both models should be grounded in code, not just reasoning in the abstract

### Prompt Discipline
- Always include the full deliberation history in each Codex prompt — Codex has no memory between calls
- For Refinement: Codex re-reads the file each round, so the document itself is the source of truth (no need to repeat content in the prompt)
- For Debate: keep individual positions focused (under 300 words per round per model) to avoid context bloat
- If `--file` is large, summarize the relevant parts in the prompt rather than relying on Codex to read and parse everything correctly

### Round Budget
- Default 3 rounds is sufficient for most topics
- No hard cap — the goal is convergence, not speed. Keep going until the answer is right.
- If rounds are climbing (5+) without progress, flag it to the user — they may want to intervene or redirect

---

**Related Commands:**
- `/_cycle` — uses deliberation automatically for spec and plan review (Standard/Complex tiers)
- `/_spec`, `/_plan` — standalone commands that offer deliberation after presenting output
- `/_research` — deep codebase exploration (single-model)
