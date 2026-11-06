# README Guide Fidelity

README visual corrections for v4.15.0, prepared on `feat/settings-redesign-20261104`. This record covers original-guide exports, the shipped settings webview, desktop handoff illustrations, and local browser checks. Release integration and publication remain separate.

## Completed

- Replaced the invented terminal with the guide's original Windows, macOS, and Linux terminal DOM, wordmark, command, output, paste states, and verification sequence.
- Replaced the simplified workflow IDE with all six stages of the original training story, including its file tree, editor tabs, code edits, tool calls, usage meters, model controls, composer, and permanent workflow strip.
- Replaced the command chat approximation with eight original guide command cards and their scopes and copy examples.
- Rendered the shipped Nexus Hub settings panel inside the guide's IDE components. Illustrative session controls show Medium, a global change to Low, a manual Codex change to Medium, Apply to all, Fast mode, guardrails, usage alerts, and extension controls. The panel uses sample data and does not modify user settings.
- Rebuilt the Claude desktop to ChatGPT desktop handoff with distinct app layouts, native-style title bars, warm Claude and dark ChatGPT colors, a desktop wallpaper and centered taskbar, and a permanent five-step chart. The conversation uses supplied project context; the final test is a draft, not a claimed repository execution.
- Replaced all ten distributed media files and retained concise README text, static alternatives, source links, editable sources, and a reproducible renderer.

## Verified

The real renderer completed all five exports in a fresh directory with no browser errors. Every GIF decoded and remained below 4 MiB.

| Export | Frames | Duration | Bytes |
| --- | --- | --- | --- |
| Installation | 73 | 30.24 s | 157,804 |
| Workflow | 108 | 99.83 s | 1,279,071 |
| Settings | 8 | 36 s | 95,827 |
| Commands | 8 | 48 s | 186,049 |
| Desktop handoff | 9 | 46.8 s | 140,468 |

- Browser exercise: nine handoff scenes at 1440, 1000, 768, and 390 pixels, 36 checks passed; both app windows and the active process step remained present, with no page overflow. Previous/Next, scene selection, keyboard activation, and Play/Pause passed.
- Visual inspection: installer completion, all six workflow endpoints, settings effort/manual override and extension controls, and desktop warning/copy/paste/resume frames. Removed website navigation that initially overlapped a capture. Source heights are padded, never stretched.
- Rendered geometry audit: passed with no findings. Python lint passed for both renderer files. The rendered README loaded all ten media files at desktop and narrow widths; all 39 checked local links resolved.
- The original guide, training HTML, story JavaScript/JSON, and shipped panel JavaScript/CSS have no changes against the starting commit. Native extension functionality was outside this documentation task.

Reproduction: `python scripts/render_readme_demos.py --output <new-directory>`. Capture receipts and screenshots are local under `C:/Users/BEDOURTHE/Documents/nx-usage-alerts-qualification/guide-readme-release-ready/` and `guide-readme-browser-checks/`.

## Edit Records

The edit-guard log contains baseline accept entries for my own generated changes to `scripts/render_readme_demos.py`, `scripts/readme_guide_capture.py`, `guides/website/readme-demos.html`, `guides/website/readme-platforms.js`, and `guides/website/readme-platforms.css`. Their initial write records exceeded the tool's 120-second window; the official diffs were reviewed and contained these task edits. These entries are bookkeeping corrections under the requested documentation work, not user approval receipts. No user changes were identified or discarded. Subsequent checks and write records succeeded normally.

CI impact: documentation, media, and local capture tooling only. No pipeline files changed and no remote validation was started.

## Open

The desktop windows are illustrations informed by official product references, not screenshots from the user's native apps. Native computer access was unavailable during this task. The guide and settings captures are local browser renders, not new installer or live-provider qualification.

Integration into the v4.15.0 release remains tracked in [the progress dashboard](../../../../todos.md). No push, pull request, merge, or release was performed.

## Next

Include the updated README, ten media files, preview sources, desktop wallpaper, and both renderer scripts when integrating the extension branch for v4.15.0.
