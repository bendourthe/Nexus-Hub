# Development Log

## [2026-01-28 22:15] - Release 0.5.1: Cross-Platform Support

*   **Goal**: Extend the DevAI-Hub installer to support macOS and Linux operating systems.
*   **Implementation**:
    *   **Bash Installer**: Ported the logic from `installer.ps1` to `scripts/installer.sh` using Bash.
    *   **Features Preserved**: Replicated global installation, workspace selection, language detection, and safe overwrite prompts.
    *   **Entry Point**: Created a root-level `install.sh` script for easy execution.
*   **Documentation**: Updated `README.md` to guide non-Windows users.
*   **Result**: The repo now supports Windows, macOS, and Linux with a unified installation experience.

## [2026-01-28 21:35] - Release 0.5.0: Universal Catalog & Installer V5 Refactor

*   **Goal**: Refactor the entire repository to a "Universal Catalog" model to remove duplication between Claude/Gemini and various languages, and build a robust, user-friendly installer.
*   **Challenges & Solutions**:
    1.  **Duplicate Templates**: Previous versions had `templates/ai-instructions/claude-code/{lang}` which duplicated content.
        *   *Solution*: Created `catalog/` with `skills`, `commands`, `context`, `memory`. Moved all assets there. Deleted legacy folders.
    2.  **Installer Instability**: The minimal `Install-Global` logic was missing providers and crashed due to syntax errors during refactoring.
        *   *Error*: `Unexpected token '}'` in `installer.ps1`.
        *   *Fix*: Restored the deleted function definitions (`Detect-Languages`, etc.) and fixed the brace mismatch.
    3.  **Inconsistent Logging**: User reported "Global" phase didn't show details like "Workspace" phase.
        *   *Fix*: Updated `Safe-Copy` to support `CustomMessage`. Added explicit "Global instructions installed at..." logs.
    4.  **Overwrite Fatigue**: Users had to press 'Y' for every file.
        *   *Fix*: Added `[A]ll` option to overwrite prompts, setting a global `$script:OverwriteAll` flag.
*   **New Capabilities**:
    *   **Universal Commands**: Created `generate-tests`, `run-deep-review` (renamed from `test`/`review`), `generate-sbom`, `update-devlog`, `create-skill-or-command`.
    *   **Smart Installer**: `installer.ps1` now handles global *and* local config with identical logic.
*   **Current Status**: Verified. Installer V5 is stable. Catalog is live.
