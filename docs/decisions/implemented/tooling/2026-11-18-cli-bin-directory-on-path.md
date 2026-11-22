# Decision: The installer puts the nexus-hub command on PATH by default

Status: implemented - both installers add `~/.nexus-hub/bin` to PATH unless the user opts out with `--no-modify-path` or `-NoModifyPath`. This replaces the v3.7.0 print-only rule.
Date: 2026-11-18
Author: Ben Dourthe
Template: Nygard

## Problem

Since v3.7.0 every install copies the `nexus-hub` launcher to `~/.nexus-hub/bin`, but no installer ever added that folder to PATH. The v3.7.0 rule was that PATH wiring is print-only, because "a no-prompt install must not silently mutate the environment". The installer printed the line to add, inside a long install log.

The maintainer hit the cost of that rule on a second Windows machine: after a v4.15.2 install, `nexus-hub upgrade` failed with `The term 'nexus-hub' is not recognized`. The upgrade path, the main reason the command exists, did not work out of the box.

## Decision

Add the folder to PATH by default, say so in the install output, and offer an opt-out:

- **Windows** (`scripts/installer.ps1`, `Add-NexusBinToUserPath`): append `~\.nexus-hub\bin` once to the user PATH under `HKCU\Environment`. The helper reads the raw value, so references such as `%USERPROFILE%` stay unexpanded, and it keeps the value's registry type (`[Environment]::SetEnvironmentVariable` would rewrite an expandable value as a plain string). It then broadcasts the settings change, so new terminals see the entry, and it adds the folder to the current session.
- **macOS and Linux** (`scripts/installer.sh`, `add_nexus_bin_to_profile`): append one block between `# >>> nexus-hub PATH >>>` and `# <<< nexus-hub PATH <<<` to the login shell's profile: `~/.zshrc` (or `$ZDOTDIR/.zshrc`) for zsh, `~/.bash_profile` for bash on macOS, `~/.bashrc` for bash elsewhere, and `~/.profile` otherwise. The block holds `export PATH="$HOME/.nexus-hub/bin:$PATH"`.
- **Idempotent:** a second install finds the entry or the marker and changes nothing.
- **Visible:** the output names the file or setting it changed and how to undo it.
- **Opt-out:** `--no-modify-path` / `-NoModifyPath` restores the v3.7.0 behavior of printing the line only. The bootstrap one-liners pass the flag through unchanged.

A machine already on v4.15.2 or earlier still needs one manual run of `~/.nexus-hub/bin/nexus-hub upgrade` (Windows: `& "$env:USERPROFILE\.nexus-hub\bin\nexus-hub.cmd" upgrade`), because its installed CLI predates this change.

## Alternatives considered

- **Keep the print-only rule and make the hint more visible.** Rejected by the maintainer on 2026-11-18: users still have to act once, and the failure mode (an upgrade command that does not exist) stays the default.
- **Windows only.** Rejected: macOS and Linux users hit the same failure, and appending a marked, removable block is the common practice of installers such as rustup and uv.
- **Write the Windows PATH with `[Environment]::SetEnvironmentVariable`.** Rejected: it expands `%VARIABLE%` references and turns a `REG_EXPAND_SZ` value into `REG_SZ`, which silently changes every existing entry.
- **Ask a question during install.** Rejected: installs are no-prompt since v3.7.0, and a prompt would block the piped bootstrap.

## Consequences

- New installs get a working `nexus-hub` command in every new terminal.
- The installer now edits one user-owned setting by default. The opt-out flag and the printed undo step keep that change reversible and visible.
- Tests run the helpers against a scratch registry key and a scratch profile file, so the suite never touches the real PATH: `tests/installer/test_upgrade_cli.py`.
- There is no global uninstall command, so removal is manual: delete the user PATH entry on Windows, or the marked block in the shell profile.
