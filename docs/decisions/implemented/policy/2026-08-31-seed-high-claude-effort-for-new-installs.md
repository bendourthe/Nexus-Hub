# Decision: Seed high Claude effort for new installs

Status: implemented - new Claude settings receive aligned high-effort defaults only when the user has not set either effort lever

## Problem

Nexus-Hub's Claude platform defaults seeded `effortLevel` and the higher-precedence `env.CLAUDE_CODE_EFFORT_LEVEL` to `medium`. That default undercut the guide's recommended posture for plan-driven, multi-phase work, where deeper reasoning is more valuable than the small savings from starting every new session at medium effort.

The two settings form one effective policy because the environment value has higher precedence than the scalar. Seeding only one can leave the visible setting and actual runtime behavior inconsistent. At the same time, treating an installer upgrade like a policy reset would overwrite deliberate user choices or add a new higher-precedence environment pin beside an existing scalar choice.

## Decision

Nexus-Hub's declared Claude defaults set both `effortLevel` and `env.CLAUDE_CODE_EFFORT_LEVEL` to `high`, with `model` remaining `opus`. The generated fallback settings use the same values so a missing defaults manifest does not silently change the policy.

Installers apply the effort pair with seed-if-absent semantics. When neither effort lever exists and `env` is absent or object-shaped, a new installation receives both aligned high values. When either effort lever already exists, both effort keys are treated as user-owned and the installer preserves their existing shape without adding the missing partner. Existing model values and unrelated settings are also preserved. A non-object `env` is preserved and reported rather than coerced or overwritten.

The setting is a starting posture, not a lock. Users can choose `medium` for routine work or `xhigh` for harder work, and installer reruns remain idempotent.

## Alternatives considered

- **Keep medium as the default.** Rejected because the distributed harness is optimized for complex implementation, review, and verification workflows where an underpowered starting posture creates more rework than it saves.
- **Seed only the scalar `effortLevel`.** Rejected because an absent or conflicting higher-precedence environment lever can make the effective runtime effort differ from the setting users see.
- **Overwrite both values on every install or upgrade.** Rejected because users own their local configuration. An upgrade must not silently replace a deliberate cost or reasoning choice.
- **Add the missing partner whenever only one effort lever exists.** Rejected because adding the environment lever can unexpectedly pin future sessions above a user's scalar choice, while adding the scalar can falsely imply that it controls a pre-existing environment override.
- **Default to `xhigh`.** Rejected because it imposes the highest reasoning cost on routine sessions. `high` is the proportional default, while `xhigh` remains an explicit escalation for the hardest work.

## Consequences

- Fresh Claude configurations start with deeper reasoning across both supported effort levers.
- Existing user-set effort values, model choices, unrelated environment variables, and malformed-but-user-owned `env` values survive installer reruns.
- Installers carry more merge logic because they must reason about the two effort keys as one user-owned pair across Bash and PowerShell.
- Behavioral parity tests must cover fresh installs, partial configurations, single-lever configurations, non-object `env` values, preservation, and idempotence on both installer implementations.
- Documentation must explain both the default and the user's lower-cost or higher-depth alternatives without implying that upgrades rewrite local choices.
