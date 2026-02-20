# Development Log

## [2026-02-20] - Release 0.6.3: Word/PowerPoint Report Generation, Template System

*   **Goal**: Enable users to generate professional Word and PowerPoint documents from Markdown analysis files via a single command, with custom template support.
*   **What Changed**:
    *   **Generate Word Report Command**: Created `catalog/commands/generate-word-report.md` (183 lines, 6-phase workflow) that reads Markdown files, discovers templates from project and global directories, analyzes content structure, and produces formatted .docx or .pptx output.
    *   **Report Generator Extension**: Extended `scripts/generate_report.py` with `--type generic-word` and `--type generic-pptx`. Added ~550 lines covering Markdown-to-DOCX conversion (title page, TOC, headers/footers, page numbers) and Markdown-to-PPTX conversion (slide structure parser, section dividers, content slides, code block text boxes). Fixed existing bug in `add_markdown_paragraph()` where empty code block lines caused IndexError.
    *   **python-pptx Integration**: Added optional `python-pptx` dependency. PowerPoint generation maps H1 headings to section divider slides, H2 headings to content slides with body text frames, code blocks to monospace text boxes with gray backgrounds, and bullet points to structured slide content.
    *   **Installer Phase 4**: Added `Install-Templates` (PS1) and `install_templates` (Bash) as Phase 4 to both installers. Copies bundled templates and `generate_report.py` to `~/.devai-hub/`. PowerShell version uses `System.Windows.Forms.OpenFileDialog` for native multi-file template import. Bash version supports drag-and-drop file paths.
    *   **Template System**: Dual-layer discovery (project `.claude/templates/documentation/` overrides global `~/.devai-hub/templates/documentation/`). Bundled `generic-word-report-template.docx` as default.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `scripts/generate_report.py` from 0.6.2 to 0.6.3. Installers bumped from V7 to V8. Registered `generate-word-report` in `skills.json` (66 skills total).
*   **Current Status**: Verified. Word and PowerPoint generation tested with single and multiple Markdown files, with and without templates. Backward compatibility confirmed for existing codebase/code-review report types.

## [2026-02-19] - Release 0.6.2: CLI Usage Display, Command Overhaul, Changelog Generator

