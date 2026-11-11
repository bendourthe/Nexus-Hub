# README Walkthrough Evidence

The 4.15.0 README preview includes two animated, illustrative VS Code mockups, static posters, and an editable offline HTML preview. This record covers rendering and documentation verification, not live provider execution or release publication.

## Scope

- [README](../../../../../README.md): Shared IDE Controls and Development Workflow appear near the top, before the product relationship section and release history.

- [Editable preview](../../../../../guides/website/readme-demos.html): nine settings scenes and six workflow scenes, opt-in playback, Previous/Next, individual scene selectors, text walkthroughs, and keyboard focus styles.

- [Renderer](../../../../../scripts/render_readme_demos.py): local Chromium frame capture and Pillow GIF assembly with a shared palette, explicit durations, and refusal to overwrite an existing output directory.

- [Media and regeneration notes](../../../../../assets/readme/README.md): two GIFs and two static posters.

- The existing guide, Training page, extension code, release version marker, and unrelated checkout edits were preserved.

## Teaching Content

The settings mockup illustrates Medium as the starting default, changing every supported session to Low, manually changing one Codex session to Medium, a new agent inheriting Low, Apply to all, Fast mode, a supported Git safety event, alerts off with taskbar usage retained, and Codex tab History/Refresh access. Only representative controls appear. Example sessions and outputs are labeled as illustrative in the README and every frame.

The workflow follows the guide's `/describe`, `/review`, `/plan`, `/implement`, `/test`, and `/update` sequence, with `/update release` as the final example. The game example shows the artifact passed between steps. Tests, local commits, and release preparation in the scene text describe intended workflow outcomes; these mockups are not an execution receipt for that example or this repository.

## Rendered Artifacts

| Asset | Frames | Duration | Bytes | SHA256 |
|---|---|---|---|---|
| assets/readme/nexus-hub-settings.gif | 47 | 38.3 s | 173715 | `de8ea27dcbacac10ddfd3bfdeb7b29ccdae0010ccba9a3e51404f87fed3a799a` |
| assets/readme/nexus-hub-workflow.gif | 14 | 33.2 s | 130567 | `e68d83d7d82c166e1dc37551682a5404984657ba802d0f21158261d2a2907692` |

Settings frames are 1152 x 806; workflow frames are 1152 x 800. Each GIF is below the 4 MiB budget. Posters use the opening scene. The full render also retains individual scene PNGs for local inspection.

## Verification

- `python scripts/render_readme_demos.py --output <new-directory>`: both animations and posters rendered, images loaded, stable frame geometry, no browser errors.

- Chromium interactions: manual session override, new agent inheritance, Apply to all, Fast indicators, guardrail/alert examples, history example, and all six workflow commands matched the scene content.

- Keyboard: scene selection with Enter passed. Play advanced the sequence; Pause stopped playback. Both previews start paused with reduced motion enabled.

- All 15 scenes at 320, 420, 900 and 1200 pixels had no page overflow. The functional-verification geometry detector passed these four widths with zero findings.

- A local GFM renderer displayed the actual new README sections, both GIFs, and all six workflow table rows at 360 and 900 pixels. The preview used GitHub-style horizontal scrolling for narrow tables. No browser errors occurred.

- Twelve local README/media-documentation links resolved, including HTML fragment targets. Added prose was ASCII-only. The new asset README passed the Unicode validator. `git diff --check` and Ruff for the renderer passed.

- Reusing the renderer's existing output directory failed without changing the previously generated GIF, as intended.

- Browser request observation recorded zero network requests. No provider accounts, extension settings, sessions, or remote release state were changed by these previews.

## Local Evidence

Qualification root: `C:/Users/you/Documents/nx-usage-alerts-qualification`.

- `readme-demos-v415-final/render-report.json` and the scene PNGs

- `verify-readme-demos-v415/results.json` and `geometry.json`

- `readme-assets-verification.json`

- `readme-v415-preview-final.html`, `readme-v415-preview-360.png`, and `readme-v415-preview-900.png`

## Release Follow-Up

The [progress tracker](../../../../todos.md) explicitly requires the walkthroughs, four media assets, and editable source in the next 4.15.0 release integration. This change is local; integration, remote validation, and publication remain pending.
