# Decision: Newer Vendor CLIs Keep Their Settings State

Status: implemented - `scripts/lib/settings_control/resolve.py` reports `unverified-for-version` only below a write's proven minimum.

Maintainers use this record when a Nexus Hub settings row shows "Unverified for version", or when someone proposes tightening or loosening the version check on catalog writes. It covers which version bound raises the state, what a newer CLI shows instead, and why the code adapters in the settings extension are not covered by this rule.

**Date**: 2026-11-13. **Source**: the maintainer's report that a fresh v4.15.0 install showed a warning icon on the Nexus Hub status bar, and the request that it resolve itself without manual re-qualification after vendor updates.

## Problem

Each catalog write carries `proven_versions` with a `min` and a `max`. The report returned `unverified-for-version` when the installed CLI was outside either bound. The bounds were the versions Nexus-Hub last checked (for example Claude Code `2.1.318`, Codex `0.136.0`). Claude Code and Codex ship weekly, so a new install almost always had a newer CLI, the effort row became `unverified-for-version`, and the status bar showed "Review application in Settings" with nothing for the user to fix.

## Decision

- A CLI older than `min` stays `unverified-for-version`: an older tool can lack the setting key.
- A CLI newer than `max` keeps its normal state and gains one caveat, `Version <x> is newer than <max>, the last version Nexus-Hub checked; the setting key is unchanged.`
- `max` remains in the catalog as the record of the last checked version.

## Alternatives considered

- **Bump every `max` to today's versions.** Rejected: it clears the warning for about a week and returns after the next vendor update.
- **Drop `max` from the catalog.** Rejected: the last checked version is useful evidence, and the caveat surfaces it to the user.
- **Keep the strict check and hide the state from the status bar.** Rejected: the panel would still show a warning badge, and the state would still claim a problem that does not exist.

## Consequences

- A renamed or removed setting key in a newer vendor version is no longer flagged by the version check. The read still reports `cannot-detect` or a mismatch when the key's value is not one Nexus-Hub writes.
- The settings extension's code adapters (live effort in the vendor UI and the Restart buttons) still require an exact vendor build, because they patch minified vendor JavaScript whose identifiers change every release. This rule does not cover them.
