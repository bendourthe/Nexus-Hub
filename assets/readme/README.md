# README Visuals

Editable mockups of the tools that use Nexus Hub: terminal installation, Claude desktop and ChatGPT desktop handoff, and VS Code workflow, commands, and settings. Nexus Hub appears as backend guidance or its optional IDE extension inside the host tool.

## Sources

- [HTML preview](../../guides/website/readme-demos.html): scene text, keyboard navigation, opt-in playback, and text walkthroughs.
- [Native windows and process charts](../../guides/website/readme-platforms.js) and [styles](../../guides/website/readme-platforms.css).
- [Renderer](../../scripts/render_readme_demos.py): Chromium capture and Pillow GIF assembly.
- [Website source](../../guides/website/nexus-hub-guide.html): installation commands. The renderer verifies both install commands against this file.

## Regeneration

From the repository root, with Pillow, Playwright, and Playwright Chromium already installed, run in PowerShell:

```powershell
python scripts/render_readme_demos.py --output "$env:TEMP/nexus-hub-readme-v415"
```

Use a new output directory. The renderer refuses to overwrite an existing one. It writes five GIFs, five posters, scene PNGs, and a JSON report. Inspect them before replacing the ten distributed media files, using the project's edit guard to preserve changes.

## Content

- Installation: paste, run, and verify in Windows PowerShell, macOS Terminal, and Linux Terminal. Output is illustrative; rendering does not execute the installer.
- Handoff: two desktop windows stay visible through project work, usage warning, handoff offer, selection, generation, copy, paste, and continuation. A five-stage chart remains visible. Both apps use supplied project files and Nexus Hub guidance. ChatGPT drafts the unfinished test; it does not claim to run repository checks.
- Workflow: `/describe`, `/review`, `/plan`, `/implement`, `/test`, and `/update release` inside a VS Code mockup.
- Commands: representative examples. `/skills list` reads the current catalog; the renderer checks the referenced command names.
- Settings: the real IDE extension's supported controls, including manual session effort choices and Apply to all, without an extra selection outline.

Playback starts paused in the offline preview. Readers can use scene buttons, Previous/Next, Play/Pause, or the text walkthrough. Every GIF has a static alternative. All preview assets are local.
