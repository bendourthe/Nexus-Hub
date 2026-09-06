# Decision: Adopt optional invocation-policy frontmatter and map it per platform only where documented

Status: implemented - two optional booleans in SKILL.md, validated locally, mapped to Codex's inverted sidecar and passed through verbatim everywhere else

## Problem

Nexus-Hub distributes one skill to many platforms and had no way for a skill to declare who may invoke it. A heavyweight or side-effecting workflow (a deploy, a destructive refactor) is auto-loadable by the model on every platform, and a pure background-knowledge skill clutters every slash menu. Both are per-skill properties that only the skill's author knows.

The adjacent risk is worse than the gap. Any per-platform mapping invites inventing a lever a platform does not actually support, which is a mistake this project has already made and shipped.

## Decision

Two OPTIONAL strict-boolean frontmatter fields, absent by default:

- `disable-model-invocation` (default `false`): the agent may not auto-load the skill.
- `user-invocable` (default `true`): the skill is hidden from the slash menu, remaining available to the model.

`scripts/validate_skills.py` enforces boolean type and rejects the combination `disable-model-invocation: true` + `user-invocable: false`, which leaves a skill nobody can invoke. That combination rule is a Nexus-Hub addition; no vendor forbids it.

Per-platform distribution is decided strictly by what a fetched vendor document says, recorded with source URLs and verified dates in `docs/policy/skill-invocation-policy-levers.md`:

- `claude`, `copilot`, `cursor` read the fields from `SKILL.md`, which the installers already copy verbatim. **No installer change.**
- `codex` uses `policy.allow_implicit_invocation` in an `agents/openai.yaml` sidecar with **inverted polarity**, so it gets a real mapping (`codex_invocation_policy`), added with maintainer approval because it touches the installer.
- `antigravity2` documents no lever. Nothing is emitted.
- Five smaller platforms are recorded as NOT SURVEYED, deliberately distinct from "none documented".

## Alternatives considered

- **A single `manual-only: true` field of our own design.** Rejected: three of four verified platforms already use Anthropic's exact field names and semantics, so inventing a synonym would require translating on every platform instead of none, and would diverge from the emerging cross-vendor convention.
- **Make the fields required, with explicit defaults on all 273 skills.** Rejected: it converts an opt-in refinement into 273 lines of always-loaded frontmatter for no behavioral change, against the Tier-1 token discipline. The framework-mapping fields set the optional-field precedent.
- **Infer a lever for platforms whose docs are silent, by analogy to similar platforms.** Rejected on the do-not-invent rule. This is precisely the fabricated `.kimi/agent.yaml` failure, frozen at `docs/decisions/rejected/policy/2026-07-23-seed-platform-default-without-vendor-doc.md`. The survey caught two live instances where a search summary asserted a field its vendor page does not document.
- **Defer the Codex mapping until a skill declares the field.** Genuinely arguable, and it is what the scope-fit rule would suggest, since nothing exercises the mapping today. The maintainer chose to build it now: the survey evidence is fresh, the inverted polarity is the kind of detail that is expensive to re-derive later, and the mapping is inert until a skill opts in.
- **Also map `user-invocable` for Codex and Cursor.** Rejected: neither documents a user-invocation lever. Emitting something plausible would be inventing one.

## Consequences

- A skill can now be authored as manual-only and behave correctly on four platforms with one frontmatter line, and harmlessly on the rest, since a platform ignores frontmatter keys it does not recognise.
- The Codex mapping carries an inversion, which is a permanent correctness hazard: a future refactor that "simplifies" it into a value copy silently produces the opposite of the author's intent. It is guarded by an explicit test and a comment in the generated file, and neither should be removed.
- The catalog gains a third policy document (`skill-invocation-policy-levers.md`) alongside the defaults-levers and read-contracts records. Each has a stated scope boundary, and the cost of the third is accepted to avoid growing either existing document past its declared scope.
- Nothing is emitted today, because no skill declares either field. A test asserts that state and fails when the first one does, which is the moment to re-check installer smoke expectations. The mapping is therefore built but unexercised, which is a deliberate acceptance of the scope-fit trade-off named above.
- Five platforms remain NOT SURVEYED. That is visible in the table rather than hidden, and completing the survey is tracked work rather than an assumed answer.
