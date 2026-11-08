# README Visuals

Six README tours show Nexus Hub inside the tools that consume it. Installation and workflow use the original HTML guide; settings and usage monitors use their shipped renderers with isolated sample data. Claude and ChatGPT desktop windows and IDE shells are illustrations. VS Code uses the user's screenshots; Cursor and Antigravity use native layout references inspected during this refinement. All conversations and account values are samples.

## Sources

| Tour | Source and behavior |
| --- | --- |
| Installation | Original guide terminal, constrained to 900 x 385 pixels with scrolling output. Windows, macOS, and Linux use the guide's commands, wordmark, output, and verification states. |
| Workflow | Original training story across six stages. The guide's full timeline preserves selection, typing, and tool-result pacing, with 4.8-second final result holds. A cursor and spotlight follow the active control; the workflow strip stays visible. |
| Handoff | Dark Claude and ChatGPT desktop windows on an original dark Windows 11-style desktop. Thirteen stages show the three usage choices, Hand off selection, streamed generation, Copy, paste, Send, and continuation. The exact same full prompt is checked in the ChatGPT composer and sent user message. |
| Settings | Shipped Nexus Hub webview beside Claude Code and Codex editor tabs. The tour shows global effort changes, a manual Codex override, Apply to all, Fast mode, guardrails, alerts, and the Nexus status hover. |
| Usage | Shipped Claude, Codex, and Copilot status-bar and dashboard renderers. Three portrait-cropped VS Code desktops hover and open their dashboards together. Each uses the original hover SVGs and dashboard HTML, including the purple Codex and teal Copilot bars. |
| Platforms | Cursor and Antigravity native Agent layouts beside the shipped settings webview. Controls follow editor capabilities; Antigravity Fast is disabled and each editor has one alert master switch. |
| Commands | Seven collapsible Markdown groups in the README, generated from all 24 HTML-guide cards with scopes, flags, examples, and notes. |

- [Offline overview](../../guides/website/readme-demos.html), [settings tour](../../guides/website/readme-vscode.html), [parallel usage tour](../../guides/website/readme-showcase.html?tour=usage), and [platform tour](../../guides/website/readme-showcase.html?tour=platforms).
- [Guide](../../guides/website/nexus-hub-guide.html) and [training](../../guides/website/training.html), which remain unchanged.
- Desktop illustration: [scenes](../../guides/website/readme-platforms.js), [styles](../../guides/website/readme-platforms.css), and [wallpaper](../../guides/website/readme-desktop.svg).
- VS Code illustration: [HTML](../../guides/website/readme-vscode.html), [styles](../../guides/website/readme-vscode.css), and [controller](../../guides/website/readme-vscode.js).
- Parallel usage and platform illustrations: [HTML](../../guides/website/readme-showcase.html), [styles](../../guides/website/readme-showcase.css), and [controller](../../guides/website/readme-showcase.js). Cursor and Antigravity app artwork was copied from their installed application resources.
- Shared cursor and spotlight: [script](../../guides/website/readme-tour.js) and [styles](../../guides/website/readme-tour.css).

The handoff follows the [session-handoff contract](../../catalog/skills/workflow/session-handoff/SKILL.md): Goal, Done and verified, In progress, Next steps, Files touched, Constraints and decisions the user stated, Open questions and blockers, and Repository state. The destination receives task context, not instructions to wait for the previous provider's usage reset.

## Regeneration

From the repository root, with Node, the settings extension's development dependencies, Pillow, Playwright, and Playwright Chromium installed, run in PowerShell:

```powershell
python scripts/render_readme_demos.py --output "$env:TEMP/nexus-hub-readme-guided-export"
```

Use a new output directory. The renderer refuses overwrites. It writes six GIFs, six posters, scene/keyframe PNGs, a generated `usage-components.js` payload, a generated `cheatsheet.md`, and a JSON report. Use `--only installation`, `workflow`, `settings`, `usage`, `platforms`, or `continuity` for one export. Inspect the frames before replacing distributed files through the project's edit guard.

[Guide adapter](../../scripts/readme_guide_capture.py) seeks the original story API. [Provider adapter](../../scripts/readme_provider_capture.py) embeds the actual settings webview. [Monitor adapter](../../scripts/readme_usage_render.cjs) loads the original TypeScript renderers with a local VS Code API stub; it neither starts the extensions nor accesses accounts. [Showcase adapter](../../scripts/readme_showcase_capture.py) captures parallel monitors and editor-specific controls. [Cheatsheet adapter](../../scripts/readme_cheatsheet.py) exports the guide cards as Markdown. Copy its output into the README's `readme-cheatsheet` markers through the edit guard. The handoff description follows the canonical chat-only contract rather than the guide's older file-first wording. The generated [component payload](usage-components.js) keeps the preview offline and is regenerated from these sources.

Rendering does not execute an installer, contact a provider, or change user settings. All account values and agent conversations are samples. These are documentation illustrations, not native-provider qualification. The original source guide, settings webview, and usage-monitor implementations remain unchanged. Reserved GIF palette entries preserve source brand colors; the handoff dimming layer leaves app identity artwork unchanged. The older command GIF and PNG are retained only as historical assets and are no longer used in the README. Every GIF has a static alternative.
