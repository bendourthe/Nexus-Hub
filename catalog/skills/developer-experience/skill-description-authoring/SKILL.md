---
name: skill-description-authoring
description: Author and rewrite SKILL.md frontmatter descriptions so they stay single-line, ASCII-sanitized, and preserve the four matching trigger nouns (product, tool, action, object). Use when writing a new skill description, compacting an over-long one, or fixing a description that no longer surfaces in search and trigger matching. Use when the user mentions two-level triggers, strict observables, confidence bands, match confidence, High/Medium/Low/Reject skill match, clarification ceiling, clarification-rate ceiling, under-triggering, over-triggering, a skill that always asks clarifying questions, context pointers, leading words, two loads, negation avoidance, sediment pruning, or hard vs soft setup-dependency. SKIP - writing the skill body (use skill-create), eval harness design, or unrelated copy-editing.
summary_l0: "Author single-line skill descriptions that preserve product, tool, action, and object trigger nouns"
overview_l1: "Write and rewrite the SKILL.md description so the matcher loads the skill. Use when authoring, compacting, or repairing a description that stopped surfacing. Rules: one physical ASCII line; preserve product, tool, action, and object trigger nouns; pair the category with a strict observable; name defaults to the parent directory; use High/Medium/Low/Reject confidence bands; treat exact invocation as neither sufficient nor necessary; a skill that always defers to clarification is failing. Apply context-pointer, two-loads, leading-word, negation-avoidance, sediment-pruning, and hard/soft setup-dependency discipline; see references/agent-writing-theory.md. Trigger phrases: skill description, two-level triggers, strict observable, trigger nouns, compact description, SKILL.md frontmatter, rewrite description, confidence bands, clarification ceiling."
category: developer-experience
---

# Skill Description Authoring

A skill's `description:` field is not marketing copy. It is the text the matcher reads to decide whether to surface the skill, and (once surfaced) the text the agent reads to decide whether to load it. Every word competes for a fixed slice of the model's context budget. This skill codifies how to write that one line so it stays cheap, stable, and faithful to how the host actually matches and renders skills.

## When to Use This Skill

Use this skill for:

- Authoring the `description:` field of a brand-new SKILL.md
- Compacting a description that has grown too long for the render budget
- Repairing a description that stopped surfacing for the tasks it should match
- Reviewing a batch of descriptions for single-line / ASCII discipline before a catalog release

**Trigger phrases**: "skill description", "description authoring", "trigger nouns", "compact description", "SKILL.md frontmatter", "rewrite description", "confidence bands", "clarification ceiling", "under-triggering", "over-triggering"

## What This Skill Does

Provides the authoring rules and the worked examples that make them concrete:

- **Single-line sanitation**: every description is one physical line, ASCII-only, no trailing whitespace
- **Trigger-noun preservation**: every description keeps the four noun categories that drive matching
- **Name defaulting**: the `name:` field falls back to the parent directory name when omitted
- **Confidence bands**: a match decision is High, Medium, Low, or Reject, and the description is what lands the match in the right band
- **Clarification ceiling**: a skill that always defers to a clarifying question is failing, not being safe
- **Agent-writing discipline**: context pointers, the two loads, leading words, negation avoidance, sediment pruning, and the hard/soft setup-dependency split; full treatment in `references/agent-writing-theory.md`

## Instructions

### Rule 1: Descriptions are single-line and ASCII-sanitized

The `description:` value MUST be a single physical line. A description that wraps onto a second line breaks the YAML frontmatter parser used by `validate_skills.py` (it reads frontmatter line-by-line and treats the wrapped remainder as a stray key) and corrupts the render-line shape `- name: description (file: path)` that the host emits into the system prompt.

Concretely:

- No embedded newlines. If your editor soft-wraps the line, that is fine; a hard line break is not.
- No trailing whitespace.
- ASCII only, per the AGENTS.md ASCII-only convention: no curly quotes (use straight `"` and `'`), no em-dashes or en-dashes (use a hyphen `-`, a comma, or parentheses), no ellipsis character (use three periods `...`).
- No leading bullet, no surrounding quotes that the YAML parser would strip inconsistently.

These rules are the same discipline `validate_skills.py` will enforce mechanically once Phase 6 of the adoption-skill-cleaner plan lands the single-line `name` / `description` checks. Authoring to the rule now keeps the catalog clean before the gate exists.

### Rule 2: Preserve the four trigger-noun categories

Skill matching keys off specific nouns in the description. When you write or rewrite a description, keep one concrete word from each of these four categories so the matcher and the agent can still find the skill:

