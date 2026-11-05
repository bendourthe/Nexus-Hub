# Nexus-Hub Settings

Summary: how to set the default effort, model, approval posture, commit attribution, and git-guardrails mode once for Claude Code, Codex, and GitHub Copilot, with the `nexus-hub settings` command or the "Nexus-Hub Settings" panel in VS Code, and how to see and undo anything that stops a default from taking effect.
Read this when: you want every new agent session to start at the same effort or approval posture, a default you chose is not taking effect, you need to undo a change, or you want to know what the panel can never change.
Covers: the five controls and what each means per tool, the VS Code status bar, the override states and their fixes, `remove-override`, the human-presence rule, the Cannot remove list, `reset`, uninstall, and the release capability usage gate.

Nexus-Hub Settings is the one place where you choose the defaults a new agent session starts with. Each tool keeps its defaults in a different file with a different key and a different set of values, and several other layers (an environment variable, a project file, an organization policy, a mode the tool remembers) can quietly beat the file. The command line writes the files and reports every layer that overrides your choice. The VS Code panel is a thin front end over the same command, so the two always agree.

Effort and native approval controls are defaults for new sessions. The five Nexus-Hub guardrail switches are read on the next hook invocation. The compact Settings 0.2.0 panel exposes one effort selector and those five switches; the CLI retains the detailed native controls described below. Shared effort persistence and the guardrail keys are documented in the [preference reference](../docs/reference/settings-preferences.md).

A control exists only where its effect was observed changing a fresh session before it shipped. Everything else is shown as "Not settable" with its reason, never as a switch that silently does nothing. The admission rule and the vendor sources are in the [settings control contract](../docs/policy/settings-control-contract.md).

## Release Capability Usage Gate

- **Activation:** install or upgrade Nexus-Hub (the installers build and install the VS Code panel when the `code` command is found), then run `nexus-hub settings show`, or open the "Nexus-Hub Settings" view in the VS Code activity bar. A default is written only when you run `nexus-hub settings set ...` or confirm a change in the panel.
- **Validation:** run `nexus-hub settings show` (add `--json` for machine-readable output). Each control and tool prints exactly one state. After a `set`, a fresh session in the tool shows the value, and `nexus-hub settings explain <control>` names the file, key, and proof for each write.
- **Rollback:** run `nexus-hub settings reset <control>`. To remove the panel itself, run `code --uninstall-extension nexus-hub.nexus-hub-settings`.
- **Authority:** the panel and command cannot change a running session, cannot override an organization policy, cannot make a tool honor a setting it does not document, and never let an agent enable a safety-weakening default. A change that lowers a safety barrier needs a person at a terminal or a confirmed panel dialog, and it is refused inside an agent session. Nothing is sent over a network, and only user-level files are written.
- **Docs:** this guide is the canonical operating reference.

## Controls

The five controls, and what each one means for each tool today. Run `nexus-hub settings explain <control>` for the exact file, key, value map, source, proof, and overrides of every write. This table states the meaning, not the keys, so it cannot drift from the catalog.

| Control | Values | Claude Code | Codex | GitHub Copilot CLI | VS Code Copilot Chat |
|---|---|---|---|---|---|
| Default effort | `low`, `medium`, `high`, `xhigh` (never `max`) | One entry per current Claude model, plus a fallback for older models | Reasoning effort | Not settable: no Proof Record yet | Not settable: effort is chosen per model in the model picker |
| Default model | A model name, chosen per tool | The `model` default | The `model` default | Not settable: no Proof Record yet | Not settable: only an organization policy sets it |
| Approval posture | `ask`, `accept-edits`, `full-auto` | The default permission mode | Approval policy, with the workspace-write sandbox kept | Not settable: no Proof Record yet | Not settable: no Proof Record yet |
| Commit attribution off | `off` | Not settable: the vendor documents the key and the default commit trailer was observed, but the empty case was not, so there is no Proof Record yet | Not settable: the vendor documents no key | Not settable: no Proof Record yet | Not settable: no user-level key |
| Git-guardrails mode | `on`, `off` | Nexus-Hub's own switch, read by the hooks on every command | Same switch | Same switch | Same switch |

Reading the table:

