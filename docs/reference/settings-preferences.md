# Settings Preferences

This reference defines the shared preferences used by Nexus-Hub Settings 0.3.0 and their hook consumers. Read it when adding a switch, reviewing a native effort mapping, or diagnosing a preference that is saved but overridden. It covers persistence, effective defaults, workspace trust, confirmation, native limitations, reset and runtime delivery.

## Shared Effort

The desired effort is stored in the user's `~/.nexus-hub/preferences.json` as `default_effort`. The existing settings engine also writes each admitted native effort setting when the user changes the shared selector. The preference remains readable even when a tool is absent, unsupported, or overridden.

Claude Code uses the authoritative user `env.CLAUDE_CODE_EFFORT_LEVEL` setting, valid persistent model fallbacks and existing project effort keys. Existing editor launch overrides are synchronized through the host configuration API while preserving unrelated environment entries. Codex uses its native reasoning-effort configuration, existing profiles and existing project effort keys. Ownership records retain the previous values, bind project writes to the project identity, and support exact reset. Managed policy remains outside user control. Vendor settings are admitted only when their documented behavior has been exercised, as the settings-control contract requires.

An effort preference is a default for new sessions, not a command to change an already running model. Unsupported clients retain their own behavior. The panel has no platform-specific selectors; the CLI remains available for detailed diagnosis.

| Shared choice | Claude native effort | Codex common native effort |
|---|---|---|
| Low | `low` | `low` |
| Medium | `medium` | `medium` |
| High | `high` | `high` |
| Extra high | `xhigh` | `xhigh` |
| Max | `max` | `xhigh` |
| Ultra | `max` | `xhigh` |

The installed Codex CLI rejects raw `max` and `ultra`, even when cached model metadata lists them; its IDE also filters unsupported levels before choosing a new-session default. The common mapping avoids this silent fallback. Model capability metadata can lower a Codex mapping further. Claude Ultra maps to maximum effort without enabling the separate orchestration mode. Readback compares the actual mapped native value with the shared choice rather than comparing different names as strings.

The extension reconciles changed supported defaults on startup and file/configuration changes in trusted workspaces, with one attempt per distinct unresolved conflict. Existing sessions retain their explicit session state. GitHub Copilot's public model API does not expose the supported per-model effort values or a configuration setter; this extension does not guess them or use the global debugging override. The installed Cursor and Antigravity native IDE agents have no verified writable public effort control. Their CLI settings are separate surfaces. These three effort integrations remain open rather than being represented as enforced.

## Guardrail Switches

The user-level `~/.nexus-hub/guardrails.json` is read on each affected hook invocation. Only an exact JSON boolean `false` disables a default-on protection. Missing files or keys, malformed JSON and invalid value types retain protection.

| Control | JSON key | Default | Consumer |
|---|---|---|---|
| `git_safety` | `block_dangerous_git` | On | Dangerous Git commands and protected-branch checks |
| `secret_scan` | `scan_secrets` | On | Secret scanning before file writes |
| `edit_preservation` | `protect_user_edits` | On | User-edit protection during file changes |
| `large_file_warning` | `warn_large_files` | On | Advisory large-file warnings |
| `git_guardrails` | `block_git_bypass_flags` | Off | Git-check and signing bypass flags |

Git safety and Git bypass-flag protection are independent. Turning off dangerous-command checks does not turn off a separately enabled bypass-flag check. Enabled Settings protections remain active in full-access mode when the host invokes their hooks; switching them off disables only the named protection. Existing per-hook environment disable controls remain available. Memory-store protection and unrelated policy rules are outside this switch set.

Claude, Codex, Copilot and Antigravity use their existing native hook registrations. Cursor registers the four guard scripts on `preToolUse` and the edit ledger on `postToolUse`, with native JSON permission responses and preserved user registrations. Delivery must refresh the runtime consumers in all five platform directories, including Copilot's `nexus-hub-scripts` subdirectory. Hook protocol exercises prove payload translation and blocking; an actual interactive model tool call remains a separate observation.

## Change Contract

Changes use the existing `nexus-hub settings` dry-run, confirmation, write, ownership and readback flow. Disabling a blocking protection requires the existing human confirmation. The panel is read-only in an untrusted workspace. Reset restores recorded prior values while retaining values changed independently afterward.

Installing the extension or updating its runtime consumers does not change any preference. Both the packaged extension and affected runtime modules and hook copies must be delivered for the controls to work. Changed installed code is backed up before replacement, and installed hashes are verified afterward. User configuration and hook registrations are preserved.

## Evidence

Local behavior observations are recorded in the [redesign proof matrix](../releases/v4/v4.15/development/settings-extension-redesign-proof.md). The [settings-control contract](../policy/settings-control-contract.md) owns vendor admission and the [permission-mode contract](../policy/permission-mode-contract.md) owns host-mode precedence.
