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

## 2. Personal meters and on-demand

Live transport remains disabled while **HO-5** is open. Use **Cursor Usage: Enter Usage Manually** (or a normalized cache from a prior authorized refresh) so the UI has data.

Verify:

- Status bar shows separate **Cursor Models** and **Other Models** values (full or compact `C` / `O` labels).
- Hover tooltip includes personal **on-demand** spend context and does not treat shared team limits as a personal allowance.
- Dashboard table shows both included-usage meters with `#4682B4` fills and numeric labels.
- Threshold warnings evaluate only personal included-usage meters (`highest` / `cursorModels` / `otherModels`), never team shared spend.

## 3. Theme smoke (light / dark / high contrast)

In Cursor, switch Color Theme through light, dark, and a high-contrast theme. Confirm:

- Status-bar glyph remains legible (`currentColor` icon font).
- Meter fills stay `#4682B4` with readable numeric text.
- Warning panel severity remains understandable from text and icons, not color alone.
- Icons8 attribution remains visible in the warning view / notices.

## 4. Commands smoke

Run each command from the Command Palette:

- Cursor Usage: Dashboard
- Cursor Usage: Refresh (expect HO-5 boundary messaging when no live transport is injected; cache/manual data stays visible)
- Cursor Usage: Recommendation
- Cursor Usage: Settings
- Cursor Usage: Enter Usage Manually
- Cursor Usage: Clear Data
- Cursor Usage: Open Native Settings
- Cursor Usage: Open Cursor Usage Page

## 5. Record the result

Note date, Cursor version, OS, whether data was manual or cache, and any defects in the active known-gaps ledger or the phase session history. Do not claim live dashboard authentication succeeded unless HO-5 was explicitly authorized for that probe.
