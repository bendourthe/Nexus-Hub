# Skill Invocation-Policy Levers (living)

The durable, sourced record of whether each skills-bearing platform documents a **per-skill invocation-policy lever**: a way for one skill to declare that the model may not auto-invoke it, or that the user may not invoke it from a slash menu.

**Last verified**: 2026-08-24 for v3.20.3 command-skill emission. Six platforms re-checked this cycle (claude, cursor, qwen fetched in Phase 4; Codex learn.chatgpt.com re-fetched at release; copilot and the none-documented set carried from 2026-08-18/22). See Scope below for what was not.

## Scope boundary

This document covers **per-skill invocation metadata only**.

Two sibling documents own adjacent questions, and none of the three should grow into the others:

- `docs/policy/platform-defaults-levers.md` owns **install-time behavioral defaults**: reasoning effort, a default-model pin, an approval or autonomy policy. Those are per-platform settings, not per-skill.
- `docs/policy/platform-read-contracts.md` (and its `.json`) owns **file discovery**: where a platform reads skills, commands, rules, and hooks.

An invocation-policy field is per-skill and travels inside `SKILL.md` (or a sidecar next to it), so it belongs to neither. It gets its own record.

## Catalog convention (v3.20.3)

Skills are model-invoked by default. A skill that must fire only when the human types it declares `disable-model-invocation: true` in its SKILL.md frontmatter.

Command-derived skills are user-invoked. Every `catalog/commands/<name>.md` the installer materializes as a skill (the flatten path used by Claude, Codex, Cursor, Qwen, Kimi, Antigravity, OpenCode, Gemini, Gemini CLI, and Nexus-AI) is a slash dispatcher, not a model-auto-loaded catalog skill. `scripts/lib/integrations/_catalog_adapters.py` (`_synthesize_skill`) emits `disable-model-invocation: true` on that generated frontmatter. Do not hand-author a catalog skill whose description begins `Run the /X command` without the same flag; `validate_skills.py` warns (it does not fail the build).

Routing invariant: a user-invoked skill or slash command may delegate to model-invoked skills. It must not delegate to another user-invoked skill or command. That is the existing thin-dispatcher contract: `/implement` dispatches to `implement-phase`; it does not call `/update`.

