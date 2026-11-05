# Settings Preferences

This reference defines the shared preferences used by Nexus-Hub Settings 0.2.0 and their hook consumers. Read it when adding a switch, reviewing a native effort mapping, or diagnosing a preference that is saved but overridden. It covers persistence, effective defaults, workspace trust, confirmation, native limitations, reset and runtime delivery.

## Shared Effort

The desired effort is stored in the user's `~/.nexus-hub/preferences.json` as `default_effort`. The existing settings engine also writes each admitted native effort setting when the user changes the shared selector. The preference remains readable even when a tool is absent, unsupported, or overridden.

Claude Code uses its saved model settings and fallback. When the user's settings file already contains `env.CLAUDE_CODE_EFFORT_LEVEL`, applying the shared preference synchronizes that existing override through the ownership record. An absent environment override is not introduced. A shell, project or managed setting can still win; the interface reports incomplete application instead of claiming enforcement. Codex uses its native reasoning-effort configuration. Vendor settings are admitted only when their documented behavior has been exercised, as the settings-control contract requires.

An effort preference is a default for new sessions, not a command to change an already running model. Unsupported clients retain their own behavior. The panel has no platform-specific selectors; the CLI remains available for detailed diagnosis.

## Guardrail Switches

The user-level `~/.nexus-hub/guardrails.json` is read on each affected hook invocation. Only an exact JSON boolean `false` disables a default-on protection. Missing files or keys, malformed JSON and invalid value types retain protection.

| Control | JSON key | Default | Consumer |
|---|---|---|---|
| `git_safety` | `block_dangerous_git` | On | Dangerous Git commands and protected-branch checks |
| `secret_scan` | `scan_secrets` | On | Secret scanning before file writes |
| `edit_preservation` | `protect_user_edits` | On | User-edit protection during file changes |
| `large_file_warning` | `warn_large_files` | On | Advisory large-file warnings |
| `git_guardrails` | `block_git_bypass_flags` | Off | Git-check and signing bypass flags |

Git safety and Git bypass-flag protection are independent. Turning off dangerous-command checks does not turn off a separately enabled bypass-flag check. Existing host permission modes and environment overrides retain their established behavior. A configured switch is not a claim that every client invokes that hook or that a host's full-access mode still enforces it. Memory-store protection and unrelated policy rules are outside this switch set.

## Change Contract

Changes use the existing `nexus-hub settings` dry-run, confirmation, write, ownership and readback flow. Disabling a blocking protection requires the existing human confirmation. The panel is read-only in an untrusted workspace. Reset restores recorded prior values while retaining values changed independently afterward.

Installing the extension or updating its runtime consumers does not change any preference. Both the packaged extension and affected runtime modules and hook copies must be delivered for the controls to work. Changed installed code is backed up before replacement, and installed hashes are verified afterward. User configuration and hook registrations are preserved.

## Evidence

Local behavior observations are recorded in the [redesign proof matrix](../releases/v4/v4.15/development/settings-extension-redesign-proof.md). The [settings-control contract](../policy/settings-control-contract.md) owns vendor admission and the [permission-mode contract](../policy/permission-mode-contract.md) owns host-mode precedence.