*   **Goal**: Add automatic CLI usage limits display, overhaul the command catalog for better separation of concerns, and add a changelog generation command.
*   **What Changed**:
    *   **Usage Display Hook**: Created `catalog/hooks/usage-display.sh` (Stop hook) that auto-fetches from the Anthropic OAuth API with 5-minute caching. Updated `catalog/hooks/settings.json`, both installers (`Install-UsageDisplay` / `install_usage_display`), and `infrastructure/hooks/README.md`.
    *   **Command Catalog Overhaul**:
        *   Added `generate-changelog.md` for full CHANGELOG.md reconstruction from git history.
        *   Replaced `run-code-review.md` with `review-codebase.md` (expanded to 596-line senior-level review).
        *   Rewritten `update-documentation.md` to focus on READMEs/guides only (excludes CHANGELOG/DEVLOG, defers to dedicated commands).
        *   Enhanced `update-version.md` (renamed from `updated-version`) with Keep a Changelog formatting, richer DEVLOG entries, and documentation update step (14 steps).
        *   Rewritten `analyze-codebase.md` with 12-section structured analysis and Mermaid diagrams.
        *   Enhanced `check-usage.md` with auto-fetch Phase 0 and cross-references.
    *   **Documentation**: Restructured root README usage monitoring section. Added cross-references across CLI hook, VS Code extension, and `/check-usage` command.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh` from 0.6.1 to 0.6.2. Installers bumped from V6 to V7.
*   **Current Status**: Verified. All version references consistent at 0.6.2.

## [2026-02-19] - CLI Usage Limits Display (Stop Hook)

*   **Goal**: Address user feedback requesting token limit visibility in the CLI. Users could see tokens consumed but had to navigate to `claude.ai/settings/usage` to see how close they were to their cap.
*   **What Changed**:
    *   **Usage Display Hook**: Created `catalog/hooks/usage-display.sh` (Stop hook, 213 lines) that fetches from the Anthropic OAuth API, caches responses for 5 minutes, and displays a compact color-coded summary to stderr when any metric exceeds 50%. Includes graceful degradation (silent exit) for missing curl/jq, missing credentials, expired tokens, and network errors.
    *   **Hook Config**: Updated `catalog/hooks/settings.json` with Stop hook entry alongside existing PreToolUse.
    *   **Installer Integration**: Added `install_usage_display` (Bash) and `Install-UsageDisplay` (PowerShell) functions to both installers. Installed in both global (Phase 1) and workspace (Phase 2) with idempotent settings.json merge.
    *   **Check-Usage Enhancement**: Added Phase 0 auto-fetch to `catalog/commands/check-usage.md`. The command now reads OAuth credentials and calls the API directly via curl before falling back to manual entry.
    *   **Documentation**: Added "Usage Display (Stop Hook)" section to `infrastructure/hooks/README.md` with configuration, customization, and cross-references to the VS Code extension and `/check-usage` command.
*   **Design Decisions**:
    *   50% smart threshold (silent when healthy, visible when it matters)
    *   5-minute cache TTL to prevent API spam
    *   3-second curl timeout to never block the CLI
    *   Reused the same Anthropic OAuth API endpoint as the VS Code extension (`usageFetcher.ts`)
*   **Current Status**: Implemented. Three complementary usage monitoring features now exist: automatic CLI hook (passive), VS Code extension (visual), and `/check-usage` command (on-demand).

## [2026-02-19] - Release 0.6.1: Git Guardrails, Tracer Bullets, Report Fixes

*   **Goal**: Add deterministic safety enforcement for AI agents running destructive git commands, plus workflow improvements and report generation fixes.
*   **What Changed**:
    *   **Git Guardrails Hook**: Created `catalog/hooks/git-guardrails.sh` (PreToolUse hook) that intercepts Bash commands, matches against 12 dangerous git patterns, and blocks with exit code 2. Includes `catalog/hooks/settings.json` template for Claude Code integration.
    *   **Installer Integration**: Added `Install-GitGuardrails` (PS1) and `install_git_guardrails` (Bash) functions. Both installers now install the hook in global (Phase 1) and workspace (Phase 2) with idempotent JSON merge into `.claude/settings.json`.
    *   **AI Instructions**: Added `### 7. Tracer Bullets` workflow directive and `## Git Safety` soft enforcement section to `generic-instructions.md`, `catalog/CLAUDE.md`, and root `CLAUDE.md`.
    *   **Hooks Documentation**: Added comprehensive "Git Guardrails (PreToolUse Hook)" section to `infrastructure/hooks/README.md` with customization guide and verification steps.
    *   **Report Generation**: Fixed dependency categorization and platform support merging in `scripts/generate_report.py` and `catalog/commands/analyze-codebase.md`.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh` from 0.6.0 to 0.6.1.
*   **Current Status**: Verified. All version references consistent at 0.6.1.

## [2026-02-10 18:00] - Release 0.6.0: Claude Usage Monitor, Code Review Overhaul, Documentation Fixes

*   **Goal**: Release v0.6.0 encompassing the Claude Usage Monitor VS Code extension, merged code-review-expert methodology, skills registry validation, and comprehensive documentation consistency fixes.
*   **What Changed**:
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh` from 0.5.3 to 0.6.0. Installers renamed from V5 to V6.
    *   **CHANGELOG.md**: Converted `[Unreleased]` section to `[0.6.0] - 2026-02-10` with full Added/Changed entries. Added 0.6.0 row to Version History Summary table. Updated footer compare links.
    *   **Documentation Fixes** (22 issues resolved from `/update-documentation` audit):
        *   Root `README.md`: Removed Codex (OpenAI) references, fixed CLAUDE.md path, fixed Copilot path casing, added VS Code Extension section, updated skill count to 63.
        *   Extension `README.md`: Fully rewritten to match current functionality (5 commands, 4 settings, auto-fetch API, SVG tooltip, dashboard).
        *   `skills.json`: Fixed 34 stale paths, removed 15 deleted skills, added 30 new entries, validated all 65 entries against disk.
        *   `CHANGELOG.md`: Fixed 19 footer URLs (`yourusername` to `bdourthe`), added 4 missing version links.
