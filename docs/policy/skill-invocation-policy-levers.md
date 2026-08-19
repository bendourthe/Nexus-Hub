# Skill Invocation-Policy Levers (living)

The durable, sourced record of whether each skills-bearing platform documents a **per-skill invocation-policy lever**: a way for one skill to declare that the model may not auto-invoke it, or that the user may not invoke it from a slash menu.

**Last verified**: 2026-08-18 for v3.17.5. Six platforms surveyed (five in Phase 6, `qwen` added during the release-pass contract re-verification); see Scope below for what was not.

## Scope boundary

This document covers **per-skill invocation metadata only**.

Two sibling documents own adjacent questions, and none of the three should grow into the others:

- `docs/policy/platform-defaults-levers.md` owns **install-time behavioral defaults**: reasoning effort, a default-model pin, an approval or autonomy policy. Those are per-platform settings, not per-skill.
- `docs/policy/platform-read-contracts.md` (and its `.json`) owns **file discovery**: where a platform reads skills, commands, rules, and hooks.

An invocation-policy field is per-skill and travels inside `SKILL.md` (or a sidecar next to it), so it belongs to neither. It gets its own record.

## The do-not-invent rule

A lever is VERIFIED only when a **specific official vendor document, fetched and read**, names the field. Never a blog post, a forum thread, an aggregator, an issue tracker, or an analogy to a platform that looks similar.

Nexus-Hub has already paid for breaking this rule: the `.kimi/agent.yaml` companion was fabricated rather than found, shipped, and had to be withdrawn in v3.15.0. That incident is frozen as a decision record at `docs/decisions/rejected/policy/2026-07-23-seed-platform-default-without-vendor-doc.md`.

**This survey caught the same failure twice, live.** Both times a search summary asserted a field that the vendor's own page does not document:

- A search summary stated Cursor supports `user-invocable`. Cursor's documentation page lists `name`, `description`, `paths`, `disable-model-invocation`, and `metadata`, and does not mention `user-invocable`. The claim traced to a community forum thread.
- A search summary stated Antigravity supports `disable-slash-command`. Antigravity's skills page documents only `name` and `description`, and states that the agent decides based on context with no per-skill mechanism to disable it.

Both are recorded below as what the vendor documents, not what the summary claimed. A secondary source is a reason to go read the first-party page, never a finding in itself.

## Summary table

