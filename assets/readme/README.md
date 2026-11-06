# README Visuals

README media is generated from the original interactive guide, the shipped Nexus Hub settings panel, and an illustrative Claude desktop to ChatGPT desktop handoff. Nexus Hub remains a backend harness; its optional settings extension appears inside the host IDE.

## Sources

- [Installer and command cards](../../guides/website/nexus-hub-guide.html): the renderer captures the original terminal DOM and command cards, including their existing output, typography, wordmark, and scopes.
- [Development workflow](../../guides/website/training.html): the renderer seeks the original story player across all six stages. File trees, editor tabs, code edits, tool calls, composers, model controls, usage meters, and the workflow strip come from the guide. The guide and its story files are unchanged.
- [Settings panel](../../extensions/nexus-hub-settings/media/panel.js) and [styles](../../extensions/nexus-hub-settings/media/panel.css): the shipped webview is rendered with sample data inside the guide's IDE shell. Two illustrative sessions show global changes, a manual override, Apply to all, and Fast mode. These captures demonstrate the controls; they are not native-provider test evidence.
- [Desktop handoff](../../guides/website/readme-platforms.js), [styles](../../guides/website/readme-platforms.css), and [original desktop wallpaper](../../guides/website/readme-desktop.svg): separate warm Claude and dark ChatGPT windows, a Windows-style taskbar, and a permanent five-step process chart. Both apps receive project context. ChatGPT drafts the unfinished test; it does not claim to run repository checks.
- [Offline preview](../../guides/website/readme-demos.html): source-guide links, exported animations, and an opt-in desktop handoff with Previous, Next, Play/Pause, scene selection, and a text transcript.

## Regeneration

From the repository root, with Pillow, Playwright, and Playwright Chromium already installed, run in PowerShell:

```powershell
python scripts/render_readme_demos.py --output "$env:TEMP/nexus-hub-readme-guide-export"
```

Use a new output directory. The renderer refuses to overwrite an existing one. It writes five GIFs, five posters, keyframes, and a JSON report. Use `--only installation`, `workflow`, `settings`, `commands`, or `continuity` for one export. Inspect the frames before replacing distributed media, using the project's edit guard to preserve changes.

[Capture adapter](../../scripts/readme_guide_capture.py) uses the original guide DOM and story API. Frames are padded when source heights differ; they are never stretched. The website navigation is excluded from exports. Terminal output and agent actions are demonstrations: rendering never executes an installer, contacts a provider, or changes user settings. Every GIF remains below 4 MiB and has a static alternative.

## Desktop References

The app windows are illustrations, not screenshots of a running desktop session. Layout references include the official [Claude desktop tutorial](https://academy.claude.com/tutorials/navigating-the-claude-desktop-app), [Claude Projects guide](https://support.claude.com/en/articles/9517075-what-are-projects), and [ChatGPT Windows release notes](https://help.openai.com/en/articles/10003026-windows-app-release-notes). The Windows release-notes screenshot is a historical layout reference; app interfaces can change.
