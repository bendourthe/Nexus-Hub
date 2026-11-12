# README Cross-Platform Evidence

The 4.15.0 README revision keeps the latest published release note, removes the settings mockup's extra selection outline, and adds command discovery and portable handoff visuals. This record verifies illustrative documentation and rendering, not native provider execution or release publication.

## Changes

- [README](../../../../../README.md) retains only its latest What's New section. Older release history points to the existing changelog. The published version marker stays unchanged; 4.15.0 remains a preview.
- [Shared controls](../../../../../guides/website/readme-demos.html#settings) use native-style state changes without the added blue selection outline. Effort changes keep the panel title visible. The mockup preserves manual session overrides and Apply to all semantics.
- [Command quick reference](../../../../../guides/website/readme-demos.html#commands) gives representative examples, with `/skills list` as the live catalog-derived cheatsheet. The renderer checks that all 13 referenced command names exist in the catalog; the visual is not a second complete command registry.
- [Cross-platform handoff](../../../../../guides/website/readme-demos.html#continuity) shows a shared local knowledge foundation, a chat-only handoff from Claude Code in VS Code, continuation in Cursor and Antigravity, supplied context in Claude and ChatGPT desktop chats, and return to Codex in VS Code for execution and verification.
- Desktop mockups use a two-pane chat layout and explicitly represent user-provided files and guidance. They do not imply installed IDE settings controls, automatic history/file synchronization, or hook enforcement in plain desktop chats.
- The original HTML guide, Training page, extension code, and release version remain unchanged.

## Media

| Animation | Frames | Duration | Bytes | SHA256 |
|---|---|---|---|---|
| continuity | 15 | 38.8 s | 187641 | `afe305e31723ebf120b004e2cb1d5364ecfd877fd335f7c8645392334706f3f8` |
| settings | 47 | 38.3 s | 146649 | `c3161fb65334653b79295b36eb0298e448e38c6c2cfc98838ec0a33289a71acb` |
| commands | 13 | 16.4 s | 70966 | `2934e449ff290de870eb1deda498ed816af81fecf8c1889b3dcf21cce052d652` |
| workflow | 31 | 33.2 s | 146833 | `eca64c7f023427a2ded750c2f65dfe9806a369112e62f41bc19a3f5f6a69b75a` |

All animations are 1152 pixels wide; continuity is 885 pixels high, settings 834, commands 899, and workflow 828. Every GIF has a static poster and is below the 4 MiB budget. The [asset notes](../../../../../assets/readme/README.md) link all editable HTML, JavaScript, CSS, and renderer sources.

## Verification

- The local renderer produced four GIFs, four posters, individual scene PNGs and a JSON report. All source images loaded, frame geometry was stable, catalog command references resolved, and browser errors were absent.
- Fresh Chromium checks exercised 25 scenes at widths 320, 420, 900 and 1200: no page overflow, no settings selection shadow, correct manual override and Apply to all values, correct platform identities, two-pane desktop views, disabled Antigravity Fast control, keyboard selection, and working Play/Pause. Playback started paused with reduced motion enabled.
- The visual detector passed all four widths on the source page and six rendered platform snapshots, including both desktop apps, with zero findings.
- The actual revised README was rendered using the locally installed GFM parser with GitHub-style table scrolling and word wrapping. Four GIFs loaded, one What's New heading remained, and layouts passed at widths 360 and 900 with no browser errors.
- Thirty local links resolved. New repository-local inbound broken references to removed README heading anchors: zero. Pre-existing unrelated link defects were not rewritten.
- `git diff --check`, targeted Ruff for the renderer, and ASCII checks on new documentation passed. The browser recorded zero network requests.
- Existing asset replacements used clean edit-guard checks. No baseline accepts were needed.

## Local Artifacts

Qualification root: `C:/Users/you/Documents/nx-usage-alerts-qualification`.

- `readme-cross-platform-reviewed/render-report.json` and scene PNGs
- `verify-readme-cross-platform-reviewed/results.json` and geometry reports
- `readme-cross-platform-assets.json`
- `readme-cross-platform-preview-reviewed.html` and the 360/900-pixel README screenshots

## Release Follow-Up

The [progress tracker](../../../../todos.md) requires all eight media files and editable preview sources in the next 4.15.0 integration, together with Nexus Hub 0.8.2 or newer and the updated usage monitors. Integration, remote validation and publication remain pending.