| Platform (registry id) | Class | Model-invocation lever | User-invocation lever | Where it lives | Source | Verified |
|---|---|---|---|---|---|---|
| `claude` | VERIFIED | `disable-model-invocation` (default `false`) | `user-invocable` (default `true`) | `SKILL.md` frontmatter | [code.claude.com](https://code.claude.com/docs/en/skills) | 2026-08-18 |
| `copilot` | VERIFIED | `disable-model-invocation` (default `false`) | `user-invocable` (default `true`) | `SKILL.md` frontmatter | [code.visualstudio.com](https://code.visualstudio.com/docs/agent-customization/agent-skills) | 2026-08-18 |
| `cursor` | VERIFIED (partial) | `disable-model-invocation` | none documented | `SKILL.md` frontmatter | [cursor.com](https://cursor.com/docs/skills) | 2026-08-18 |
| `codex` | VERIFIED (different shape) | `policy.allow_implicit_invocation` (default `true`, inverted polarity) | none documented | `agents/openai.yaml` sidecar | [learn.chatgpt.com](https://learn.chatgpt.com/docs/build-skills) | 2026-08-18 |
| `qwen` | VERIFIED | `disable-model-invocation` | `user-invocable` | `SKILL.md` frontmatter | [qwenlm.github.io](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) | 2026-08-18 |
| `antigravity2` | UNVERIFIED | none documented | none documented | n/a | [antigravity.google](https://antigravity.google/docs/skills) | 2026-08-18 |
| `opencode`, `kimi`, `hermes`, `nexus-ai` | NOT SURVEYED | - | - | - | - | - |

"NOT SURVEYED" is deliberately distinct from "none documented". The first means nobody looked yet; the second means someone read the vendor's page and the field is not there. Collapsing the two is how an unchecked assumption becomes a recorded fact.

## Per-platform detail

### claude - VERIFIED

Both fields, with the semantics Nexus-Hub's schema adopts.

- `disable-model-invocation`: "Set to `true` to prevent Claude from automatically loading this skill. Use for workflows you want to trigger manually with `/name`." Default `false`.
- `user-invocable`: "Set to `false` when only Claude should invoke the skill: Claude Code hides it from the `/` menu and doesn't run it when you type `/name`. Use for background knowledge users shouldn't invoke directly." Default `true`.

### copilot - VERIFIED

Same field names and defaults as Claude, documented on the VS Code agent-skills page, which is the surface Nexus-Hub's opt-in `.github/skills/` wrapper targets.

- `user-invocable`: "Controls whether the skill appears as a slash command in the chat menu. Defaults to `true`."
- `disable-model-invocation`: "Controls whether the agent can automatically load the skill based on relevance. Defaults to `false`."

### cursor - VERIFIED (partial)

- `disable-model-invocation`: "When `true`, the skill is only included when explicitly invoked via `/skill-name`. The agent will not automatically apply it based on context." No default stated on the page; the page marks the field Optional.
- No `user-invocable` field is documented. See the do-not-invent section above for the forum claim that was not confirmed.

### codex - VERIFIED (different shape)

Codex expresses the same intent through a different file, a different key, and the opposite polarity.

- `policy.allow_implicit_invocation` in an `agents/openai.yaml` sidecar, default `true`. Setting it `false` stops Codex activating the skill from a user prompt while explicit `$skill` invocation keeps working.
- No user-invocation lever is documented.

Because the polarity is inverted, `disable-model-invocation: true` corresponds to `allow_implicit_invocation: false`. A mapping must not copy the value across.

### qwen - VERIFIED

Found during the v3.17.5 release-pass contract re-verification, not the Phase 6 survey. Both fields, with semantics matching Nexus-Hub's schema:

- `user-invocable`: "To hide a Skill from direct slash-command use while keeping it available for model invocation, set `user-invocable: false`". Default is user-invocable.
- `disable-model-invocation`: "To hide a Skill from model invocation while keeping direct user invocation available, set `disable-model-invocation: true`". Default is model-invocable.

Like `claude`, `copilot`, and `cursor`, Qwen reads these from `SKILL.md`, so the fields reach it through the verbatim copy with no installer change.

### antigravity2 - UNVERIFIED

The skills page documents only `name` (defaults to the folder name) and `description`, and states the agent decides whether to use a skill based on context. No per-skill mechanism to disable that is documented. This is a valid, expected result, not a gap to fill.

## Distribution consequence

Nexus-Hub copies `SKILL.md` verbatim to every skills-bearing platform. So for `claude`, `copilot`, `cursor`, and `qwen`, a skill that declares these fields **already reaches the platform correctly with no installer change**: the fields ride inside the file the installer already copies, and a platform that does not recognise a frontmatter key ignores it.

`codex` is the only surveyed platform needing real mapping work, because its lever lives in a separate `agents/openai.yaml` sidecar with an inverted key. **That mapping is implemented** (v3.17.5 Phase 6, with maintainer approval, since it touches the installer surface): `codex_invocation_policy` in `scripts/lib/integrations/_catalog_adapters.py`, invoked from `CodexIntegration._mirror_codex` for both skill roots.

Three properties of that mapping are load-bearing and each has a test:

1. **The value is inverted, never copied.** `disable-model-invocation: true` emits `allow_implicit_invocation: false`. A mapping that copied the value would produce exactly the opposite of the author's intent while looking correct in a diff, so the generated file says so in a comment.
2. **Nothing is emitted unless a skill declares the field.** Codex's default already matches Nexus-Hub's, so an unconditional sidecar would be noise on every skill.
3. **An authored sidecar is never overwritten.** OpenAI's `agents/openai.yaml` also carries `interface` and `dependencies` metadata this mapping cannot reconstruct, so a skill shipping its own keeps it and the skip is logged.

No catalog skill declares either field today, so the mapping currently emits nothing. A test asserts that state, and it fails loudly when the first skill starts declaring the field, which is the point at which the installer smoke expectations should be re-checked.
