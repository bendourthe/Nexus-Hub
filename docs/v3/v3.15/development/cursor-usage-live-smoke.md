# Cursor Usage Monitor - Live Smoke Checklist

**Version**: v3.15.9 Phase 6
**Host**: Cursor (never VS Code)
**Extension id**: `nexus-hub.cursor-usage-monitor`

Use this checklist after a full Nexus-Hub installer run, or whenever CI skips the Cursor-profile E2E job because the hosted runner has no `cursor` CLI.

## 1. Host isolation after installer

1. Open **Cursor** → Extensions and confirm `Cursor Usage Monitor` (`nexus-hub.cursor-usage-monitor`) is installed and enabled.
2. Confirm these VS Code-only monitors are **absent** from Cursor:
   - `nexus-hub.claude-usage-monitor`
   - `nexus-hub.codex-usage-monitor`
   - `nexus-hub.github-usage-monitor`
3. If VS Code is also installed, open **VS Code** → Extensions and confirm Claude / Codex / GitHub monitors are present there, and that `nexus-hub.cursor-usage-monitor` is **absent**.

Optional CLI checks:

```bash
cursor --list-extensions | grep usage-monitor
code --list-extensions | grep usage-monitor
```

Expected: Cursor lists only `nexus-hub.cursor-usage-monitor`; VS Code lists the three non-Cursor monitors.

## 2. Consent prompt and live transport (v3.15.12 Phase 1)

On first activation the extension shows **one** modal consent prompt when a Cursor state database is present and the host supports reading it. Verify:

- The prompt states what will be read (state database **read-only**, **one named key**, one request to Cursor's usage endpoint) and what will not (browser cookies, `Login Data`, OS keychain, process memory, shell history, HTML billing pages, filesystem credential search).
- Choosing **Keep manual only** is respected and **never re-prompts**, and the extension continues on cache/manual data.
- Choosing **Allow live usage** yields real numbers with no further setup. Record the Cursor version and whether numbers appeared, because live reads require Node 22.13+ in the extension host (**WN-5**); if the host is older the panel correctly reports the capability unavailable and falls back.
- **Cursor Usage: Revoke Live Usage Access** clears the decision and any usage cached from it, while usage entered manually survives.

**HO-5 is narrowed, not closed**: the undocumented route's field names and units are unconfirmed. If the panel degrades with a staleness label rather than showing numbers, that is the fixture rejecting a shape it does not recognize, which is the designed behavior. Capture the sanitized field names and units per the Bounded Probe Procedure in `cursor-usage-auth-probe.md` and correct `tests/fixtures/cursor-usage/wire-contract.json` together with the `CURSOR_WIRE_CONTRACT` constant.

## 3. Personal meters and the three bars (v3.15.12 Phase 2)

Use live data if consent was granted, otherwise **Cursor Usage: Enter Usage Manually** so the UI has data.

Verify:

- Status bar shows separate **Cursor Models** and **Other Models** values (full or compact `C` / `O` labels), with percentages carrying one decimal where the value has one (a 1.7% pool must not read `2%`).
- The status bar, hover, and dashboard agree on the same percentage for the same pool.
- Hover tooltip includes personal **on-demand** spend context and does not treat shared team limits as a personal allowance.
- Dashboard renders **three** bars: both included-usage meters with `#4682B4` fills and numeric labels, plus an **on-demand spend** bar.
- The on-demand bar is labelled in **currency** against its limit (for example `$12.50 of $200.00`), never as a percentage of tokens.
- The on-demand bar carries a note stating the limit is **shared across your team** and naming the reset date from the billing cycle, not a hardcoded day.
- A pool at 100% is obviously distinguishable from one at a few percent at a glance.
- Threshold warnings evaluate only personal included-usage meters (`highest` / `cursorModels` / `otherModels`), never team shared spend or the on-demand bar.

## 4. Theme smoke (light / dark / high contrast)

This section is what closes **QG-4** and **QG-5**, and v3.15.12 Phase 2 widened its scope with a third bar.

In Cursor, switch Color Theme through light, dark, and a high-contrast theme. Confirm:

- Status-bar glyph remains legible (`currentColor` icon font).
- Meter fills stay `#4682B4` with readable numeric text, on **all three** bars.
- The on-demand bar's currency labels and its shared-scope note remain readable in every theme, including when the bar is clamped at full width for over-limit spend.
- A dropped on-demand bar (no limit, or a limit in a different currency) shows its absolute-spend fallback legibly rather than an empty track.
- Warning panel severity remains understandable from text and icons, not color alone.
- Icons8 attribution remains visible in the warning view / notices.

## 5. Commands smoke

Run each command from the Command Palette:

- Cursor Usage: Dashboard
- Cursor Usage: Refresh (with consent granted, expect live data or an explicit staleness label; with consent declined or the capability unavailable, expect a notice naming the provenance of what is on screen, and cache/manual data stays visible)
- Cursor Usage: Recommendation
- Cursor Usage: Settings
- Cursor Usage: Enter Usage Manually
- Cursor Usage: Clear Data
- Cursor Usage: Revoke Live Usage Access
- Cursor Usage: Open Native Settings
- Cursor Usage: Open Cursor Usage Page

## 6. Record the result

Note date, Cursor version, OS, whether data was live / cache / manual, and any defects in the active known-gaps ledger or the phase session history. Two claims specifically must not be made without evidence from this run: do not claim live dashboard authentication succeeded unless the bounded probe was actually run, and do not claim the wire contract is verified unless the sanitized field names and units were captured and the fixture corrected.