| Category | What it names | Examples |
|----------|---------------|----------|
| **product** | what the skill is about (its domain) | `skills`, `memory`, `code-graph` |
| **tool** | the object the action verb operates on | `skills`, `tests`, `docs` |
| **action** | the imperative verb the skill performs | `audit`, `generate`, `compress` |
| **object** | the artifact the skill produces | `report`, `SKILL.md`, `manifest` |

A description that drops these nouns in favor of abstract phrasing ("streamline your workflow", "boost productivity") becomes invisible to the matcher even when it is the right skill for the task. When you compact a description for length, the trigger nouns are the last words you remove, not the first.

### Rule 3: `name:` defaults to the parent directory name

When the `name:` field is omitted from the frontmatter, the loader uses the skill's parent directory name as the name. To keep this defaulting safe:

- The parent directory name MUST be kebab-case (`^[a-z0-9-]+$`), because that becomes the skill `name`.
- When `name:` IS present, it MUST match the directory name exactly. `validate_skills.py` already enforces this as a hard error.
- Never rely on defaulting to "rename" a skill; rename the directory instead, so the name and path stay in sync.

### Rule 4: Confidence bands land the match in the right bucket

A skill-match decision is not a boolean. Write the description so an honest matcher can put the request in one of four bands:

| Band | Meaning | Description job |
|---|---|---|
| High | This skill is the primary handler | Name the user's likely phrases verbatim in the first two sentences |
| Medium | Relevant, but another skill might own the core | Cover synonyms and adjacent intents; do not claim exclusive ownership |
| Low | Tangential; load only if nothing stronger matches | Mention the adjacent intent once, then point away |
| Reject | Do not load | Put the look-alike request in a `SKIP:` / `Do NOT use for:` clause |

Under-triggering happens when the description is narrow, clean, or implicit: the user said "show internal metrics" and the dashboard skill never loaded because it only said "dashboard". Over-triggering happens when the description is a grab-bag with no SKIP fence. Pushy trigger lists plus an explicit SKIP clause are how both failure modes get fixed.

### Rule 5: A clarification-rate ceiling is a quality signal, not a personality trait

Asking one clarifying question on a genuinely underspecified request is fine. Asking a clarifying question on every invocation is a description failure. The skill is hiding behind "I wanted to be safe" instead of naming the default and the SKIP cases up front.

Before (always defers; looks careful; never actually runs):

```yaml
description: Help with dashboards. Ask the user which metrics they want before doing anything.
```

After (High-band default, Medium-band synonyms, Reject fence; one clarification only when the request names no data source at all):

```yaml
description: Build an internal metrics dashboard with filters and drill-down. Use whenever the user mentions dashboards, data visualization, internal metrics, or displaying company data, even if they never say dashboard. SKIP: standalone chart generation, one-off CSV exports, or a read-only status page with no filters. If the request names no data source, ask once; do not block on a metrics laundry list.
```

The after form is longer on purpose. Those extra words are the difference between a skill that fires and a skill that interviews the user until the session dies.

### Rule 6: Apply agent-writing discipline to the description and its pointers

The description is a context pointer: its wording, not the body sitting on disk, decides whether the agent ever loads this skill. The six concepts below apply here; the full treatment with worked examples is in `references/agent-writing-theory.md`.

- **Context pointers**: sharpen the always-loaded wording before inlining more body. One trigger family per genuinely distinct branch. Name the file the agent should open (`references/agent-writing-theory.md`), not "see the bundled reference".
- **Two loads**: the description spends context load (always-loaded tokens) on every session across the catalog. Keep it pushy and short. Cognitive load is what the author must remember; a strong pointer (path plus why) converts that into an on-demand read.
- **Leading words**: prefer compact pretraining-anchored tokens (`SKIP`, `Verification`, `frontmatter`) over spelled-out triads. Collapse a triad into one catalog word. Delete an instruction the model already obeys (the no-op test); do not trim it.
- **Negation avoidance**: state the positive target ("write one physical line") first. Reserve "do not" for hard guardrails and pair each with the allowed alternative.
- **Sediment and relevance pruning**: every line must still change behavior. If removing a clause would not change the agent's action, it is sediment; cut it. Prune on every substantial edit, not only at the 500-line size-norm.
- **Hard/soft setup-dependency**: this skill has no hard setup dependency. A skill that cannot function without prior setup carries an explicit run-this-first pointer; a skill that merely sharpens with setup mentions it in soft prose and does not block.

When compacting a description, apply the no-op test and sediment prune before dropping a trigger noun. Trigger-noun preservation (Rule 2) still wins over compactness.

### Rule 7: Pair the category with a strict observable

