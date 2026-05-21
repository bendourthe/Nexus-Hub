@base-google-shared.md

## Surface: Gemini IDE (Google Code Assist)

This file deploys to `~/.gemini/GEMINI.md` (global) or `<project>/.gemini/GEMINI.md` (workspace) and is consumed by the in-IDE Gemini Code Assist extension. The Gemini IDE shares the `~/.gemini/` root with Gemini CLI; if both surfaces are installed, both read this file via the `<!-- NEXUS_HUB_START -->` / `<!-- NEXUS_HUB_END -->` marker block so user-authored content above and below the block is preserved.

- Binary / invocation: in-IDE only (no PATH executable for the IDE surface; use the Code Assist panel inside VS Code / IntelliJ / Android Studio)
- Slash commands: not available on the IDE surface; use the Code Assist panel chat
- Permissions: governed by Code Assist's per-IDE settings -- Nexus-Hub does not write IDE-side permissions
