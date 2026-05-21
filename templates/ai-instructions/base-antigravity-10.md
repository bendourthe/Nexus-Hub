@base-google-shared.md

## Surface: Antigravity 1.0 (Google IDE, pre-I/O 2026 release)

This file deploys to `~/.gemini/antigravity/rules.md` (global) or `<project>/.gemini/antigravity/rules.md` (workspace) and is consumed by the original Antigravity IDE released ahead of Google I/O 2026. Antigravity 1.0 shares the `~/.gemini/` root with Gemini IDE and Gemini CLI but writes to its own `antigravity/` subdirectory.

- Binary / invocation: in-IDE only (Antigravity 1.0 desktop)
- Customizations: surfaced via the IDE's Customizations menu; the on-disk layout uses `rules_library/` for rule sets and `global_workflows/` for saved prompts
- Hooks: not supported on the 1.0 surface (see Antigravity 2.0 for hook support)
- Migration note: Antigravity 1.0 is superseded by Antigravity 2.0 + CLI for new users; this template remains supported for existing 1.0 installs
