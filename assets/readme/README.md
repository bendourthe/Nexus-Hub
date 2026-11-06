# README Visuals

Editable, offline IDE and desktop-app mockups for the Nexus Hub knowledge layer, shared controls, command discovery, handoffs, and development workflow. These visuals are illustrative teaching assets, not evidence of a real provider session or release run.

## Sources

- [HTML preview](../../guides/website/readme-demos.html): scene content, layout, keyboard controls, text walkthroughs, and opt-in playback.
- [Platform scenes](../../guides/website/readme-platforms.js) and [styles](../../guides/website/readme-platforms.css): command examples and the VS Code, Cursor, Antigravity, Claude desktop, and ChatGPT desktop views.
- [Renderer](../../scripts/render_readme_demos.py): captures Chromium frames and assembles GIFs with one shared palette per animation.
- [Guide](../../guides/website/nexus-hub-guide.html) and [Training](../../guides/website/training.html): the six-command workflow and game example.

## Regeneration

From the repository root, with Pillow, Playwright, and Playwright Chromium already installed, run this command in PowerShell:

```powershell
python scripts/render_readme_demos.py --output "$env:TEMP/nexus-hub-readme-v415"
```

The output directory must be new. The renderer refuses to overwrite an existing directory. It writes four GIFs, four posters, individual scene PNGs, and a JSON report. Command examples are validated against the actual catalog before rendering. Review the rendered scenes before replacing the eight distributed GIF/PNG files in this folder; preserve any edits with the project's edit guard first. The source uses only local assets and makes no network requests.

## Content Contract

The continuity animation presents the local knowledge foundation, a chat-only handoff from VS Code, continuation in Cursor and Antigravity, user-provided context in Claude and ChatGPT desktop chats, and return to an IDE agent for execution and verification. Desktop views do not imply automatic synchronization or installed IDE controls.

The command animation is a representative quick reference. `/skills list` reads the current command catalog; these visual examples are not a second registry.

Settings scenes show a global change, a manual session override, a new agent, Apply to all, Fast mode, a supported guardrail event, alert suppression with taskbar monitoring retained, and Codex History/Refresh access. Only representative controls are shown. The mockup uses native-style control state changes without an added selection outline. Provider names are model-family labels without version numbers.

Workflow scenes follow `/describe`, `/review`, `/plan`, `/implement`, `/test`, and `/update release`. Example outputs explain the handoff between commands; test, commit, and release text does not claim those actions ran against this repository.

The offline preview starts paused. Readers can use Previous, Next, individual scene buttons, or Play/Pause, with keyboard focus indicators and text alternatives. The README links to static posters beside each GIF.
