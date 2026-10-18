# Decision: Claude Effort Default Lever

Status: proposed - the maintainer selected per-model High; whole-plan integration and release qualification remain pending.

Installer maintainers use this decision when changing Claude effort defaults or migrating previously seeded values. It covers the selected per-model lever, ownership evidence, legacy overrides, and the concrete-model refresh obligation.

**Date**: 2026-10-16. **Source decision**: maintainer Q3, 2026-10-15, explicitly amended in the approved v4.14.0 plan.

## Problem

An environment override defeats saved effort choices. User-scope top-level effort does not establish the Opus 5.5 default. Per-model settings use canonical names and retain normal settings-scope precedence. [Dated evidence](../../../releases/v4/v4.14/development/phase-6-effort-evidence.md) records the fetched references.

## Alternatives considered

1. Keep the environment variable. Rejected: it applies broadly but overrides `/effort` and the Settings panel's saved values.
2. Seed `modelSettings.<canonical-id>.effortLevel`. Selected: saved choices remain effective at their scope. The concrete-ID list requires maintenance as models change.
3. Seed both. Rejected: the environment variable still wins and cancels the benefit of per-model saving.

## Proposal

Declare High for the four current canonical IDs and retain the top-level fallback for older models. Stop declaring the effort env seed. Upgrade or retire only a value equal to the installer's recorded seed; absent, invalid, mismatched, or user-changed ownership evidence preserves existing values. Never seed max.

Use a separate `.nexus-hub/core-settings-seeds.json` beside the target configuration root. The existing install manifest tracks file delivery and drops unknown fields when reloaded; extending it would silently lose ownership data or require unrelated schema changes. Scope this record to the settings directory, and replace its file atomically using a sibling temporary file. Record only actual core writes or a verified fresh template copy, never merely matching pre-existing defaults.

## Consequences

Unknown legacy overrides remain until the user removes them; doctor reports the exact key without editing it. A user choice equal to the last seed cannot be distinguished from that seed and may upgrade. Higher-precedence settings can still override a saved value. The approved amendment supersedes the older env-to-High example: migrate a provably owned env seed to effective per-model High rather than recreate the override.

## Acceptance criteria

The declared canonical-model defaults and both derived artifacts agree. Both native installers preserve user-owned values, upgrade matching recorded seeds, remember removals, and record actual fresh writes. Doctor names a retained override without writing files. The full native gate, supported-host installer qualification, required integration checks and release must complete before this proposal is recorded as shipped.

## Risks

The concrete-ID list needs maintenance when a model changes. An unknown legacy override remains effective until its user removes it. A user choice equal to the recorded seed is indistinguishable and may upgrade. Native atomic replacement does not promise uninterrupted read availability or serializable ownership between concurrent installs. Higher settings scopes can still override the selected per-model default.