*   **Lessons Learned**: Running `/update-documentation` before a version release is an effective way to catch stale references and path inconsistencies across the project.
*   **Current Status**: Verified. All version references consistent at 0.6.0.

## [2026-02-10 12:00] - Created Claude Usage Monitor VS Code Extension

*   **Goal**: Build a VS Code extension that monitors Claude Code API usage (session and weekly limits) with auto-fetching, a status bar indicator, rich tooltip, and a full dashboard panel.
*   **Attempted Solutions**:
    *   *Icon Font Generation (fantasticon)*:
        *   *Result*: Failed. fantasticon v4.x reported "No SVGs found" regardless of path format, even in a temp directory without spaces. Version self-reported as "0.0.0".
        *   *Analysis*: fantasticon's glob resolution is broken in v4.x on Windows.
        *   *Solution*: Bypassed fantasticon entirely. Wrote custom `scripts/generate-icon-font.js` using `svgpath` + `svg2ttf` + `ttf2woff2`. Key insight: SVG fonts have Y-axis going UP (opposite of regular SVGs), requiring `svgpath(path).scale(64, -64).translate(0, 1024)` for 16px to 1024 unitsPerEm conversion.
    *   *Tooltip Progress Bars (HTML divs)*:
        *   *Result*: Failed. VS Code MarkdownString tooltips do not render `background` CSS on content-less `<div>` elements. `<table>` width attributes are also ignored.
        *   *Analysis*: VS Code's tooltip renderer has a limited CSS subset. Properties like `background`, `color`, `opacity`, and `font-style` on arbitrary HTML elements are unreliable.
        *   *Solution*: Switched to SVG data URI images via `<img src="data:image/svg+xml,${encodeURIComponent(svg)}">`. This renders reliably when `isTrusted` and `supportHtml` are true.
    *   *Percentage Right-Alignment (HTML tables)*:
        *   *Result*: Failed. HTML `<table width="260">` was not respected by VS Code's tooltip. Percentages appeared next to labels instead of at the far right edge.
        *   *Solution*: Baked label, percentage, AND progress bar into a single SVG image using `text-anchor="end"` for guaranteed pixel-perfect right alignment.
    *   *PowerShell Installer Phase 3*:
        *   *Result*: Initially failed. `$ErrorActionPreference = "Stop"` converted npm/npx stderr output into terminating PowerShell exceptions.
        *   *Solution*: Wrap native CLI tool sections with `$ErrorActionPreference = "Continue"` and restore afterward. Use `2>$null | Out-Null` instead of `2>&1 | Out-Null` for stderr suppression.
*   **Changes**:
    *   Created `extensions/claude-usage-monitor/` (full extension, 22 files):
        *   `src/usageFetcher.ts`: Reads OAuth token from `~/.claude/.credentials.json`, calls `GET https://api.anthropic.com/api/oauth/usage` with `anthropic-beta: oauth-2025-04-20` header, maps response to internal types.
        *   `src/statusBarManager.ts`: Status bar with `$(claude-icon)` custom icon, `X% (current) Y% (week)` format, SVG data URI tooltip with theme-aware colors via `activeColorTheme.kind`, auto-refresh timer.
        *   `src/dashboardPanel.ts`: WebviewPanel with full usage breakdown, model recommendations, optimization tips, theme-aware tab icons via `{ light: Uri, dark: Uri }` iconPath.
        *   `src/extension.ts`: Orchestrates auto-fetch on activation, registers commands (`dashboard`, `refresh`, `update`, `reset`), configures auto-refresh interval.
        *   `src/inputCollector.ts`: Manual input fallback (4-step wizard) when API credentials are unavailable.
        *   `src/recommendations.ts`: Usage-based model switching recommendations (Opus/Sonnet/Haiku).
        *   `scripts/generate-icon-font.js`: Custom SVG-to-WOFF2 font generator.
        *   `icons/claude.svg`, `icons/claude-dark.svg`, `icons/claude-light.svg`: Theme-aware icon variants.
        *   `fonts/claude-icons.woff2`: Generated icon font at codepoint U+E101.
    *   Modified `scripts/installer.ps1`: Added Phase 3 (extension build, VSIX packaging, VS Code installation with Node.js detection).
    *   Modified `scripts/installer.sh`: Added Phase 3 (same logic for macOS/Linux with brew/apt detection).
    *   Created `catalog/commands/check-usage.md`: CLI command for checking usage from the terminal.
    *   Added `catalog/claude_icon.svg`, `catalog/claude_logo.png`: Icon assets.
    *   Modified `skills.json`: Registered `check-usage` command.
