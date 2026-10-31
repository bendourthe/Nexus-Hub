# Decision: Settings control admission

Status: implemented - a Nexus-Hub Settings control ships only with a fetched vendor source and an observed effect in a fresh session of the real tool, enforced by `scripts/lib/settings_control/catalog.json` and `tests/validators/test_settings_control_catalog.py`. Every other cell is cataloged Not-Settable with its reason.

Maintainers adding a settings control, and anyone asking why a toggle is missing, use this record. It fixes the admission rule, how it differs from the retired v3.17.2 autonomy controller, the human-presence rule for safety-weakening writes, and the options that lost.

**Date**: 2026-10-15, applied in Phase 1 on 2026-10-30. **Source decision**: maintainer discovery round and plan review of 2026-10-15 (every recommendation accepted). **Plan**: `docs/releases/v4/v4.14/plans/v4.14.6-nexus-hub-settings-extension.md`.

## Problem

A settings toggle that writes a key the tool ignores looks identical to one that works. Of roughly 70 candidate keys across Claude Code, Codex, and GitHub Copilot, about 40 are documented at user level, and three of the most wanted controls have no user-level setting on at least one surface. Documentation alone is not proof: a documented key can be overridden by an environment variable, a project file, a remembered mode, or a policy, and a key can change between tool versions.

## Decision

A setting ships as a control only when both hold:

1. **Source.** The key, its allowed values, and its override layers are cited to a fetched primary vendor page with a fetched date. The one internal control, git-guardrails, cites its owning decision record (`2026-10-14-opt-in-git-bypass-flag-guard.md`).
2. **Proof Record.** A `proven` row in the proof matrix: the write applied in a scratch home, a fresh session of the real tool started in an empty directory with its tools turned off, and the single field the tool reported. For git-guardrails the probe pipes a `git commit --no-verify` payload to the hook with the switch on and off.

A cell with no Proof Record is Not-Settable with its reason, and `max` effort, Codex `untrusted`, writes to omitted keys, and project or managed files are refused by the validator. Safety-weakening writes (`full-auto`, git-guardrails off, removing a safety block, `chat.tools.global.autoApprove`) need a human: a TTY on stdin and stdout, or the panel's one-time token, and they are refused whenever the tool's documented agent-session marker is present. No flag bypasses this.

## Consequences

- **Difference from v3.17.2.** The retired autonomy controller tried to steer approvals while a session ran and could not guarantee its effect. Nexus-Hub Settings writes documented defaults that each tool reads when a session starts, never intervenes in a running session, and shows what overrides a default instead of claiming it applies.
- **Fewer controls at first.** Phase 1 admitted the Claude Code and Codex posture and model writes and git-guardrails. Effort, attribution, the VS Code surfaces, and every Copilot CLI cell have no Proof Record yet (a paid request, a VS Code window, or an uninstalled tool is needed), so they ship Not-Settable until observed.
- **One named exception.** Codex `model` is an omitted key in `configs/platform-defaults.json` because Nexus-Hub must not seed a model id the user's account may not reach. A model the user chooses is not a seed, so the validator carries a single exception for it and fails for any other omitted key.
- **Agent markers.** Only Claude Code documents an agent-session marker (`CLAUDECODE`, `CLAUDE_CODE_CHILD_SESSION`). For the other tools the human-presence rule rests on the TTY test.

## Alternatives considered

- **Ship every documented key without proof.** Rejected: this is exactly the toggle that does nothing, and Phase 1 found documented behavior that differs from the product (Codex `workspace-write` on Windows needs `[windows] sandbox`; the Copilot CLI bypass block is a string while the maintainer's file holds a boolean).
- **Ship proof-less keys behind an "experimental" label.** Rejected: a label does not tell a user that the value they chose is overridden, and the panel would still show a toggle with no observed effect.
- **Do nothing and document per-tool steps.** Rejected: the harm is four hand-edited files and a legacy `env.CLAUDE_CODE_EFFORT_LEVEL` that silently beats every in-session choice.
- **Revive the run-time controller.** Rejected: v3.17.2 removed it because it could not guarantee its effect, and acting on another tool's approvals at run time is outside what any vendor documents as a user default.
- **Allow a `--confirm-full-auto` flag.** Rejected: an agent's own shell call can pass it, so it would let an agent turn its own prompts off. The TTY or panel-token check, refused under an agent marker, has no flag.
