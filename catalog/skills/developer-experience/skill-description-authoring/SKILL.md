---
name: skill-description-authoring
description: Author and rewrite SKILL.md frontmatter descriptions so they stay single-line, ASCII-sanitized, and preserve the four matching trigger nouns (product, tool, action, object). Use when writing a new skill description, compacting an over-long one, or fixing a description that no longer surfaces in search and trigger matching.
summary_l0: "Author single-line skill descriptions that preserve product, tool, action, and object trigger nouns"
overview_l1: "This skill codifies how to write and rewrite the description field in a SKILL.md so it stays faithful to the matcher that loads skills into the agent prompt. Use it when authoring a new skill, compacting a description grown too long for the render budget, or repairing one that stopped surfacing for its tasks. Three rules drive the work: descriptions are single-line and ASCII-sanitized (no newlines, no trailing whitespace, no curly quotes or em-dashes); descriptions preserve the four trigger-noun categories that drive matching (product, tool, action, object); and the name field defaults to the parent directory name when omitted. The skill ships three worked examples (a good description, an over-long description with a compaction diff, and a no-trigger-noun description with a rewrite) and points at Nexus-Hub validate_skills.py as the eventual enforcement point. Trigger phrases: skill description, description authoring, trigger nouns, compact description, SKILL.md frontmatter, rewrite description."
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

**Trigger phrases**: "skill description", "description authoring", "trigger nouns", "compact description", "SKILL.md frontmatter", "rewrite description"

## What This Skill Does

Provides three authoring rules and the worked examples that make them concrete:

- **Single-line sanitation**: every description is one physical line, ASCII-only, no trailing whitespace
- **Trigger-noun preservation**: every description keeps the four noun categories that drive matching
- **Name defaulting**: the `name:` field falls back to the parent directory name when omitted

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

## Verification

- [ ] The `description:` value is a single physical line (no embedded newline).
- [ ] The description is ASCII-only: no curly quotes, no em/en-dashes, no ellipsis character, no trailing whitespace.
- [ ] The description names a **product**, a **tool**, an **action**, and an **object** (or a deliberate subset when one genuinely does not apply).
- [ ] The description is at most ~250 characters (the limit Phase 6's validate_skills.py check will enforce).
- [ ] If `name:` is present, it matches the parent directory name exactly; the directory name is kebab-case.
- [ ] Running `python scripts/validate_skills.py --path catalog/skills/<category>/<skill>/` reports PASS with no errors.

## Source

This skill adopts the description-authoring rule surfaced in the skill-cleaner source comparison (insight I-15, supported by I-03). External source: Peter Steinberger's `skill-cleaner` SKILL.md in [steipete/agent-scripts](https://github.com/steipete/agent-scripts/blob/main/skills/skill-cleaner/SKILL.md). Only the authoring rule was adopted; the cleaner's analyzer script was deliberately not imported (per the Nexus MCP Registry Policy reverse-engineer-first preference). The eventual mechanical enforcement point is Nexus-Hub's `scripts/validate_skills.py` (single-line `name` / `description` checks, planned in the adoption-skill-cleaner Phase 6).

## Related Skills

- [[tool-design]] - designing tool and skill descriptions for AI agent consumption
- [[prompt-engineering]] - the broader discipline of writing text an LLM reads precisely
- [[writing-editing]] - general clarity and concision principles that apply to the prose around the description

---

**Version**: 1.0.0
**Last Updated**: May 2026
**Author**: Nexus-Hub
**Attribution**: Authoring rule adapted from the skill-cleaner SKILL.md in [steipete/agent-scripts](https://github.com/steipete/agent-scripts) (insight I-15). Analyzer script not adopted.
