# README Cheatsheet and Settings Color

This refinement moves the complete command cheatsheet to the end of the README, makes every group and command visible, and renames the section to Centralized IDE Settings. It also corrects Claude artwork in the settings animation.

## Changes

- Replaced disclosure controls with ordinary group headings, command headings, tables, examples, and section separators. All 24 commands remain generated from the guide and inherit the README's theme colors.
- Moved Command Cheatsheet after License and updated navigation links.
- Regenerated the settings GIF using the corrected palette. The previously retained GIF had mapped orange artwork to olive/yellow. Provider artwork now remains above the spotlight dimming layer.

## Verification

- 90 browser/content checks passed with no browser errors: complete guide parity, all command headings visible, final cheatsheet placement, correct section title, local links, ten settings scenes at four widths, and source effort/Apply to all interactions.
- 165 image-region checks passed: Claude tab, brand, and toolbar artwork retain exact `#D97757` in all 54 GIF frames and the PNG poster.
- Dark and light Markdown previews and the new settings poster were visually inspected. Ruff and `git diff --check` passed.
- Distributed settings GIF/PNG hashes match the verified exports. No extension runtime, original guide, or original training sources changed.

Receipts: `C:/Users/you/Documents/nx-usage-alerts-qualification/readme-expanded-checks/results.json` and `readme-settings-orange-final/orange-checks.json` under the same qualification root. The GIF is 251185 bytes and 38.8 seconds long.

## Release Inclusion

Include this refinement with the settings branch in v4.15.0. Integration and publication remain pending. All rendered conversations and provider state are samples; this change adds no native-provider functionality.
