# Decision: The Copilot Usage Monitor Installs Into VS Code Only

Status: implemented - the installers stop putting the Copilot monitor into Cursor and remove copies earlier releases left there.

Maintainers of the usage-monitor install step use this record when deciding which editor receives each monitor. It reverses the v4.13.11 WN-30 choice to install the Copilot monitor into Cursor as a second host, and states how existing installs are cleaned up.

**Date**: 2026-10-22. **Source**: maintainer direction: "It should not have the github copilot usage monitor extension. That extension should only be installed in VS Code."

## Problem

Since v4.13.11 (WN-30), both installers passed Cursor's CLI to the Copilot monitor as a second host, on the reasoning that Copilot can run inside Cursor. The maintainer uses Copilot in VS Code, and Cursor already carries its own Cursor Usage Monitor, so the Copilot monitor in Cursor adds a status-bar item for a product that is not used there. Removing the second host alone would leave every existing Cursor copy running.

## Decision

The Copilot monitor installs through the VS Code CLI only, like the Claude and Codex monitors, and the installer banner says so. The existing legacy-extension sweep, which already runs on every install against both `code` and `cursor`, adds `nexus-hub.copilot-usage-monitor` to its removal list for the Cursor host only. The id stays out of the shared retirement array, because that array is swept from VS Code too and would uninstall the monitor where it belongs.

## Alternatives considered

- **Keep the Cursor copy and only stop new installs.** Rejected: existing users keep the extension indefinitely, which is the state the maintainer asked to end.
- **Add the id to the shared retirement array.** Rejected: that array is swept from VS Code as well, so it would uninstall the monitor from the one editor that should have it.
- **Make the second host an installer option.** Rejected: no user has asked for Copilot usage in Cursor, and an option nobody sets is surface without a call site.

## Consequences

A fresh install puts the Copilot monitor in VS Code only, and an upgrade removes it from Cursor with a "Removing retired extension from cursor" line. Copilot users who do work in Cursor no longer get a Copilot status-bar meter there. The smoke tests now treat Copilot as a VS Code-only monitor and assert the Cursor-only sweep entry.
