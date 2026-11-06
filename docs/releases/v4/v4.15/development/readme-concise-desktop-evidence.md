# Concise README and Desktop Handoff

The 4.15.0 README now presents Nexus Hub as a backend harness used through existing tools. This record covers the shortened text, native-window mockups, terminal installation example, and the selected Claude desktop to ChatGPT desktop handoff. It verifies documentation rendering, not native provider execution or release publication.

## Content

- The [README](../../../../../README.md) is 547 words, down from 6,541. The long guide section is replaced by a direct link to the supplied online `index.html`. One latest-release section remains.
- Detailed supported-platform, installation, update, pinning, verification and manual-setup content is preserved in the [installation reference](../../../../guides/installation-and-platforms.md). Detailed project workflows and local checks are preserved in the [workflow reference](../../../../guides/development-workflows.md), with relative links rebased.
- Installation uses the website source's exact Windows PowerShell and macOS/Linux commands. A terminal animation shows paste, run and verification for all three systems, including the main-branch checksum warning in selected example output.
- The handoff keeps Claude desktop on the left and ChatGPT desktop on the right for every scene: project, usage warning, handoff offer, selection, generation, copy, paste, recovery of the unfinished task, and a suggested test draft.
- The permanent chart has five stages: Project, Usage warning, Handoff, Copy and paste, Resume. The chart is the sole progress indicator for this animation.
- Both apps show supplied project files and Nexus Hub guidance. ChatGPT drafts the unfinished zero-health regression from context; it does not claim to inspect a repository or run tests.
- All other animations use terminal or VS Code chrome. The real Nexus Hub settings panel appears inside VS Code. The standalone harness dashboard and extra selection outline are absent.

## Verification

- The local renderer produced five GIFs, five posters, scene PNGs and its report. Stable frame sizes, local images, referenced catalog command names, and installation commands were checked during rendering.
- Thirty-six scenes passed at 320, 420, 900 and 1200 pixels with no page overflow. Checks covered two desktop windows throughout, the permanent chart, handoff choices, copied and pasted content, the same unfinished test, keyboard controls, Play/Pause, native-window framing, and the existing manual effort override example.
- The geometry detector passed the source page and seven rendered snapshots at all four widths, with zero findings. Native code blocks use horizontal scrolling and terminal commands wrap within their input columns.
- The actual README rendered through the installed GFM parser at 360 and 900 pixels. All five GIFs loaded, the online guide link matched the requested URL, only one latest-release section remained, and there were no browser errors or page overflow.
- Forty-five local links across the README, asset notes and relocated references resolved, including Markdown and HTML fragment targets. Unicode checks, targeted Ruff, JavaScript parsing and `git diff --check` passed.
- The preview made zero network requests. No installation command, provider call, live handoff, account operation, or repository test shown in a mockup was executed by rendering it.
- Asset replacements used clean edit guards, with no baseline accepts.

## Media

| Animation | Frames | Duration | Bytes | SHA256 |
|---|---|---|---|---|
| installation | 32 | 50.0 s | 142875 | `f5ac56f251c191e731772297d13b9977cbb0ddbd88eeac8b855475657ffd90fc` |
| continuity | 49 | 50.0 s | 149631 | `19b8ab6d4772a46b1fbef0a603de3626ace3aacda2a83f518c3667c61cb2b714` |
| settings | 47 | 38.3 s | 137735 | `77a52fedc389ea48839796c5ac9c44075da4fb9cf74e7acb799a936241b4a3c2` |
| commands | 6 | 16.4 s | 40346 | `9fc5b2a053440d5c0443bb2d2ec3f94c33392d38b31e0b395a7cc091ee19f1bb` |
| workflow | 16 | 33.2 s | 118658 | `b058f0ed39d225545fd125eb59d03ce585cdf5ede2618ad7885a0b92e75ff209` |

All GIFs are 1152 pixels wide. Installation is 730 pixels high, handoff 811, settings 710, commands 829, and workflow 705. Each has a static PNG alternative. [Source and regeneration notes](../../../../../assets/readme/README.md) cover all ten media files.

## Website Comparison

The normal web reader could not open the live page; a direct read returned a JavaScript browser challenge, and the normal browser host was unavailable. The commands and terminal sequence were therefore checked against the repository's website source. Live deployed-page comparison remains unverified; no access-control workaround was attempted.

## Evidence

Local root: `C:/Users/BEDOURTHE/Documents/nx-usage-alerts-qualification`.

- `readme-desktop-pair-reviewed/render-report.json` and scene PNGs
- `verify-desktop-pair-readme-reviewed/results.json` and geometry reports
- `readme-concise-assets.json` and `readme-concise-render.json`
- `readme-concise-desktop-reviewed.html` and the 360/900-pixel README screenshots

## Release Follow-Up

The [progress tracker](../../../../todos.md) requires the concise README, both reference pages, ten media assets and all editable preview sources in the next 4.15.0 integration. Integration, remote validation and publication remain pending.