Use two-level triggering in every description:

1. **Level 1 - category or domain**: name the bucket the request belongs to, normally the category encoded by `catalog/skills/<category>/` (for example TypeScript contract hygiene, skill authoring, or incident response).
2. **Level 2 - strict observable**: name something inspectable that distinguishes the skill inside that bucket, such as an error string, file type, command name, schema field, hook event, or AST smell.

Synonyms and verbatim user phrases remain required; the strict observable is additive. A description that says only "TypeScript cleanup" has Level 1 but no discriminator. `as unknown as`, `Record<string, unknown>`, or `vi.mock` provide Level 2 observables that separate contract hygiene from general TypeScript design.

Published retrieval results show precision falling sharply around 100 competing options. Nexus-Hub's 300-plus-skill always-loaded index is well past that point, so category ownership and `SKIP` fences are load-bearing. Do not respond by shrinking the catalog; give the matcher a category, an observable, and an explicit Reject fence.

### Rule 8: Exact invocation is neither sufficient nor necessary

An exact match to the intended skill name or trigger phrase is not sufficient if the body is a weak tutorial, and it is not necessary if a nearby skill in the same category provides a competent partial runbook. Write each body so a near-match still helps the agent inspect, decide, act, and verify within the shared domain.

Do not over-fit a unique phrase merely to win routing. The description must distinguish ownership, but body quality remains the outcome control. A neighboring skill may hand off the specialized branch while still giving safe partial procedure for the shared category.

## Worked Examples

### Example 1: A good description

A skill that audits a skill catalog against a token budget:

```yaml
description: Audit a skill catalog against the active model's token budget and emit a five-section report (budget, descriptions, duplicates, unused, roots). Use when the loaded skill list is large, descriptions are bloating the prompt, or you need to find duplicate or never-invoked skills.
```

Why it works: single line, ASCII-only; carries **product** (`skill catalog`), **tool** (`skills`), **action** (`audit`), and **object** (`report`); and the second sentence gives concrete trigger conditions.

### Example 2: An over-long description, compacted

Before (over budget, two ideas crammed in, marketing filler):

```yaml
description: This powerful and comprehensive skill will help you to thoroughly analyze and deeply understand your entire skill catalog by carefully measuring how much of the precious context window budget every single one of your skills is consuming, and it will then go on to also detect any and all duplicate skills as well as skills that nobody has used in a very long time, giving you a complete and detailed report.
```

After (compacted, trigger nouns preserved):

```yaml
description: Audit a skill catalog against the token budget and report bloated descriptions, duplicate skills, and unused skills. Use when the loaded skill list is large or you suspect duplicate or never-invoked skills.
```

Compaction diff (what was cut and why):

- Cut "powerful and comprehensive", "thoroughly", "deeply", "precious", "very long time", "complete and detailed" -- marketing filler carries no trigger nouns.
- Kept **product** (`skill catalog`), **action** (`audit` / `report`), **tool** (`skills`), **object** (`report`).
- Result drops from ~70 words to ~30 while preserving every matching signal.

### Example 3: A description with no trigger nouns, rewritten

Before (abstract, matches nothing):

```yaml
description: Streamline your development experience and boost productivity by keeping everything clean, organized, and running smoothly at all times.
```

This description names no **product**, no **tool**, no **action**, and no **object**. The matcher cannot surface it for any concrete request.

After (rewritten with all four categories, assuming the skill removes dead code):

```yaml
description: Find and remove dead code (unreferenced functions, unreachable branches, unused exports) using static call-graph analysis, and produce a removal report. Use when a module has accumulated unused code or a refactor left orphaned symbols.
```

Now the description carries **product** (`dead code`), **tool** (`code`), **action** (`remove` / `find`), and **object** (`removal report`).

## Common Rationalizations