Per-platform support is the summary table below. Do not invent a lever. Discovery paths are unchanged; see [`platform-read-contracts.md`](platform-read-contracts.md).

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
| `codex` | VERIFIED (different shape) | `policy.allow_implicit_invocation` (default `true`, inverted polarity) | none documented | `agents/openai.yaml` sidecar | [learn.chatgpt.com](https://learn.chatgpt.com/docs/build-skills) | 2026-08-24 |
| `qwen` | VERIFIED | `disable-model-invocation` | `user-invocable` | `SKILL.md` frontmatter | [qwenlm.github.io](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) | 2026-08-18 |
| `antigravity2` | UNVERIFIED | none documented | none documented | n/a | [antigravity.google](https://antigravity.google/docs/skills) | 2026-08-18 |
| `opencode` | VERIFIED (none documented) | none documented | none documented | `SKILL.md` frontmatter | [opencode.ai](https://opencode.ai/docs/skills/) | 2026-08-22 |
| `kimi` | VERIFIED (none documented) | none documented | none documented | `SKILL.md` frontmatter | [moonshotai.github.io](https://moonshotai.github.io/kimi-cli/en/customization/skills.html) | 2026-08-22 |
| `hermes` | VERIFIED (none documented) | none documented | none documented (see `platforms`) | `SKILL.md` frontmatter | [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | 2026-08-22 |
| `nexus-ai` | VERIFIED (none implemented) | none implemented | none implemented | n/a (first-party sibling) | [github.com/bendourthe/Nexus-AI](https://github.com/bendourthe/Nexus-AI) | 2026-08-22 |

"NOT SURVEYED" is deliberately distinct from "none documented". The first means nobody looked yet; the second means someone read the vendor's page and the field is not there. Collapsing the two is how an unchecked assumption becomes a recorded fact.

As of 2026-08-22 the roster carries **no NOT SURVEYED rows**: the final four (`opencode`, `kimi`, `hermes`, `nexus-ai`) were surveyed against their own documentation, closing v3.17 DF-1. Every one returned "none documented", which is a finding rather than a non-answer - it means a declared field reaches those platforms and is ignored, and the distribution rule below therefore holds unchanged. `nexus-ai` is recorded as "none implemented" instead, because a first-party sibling is surveyed against its source rather than a vendor page.

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


### opencode - VERIFIED (none documented)

Surveyed 2026-08-22. The documentation enumerates the recognised frontmatter fields EXHAUSTIVELY ("Only these fields are recognized"): `name` (required), `description` (required), `license`, `compatibility`, and `metadata`. Neither invocation lever is among them.

The distinction matters for this platform: opencode does have invocation controls, but they live in `opencode.json` permission rules and agent configuration rather than in `SKILL.md` frontmatter. So a declared `disable-model-invocation` reaches opencode and is ignored, exactly as the general rule below predicts. Source: <https://opencode.ai/docs/skills/>.

### kimi - VERIFIED (none documented)

Surveyed 2026-08-22. The Kimi Code CLI skills page documents `name`, `description`, `license`, `compatibility`, `metadata`, and `type` (for flow skills). Neither lever appears. The page describes the agent deciding on its own whether to read a `SKILL.md`, which is default behavior rather than a frontmatter-controlled policy. Source: <https://moonshotai.github.io/kimi-cli/en/customization/skills.html>.

### hermes - VERIFIED (none documented), with one nuance worth recording

Surveyed 2026-08-22. Hermes documents `name`, `description`, `version`, `platforms`, `required_environment_variables`, `author`, and a `metadata.hermes.*` block (`tags`, `category`, `config`, `requires_toolsets`, `fallback_for_toolsets`, `requires_tools`, `fallback_for_tools`). Neither Nexus-Hub lever is present.

The nuance: `platforms` produces CONDITIONAL visibility - "When set, the skill is automatically hidden from the system prompt, `skills_list()`, and slash commands on incompatible platforms" - and the toolset fields hide skills conditionally too. That is capability-gating, not an invocation-policy toggle: it answers "does this skill apply here" rather than "may the model load it" or "may the user type it". It is recorded here so a future reader does not mistake it for a `user-invocable` counterpart and map the two together. Source: <https://hermes-agent.nousresearch.com/docs/user-guide/features/skills>.

### nexus-ai - VERIFIED (none implemented)

Surveyed 2026-08-22, and surveyed differently from the rest, because this is the first-party sibling product rather than a third-party vendor. There is no external vendor page to fetch; `docs/policy/platform-read-contracts.json` classifies it MATCH-LOCAL with an empty `sources` list for exactly that reason. The authoritative source for a first-party product is its own repository, which is public: a code search across `bendourthe/Nexus-AI` for `disable-model-invocation` and for `user-invocable` returns **zero hits** for both.

Recorded as "none implemented" rather than "none documented" to keep the two situations distinguishable: a third-party platform might implement a lever it has not documented, whereas here the absence is in the code itself.

## Distribution consequence

Nexus-Hub copies `SKILL.md` verbatim to every skills-bearing platform. So for `claude`, `copilot`, `cursor`, and `qwen`, a skill that declares these fields **already reaches the platform correctly with no installer change**: the fields ride inside the file the installer already copies, and a platform that does not recognise a frontmatter key ignores it.

`codex` is the only surveyed platform needing real mapping work, because its lever lives in a separate `agents/openai.yaml` sidecar with an inverted key. **That mapping is implemented** (v3.17.5 Phase 6, with maintainer approval, since it touches the installer surface): `codex_invocation_policy` in `scripts/lib/integrations/_catalog_adapters.py`, invoked from `CodexIntegration._mirror_codex` for both skill roots.

Three properties of that mapping are load-bearing and each has a test:

1. **The value is inverted, never copied.** `disable-model-invocation: true` emits `allow_implicit_invocation: false`. A mapping that copied the value would produce exactly the opposite of the author's intent while looking correct in a diff, so the generated file says so in a comment.
2. **Nothing is emitted unless a skill declares the field.** Codex's default already matches Nexus-Hub's, so an unconditional sidecar would be noise on every skill.
3. **An authored sidecar is never overwritten.** OpenAI's `agents/openai.yaml` also carries `interface` and `dependencies` metadata this mapping cannot reconstruct, so a skill shipping its own keeps it and the skip is logged.

No catalog skill declares either field today, so catalog copies still emit no Codex sidecar. **Command-derived skills do declare the field** (v3.20.3): `_synthesize_skill` writes `disable-model-invocation: true`, and `_mirror_codex` runs `codex_invocation_policy` *after* that write so each command-skill gets `allow_implicit_invocation: false`. A test still asserts the shipped catalog declares no manual-only skill; a separate install test asserts the generated command-skill plus sidecar.