- **Effort** takes one value that is applied to every tool that can take it, with an optional override per tool. Model is chosen per tool because each tool has its own model family.
- **Posture** `full-auto` means no approval prompts for ordinary actions. It is not "no limits": see [Cannot remove](#cannot-remove).
- **Git-guardrails** is the `block_git_bypass_flags` switch in `~/.nexus-hub/guardrails.json`. Hooks on the platforms that run Nexus-Hub hooks enforce it. The environment variable `NEXUS_GUARD_GIT_BYPASS` (`1` forces it on, `0` forces it off) overrides the file, and the panel shows that as an override.
- A "Not settable: no Proof Record yet" cell moves to a control only after the effect is observed in a fresh session of the real tool and the catalog validator passes. The reason is always shown by `show` and `explain`.

### What a new session starts with

If you choose High effort and Full auto through the CLI, the intended result per tool is below. This is CLI reference material; the compact panel does not expose this scenario table or a native approval-mode selector.

| Tool | Intended result | Today |
|---|---|---|
| Claude Code CLI | High effort, `bypassPermissions` | Settable |
| Claude Code in VS Code | `bypassPermissions`, unless a remembered mode is reported as a note | Posture cell not settable yet: needs a manual observation in a VS Code window |
| Codex | High reasoning effort, approval `never`, sandbox `workspace-write` | Settable |
| VS Code Copilot Chat | No tool-approval prompts | Not settable yet: needs a manual observation in a VS Code window |
| Copilot CLI | High effort, with `--yolo` accepted | Not settable yet: Copilot CLI was not available to observe |

## Commands

Run these in any terminal after installing Nexus-Hub. Every action accepts `--json`, `--dry-run`, and `--project <dir>`. `--tool <tool>` limits `set`, `reset`, and `remove-override` to one tool (`claude`, `codex`, `copilot-cli`, `vscode-copilot`, or `internal`).

```bash
nexus-hub settings show
nexus-hub settings explain posture
nexus-hub settings set effort high --dry-run
nexus-hub settings set effort high
nexus-hub settings reset effort
nexus-hub settings remove-override effort --tool claude
```

- `show` reports one state per control, tool, and surface.
- `explain <control>` prints the keys, value map, timing, sources, proof, overrides with their fixes, and the Cannot remove list. It is the reference for exact keys, and it replaces any copy of those keys in a document.
- `set <control> <value>` writes the value into each tool's user file for new sessions. `--dry-run` prints the plan and writes nothing.
- `reset <control>` undoes what `set` replaced (see [Reset](#reset)).
- `remove-override <control>` removes a known leftover override after you confirm (see [Remove override](#remove-override)).

Writes preserve comments and unrelated keys, follow a symlink to the real file, keep the file's permissions, and are atomic. A file that does not parse is never written.

## Status bar

In VS Code, the Nexus mark sits next to the usage monitors with a clear label such as `Nexus High`. It uses the stored shared effort preference, with a warning marker when application is incomplete or overridden.

The hover gives a short effort, guardrail and readiness summary with an open action. Click it to open Settings. The panel contains one autosaving effort selector and five named switches; `nexus-hub settings show` retains detailed diagnosis. The status bar writes nothing. To hide it without uninstalling the panel, right-click the status bar and clear "Nexus Settings".

## Override states

`show` gives each control and tool exactly one of these states. A note the command cannot verify (for example, that the Claude Code panel remembers the last mode you picked) appears as a separate note, never as a second state.

| State | Meaning | What to do |
|---|---|---|
| `in-effect` | Your value applies | Nothing |
| `tool-default` | Nothing is set, so the tool's documented default applies | Run `set` if you want a different default |
| `overridden-by <layer>` | A higher layer beats your value. The layer names the file, environment variable, or policy | Follow the one-line fix printed beside it |
| `not-settable` | No write is proven for this cell. The reason is printed | Nothing; the reason says what would be needed |
| `not-covered <model-id>` | A current Claude model has no effort entry | Run `set effort <value>` again to add the entry |
| `unverified-for-version <x>` | The installed tool is outside the version range the write was proven on | Check the installed version against the catalog proof; the layers found are still listed |
| `tool-not-installed` | Neither the tool's command nor its configuration folder exists | Install the tool, or ignore the row |
| `cannot-detect` | A layer or file cannot be read, for example a file that does not parse, or VS Code organization policy | Fix the file the reason names; for VS Code, look for the lock icon in the Settings editor |

The usual overrides and their fixes:

- **An environment variable.** For example `CLAUDE_CODE_EFFORT_LEVEL` in your shell profile or in the `env` block of a settings file outranks `/effort` and every saved effort level. The fix is to unset it where it is set.
- **A project file.** A project settings file can set the same key for that project. Remove the key from the project file, or keep your value in the project's local file.
- **A leftover seed.** An older Nexus-Hub install may have written a key that now blocks your choice, for example `env.CLAUDE_CODE_EFFORT_LEVEL` or a bypass block. Use [`remove-override`](#remove-override).
- **A remembered mode.** The Claude Code VS Code panel remembers the last mode you picked. Nexus-Hub cannot read or clear it. Pick the mode in the indicator.
- **A managed or organization policy.** Managed settings, MDM, `requirements.toml`, and VS Code organization policy outrank every user value. Ask your administrator.

## Remove override

`remove-override` is for an override that Nexus-Hub probably seeded earlier but has no seed record for, so the installer will not remove it by itself. It applies only to a short list kept in the catalog: the legacy `env.CLAUDE_CODE_EFFORT_LEVEL` for Claude Code, and the `permissions.disableBypassPermissionsMode` block for Claude Code and Copilot CLI.

It removes the key only after you confirm, and it records the removal, so `reset` puts the key back exactly where it was. In the panel it appears as "Remove this override" on a row that has one. A key that is not in the catalog list is never removed. Every removal follows the [human-presence rule](#human-presence), including a removal that does not touch a safety barrier, because it deletes a setting you did not choose through Nexus-Hub.

## Human presence

Three kinds of change need a person: a change that lowers a safety barrier (the `full-auto` posture, git-guardrails off, any VS Code auto-approve write), every `remove-override`, and a `reset` that would put back a weaker value than the one Nexus-Hub wrote (for example the `bypassPermissions` you had before you chose Ask). A `reset` that returns a safe value stays open to an agent, and `--dry-run` never asks anyone.

- In a terminal, the command asks you to type `yes`, and only runs when both standard input and standard output are terminals.
- In the panel, the confirmation dialog lists every key to be written (or restored) and what will still prompt, and repeats VS Code's own warning for the auto-approve switch, which the configuration API skips.
- Both paths are refused when an agent session marker is present (for example `CLAUDECODE=1`), even after confirming. There is no flag that bypasses this.
- Codex, Copilot CLI, and VS Code document no agent session marker, so for those tools the terminal test is the barrier.

The panel confirms through a one-time file (valid 30 seconds, for one action, control, value, and tool) that holds only the digest of a secret the panel hands to the one command it starts, so a file that is planted or merely read is useless. A process running as you can still do everything the panel does, so this stops a planted file and a replay, not a deliberate forgery by a program you run. The agent marker refusal and the terminal test are the barriers against an agent session, and a hook rule that blocks the command inside an agent's tool call is planned as a second layer.

## Cannot remove

Choosing `full-auto` removes approval prompts, not every barrier. These still apply, per tool. `nexus-hub settings explain posture` prints the current list.

- **Claude Code:** deny rules and explicit ask rules (deny blocks in every mode, including `bypassPermissions`); tools that require user interaction; recognized critical-path `rm` and `rmdir` removals; connector tools your organization set to ask; cross-session messaging safeguards; managed settings, including a bypass block set by an administrator; a running session's mode.
- **Codex:** the sandbox (approval `never` keeps `workspace-write`, so commands that need the sandbox lifted are not run); `requirements.toml` and cloud-managed requirements, which can forbid `never`; a running session's approval policy.
- **Copilot CLI:** deny rules and enterprise restrictions; an MDM `disable` value for the bypass block, which always wins; non-interactive runs, which ignore the default permission mode.
- **VS Code Copilot Chat:** the organization policy that disables auto-approval; any workspace-level value that overrides your user setting.

## Reset

`reset <control>` restores what `set` replaced, for each tool it wrote to. Nexus-Hub keeps an owner-only record at `~/.nexus-hub/settings-control.json` of the first previous value and the value it wrote, per tool, file, and key.

- A key is restored only while it still equals what Nexus-Hub wrote. If you changed it since, `reset` refuses, names both values, and drops the entry so the key is treated as yours.
- A key that did not exist before is removed again, and a key you removed with `remove-override` is put back where it was.
- A reset that would put back a weaker value (for example `bypassPermissions`) asks for the same confirmation as setting it.
- Two commands at once are safe: they take turns on a lock file, and the second one waits.
- VS Code keys the panel wrote are restored in the same profile that wrote them, and only while they still hold what was written.
- After a successful reset the entry is gone, so the installers' normal seeding resumes for that key.

While an entry exists, both installers and the platform-defaults seeder skip that key, so an upgrade never replaces a value you chose. An unreadable record stops seeding for the files it could affect, so a recorded choice is never overwritten blind.

## Uninstall

1. Reset the controls you changed, so each tool file returns to its earlier state: run `nexus-hub settings reset effort`, then the same for `model`, `posture`, `attribution`, and `git_guardrails`.
2. Remove the VS Code panel: run `code --uninstall-extension nexus-hub.nexus-hub-settings`.
3. Optionally delete `~/.nexus-hub/settings-control.json`. A missing record means no recorded choices, and installer seeding resumes everywhere.

If you skip step 1, the values already written stay in the tool files as ordinary user settings. Uninstalling the panel does not change a tool file.

## Related

- [Settings control contract](../docs/policy/settings-control-contract.md): the admission rule, the vendor sources, the write rules, and the panel contract.
- [Platform defaults levers](../docs/policy/platform-defaults-levers.md): the defaults the installer seeds, which the catalog points to where a key is shared.
- [Panel README](../extensions/nexus-hub-settings/README.md): requirements and the panel's safety properties.
