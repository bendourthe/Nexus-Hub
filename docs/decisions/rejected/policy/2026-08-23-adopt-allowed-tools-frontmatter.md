# Decision: Adopt an `allowed-tools` SKILL.md frontmatter field

Status: rejected - no fetched official vendor document names this field; inventing it would repeat the fabricated companion-file failure withdrawn in v3.15.0

## Problem

Some comparison-catalog skills declare which tools the agent may use when the skill is active. That looks like a useful least-privilege lever: a firmware skill would not get a browser, a detection skill would not get a write tool. Nexus-Hub already has optional invocation-policy booleans (`disable-model-invocation`, `user-invocable`) mapped only where a vendor document names the lever.

## Proposal

Add `allowed-tools` (or `allowed-tools`) as an optional YAML list in SKILL.md frontmatter, validate the shape in `validate_skills.py`, and teach installers to copy it into each platform's tool-restriction surface.

## Alternatives considered

- **Wait for an official vendor document, then map the field the way invocation-policy booleans are mapped.** This is what remains open. Absence of a lever is recorded, not filled. See `docs/decisions/rejected/policy/2026-07-23-seed-platform-default-without-vendor-doc.md` and the v3.15.0 withdrawal of the fabricated `.kimi/agent.yaml` companion.
- **Invent the field now and no-op it on platforms that ignore unknown keys.** Rejected: an undocumented field in shipped SKILL.md files becomes a false contract. Authors will write lists that do not constrain anything, users will believe they do, and a later vendor field with different semantics at the same name becomes an active conflict.
- **Encode tool limits only in the skill body Instructions.** This is the current behavior. Dual-use skills already open with an authorization precondition. That is prose, not a harness guarantee, and it is honest about what the catalog can enforce.

## Acceptance criteria

- A fetched official vendor document names the field, with `source_url` and a verified date, the same bar `docs/policy/platform-defaults-levers.md` uses.
- The field is classified VERIFIED before it appears in any distributed SKILL.md.

Until both are true, the proposal stays rejected. Do not invent the field because a comparison catalog has it.