*   **Lessons Learned**:
    *   VS Code MarkdownString tooltips support `<img>` tags with `data:image/svg+xml` URIs but do NOT reliably support CSS `background`, `color`, `opacity`, or `font-style` on HTML elements. Tables render but ignore width attributes. The most reliable approach for custom graphics in tooltips is inline SVG data URIs.
    *   fantasticon v4.x is unusable on Windows. A custom script with `svgpath` + `svg2ttf` + `ttf2woff2` is more reliable and produces smaller output.
    *   PowerShell `$ErrorActionPreference = "Stop"` must be temporarily disabled when invoking npm, npx, node, or any native CLI tool that writes to stderr as part of normal operation.
    *   The Claude OAuth usage API lives at `https://api.anthropic.com/api/oauth/usage` (not `claude.ai`), requires the `anthropic-beta: oauth-2025-04-20` header, and returns `five_hour`, `seven_day`, `seven_day_sonnet`, `seven_day_opus`, and `extra_usage` fields each with `utilization` (0-100) and `resets_at` (ISO 8601).
*   **Current Status**: Verified. Extension builds, packages, installs, and runs correctly. Auto-fetch populates status bar on activation. Tooltip shows SVG progress bars with theme-aware colors. Dashboard opens with Claude icon on tab. Manual fallback works when credentials are missing.

## [2026-02-06 14:00] - Merged code-review-expert into run-code-review

