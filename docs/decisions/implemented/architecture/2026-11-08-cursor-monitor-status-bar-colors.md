# Decision: Cursor monitor status bar colors

Status: implemented - the Cursor monitor colors its status bar item by usage level, like the Claude and Codex monitors, and names the level in text wherever it is colored

## Problem

v3.15 shipped the Cursor Usage Monitor with no urgency colors on purpose. The v3.15 DEVLOG records: "Custom urgency colors were deliberately not added despite sibling Claude/Codex patterns, because the Cursor visual contract and manifest tests forbid color-only warning presentation." `test/manifest.test.ts` enforced that by rejecting any configuration key matching `colors?`.

v3.15.12 Phase 8 (commit 14d64b816) then copied the Claude monitor's settings form, color pickers included, without revisiting that choice. The form wrote `cursorUsage.colors.*` keys that the manifest did not declare, and nothing read them. The maintainer saw the color pickers, set thresholds, and reported on 2026-11-08 that the status bar stayed uncolored at "Other 77.3%" with High at 75%.

## Decision

- The status bar item takes its background from the same alert metric and thresholds as the usage warnings, through `statusBarItem.warningBackground` (Moderate, High) and `statusBarItem.errorBackground` (Critical). The user's hex goes into `workbench.colorCustomizations`, as in the Claude monitor. At Low the monitor writes nothing, so it cannot overwrite a color a sibling monitor set.
- The three `cursorUsage.colors.*` keys are declared in `package.json`; `none` turns a level's highlight off.
- The visual contract's real rule is kept: "No meter, warning, or stale state relies on color alone." Whenever the item is colored, the hover shows `$(warning) <Level> usage level` and `accessibilityInformation.label` ends with `<Level> usage level`. The manifest test now requires the color keys instead of forbidding them.

## Alternatives considered

**Keep no colors and remove the color pickers from the Settings form.** Rejected: it restores consistency, but the maintainer asked for the colors, the sibling monitors have them, and the contract forbids color-only signals, not color.

**Color the item without any text equivalent.** Rejected: it breaks the contract for screen-reader and color-blind users, which is the risk the original choice guarded against.

**Put the level name into the status bar text itself.** Rejected: the item is already long ("Cursor 0% · Other 77.3%"), compact mode exists to shorten it, and the hover plus the accessibility label carry the level without widening the bar.

## Consequences

- With colors on, the monitor writes the two `statusBarItem.*Background` keys in the user's `workbench.colorCustomizations`, which the Claude and Codex monitors also use. The last monitor to reach Moderate or above sets the hex for that key.
- Users who never opened the Settings form get the default colors (#cca700, #f0643c, #e05555) as soon as usage crosses a threshold.
