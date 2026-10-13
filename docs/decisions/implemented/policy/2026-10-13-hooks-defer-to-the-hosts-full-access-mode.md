# Decision: Nexus-Hub hooks defer to the host's full-access mode

Status: implemented in the v4.13.12 candidate; publication pending - Nexus-Hub's security guards step aside under `permission_mode: "bypassPermissions"`, and prompt-forcing hooks no longer force `ask` in `auto`, `dontAsk`, or `bypassPermissions`. Contract: `docs/policy/permission-mode-contract.md`.

## Problem

A Claude Code session in Bypass permissions mode still prompted for most PowerShell commands. `format-powershell-description.py` returned `permissionDecision: "ask"` for every command outside its allow list without reading the session's mode, and a hook `ask` overrides the mode. Codex in Full access mode showed no prompts, which made the cause visible: Nexus-Hub, not the host, was adding them. The same pattern meant auto mode prompted for every unlisted PowerShell command, and the Antigravity bridge answered `ask` for every silent guard, which prompts even under Always Proceed.

## Decision

The host mode the user picks decides the friction. Full access (`bypassPermissions`) disables every Nexus-Hub approval gate and security guard (user-edit-guard and an opted-in escalation-trigger block downgrade to warnings). `auto` and `dontAsk` keep the deterministic security guards but never receive a forced `ask`, so the auto-mode classifier and the dontAsk pre-approval list decide prompts. The prompting modes are unchanged. The Antigravity bridge returns `allow`, which its documentation defines as delegating to the user's default policy, when a guard has no objection.

Reopening trigger: Cursor, Copilot, or Antigravity starts exposing the approval mode to hooks (extend detection), or Codex documents a full-access `permission_mode` other than `bypassPermissions`.

## Alternatives considered

**Lower the guards in auto mode too.** Rejected. Auto mode is the host's "autonomy with a safety net" mode; the guards cover irreversible actions, the class the classifier exists to stop, and a deterministic check complements a model check. Only the forced prompts were removed, because they defeat the classifier for routine commands.

**Drop the formatter's `ask` in every mode.** Rejected for now. The current hooks reference says a silent hook falls through to the normal permission flow, but the formatter's `ask` was added after an empirical observation that PowerShell ran unprompted without it on Claude Code 2.1.x. Keeping it in the prompting modes preserves that protection until it is re-verified.

**Read each platform's settings file to detect full access on Cursor, Copilot, and Antigravity.** Rejected. The storage locations of those UI settings are not documented, and inferring a security-relaxing mode from an undocumented file risks lifting guards the user did not intend to lift. The gap is recorded in the contract instead.

**A user environment switch (`NEXUS_FULL_ACCESS=1`).** Rejected. It would stay set when the user later returns to a prompting mode, silently leaving guards off. `NEXUS_DISABLED_HOOKS` already covers a deliberate per-guard override.

## Consequences

- A session reporting the top-level `bypassPermissions` mode receives no prompts or blocks from the guards covered by this contract. Claude Code documents this value; Codex Full access remains unconfirmed. Destructive git commands, secret writes, and overwrites of user edits are no longer stopped there; that is the mode's documented meaning.
- On Cursor, Copilot, and Antigravity a guard block still applies in full access; per-session override is `NEXUS_DISABLED_HOOKS=<guard>`.
- New gating hooks must declare their row in the contract and test `default`, `auto`, and `bypassPermissions`.
