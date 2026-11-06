# README Visuals

Editable, offline VS Code mockups for the Nexus Hub controls and development workflow. These visuals are illustrative teaching assets, not evidence of a real provider session or release run.

## Sources

- [HTML preview](../../guides/website/readme-demos.html): scene content, layout, keyboard controls, text walkthroughs, and opt-in playback.
- [Renderer](../../scripts/render_readme_demos.py): captures Chromium frames and assembles GIFs with one shared palette per animation.
- [Guide](../../guides/website/nexus-hub-guide.html) and [Training](../../guides/website/training.html): the six-command workflow and game example.

## Regeneration

From the repository root, with Pillow, Playwright, and Playwright Chromium already installed, run this command in PowerShell:

```powershell
python scripts/render_readme_demos.py --output "$env:TEMP/nexus-hub-readme-v415"
```

The output directory must be new. The renderer refuses to overwrite an existing directory. It writes two GIFs, two posters, individual scene PNGs, and a JSON report. Review the rendered scenes before replacing the four distributed GIF/PNG files in this folder; preserve any edits with the project's edit guard first. The source uses only local assets and makes no network requests.

## Content Contract

Settings scenes show a global change, a manual session override, a new agent, Apply to all, Fast mode, a supported guardrail event, alert suppression with taskbar monitoring retained, and Codex History/Refresh access. Only representative controls are shown. Provider names are model-family labels without version numbers.

Workflow scenes follow `/describe`, `/review`, `/plan`, `/implement`, `/test`, and `/update release`. Example outputs explain the handoff between commands; test, commit, and release text does not claim those actions ran against this repository.

The offline preview starts paused. Readers can use Previous, Next, individual scene buttons, or Play/Pause, with keyboard focus indicators and text alternatives. The README links to static posters beside each GIF.