| Rationalization | Reality |
|-----------------|---------|
| "A longer description gives the agent more context, so longer is better." | The description is read at match time against a fixed budget. Past ~250 characters it crowds out other skills' descriptions and gets truncated by the render fallback ladder anyway. Compact and keep the trigger nouns. |
| "Marketing language makes the skill sound more capable." | The matcher does not read for tone; it reads for nouns. "Powerful comprehensive solution" matches nothing. "Audit skills, emit report" matches the task. |
| "I will just wrap the description onto two lines for readability." | A hard line break breaks the frontmatter parser and corrupts the render line. Keep it one physical line; let the editor soft-wrap. |
| "I can omit name: and let it default, then rename freely later." | Defaulting ties the name to the directory. Renaming the skill means renaming the directory, or the name and path silently diverge. |
| "Curly quotes and em-dashes look more polished." | They violate the ASCII-only convention, corrupt on some Windows encodings, and will be rejected once validate_skills.py enforces the rule. Use straight quotes and hyphens. |
| "I will ask a clarifying question every time so I do not guess wrong." | A skill that always defers is failing, not being safe. Name the default path and the SKIP fence; ask once only when a required input is actually absent. |
| "High/Medium/Low/Reject is ceremony for a boolean match." | Under-triggering is the catalog's default failure mode. Bands force the description to list trigger phrases and SKIP cases so the matcher can Reject look-alikes instead of staying silent. |
| "I will inline the whole writing theory so the agent cannot miss it." | The description is the pointer. Inlining spends context load on every session. Sharpen the pointer; keep the six concepts in `references/agent-writing-theory.md`. |
| "A prohibition is clearer than a positive instruction." | Models overweight the forbidden object. State the target behavior. Reserve "do not" for hard guardrails and pair each with the allowed alternative. |
| "This extra sentence does not hurt, and the model already knows it anyway." | If removing it would not change behavior, it is sediment or a no-op. Delete it. Restating a default dilutes the lines that actually change matching or rendering. |
| "Pushy synonyms are enough; a strict observable would over-constrain matching." | Synonyms establish the category but do not separate neighbors inside a 300-plus-skill index. Add an error string, file type, command, schema field, hook event, or AST smell while keeping the synonyms and `SKIP` fence. |
| "The exact intended skill must win every route, so body overlap is waste." | Exact invocation is neither sufficient nor necessary. A near-match still needs a competent partial runbook and an ownership handoff; routing precision cannot rescue a weak body. |

## Verification

- [ ] The `description:` value is a single physical line (no embedded newline).
- [ ] The description is ASCII-only: no curly quotes, no em/en-dashes, no ellipsis character, no trailing whitespace.
- [ ] The description names a **product**, a **tool**, an **action**, and an **object** (or a deliberate subset when one genuinely does not apply).
- [ ] The description is at most ~250 characters (the limit Phase 6's validate_skills.py check will enforce).
- [ ] The description names High-band trigger phrases and a SKIP / Reject fence for look-alike requests.
- [ ] The description has a Level 1 category/domain and at least one Level 2 strict observable (error string, file type, command, schema field, hook event, or AST smell).
- [ ] The body remains a competent partial runbook for a nearby same-category match and does not over-fit one unique trigger phrase at the expense of procedure quality.
- [ ] The description does not instruct the agent to ask a clarifying question on every invocation.
- [ ] If `name:` is present, it matches the parent directory name exactly; the directory name is kebab-case.
- [ ] Running `python scripts/validate_skills.py --path catalog/skills/<category>/<skill>/` reports PASS with no errors.
- [ ] The description and body (or `references/agent-writing-theory.md`) cover all six agent-writing concepts: context pointers, two loads, leading words, negation avoidance, sediment pruning, hard/soft setup-dependency.
- [ ] `references/agent-writing-theory.md` is named from this SKILL.md (orphan-bundle audit clean).
- [ ] Compaction applied the no-op test and sediment prune before dropping any trigger noun.

## Source

This skill adopts the description-authoring rule surfaced in the skill-cleaner source comparison (insight I-15, supported by I-03). External source: Peter Steinberger's `skill-cleaner` SKILL.md in [steipete/agent-scripts](https://github.com/steipete/agent-scripts/blob/main/skills/skill-cleaner/SKILL.md). Only the authoring rule was adopted; the cleaner's analyzer script was deliberately not imported (per the Nexus MCP Registry Policy reverse-engineer-first preference). The eventual mechanical enforcement point is Nexus-Hub's `scripts/validate_skills.py` (single-line `name` / `description` checks, planned in the adoption-skill-cleaner Phase 6).

## Related Skills

- [[tool-design]] - designing tool and skill descriptions for AI agent consumption
- [[prompt-engineering]] - the broader discipline of writing text an LLM reads precisely
- [[writing-editing]] - general clarity and concision principles that apply to the prose around the description
- [[skill-create]] - drafts a full SKILL.md from git history; apply this skill's description rules and `references/agent-writing-theory.md` at its draft step
- `references/agent-writing-theory.md` - the six agent-writing concepts (context pointers, two loads, leading words, negation avoidance, sediment pruning, hard/soft setup-dependency)

---

**Version**: 1.0.0
**Last Updated**: May 2026
**Author**: Nexus-Hub
**Attribution**: Authoring rule adapted from the skill-cleaner SKILL.md in [steipete/agent-scripts](https://github.com/steipete/agent-scripts) (insight I-15). Analyzer script not adopted.