*   **Goal**: Merge the methodology from `sanyuan0704/code-review-expert` (GitHub) into the existing `run-deep-review` command and rename to `run-code-review`, creating a unified, comprehensive code review system.
*   **What Changed**:
    *   **New Command**: Created `catalog/commands/run-code-review.md` replacing `run-deep-review.md`. Supports dual-mode (full codebase review and git-changes review), P0-P3 severity classification, review-first paradigm (no changes without user confirmation), and a structured next steps menu.
    *   **New Reference Checklists** (4 files under `catalog/skills/code-review/references/`):
        *   `solid-checklist.md`: SOLID diagnostic questions per principle, 12 code smells with thresholds, 7 refactor heuristics.
        *   `security-checklist.md`: 10-domain security model with diagnostic questions, including race conditions deep-dive (shared state, TOCTOU, DB concurrency, distributed systems).
        *   `code-quality-checklist.md`: Error handling anti-patterns, performance/caching analysis, boundary conditions (null, empty, numeric, string).
        *   `removal-plan.md`: Dead code removal templates (safe-delete-now vs defer-with-plan), 7-item pre-removal checklist.
    *   **Updated Skills** (all 6 SKILL.md files bumped to v2.0.0):
        *   `context-analysis`: Added dual-mode support, git-changes preflight, edge case handling (>500 lines batching), critical path identification.
        *   `code-quality`: Added SOLID analysis with diagnostic questions, dead code removal planning, expanded to 12 code smells, 7 refactor heuristics.
        *   `security-review`: Restructured to 10-domain model, added race conditions deep-dive (4 sub-categories), exploitability + impact assessment, expanded language-specific vulnerability lists (C#, Go).
        *   `performance-review`: Added caching strategy analysis (TTL, invalidation, stampede, key collisions), boundary conditions, 4 diagnostic questions.
        *   `testing-review`: Added P0-P3 severity classification, git-changes mode gap analysis.
        *   `final-report`: Added overall verdict (APPROVE/REQUEST_CHANGES/COMMENT), inline comment format, clean review protocol, next steps confirmation menu, review-first enforcement.
    *   **Deleted**: `catalog/commands/run-deep-review.md` (replaced by `run-code-review.md`).
*   **Key Design Decisions**:
    *   Unified severity on P0-P3 scale (with CRITICAL/HIGH/MEDIUM/LOW as aliases) for consistency across all phases.
    *   Adopted review-first paradigm from code-review-expert: findings are presented first, user must confirm before any changes are implemented.
    *   Integrated SOLID analysis and dead code removal into the existing code-quality phase (Phase 2) rather than adding new phases, keeping the 6-phase structure intact.
    *   Reference checklists are standalone files in `references/` to allow independent maintenance and reuse across skills.
*   **Current Status**: Complete. All files verified. No functional stale references (only historical mentions in DEVLOG.md and CHANGELOG.md).

## [2026-02-04 15:32] - Release 0.5.3: Documentation Fixes & Command Cleanup

*   **Goal**: Simplify the repository by removing deprecated legacy skill definitions, consolidating catalog commands, and fixing critical broken links.
*   **Attempted Solutions**:
    *   **Cleanup Legacy Skills**:
        *   *Action*: Removed `.codex`, `.gemini`, and `.github/copilot-instructions.md` directories containing outdated definitions.
        *   *Result*: Success. Codebase is significantly cleaner.
    *   **Consolidate Commands**:
        *   *Action*: Consolidated `generate-commit-message`. Removed redundant `create-commit-message`, `generate-codebase-report`, `upgrade-version`.
        *   *Result*: Success. Reduced maintenance overhead.
    *   **Installer Logic**:
        *   *Action*: Updated `scripts/installer.ps1` to ensure `$globalAntigravityWorkflows` directory is explicitly created before copying.
        *   *Result*: Verified.
*   **Changes**:
    *   Modified `scripts/installer.ps1`: Enhanced global workflow directory handling.
    *   Modified `scripts/generate_report.py`: Refined report generation logic.
    *   Deleted `.codex/`, `.gemini/`, `.github/copilot-instructions.md`: Removed legacy artifacts.
*   **Lessons Learned**: Always verify destination directory existence in PowerShell before copy operations to prevent runtime errors.
*   **Current Status**: Verified.

## [2026-01-30 16:55] - Release 0.5.2: Enhanced Reporting & Upgrade Automation

*   **Goal**: Improve the codebase reporting capabilities with professional DOCX output and streamline the version upgrade process.
*   **Implementation**:
    *   **Reporting**: Updated `scripts/generate_report.py` to support `python-docx`, automatic TOC updates via Word Interop, and better metadata handling.
    *   **Upgrade Automation**: Enhanced the `/upgrade-version` workflow to perform auto-analysis of git changes, generate context-aware commit messages, and validate version consistency.
    *   **Documentation**: Added a dedicated Claude Skills section to `README.md` and standardized Python template formatting.
*   **Result**: Users can now generate professional-grade codebase reports and manage project versions with significantly less manual effort.

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
    *   1.  **Duplicate Templates**: Previous versions had `templates/ai-instructions/claude-code/{lang}` which duplicated content.
        *   *Solution*: Created `catalog/` with `skills`, `commands`, `context`, `memory`. Moved all assets there. Deleted legacy folders.
    *   2.  **Installer Instability**: The minimal `Install-Global` logic was missing providers and crashed due to syntax errors during refactoring.
        *   *Error*: `Unexpected token '}'` in `installer.ps1`.
        *   *Fix*: Restored the deleted function definitions (`Detect-Languages`, etc.) and fixed the brace mismatch.
    *   3.  **Inconsistent Logging**: User reported "Global" phase didn't show details like "Workspace" phase.
        *   *Fix*: Updated `Safe-Copy` to support `CustomMessage`. Added explicit "Global instructions installed at..." logs.
    *   4.  **Overwrite Fatigue**: Users had to press 'Y' for every file.
        *   *Fix*: Added `[A]ll` option to overwrite prompts, setting a global `$script:OverwriteAll` flag.
*   **New Capabilities**:
    *   **Universal Commands**: Created `generate-tests`, `run-deep-review` (renamed from `test`/`review`), `generate-sbom`, `update-devlog`, `create-skill-or-command`.
    *   **Smart Installer**: `installer.ps1` now handles global *and* local config with identical logic.
*   **Current Status**: Verified. Installer V5 is stable. Catalog is live.
