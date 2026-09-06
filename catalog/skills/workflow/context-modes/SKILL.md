---
name: context-modes
description: Switch the agent's working posture by adopting a named mode (dev, review, research) that retunes priorities, tool preferences, and stopping conditions. Make sure to use this skill whenever the user says "switch to dev mode", "switch to review mode", "switch to research mode", "enter review posture", "act as a reviewer", "we are researching", "research mode", "code-first mode", or otherwise asks the agent to behave like a different specialist for the rest of the session, even when the word "mode" is not used. Also trigger when the user pivots from one phase of work to another (e.g., from designing to reviewing, or from researching to implementing) and the prior posture would now be wrong. SKIP, do NOT use for, one-off tone changes, single-message rephrasing requests, persona role-plays unrelated to engineering work, or selecting between competing implementation approaches (use plan-before-code for that).
summary_l0: "Switch the agent's working posture (dev, review, research) with explicit entry, exit, and reset rules"
overview_l1: "This skill defines three named working modes for the agent (dev, review, research) and the explicit rules for entering, exiting, and switching between them. Each mode retunes the agent's defaults: dev favors writing code, running tests, and small atomic commits; review favors reading carefully, citing line numbers, and refusing to write code; research favors fetching evidence, comparing options, and producing a written report. The skill teaches the agent to recognize when a user has implicitly switched modes, to announce the mode change, to scope its own behavior accordingly until the user asks for something the current mode forbids, and to refuse silent mode drift. Each mode is defined in a referenced fragment under references/ (references/dev.md, references/review.md, references/research.md) so the body stays terse. Trigger phrases: dev mode, review mode, research mode, switch modes, enter review, act as reviewer."
---

# Context Modes

Adopt a named working posture (`dev`, `review`, or `research`) so the agent's priorities, tool choices, and stopping conditions match the user's current phase of work. Without explicit modes, the agent silently mixes review behavior into implementation work (slow, hedging) or implementation behavior into review (writes code instead of reading carefully). This skill makes the posture explicit.

## When to Use This Skill

Use when:

- The user asks for a specific posture: "switch to review mode", "enter research mode", "act as a reviewer".
- The user implicitly pivots phase: "OK, now let's look at the PR" (review), "before we code, what are the options?" (research), "ship the next sub-task" (dev).
- The current session has been in one mode and the next request would be wrong under that mode (e.g., user is in research mode and asks "go ahead and implement option 2" -- switch to dev before writing code).
- A skill or command names a mode it expects (a plan asks for a "review pass"; a runbook says "in research mode...").

**When NOT to use:**

- One-off tone changes ("be more concise") -- that is not a mode switch, just a preference.
- Persona role-play unrelated to engineering ("pretend you are a pirate") -- out of scope.
- Picking between competing implementation approaches -- use [[plan-before-code]] for that.
- Selecting a category of skill (e.g., choosing between language-specialist skills) -- that is skill routing, not mode.

## The Three Modes

| Mode | Posture | Primary tools | Forbidden actions |
|---|---|---|---|
| `dev` | Write code first, ship sub-tasks, keep commits atomic. | Edit, Write, Bash (tests / lint / build), Read for code under change. | Long survey reads, hedged language, refusing to make small decisions. |
| `review` | Read carefully, cite file:line, do not write code. | Read, Grep, Glob, git diff via Bash. | Edit / Write to source files, running tests as the primary action, scope creep into refactors. |
| `research` | Compare options, gather evidence, produce a written report. | Read, Grep, WebFetch / WebSearch when authorized, Bash for `git log` and analysis. | Editing source code, committing, choosing the option for the user without surfacing alternatives. |

Per-mode details are in `references/dev.md`, `references/review.md`, and `references/research.md`. Read the relevant fragment when entering a mode; do not memorize all three.

## Instructions

### 1. Detecting a mode switch

Look for either form:

- **Explicit**: the user names a mode (`dev`, `review`, `research`, `coding mode`, `review pass`, `research mode`, `research this first`).
- **Implicit**: the user requests work that is characteristic of a mode (`look at this PR` → review; `what are our options for X?` → research; `ship the next sub-task` → dev).

If both forms point to the same mode, switch. If they conflict, ask which mode the user wants for the next turn before acting.

### 2. Entering a mode

When entering or switching mode, announce it in one short line and read the corresponding fragment if the mode is new in this session:

```
Entering review mode. (Read references/review.md if needed.)
```

Then load the fragment's rules into the working context and behave by them.

### 3. Operating inside a mode

For the duration of the mode:

- Honor the mode's primary tools and avoid its forbidden actions.
- Use the mode's exit-criteria language. `dev` stops when sub-task is shipped and tests are green; `review` stops when the diff is fully covered with findings; `research` stops when a written report exists with the alternatives compared.
- If the user asks for something the mode forbids (e.g., asks for code while in `review`), surface the conflict: "I am in review mode -- should I switch to dev to make that change?"

### 4. Switching modes mid-task

When the user pivots (e.g., approves the research conclusion and wants implementation), announce the switch:

```
Research mode concluded. Switching to dev to implement option 2.
```

Do NOT silently slide between modes. Each switch is announced.

### 5. Exiting all modes

If the user asks the agent to "drop the mode" or signals the session is over, return to default behavior (no mode flagged). Default behavior is the harness's normal posture as defined elsewhere in `AGENTS.md` and the user's CLAUDE.md.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I do not need to announce the mode -- the user knows what they asked for" | A silent mode switch hides the agent's posture. The user cannot tell whether the next response will be code, prose, or analysis. One short announcement (`Entering review mode.`) is cheap and prevents misaligned output. |
| "Modes are arbitrary -- I can just blend behaviors as needed" | Blending behaviors is exactly the failure this skill is designed to prevent. Review with editing privileges turns into "I changed it for you", which bypasses the user's review. Research with implicit implementation produces code instead of options. The boundaries are the point. |
| "Switching modes is too rigid for fluid sessions" | The skill is not rigid about which mode to be in -- only that the mode is named when it changes. A session can move dev -> research -> dev in three turns; each switch costs one sentence. |
| "If I notice the user is in research mode, I should just answer the research question and not bother with the mode framework" | The user may not know they are in research mode. Naming it gives them the chance to redirect ("no, just implement option 2 -- skip the comparison"). Silent compliance loses that off-ramp. |

## Verification

- [ ] When a mode is entered, the agent emits a single-line announcement naming the mode.
- [ ] When the mode requires a fragment that is not in the working context, the agent reads `references/<mode>.md` before acting under the mode.
- [ ] Forbidden actions for the active mode are refused or routed to a mode switch (e.g., review-mode edit requests prompt "switch to dev?").
- [ ] When the user pivots phases, the agent announces the mode switch before the first action of the new mode.
- [ ] On exit, the agent confirms it is no longer in a named mode.

## Related Skills

- [[context-engineering]] -- shapes WHAT is in the context window; this skill shapes the agent's POSTURE inside that context.
- [[context-optimization]] -- reduces token cost; mode switches do not save tokens, they sharpen behavior.
- [[plan-before-code]] -- choosing what to do; modes choose HOW to behave while doing it.
- [[research-plan-implement]] -- a multi-phase workflow that naturally cycles through research -> dev with a review gate in between.
- [[incremental-implementation]] -- pairs with `dev` mode for atomic sub-task shipping.
