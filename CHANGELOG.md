# Changelog

All notable changes to the DevAI Hub repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

(none)

---

## [1.3.0] - 2026-05-12

### Added

- **New skill `docs-layout-refactor` (code-cleanup category)** with companion command `/refactor-docs` for auditing and reorganizing a project's `docs/` folder. The workflow walks the docs tree, scores every file with eight weighted heuristics (version-vs-active, external reference count, filename pattern, age, sha256 duplication, CHANGELOG citation, body keywords, inbound link count from other docs), assigns one of four explicit categories (Cat 1 delete / Cat 2 archive / Cat 3 stale-flag / Cat 4 active), and proposes a version-first reorganization with a dedicated `docs/archive/<source-version>/<topic>/` subtree. Default mode is propose-only; the `--apply` flag turns on a confirmation gate before any file moves or deletes. Signals 2 (external references) and 6 (CHANGELOG citation) are hard floors that can only raise a category, never lower it.
- **Stdlib-only Python helper `catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py`** (with PowerShell sibling for Windows users without Python on PATH) ships as a Tier-3 bundled resource. The agent invokes it via the shell and consumes NDJSON inventory and JSON reference-graph output without reading the script's source into context. Two subcommands: `inventory` (one record per file with size, mtime age, sha256 prefix, version dir, topic dir, line count, binary detection) and `refgraph` (inbound reference map from outside `docs/`).
- **Per-skill bundled `references/archive-layout.md`** documents the canonical `docs/archive/` tree shape (version-keyed for `docs/v*/` content, date-keyed wholesale for top-level subdirs like `docs/git/` or `docs/security/`), the `docs/archive/README.md` template, and the archive-path collision rule (suffix with `-<source-version>`, never silently overwrite).
- **New PreToolUse hook `catalog/hooks/old-version-docs-guard.sh`** (with PowerShell sibling) warns when Write or Edit targets a historical `docs/v<old-version>/` path. Non-blocking by default; the `DEVAI_OLD_DOCS_GUARD=block` env var upgrades it to a hard block (exit 1). Honors the existing `DEVAI_DISABLED_HOOKS` and `DEVAI_HOOK_PROFILE=minimal` runtime controls. Registered under `PreToolUse` for both `Write` and `Edit` tool matchers. Active-version detection walks docs/v*/ directories with semver comparison; if no `docs/v*/` exist, the hook is a silent no-op.
- **New `release-prep` bundle in `data/bundles.json`** groups seven skills for a one-click pre-release skill install: `docs-layout-refactor`, `project-layout-refactor`, `documentation-consistency`, `version-upgrade`, `release-notes-writer`, `known-gaps-tracker`, `code-commit-workflow`.
- **`--migrate-known-gaps` flag on `/refactor-docs`** auto-promotes Cat 3 (stale but load-bearing) findings into `docs/<next-version>/known-gaps.md` under a `## Stale documentation flagged by /refactor-docs` section, deduplicating by file path against existing entries. Bridges the gap between the docs-layout-refactor and known-gaps-tracker skills.
- **Pytest test `catalog/hooks/tests/test_old_version_docs_guard.py`** covers nine cases for the new hook: warns on historical docs/v*/ writes, silent on active version, hard block under `DEVAI_OLD_DOCS_GUARD=block`, silent for non-docs paths, silent for top-level docs files, silent when no version dirs exist, silent when disabled via `DEVAI_DISABLED_HOOKS`, silent under `DEVAI_HOOK_PROFILE=minimal`, and Windows path separator normalization. Tests requiring stderr output skip cleanly when `jq` is not installed (matching the existing pattern in `large-file-guard.sh` and `secret-scan.sh`).

### Changed

- **`/wrap-up-session`** Phase 2 (Codebase Hygiene) adds a new Step 2c that runs `/refactor-docs --mode audit` to produce a docs-cleanup report in audit-only mode (never auto-applies in wrap-up context). Triage table and completion-report template updated to surface the new step.
- **`/update-version`** Phase B (Cleanup) adds a new Step B4 that runs the full `/refactor-docs` workflow (propose-only by default with the command's own confirmation gate). The Phase B Summary template now includes a `Docs Cleanup` block with moved / deleted / flagged counts.
- **`/run-deep-review`** Phase 4 (Docs / Git / CI/CD Hygiene) adds a new subsection 4.11 that invokes `/refactor-docs --mode audit` and promotes Cat 1 findings to P2 and Cat 3 findings to P1 in the synthesis report. Cat 2 (archive candidates) flows in as informational only. The 4.10 summary table gets a new row for the docs cleanup signal.
- **`/review-codebase`** Phase 6f (Workflow and Developer Experience) adds an advisory bullet that triggers `/refactor-docs --mode audit` when `docs/` has more than 3 version directories.
- **`catalog/skills/code-cleanup/` description in `data/marketplace.json`** updated from "Language-specific cleanup for C, C++, C#, Go, Java, JavaScript, Python" to "Code, layout, and docs cleanup: per-language modernization plus repo and docs structural refactoring" to reflect that the category now covers both code modernization and structural refactoring (project layout + docs layout).
- **Skill total bumped from 196 to 197** (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` `skill_count` for `code-cleanup` from 9 to 10). Command total bumped to reflect `/refactor-docs`. Hook total bumped to reflect `old-version-docs-guard`. Surface updates in `AGENTS.md`, `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`.
- **Installer banner version** in `scripts/installer.sh` and `scripts/installer.ps1` bumped to `1.3.0`.

### Tests

- 364 hook pytest tests pass (3 skipped: the warning-path tests in `test_old_version_docs_guard.py` that require `jq` on PATH; consistent with the existing pattern). The new `test_old_version_docs_guard.py` adds 9 cases (6 pass without jq, 3 skip without jq).
- `python scripts/validate_skills.py --bundles-only` passes with 0 errors, 4 warnings (all pre-existing orphan-bundle warnings on `fastapi-expert`, `nextjs-expert`, `react-expert`; carried from WN-001). Total skills scanned: 201 (197 catalog + 4 fixtures).
- Smoke tests of `audit-docs.py`: `inventory` against this repo's `docs/` emits valid NDJSON for every file; `refgraph` against the repo correctly identifies inbound references to `docs/DEVLOG.md` from `README.md`, `AGENTS.md`, and skills under `catalog/skills/workflow/`.

### Fixed

- **Description-prefix separator is now a shell comment.** Both `catalog/hooks/format-bash-description.py` and `catalog/hooks/format-powershell-description.py` emit `# ___` instead of `___` as the divider line between the `# Description:` prefix and the actual command. The previous bare `___` line was a syntactically valid token that some shells would attempt to execute (or that PowerShell would interpret as a variable reference), producing spurious `command not found` style errors on retry. Commenting the divider out (`# ___`) keeps the visual separator but guarantees it is a no-op at execution time. `strip_description_box` recognizes both the legacy `___` shape and the new `# ___` shape so mid-conversation retries continue to round-trip cleanly. Test suites updated.
- **Windows-friendly directory listing permission.** `configs/permissions/claude-permissions.json` and `configs/permissions/gemini-permissions.json` add `Bash(dir)` / `Bash(dir *)` and `run_shell_command(dir)` to the auto-allow list alongside the existing `ls` entry, so Claude's and Gemini's permission dialogs do not prompt for the Windows-native directory listing command.

### Migration Impact

Users re-run the installer. The new skill bundle (under `catalog/skills/code-cleanup/docs-layout-refactor/`), command (`catalog/commands/refactor-docs.md`), hook script and PowerShell sibling (`catalog/hooks/old-version-docs-guard.{sh,ps1}`), and bundle entry (`data/bundles.json` `release-prep`) all land at their expected target paths via existing recursive-copy logic. The hook is registered under `PreToolUse` for `Write` and `Edit` in `catalog/hooks/settings.json`. No installer flow change, no schema change, no `settings.json` structural change for existing users. The four chained commands (`wrap-up-session`, `update-version`, `run-deep-review`, `review-codebase`) gain optional integration steps that default to safe modes (audit-only or with a confirmation gate).

---

## [1.2.1] - 2026-05-12

### Changed

- **Shell-tool description format: single-line `# Description:` prefix plus `___` separator line replaces the four-line comment box.** Both `catalog/hooks/format-bash-description.py` and `catalog/hooks/format-powershell-description.py` now prepend the shape `# Description: <text>\n___\n<command>` to non-auto-approved commands instead of the legacy `# ===== Description ===== #` box. The `___` divider renders as a Markdown horizontal rule on surfaces that parse Markdown and as a visible underscore line on plain-text surfaces, giving the dialog a clear visual break between the description and the command. Motivation: the four-line box rendered beautifully in the VS Code Claude Code extension and in the Claude Code terminal (where `\n` becomes a real newline) but rendered as unreadable escaped `\n` characters in the Claude Desktop app and on any other surface that displays the tool input as raw JSON. The new shape degrades gracefully on every surface: even on a raw-JSON surface the first readable token is still `# Description: <text>`, and the same text is mirrored to `updatedInput.description` (for surfaces that render the description field as the dialog subtitle) and, for PowerShell, to `permissionDecisionReason` (the v1.1.0 visible-body channel). Long descriptions are normalized to single-line and truncated to 120 chars with a trailing `...` for the inline prefix; the field-level `description` and `permissionDecisionReason` values carry the full normalized sentence so they wrap naturally in the dialog's own UI. The PowerShell hook continues to set `permissionDecision: "ask"` for non-allowed commands; that v1.1.0 safety guarantee is preserved verbatim. **Breaking for external tooling that grepped shell history for the literal `=====` box header**: such tools should switch to matching `^# Description:`. The hooks' `strip_description_box` function still removes the legacy 4-line box AND drops the new `___` separator line on retry, so commands formatted by the previous hook version (and the current version) round-trip cleanly during the transition. The previous public name `format_description_box` remains as a one-release-cycle alias for any external Python caller; it will be removed in the next minor release.
- **Hook helper rename**: `format_description_box(text, *, width=None)` becomes `format_description_prefix(text)` (no width argument; the prefix is always a single line). The alias `format_description_box = format_description_prefix` is kept for one release cycle.
- **`require-description.sh` and `require-powershell-description.sh` agent-facing blurbs** updated to show the new `# Description: <text>` example and to mention the 120-char single-sentence rule. The fallback regex that lets a description comment at the top of a command satisfy the "needs a description" check is now `^[[:space:]]*#.*\(desc:\|description\)`; the `desc:` alternative is kept so any session formatted with an intermediate `# desc:` shape still satisfies the check, but the canonical prefix the hooks emit is `# Description:`.
- **Unified shell-tool description rule across all five platform briefings.** `templates/ai-instructions/base-claude.md` previously carried two separate `MANDATORY` rules (one for Bash, one for PowerShell); both are replaced by a single unified rule that names every shell-style tool the platforms expose (Bash, PowerShell, `run_shell_command`, `shell`, etc.) and tells the agent: single plain-text sentence, <=120 chars, no newlines, no `#` characters. The same rule replaces the Bash-only `MANDATORY` in `templates/ai-instructions/base-codex.md` and `templates/ai-instructions/base-gemini.md`, and is **newly added** to `templates/ai-instructions/base-cursor.md` and `templates/ai-instructions/base-opencode.md` (those two templates previously carried no shell-tool description rule at all — this is new discipline for users on those platforms).

### Migration Impact

Users re-run the installer; the new hook scripts and the updated platform briefings land at their existing paths. No `settings.json` change, no schema change, no installer-flow change. The single behavioral change for Cursor / OpenCode users: their AI agent will now be reminded to provide a `description` parameter on every shell tool call (it previously had no rule and may have omitted descriptions). Mid-session retries on commands formatted with the legacy `# ===== Description ===== #` box still strip cleanly thanks to the `strip_description_box` regression test added in this release.

### Tests

- `catalog/hooks/tests/test_format_bash_description.py`: `TestFormatDescriptionBox` renamed to `TestFormatDescriptionPrefix` with assertions covering single-line shape, empty-input placeholder, internal-newline collapse, and >120-char truncation. `TestStripDescriptionBox` updated to use the new prefix shape in its round-trip tests; new `test_strips_legacy_box_format` and `test_strips_legacy_box_with_multiline_content` regression guards ensure mid-conversation retries on legacy-formatted commands still work. `TestMainIntegration` tests renamed (`..._prepends_box` -> `..._prepends_prefix`, `..._has_no_description_box` -> `..._has_no_description_prefix`, `..._has_box_not_double_wrapped` -> `..._has_prefix_not_double_wrapped`) with single-newline-count assertions added.
- `catalog/hooks/tests/test_format_powershell_description.py`: parallel updates to the bash test changes. `test_with_description_renders_box_and_asks` becomes `test_with_description_renders_prefix_and_asks` but the load-bearing `permissionDecision == "ask"` and `permissionDecisionReason == "Stops the Explorer process"` assertions are preserved verbatim — the v1.1.0 safety contract remains under test. Legacy-box strip regression test added in `TestStripDescriptionBox`.

---

## [1.2.0] - 2026-05-11

Phases 1, 2, 3, 4, 5, 6, and 7 of the v1.1.5 `adoption-skills` plan (`docs/v1.1.5/plans/adoption-skills.md`). Phase 1 shipped five doc-only edits that institutionalize patterns observed in upstream skill-authoring guidance. Phase 2 closes the A4 cleanup item (the `claude-api` row was already fully de-listed across all three `data/` registries before Phase 2 began, so A4 needed no code change beyond verifying state) and adds the new A9 `doc-coauthoring` workflow skill - a 3-stage co-authoring workflow (Context Gathering -> Refinement and Structure -> Reader Testing) for specs, proposals, decision docs, RFCs, ADRs, and long-form internal writeups. Phase 3 (A13) formalizes the per-skill bundled-resources convention: skill folders MAY ship `scripts/`, `references/`, and `assets/` subdirectories alongside `SKILL.md`, both installers' existing recursive-copy primitives auto-distribute them, and a new `--bundles-only` audit mode of `scripts/validate_skills.py` (wired into `make validate`) flags orphan files that the parent SKILL.md never references. Phase 4 ships four net-new content skills that all consume the Phase 3 layout convention - `generative-art` (specialized-domains), `theme-tokens` (specialized-domains), `internal-comms` (business-product), and `web-artifacts-builder` (developer-experience) - covering generative p5.js sketches with seeded randomness, ten brand-neutral curated theme JSONs, six structured internal-communication templates with worked examples, and a cross-platform Vite + React + TypeScript + Tailwind v4 + shadcn/ui scaffolder (init-artifact.sh + init-artifact.ps1 in lockstep per the v1.1.3 four-hook precedent). Phase 6 (A2 + A5) ships two more skills consuming the Phase 3 layout convention: `brand-styling` (specialized-domains) - a token-pattern skill that applies the user's own brand to generated artifacts via a per-brand `~/.devai-hub/brand/<slug>/tokens.json`, with EMPTY palette / fonts / logo placeholders and zero vendor assets per the company-neutral framing rule (the user MUST supply their own brand) - and `mcp-builder` (ai-development) - a skill that walks the agent through building a local MCP server in either Python (FastMCP) or Node / TypeScript (the official MCP SDK), with bundled cross-platform scaffolding scripts for both stacks (init-mcp-fastmcp.{sh,ps1} + init-mcp-ts.{sh,ps1}) and reference docs for the deeper API surfaces. The mcp-builder skill enforces the AGENTS.md MCP Registry Policy decision tree before scaffolding and documents settings.json registration across all 5 supported AI CLIs.

Phase 5 (A6 + A7) ships the `skill-eval-loop` workflow skill plus three repo-level dispatcher scripts (`aggregate_benchmark.py`, `skill_eval_viewer.py`, `optimize_skill_description.py`) that drive a closed-loop evaluation workflow against any skill in the catalog: paired with-skill / without-skill runs, assertion-graded outputs, browser-reviewed benchmarks, structured feedback capture, and a held-out-test description optimizer with a 60/40 train/test split. All three scripts are CLI-agnostic (claude / gemini / codex / opencode), follow the v1.1.3 four-hook precedent (single dispatcher with `--cli` flag, no cross-CLI fallback), and the parity invariant is enforced by a parametrized pytest. All edits land in tracked Markdown / JSON / Python files that the existing installer recursive-copy logic already distributes to all 5 supported AI-IDE platforms (Claude Code, Cursor, Codex, Gemini, OpenCode) on Windows, macOS, and Linux. No installer feature change, no version bump (per the user-supplied constraint that the version bump waits until Phase 7 of the plan).

Phase 7 (A16) ships the `.skill` archive packager: a new stdlib-only `scripts/package_skill.py` that validates a catalog skill's SKILL.md frontmatter (refusing to package if `name` or `description` are missing, or if `name` is not kebab-case) and emits a portable ZIP archive at `<skill-name>.skill` containing SKILL.md plus any per-skill bundled subdirectories (`scripts/`, `references/`, `assets/`, and any sibling subdirs like `themes/` / `templates/` / `examples/` / `agents/`). Round-trip-tested against the live `catalog/skills/workflow/skill-eval-loop/` bundle (8 files: SKILL.md + 4 references + 3 agents). Adds a delivery channel DevAI-Hub did not previously reach - Claude.ai and the Anthropic API skill-upload endpoint, which accept the `.skill` format upstream. Registered in BOTH `scripts/installer.sh` and `scripts/installer.ps1` per the AGENTS.md "Installer-Aware Changes" rule, modeled after the existing `generate_report.py` / eval-loop dispatcher precedents. Cross-platform parity verified via shellcheck-clean installer.sh, PowerShell-parser-clean installer.ps1, and a 14-test pytest module covering the happy path (minimal skill, archive validity, SKILL.md at root, bundled subdir round-trip, `.gitkeep` exclusion, default-output naming), the failure modes (missing SKILL.md, missing required frontmatter field, no frontmatter block, non-kebab-case name, missing skill directory), and the `--validate-only` mode. No version bump in this phase either - the cumulative v1.1.5 -> v1.2.0 bump happens via `/update-version` in `/wrap-up-session` after this phase closes.

### Changed

Skill-authoring guidance in AGENTS.md:

- **A14 - Pushy description guidance.** New "Description style: combat undertriggering" block under "Adding a New Skill -> Write SKILL.md". Documents that Claude under-triggers on narrow descriptions; the fix is a pushy description that lists trigger phrases AND skip phrases (`SKIP:` / `Do NOT use for:`) explicitly, covers synonyms and adjacent intents, and leads with the action then the trigger surface. Includes a before / after example contrasting "How to build a dashboard." (6 words, narrow) with the pushy form (60 words, explicit triggers + explicit skips).
- **A17 - Three-Tier Loading Model.** New `#### Three-Tier Loading Model` subsection under "Write SKILL.md". Documents the three tiers: tier 1 (always loaded) = `name` + `description` + `summary_l0` + `overview_l1`, ~150-300 tokens, determines triggering; tier 2 (on trigger) = SKILL.md body, target ≤500 lines; tier 3 (on demand) = bundled `scripts/`, `references/`, `assets/` per the A13 convention from Phase 3, with the critical affordance that scripts EXECUTE without their source being loaded into context. Includes practical authoring implications: push some-of-the-time content to references, push deterministic steps to scripts, keep tier 1 fields tight because they pay tokens on every catalog read across every session.
- **A15 - SKILL.md size norm reconciled.** "Keep SKILL.md under 800 lines." replaced with "Target ≤500 lines for the SKILL.md body. Soft cap 800 lines." Beyond 500 lines, add a `references/` subdirectory with a TOC and link to it. Beyond 800 lines, the skill MUST be split or refactored before merge. Existing skills that exceed 500 lines are explicitly grandfathered - the norm is forward-looking and applies to new and substantially-rewritten skills only.
- **A13 (Phase 3) - Per-skill Bundled Resources convention documented.** New `#### Per-skill Bundled Resources` subsection under "Adding a New Skill -> Write SKILL.md", placed immediately after the SKILL.md size norm. Documents the optional `scripts/`, `references/`, `assets/` subdirectories that any skill folder MAY ship alongside `SKILL.md`, with file-naming conventions (kebab-case, scoped by topic), the reference rule (every bundled file must be referenced from SKILL.md or another reference file in the same bundle, except `.gitkeep`), the installer behavior (both installers' existing recursive-copy primitives auto-distribute these subdirs without an installer edit), and the orphan-bundle detection now wired into `make validate`. Forward-references the v1.1.3 four-hook precedent for per-CLI parity invariants. Cross-link from the Three-Tier Loading Model fixed up to point at the new subsection (was a forward-reference to "the Per-skill Bundled Resources section that gets added in Phase 3"; now points at the actual section).

Installer documentation (Phase 3):

- **`scripts/installer.sh::safe_folder_copy`** gains a 6-line block comment above the function definition documenting that the existing `rsync -a --delete` / `cp -R` primitives already preserve per-skill bundled subdirectories (`scripts/`, `references/`, `assets/`). No code change in the body of the function -- the Phase 3 audit confirmed the recursive-copy primitives already handle the new convention correctly. Comment cross-references the AGENTS.md "Per-skill Bundled Resources" section so future installer maintainers see the contract.
- **`scripts/installer.ps1::Safe-Folder-Copy`** gains the same 8-line block comment above the function definition, in lockstep with `installer.sh`. Documents that `robocopy /MIR` mirrors arbitrary subdirectory depth and therefore picks up per-skill bundled subdirs automatically.
- **`Makefile::validate`** target gains an additional pass: after the JSON catalog loads, `make validate` now runs `python scripts/validate_skills.py --bundles-only`. The new flag scopes the validator to the orphan-bundle audit only, so existing pre-existing false-positive secret detections in the strict full-validator mode do not break CI. The full strict validator remains available via the unflagged `python scripts/validate_skills.py` invocation for manual deep audits.

Skill body edits:

- **A14 (cont.) - `catalog/skills/workflow/create-custom-command/SKILL.md`.** Adds a new "Description Style: Combat Undertriggering" section between "Step 5: Team-Wide Commands" and "Command Best Practices", with the same pushy-description rules (verbatim trigger phrases, `SKIP:` clauses, synonym coverage, action-then-trigger structure) and the same before / after example adapted for command descriptions. Adds a Common Rationalizations table (which the file did not previously have) with three rebuttals targeting the most common reasons authors leave descriptions narrow. Cross-links to the equivalent rule in AGENTS.md so skill authors and command authors see the same guidance from either entry point.
- **A11 - `catalog/skills/developer-experience/frontend-ui-engineering/SKILL.md`.** Adds an "Aesthetic Distinctiveness" section after "Step 7: Component Testing". Documents the AI-default aesthetic that production-grade UI must avoid (centered hero + three-card grid + gradient button + Inter typeface + uniform padding + 12px border-radius), six countermeasures (custom typography pairing, asymmetric layout, intentional density, distinctive accent color, motion that means something, copy with a voice), three reference patterns the agent can pick one of (editorial multi-column, brutalist over-borders, restrained motion), and a process step (write a one-page direction note up-front, not as a polish pass). Adds a Common Rationalizations row rebutting "the agent's default looks fine, we can polish later." Adds a Verification entry requiring the project to deviate from the AI-default in at least 2-3 dimensions.
- **A12 - `catalog/skills/developer-experience/creative-generation/SKILL.md`.** Adds a "Static Poster / Print Workflow" section after the existing "Ideation" section. Documents a deliberate two-step approach: step 1 writes a 30-80 line Markdown design philosophy fixing color palette, typography, composition principles, and 1-2 reference movements; step 2 renders the actual `.png` / `.pdf` output via `pptx-generation` / `docx-generation` / `pdf-document-generation` for standard formats or a single-purpose Pillow / matplotlib script for one-off bespoke layouts. Explicitly scopes p5.js / interactive-canvas outputs OUT (those belong to the `generative-art` skill being added in Phase 4 / A1). Adds a Common Rationalizations table (which the file did not previously have) with three rebuttals targeting the most common reasons authors skip the philosophy step.

### Added

New skills (Phase 2):

- **A9 - `catalog/skills/workflow/doc-coauthoring/SKILL.md`.** New 114-line workflow skill that drives a 3-stage co-authoring workflow for any non-trivial written artifact (specs, proposals, decision docs, RFCs, ADRs, technical memos, long-form internal writeups). Stage 1 - Context Gathering surfaces audience, purpose, prior art, and constraints in a single batched turn before any prose is written. Stage 2 - Refinement and Structure produces an outline first, then a draft against the accepted outline, with explicit checkpoints to detect drift from the Stage 1 Purpose. Stage 3 - Reader Testing simulates a fresh reader who has not seen the conversation, surfaces a gap list (unbacked claims / missing antecedents / lost-thread transitions) the user resolves or accepts. Frontmatter follows the v1.1.5 pushy-description rule from A14 (lists trigger phrases and a SKIP clause explicitly). Common Rationalizations table covers the six most common reasons agents skip stages (especially Stage 1 inference and Stage 3 omission). Verification section is binary and observable. Cross-links to `business-product/technical-writer`, `developer-experience/writing-editing`, `documentation/technical-documentation`, `business-product/internal-comms`, `developer-experience/idea-refine`, and `developer-experience/spec-driven-development`.

Registry updates (Phase 2):

- **`data/SKILL_INDEX.md`** gets a new `doc-coauthoring` row in the workflow category; total updated from 186 to 187.
- **`data/skills.json`** gets a new entry following the full schema (name, title, description, long_description, summary_l0, overview_l1, version=1.0.0, author, category=workflow, language=Multi-language, tags, priority=MEDIUM, based_on, tools_required, path, file, size, downloads, status=production, security 100/100/95). `statistics.total_skills` and `statistics.categories.workflow` incremented; `total_lines` and `total_tokens_estimate` adjusted for the new skill.
- **`data/marketplace.json`** workflow category `skill_count` incremented from 18 to 19.

Per-skill bundled-resources tooling (Phase 3 / A13):

- **`scripts/validate_skills.py` orphan-bundle audit.** New `validate_skill_bundles(skill_dir, skill_md_content)` function: walks a skill directory, lists every file under `scripts/`, `references/`, `assets/` (recursive), builds a haystack from SKILL.md plus every `references/*.md`, and emits a warning for each bundled file whose basename does not appear in the haystack. The exempt-filename set is `{".gitkeep"}` (placeholder for future-expansion subdirs). Warnings, not errors -- a work-in-progress branch can carry orphans without failing CI. New `--bundles-only` CLI flag scopes the validator to this audit only, skipping the full-strict-validator's frontmatter and secret-scan passes. Wired into `make validate` so the audit runs on every catalog change.
- **`catalog/hooks/tests/test_skill_bundles.py`.** New 8-test pytest module covering the orphan detector: orphan-in-scripts is warned, referenced file is silent, `.gitkeep` is exempt, reference-from-another-reference satisfies the audit, mix of orphan and referenced reports only the orphan, orphan in nested `assets/<subdir>/` is detected, skills with no bundled subdirs return empty, and `python scripts/validate_skills.py --bundles-only` exits clean against the real catalog (subprocess test). Follows the importlib-based loader pattern from `test_format_bash_description.py` because `validate_skills.py` is a top-level script (no package).
- **`catalog/skills/workflow/doc-coauthoring/scripts/.gitkeep`.** Sentinel placeholder proving the per-skill bundled-resources convention survives an installer copy. Round-trip-tested on Windows via both `cp -R catalog/skills <tmp>` (Git Bash, exercises the same primitive `installer.sh` runs on Linux/macOS) and `robocopy catalog\skills <tmp> /MIR` (PowerShell, exercises `installer.ps1`'s primitive). Both copy mechanisms preserved the `.gitkeep` at `<tmp>/skills/workflow/doc-coauthoring/scripts/.gitkeep`. SKILL.md gained a brief "Bundled Resources" trailer explaining the directory's role; this also satisfies the orphan-audit reference rule (the `scripts/` reference + the `.gitkeep` exemption combined keep the audit silent for this skill).

New skills (Phase 4):

- **A1 - `catalog/skills/specialized-domains/generative-art/SKILL.md`.** New 130-line skill that produces algorithmic / generative-art artifacts through a strict two-step process: Step 1 writes a 30-80 line Markdown philosophy manifesto fixing movement reference (suprematism, op-art, Vera Molnar, Casey Reas, James Paterson), underlying principle (flow, swarm, growth), color and density behavior, motion behavior, parameter surface, and an explicit "what this is NOT" negative-space declaration; Step 2 ships a p5.js sketch with `randomSeed()` + `noiseSeed()` for deterministic re-rolls and an HTML viewer with native `<input type="range">` sliders mapped to the manifesto's parameter surface. Three starter templates ship under `assets/`: `flow-field.html` (curl-noise traced particles), `particle-system.html` (force-directed swarm with mouse target), `l-system.html` (recursive grammar branching with seeded jitter). Each template is self-contained (single HTML file with embedded p5 + sliders + sketch, p5 from CDN, no build step). Frontmatter follows the v1.1.5 pushy-description rule from A14 (verbatim trigger phrases + `SKIP:` clause). Cross-links to `creative-generation`, `glsl-shader-development`, `brand-styling`, `ui-component-generation`, `gif-sticker-maker`.
- **A3 - `catalog/skills/specialized-domains/theme-tokens/SKILL.md`.** New 175-line skill providing a stable token schema (palette: 6 slots, fonts: 3 slots, spacing: base + scale, radius, shadow) plus 10 brand-neutral curated theme JSON files under `themes/`: `editorial-serif`, `brutalist-sans`, `pastel-soft`, `terminal-mono`, `corporate-slate`, `sunset-warm`, `forest-cool`, `mid-century-modern`, `neon-cyber`, `newsprint-mono`. Each theme parses as valid JSON with `#rrggbb` palette values, real CSS font stacks (no synthetic typeface names), an explicit spacing scale tuned to the theme's density character, and an explicit `radius` + `shadow` value (or `"none"`). Documents how downstream generators (`pptx-generation`, `docx-generation`, `pdf-document-generation`, `web-artifacts-builder`, `generative-art`) map the tokens to their underlying engines. The bundled set is closed - user-supplied themes route through `brand-styling` instead of extending this skill's `themes/` folder. Common Rationalizations table rebuts the four most likely drift modes (slot expansion, fourth font, vendor-palette adoption, hardcoded spacing).
- **A8 - `catalog/skills/business-product/internal-comms/SKILL.md`.** New 240-line skill providing six named templates for internal-audience writing: 3P Update (Progress / Plans / Problems), Weekly Status Report, Leadership Update (executive briefing), Company FAQ entry, Incident Report (Summary + Impact + Timeline + Root Cause + What Went Well/Wrong + Action Items table), Project Update (one-pager with Status: On track / At risk / Off track + Risks + Asks). Each template documents when to use it, the exact section headers, expected length range, and 3-5 common pitfalls. Six worked examples ship under `examples/` using placeholder organizations (Project Aurora, Team Phoenix, Apex Logistics) so the patterns are reusable without modeling on a real company. Cross-links to `developer-experience/writing-editing`, `business-product/technical-writer`, `workflow/doc-coauthoring`, `documentation/technical-documentation`, `developer-experience/idea-refine`.
- **A10 - `catalog/skills/developer-experience/web-artifacts-builder/SKILL.md`.** New 145-line skill scaffolding multi-component HTML artifacts using the Vite + React + TypeScript (strict) + Tailwind v4 + shadcn/ui stack. Two parallel init scripts ship under `scripts/`: `init-artifact.sh` (bash, `set -euo pipefail`, runs `npm create vite@latest`, installs `@tailwindcss/vite`, wires the v4 plugin into `vite.config.ts`, replaces `src/App.css` with `@import "tailwindcss";` plus an empty `@theme { ... }` block, runs `shadcn init`, trims demo content) and `init-artifact.ps1` (PowerShell, `$ErrorActionPreference = 'Stop'`, same output). Both scripts gracefully fail with a clear install hint when `node` / `npm` is missing. The pair follows the v1.1.3 four-hook precedent: each script is self-contained, neither cross-references the other, and both produce byte-identical project layouts. Cross-platform installer parity confirmed via `bash -n init-artifact.sh` (clean) and PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile` clean).

Registry updates (Phase 4):

- **`data/SKILL_INDEX.md`** gets four new rows (`generative-art`, `theme-tokens`, `internal-comms`, `web-artifacts-builder`); total updated from 187 to 191.
- **`data/skills.json`** gets four new entries following the full schema; `statistics.total_skills` updated from 189 to 193 (the 187 visible total + 4 = 191 user-facing skills, plus 2 categorical alias rows that already counted toward the canonical 193 statistics figure); `statistics.categories.specialized-domains` 9 -> 11, `statistics.categories.business-product` 4 -> 5, `statistics.categories.developer-experience` 22 -> 23.
- **`data/marketplace.json`** category descriptions updated and `skill_count` incremented: `specialized-domains` 9 -> 11, `business-product` 4 -> 5, `developer-experience` 25 -> 26.

New skill (Phase 5):

- **A6 + A7 - `catalog/skills/workflow/skill-eval-loop/SKILL.md`.** New ~200-line workflow skill that drives a closed-loop evaluation workflow for any DevAI-Hub skill. Each iteration writes 2-3 realistic test prompts to `evals/evals.json`, spawns paired runs (with-skill vs baseline) into `<workspace>/iteration-N/eval-XXX/{with_skill,without_skill}/`, captures `total_tokens` + `duration_ms` per run, grades each output against per-eval assertions (`text` / `passed` / `evidence` schema), aggregates a benchmark, presents the runs side-by-side in a browser viewer, collects structured feedback, and feeds the next iteration via five named improvement heuristics (pushy descriptions, explain-the-why, repeated-work elimination, negative-space coverage, assertion calibration). Frontmatter follows the v1.1.5 pushy-description rule from A14 (verbatim trigger phrases + `SKIP:` clause). Cross-links to `developer-experience/ai-output-evaluation`, `workflow/create-custom-command`, `developer-experience/prompt-engineering`, `orchestration/multi-agent-coordinator`, `tests-generation/code-coverage`, and `workflow/known-gaps-tracker`.
- **Per-skill bundled `references/`** (4 files, all referenced from SKILL.md per the A13 audit): `schemas.md` (JSON schemas for evals.json, run_metadata.json, grading.json, benchmark.json, feedback.json, optimizer result), `improvement-heuristics.md` (the five heuristics applied at step 9 of the loop, with priority order H1 -> H4 -> H2 -> H5 -> H3), `cli-adapter.md` (option-A vs option-B design rationale, per-CLI invocation patterns for claude / gemini / codex / opencode, parity-test specification), `description-optimizer.md` (60/40 train-test split rationale, candidate-generation prompt template, held-out-test selection rule).
- **Per-skill bundled `agents/`** (3 sub-agent prompt files - the directory is sibling to `references/`, intentionally outside the A13 orphan-audit scope which is `scripts/` / `references/` / `assets/`): `grader.md` (evaluates assertions against a run's outputs and writes `grading.json` with `text` / `passed` / `evidence`), `comparator.md` (blind A/B comparison without knowing which run had the skill loaded; output verdict alphabet `A_better` / `B_better` / `tie`), `analyzer.md` (reads `benchmark.json` and surfaces non-discriminating assertions, high-variance evals, time/token trade-offs into `analysis.md`).

Eval-loop dispatcher scripts (Phase 5):

- **`scripts/aggregate_benchmark.py`.** Stdlib-only Python 3.10+ aggregator that walks `<workspace>/iteration-N/` and emits `benchmark.json` (per-eval pass_rate / duration_ms_mean / duration_ms_stddev / tokens_mean / tokens_stddev plus `with_skill_vs_baseline_delta` for each metric, plus an `overall` block) and `benchmark.md` (the same data as a Markdown table for human review). Pure post-processing - no CLI invocation. Schema documented at `catalog/skills/workflow/skill-eval-loop/references/schemas.md`. Registered in BOTH `scripts/installer.sh` (line ~1424) AND `scripts/installer.ps1` (line ~1735) per the AGENTS.md "Installer-Aware Changes" rule, modeled after the existing `generate_report.py` block; lockstep dual entries.
- **`scripts/skill_eval_viewer.py`.** Stdlib-only Python 3.10+ browser viewer with two modes: server (default - starts `http.server` on a random port, opens the user's browser via `webbrowser.open()`, accepts `POST /submit-feedback` that writes `<workspace>/iteration-N/feedback.json`) and static (`--static <path>` - writes a self-contained HTML file whose "Submit All Reviews" button downloads `feedback.json` as a JS Blob; designed for headless / CI environments). Two-tab UI: "Outputs" (per-eval, with_skill vs without_skill side-by-side, with assertion-grading badges and free-form feedback textareas) and "Benchmark" (the `benchmark.json` table). No external deps; jinja-style templating done with `str.format`. Registered in BOTH installers in lockstep with `aggregate_benchmark.py`.
- **`scripts/optimize_skill_description.py`.** Description optimizer with the 60/40 train-test split (deterministic via `--seed`, default 42). For each iteration: estimates trigger rate on train and test under the current description, asks the chosen CLI to PROPOSE 3 candidate description rewrites based on which train queries failed, evaluates each candidate on train AND test, selects `best_description` by **held-out test score** (NOT train) - the rule that prevents overfitting to the candidate-generation prompt. Selection ties broken by `train_trigger_rate`, then by description length (shorter wins per the AGENTS.md three-tier loading model). `--dry-run` prints the train/test split, the baseline description, and the candidate-generation prompt template, then exits 0 without invoking any CLI. CLI dispatch follows the v1.1.3 four-hook precedent: `assert cli in {"claude", "gemini", "codex", "opencode"}` at the top of `invoke_cli()`, four parallel `if cli == "X":` branches, no cross-CLI fallback. Registered in BOTH installers.

CLI-adapter parity test (Phase 5):

- **`catalog/hooks/tests/test_eval_loop.py`.** New 14-test pytest module covering three things: (1) the CLI-adapter parity invariant - parametrized over (`optimize_skill_description.py`, each of the four supported CLIs), reads the dispatcher source, isolates each `if cli == "X":` branch by indent-anchored line scanning, and asserts no other CLI binary appears in argv-list form within that branch (modeled on `test_diff_review_hooks.py::TestPlatformIndependence`); (2) the optimizer dry-run schema - asserts `--dry-run` returns 0, emits the declared shape (`mode` / `cli` / `selection_metric` / `n_train` / `n_test` / `split` / `baseline_description` / `candidate_generation_prompt_template_preview`), the split is deterministic under a fixed `--seed`, and the optimizer does NOT invoke any CLI when `--dry-run` is passed (verified by running with `PATH` pointing at an empty directory); (3) the aggregator + viewer end-to-end smoke - builds a fixture iteration directory with one eval, paired runs, and grading.json, runs `aggregate_benchmark.py`, asserts `benchmark.json` has `with_skill_pass_rate=1.0` / `without_skill_pass_rate=0.0` / `pass_rate_delta=1.0`, then runs `skill_eval_viewer.py --static review.html` and asserts the HTML body contains `eval-001`, `with_skill`, `without_skill`, and `submitFeedback`.

Registry updates (Phase 5):

- **`data/SKILL_INDEX.md`** gets a new `skill-eval-loop` row in the workflow category; total updated from 191 to 192.
- **`data/skills.json`** gets a new entry following the full schema (name, title, description, long_description, summary_l0, overview_l1, version=1.0.0, author, category=workflow, language=Python, tags, priority=MEDIUM, based_on, tools_required, path, file, size, downloads=0, status=production, security 100/100/95). `statistics.total_skills` incremented from 193 to 194; `statistics.categories.workflow` incremented from 18 to 19.
- **`data/marketplace.json`** workflow category description updated to mention "skill evaluation"; `skill_count` incremented from 19 to 20.
- **`.gitignore`** gets a new `*-workspace/` entry to ignore user-generated eval workspaces (the loop creates `<skill-name>-workspace/` directories at the repo root with per-iteration outputs, benchmarks, and feedback that should not leak into commits).

New skills (Phase 6):

- **A2 - `catalog/skills/specialized-domains/brand-styling/SKILL.md`.** New 180-line skill that applies user-supplied brand tokens (palette, typography, logo, voice) to generated artifacts (decks, docs, PDFs, web, internal-comms). Extends the Phase 4 / A3 `theme-tokens` schema with brand-specific extensions: `logo` (primary / secondary / wordmark / `min_height_px` / `clear_space_factor`), `voice` (tone + do / dont rules), and `assets_dir` for self-hosted fonts / icons. Brands live entirely under `~/.devai-hub/brand/<slug>/{tokens.json, fonts/, logo.{svg,png}}`. Frontmatter follows the v1.1.5 pushy-description rule (verbatim trigger phrases + explicit `SKIP:` clause for brand-neutral, vendor-specific, and one-off-styling cases). The skill is opinionated about TWO failure modes: (1) the agent inventing brand decisions ("a professional navy and gray") - rebutted with explicit instructions to ALWAYS ask the user for tokens before picking colors and to OFFER a default scaffold if the user has none yet; (2) silent defaults masking missing brand data - rebutted with a fail-loudly rule for missing required fields. Common Rationalizations table covers seven common drift modes (vendor-palette substitution, screenshot-as-brand-source, voice skipping, inline-only persistence, single-logo lock-in, silent defaults). Bundled `templates/tokens.template.json` ships with all required keys present but every value empty / null / empty-string - the user copies this into their brand directory and fills the values. Cross-links to `theme-tokens` (the brand-neutral counterpart), `pptx-generation`, `docx-generation`, `pdf-document-generation`, `web-artifacts-builder`, `internal-comms`, `writing-editing`, `technical-writer`. Ships ZERO vendor-specific colors / fonts / logos / identifiers (verified via `git grep -i 'anthropic\|openai\|tailwind.*palette\|material.*color\|google.*brand'` against the skill folder - no hits) per the company-neutral framing rule and the AGENTS.md reverse-engineering attribution rule.
- **A5 - `catalog/skills/ai-development/mcp-builder/SKILL.md`.** New 242-line skill that walks the agent through building a local MCP (Model Context Protocol) server in either Python (FastMCP) or Node / TypeScript (the official `@modelcontextprotocol/sdk`), then registering the server across all five DevAI-Hub-supported AI CLIs (Claude Code, Cursor, Codex, Gemini / Antigravity, OpenCode) via each CLI's settings.json. The skill is opinionated about Step 0: BEFORE scaffolding any server, walk the AGENTS.md MCP Registry Policy decision tree with the user - many requests for "an MCP" are better served by a skill (LLM-native, zero infrastructure), and the skill explicitly cross-links the policy from its body. The "When to build vs. skill vs. hook" comparison table makes the decision tree concrete: skill when LLM-native, hook when one-shot lifecycle event, MCP when deterministic capability returning structured data the LLM cannot reliably do. Step 6 documents the settings.json registration shape across all five CLIs (Claude `~/.claude/settings.json`, Cursor `~/.cursor/mcp.json`, Codex `~/.codex/config.json`, Gemini `~/.gemini/mcp.json`, OpenCode `~/.config/opencode/mcp.json`) - the entry shape is identical (the MCP protocol is the contract); only the file path varies. Common Rationalizations table covers eight common drift modes (search-as-service wrappers, MCP-when-skill-suffices, Python-by-default, Step-0 skipping, HTTP-by-default, auth deferral, single-CLI registration, terse tool descriptions). Cross-links to `developer-experience/tool-design`, `workflow/create-skill-or-command`, `ai-development/ai-agent-development`, `ai-development/claude-agent-sdk`, `architecture/api-design`, `language-specialists/python-expert`, `language-specialists/typescript-expert`.
- **Per-skill bundled `references/`** (2 files, both referenced from SKILL.md per the A13 audit): `fastmcp.md` (deeper FastMCP API surface - install, minimal server, tool definitions with Pydantic, transports, auth for HTTP / SSE, resources and prompts, testing patterns, common pitfalls, going-beyond-the-scaffold guidance), `ts-sdk.md` (deeper TS SDK API surface - same topics for Node / TypeScript with Zod schemas).
- **Per-skill bundled `scripts/`** (4 files in two parallel pairs, all referenced from SKILL.md per the A13 audit and following the v1.1.3 four-hook precedent): `init-mcp-fastmcp.sh` + `init-mcp-fastmcp.ps1` (scaffold a FastMCP Python server: verify Python 3.10+, create `<name>/` directory, write `pyproject.toml` with `mcp[cli]>=1.0.0` + `pydantic>=2.0.0` deps, write `server.py` with one example `@mcp.tool()`-decorated `echo` function returning a `Pydantic BaseModel`, write `.gitignore`, create venv at `.venv/`, install dependencies into the venv, print next-step instructions); `init-mcp-ts.sh` + `init-mcp-ts.ps1` (scaffold a TypeScript MCP server: verify Node 20+, `npm init`, install `@modelcontextprotocol/sdk` + `zod` + `tsx` + `typescript` + `@types/node`, write ESM-native `package.json` with `dev` / `build` / `start` scripts, write `tsconfig.json` targeting ES2022 / ESNext / Bundler resolution, write `src/server.ts` with one example `server.tool()` registration using a Zod schema and stdio transport, write `.gitignore`, run `npm install`, print next-step instructions). Each `.sh` and its `.ps1` sibling produce equivalent scaffolds; neither cross-references the other. Both bash scripts are `set -euo pipefail`-compliant and use the standard `log_info` / `log_warn` / `log_error` helpers per the project's bash safety rules. Both PowerShell scripts use `$ErrorActionPreference = 'Stop'` and follow the v1.1.0+ PowerShell-tool conventions. ShellCheck (`--severity=warning`) clean on both `.sh` files; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on both `.ps1` files.

Registry updates (Phase 6):

- **`data/SKILL_INDEX.md`** gets two new rows (`brand-styling` in specialized-domains, `mcp-builder` in ai-development); total updated from 192 to 194.
- **`data/skills.json`** gets two new entries following the full schema; `statistics.total_skills` 194 -> 196; `statistics.categories.specialized-domains` 11 -> 12; `statistics.categories.ai-development` 8 -> 9.
- **`data/marketplace.json`** category descriptions updated and `skill_count` incremented: `specialized-domains` 11 -> 12 (description appends "brand styling"), `ai-development` 8 -> 9 (description appends "build MCP servers").

Skill packager (Phase 7 / A16):

- **`scripts/package_skill.py`.** New stdlib-only Python 3.10+ script that packages a `catalog/skills/<cat>/<name>/` directory into a portable `.skill` ZIP archive. The archive root contains SKILL.md plus any per-skill bundled subdirectories (`scripts/`, `references/`, `assets/`, and any sibling subdirs like `themes/` / `templates/` / `examples/` / `agents/` that ship alongside SKILL.md) at their original relative paths, so `unzip <name>.skill -d <dest>` reproduces a fresh skill folder. Validates SKILL.md frontmatter before packaging: `name` and `description` are required (refused with exit code 1 if missing); `summary_l0` and `overview_l1` are recommended (informational note only); `name` must be kebab-case (lowercase letters, digits, hyphens). Excludes housekeeping artifacts (`.DS_Store`, `__pycache__`, Windows tilde-prefixed lock files, `.gitkeep` placeholders) so the archive is clean for upstream consumers. `--validate-only` mode validates frontmatter without writing the archive. `--output <path>` overrides the default `./<skill-name>.skill` location. Frontmatter parser mirrors `scripts/validate_skills.py` so behavior is aligned without a YAML library dependency. Schema and rationale: this is Phase 7 / A16 of `docs/v1.1.5/plans/adoption-skills.md`; the `.skill` format is the consumer-side input shape for Claude.ai and the Anthropic API skill-upload endpoint - delivery channels DevAI-Hub did not previously reach. Registered in BOTH `scripts/installer.sh` (in lockstep with the eval-loop dispatcher block) AND `scripts/installer.ps1` (matching `Safe-Copy` block) per the AGENTS.md "Installer-Aware Changes" rule.
- **`catalog/hooks/tests/test_package_skill.py`.** New 14-test pytest module: 5 happy-path tests (packages minimal skill, archive is a valid ZIP, SKILL.md at archive root, bundled subdirectories - `scripts/` + `references/` + `assets/` + sibling `themes/` - all survive the round-trip, `.gitkeep` files excluded from the archive, default output path uses the frontmatter `name`), 5 validation-failure tests (missing SKILL.md raises SystemExit(1), missing required frontmatter field raises, no frontmatter block raises, non-kebab-case `name` raises, missing skill directory raises), 2 `--validate-only` tests (does not write archive on success, still fails on invalid frontmatter), and 2 CLI entry-point tests (`main()` packages on success, `main()` honours `--validate-only`). Follows the importlib-based loader pattern from `test_skill_bundles.py` because `package_skill.py` is a top-level script (no package).

### Removed

Phase 2 cleanup (A4):

- **`claude-api` skill index drift resolved.** The comparison report (`docs/v1.1.5/comparison-skills.md` Section 5a A4) flagged the `claude-api` row as present in all three `data/` registry files while the file `catalog/skills/ai-development/claude-api/SKILL.md` did not exist. State at the start of Phase 2 was that the row had already been removed from `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` between the comparison report and Phase 2 - the de-list path (option C in the plan's 2.1 question) was effectively already executed. Verified consistency: zero matches for `claude-api` in any `data/` file; no orphan rows. No code change required for A4 beyond this confirmation; recorded in the Phase 2 known-gaps DF entry for traceability.

### Verified

Cross-platform installer parity (Phase 2):

- **Both installers' recursive-copy logic auto-distributes the new skill** without requiring an installer edit. `scripts/installer.sh::safe_folder_copy` uses `rsync -a --delete` (or `cp -R "$source/"*` fallback) on `catalog/skills/`; `scripts/installer.ps1::Safe-Folder-Copy` uses `robocopy ... /MIR`. Both primitives are recursive and pick up new skill folders automatically.
- **All 5 platform templates pick up the new SKILL_INDEX row at install time.** `templates/ai-instructions/base-{claude,cursor,codex,gemini,opencode}.md` and `generic-instructions.md` each contain a `{{SKILL_INDEX}}` placeholder that the installer substitutes from `data/SKILL_INDEX.md`. Updating the index file once distributes the new row to all 5 supported IDEs.
- **`bash -n scripts/installer.sh`** clean; ShellCheck clean against `scripts/installer.sh` and `install.sh`.

Per-skill bundled-resources convention (Phase 3 / A13):

- **Round-trip smoke test on both copy primitives.** `cp -R catalog/skills <tmp>` (Git Bash on Windows, equivalent to the `installer.sh` Linux/macOS path) preserves `doc-coauthoring/scripts/.gitkeep` at `<tmp>/skills/workflow/doc-coauthoring/scripts/.gitkeep`. `robocopy catalog\skills <tmp> /MIR` (PowerShell, the exact primitive `installer.ps1` invokes via `Safe-Folder-Copy`) preserves the same path under `<tmp>\skills\workflow\doc-coauthoring\scripts\.gitkeep`. Both confirmed in this session.
- **Orphan-bundle audit on the live catalog.** `python scripts/validate_skills.py --bundles-only` against the 193-skill catalog: 0 errors, 4 warnings (4 pre-existing orphan files in 3 framework-specialist skills - `fastapi-expert`, `nextjs-expert`, `react-expert`; tracked in `docs/v1.1.5/known-gaps.md` as WN-001). Warnings do not gate CI. Verbose mode prints the orphan paths for triage.

Cross-platform installer parity (Phase 5):

- **All three new dispatcher scripts registered in lockstep** in `scripts/installer.sh` (Bash `safe_copy` block at line ~1424) AND `scripts/installer.ps1` (PowerShell `Safe-Copy` block at line ~1735). Both blocks copy `aggregate_benchmark.py`, `skill_eval_viewer.py`, and `optimize_skill_description.py` to `~/.devai-hub/scripts/` (POSIX) or `$env:USERPROFILE\.devai-hub\scripts\` (Windows), modeled after the existing `generate_report.py` and `devai_mcp_benchmark.py` precedents.
- **Syntax validation clean.** `bash -n scripts/installer.sh` clean; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on `installer.ps1`; ShellCheck (`--severity=warning`) clean on both `scripts/installer.sh` and `install.sh`.
- **Per-skill recursive copy reaches the new bundle.** The `catalog/skills/workflow/skill-eval-loop/` folder (with `references/` and `agents/` subdirs) is auto-distributed by the existing `safe_folder_copy` / `Safe-Folder-Copy` primitives that already pick up Phase 4's bundled subdirs - no installer edit was needed for the skill folder itself, only for the three repo-level scripts.
- **CLI parity invariant enforced via pytest.** `catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter` is parametrized over `(optimize_skill_description.py, claude|gemini|codex|opencode)` and asserts every `if cli == "X":` branch invokes ONLY its matching CLI - no cross-CLI bleed possible. Test methodology mirrors the v1.1.3 `test_diff_review_hooks.py::TestPlatformIndependence` source-inspection pattern.

Cross-platform installer parity (Phase 7):

- **`scripts/package_skill.py` registered in BOTH installers in lockstep.** `scripts/installer.sh` gains a `safe_copy` block immediately after the eval-loop dispatcher trio (after the `optimize_skill_description.py` copy); `scripts/installer.ps1` gains the matching `Safe-Copy` block at the same logical position. Both blocks copy to `~/.devai-hub/scripts/package_skill.py` (POSIX) or `$env:USERPROFILE\.devai-hub\scripts\package_skill.py` (Windows). Modeled after the existing `generate_report.py` + eval-loop dispatcher precedents.
- **Syntax validation clean.** `bash -n scripts/installer.sh` clean; ShellCheck (`--severity=warning`) clean on `scripts/installer.sh` and `install.sh`; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on `installer.ps1`; `python -m py_compile scripts/package_skill.py` clean.
- **Round-trip pack-and-extract verified against a real skill bundle.** `python scripts/package_skill.py catalog/skills/workflow/skill-eval-loop --output <tmp>.skill` produced an 8-file archive; `zipfile.ZipFile(<tmp>.skill).namelist()` confirmed SKILL.md at the archive root plus all 3 `agents/*.md` files and all 4 `references/*.md` files preserved at their original relative paths. The Phase 5 skill bundle survives the round-trip in its entirety.
- **JSON catalogs valid (Phase 7).** `data/skills.json` (196 skills), `data/bundles.json` (11 bundles), `data/workflows.json` (17 workflows), `data/templates.json`, `data/marketplace.json` all parse cleanly with UTF-8 encoding; total skill count unchanged from Phase 6 close (the packager is a repo-level script, not a new skill).

Cross-platform installer parity (Phase 6):

- **Both new skills' bundled subdirectories ride the existing recursive-copy primitives** (`safe_folder_copy` in `installer.sh`, `Safe-Folder-Copy` in `installer.ps1`) confirmed in Phase 3 to handle per-skill `scripts/`, `references/`, and `templates/` subdirs. No installer edit was required for either skill: `catalog/skills/specialized-domains/brand-styling/templates/tokens.template.json`, `catalog/skills/ai-development/mcp-builder/references/{fastmcp,ts-sdk}.md`, and `catalog/skills/ai-development/mcp-builder/scripts/{init-mcp-fastmcp,init-mcp-ts}.{sh,ps1}` all auto-distribute to `~/.claude/skills/`, `~/.gemini/skills/`, and `~/.codex/skills/` (the three per-file-tree platforms) plus the `{{SKILL_INDEX}}` block in the Cursor / OpenCode / Copilot instruction templates picks up the two new SKILL_INDEX rows.
- **No vendor-specific assets in either bundle.** `git grep -i 'anthropic\|openai\|tailwind.*palette\|material.*color\|google.*brand'` against `catalog/skills/specialized-domains/brand-styling/` and `catalog/skills/ai-development/mcp-builder/` returns no hits. `brand-styling/templates/tokens.template.json` ships with all required keys present but every value empty / null / empty-string. `mcp-builder` references the AGENTS.md MCP Registry Policy throughout but does not embed the policy text - it cross-links to the canonical source.
- **Bundle audit clean for both new skills.** `python scripts/validate_skills.py --bundles-only` against the 196-skill catalog: 0 errors, 4 pre-existing warnings (unchanged from Phase 5; all in framework-specialist skills tracked as WN-001). Both new skills pass the orphan check - every file under their bundled subdirs is referenced from SKILL.md.
- **Syntax validation clean.** `bash -n` clean on both new `.sh` scripts; ShellCheck (`--severity=warning`) clean on both; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on both new `.ps1` scripts.
- **JSON catalogs valid.** `data/skills.json`, `data/bundles.json`, `data/workflows.json`, `data/templates.json`, `data/marketplace.json` all parse cleanly with UTF-8 encoding; total skill count 196.

### Tests

- All four test suites passing across Phases 1, 2, 3, 4, 5, 6, and 7: 37 (devai-skill-server) + 36 (devai-code-search, 1 skipped) + 23 (devai-web-fetch) + 346 (catalog/hooks/tests, up from 332 at Phase 6 close - the new `test_package_skill.py` module adds 14 cases) = 442 passed, 1 skipped, 0 failures. Phase 7 adds the new packager pytest module covering happy path / validation failures / `--validate-only` / CLI entry-point. Pre-existing tests remain green. ShellCheck clean against `scripts/installer.sh` and `install.sh`; ShellCheck clean against the two Phase 6 bundled `.sh` scaffolders. PowerShell parser clean on `installer.ps1` AND on both Phase 6 `.ps1` scaffolders. `python -m py_compile scripts/package_skill.py` clean. JSON catalogs valid: 196 skills, 11 bundles, 17 workflows, templates and marketplace OK. `make validate`-equivalent pass via per-skill bundled-resources orphan audit (200 skills scanned, 0 errors, 4 pre-existing warnings carried forward from Phase 3 / WN-001 - all in framework-specialist skills that pre-date the convention).

### Known gaps

- See `docs/v1.1.5/known-gaps.md` for the cumulative gap log. As of Phase 7 close: 11 open items, 0 resolved this version. Phase 7 added DF-008 extending the cumulative cross-OS verification queue (DF-003 / DF-005 / DF-006 / DF-007) to cover the new `scripts/package_skill.py` installer registration - the script itself is stdlib-only Python so the runtime risk surface is minimal, but a real `bash scripts/installer.sh` execution on macOS / Linux to confirm the new copy line lands at `~/.devai-hub/scripts/package_skill.py` was not run in this session. As of Phase 6 close: 10 open items, 0 resolved this version. Phase 1 surfaced one DEVIATION (the plan referenced `catalog/skills/workflow/create-skill-or-command/SKILL.md` for sub-task 1.1, but only `create-custom-command` exists in the catalog - skill-creation guidance for skills lives in AGENTS.md "Adding a New Skill", not in a dedicated catalog skill; A14 was applied to both `create-custom-command/SKILL.md` and the equivalent AGENTS.md location, achieving the original intent without inventing a new skill file). Phase 2 surfaced one DEVIATION (A4's plan-described starting state - claude-api row present across all three registries - did not match the actual repo state at Phase 2 start; the row was already absent everywhere, so the de-list work was a no-op verification rather than an edit). Phase 2 also accepted one cross-OS coverage gap: cross-platform installer parity verification was performed on Windows / Git Bash only (the work-environment constraint); macOS / Linux real-install verification is deferred. Phase 3 added two further DEFERRED items: DF-004 (the Phase 3 plan's optional `--dry-run` flag suggestion was assessed out of scope - adding a real dry-run mode to two ~1700-line installers is a substantive refactor, and the smoke test was performed by direct invocation of the recursive-copy primitives instead) and WN-001 (the new `--bundles-only` audit detected 4 pre-existing orphan reference files in three framework-specialist skills - `fastapi-expert`, `nextjs-expert`, `react-expert` - which pre-date the convention and are out of Phase 3's layout-only scope; the recommended fix is a small `## References` block in each affected SKILL.md, scheduled for a future patch). Phase 4 added DF-005 extending DF-003 to cover the cross-OS verification gap for the four Phase 4 skill bundles. Phase 5 added DF-006 extending DF-003 / DF-005 to cover the three new repo-level scripts (real `bash scripts/installer.sh` execution on a real macOS / Linux host is the cumulative deferred item; the recommended fix is a CI matrix step before the v1.1.5 -> v1.2.0 version bump in Phase 7) and MT-001 (the optimizer's `run_iteration()` function lacks a "stub CLI binary on PATH" smoke test analogous to the v1.1.3 hooks; covered indirectly via the parity test + dry-run schema test, but a direct integration test would be stronger - out of scope for v1.1.5 if Phase 7 ships first). Phase 6 added DF-007 (the four new mcp-builder bundled scaffolding scripts -- `init-mcp-fastmcp.{sh,ps1}` and `init-mcp-ts.{sh,ps1}` -- have not been executed end-to-end against a real Python 3.10+ / Node 20+ host to scaffold a working server; only static syntax validation was performed in this session; the recommended fix is a CI matrix step that runs each scaffolder against a clean fixture directory and verifies the generated server starts under `mcp dev` / `npm run dev` without errors).

---

## [1.1.5] - 2026-05-06

Patch release. Adds an explicit **sectioned-bullet structure** rule to every command and workflow that generates commit messages, so multi-component commits stop coming out as long flowing paragraphs separated by blank lines. Reported live against a v1.1.4-generated commit message - the v1.1.4 fix had stopped hard-wrapping at the column level but did nothing about the flowing-paragraph shape, which still forces reviewers to read every paragraph linearly to find a specific component. Five files patched in lockstep with consistent wording. Safe to upgrade from v1.1.4; no migration steps. Restart any running AI-agent sessions after re-installing so the patched command bodies take effect.

### Changed

- **`catalog/commands/generate-commit-message.md` body rules expanded.** Adds a "Body structure (CRITICAL for non-trivial commits)" rule that requires labeled sections with bullets after the subject line and a 1-2 sentence intro paragraph; section headers end in a colon and group bullets by component, module, or theme; **Tests** and **Known gaps** / **Deviations** are dedicated sections at the end. The example block was rewritten to demonstrate the sectioned style on a realistic multi-component commit (Reporting package / Packaging and paths / Desktop UI / Tests / Known gaps), and a counter-example was added showing the multi-paragraph flowing-prose body shape that the agent must NOT produce.
- **`catalog/skills/workflow/code-commit-workflow/SKILL.md` Body subsection expanded.** Adds the same sectioned-bullet rule. New realistic Good Example demonstrating the sectioned style. New Bad Example demonstrating the multi-paragraph flowing-prose body shape. New row in the Common Rationalizations table rebutting "flowing paragraphs read better than bulleted lists for prose-heavy commits" (reviewers don't read commit bodies linearly; they scan for the component or theme they care about, and section headers put scannable anchors in the right place). Quality Checklist gains a sectioned-structure item.
- **`catalog/commands/implement-phase.md` post-phase sub-step 6 inline rule expanded.** Adds the sectioned-bullet rule with implementation-specific suggested headers (`Reporting package:` / `Packaging:` / `Desktop UI:` / `Tests:` / `Known gaps:`-style, scoped to each phase's actual components). Whitespace constraint added (exactly one blank line between sections; bullets contiguous within a section).
- **`catalog/commands/wrap-up-session.md` Phase 7 inline rule expanded.** Adds the sectioned-bullet rule with wrap-up-specific suggested headers (`Session history:` / `DEVLOG:` / `Documentation:` / `Gitignore:` / `Memory:` / `Version bump:` - only the ones that actually changed in this session).
- **`catalog/commands/update-version.md` Phase E4 inline rule and example replaced.** Format and rules block now requires the sectioned-bullet structure using CHANGELOG section names as headers directly (`Added:` / `Changed:` / `Fixed:` / `Removed:` / `Tests:`). The example was rewritten to map CHANGELOG entries to the matching section headers; a counter-example showing the previous flat `Changes:` bullet-soup style was added so the agent cannot fall back to that shape.

### Why a separate patch and not a v1.2.0

Same diagnosis as v1.1.4: slash command bodies are not transitively imported. A reference like "Run `/generate-commit-message`" inside another command body is just text. So even with the v1.1.4 fix patching the no-hard-wrap rule into all three downstream commands, the structure rule had to be patched into all five files (canonical command + canonical skill + three downstream commands) the same way. Strictly additive content-only changes; no schema, no installer, no test changes; safe PATCH bump.

---

## [1.1.4] - 2026-05-06

Patch release. Closes a gap missed by v1.1.1: the no-hard-wrap rule was added to `/generate-commit-message` and the `code-commit-workflow` skill, but the commands that mention `/generate-commit-message` as a sub-step (`/implement-phase`, `/wrap-up-session`) and the one with its own inline commit-message rules (`/update-version`) never picked it up. A reference like "Then run `/generate-commit-message`" inside another command body is just text - the agent does NOT auto-load that file's content when it sees the reference. So the v1.1.1 fix only applied when the user typed `/generate-commit-message` directly; every other code path ending in a commit-message generation kept producing wrapped output. Reported against a v0.3.0 phase-implementation commit shortly after the v1.1.3 install. Safe to upgrade from v1.1.3; no migration steps. Restart any running AI-agent sessions after re-running the installer so the patched command bodies take effect.

### Fixed

- **`/implement-phase` post-phase sub-step 6 now carries the no-hard-wrap rule.** `catalog/commands/implement-phase.md` line 311 (sub-step 6 "Final Commit Message", the one that says "Run `/generate-commit-message`") now inlines the rule with explicit wrap-column callouts (50, 72, 80, 100), the 72-char subject-line cap exception, and the blank-line-still-separates-paragraphs clarification. Resolves the user-reported bug where /implement-phase produced commit messages with paragraph bodies and bullets hard-wrapped at ~70 columns even after a fresh v1.1.3 install.
- **`/wrap-up-session` Phase 7 now carries the no-hard-wrap rule.** `catalog/commands/wrap-up-session.md` line 192 ("Final Commit") gets the same explicit rule injection, just before the existing scope-and-format guidance.
- **`/update-version` Phase E4 commit-message rules extended.** `catalog/commands/update-version.md` lines 430-437 previously said "Keep each bullet point concise and on a single line" - bullets only. Replaced with the full paragraph-and-bullet rule, with the 72-char subject-line cap explicitly called out as a hard limit (not a wrap) and the obsolete "72-char convention" rebutted inline so the agent cannot fall back to it.

### Why three patches and not one upstream rule

Slash command bodies are not transitively imported. The agent reads the body of the command the user typed, but textual references to other commands (e.g. "Run `/generate-commit-message`") do NOT cause the referenced file's body to be loaded. Every command that produces a commit message must therefore carry the no-hard-wrap rule in its own body to keep it in the agent's context window when generation happens. This release patches the three currently-affected commands; future commands with commit-message generation steps must follow the same pattern (an enforcement test could be added in a future release if regressions recur).

---

## [1.1.3] - 2026-05-06

Patch release. Breaks the v1.1.2 Claude-only pre-commit review design out into four parallel, fully-independent hooks - one per supported AI CLI. Removes the implicit coupling that forced every user to install Anthropic's `claude` CLI to use the v1.1.2 hook regardless of their primary AI platform. Each user now picks the hook variant matching the AI service they already pay for; Cursor and GitHub Copilot are explicitly out of scope (no usable headless review CLI). Safe to upgrade from v1.1.2: existing v1.1.2 installations of `~/.devai-hub/hooks/claude-diff-review.sh` keep working unchanged, and re-running the installer simply adds three sibling files alongside it.

### Added

- **Three new platform-parallel pre-commit review hooks** in `catalog/hooks/`. Each hook is a fully self-contained ~125-line bash script that calls only its own CLI - no shared library dependency, no cross-platform fallbacks. Bypass paths (`DEVAI_DIFF_REVIEW_DISABLE=1`, `git commit -n`, `DEVAI_DIFF_REVIEW_MAX_BYTES`), merge / cherry-pick / rebase short-circuit, fail-open behavior, and `VERDICT: PASS|WARN|BLOCK` parsing are duplicated across all four hooks so each can be copied to `.git/hooks/pre-commit` standalone.
    - `gemini-diff-review.sh` calls `gemini -p` (Google Gemini CLI / Antigravity).
    - `codex-diff-review.sh` calls `codex exec` (OpenAI Codex CLI). Combines prompt + diff into a single argument because Codex's `exec` subcommand does not consistently read context from stdin across versions.
    - `opencode-diff-review.sh` calls `opencode run` (OpenCode CLI). Same combined-argument pattern as the Codex variant for the same reason.
- **`/install-pre-commit-review-hook` slash command** at `catalog/commands/install-pre-commit-review-hook.md`. Replaces the v1.1.2 `/install-claude-pre-commit-hook`. Auto-detects which of the four supported CLIs are on PATH and either auto-selects (exactly one), asks the user to choose (multiple), or asks the user to install one (zero) - with `--platform=<claude|gemini|codex|opencode>` and `--force` flag overrides. Same backup / chain / abort logic as v1.1.2 for pre-existing pre-commit hooks. The marker-comment detection now matches any of the four hook variants so a re-run can detect which platform is currently installed and offer to switch / re-install cleanly.
- **`TestPlatformIndependence` parametrized test class** in `catalog/hooks/tests/test_diff_review_hooks.py`. Asserts that no hook script contains `command -v <other-cli>` or invokes any sibling CLI, so a Gemini user's hook can never silently fall back to Claude (or any other vendor) and vice versa. The test inspects the source file directly rather than the runtime behavior, so it catches accidental cross-references at edit time.
- **Hook source distribution loop** in both `scripts/installer.sh` and `scripts/installer.ps1`. The single `safe_copy` / `Safe-Copy` line from v1.1.2 was replaced by a 4-element loop that copies all four `*-diff-review.sh` variants to `~/.devai-hub/hooks/`. Loop body deliberately silent on missing files (the `[ -f ]` / `Test-Path` guard) so a partial catalog still installs cleanly.

### Changed

- **v1.1.2 test file `test_claude_diff_review.py` renamed to `test_diff_review_hooks.py`** (plural) and parametrized over all four hook variants via `pytest.mark.parametrize` on a `(hook_filename, cli_binary_name)` tuple list. Each of the 11 logical scenarios from v1.1.2 (bash syntax, env-var bypass, empty diff, missing CLI, merge skip, rebase skip, diff-size cap, PASS / WARN / BLOCK / unparseable verdict) now runs four times, once per variant - 44 logical tests, plus 4 platform-independence assertions, total 48 tests. Combined hook test suite: **310 tests passing** (262 v1.1.1 baseline + 48 new diff-review tests, with the v1.1.2 11 absorbed into the parametrized set).

### Removed (Breaking, but no v1.1.2-installed users likely affected)

- **v1.1.2 `/install-claude-pre-commit-hook` slash command deleted.** Users who started typing `/install-claude-...` after v1.1.2 will need to switch to `/install-pre-commit-review-hook` or pass `/install-pre-commit-review-hook --platform=claude` for the same result. v1.1.2 was released earlier the same day as v1.1.3, so the migration window is effectively zero hours; no deprecation alias was added.

---

## [1.1.2] - 2026-05-06

Patch release. Adds an opt-in git pre-commit hook (`claude-diff-review.sh`) and a new slash command (`/install-claude-pre-commit-hook`) that wires the hook into a target repository on demand. Nothing changes in any existing repository unless the user explicitly runs the new command - the hook is distributed to `~/.devai-hub/hooks/` but is never auto-wired into any `.git/hooks/pre-commit`. Safe to upgrade from v1.1.1 with no migration steps and no installer-rerun side effects beyond picking up the new hook source file.

### Added

- **`/install-claude-pre-commit-hook` slash command** (`catalog/commands/install-claude-pre-commit-hook.md`). When invoked from inside a target repo, copies `~/.devai-hub/hooks/claude-diff-review.sh` to that repo's `.git/hooks/pre-commit` after detecting and asking about any pre-existing pre-commit hook (replace / abort / chain-manually options, with a `.git/hooks/pre-commit.devai-backup-<timestamp>` backup written before any overwrite). Cross-platform: works on Linux, macOS, and Windows (Git for Windows runs hooks via its bundled bash, so the bash hook source runs natively without a Windows-specific port).
- **`catalog/hooks/claude-diff-review.sh`** opt-in git pre-commit hook. Pipes `git diff --cached` through `claude -p` with a strict review prompt covering: hardcoded credentials, debug artifacts (console.log / print / debugger / pdb / dd / dump / fmt.Println in production code), unfinished TODOs / FIXMEs / placeholder values, and commented-out code blocks larger than 3 contiguous lines. Parses Claude's response on the first line (`VERDICT: PASS|WARN|BLOCK`) and exits accordingly: `PASS` silent allow, `WARN` prints findings to stderr but allows the commit, `BLOCK` refuses the commit with exit 1. Fail-open on every error path (CLI absent, response empty, verdict unparseable, oversized diff, merge / cherry-pick / rebase in progress) so the hook can never permanently brick a workflow. Three bypass paths baked in: `DEVAI_DIFF_REVIEW_DISABLE=1 git commit ...` env-var override, git's standard `--no-verify` flag, and the configurable `DEVAI_DIFF_REVIEW_MAX_BYTES` cap (default 50 KB) so large commits skip review automatically.
- **Installer wiring** in both `scripts/installer.sh` and `scripts/installer.ps1`. New `safe_copy` / `Safe-Copy` line in the existing `install_templates` function copies `catalog/hooks/claude-diff-review.sh` to `~/.devai-hub/hooks/claude-diff-review.sh` (Linux/macOS) or `%USERPROFILE%\.devai-hub\hooks\claude-diff-review.sh` (Windows), with `chmod +x` on POSIX. The hook is shared cross-platform under `~/.devai-hub/`, not per-platform under `~/.claude/hooks/`, because it is a git hook (not a Claude Code PreToolUse hook) that fires on `git commit` regardless of which AI assistant the user runs.
- **11 new pytest tests** in `catalog/hooks/tests/test_claude_diff_review.py` covering: bash syntax (`bash -n`), env-var bypass short-circuit, empty-diff exit, missing-CLI fail-open with warning to stderr, merge-state skip, rebase-state skip, diff-size-cap warning, and PASS / WARN / BLOCK / unparseable verdict parsing. Tests stub the `claude` CLI by creating a fake bash binary on PATH that emits a fixed response. Combined hook test suite: **273 tests passing** (262 prior + 11 new).
- **Command count incremented** from 32 to 33 in `catalog/hooks/session-start.sh` (the value displayed in the SessionStart orientation banner).

---

## [1.1.1] - 2026-05-06

Patch release. Tightens the commit-message no-hard-wrap rule so it covers body paragraphs and footers, not just bullet points, and makes the installer-smoke test resilient to future version bumps. No behavioral or schema changes; safe to upgrade from v1.1.0 with no migration steps and no installer-rerun side effects (the installer's distributed artifacts are content-only).

### Changed

- **Commit-message no-hard-wrap rule extended from bullets to all body content.** Previously `/generate-commit-message` and the `code-commit-workflow` skill forbade hard-wrapping only on bullet points; long body paragraphs were still being silently wrapped at ~72 columns. Both files now require every paragraph and every bullet point in the commit body and footer to be a single continuous source line, regardless of length, with the common wrap columns (50, 72, 80, 100) called out explicitly so the agent cannot rationalize one of them as "the convention." The subject line's 50-character cap is the only exception (it is a hard limit, not a wrap). Cross-platform reach: command file via `catalog/commands/` recursive copy (Claude Code, Gemini / Antigravity, Codex); skill file via the skill index in `base-*.md` instruction files (all five platforms). No installer edits needed for either file.
- **Three "Good Examples" in the `code-commit-workflow` skill unwrapped** so they demonstrate the new rule instead of silently contradicting it. A hard-wrapped "Bad Example" was added so the failure mode is visible side-by-side with a Good Example. Two new entries in the Common Rationalizations table rebut the "72-column convention" excuse (modern Git tooling, GitHub, GitLab, IDE diff views, and `git log` all soft-wrap on display; hard-wrapped source breaks copy-paste round-trips into changelogs and review comments) and the "split for readability" excuse (visual readability is the renderer's job; if a bullet is genuinely too long to follow, split it into two distinct bullets, not into a continuation line that breaks the bullet's identity in Markdown and Git UIs).
- **Quality Checklist and Verification in `code-commit-workflow` gain a no-wrap item** with a `git show --no-patch HEAD` spot-check so the rule is enforceable post-commit, not just a generation-time intent.

### Fixed

- **Installer-smoke test no longer hard-codes the canonical version string.** `catalog/hooks/tests/test_installer_smoke.py` now reads the canonical version from `.claude-plugin/plugin.json` at test time instead of asserting against a hard-coded `"1.1.0"`. Every prior version bump required a follow-up commit to keep the smoke test green; future PATCH / MINOR / MAJOR bumps will not need that follow-up.

---

## [1.1.0] - 2026-05-05

PowerShell-tool parity for the description-and-auto-approve pipeline that was previously Bash-only, plus the per-version known-gaps tracker introduced earlier in the cycle. Minor bump because the changes are additive: existing Bash-only configurations continue to work without modification.

> **Upgrade note**: Claude Code (and most other AI agents) read `settings.json`, `AGENTS.md`, and `.cursor/rules/` at session start and do NOT hot-reload them. After running the v1.1.0 installer, restart any running Claude Code / Cursor / Gemini / Codex / Copilot sessions for the new hooks and permission entries to take effect. The installer now prints this reminder at the end of every run.

> **Known limitation (Claude Code upstream)**: Claude Code's PowerShell approval dialog renders an empty body when a `PreToolUse` hook returns `permissionDecision: "ask"`. The hook-prepended `# ===== Description ===== #` comment block is delivered to Claude Code via `updatedInput.command` and is visible in the chat-history `IN` block and inside the collapsible `Details ▾` panel, but NOT directly under the dialog header where the equivalent Bash dialog renders it. We tried three different output surfaces (`updatedInput.command`, `updatedInput.description`, `permissionDecisionReason`) - none reach the dialog body for PowerShell. This is a Claude Code rendering inconsistency between the Bash and PowerShell tools, not a DevAI-Hub bug. The safety guarantee (destructive PowerShell commands gate on user approval) holds regardless. Workaround: click `Details ▾` to expand the panel and see the prepended description. Tracked upstream at `anthropics/claude-code` (issue to be filed).

### Fixed

- **Stale-sentinel bug in Claude permission installer**. `scripts/installer.sh`, `scripts/installer.ps1`, and `scripts/Install-DevAI-Permissions.ps1` (Claude branch) skipped the entire permissions merge when a single hard-coded sentinel string (`Bash(gh pr list)` / `WebFetch(domain:api.github.com)` / `WebFetch(domain:github.com)`) was already present in the user's `~/.claude/settings.json`. Any user who installed v0.9.5+ in the past would never receive new allow-list entries shipped in later versions - including the ~100 `PowerShell(...)` patterns added in v1.1.0. Replaced the binary sentinel with a count-based delta computation: the installer now compares the merged set against the existing set and only writes (and creates a backup) when at least one new entry would be added. Same code path now reports `(N new entries)` or `(0 new entries)` accurately. Gemini / Codex / Copilot installer branches carry the same bug pattern and are not fixed in this release because they do not ship new entries in v1.1.0; tracked as a follow-up.
- **PowerShell hook now explicitly returns `permissionDecision: "ask"` for non-allow-listed commands**. Empirically verified against Claude Code 2.1.x by replaying real session transcripts: when a `PreToolUse:PowerShell` hook returns `updatedInput` without an explicit `permissionDecision`, Claude Code's PowerShell tool treats it as approval and executes the command silently - bypassing the user-approval dialog entirely. The Bash tool falls through to a default-ask path in the same scenario; PowerShell does not. The hook now returns `{"permissionDecision": "ask", "permissionDecisionReason": "..."}` alongside the comment-block-augmented `updatedInput` so non-read-only commands (Set-Content, Remove-Item, Copy-Item, anything with script blocks / redirects / call operators) reliably surface in the approval dialog instead of executing silently.
- **PowerShell hook now surfaces the description in `permissionDecisionReason`**, not just inside `updatedInput.command`. Side-by-side test against Bash showed Claude Code's PowerShell approval dialog hides the body of `updatedInput` behind a collapsed "Details" panel, while the Bash dialog renders the comment-box prepend visibly under the header. To reach the user-visible dialog body, the hook now writes the model-supplied `description` field into `permissionDecisionReason` for every non-allow-listed command. Auto-approved commands keep the existing reason ("All pipeline segments match configured allow patterns") so the audit trail still distinguishes them.
- **Extra read-only automatic-variable patterns** added to `configs/permissions/claude-permissions.json`: `$PWD`, `$PWD.Path`, `$PWD.ProviderPath`, `$HOME`, `$PROFILE`, `$PID`, `$Host.Version`, `$Host.Name`, `$Host.UI.RawUI.WindowSize`, `$ExecutionContext.SessionState.Path.CurrentLocation`, `$PSVersionTable.PSVersion`, `$PSVersionTable.PSVersion.ToString()`. The model frequently reaches for these property-access forms when asked for read-only commands; explicit cmdlet equivalents (e.g. `Get-Location` for `$PWD.Path`) were already covered, but the bare-variable form now auto-approves too.

### Added

- **PowerShell description hooks** (`catalog/hooks/require-powershell-description.sh` + `catalog/hooks/format-powershell-description.py`) - mirror the existing Bash description pipeline for Claude Code's PowerShell tool. The format hook prepends a `# ===== Description ===== #` comment block to the script body so the description stays visible in the truncated approval-dialog preview (Claude Code does not surface the `description` field in the PowerShell approval header today), and auto-approves single-line read-only pipelines whose pipe-separated segments all match a `PowerShell(...)` allow pattern. The require hook hard-blocks calls without a description. Both are registered for `"matcher": "PowerShell"` in `catalog/hooks/settings.json`.
- **PowerShell auto-approve allow-list** in `configs/permissions/claude-permissions.json` - read-only `Get-*`, `Test-*`, `Resolve-*`, `Format-*`, `Select-*`, `Sort-*`, `Group-*`, `Measure-*`, `ConvertFrom-*` / `ConvertTo-*`, `Where-Object` (comparison-statement form only), CIM/WMI getters, network info getters, hashing, and the common aliases (`ls`, `dir`, `cat`, `pwd`, `gci`, `gc`, `gm`, `sls`, ...). Auto-approve is intentionally conservative: any command containing `;`, `{`, `}`, `>`, `<`, `` ` ``, `$(`, `@(`, `@{`, or `&` (outside single-quoted literals; `$(` and backticks are also blocked inside double quotes because PowerShell interpolates and escapes there) is rejected. Multi-line scripts are never auto-approved. `ForEach-Object` is intentionally excluded because its property-access and method-invocation forms (`ForEach-Object Name` vs `ForEach-Object Delete`) are syntactically indistinguishable.
- **80 new pytest tests** in `catalog/hooks/tests/test_format_powershell_description.py` covering the pipeline splitter, quote-aware syntax scanner, allow-list matcher, real-config integration (parametrized over safe and unsafe command samples), description-box rendering, and end-to-end subprocess flow. Combined hook test suite: 261 tests passing.
- **MANDATORY rule** in `templates/ai-instructions/base-claude.md` extending the existing Bash-tool description requirement to the PowerShell tool. Codex / Gemini / Cursor / OpenCode templates are unchanged because none of those agents expose a PowerShell-specific tool.
- **Post-install restart reminder** in both `scripts/installer.sh` and `scripts/installer.ps1`. After the "Installation Complete" banner, both installers now print a yellow notice explaining that `settings.json` / `AGENTS.md` / `.cursor/rules/` are loaded at session start and not hot-reloaded - any already-running AI-agent session must restart before new hooks, commands, skills, and permission entries take effect. Surfaces an upstream Claude Code limitation tracked at `anthropics/claude-code#17127`.

- **`known-gaps-tracker` skill** (`catalog/skills/workflow/known-gaps-tracker/`) - per-version, append-only log at `docs/<version>/known-gaps.md` recording items that did not reach a clean state by the end of each phase: subtasks not implemented (`NI`), intentionally deferred work (`DF`), bugs found but not fixed (`BG`), suppressed warnings (`WN`), missing-test / coverage gaps (`MT`), and quality-gate gaps the user bypassed with "Proceed anyway" (`QG`). Each item carries `Source phase`, `Plan reference`, `Reason`, and `Suggested next step`. File is `in-progress` while the version is active and `finalized` at version bump.
- **`/implement-phase` Phase 8 step 2: known-gaps Append** - after `/update-gitignore`, the command now classifies and appends gaps surfaced during the phase to `docs/<version>/known-gaps.md`, recomputes the Summary table, and moves any earlier items it just resolved to the Resolved table. The Completion Report surfaces `Known gaps: N added, M resolved`.
- **`/wrap-up-session` Phase 4 Step 4b: known-gaps Sweep** - after `/update-devlog`, the command mines the live conversation for items not already captured during `/implement-phase` (TODOs, suppressed warnings, stubbed-out functions, partial implementations) and appends them with category prefixes.
- **`/wrap-up-session` Phase 6 Step 6b: known-gaps Finalize** - on a successful `/update-version` run, flips the prior version's `known-gaps.md` `Status:` from `in-progress` to `finalized` and appends a version-bump note. Files left `in-progress` (no version bump) are still picked up by the next `/generate-plan`.
- **`/generate-plan` Step 0.6: Prior-Version Known-Gaps Ingest** - always runs (regardless of whether Step 0.5 From-comparison mode triggered). Reads `docs/<prior-version>/known-gaps.md` plus any older still-`in-progress` files, presents open items grouped by originating version, and offers Ingest-all / Pick-subset / Skip. Selected items seed Q2 (Scope) and Q3 (Affected Areas) of the discovery interview and become tagged sub-tasks in Step 4 with the prefix `[from <prior-version> known-gaps: <ID>]`. Source-file entries are moved from `## Open Items` to `## Resolved` with `transferred to <new-version> plan` after the new plan is written.

---

## [1.0.0] - 2026-04-24

**First stable release.** Reverse-engineering-first security hardening: DevAI-Hub is now safe for use in regulated industries and other high-trust environments where proprietary source code, prompts, and query text must not leak to third-party data processors. 12-phase plan at [docs/v1.0.0/plans/security-hardening-v100.md](docs/v1.0.0/plans/security-hardening-v100.md). Version-bump skipped 0.9.8 because the accumulated scope (policy bake-in, new authoritative matrix, 2 new internal MCPs, 3 new skills, breaking registry removals, command-level workflow change, new governance section in AGENTS.md) is a major-version event.

### Added
- **MCP Registry Policy** in `AGENTS.md` with a reverse-engineering-first decision tree (local-only -> LLM-native skill -> reverse-engineered internal MCP -> trusted vendor wrapper -> drop), 5-question audit checklist required on every registry entry's `_comment`, and an explicit hard-no list (search-as-service, embeddings-as-service, scraping-as-service, generation-as-service). Condensed summary distributed diff-identical across 7 platform surfaces (5 base-*.md templates + `.github/copilot-instructions.md` + `.cursor/rules/devai-hub.mdc`).
- **Reverse-Engineering Matrix** at `docs/v1.0.0/mcp-reverse-engineering-matrix.md`: authoritative classification document for every MCP ever referenced by DevAI-Hub (18 rows: 5 internal/local + 6 vendor-intrinsic + 4 dropped + 2 new internal + 1 reverted). Each row cites upstream evidence and names its internal deliverable (for `re-*` classifications) or its justification paragraph (for `vendor-intrinsic`).
- **`devai-code-search` internal MCP** at `extensions/devai-code-search/` - local-only code search with keyword-only retrieval in v1.0.0 (inverted index + `rapidfuzz` + underscore-split tokenizer), content-hash incremental re-indexing, `.gitignore` + `.devaiignore` respect, SSRF-irrelevant (no network), zero API keys, zero model downloads. Four MCP tools: `index_codebase`, `search_code`, `clear_index`, `get_indexing_status`. Dense / hybrid retrieval planned for v1.1.0.
- **`devai-web-fetch` internal MCP** at `extensions/devai-web-fetch/` - local-only HTTPS fetch + `readability-lxml` main-content extraction. SSRF guard blocks RFC 1918, loopback, link-local, and `file://` by default (user-overridable via `~/.devai/web-fetch.yaml`). Three extract modes (readability, text, raw). Single-URL scope; Playwright JS rendering reserved for v1.1.0.
- **`code-semantic-search` skill** (`catalog/skills/ai-development/code-semantic-search/`) - specialized sibling of `rag-implementation` for code corpora. References DevAI-Hub's internal `devai-code-search` as the reference implementation; zero external attribution.
- **`ui-component-generation` skill** (`catalog/skills/developer-experience/ui-component-generation/`) - LLM-native replacement for external component-generation services. Instructs the agent to generate components directly using its own LLM; zero code, zero MCP.
- **`local-docs-lookup` skill** (`catalog/skills/research/local-docs-lookup/`) - disciplined 7-step lookup sequence (introspect -> vendored README -> shipped docs -> type stubs -> project docs -> man pages -> user-approved single URL) replacing one use case of external documentation-lookup services.
- **`/compare-project` Section 9 "Security and Risk Assessment"** - mandatory section in every comparison report. Four subsections: threat model comparison, per-item risk scorecard, reverse-engineering viability analysis (classifies every adoption candidate per the decision tree), and recommendation ordering (skill-native first, then RE builds, then vendor-intrinsic with justification, then drops moved to N-item list). Renumbered existing Sections 9-12 to 10-13.
- **`/run-deep-review` command** - new pre-release deep-review orchestrator that chains known-gaps collection, health gates (test execution + 80% coverage threshold), dependency scan, docs / git / CI/CD / release-readiness hygiene, project validators, `/analyze-codebase`, `/run-security-audit`, `/run-penetration-test --depth=deep`, and `/review-codebase` into a single 12-phase run. Synthesizes findings (P0/P1/P2/P3) into one severity-ranked report with a GO / GO-WITH-CONDITIONS / NO-GO verdict, then chains into `/generate-plan` for the remediation roadmap. Phase 4 also covers CI/CD workflow file audit, CI run history (last 20 runs on main; flaky-test detection), branch protection rules, version-bump consistency across canonical files, tag hygiene (annotated vs lightweight, on-main check), and pending draft GitHub releases. All artifacts centralized under `docs/<next-version>/review/`. Use this before cutting a major or minor release; use the individual review commands during day-to-day development.
- **`/compare-project` -> `/generate-plan` RE-first handoff** - the chain always passes `reverse-engineer-first=true`. `/generate-plan` Step 0.5f sequences phases per the Section 9.4 ordering when the flag is set.
- **Internal MCP benchmark harness** at `scripts/devai_mcp_benchmark.py` + `make benchmark` target + pytest coverage. Benchmarks all three internal MCPs in one run; no-network guard refuses outbound sockets during the skill-server and code-search phases. JSON output retained in `data/benchmarks/mcp.json` (last 10 runs, gitignored).
- **13 new pytest tests** for the benchmark harness. Skill-server / code-search / web-fetch / benchmark combined: 88 tests passing.
- **`/compare-project` now chains into `/generate-plan`.** A new Step 8 counts adoption items by tier (P0 / P1 / P2 / P3) AND by RE bucket (skill-native, re-full, re-partial, vendor-intrinsic, drop-outright), and always asks whether to immediately generate an implementation plan.
- **`/generate-plan` Step 0.5 From-comparison mode.** Parses the report's Adoption Plan section, inherits the version from the comparison file's path, derives the slug as `adoption-<name>`, defaults the plan type to Feature/Enhancement, and skips interview questions the report already answers.
- **`implementation-plan` skill v1.2.0** documents the from-comparison hand-off path.

### Changed
- **`rag-implementation` skill de-branded.** The Phase 1 content additions from the abandoned `adoption-claude-context` plan (Canonical OSS Reference paragraph, Vector Store / Embedding / AST / Merkle tables and subsections) are rewritten to strip every external-source attribution (`zilliztech/claude-context`, `Zilliz Cloud`, `voyage-code-3`, SWE-bench metrics, upstream file-path citations) while preserving all technical content. Concrete references now point at the internal `devai-code-search` MCP; generic ecosystem enumerations replace specific vendor-named models.
- **`context-manager` and `context-engineering` skills** cross-link to `code-semantic-search` (one Related Skills entry each), framed as the escape valve when the repo exceeds the context window.
- **`catalog/mcp-configs/mcp-servers.json` rewritten.** Registry went from 15 -> 11 kept -> 13 (with the 2 new internal MCPs). Every kept entry now carries the full 5-question audit in its `_comment`. Top-level `_comment` references the MCP Registry Policy and the matrix.
- **`guides/MCP_DEVELOPMENT_SERVERS.md` rewritten** - replaced recommendations for `context7` / `deepwiki-mcp` / `tavily` (all drop-class under the new policy) with recommendations for only policy-compliant servers. New "Reverse-engineered replacements" table maps popular dropped patterns to DevAI-Hub equivalents.
- **`infrastructure/integrations/README.md` shortened 601 -> 180 lines** with a policy-compliance callout at the top. Removed the OpenAI template block (unspecified prompt-to-third-party-LLM is drop-class under the policy).
- **7 platform instruction surfaces** carry the condensed MCP Registry Policy summary in lockstep.
- **`/compile-deep-research` pivoted from script-based to agent-driven.** The persistent generator at `scripts/compile_deep_research.py` has been deleted along with its entries in `scripts/installer.sh` / `scripts/installer.ps1`. The SKILL and command have been rewritten as a detailed playbook: per invocation the agent inspects the user-selected template's styles.xml / theme / header-footer, builds a style profile, synthesizes content, and writes a throwaway python-docx generator (`generate.py` saved in the cache dir for reproducibility) whose styling is derived entirely from the template.
- **`/compile-deep-research` output layout split final outputs from intermediates.** Final outputs land in `<project>/docs/compiled/<ReportTitle>.{ext}`; intermediates in `<project>/.cache/compile-deep-research/<ReportTitle>/`.
- **Style-guide companion files moved out of `catalog/commands/`.** `compile-deep-research-style-guide.md` and `generate-report-style-guide.md` were both surfacing as slash commands (`/compile-deep-research-style-guide`, `/generate-report-style-guide`), confusing users about which to invoke vs. the actual `/compile-deep-research` and `/generate-report` commands. Both files moved to a new `catalog/style-guides/` directory at the catalog top level (sibling of `catalog/commands/`); files were renamed to drop the redundant `-style-guide` suffix since the parent folder name now provides that context. The two affected command bodies were updated to reference the new paths. Both installers gained a single `safe_folder_copy` step that distributes `catalog/style-guides/` to `~/.devai-hub/style-guides/` (a shared, non-platform-specific install). The `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, and `.cursor/rules/devai-hub.mdc` "new command" rule was updated so future commands needing a style-guide reference put it in the new location. Test (`catalog/hooks/tests/test_installer_smoke.py`) updated to expect the new path.
- **Version bump** across 14 canonical files from `0.9.7` -> `1.0.0` (skipping 0.9.8).
- **`claude-usage-monitor` extension v0.5.0** - threshold notifications rewritten around an Effort-first policy: Moderate -> reduce Effort to High or Medium (no model swap); High -> switch to Sonnet 4.6 if on Opus AND reduce Effort to High or Medium; Critical -> switch to Haiku 4.5 and set Effort to Low. Critical default raised from 90% to 95%. All notifications now auto-dismiss via `vscode.window.withProgress` after `claudeUsage.notificationTimeoutSeconds` (default 12s, range 3-60s) so they never stack while VS Code is in the background. Status bar gear icon now mirrors the urgency background color so users can tell it belongs to the Claude Usage Monitor. New gear button added to the dashboard panel right of "Open Usage Page" for quick access to the Settings webview.

### Removed (Breaking)
- **Four third-party MCP registry entries removed** from `catalog/mcp-configs/mcp-servers.json`: `context7` (Upstash search-as-service), `exa-web-search` (Exa search-as-service), `firecrawl` (scraping-as-service), `magic-ui` (21st.dev generation-as-service). Users who relied on these can add them back to their own `.claude/settings.json` manually; DevAI-Hub no longer ships the snippets.
- **The `claude-context` registry entry** that was briefly added in the aborted v0.9.8 Phase 2 is reverted before ship. Never committed to a tagged release.
- **The `adoption-claude-context` plan (v0.9.7 Phases 3-6)** is abandoned, superseded by the v1.0.0 plan. Phases 3-5 are reverse-engineered into v1.0.0 Phases 8-10; Phase 6 (release) is absorbed here.
- **`/generate-implementation-plan` deprecation alias deleted.** The v0.9.7 forwarding shim (`catalog/commands/generate-implementation-plan.md`) has been removed along with every remaining textual reference that described the alias as preserved. Users must now invoke `/generate-plan` directly.

---

## [0.9.7] - 2026-04-22

Closes 22 deduplicated recommendations from the three v0.9.6 gap analyses (session management / 1M context, Opus 4.7 best practices, red-team security audit). Six planned phases shipped; Phase 5 (VS Code extension effort-level integration) is partially deferred - see **Deferred** below.

### Added

**New skills**:
- **`catalog/skills/security/business-logic-abuse/SKILL.md`** - domain-aware audit covering race conditions, TOCTOU, double-spending, workflow-state bypass, idempotency violations, and check-sequence abuse. Includes a rule-elicitation step that refuses to proceed on unspecified domains and produces a findings table keyed by attack class, invariant violated, and architectural remediation.
- **`catalog/skills/security/advanced-attack-patterns/SKILL.md`** - architecture-level attack classes gated on applicability checks: state desynchronization, cache poisoning, replay attacks, and timing-attack surfaces beyond password comparison. Each class has applicability / patterns / remediation / indicators-in-code sections.
- **`catalog/skills/specialized-domains/deep-research-compilation/SKILL.md`** - compile multiple research reports across 7 input formats (.docx, .md, .pdf, .pptx, .html, raw URLs, .txt) into a single unified document in .docx, .pdf, or .md form, with deduplicated inline [N] citations linking to a References section. Detailed agent-driven playbook: per invocation the agent inspects the user-selected template, builds a style profile, synthesizes content with no redundancy, and authors a throwaway python-docx program tailored to the template's own styles -- no persistent generator script. Reference dedup via DOI -> normalized URL -> rapidfuzz fuzzy title match.

**New guides**:
- **`guides/SESSION_LIFECYCLE_DECISIONS.md`** - five-branch decision tree (continue / `/rewind` / `/clear` / `/compact` / delegate to subagent) with ASCII decision flowchart, trigger criteria per branch, `/compact focus on X, drop Y` steerable-compaction examples, and three worked examples. Cross-linked from `TOKEN_OPTIMIZATION.md`, 4 orchestration SKILLs, `session-history/SKILL.md`, and `SUBAGENTS_GUIDE.md`.
- **`docs/v0.9.6/opus-4-7-migration.md`** - operator migration guide synthesizing the Opus 4.6 -> 4.7 behavioral deltas. TL;DR with four must-do items (reconfirm effortLevel, explicit fan-out, remove fixed thinking budgets, batch clarifying questions), 13-row cross-reference table indexing each delta to its canonical catalog location, what-to-remove list, and a migration checklist. Filed under `v0.9.6/` to co-locate with the comparison document that drove the work.

**New checklists**:
- **`catalog/checklists/file-upload-security.md`** - defense checklist against polyglot files, MIME confusion, archive path traversal, zip-bomb signatures, resource-limit bypasses, AV pipeline gaps, and unsafe serving of user-uploaded content. Cross-linked from `security-patch-advisor/SKILL.md` Related Resources.

**New commands**:
- **`/run-penetration-test --depth=deep`** - optional 6th hunter (Business Logic & Advanced Attacks) that wires in both new security skills. Gated behind the flag because aggregate cost increases by ~20%; base 5-hunter run remains the default.
- **`/compile-deep-research`** (`catalog/commands/compile-deep-research.md` + companion `compile-deep-research-style-guide.md`) - 9-phase command that ingests multiple research reports and emits a unified document matching a user-selected template. Agent-driven throughout: Phase 2 asks for the template explicitly, Phase 5 inspects the template to build a style profile, Phase 8 writes a throwaway python-docx generator per invocation saved as `<Title>_generate.py` for reproducibility. No persistent generator script.

**New supporting templates**:
- **`templates/documentation/branded-report-template.docx`** - default branded Word template with teal #215868 Consolas title, Calibri Light small-caps headings, auto-TOC, superscript [N] citation styling, and hanging-indent references. Ships alongside the existing generic template. `/compile-deep-research` presents it as the default in Phase 2 but always asks for explicit user confirmation; the agent adapts its generation to whichever template is chosen.

**Repo-scoped AI agent instruction set** (covers installer-aware contribution rules across all 6 agentic platforms):
- **`AGENTS.md`** extended with a new **"Installer-Aware Changes (Cross-Platform)"** section (canonical; read by Codex / OpenCode / Aider / Jules).
- **`CLAUDE.md`** (Claude Code) and **`GEMINI.md`** (Gemini CLI / Antigravity) - thin pointer files using `@AGENTS.md` import + quick reference.
- **`.github/copilot-instructions.md`** (GitHub Copilot, inline summary - Copilot cannot use `@` imports).
- **`.cursor/rules/devai-hub.mdc`** (Cursor IDE, with `alwaysApply: true` frontmatter).
- All six files enforce the same rules: any new `scripts/*.py` MUST be registered in both `scripts/installer.sh` and `scripts/installer.ps1`; any new skill MUST update the three registry files (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`); platform instruction templates (`templates/ai-instructions/base-*.md`) MUST be edited in lockstep across all five platforms.

### Changed

**Platform templates**:
- **Batched clarifying-questions rule** applied to all 5 platform base templates (`base-claude.md`, `base-gemini.md`, `base-codex.md`, `base-cursor.md`, `base-opencode.md`) plus the global `CLAUDE.md`. Replaces the unbounded 4.6-era variant with the Opus 4.7 batched-first-turn variant: ambiguous requirements must surface multiple interpretations + acceptance criteria in one round-trip instead of one-question-per-turn ping-pong.

**Opus 4.7 behavioral skill extensions**:
- **`prompt-engineering`** (`catalog/skills/ai-development/prompt-engineering/SKILL.md`) - new `## Effort-Level Strategy` section (all 5 tiers, default rationale, escalation/de-escalation rules, anti-patterns, 8-row decision table) and new `## Opus 4.7 Practices` section (positive-examples-over-negative, explicit-tool-invocation, adaptive-thinking-without-fixed-budgets, first-turn-specification-checklists).
- **`ai-agent-development`** (`catalog/skills/ai-development/ai-agent-development/SKILL.md`) - new `## Anti-Patterns (Opus 4.7)` table (fixed thinking budgets, excessive tool-calling as "thorough investigation", `max` effort on extended runs) mirroring the existing Common Rationalizations pattern.
- **`multi-agent-coordinator`** (`catalog/skills/orchestration/multi-agent-coordinator/SKILL.md`) - new `### Step 0: Should I delegate to a subagent?` section with the "will I need this tool output again?" reuse test and three worked delegation patterns; Pattern A "Opus 4.7 behavior - explicit fan-out required" callout with three concrete fan-out prompt templates (research, code generation, verification).
- **`context-compression`** (`catalog/skills/orchestration/context-compression/SKILL.md`) - new `#### Proactive steering with /compact focus on X, drop Y` subsection inside Step 2 with six directly-usable directives and `/clear` vs `/compact` guidance.
- **`context-degradation`** (`catalog/skills/orchestration/context-degradation/SKILL.md`) - 1M-token window Lost-in-Middle calibration table in Step 1 (Green/Yellow/Orange/Red at 100k/300k/500k boundaries) with task-dependency caveat; Step 2 cross-link added to proactive-steering and SESSION_LIFECYCLE_DECISIONS.
- **`session-history`** (`catalog/skills/workflow/session-history/SKILL.md`) - new "Summarize from here (mid-session handoff)" operating mode with purpose, trigger, 4-step usage pattern, and paste-ready handoff template.

**Guides**:
- **`guides/TOKEN_OPTIMIZATION.md`** - new "When NOT to compact" subsection under Auto-Compaction covering the bad-compact failure mode, three recognition signals (70-80% capacity on long task; mid-tool-use chain; recently loaded large files still needed), proactive `/compact focus on X, drop Y` remedy, and `/clear` vs `/compact` decision.
- **`guides/CLAUDE_CODE_SETTINGS_REFERENCE.md`** - Effort Levels table expanded from 3 tiers to the full 5 (xhigh / high / max / medium / low) with `high` marked as the v0.9.7 shipped default and `xhigh` reframed as an escalation option.

**Security command**:
- **`/run-penetration-test`** (`catalog/commands/run-penetration-test.md`) - "Attack Paths" renamed to "Attack Paths / Chains" in the report template with expanded narrative on exploit-chain composition. New `### Secure Design Recommendations` subsection between per-finding remediation and the project-wide Roadmap (architectural patterns: centralize authorization, typed query layer, server-authoritative state machine, constant-time comparators, idempotency middleware, CDN boundary hardening). WSTG Coverage Matrix expanded with WSTG-BUSL (business logic), cache poisoning, replay & token binding, and timing side channel rows - all gated on `--depth=deep`. Hunter agents default to shipped `effortLevel: high` (not `xhigh`) - parallel fan-out compounds cost; Phase 2 header cross-links to Effort-Level Strategy and multi-agent-coordinator explicit fan-out.
- **`catalog/skills/security/security-patch-advisor/SKILL.md`** - new `## Related Resources` footer cross-linking to the file-upload-security checklist and the two new security skills (previously had no "Related" section).

**Planning workflow generalization** (unrelated to Opus 4.7 adaptation but shipped in the same release):
- **`/generate-implementation-plan` renamed to `/generate-plan`** (`catalog/commands/generate-plan.md`) - scope broadened beyond v0.1.0 greenfield builds to cover feature additions, UX enhancements, refactors, and bug-fix campaigns. A plan-type selector (Initial Implementation / Feature / Refactor / Other) routes the discovery interview to either the full 11-question greenfield set or a shorter 7-question scope-focused set. Old command name preserved as a deprecation alias (`catalog/commands/generate-implementation-plan.md`).
- **Plan output path generalized to `docs/<version>/plans/<slug>.md`** - plans now live in a dedicated `plans/` subfolder per version instead of the hardcoded `docs/v0.1.0/implementation-plan.md`. Version resolves from git tags, CHANGELOG.md, or package manifests (falling back to `v0.1.0`). Filename slug auto-suggested from a one-sentence scope statement; collision handling via `<slug>-2`, `<slug>-3`.
- **`/implement-phase` discovery updated to match the new layout** (`catalog/commands/implement-phase.md`) - searches `docs/**/plans/*.md` as primary location and `docs/**/implementation-plan.md` as legacy fallback. Supports `/implement-phase <slug>`, `/implement-phase <path/to/plan.md>`, `/implement-phase <slug> <phase>` in addition to version-only and phase-only forms.
- **`setup-project` Phase 9** invokes `/generate-plan` (plan type 1) instead of `/generate-implementation-plan`; advertises `docs/v0.1.0/plans/v0.1.0-initial.md` as the default output path.
- **`generate-session-history`** plan-file discovery searches both new and legacy layouts.
- **`implementation-plan` skill** (`catalog/skills/workflow/implementation-plan/SKILL.md`) - frontmatter description, overview, question-set header, and quality checklist updated for the broader plan-type coverage and the new output path. Version bumped to 1.1.0.

### Fixed

- **Correction (v0.9.6 CHANGELOG)** - the v0.9.6 entry line stating the installer `effortLevel` default was changed to `high` was inaccurate; v0.9.6 actually shipped `xhigh` (matching the then-current `catalog/hooks/settings.json` template and `scripts/installer.ps1` fallback). The v0.9.6 entry has been rewritten to describe the actual v0.9.6 shipped behavior. v0.9.7 keeps the shipped default at `xhigh`.

### Deferred

- **VS Code extension effort-level integration** (planned Phase 5) - shipped as a documentation roadmap in the `claude-usage-monitor` extension README rather than as the originally planned `markdownDescription` hover-help integration. Two upstream blockers remain unresolved in Claude Code as of April 2026: (a) the statusline hook JSON does not carry the current effort level (tracked in `anthropics/claude-code#31415`), so an extension cannot reliably observe mid-session `/effort` changes; (b) edits to `~/.claude/settings.json` do not propagate live to running sessions (tracked in `anthropics/claude-code#17127`), so auto-switching by usage band cannot take effect without a session restart. The configured-value display and usage-banded auto-switch features are documented as roadmap items in the extension README and will be reconsidered when the upstream primitives exist. See [docs/v0.9.7/development/history/2026-04_phase-5-vscode-extension-deferred.md](docs/v0.9.7/development/history/2026-04_phase-5-vscode-extension-deferred.md) for full context including the research refresh addendum.

---

## [0.9.6] - 2026-04-14

### Added
- **Command classification normalization** (`format-bash-description.py`) - four new normalization passes: git global option stripping (`-C`, `--no-pager`, `--git-dir`, `-c key=val`), absolute binary path stripping (`/usr/bin/head` matches `head`), prefix command unwrapping (`env`, `time`, `command`, `nice`), and subshell/brace group handling with recursive inner command checking
- **115 new Claude Bash patterns** (`claude-permissions.json`) - macOS tools (sw_vers, xcrun, mdfind, defaults read), Linux tools (free, lscpu, ip, ss, systemctl status, journalctl), package manager introspection (npm/pip/yarn/pnpm/go/rust/dotnet/java), Docker read-only (ps, images, logs, inspect), and GitHub CLI read-only (pr/issue/run/release list/view)
- **123 new Gemini shell command patterns** (`gemini-permissions.json`) - same expanded categories translated to `run_shell_command()` format for cross-platform parity
- **Classification audit test suite** (`test_classification_audit.py`) - 160 edge cases across 18 categories covering all platforms (macOS, Linux, Windows), git global options, compound commands, subshells, prefix wrappers, and absolute paths

### Changed
- **Installer sentinel checks** - Claude sentinel updated from `api.github.com` to `gh pr list`; Gemini sentinel updated from `ReadFileTool` to `docker ps` -- existing installations now pick up the new patterns on re-install

### Fixed
- **Settings panel thresholdMetric persistence** (`settingsPanel.ts`) - replaced `Promise.all` with sequential `config.update()` calls to eliminate race condition where concurrent writes to the same settings file caused the metric value to be silently lost; added post-save confirmation via `loadSettings` message and removed the optimistic update in the webview `onSave()` handler
- **Installer effortLevel default** - installer writes `effortLevel: xhigh` to generated user settings, matching the shipped `catalog/hooks/settings.json` template and aligning with current Opus 4.7 best-practice guidance

---

## [0.9.5] - 2026-04-10

### Added
- **`generate-todos` command** - bootstraps `docs/todos.md` for inherited projects by analyzing git history, existing docs, and code annotations, then writing a structured progress tracker (`catalog/commands/generate-todos.md`)
- **claude-usage-monitor Settings Panel** - new `Claude Usage: Settings` command and webview UI for configuring urgency thresholds, status bar colors, and threshold metric without editing `settings.json` directly

### Changed
- **claude-usage-monitor extension (v0.4.0)** - urgency thresholds (moderate/high/critical) and status bar colors are now fully user-configurable via VS Code settings (`claudeUsage.thresholds.*`, `claudeUsage.colors.*`) or through the new settings panel; `claudeUsage.thresholdMetric` setting controls which usage metric is evaluated against the thresholds

### Fixed
- SC2088 tilde expansion and missing trailing newline in hook/CI scripts

---

## [0.9.4] - 2026-04-07

### Added
- **`dev-progress-tracker` skill** - new workflow skill (`catalog/skills/workflow/dev-progress-tracker/SKILL.md`) that maintains `docs/todos.md` as a living project progress tracker across sessions and AI platforms; includes session-start read behavior, task checkbox management, dashboard metrics, sprint roadmap structure, and functionality matrix template (184 total skills)
- **`catalog/hooks/commit-msg`** - new git commit-msg hook that silently auto-replaces Unicode punctuation (em-dashes, en-dashes, curly quotes, ellipsis, arrows) with ASCII equivalents at commit time, preventing CP1252 encoding corruption on Windows
- **Global commit-msg hook deployment** - `install_git_commit_msg_hook` (bash) and `Install-GitCommitMsgHook` (PowerShell) added to both installers; copies the hook to `~/.git-templates/hooks/` and sets `git config --global init.templateDir` so all future repos on the machine inherit it automatically

### Changed
- **All 5 platform base templates** (`base-claude.md`, `base-gemini.md`, `base-codex.md`, `base-cursor.md`, `base-opencode.md`) - added two new cross-platform rules: ASCII-only commit messages and `docs/todos.md` progress tracking convention; both rules are now distributed to Claude, Gemini, Codex, Cursor, and OpenCode instruction files at install time
- **`generate-commit-message` command** and **`code-commit-workflow` skill** - added explicit ASCII encoding requirement to body formatting rules, quality checklist, and verification items
- **`format-bash-description.py`** and **`session-start.sh`** - replaced Unicode punctuation in comments with plain ASCII hyphens; updated version display; corrected file permissions
- **Guides** (`CLAUDE_CODE_PROJECT_SETUP.md`, `SUBAGENTS_GUIDE.md`) - replaced stale `ai-templates` references with `DevAI-Hub`; updated version footer
- **Skill count**: 183 -> 184

### Fixed
- Non-ASCII characters (em-dashes, en-dashes, curly quotes) in commit messages causing CP1252 mojibake on Windows (e.g., `--` appearing as `â€"`)
- Missing final newlines in `data/marketplace.json` and `data/skills.json`
- Permissions configuration, stale documentation references, and installer sync issues (issues #1-#4)

---

## [0.9.3] - 2026-04-06

### Added
- **9 new skills**: `idea-refine`, `spec-driven-development`, `incremental-implementation`, `context-engineering`, `frontend-ui-engineering`, `browser-testing-with-devtools`, `code-simplification`, `shipping-and-launch`, and `using-devai-hub` (meta-skill) — closing SDLC coverage gaps identified in the agent-skills comparison (183 total skills)
- **`wrap-up-session` command**: 7-phase session close-out workflow covering session history capture, gitignore hygiene, documentation sync, devlog update, memory refresh, version assessment, and commit message generation (`/wrap-up-session` or `/wrap-up-session --quick`)
- **SessionStart hook**: `catalog/hooks/session-start.sh` auto-loads the `using-devai-hub` meta-skill at every new session to guarantee skill catalog awareness; registered in `catalog/hooks/settings.json`
- **`AGENTS.md`**: Comprehensive guidance document for AI coding agents contributing to DevAI-Hub — documents project structure, skill anatomy requirements, and registration workflow
- **4 reference checklists**: API design, architecture, security, and testing patterns (`catalog/checklists/`)
- **Plugin marketplace manifests**: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for one-command Claude Code plugin distribution
- **Cross-project comparison report**: 12-section analysis of DevAI-Hub vs. agent-skills with adoption roadmap (`docs/v0.9.2/comparison-agent-skills.md`)

### Changed
- **Skill anatomy**: Added Common Rationalizations tables and binary Verification checklists to 19 priority skills (ai-agent-development, prompt-engineering, api-design, architecture-design, bug-localization, semantic-bug-detector, behavior-preservation-checker, code-quality, intent-based-review, security-review, cicd-architect, observability-setup, authentication-patterns, dependency-security-audit, integration-test-generator, unit-tests, code-commit-workflow, plan-before-code, test-driven-development)
- **Permissions**: Expanded `configs/permissions/claude-permissions.json` bash allowlist with 40+ additional safe tool patterns (binary inspection: `od`, `hexdump`, `xxd`, `strings`; checksums: `sha256sum`, `sha1sum`, `md5sum`; archive listing: `tar -tf`, `unzip -l`; system info: `uptime`, `hostname`, `id`)
- **Hook tests**: Added 61 new test cases to `catalog/hooks/tests/test_format_bash_description.py` covering expanded allowlist patterns and pipeline regression cases
- **Infrastructure docs**: Overhauled `infrastructure/tools/README.md` with current project metrics; fixed stale version footers in `infrastructure/hooks/README.md` and `infrastructure/integrations/README.md`
- **VS Code extension**: Removed emoji from usage-monitor notification messages for cross-platform compatibility
- **Skill count**: 175 → 183
- **Hook count**: 12 → 13

---

## [0.9.2] - 2026-04-06

### Added
- **`generate-implementation-plan` Command**: New command (`catalog/commands/generate-implementation-plan.md`) that generates a structured, phased implementation plan from a task description or requirement
- **`implement-phase` Command**: New command (`catalog/commands/implement-phase.md`) for executing a single named phase from an implementation plan with scoped context
- **`implementation-plan` Skill**: New workflow skill (`catalog/skills/workflow/implementation-plan/`) with OpenAI agent integration for structured planning workflows
- **Hook Test Suite**: Comprehensive test suite (`catalog/hooks/tests/test_format_bash_description.py`, 763 lines) covering the Bash description formatting hook edge cases and approval flows

### Changed
- **Permission configuration**: Expanded `configs/permissions/claude-permissions.json` with additional bash tool allowlist entries
- **Skill index**: Updated `data/SKILL_INDEX.md` to include the new `implementation-plan` skill (175 total skills)
- **Setup project command**: Minor updates to `catalog/commands/setup-project.md`

---

## [0.9.1] - 2026-04-03

### Fixed
- **Bash description hook**: Enforce strict 2-case approval flow and expand bash tool allowlist in `format-bash-description.py`
- **Bash description hook**: Make description box conditional on permission allow list in `format-bash-description.py`
- **Require-description hook**: Fix shell-construct parsing bug in `require-description.sh`
- **VS Code extension**: Rewrite auto-switch to use `settings.json` instead of deprecated API, fixing repeated notifications
- **VS Code extension**: Suppress 50% and 75% usage notifications when usage exceeds 90% threshold
- **VS Code extension**: Fix usage monitor store and type definition bugs (`types.ts`, `usageStore.ts`, `dashboardPanel.ts`)

---

## [0.9.0] - 2026-03-26

### Added
- **12 new specialist skills**: Astro, Svelte, Vue experts (framework-specialists); Android/iOS development, DOCX/XLSX/PPTX/PDF generation, GIF/sticker maker, GLSL shader development (specialized-domains); session-history workflow (174 total skills)
- **Permission configuration system**: `configs/permissions/` with profiles for Claude, Codex, Copilot, Gemini plus `trusted-domains.json`; new `Install-DevAI-Permissions.ps1` installer
- **Auto-switcher module**: `autoSwitcher.ts` for automatic model/plan switching in VS Code usage monitor
- **Bash description hook**: `format-bash-description.py` PreToolUse hook for automatic description formatting
- **Skill validation**: `scripts/validate_skills.py` for automated SKILL.md structure validation
- **IDE templates**: New instruction templates for Cursor (`base-cursor.md`) and OpenCode (`base-opencode.md`)
- **Chinese documentation**: `README_zh.md` with full translation
- **Marketplace metadata**: `data/marketplace.json` for plugin registry compatibility
- **React expert references**: 4 reference docs (dependency injection, data fetching, performance, testing patterns)

### Changed
- **Session history command**: Replaced `generate-dev-history.md` with `generate-session-history.md`
- **Setup project command**: Overhauled with expanded detection and configuration
- **Dashboard panel**: Enhanced with improved visualizations and session management types
- **Hook settings**: Updated `settings.json` and `require-description.sh`
- **Skills catalog**: `data/skills.json` rebuilt with 174 skills (was 162)
- **Installer scripts**: Both `installer.ps1` and `installer.sh` upgraded with permission installation support

---

## [0.8.9] - 2026-03-23

### Added
- **Tiered Skill Summaries**: Added `summary_l0` and `overview_l1` frontmatter to all 162 SKILL.md files for hierarchical skill discovery
- **MCP Skill Server**: New `devai-skill-server` Python extension with keyword search, category browsing, and bundle tools (`extensions/devai-skill-server/`)
- **Compiled Skill Index**: Generated `data/SKILL_INDEX.md` for `{{SKILL_INDEX}}` template injection
- **Skill Discovery Integration**: Added Skill Discovery section with `{{SKILL_INDEX}}` placeholder to all AI instruction templates
- **Build Tooling**: Added `Makefile`, `LICENSE` (MIT), and `.pr_agent.toml`
- **Pre-commit Hooks**: Added shellcheck and commitizen hooks to `.pre-commit-config.yaml`
- **OpenViking Comparison Report**: Added `docs/v0.8.8/comparison-OpenViking.md`

### Changed
- **Release Orchestrator**: Restructured `update-version` command from linear steps into five-phase orchestrator (A-E) with user confirmation gates and sub-command delegation
- **Skills Catalog Rebuilt**: `data/skills.json` rebuilt with L0/L1 summary fields and nested category/skill directory structure
- **Build Script Enhanced**: `build_skills_catalog.py` updated for nested directory structure and tiered summary extraction
- **Installer Scripts Updated**: Both `installer.ps1` and `installer.sh` updated for new catalog structure
- **MCP Server Registration**: Registered `devai-skill-server` in `catalog/mcp-configs/mcp-servers.json`

---

## [0.8.8] - 2026-03-20

### Added
- **`require-description` Hook**: New PreToolUse hook (`catalog/hooks/require-description.sh`) that enforces bordered description blocks on all Bash, Cmd, and PowerShell commands; blocks execution (exit 2) when the block is absent
- **20 New Specialist Skills**: Language specialists (C++, C#, Java, JavaScript, PowerShell, Python, TypeScript), infrastructure (Azure infra engineer, network engineer, platform engineer, SRE engineer), orchestration (error-coordinator, multi-agent-coordinator), business-product (business-analyst, scrum-master, product-manager, technical-writer), and specialized-domains (fintech-engineer)
- **18 Category README Files**: Every `catalog/skills/` subdirectory now has a README with skill listings and descriptions
- **`CONTRIBUTING.md`**: New contribution guide covering skills, commands, hooks, agents, and templates
- **Codex Subagents Comparison Report**: Added `docs/v0.8.7/comparison-awesome-codex-subagents.md`

### Changed
- **Skills Catalog Rebuilt**: `data/skills.json` rebuilt to match all 162 on-disk skills (added 7 missing entries, removed 4 misplaced command entries, sorted by category then name)
- **Documentation Synced**: Updated `catalog/skills/README.md` (47 to 162 skills, 8 to 20 categories), root `README.md` (134 to 162 skills, added Codex support and component counts), and `extensions/claude-usage-monitor/README.md` (corrected defaults and removed ghost settings)
- **Hook Format**: Standardized description-block hook to wider no-pad format

### Fixed
- **Usage Monitor**: Default model updated from Sonnet to Opus 4.6
- **Extension README**: Corrected refresh interval default (15 to 10 min), removed non-existent `currentModel` setting and `Manual Update` command
- **Root README**: Skill count corrected from 134 to 162 with component counts (29 Commands, 11 Hooks, 10 Agents)

---

## [0.8.7] - 2026-03-16

### Added
- **`run-security-audit` Command**: New command (`catalog/commands/run-security-audit.md`) that performs a comprehensive 9-phase security audit covering secrets, git hygiene, installer security, input validation, auth/authz, dependency CVEs, configuration hardening, and dangerous code patterns; includes an active remediation loop (`--fix`) that applies fixes in P0→P3 priority order and re-audits until clean
- **`commands-cheatsheet` Command**: New command (`catalog/commands/commands-cheatsheet.md`) that discovers all global and project slash commands, groups them by logical category, and renders a live Markdown cheatsheet table with descriptions and usage examples
- **`update-gitignore` Command**: New command (`catalog/commands/update-gitignore.md`) that audits `.gitignore` against the codebase using a G0–G3 severity scale, identifies wrongly-tracked files and missing patterns, and applies cleanup and Git LFS recommendations after explicit user confirmation

### Changed
- **AI Instruction Templates**: Added mandatory file-access explanation rule (every Read, Glob, and Grep call must be preceded by a one-sentence plain-language explanation) to `templates/ai-instructions/base-claude.md`, `base-codex.md`, `base-gemini.md`, and all four project example CLAUDE.md files

---

## [0.8.6] - 2026-03-13

### Added
- **10 Specialist Agents**: New agent definitions in `catalog/agents/` covering architect, build-error-resolver, code-reviewer, doc-updater, harness-optimizer, loop-operator, planner, refactor-cleaner, security-reviewer, and tdd-guide roles; installable via the Phase 4 installer step
- **Language Rule Sets**: New coding-style, security, and testing rules for Bash, Go, Python, and TypeScript in `catalog/rules/`, installable via the Phase 4 installer step
- **MCP Server Configs**: New `catalog/mcp-configs/mcp-servers.json` with curated MCP server definitions installable via Phase 4
- **5 New Skills**: `ai-billing-safeguards`, `claude-agent-sdk`, `multi-provider-ai`, `project-layout-refactor`, and `temporal-orchestration` added to the catalog
- **4 New Commands**: `refactor-project-layout`, `run-penetration-test`, `tdd`, and `continue-session` added to the catalog
- **5 New Hook Profiles**: `auto-format-on-write.sh`, `large-file-guard.sh`, `lint-on-write.sh`, `notify-on-complete.sh`, and `session-summary.sh` added to `catalog/hooks/`
- **Project Examples**: Four real-world `CLAUDE.md` examples added in `examples/` (Django API, Go microservice, Next.js SaaS, Rust API) for reference during workspace setup
- **Token Optimization Guide**: New `guides/TOKEN_OPTIMIZATION.md` covering context window strategies and cost-reduction techniques

### Changed
- **Repository Layout**: Moved JSON catalog files (`skills.json`, `bundles.json`, `templates.json`, `workflows.json`, `report_data.json`) from the repo root to `data/`, and moved `DEVLOG.md` from root to `docs/`, enforcing the documented layout rules
- **Installer Phase 4**: Updated `scripts/installer.ps1` to install agents, language rules, and MCP server configs alongside the VS Code extension; added hook-profile selection step
- **Usage Monitor Poll Interval**: Increased the default `claudeUsage.refreshInterval` from 5 to 10 minutes to reduce API call frequency

### Fixed
- **Claude Code Logout Bug**: Removed `scripts/claude-auth-monitor.ps1` and its Windows Task Scheduler integration; the 2-minute external token-refresh schedule was racing with Claude Code's own OAuth refresh, invalidating one-time-use refresh tokens and causing multiple forced logouts per day
- **Installer Header Style**: Replaced `Write-CenteredBanner` calls with plain `Write-Host` headers in `scripts/installer.ps1` for cleaner phase output

### Removed
- **Auth Monitor**: `scripts/claude-auth-monitor.ps1` and `scripts/claude-auth-automate.ahk` removed; the VS Code extension's built-in token refresh handles all OAuth token renewal

---

## [0.8.5] - 2026-03-10

### Added
- **Auto-Devlog Hook**: New `infrastructure/hooks/auto-devlog.sh` stop hook that prepends a git-summary entry to `DEVLOG.md` at session end; opt-in via `AUTO_DEVLOG=1`, with optional AI enrichment via `AUTO_DEVLOG_AI=1`
- **Generate Dev History Command**: New `generate-dev-history` command (`catalog/commands/generate-dev-history.md`) that reconstructs full project history organized by implementation phase from session logs, git history, DEVLOG.md, CHANGELOG.md, and planning docs
- **Extra Credits Dashboard**: Extra credits progress bar and dollar amounts displayed in the usage monitor dashboard panel, tracking consumption against the monthly extra-credits limit
- **1M Context Warnings**: Info banner in the dashboard and tooltip in the status bar warning users on 1M extended-context models about extra credit consumption

### Changed
- **OAuth Token Auto-Refresh**: Usage monitor now refreshes the OAuth access token automatically on expiry and on 429 rate-limit responses, replacing hard failure with seamless re-authentication; adds `token-refresh-failed` error code if refresh itself fails
- **Extra Credits Display Fix**: Corrected credit amounts by dividing `monthly_limit` and `used_credits` by 100 (API returns cents, display now shows dollars); reset label changed from static "monthly" to "on Month Day" computed from next first-of-month date
- **Model Recommendations**: Fixed default model classification so "default" is treated as Sonnet (not Opus) in switch recommendations; added Sonnet-as-default guidance when all usage levels are healthy and user is not already on Sonnet
- **Model Name Display**: `formatModelName` now returns "Default (Sonnet)" instead of "Default" for the default model ID, making the active model unambiguous in the dashboard

### Fixed
- **Bash Installer Prompts**: Redirected `read_prompt` display text to stderr so prompts are visible when the function is called inside `$(...)` command substitution; same fix applied to the language selection menu
- **Bash Installer Error Handling**: Replaced standalone npm/code commands followed by `$?` checks with `if ! <command>` pattern so `set -e` does not exit the script before the error handler fires
- **Fetch Timeout**: Added 30-second `AbortController` timeout to all API fetch calls in `usageFetcher.ts` to prevent indefinitely hung requests
- **In-Flight Fetch Guard**: Fixed stale UI state — when a fetch is already in progress, the status bar and dashboard now still refresh with the latest available data instead of silently skipping the update

---

## [0.8.4] - 2026-03-09

### Changed
- **Usage Monitor: Dynamic Model Detection**: Replace the manual `claudeUsage.currentModel` VS Code setting with automatic detection from `claudeCode.selectedModel` (Claude Code's own model picker); eliminates the need for users to keep a separate setting in sync
- **Usage Monitor: Open Model ID Support**: Replace `ClaudeModel` union type and static `MODEL_DISPLAY_NAMES` map with `formatModelName()` which parses any model ID string, including `[1m]` extended-context suffix variants; adds `baseModelId()` and `is1MContext()` helpers
- **Usage Monitor: 1M Context Recommendation**: New recommendation rule that fires when session usage is high while the user is on a `[1m]` extended-context variant, suggesting they switch to the standard context model for non-large-file tasks
- **Usage Monitor: Live Model Switch Response**: Extension now listens for `claudeCode.selectedModel` configuration changes and refreshes the status bar and dashboard immediately when the user switches models in Claude Code

### Removed
- **`claudeUsage.currentModel` Setting**: Removed the manual model selection setting from the extension's VS Code configuration (superseded by automatic detection from `claudeCode.selectedModel`)

---

## [0.8.3] - 2026-03-06

### Added
- **Context Optimization Skill**: New `context-optimization` skill (`catalog/skills/context-optimization/SKILL.md`) for managing token budgets, pruning irrelevant context, and applying structured context engineering patterns
- **Search Skills Command**: New `search-skills` command (`catalog/commands/search-skills.md`) for keyword, category, and role-based skill discovery from the Hub catalog
- **OAuth Token Refresh**: Usage monitor now refreshes the OAuth access token automatically before each API call, reading from `~/.claude/.credentials.json` to prevent stale-token 401 errors
- **Live Dashboard Auto-Polling**: Dashboard panel polls the usage API on a configurable interval without requiring manual refresh; added refresh indicator showing last-updated timestamp
- **LLMs.txt**: Added `llms.txt` LLM crawler manifest (139 lines) for structured discovery of the Hub's content by AI crawlers
- **RTK Context Compression Guide**: New `guides/RTK_CONTEXT_COMPRESSION.md` documenting automated context compression with Rust/cargo
- **Governance Files**: Added `CODE_OF_CONDUCT.md` and `SECURITY.md` to the repository root
- **v0.8.2 Design Docs**: Added `docs/v0.8.2/comparison-context-hub.md`, `docs/v0.8.2/content-guide.md`, and `docs/v0.8.2/design.md`

### Changed
- **Usage Monitor Refactored**: Extracted `usageFetcher.ts` module, removed `inputCollector.ts` (manual credential input eliminated), streamlined `extension.ts` (-121 lines), and enhanced `statusBarManager.ts` with live refresh indicator
- **AI Instruction Templates**: Added output minimization rules (suppress verbose progress bars, prefer `--quiet` flags, summarize long output) to `base-claude.md`, `base-codex.md`, and `base-gemini.md`
- **Skills Registry**: Updated `skills.json` with new skill entries

---

## [0.8.2] - 2026-03-05

### Added
- **Catalog Expansion**: 40 new skills growing catalog from 94 to 134 across 17 categories, with a new Bug Fixing category (5 skills: bug-localization, bug-to-patch-generator, regression-root-cause-analyzer, bug-reproduction-test-generator, semantic-bug-detector)
- **Bug Hunter Bundle**: New role-based bundle targeting systematic bug diagnosis, reproduction, and root-cause analysis workflows
- **7 New Workflows**: cross-model-orchestration, research-plan-implement, token-optimization, intent-based-code-review, adversarial-code-review, competitive-implementation, progressive-delivery
- **Hooks Catalog**: 6 new hook templates — PreToolUse secret-scan, large-file-guard, escalation-trigger on Write/Edit; PostToolUse auto-format-on-write, lint-on-write; Stop session-summary, notify-on-complete
- **Codex AGENTS.md Support**: Both installers now render AGENTS.md from base-codex.md template and install commands to prompts/ directory (compatible with Codex, Jules, Cursor, Aider)
- **Custom Agent Configuration Guide**: New section in SUBAGENTS_GUIDE.md covering YAML frontmatter fields, memory scopes (user/project/local), and command-agent-skill orchestration pattern

### Changed
- **Role Bundles Enriched**: Existing AI Engineer, DevOps, Security Specialist, QA Engineer, and Tech Lead bundles expanded with newly cataloged skills
- **Usage Monitor Reliability**: Overhaul of FetchError (now typed object with code/statusCode/statusText), fetch retry with exponential backoff for 429 and 5xx, rate-limit suppression, stale data indicator (warning badge + tooltip), concurrency guard, urgency escalation notifications
- **Refresh Interval**: Default lowered from 15 min to 5 min, minimum from 5 to 1 min
- **Installer UI**: Added Write-CenteredBanner helper and Restore-Title calls in PS1 installer after npm/robocopy operations

### Fixed
- **Commit Message Templates**: Strengthened no-hard-wrap rule to MANDATORY with no exceptions in base-claude.md, base-gemini.md, and commit-related templates

---

## [0.8.1] - 2026-03-04

### Fixed
- **AI Output Formatting**: Added no-hard-wrap rule to base templates (base-claude.md, base-gemini.md) and all 7 coding-instructions templates, preventing ~80-character line breaks that don't reflow with window width in plans, PR descriptions, and other output

---

## [0.8.0] - 2026-03-03

### Added
- **Architecture Skills** (new category, 5 skills): `architecture-design`, `ddd-strategic-design`, `api-design`, `microservices-patterns`, `event-driven-architecture`
- **AI Development Skills** (new category, 3 skills): `ai-agent-development`, `rag-implementation`, `prompt-engineering`
- **Framework Specialist Skills** (new category, 3 skills): `react-expert`, `nextjs-expert`, `fastapi-expert`
- **Infrastructure Skills** (4 new): `database-design`, `data-pipeline-design`, `observability-setup`, `containerization`
- **Testing Skill**: `e2e-testing-automation` for Playwright/Cypress browser automation with page objects, visual regression, and CI integration
- **Security Skill**: `authentication-patterns` for OAuth 2.0, OIDC, JWT, session management, MFA, and passkeys
- **Developer Experience Skills** (2 new): `async-patterns`, `graphql-development`
- **Skill Bundles**: `bundles.json` with 10 role-based skill collections (Core Developer, Frontend Engineer, Backend Engineer, AI Engineer, Architect, DevOps Engineer, Security Specialist, Compliance Auditor, QA Engineer, Tech Lead)
- **Workflow Definitions**: `workflows.json` with 10 goal-based workflows (Full Code Review, Security Audit, New Project Setup, API Development, Release Preparation, Legacy Modernization, AI Agent Pipeline, Compliance Assessment, Test Coverage Boost, Production Readiness)

### Changed
- **Skills Registry**: `skills.json` updated from 75 to 94 skills across 16 categories (3 new categories added)
- **README.md**: Updated skill count and featured skills table with Architecture, AI, and E2E highlights

### Fixed
- **Commit Message Templates**: Removed "Wrap at 72 characters" body rule from `code-commit-workflow` skill and `generate-commit-message` command; replaced with single-line bullet point rule

---

## [0.7.1] - 2026-03-03

### Fixed
- Removed conflicting `Co-authored-by` example from `code-commit-workflow` skill footer; replaced with trailer metadata guidance
- Added explicit "no AI attribution" prohibition to `generate-commit-message` command, `code-commit-workflow` skill, and all instruction templates (Claude, Gemini, generic)
- Added "Shell Command Clarity" rule to `base-claude.md`, `base-gemini.md`, and `generic-instructions.md` templates

---

## [0.7.0] - 2026-02-27

### Added
- **Context Engineering Skills**: 5 new skills adapted from [Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) (MIT License):
  - `context-degradation` (Orchestration): Detect and mitigate context quality decay with 5 degradation patterns and 4-bucket mitigation approach
  - `context-compression` (Orchestration): Minimize tokens per task with anchored summarization, observation masking, and session handoff procedures
  - `tool-design` (Developer Experience): Design effective tools/APIs for AI agents (MCP servers, slash commands) with description engineering and consolidation principles
  - `filesystem-context-patterns` (Workflow): 6 filesystem patterns for agent context management (scratch pad, plan persistence, sub-agent communication, dynamic skill loading, terminal persistence, self-modification)
  - `ai-output-evaluation` (Developer Experience): LLM-as-judge evaluation with multi-dimensional rubrics, bias mitigation, and token economics
- **Developer Experience Skills**: 3 new skills: `writing-editing`, `analysis-logic`, `creative-generation`
- **Coding Snippets**: `templates/ai-instructions/coding-snippets/` directory for Copilot instruction assembly with per-language convention files
- **Template Rendering System**: `base-claude.md` and `base-gemini.md` with `{{PLACEHOLDER}}` substitution for project-specific CLAUDE.md/GEMINI.md generation
- **Generate Report Style Guide Command**: `catalog/commands/generate-report-style-guide.md` for report quality metrics and style enforcement
- **Report Generator Enhancements**: Template-aware rendering, PRE-TOC marker support, Mermaid diagram detection, companion PPTX generation from Word reports

### Changed
- **context-manager** (v1.1.0): Added Step 0 with context fundamentals (5-component model, attention budget, progressive disclosure, 70-80% compaction trigger)
- **task-coordinator** (v1.1.0): Added multi-agent coordination patterns (supervisor, swarm, hierarchical), token multiplier economics, and handoff protocol template
- **plan-before-code** (v1.1.0): Added Step 0 with LLM task suitability assessment, token cost estimation template, and 5-stage pipeline model
- **Installer Overhaul**: `Render-Template` replaces static CLAUDE.md/GEMINI.md copy; auto-detects project metadata (language, package manager, build tool, test framework). Installer bumped from V8 to V9.
- **Generate Report Command**: Renamed from `generate-word-report` to `generate-report` with 6-step synthesis-first workflow replacing Phase 4
- **Skills Registry**: `skills.json` updated from 66 to 75 skills; `CATALOG.md` updated to v1.3.0
- **Legacy Templates**: Moved old `coding-instructions/` to `templates/ai-instructions/legacy/`; deprecated `generic-instructions.md` in favour of `base-gemini.md`

### Fixed
- **Report Generator**: GFM table parsing, horizontal rule handling, Mermaid code block placeholders, `_strip_first_h1()` for title page extraction, companion PPTX generation pipeline
- **Templates**: Fixed tab-corrupted paths and em-dash encoding across 7 language templates

---

## [0.6.3] - 2026-02-20

### Added
- **Generate Word Report Command**: `catalog/commands/generate-word-report.md` produces professional Word (.docx) and PowerPoint (.pptx) documents from Markdown files with template discovery, content analysis, and structured output to `docs/<version>/reports/` or `docs/<version>/presentations/`.
- **Generic Report Types**: `scripts/generate_report.py` now supports `--type generic-word` and `--type generic-pptx` with `--md-files`, `--title`, `--subtitle`, `--template`, and `--output` arguments. Existing codebase/code-review types unchanged.
- **PowerPoint Generation**: `python-pptx` integration maps H1 headings to section divider slides, H2 headings to content slides, bullet points to body text, and code blocks to monospace text boxes with gray backgrounds.
- **Installer Phase 4**: Templates and report generator installation to `~/.devai-hub/`. Includes native file picker dialog (Windows) for importing custom `.docx`/`.pptx` templates with import loop.
- **Bundled Template**: `templates/documentation/generic-word-report-template.docx` serves as the default Word report template.

### Changed
- **Installers**: Version bumped from V7 (v0.6.2) to V8 (v0.6.3). Added `Install-Templates` (PS1) and `install_templates` (Bash) functions as Phase 4.

### Fixed
- **Report Generation**: `add_markdown_paragraph()` no longer crashes on empty lines inside Markdown code blocks (IndexError on `p.runs[0]`).
- **Installer**: Stale files at destination are now removed during overwrite to prevent orphaned artifacts.

---

## [0.6.2] - 2026-02-19

### Added
- **Usage Display Stop Hook**: `catalog/hooks/usage-display.sh` shows color-coded CLI usage limits (session, weekly, Sonnet-only) after each Claude Code response when any metric exceeds 50%. Fetches from Anthropic OAuth API with 5-minute caching and 3-second timeout. Fails silently when dependencies or credentials are unavailable.
- **Generate Changelog Command**: `catalog/commands/generate-changelog.md` reconstructs a full CHANGELOG.md from git tags, commit messages, and history following Keep a Changelog format.
- **Review Codebase Command**: `catalog/commands/review-codebase.md` replaces `run-code-review` with a comprehensive senior-level review producing structured findings, remediation roadmap, and test coverage analysis.
- **Hook Config Template**: Updated `catalog/hooks/settings.json` with Stop hook entry for usage-display alongside existing PreToolUse (git guardrails).
- **Usage Display Documentation**: Added "Usage Display (Stop Hook)" section to `infrastructure/hooks/README.md` with configuration, customization, and graceful degradation details.

### Changed
- **Installers**: Both `scripts/installer.ps1` and `scripts/installer.sh` now install the usage-display hook in both global (Phase 1) and workspace (Phase 2) phases via `Install-UsageDisplay` / `install_usage_display` functions. Version bumped from V6 (v0.6.1) to V7 (v0.6.2).
- **Check-Usage Command**: Enhanced with Phase 0 auto-fetch from Anthropic OAuth API before falling back to manual entry. Added cross-references to related monitoring features.
- **Update-Documentation Command**: Rewritten to focus exclusively on READMEs, guides, and manuals (excludes CHANGELOG/DEVLOG). Now discovers, compares against codebase, and updates files.
- **Update-Version Command**: Enhanced CHANGELOG step (Keep a Changelog format, footer links), richer DEVLOG entries, and new documentation update step (14 steps total). Renamed from `updated-version` to `update-version`.
- **Analyze-Codebase Command**: Rewritten with structured 12-section analysis and Mermaid diagram output.
- **Root README**: Restructured usage monitoring into 3 complementary features (CLI hook, VS Code extension, /check-usage).

### Removed
- **run-code-review.md**: Replaced by `review-codebase.md` with expanded scope.

---

## [0.6.1] - 2026-02-19

### Added
- **Git Guardrails PreToolUse Hook**: `catalog/hooks/git-guardrails.sh` blocks destructive git commands (force push, hard reset, clean -f, branch -D, checkout ., restore ., stash drop) before execution via Claude Code's PreToolUse mechanism.
- **Hook Config Template**: `catalog/hooks/settings.json` for automatic Claude Code integration with idempotent settings.json merging.
- **Tracer Bullets Workflow**: New workflow directive in AI instructions requiring agents to build a single, tiny end-to-end slice first before expanding (from *The Pragmatic Programmer*).
- **Git Safety Soft Enforcement**: Cross-platform `## Git Safety` section added to AI instruction templates for Gemini, Codex, and Copilot.
- **Git Guardrails Documentation**: Comprehensive section in `infrastructure/hooks/README.md` covering customization, verification, and disabling.

### Changed
- **Installers**: Both `scripts/installer.ps1` and `scripts/installer.sh` now install git guardrails hook in both global (Phase 1) and workspace (Phase 2) phases with JSON merge strategy for existing settings.
- **Report Generation**: Categorize dependencies by type and merge platform support data in `scripts/generate_report.py` and `catalog/commands/analyze-codebase.md`.

### Fixed
- **Report Generation**: Fix dependency categorization and issue grouping logic for codebase analysis reports.

---

## [0.6.0] - 2026-02-10

### Added
- **Claude Usage Monitor VS Code Extension**: Full VS Code extension (`extensions/claude-usage-monitor/`) for monitoring Claude Code API usage limits with auto-fetch, custom Claude icon in status bar, SVG data URI tooltips with theme-aware progress bars, full dashboard WebviewPanel, and manual input fallback. Includes custom icon font generator, theme-aware tab icons, and installer integration (Phase 3 in both `installer.ps1` and `installer.sh`).
- **New Commands**: `generate-readme`, `generate-devlog`, `check-usage`.
- **New Skill**: `devlog-generation` added to `catalog/skills/workflow/`.
- **Icon Assets**: `catalog/claude_icon.svg`, `catalog/claude_logo.png`.
- **Code Review Reference Checklists**: 4 standalone reference files (`solid-checklist.md`, `security-checklist.md`, `code-quality-checklist.md`, `removal-plan.md`) under `catalog/skills/code-review/references/`.

### Changed
- **Code Review System**: Merged `code-review-expert` methodology into `run-code-review` command (replacing `run-deep-review`). Added dual-mode support (full codebase + git-changes), P0-P3 severity classification, review-first paradigm, SOLID analysis, dead code removal planning, race conditions deep-dive, and 4 reference checklists. All 6 code-review skills bumped to v2.0.0.
- **Code Review Report**: Restructured final report into 4-section format with dual-view findings and export capability.
- **Installers**: Both `scripts/installer.ps1` and `scripts/installer.sh` updated with Phase 3 (extension build, VSIX packaging, VS Code installation).
- **Skills Registry**: Overhauled `skills.json` with 65 validated entries across 13 categories, fixed 34 stale paths, removed 15 deleted skills, and added 30 new entries.
- **Documentation Consistency**: Fixed root `README.md` (removed Codex references, corrected paths, added extension section), updated `CHANGELOG.md` footer links, and corrected extension `README.md` to match current functionality.

---

## [0.5.3] - 2026-02-04

### Changed
- **Documentation Refactoring**: Fixed critical path issues by renaming `claude-skills-catalog` references to `catalog/skills` across 20+ documentation files.
- **Legacy Cleanup**: Removed deprecated `claude-skills-catalog` references from `README.md`, `CHANGELOG.md`, and guides.
- **Command Consolidation**: Merged overlapping functionality to streamline the CLI experience.

## [0.5.2] - 2026-01-30

### Added
- Claude Skills section to README with quick setup instructions.
- Auto-analysis and commit message generation to `/upgrade-version` command.
- Standardized code formatting guidelines for Python templates.

### Fixed
- Added `CLAUDE.md` to `.gitignore`.

### Changed
- Updated `templates.json` version to match project version.

---

## [0.5.1] - 2026-01-28

### Added

#### Cross-Platform Installation
- **macOS & Linux Support**: Added native Bash installer support.
  - `install.sh`: New entry point for Unix-like systems.
  - `scripts/installer.sh`: Bash implementation mirroring the Windows logic (Global/Workspace install, Language Detection).
  - **Gemini / Antigravity Support**: Correctly maps `catalog/commands` to `.agent/workflows` and `catalog/skills` to `.agent/skills` for full agentic capability.

### Changed
- **Documentation**: Updated `README.md` with installation instructions for macOS/Linux.

---

## [0.5.0] - 2026-01-28

### Changed

#### Universal Catalog Refactoring
Massive structural simplification to create a single source of truth for all AI assets.

- **New `catalog/` Directory**: Centralized formatted assets.
  - `catalog/skills/`: Consolidated skills (formerly `claude-skills-catalog`).
  - `catalog/commands/`: Language-agnostic slash commands.
  - `catalog/context/` & `catalog/memory/`: Shared architecture/decision templates.
  - `catalog/CLAUDE.md`: Universal system prompt template.

- **Removed**:
  - `claude-skills-catalog/` (merged into catalog).
  - `templates/ai-instructions/claude-code/` (legacy language-specific redundancy removed).

#### Installer V5
Complete rewrite of `installer.ps1` implementation.
- **Unified Logic**: Now installs to both `.claude` and `.gemini` using the same catalog source.
- **Enhanced UX**:
  - Clearer prompts (`[Y]es / [N]o / [A]ll`).
  - "Overwrite All" support for bulk updates.
  - Strict, consistent logging (e.g., `✓ Global instructions installed at...`).
  - Restored support for Copilot, Cursor, and Windsurf global/workspace configuration.

### Added

#### New Operational Commands
- `/generate-tests`: Deep comprehensive test suite generation (Unit, Feature, Edge Cases).
- `/run-deep-review`: Comprehensive code analysis and reporting.
- `/generate-sbom`: Generate Software Bill of Materials (JSON/Markdown).
- `/create-skill-or-command`: Interactive wizard to build new AI capabilities.
- `/generate-commit-message`: Context-aware git commit message generation.
- `/update-devlog`: "Flight recorder" logger for development context.

---

## [0.4.0] - 2026-01-07

### Changed

#### Major Repository Restructuring

Simplified repository structure for improved navigation and maintainability with kebab-case naming conventions throughout.

**Directory Structure Changes**:

- **Skills Catalog**: Moved `catalogs/claude_skills/` → `catalog/skills/` (root level for easier access)

- **AI Instructions**: Simplified `templates/ai_instructions/agentic_systems/claude_code/` → `templates/ai-instructions/CLAUDE_MD/`

- **Development Templates**: Reorganized under `templates/development/` with kebab-case naming:
  - `code_cleanup/` → `codebase-cleanup/`
  - `code_review/` → `codebase-review/`
  - `compliance_governance/` → `compliance-review/`
  - `documentation_generation/` → `documentation-generation/`
  - `tests_generation/` → `tests-generation/`

- **JSON Catalogs**: Moved to repository root for easier access:
  - `catalogs/skills.json` → `skills.json`
  - `catalogs/templates.json` → `templates.json`

**Removed**:

- **Coding Assistants Templates**: Removed `templates/ai_instructions/coding_assistants/` (deprecated in favor of Claude Code templates)

- **Legacy Folders**: Removed all `legacy/` subdirectories across 7 language templates

- **Old Catalogs Directory**: Removed empty `catalogs/` after migration

**Updated Documentation** (75+ link updates):

- Updated all path references in `README.md`, `CLAUDE.md`, and guide files

- Updated all `import-skills.md` files across 7 languages

- Updated compliance-review documentation with corrected relative paths

- Updated tests-generation documentation and VS Code configuration paths

- Updated skills catalog README with new repository structure

**Benefits**:

- **Cleaner Navigation**: Simpler, more intuitive directory structure

- **Consistent Naming**: Kebab-case throughout (e.g., `codebase-review` vs `code_review`)

- **Reduced Depth**: Skills catalog at root level, AI instructions path shortened

- **Focused Content**: Removed deprecated coding assistants, keeping focus on Claude Code

**Statistics**:

- **Files Moved**: 400+ files reorganized

- **Links Updated**: 75+ documentation links corrected

- **Directories Renamed**: 7 major directory renames

- **Templates Regenerated**: `templates.json` rebuilt with 306 templates

---

## [0.3.3] - 2026-01-05

### Added

#### New Claude Skills Categories (13 new skills)

Expanded the Claude Skills catalog from 47 to 60 skills with 4 new categories inspired by awesome-claude-code-subagents patterns.

**Infrastructure Skills** (4 skills):

- **kubernetes-expert** - Deep Kubernetes expertise for container orchestration, deployment patterns, Helm charts, RBAC, and cluster management

- **terraform-specialist** - Infrastructure as Code with Terraform/OpenTofu for cloud provisioning, module design, state management, and multi-environment setups

- **cicd-architect** - CI/CD pipeline expertise for GitHub Actions, GitLab CI, Jenkins with deployment strategies (blue-green, canary) and security scanning

- **cloud-architect** - Multi-cloud architecture for AWS, Azure, GCP with Well-Architected Framework principles, high availability, and cost optimization

**Orchestration Skills** (3 skills):

- **task-coordinator** - Coordinate complex multi-step tasks with dependency tracking, parallel execution, and progress monitoring

- **context-manager** - Manage context across large codebases, track file relationships, and synthesize information for multi-file changes

- **workflow-orchestrator** - Design end-to-end workflows by chaining skills with quality gates between phases

**Developer Experience Skills** (3 skills):

- **refactoring-expert** - Safe code refactoring using Martin Fowler's catalog patterns, incremental changes, and test preservation

- **legacy-modernizer** - Modernize legacy codebases using Strangler Fig pattern, dual-write migrations, and feature toggles

- **dependency-manager** - Safe dependency upgrades, vulnerability patching, breaking change handling, and lock file management

**Language Specialist Skills** (3 skills):

- **rust-expert** - Deep Rust expertise for ownership, borrowing, lifetimes, async/await, and unsafe Rust patterns

- **go-expert** - Go expertise for goroutines, channels, interface design, error handling idioms, and concurrent systems

- **sql-expert** - SQL expertise for query optimization, indexing strategies, execution plans, and database-specific features (PostgreSQL, MySQL, SQL Server)

**Catalog Updates**:

- Updated CATALOG.md with all 13 new skills organized in 4 categories

- Updated skill count from 47 to 60 in README.md

- Added new categories to Pre-Built Skill Categories table

---

## [0.3.2] - 2025-12-09

### Changed

#### Simplified AI Instructions Templates

Consolidated and streamlined coding assistant templates for better usability and GitHub Copilot compatibility.

**Template Consolidation** (7 languages):

- **Merged comprehensive/condensed templates** - Each language now has ONE optimized template (~20k characters) instead of two separate files

- **Renamed to GitHub Copilot format** - All templates renamed to `copilot-instructions.md` matching VS Code's expected format

- **Balanced content** - Combines the best of comprehensive (detail) and condensed (efficiency) approaches

**Languages Updated**:

- Python, JavaScript, Java, C#, Go, C, C++ - All consolidated to single `copilot-instructions.md`

**Documentation Simplification**:

- **Focused on two platforms** - GitHub Copilot (coding assistants) and Claude Code (agentic systems)

- **Removed Cursor/Windsurf/Codex CLI references** - Simplified to reduce maintenance burden

- **Clear setup instructions** - 3-step guides for both GitHub Copilot and Claude Code

**README Updates**:

- Simplified Coding Assistants section with VS Code setup instructions

- Streamlined Agentic Systems section with `/setup-project` and `/import-skills` workflow

- Removed redundant "AI Instructions Setup" section

**Benefits**:

- **Easier to use** - One template per language, no decision fatigue

- **Better Copilot integration** - Correct filename format for VS Code auto-discovery

- **Reduced maintenance** - Single template to maintain per language

- **Clearer documentation** - Focused on the most popular platforms

---

## [0.3.1] - 2025-12-08

### Added

#### Compliance & Governance Templates (96 new templates across 7 languages)

Complete enterprise security and AI governance framework with production-ready implementations:

**Compliance Frameworks** (28 templates):

- **SOC 2 Type II Compliance** - Trust Service Criteria implementation (Security, Availability, Confidentiality, Processing Integrity, Privacy) across all 7 languages

- **ISO 27001 Implementation** - Information security management with 114 controls mapped to code-level implementations

- **NIST AI RMF** - AI Risk Management Framework with Govern, Map, Measure, Manage phases

- **PCI-DSS v4.0 Compliance** - Payment card data security with tokenization, encryption, and audit logging

**AI Agent Governance** (28 templates - 4 pillars × 7 languages):

- **🔄 Pillar 1: Lifecycle Management** - Separation of duties, multi-stage promotion (Development → Testing → Staging → Production), version control

- **⚠️ Pillar 2: Risk Management** - Rate limiting, circuit breakers, confidence thresholds, human-in-the-loop for high-risk decisions

- **🔒 Pillar 3: Security** - Input validation, prompt injection prevention, least privilege access, secure credential management

- **🔍 Pillar 4: Observability** - Decision logging, model drift detection, performance metrics, audit trails

**Privacy Protection** (14 templates):

- **GDPR Compliance** - EU data protection with 72-hour breach notification, data subject rights (access, erasure, portability)

- **CCPA Compliance** - California consumer privacy with opt-out mechanisms, data inventory, transparency requirements

**Risk Management** (14 templates):

- **Risk Assessment** - CVSS scoring, threat modeling (STRIDE framework), risk matrix visualization

- **Threat Modeling** - Attack surface analysis, attack tree generation, mitigation strategies

**Governance Policies** (14 templates):

- **Security Policies** - Access control policies, data classification, acceptable use policies

- **Access Control** - RBAC/ABAC implementation, least privilege, separation of duties

**Incident Response** (14 templates):

- **Incident Response Plan** - NIST SP 800-61 6-phase lifecycle (Preparation, Detection, Containment, Eradication, Recovery, Post-Incident)

  - Response time SLAs: P1 Critical (15 min), P2 High (60 min), P3 Medium (240 min), P4 Low (1440 min)

  - Duration metrics tracking, comprehensive incident reporting

  - Post-mortem analysis with root cause and lessons learned

- **Breach Protocols** - GDPR Article 33/34 compliance, 72-hour notification workflow, breach assessment, authority/individual notification templates

**Documentation & Guides** (7 files):

- Category README with implementation roadmap

- Sub-phase READMEs for each governance area (5 files)

- IMPLEMENTATION_GUIDE.md with integration patterns

### Enhanced

- **All Incident Response Templates** - Added comprehensive `generateIncidentReport()` functions with full timeline, impact analysis, response actions, and post-mortem data across all 7 languages (Java, C#, Go, C, C++, Python, JavaScript)

### Key Features

- **96 production-ready templates** covering 8 major compliance frameworks

- **4 Pillars AI Agent Governance** - Research-backed framework from McKinsey, Bain, AWS, NIST

- **Code-level implementations** - Not just documentation, actual working code for all controls

- **Audit preparation guidance** - Evidence collection, gap analysis, remediation tracking

- **Cross-language consistency** - Same governance patterns adapted idiomatically to Python, JavaScript, Java, C#, Go, C, C++

- **Integration with existing templates** - Links to Security Review, SBOM Generation, Documentation templates

### Research Sources

- [McKinsey: Deploying Agentic AI with Safety and Security](https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/deploying-agentic-ai-with-safety-and-security-a-playbook-for-technology-leaders)

- [Bain: Building the Foundation for Agentic AI](https://www.bain.com/insights/building-the-foundation-for-agentic-ai-technology-report-2025/)

- [AWS: Advancing AI Agent Governance](https://aws.amazon.com/blogs/machine-learning/advancing-ai-agent-governance-with-boomi-and-aws-a-unified-approach-to-observability-and-compliance/)

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

---

## [0.3.0] - 2025-12-04

### Added

#### Google Test + VS Code + GitHub Copilot Integration (7 new files, 2 enhanced templates)

Complete integration enabling automated C++ unit test generation with seamless IDE workflow:

**VS Code Workspace Configuration** (5 files):

- **tasks.json** - 6 pre-configured tasks (Configure, Build, Run All Tests, Verbose Tests, Single Test, Coverage)

  - Keyboard shortcuts: `Ctrl+Shift+B` (build), Command Palette test tasks

  - Ninja build system integration with parallel execution

- **launch.json** - Debugging configurations with GTest filter support

  - Press `F5` to debug tests with breakpoints

  - Step-through debugging (F10/F11) with variable inspection

- **settings.json** - CMake Tools auto-configuration, IntelliSense, Test Explorer integration

  - Auto-configure on project open

  - GitHub Copilot enabled by default

- **c_cpp_properties.json** - Cross-platform IntelliSense (Linux/Mac/Windows)

  - Google Test header paths pre-configured

  - Prevents red squiggly lines in test code

- **README.md** (vscode_config/) - Complete documentation with troubleshooting guide (6 common issues)

**Documentation & Workflow** (2 files):

- **COPILOT_QUICK_REFERENCE.md** - AI-assisted test generation guide

  - One-line prompts for common testing tasks

  - 6 detailed prompt templates (fixtures, mocks, parametrized tests, exceptions, coverage, CMake)

  - 3 complete conversation flow examples

  - Best practices for Copilot interaction

  - CMake integration prompts

- **GOOGLE_TEST_VSCODE_WORKFLOW.md** - End-to-end workflow guide (10 steps)

  - Prerequisites and installation (Linux/Mac/Windows)

  - Step-by-step from project creation to code coverage

  - Troubleshooting section (8 common issues with solutions)

  - Next steps and advanced patterns

**Enhanced Templates** (2 files):

- **cpp_unit_tests.md** - Added "🤖 GitHub Copilot Agent Mode Integration" section

  - Quick start guide (4 steps: Clone → Configure → Generate → Run)

  - Iterative test generation patterns

  - Copilot best practices (DOs and DON'Ts)

  - Links to complete workflow documentation

- **cpp_test_structure.md** - Added "IDE Integration: VS Code Configuration" section

  - Quick setup instructions

  - Extension requirements (4 essential, 3 recommended)

  - GitHub Copilot integration overview

  - Alternative IDE options (CLion, Visual Studio, Qt Creator)

**Key Features**:

- ⚡ **10-minute setup**: Clone → Configure → Generate Tests → Run

- ⌨️ **Keyboard shortcuts**: Build, test, and debug with single keystrokes

- 🤖 **AI-assisted testing**: GitHub Copilot generates 15+ comprehensive test suites

- 🐛 **Seamless debugging**: Breakpoints, step-through, variable inspection

- 📊 **Code coverage**: Automated coverage report generation with lcov/gcovr

- 🔄 **Cross-platform**: Works on Linux, macOS, and Windows

- ✅ **Ready-to-use**: No manual VS Code setup needed

- 📚 **Comprehensive docs**: Complete workflow guide + quick reference + troubleshooting

**Expected User Workflow**:

1. Clone repo (2 min) → 2. Copy `.vscode/` configs (1 min) → 3. Open in VS Code (auto-configures) → 4. Open GitHub Copilot (`Ctrl+Shift+I`) → 5. Paste prompt template (30 sec) → 6. Copilot generates tests (2-5 min) → 7. Build (`Ctrl+Shift+B`, 30 sec) → 8. Run tests (Command Palette, 10 sec) → 9. Debug failures (`F5`) → 10. Iterate with Copilot

**Total Time**: ~10 minutes from clone to first test run (vs. ~1-2 hours manual setup)

**Statistics**:

- **7 new files created** (~8,500 lines)

- **2 existing templates enhanced** (cpp_unit_tests.md, cpp_test_structure.md)

- **14 common issues documented** with solutions

- **6 pre-configured VS Code tasks**

- **3 debugging configurations**

- **50+ Copilot prompt examples**

- **Cross-platform support** (Linux/Mac/Windows)

### Changed

#### Test Development Templates Enhancement
- Enhanced cpp_unit_tests.md with GitHub Copilot integration section (102 lines added)

- Enhanced cpp_test_structure.md with VS Code integration section (47 lines added)

- Improved discoverability of Google Test workflow from existing templates

### Fixed

#### Documentation Cross-References
- Added navigation links between unit tests, test structure, and workflow documentation

- Fixed relative paths in workflow documentation

- Ensured consistent terminology (Google Test vs GoogleTest)

---

## [0.2.9] - 2025-11-06

### Added

#### Severity Classification Framework (42 code review templates)
Comprehensive severity classification system added to ALL code review templates across 6 phases and 7 languages:

- **Four Severity Levels**: CRITICAL, HIGH, MEDIUM, LOW with clear definitions

- **Actionable Guidelines**: Specific actions required for each severity level

- **Escalation/De-escalation Rules**: Context-based severity adjustment criteria

- **Standardized Reporting Format**: Consistent structure for all findings with effort estimates

**Phases Enhanced**:

- code_quality (7 templates) - Manual additions with language-specific examples for Python, JavaScript, Java

- context_analysis (7 templates)

- security_review (7 templates)

- performance_review (7 templates)

- testing_review (7 templates)

- final_report (7 templates)

**Benefits**:

- Helps prioritize code review findings objectively

- Clear communication between reviewers and developers

- Consistent severity assessment across all languages

#### Stopping Criteria for Multi-Pass Cleanup (7 cleanup templates)
Added comprehensive stopping criteria to prevent infinite cleanup loops:

- **Four Clear Stopping Conditions**:

  - Zero-change pass (ideal completion state)

  - Diminishing returns threshold (<5% files cleaned per pass)

  - Pass limit reached (maximum 3 passes)

  - Time limit reached (8 hours total cleanup time)

- **Progress Tracking Template**: Structured markdown for logging each pass with metrics

- **Multi-Pass Decision Matrix**: Table showing when to STOP vs CONTINUE based on percentage

- **Never stop without verification**: Requires minimum 2 passes (initial + verification)

**Templates Enhanced**:

- Python, JavaScript, Java, C#, Go, C, C++ cleanup templates

**Impact**:

- Prevents analysis paralysis in cleanup tasks

- Provides objective criteria for completion

- Documents cleanup progress systematically

#### Testing Phase Diagrams (56 test development templates)
Visual phase diagrams added to all testing templates to show position in 8-phase methodology:

- ASCII art diagram showing current phase, completed phases, and next steps

- Prerequisites clearly indicated

- Next step recommendations

- Enhanced user orientation within testing workflow

**Automation**: Created `tools/add_phase_diagrams.py` for consistent diagram generation

### Changed

#### Consistency Improvements

**OUTPUT_DIR Pattern Standardization (14 templates)**:

- Fixed inconsistent `{OUTPUT_DIR}` pattern to `${OUTPUT_DIR}` for bash compatibility

- Updated reward_hacking and unit_tests templates (7 files each)

- Ensures proper shell variable expansion

**Tool Version Updates (3 templates)**:

- Python: black 24.1.1 → 24.12.0, flake8 7.0.0 → 7.1.1, mypy v1.8.0 → 1.13.0

- Python: pytest 7.x → 8.3.4

- Go: Go 1.20 → 1.23

#### Enhanced Documentation

**README.md Restructure**:

- Transformed dense 502-line README into interactive collapsible sections

- Added task-oriented organization ("What are you looking for?")

- Nested dropdowns for language-specific setup

- Quick links to popular templates

- Reduced effective reading to ~3 clicks for any template

**TEMPLATE_FINDER.md (NEW)**:

- Comprehensive quick-reference matrix for finding templates

- Organized by: Task Type, Language, Time Available, Difficulty

- Template combinations and recommended workflows

**DECISION_TREES.md (NEW)**:

- Interactive ASCII decision trees for template selection

- Five decision trees covering common scenarios

- Visual guidance from task to specific template path

#### YAML Frontmatter for All Templates (189 templates)
Added comprehensive YAML frontmatter to enable searchability and automated catalog generation:

- **Metadata Fields**: template_id, template_name, version, last_updated, language, category, phase, phase_number, difficulty, estimated_time_hours

- **Searchable Lists**: prerequisites, related_templates, tools, tags

- **Automation Script**: `tools/add_yaml_frontmatter.py` processes all templates automatically

**Benefits**:

- Enables advanced search and filtering

- Powers templates.json catalog

- Supports web interface enhancements

- Enables dependency tracking

#### Quick Start Guide (NEW)
Created user-friendly QUICKSTART.md with step-by-step guidance:

- **Collapsible sections** for each major task (Clean Up, Review, Test, Document)

- **Direct links** to templates by language and phase

- **Copy-paste instructions** for GitHub Copilot, ChatGPT, Claude, Cursor, Windsurf

- **Example workflows** showing complete task execution

- **Tips for success** and common pitfalls to avoid

**Previous QUICKSTART.md renamed to QUICKSTART_CLAUDE_CODE.md** for Claude Code-specific setup

#### Enhanced Category READMEs
Updated code_review and test_development READMEs with user-friendly navigation:

- **Quick Start** flowcharts for decision-making

- **Collapsible sections** for each phase with direct template links

- **Review strategies** (quick vs comprehensive)

- **Clear "What You'll Get"** sections with checkboxes

- **Links** to QUICKSTART and TEMPLATE_FINDER for easy navigation

### Tools Added

Created 7 automation scripts for repository maintenance and quality assurance:

1. **tools/add_phase_diagrams.py** - Adds phase diagrams to testing templates (56 files processed)

2. **tools/add_severity_classification.py** - Adds severity framework to code review templates (39 files updated)

3. **tools/fix_consistency.py** - Fixes OUTPUT_DIR and other consistency issues (14 files updated)

4. **tools/update_tool_versions.py** - Updates tool versions to 2025 standards (3 files updated)

5. **tools/add_yaml_frontmatter.py** - Adds YAML frontmatter to all templates (189 files updated)

6. **tools/build_templates_catalog.py** - Generates searchable templates.json catalog (229 templates)

7. **tools/lint_templates.py** - Validates template consistency and completeness

**Total Automated Impact**: 310+ files improved through automation

### Infrastructure Added

**.pre-commit-config.yaml**:

- Pre-commit hooks for template validation

- Automatic catalog regeneration

- YAML frontmatter verification

- JSON validation

**templates.json**:

- Searchable catalog of all 229 templates

- Statistics by language, category, difficulty

- Total estimated hours: 623.0

- Powers web interface and CLI tools

### Statistics

**Phase 1-5 Complete (100% of originally planned phases)**

**Files Modified**: 310+ templates enhanced
**New Files Created**: 5 (QUICKSTART.md, templates.json, .pre-commit-config.yaml, 3 tools, enhanced READMEs)
**YAML Frontmatter Added**: 189 templates
**Automation Scripts**: 7 reusable tools for maintenance
**Lines Added**: ~25,000+ lines of documentation and metadata
**User Navigation**: Reduced template discovery time from 10+ minutes to <30 seconds

---

## [0.2.8] - 2025-11-06

### Added

#### Test Development: Unit Tests & Reward Hacking Phases (16 new files)
Implemented two critical testing phases to complete the comprehensive 8-phase testing methodology, focusing on unit testing fundamentals and final test quality validation through reward hacking detection.

**Unit Tests Phase** (8 files):

- **Comprehensive README** - Complete phase overview with FIRST principles and AAA pattern

- **7 Language Templates** - Python, JavaScript, Java, C#, Go, C, C++ (800-2,700 lines each)

  - FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)

  - AAA pattern (Arrange-Act-Assert) with extensive examples

  - Testing different component types (functions, classes, async, decorators, generators, context managers)

  - Edge cases and error handling patterns

  - Test quality and maintenance guidelines

  - Anti-patterns and remediation strategies

  - 20-30+ code examples per language

  - Framework-specific best practices (pytest, Jest, JUnit 5, xUnit, testing package, Unity, Google Test)

**Reward Hacking Phase** (8 files):

- **Comprehensive README** - Explains reward hacking detection and mutation testing

- **7 Language Templates** - Python, JavaScript, Java, C#, Go, C, C++ (1,000-2,200 lines each)

  - 7-phase validation framework covering ALL previous test phases

  - Mutation testing setup (mutmut, Stryker, PITest, Stryker.NET, go-mutesting, mull)

  - Weak test detection patterns (tautological tests, execution-only tests, over-mocking)

  - 15-20 weak vs. strong test examples per language

  - Detection scripts in native language

  - Phase-by-phase validation for all 7 previous phases

  - Remediation action plans with concrete examples

  - Continuous monitoring and quality scorecard setup

  - Quality metrics (mutation score >80%, test independence 100%)

### Changed

#### Updated Test Development Framework (7 files)
Enhanced existing test development documentation to integrate the two new phases:

- **test_development/README.md**:

  - Updated from 6 to 8 testing phases

  - Added recommended phase order workflow

  - Updated success criteria with unit test and mutation testing targets

  - Added unit test speed requirements (<1s per test)

  - Added mutation score target (>80%)

- **Updated All 6 Existing Phase READMEs**:

  - test_structure/README.md - Added Unit Tests and Reward Hacking cross-references

  - test_cases/README.md - Noted Unit Tests should precede this phase

  - mocks_fixtures/README.md - Added Unit Tests as companion phase

  - performance_testing/README.md - Added Reward Hacking validation reference

  - maintenance_cicd/README.md - Added Reward Hacking for pipeline validation

  - code_coverage/README.md - Added Unit Tests foundation and Reward Hacking as critical follow-up

### Technical Details

#### Complete 8-Phase Testing Workflow

```
1. Test Structure      → Infrastructure setup

2. Unit Tests          → Foundational component testing (NEW)

3. Test Cases          → Integration & E2E tests

4. Mocks & Fixtures    → Test isolation strategies

5. Performance Testing → Load and stress testing

6. Maintenance & CI/CD → Automation and pipelines

7. Code Coverage       → Measure and improve coverage

8. Reward Hacking      → Final quality validation (NEW)
```

#### Unit Tests Phase Features
- **Speed Requirements**: <1 second per unit test (target: <100ms)

- **Independence**: Tests run in any order with no shared state

- **Coverage**: All component types (functions, classes, async, decorators, generators, context managers)

- **Anti-Patterns**: Comprehensive guide with examples (tautological tests, weak assertions, over-mocking, test interdependencies)

- **Testing Frameworks**:

  - Python: pytest, unittest

  - JavaScript: Jest, Mocha, Vitest

  - Java: JUnit 5

  - C#: xUnit, NUnit

  - Go: testing package

  - C: Unity, Check

  - C++: Google Test, Catch2

#### Reward Hacking Phase Features
- **Mutation Testing**: Language-specific tool setup and configuration

  - Python: mutmut, mutpy

  - JavaScript: Stryker

  - Java: PITest

  - C#: Stryker.NET

  - Go: go-mutesting

  - C/C++: mull

- **Validation Matrix**: Cross-phase validation for all 7 previous phases

- **Detection Patterns**: 15-20 examples per language of weak vs. strong tests

- **Quality Metrics**:

  - Mutation Score: >80% target

  - Test Independence: 100%

  - Assertion Quality: >90% specific assertions

  - Error Path Coverage: >80%

  - Mock Usage Ratio: <30%

  - Flaky Test Rate: <2%

#### Reward Hacking Detection Patterns
- **Tautological Tests**: Tests that can never fail

- **Execution-Only Tests**: No assertions, just checks for exceptions

- **Weak Assertions**: Too broad or always true (e.g., `assert result is not None`)

- **Over-Mocking**: Testing mock behavior instead of real code

- **Happy Path Only**: Missing error conditions and edge cases

- **Brittle Tests**: Testing implementation details instead of behavior

### Statistics

- **Files Created**: 16 new comprehensive template files

- **Total Lines**: ~25,800 lines of testing guidance

  - Unit Tests: ~14,000 lines (7 templates + README)

  - Reward Hacking: ~10,000 lines (7 templates + README)

- **Code Examples**: 150+ complete test examples across all languages

- **Languages Supported**: 7 (Python, JavaScript, Java, C#, Go, C, C++)

- **Testing Phases**: Increased from 6 to 8 complete phases

- **Files Updated**: 7 existing documentation files with cross-references

### Benefits

**Unit Tests Phase**:

- Fills critical gap between test infrastructure and broader test case development

- Emphasizes speed (<1s execution) and isolation (no dependencies)

- Comprehensive patterns for all component types with language-specific idioms

- 20-30+ code examples per language demonstrating best practices

**Reward Hacking Phase**:

- Industry-first comprehensive validation specifically designed for AI-generated tests

- Prevents false confidence from high coverage percentages that don't represent true validation

- Mutation testing integration across all 7 languages

- Validates all 7 previous testing phases through cross-phase analysis

- Actionable remediation with concrete before/after examples and timelines

- Detects "reward hacking" where tests achieve high metrics without validating functionality

**Overall Testing Framework**:

- Complete 8-phase methodology from infrastructure to quality validation

- Ensures not just high coverage (>80%), but truly effective, high-quality tests

- Catches real bugs through mutation testing validation

- Provides genuine confidence in code quality and test effectiveness

---

## [0.2.7] - 2025-10-21

### Added

#### Discovery & Installation System
Implemented comprehensive skill discovery, browsing, and installation infrastructure inspired by claude-code-templates repository analysis.

- **Skills Catalog** (`skills.json`): Machine-readable catalog with metadata for all 48 skills

  - Complete metadata: category, priority, tools required, size metrics

  - Security validation scores (structural, integrity, semantic)

  - Download tracking and versioning support

  - ~143,667 estimated tokens across 46,259 lines

- **CLI Installation Tool** (`tools/install_skill.py`): One-command skill installation

  - Install by skill name: `--skill plan-before-code`

  - Install by category: `--category workflow`

  - Install by priority: `--priority CRITICAL`

  - Install all skills: `--all`

  - List and filter: `--list`, `--categories`, `--info`

  - Auto-detect `.claude/skills/` directory

  - Force overwrite with `--force` flag

  - Cross-platform support (Windows, Linux, macOS)

- **Catalog Builder** (`tools/build_skills_catalog.py`): Automated catalog generation

  - Extracts YAML frontmatter from all SKILL.md files

  - Calculates size metrics (lines, characters, estimated tokens)

  - Identifies required tools from skill content

  - Generates comprehensive statistics

  - Validates skill structure and metadata

- **Web-Based Skills Browser** (`docs/index.html`): Interactive skill discovery

  - Search by name or description

  - Filter by category, priority, language

  - Responsive design (desktop and mobile)

  - Installation command generation

  - Copy-to-clipboard functionality

  - GitHub Pages ready

  - No backend required (pure client-side)

- **Tools Documentation** (`tools/README.md`): Complete usage guide

  - Installation workflows for new and existing projects

  - Skill categories and descriptions

  - Advanced usage patterns

  - Troubleshooting guide

  - Batch installation examples

#### Integration & Automation Infrastructure

- **MCP Integration Guide** (`integrations/README.md`): External service connections

  - 11 MCP templates (GitHub, GitLab, databases, cloud, AI services)

  - Security best practices for API keys

  - Environment variable configuration

  - Troubleshooting common issues

  - Skills-to-MCP mapping

- **Hooks System** (`hooks/README.md`): Automation workflows

  - Git hooks (pre-commit, pre-push, post-commit)

  - File hooks (on-save actions)

  - Development hooks (test run, build success)

  - Hook installation templates

  - CI/CD integration patterns

  - Workflow examples (quality gates, auto-documentation)

#### Contributing Guidelines

- **CONTRIBUTING.md**: Comprehensive contribution guide

  - Skill creation guidelines with templates

  - Quality standards and requirements

  - Submission process and PR template

  - Testing guidelines

  - Tool development standards

  - Documentation requirements

  - Common pitfalls to avoid

#### User Onboarding Documentation

- **QUICKSTART.md**: 5-minute setup guide for new projects

  - Step-by-step project initialization from scratch

  - Skill installation workflow with examples

  - Common scenarios (Python web app, JavaScript/React, existing projects, teams)

  - Verification steps and project structure overview

  - Troubleshooting section with solutions

  - Tips, best practices, and next steps

### Changed

- **README.md**: Major update with new features and onboarding

  - Added prominent "New to This Repository? Start Here!" section

  - Added comprehensive "Setting Up a New Project" guide (7 steps)

  - Added Quick Reference with 4 common setup scenarios

  - Included "Installing Skills to Existing Projects" section

  - Updated repository structure with new directories

  - Added links to web browser and QUICKSTART guide

  - Updated statistics (48 skills, 46k lines, 144k tokens)

  - Improved navigation and organization

- **Skills Browser UX**: Enhanced discovery experience

  - Priority badges with color coding (Critical, High, Medium, Low)

  - Category tags for quick identification

  - Tool requirements displayed on cards

  - Size metrics (lines, tokens) visible

  - Installation modal with detailed information

### Fixed

- **Windows Console Compatibility**: Resolved emoji encoding issues

  - Replaced Unicode emojis with ASCII markers in CLI tool

  - Used text-based priority indicators: [!], [*], [-], [ ]

  - Ensured cross-platform console output

### Technical Debt

- **Category Normalization**: Skills catalog has inconsistent category casing

  - Some categories use Title Case (e.g., "Code Cleanup")

  - Others use lowercase (e.g., "configuration", "security")

  - Future version should normalize to single standard

  - Affects catalog statistics and filtering

### Statistics

- **Total Skills**: 48 production-ready skills

- **Total Lines**: 46,259 lines of skill content

- **Estimated Tokens**: 143,667 tokens

- **Categories**: 12 unique categories

- **New Files Added**: 9 major files

  - 2 tools (install_skill.py, build_skills_catalog.py)

  - 1 catalog (skills.json)

  - 1 web browser (docs/index.html)

  - 5 documentation files (CONTRIBUTING, QUICKSTART, integrations/README, hooks/README, tools/README, docs/README)

---

## [0.2.6] - 2025-10-20

### Added

#### Claude Code Skills Framework - 100% COMPLETE (52 production-ready skills)
Created comprehensive Claude Skills framework for token-efficient, task-specific expertise with natural language invocation. **All 52 planned skills have been implemented!**

**🎉 Framework Complete** (52/52 skills - 100%):

1. **`plan-before-code`** 🔥 - Anthropic's #1 Best Practice

   - Implements explore → plan → execute workflow

   - Prevents premature coding that leads to iterations

   - Significantly improves code quality (50-70% fewer iterations)

   - Based on Anthropic Claude Code Best Practices 2025

2. **`create-claude-md`** 🔥 - CLAUDE.md Configuration Generator

   - Generates comprehensive CLAUDE.md files (the "most important tool" per Anthropic)

   - Provides persistent context without token cost

   - Includes bash commands, coding standards, testing procedures

   - Team consistency and onboarding tool

3. **`init-python-project`** - Complete Project Initialization

   - Creates production-ready Python project structure in minutes

   - Standard directory layout (src/, tests/, docs/)

   - Configuration files (pyproject.toml, requirements.txt, .gitignore)

   - Testing framework, documentation templates, CI/CD setup

4. **`setup-python-system-prompt`** - Python Standards Configuration

   - Configures Claude Code with comprehensive Python development standards

   - PEP 8 compliance, Black formatting, type hints

   - Project architecture, testing framework, development workflow

   - 600+ lines of detailed configuration guidance

5. **`cleanup-python`** - Code Modernization

   - Removes dead code, consolidates duplicates

   - Modernizes to Python 3.9+ patterns (f-strings, pathlib, type hints)

   - Organizes imports, simplifies code

   - 850+ lines with comprehensive examples

6. **`generate-api-docs`** - API Documentation Generator (Multi-language)

   - Generates comprehensive API documentation

   - OpenAPI/Swagger specs, language-specific formats

   - Supports all 7 repository languages

   - Interactive documentation (Swagger UI, etc.)

**All Skills Implemented** (52 total - 100% complete):

**Workflow & Development Process** (4 skills) ✅:

- `plan-before-code`, `test-driven-development`, `code-commit-workflow`, `debug-with-logs`

**System Prompt Configuration** (7 skills) ✅:

- Python, JavaScript, Java, C#, Go, C, C++ - Complete configuration for all languages

**Code Review** (6 skills) ✅:

- 6-phase workflow: context-analysis, quality, security, performance, testing, final-report

**Code Cleanup** (7 skills) ✅:

- Python, JavaScript, Java, C#, Go, C, C++ - Language-specific cleanup and modernization

**Documentation** (6 skills) ✅:

- API docs, docstrings, strategic-comments, user-documentation, technical-docs, SBOM

**Testing** (6 skills) ✅:

- test-infrastructure, test-cases, mocks-fixtures, performance-testing, ci-cd-testing, code-coverage

**Project Initialization** (4 skills) ✅:

- Python, JavaScript, Java, C# - Complete project setup automation

**Security & Quality** (5 skills) ✅:

- dependency-security-audit, pre-commit-checklist, complexity-analysis, licensing-compliance-check, subagent-workflow

**Migration & Refactoring** (4 skills) ✅:

- migrate-python-2-to-3, refactor-for-testability, extract-microservice, dependency-upgrade

**AI Assistant Configuration** (3 skills) ✅:

- create-claude-md, create-custom-command, optimize-context-usage

**Skills Documentation** (6 files):

- `README.md` - Main skills guide with complete overview

- `SKILLS_LIST.md` - Complete catalog of all 52 skills

- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details

- `QUICK_START.md` - Quick reference guide

- `INDEX.md` - Complete file index

- `FINAL_SUMMARY.md` - Project completion summary

**Framework Statistics**:

- **52 Skills**: All production-ready and fully documented

- **45,000+ Lines**: Average ~865 lines per skill

- **10 Categories**: Comprehensive coverage of development workflows

- **7 Languages**: Multi-language support (Python, JavaScript, Java, C#, Go, C, C++)

- **100% Complete**: All planned skills implemented

**Benefits**:

- **Token Efficient**: Metadata-only loading vs full templates (20-50x reduction)

- **Discoverable**: Natural language invocation ("Use the [skill-name] skill")

- **Composable**: Chain skills in multi-step workflows

- **Best Practices**: Implements Anthropic's Claude Code recommended workflows

- **Production Ready**: All 52 skills fully documented with real-world examples

- **Comprehensive**: Complete development lifecycle coverage from setup to deployment

### Changed

#### Directory Rename: system_prompts → agent_prompts
Renamed directory for better clarity and alignment with industry terminology.

**Rationale**:

- "agent_prompts" better describes contents (autonomous agents + interactive assistants)

- Clearer distinction from generic "system prompts"

- More intuitive for users

**Files Modified** (15 total):

- Main `README.md` - Updated all references, added skills section

- `agent_prompts/README.md` - Added skills framework section at top

- All 6 skills directories - Updated all path references

- All 6 skills documentation files - Updated directory references

**Path Updates**:

- All `system_prompts/` references → `agent_prompts/`

- All internal links and navigation updated

- Directory structure diagrams updated

### Documentation

#### Updated Main README.md
- **Version**: 0.2.5 → 0.2.6

- **Added Skills Section**: Complete table with 6 production-ready skills

- **Quick Start Examples**: Natural language skill invocation patterns

- **Skills Roadmap**: 52 total skills (6 complete, 46 remaining)

- **Repository Structure**: Updated to show skills/ subdirectory

#### Updated agent_prompts/README.md
- **Skills Framework Section**: Prominent placement at top of file

- **Quick Start**: Examples for immediate skill usage

- **Directory Structure**: Shows new skills/ subdirectory

- **All Path References**: Updated to agent_prompts/

### Technical Details

**Skills Structure**:
```
agent_prompts/autonomous_agents/claude_code/skills/
├── README.md                      # Complete skills documentation
├── SKILLS_LIST.md                 # 52-skill catalog
├── IMPLEMENTATION_SUMMARY.md      # Technical details
├── QUICK_START.md                 # Quick reference
├── INDEX.md                       # File index
├── FINAL_SUMMARY.md              # Completion summary
├── plan-before-code/
│   └── SKILL.md                  # 750+ lines
├── create-claude-md/
│   └── SKILL.md                  # 900+ lines
├── init-python-project/
│   └── SKILL.md                  # 1000+ lines
├── setup-python-system-prompt/
│   └── SKILL.md                  # 600+ lines
├── cleanup-python/
│   └── SKILL.md                  # 850+ lines
└── generate-api-docs/
    └── SKILL.md                  # 700+ lines
```

**Skill Format**:

- YAML frontmatter with metadata

- "When to Use" section (5-7 use cases)

- "What This Skill Does" (detailed capabilities)

- Prerequisites

- Step-by-step instructions

- Code examples (2-5 per skill)

- Success criteria checklist

- Related skills cross-references

- External resources

**Based On**:

- Anthropic Claude Code Best Practices 2025

- Simon Willison's Claude Skills research

- ai_templates v0.2.5 templates (162 templates as source material)

**Development Time**: ~6 hours

- Research: 1 hour (Claude Code best practices, skills format)

- Planning: 1 hour (repository analysis, skill categorization)

- Development: 4 hours (6 skills + 6 documentation files)

**Total Output**: ~7,000+ lines of documentation

---

## [0.2.5] - 2025-10-16

### Added

#### System Prompt Consistency Enhancements (29 files)
Enhanced all system prompt files with 4 critical instructions to improve AI behavior consistency, code quality, documentation practices, and testing protocols.

**The 4 New Instructions**:

1. **System Prompt Adherence** (Section 1)

   - Added after Quality Assurance section

   - Reminds AI to periodically review instructions during long conversations

   - Ensures compliance with all coding standards and workflows

   - References specific sections when needed to maintain consistency

2. **No Change-Tracking Comments** (Section 3)

   - Added to Code Standards / Comment Guidelines section

   - Prevents meta-commentary in code comments (e.g., "changed value to 12")

   - Language-specific examples for all 7 languages (Python, JavaScript, Java, C#, Go, C, C++)

   - Focuses on explaining "why" rather than documenting "what changed"

3. **Documentation Best Practices** (Section 4)

   - Added after DEVLOG.md structure

   - Ensures all development documentation goes in DEVLOG.md only

   - Prevents documentation fragmentation across multiple markdown files

   - Maintains single source of truth for development history

   - Updated DEVLOG.md template with "Tests Run" and "Iterations" fields

4. **Iterative Testing Protocol** (Section 6)

   - Added after Quality Gates section

   - Establishes test-driven problem-solving workflow

   - Uses temporary test files in `tests/temp/` directory

   - Includes iteration tracking and cleanup procedures

   - Language-specific test file extensions and paths for all 7 languages

**Files Modified**:

- Autonomous Agents (Claude Code): 13 files

  - Python, JavaScript, Java, C#, Go, C, C++ (comprehensive + condensed)

- Coding Assistants (General): 14 files

  - Python, JavaScript, Java, C#, Go, C++ (comprehensive + condensed)

- Global Generalized: 1 file

- Automation Scripts: 2 batch update scripts created

**Files Renamed**:

- All comprehensive system prompts: `*_35k.md` → `*_40k.md` (13 files)

- Reflects increased content size from new instructions

**Language-Specific Customization**:

- Python: `tests/temp/test_feature_validation.py`

- JavaScript/TypeScript: `tests/temp/test_feature_validation.test.ts`

- Java: `src/test/java/temp/TempFeatureValidationTest.java`

- C#: `tests/temp/TempFeatureValidationTests.cs`

- Go: `tests/temp/temp_feature_validation_test.go`

- C: `tests/temp/test_feature_validation.c`

- C++: `tests/temp/test_feature_validation.cpp`

### Changed

**Automation and Efficiency**:

- Created `batch_update_remaining_files.py` - Updated 8 Claude Code files (C#, Go, C, C++) automatically

- Created `batch_update_coding_assistants.py` - Updated 11 coding assistant files automatically

- Manual updates for Python, JavaScript, Java files to ensure quality

- Total processing time: ~2 hours (estimated 1 hour saved through automation)

**Documentation Created**:

- `COMPLETION_SUMMARY.md` - Comprehensive summary of all updates

- `HANDOFF_FOR_NEW_CONVERSATION.md` - Detailed handoff documentation with all 4 instructions

- `SYSTEM_PROMPT_UPDATE_GUIDE.md` - Step-by-step guide for system prompt updates

- `UPDATE_STATUS.md` - Progress tracking document

### Benefits

**Improved AI Behavior**:

- **Consistency**: AI maintains adherence to standards throughout long conversations

- **Code Quality**: Eliminates meta-commentary that clutters code comments

- **Documentation**: Single source of truth in DEVLOG.md prevents fragmentation

- **Reliability**: Test-driven approach ensures solutions actually work before claiming completion

**Developer Experience**:

- **Clearer Standards**: Language-specific examples make expectations explicit

- **Better Testing**: Iterative protocol with temp files ensures robust solutions

- **Organized Documentation**: All development notes in one place (DEVLOG.md)

- **Professional Output**: No "changed from X to Y" comments in production code

**Production Readiness**:

- All 29 system prompt files now have consistent quality standards

- Language-specific examples tailored to each ecosystem

- Comprehensive and condensed versions both fully updated

- Ready for immediate deployment across all supported languages

---

## [0.2.4] - 2025-10-10

### Fixed

#### Template Content Cleanup and Bitbucket Rendering (154 files)
Removed redundant sections, fixed markdown formatting issues, and improved content organization for better Bitbucket compatibility.

**Template Updates** (154 files):

- **Removed old "File Output Instructions" section**: Eliminated redundant and outdated section that referenced deprecated `generated_docs/` subdirectory

- **Moved "Output Format Specifications" inside prompt templates**: Relocated section from outside closing `~~~` marker to inside, ensuring specifications are included when users copy templates

- **Fixed bullet point rendering**: Added blank lines before bullet lists for proper Bitbucket markdown rendering

- **Improved section organization**: Template content now properly structured with instructions inside copyable section, verification checklist outside

**Files Modified**:

- Documentation Templates: 49/49 files

- Code Review Templates: 43/43 files

- Code Cleanup Templates: 8/8 files

- Test Development Templates: 54/54 files

**Benefits**:

- **Perfect Bitbucket Rendering**: Bullet points now display correctly with proper spacing

- **No Redundant Sections**: Removed confusing and outdated "File Output Instructions"

- **Better Template Structure**: Output specifications now included in copyable prompt template

- **Clearer Organization**: Logical separation between template content and verification steps

### Technical Details

**Issues Resolved**:

1. **Bullet Points on Same Line**: Added blank lines before bullet lists
   ```markdown
   # Before
   Text

   - Bullet 1

   - Bullet 2

   # After
   Text

   - Bullet 1

   - Bullet 2
   ```

2. **Content Outside Template**: Moved specifications inside
   ```markdown
   # Before
   ~~~  ← End of template
   ## Output Format Specifications  ← Outside (not copied)

   # After
   ## Output Format Specifications  ← Inside
   ~~~  ← End of template
   ```

3. **Redundant Sections**: Removed old file output instructions that duplicated OUTPUT_DIR setup

---

## [0.2.3] - 2025-10-10

### Changed

#### Directory Structure Improvements (155 files)
Optimized output directory structure across all template files to improve organization and eliminate redundant subdirectories.

**Template Updates** (155 files):

- **Removed `generated_docs/` subdirectory**: Simplified from 4 to 3 subdirectories for clearer organization

- **Standardized 3-subdirectory structure**:

  - `templates/` - Reusable templates, example configurations, and scripts

  - `assets/` - Images, diagrams, charts, and supplementary files

  - `exports/` - Final reports, documentation, and publishable artifacts

- **Added `OUTPUT_DIR` variable**: All templates now establish output directory at the beginning with shell variable

- **Updated file path references**: All file generation commands now use `${OUTPUT_DIR}/` prefix for consistent output location

- **Added verification sections**: Each template includes end-of-process directory structure verification checklist

**Files Modified**:

- Documentation Templates: 49/49 files

- Code Review Templates: 43/43 files

- Code Cleanup Templates: 8/8 files

- Test Development Templates: 55/55 files

**Benefits**:

- **Clearer Organization**: 3 subdirectories instead of 4 eliminates confusion

- **Consistent Output Paths**: `${OUTPUT_DIR}` variable ensures all files go to correct location

- **Better User Experience**: Templates now explicitly establish output directory before any operations

- **Verification Built-in**: Each template includes checklist to verify correct directory structure

### Technical Details

**Before (4 subdirectories)**:
```
phase_name/
├── generated_docs/  # Redundant with exports/
├── templates/
├── assets/
└── exports/
```

**After (3 subdirectories)**:
```
phase_name/
├── templates/       # Reusable templates and scripts
├── assets/          # Images, diagrams, supplementary files
└── exports/         # Final reports and publishable artifacts
```

**Example OUTPUT_DIR Usage**:
```bash
OUTPUT_DIR="documentation/sbom"
mkdir -p ${OUTPUT_DIR}/{templates,assets,exports}
cyclonedx-py requirements requirements.txt -o ${OUTPUT_DIR}/exports/sbom.json
```

---

## [0.2.2] - 2025-10-10

### Changed

#### Bitbucket Migration & Repository Agnostic Updates (150 files)
Migrated all templates from GitHub-specific references to repository-agnostic format compatible with Bitbucket and other Git platforms.

**Template Updates** (133 files):

- **Bullet Point Formatting**: Fixed markdown formatting with blank lines between bullets for proper Bitbucket rendering

- **Repository URL Instructions**: Replaced hardcoded GitHub URLs with `<REPO_URL>` placeholder

- **Git Config Integration**: Added instructions to retrieve repository URL from `.git/config`:
  ```bash
  git config --get remote.origin.url
  ```
- **Explicit File Output Paths**: Added "File Output Instructions" section to all prompt templates with exact file paths and directory creation commands

**System Prompt Updates** (17 files):

- Replaced GitHub URLs with `<REPO_URL>` placeholder throughout autonomous agent and coding assistant prompts

- For Go templates: Replaced `github.com/` module paths with `<MODULE_PATH>` placeholder

- Added `.git/config` retrieval instructions near git workflow sections

- Maintained tool-specific references (e.g., `github.com/gin-gonic/gin` for third-party packages)

**Files Modified**:

- Code Review Templates: 42/42 files

- Test Development Templates: 42/42 files

- Documentation Templates: 42/42 files

- Code Cleanup Templates: 7/7 files

- System Prompts: 17/29 files (only those with GitHub references)

**Benefits**:

- **Platform Agnostic**: Templates work with Bitbucket, GitHub, GitLab, or any Git platform

- **Better Bitbucket Rendering**: Fixed bullet point formatting displays correctly in Bitbucket's markdown viewer

- **Clear File Management**: Users know exactly where to save each generated file

- **Repository Discovery**: Users can easily find their repository URL from local `.git/config`

- **Reduced Maintenance**: No hardcoded URLs to update when repositories move

---

## [0.2.1] - 2025-10-09

### Changed

#### Standardized Output Directory Structures (133 templates updated)
Added explicit output directory specifications to all templates for organized file management and consistent project structure.

**Code Review Templates** (42 files):

- All review outputs now go to `review/{phase}/` directories

- Each phase (context_analysis, code_quality, security_review, performance_review, testing_review, final_report) has dedicated subdirectory

- Standardized outputs: phase_report.md, phase_findings.json, analysis_scripts/, supporting_data/

**Test Development Templates** (42 files):

- All test outputs now go to `tests/{phase}/` directories

- Each phase (test_structure, test_cases, mocks_fixtures, performance_testing, maintenance_cicd, code_coverage) has dedicated subdirectory

- Standardized outputs: test_files/, test_data/, test_reports/, test_configs/

**Documentation Templates** (42 files):

- All documentation outputs now go to `documentation/{phase}/` directories

- Each phase (docstrings, comments, user_docs, technical_docs, api_docs, sbom) has dedicated subdirectory

- Standardized outputs: generated_docs/, templates/, assets/, exports/

**Code Cleanup Templates** (7 files):

- All cleanup outputs now go to `cleanup/` directory

- Standardized outputs: cleanup_report.md, cleanup_history.md, backup/, scripts/, analysis/

#### Repository Organization Improvements
- Renamed COMPLETION_STATUS_AND_PLAN.md → DEVLOG.md

- Refactored DEVLOG.md to follow CLAUDE.md standard structure

- Added Current Task List, Development History, Implementation Challenges, Technical Decisions

- Added Troubleshooting History, Version Milestones, Future Enhancements, Metrics

### Technical Details

**Directory Structure Overview**:
```
repository_root/
├── review/           # Code review outputs (6 phases)
├── tests/            # Test development outputs (6 phases)
├── documentation/    # Documentation outputs (6 phases)
└── cleanup/          # Code cleanup outputs
```

**Benefits**:

- Organized output management across all template workflows

- Consistent project structure for teams using multiple templates

- Clear separation of concerns (review vs tests vs docs vs cleanup)

- Easy gitignore patterns for generated artifacts

- Improved traceability and audit trails

---

## [0.2.0] - 2025-10-09

### 🎉 Complete Multi-Language Expansion - ALL 161 Templates

**Major Milestone**: Complete multi-language support across ALL template sections

### Added

#### System Prompts (29 files - 100% COMPLETE)
- **Autonomous Agents (Claude Code)**: 14 files

  - 7 languages: Python, JavaScript, Java, C#, Go, C, C++

  - Each language: Comprehensive (~35k tokens) + Condensed (~20k tokens)

  - Language-specific: build systems, testing frameworks, tooling, best practices

- **Coding Assistants (General)**: 14 files

  - 7 languages: Python, JavaScript, Java, C#, Go, C, C++

  - Each language: Comprehensive (~35k tokens) + Condensed (~15k tokens)

  - Platform-agnostic prompts for GitHub Copilot, Cursor, Windsurf

- **Generalized Prompt**: 1 file

  - Universal system prompt for general-purpose AI assistants

#### Documentation Templates (42 files - 100% COMPLETE)
- **Docstrings** (7 languages)

  - Language-specific documentation formats: JSDoc, JavaDoc, XML docs, godoc, Doxygen

  - Module, class, function documentation standards per language

- **Comments** (7 languages)

  - Strategic commenting guidelines for each language ecosystem

  - Explain "why" not "what" approach across all languages

- **User Documentation** (7 languages)

  - README, installation guides, quick starts per language/ecosystem

  - Package managers: npm/yarn, Maven/Gradle, NuGet, go modules, Make/CMake

- **Technical Documentation** (7 languages)

  - Architecture, ADRs, design decisions for each language context

  - Language-specific patterns and idioms

- **API Documentation** (7 languages)

  - OpenAPI/Swagger for web languages (JavaScript, Java, C#, Go)

  - Function signatures and headers for C/C++

- **SBOM Generation** (7 languages)

  - NTIA compliance, EU Cyber Resilience Act

  - Language-specific tools: npm audit, OWASP Dependency-Check, CycloneDX, Syft

  - CycloneDX/SPDX format generation for all languages

#### Test Development Templates (42 files - 100% COMPLETE)
- **Test Structure** (7 languages)

  - Framework setup: Jest/Mocha, JUnit 5, xUnit/NUnit, testing package, Unity/CUnit, GoogleTest/Catch2

  - Directory organization and configuration per language

- **Test Cases** (7 languages)

  - Unit/integration/e2e patterns for each language

  - AAA pattern, parametrized tests, table-driven tests (Go)

- **Mocks & Fixtures** (7 languages)

  - Language-specific mocking: Jest/Sinon, Mockito, Moq, testify, CMock, GMock

  - Test data factories and isolation strategies

- **Performance Testing** (7 languages)

  - Load testing tools: k6, JMH/Gatling, BenchmarkDotNet, testing.B, custom timing, Google Benchmark

  - Profiling: clinic.js, VisualVM, dotTrace, pprof, Valgrind, perf

- **Maintenance & CI/CD** (7 languages)

  - GitHub Actions workflows for all languages

  - Quality gates, pre-commit hooks, automated testing

- **Code Coverage** (7 languages)

  - Coverage tools: Istanbul/nyc/c8, JaCoCo, Coverlet, go test -cover, gcov/lcov, llvm-cov

  - 80%+ coverage target across all languages

### Changed
- **Updated all subdirectory READMEs** with language comparison tables

  - 6 code_review subdirectories

  - 6 documentation subdirectories

  - 6 test_development subdirectories

  - All show complete language availability in table format

- **Updated system_prompts/README.md** with complete structure

  - Comprehensive tables showing all 29 system prompt files

  - Platform selection guide (autonomous vs coding assistants)

  - Token target reference (comprehensive vs condensed)

- **Verified 100% completion** of all template files

  - Code Cleanup: 7/7 ✅

  - Code Review: 42/42 ✅

  - Documentation: 42/42 ✅

  - Test Development: 42/42 ✅

  - System Prompts: 29/29 ✅

  - **Total: 162/162 templates** (161 planned + 1 bonus generalized prompt)

### Technical Details

#### Languages Supported (7 Total)
1. **Python** - General-purpose, data science, web development

2. **JavaScript/TypeScript** - Web, Node.js, React, Angular, Vue

3. **Java** - Enterprise, Spring Boot, Android

4. **C#** - .NET, ASP.NET Core, Unity

5. **Go** - Microservices, cloud-native

6. **C** - Embedded systems, firmware, RTOS

7. **C++** - Performance-critical, embedded, modern C++

#### Template Statistics
- **Total Files**: 162 templates (161 planned + 1 bonus)

- **Total Lines**: ~150,000+ lines of comprehensive templates

- **Documentation Coverage**: 100% across all sections

- **Language Coverage**: 7 production-ready languages

- **Tool Integration**: 50+ language-specific tools, linters, formatters, test frameworks

#### Language-Specific Tooling
- **Build Systems**: npm/yarn, Maven/Gradle, .NET SDK/NuGet, go modules, Make/CMake

- **Testing**: Jest/Mocha/Cypress, JUnit 5/Mockito, xUnit/NUnit/Moq, testing/testify, Unity/CUnit, GoogleTest/Catch2

- **Linting**: ESLint/Prettier, Checkstyle/SpotBugs, StyleCop/ReSharper, gofmt/golint, cppcheck/clang-tidy

- **Coverage**: Istanbul/nyc/c8, JaCoCo/Cobertura, Coverlet/dotCover, go test -cover, gcov/lcov/llvm-cov

- **Security**: npm audit, OWASP Dependency-Check, Snyk, gosec, Valgrind/AddressSanitizer

- **Performance**: clinic.js/autocannon, JMH/Gatling, BenchmarkDotNet, pprof, Valgrind, Google Benchmark

---

## [0.1.5] - 2025-10-08

### Added
- **Complete Code Cleanup Templates** (7 languages)

  - Python, JavaScript, Java, C#, Go, C, C++ cleanup templates

  - Language-specific: ESLint, Prettier, Maven/Gradle, ReSharper, gofmt, MISRA-C, clang-tidy

  - Dead code removal, import cleanup, modernization patterns

- **Complete Code Review Templates** (42 files: 7 languages × 6 phases)

  - **Context Analysis**: Project structure, dependencies, build systems for all 7 languages

  - **Code Quality**: Linters, complexity analysis, best practices for each language

  - **Security Review**: OWASP Top 10, language-specific vulnerabilities, security tools

  - **Performance Review**: Profiling tools and optimization strategies per language

  - **Testing Review**: Framework-specific test quality assessment

  - **Final Report**: Consolidated findings with prioritized recommendations

  Languages: Python, JavaScript/TypeScript, Java, C#, Go, C (embedded), C++ (modern)

### Changed
- **Updated Code Review subdirectory READMEs** with language comparison tables

  - All 6 subdirectory READMEs now show all available language templates in table format

  - Improved navigation and language template discovery

### Documentation
- Added [COMPLETION_STATUS_AND_PLAN.md](COMPLETION_STATUS_AND_PLAN.md) with detailed gap analysis

- Documents current completion status (47% complete overall)

- Provides systematic plan for reaching v0.2.0

### Technical Details
- **Code Cleanup**: 7 language-specific templates

- **Code Review**: 42 comprehensive templates across 7 languages

- **Languages**: Python, JavaScript/TypeScript, Java, C#, Go, C, C++

- **Tool Integration**: Language-specific linters, formatters, profilers, security scanners

---

## [0.1.4] - 2025-10-08

### Added
- **Complete Code Review Templates** (6 phases, 13 files)

  - Context Analysis: Project structure, architecture, dependencies

  - Code Quality: Complexity, maintainability, coding standards

  - Security Review: OWASP Top 10, vulnerability scanning, secrets detection

  - Performance Review: Profiling, bottleneck identification, optimization

  - Testing Review: Coverage analysis, test quality, flaky test detection

  - Final Report: Consolidated findings with prioritized action plan

- **Complete Documentation Templates** (6 phases, 13 files)

  - Docstrings: Module, class, and function documentation (Google/NumPy/Sphinx styles)

  - Comments: Strategic commenting guidelines (explain "why" not "what")

  - User Docs: README, installation guides, quick starts, tutorials

  - Technical Docs: Architecture, ADRs, design decisions, codebase walkthroughs

  - API Docs: OpenAPI/Swagger, endpoint documentation, authentication

  - SBOM Generation: NTIA compliance, EU CRA, CycloneDX/SPDX formats

- **Complete Test Development Templates** (6 phases, 13 files)

  - Test Structure: Framework setup, organization, conftest.py hierarchy

  - Test Cases: Unit/integration/e2e tests, AAA pattern, parametrized tests

  - Mocks & Fixtures: pytest fixtures, unittest.mock, test data factories

  - Performance Testing: Load testing (Locust), benchmarking (pytest-benchmark)

  - Maintenance & CI/CD: GitHub Actions, quality gates, flaky test detection

  - Code Coverage: 80%+ target, coverage.py, gap analysis, CI/CD integration

### Changed
- Updated main README with version 0.1.4 and complete template coverage

- Enhanced navigation with direct links to all subdirectory READMEs

### Technical Details
- **Total Files Created**: 39 markdown files

- **Documentation Lines**: ~25,000+ lines of comprehensive templates

- **Phase Structure**: Consistent multi-phase approach across all templates

- **Tool Integration**: pytest, coverage.py, bandit, safety, pip-audit, locust, GitHub Actions

- **Coverage Standards**: 80%+ code coverage, OWASP Top 10 security, performance profiling

---

## [0.1.2] - 2025-10-07

### Changed
- Refreshed `code_review/README.md` with quick navigation, depth-based review modes, and prompt deep links.

- Condensed `documentation/README.md` into a six-phase handbook featuring compliance and maintenance guidance.

- Modernized `test_development/README.md` with build paths, tooling summaries, and CI/CD quality gates.

---

## [0.1.0] - 2025-10-07

### Added

#### Repository Structure
- **Phase-based directory organization** for code_review, test_development, and documentation

- Individual directories for each phase with dedicated READMEs

- Fully clickable navigation structure throughout repository

- Consistent naming pattern: `phase_name/python_phase_name.md`

#### Code Review Templates (6 Phases)
- Phase 1: Context Analysis & Initial Assessment

- Phase 2: Code Quality Review

- Phase 3: Security Review

- Phase 4: Performance Review

- Phase 5: Testing Review

- Phase 6: Final Report & Recommendations

- Python templates for all phases with copy-paste prompts

- Comprehensive checklists and evaluation criteria

- Time estimates: 1-16 hours depending on depth

#### Test Development Templates (6 Phases)
- Phase 1: Test Structure & Organization

- Phase 2: Test Case Development

- Phase 3: Mock & Fixture Management

- Phase 4: Performance & Load Testing

- Phase 5: Test Maintenance & CI/CD Integration

- Phase 6: Code Coverage Analysis & Improvement

- Python templates with master test runner patterns

- TestResultAggregator and PerformanceTimer utilities

- Coverage analysis tools and CI/CD workflows

- Time estimates: 8-15 hours for complete implementation

#### Documentation Templates (6 Phases)
- Phase 1: Docstrings & Code Documentation

- Phase 2: Strategic Code Comments

- Phase 3: User Documentation (README, CHANGELOG, guides)

- Phase 4: Technical Documentation (architecture, design decisions)

- Phase 5: API Reference Documentation

- Phase 6: SBOM & Dependency Documentation

- Python templates for all documentation types

- SBOM generation with CycloneDX/SPDX formats

- Compliance templates (NTIA, EU Cyber Resilience Act)

- Time estimates: 8-15 hours for complete documentation

#### System Prompts
- Comprehensive system prompts (~35k tokens) for autonomous agents

- Condensed system prompts (15-20k tokens) for coding assistants

- Platform-specific configurations:

  - GitHub Copilot (`.github/copilot-instructions.md`)

  - Cursor (`.cursorrules` via User Rules)

  - Windsurf (`global_windsurf.md` via Rules)

  - Claude Code (`CLAUDE.md`)

- Separate prompts for autonomous agents and coding assistants

- Python-focused with organizational coding standards

#### Navigation & Usability
- 18 phase-specific READMEs with objectives and success criteria

- 3 main section READMEs with clickable directory structures

- Main repository README with direct links to all phases

- Consistent back-navigation links throughout

- Visual directory trees showing complete structure

#### Documentation & Guides
- Getting Started sections for each template category

- Quick reference guides for time investment planning

- Best practices and customization guidelines

- Contributing guidelines

- Platform setup instructions for system prompts

### Features

#### Code Review
- Health score assessment (1-5 scale)

- Deployment recommendations (Go/No-Go/Conditional)

- Prioritized action plans (Critical/High/Medium/Low)

- Technical debt quantification

- Risk assessment with mitigation strategies

- Educational feedback approach

- AI-assisted review prompts

#### Test Development
- Master test runner with auto-discovery

- Standardized output formatting (100-char separators, box-drawing)

- Timeout protection for tests

- Mock patterns for databases, APIs, file systems

- Performance testing with percentile analysis (p95, p99)

- Concurrent load testing with ThreadPoolExecutor

- GitHub Actions and Jenkins workflow templates

- Coverage threshold enforcement (80%+ standards)

- Coverage trend tracking and reporting

#### Documentation
- Simple and complex docstring templates

- Strategic commenting guidelines (no inline, explain "why")

- README, CHANGELOG, DEVLOG structures

- Architecture documentation with diagram templates

- Complete API reference format

- CycloneDX/SPDX SBOM generation

- Vulnerability scanning integration (pip-audit, Safety, Snyk, Trivy)

- License compliance tracking

- Third-party attribution notices

### Technical Details

#### Organizational Standards Integration
- Black formatter compliance (88-char line length)

- Import organization (standard library, third-party, local)

- No inline comments policy

- Type hints for all public functions

- Comprehensive docstrings with authors attribution

- Function design patterns and naming conventions

- Error handling and validation standards

#### Quality Metrics
- Code review: 150+ evaluation points across 6 phases

- Test development: 80%+ coverage target, <2s per test

- Documentation: Complete coverage from code to compliance

- Time-based success criteria for each phase

#### CI/CD Integration
- GitHub Actions workflows for testing and coverage

- Jenkins pipeline configurations

- GitLab CI templates

- Pre-commit hooks

- Quality gate enforcement

- Automated SBOM generation

- Coverage reporting with Codecov/Coveralls integration

### Repository Statistics
- **Total Templates**: 18 phase templates (6 per section)

- **Total READMEs**: 22 (1 main + 3 section + 18 phase)

- **Languages Supported**: Python (complete)

- **Total Documentation**: ~50,000+ lines of templates and guides

- **Clickable Links**: 100+ navigation links throughout repository

---

## Version History Summary

| Version | Date       | Description                                      |
|---------|------------|--------------------------------------------------|
| 0.8.1   | 2026-03-04 | **Output Formatting**: No-hard-wrap rule across all AI instruction templates |
| 0.8.0   | 2026-03-03 | **Catalog Expansion**: 19 new skills (Architecture, AI Development, Framework Specialists), bundles, workflows |
| 0.7.1   | 2026-03-03 | **Template Hygiene**: No-AI-attribution rules, shell command clarity across all instruction templates |
| 0.7.0   | 2026-02-27 | **Context Engineering**: 8 new skills, template rendering system, coding snippets, installer V9, report generator overhaul |
| 0.6.3   | 2026-02-20 | **Word/PPTX Reports**: Generate Word and PowerPoint documents from Markdown, template system, installer Phase 4 |
| 0.6.2   | 2026-02-19 | **CLI Usage Display**: Stop hook for usage limits, generate-changelog command, command catalog overhaul, documentation updates |
| 0.6.1   | 2026-02-19 | **Git Guardrails**: PreToolUse hook blocking destructive git commands, tracer bullets workflow, cross-platform git safety rules |
| 0.6.0   | 2026-02-10 | **Claude Usage Monitor**: VS Code extension, code review overhaul, skills registry validation, documentation fixes |
| 0.5.3   | 2026-02-04 | **Documentation Fixes**: Fixed broken paths, removed legacy `.codex`/`.gemini` artifacts, consolidated commands |
| 0.5.2   | 2026-01-30 | **Enhanced Reporting**: DOCX report output, `/upgrade-version` auto-analysis, Claude Skills README section |
| 0.5.1   | 2026-01-28 | **Cross-Platform**: macOS/Linux Bash installer (`install.sh`) |
| 0.5.0   | 2026-01-28 | **Universal Catalog**: Single `catalog/` source of truth, Installer V5 rewrite, 6 new commands |
| 0.4.0   | 2026-01-07 | **Repository Restructuring**: Simplified structure, kebab-case naming, skills catalog at root |
| 0.3.3   | 2026-01-05 | **Expanded Skills**: 13 new specialist skills, subagents integration |
| 0.3.2   | 2025-12-09 | **Simplified Templates**: Consolidated coding assistant templates, GitHub Copilot format |
| 0.3.1   | 2025-12-08 | **Compliance & Governance**: 96 templates for SOC 2, ISO 27001, GDPR, AI governance |
| 0.3.0   | 2025-12-04 | **Google Test Integration**: VS Code + GitHub Copilot workflow for C++ testing |
| 0.2.9   | 2025-11-06 | **Quality Enhancements**: Severity classification, stopping criteria, phase diagrams |
| 0.2.8   | 2025-11-06 | **Testing Complete**: Unit Tests + Reward Hacking phases (16 files, 8-phase testing methodology) |
| 0.2.7   | 2025-10-21 | Discovery & Installation System: Skills catalog, CLI tool, web browser, comprehensive onboarding |
| 0.2.6   | 2025-10-20 | **Claude Code Skills**: 52 production-ready skills + directory rename (system_prompts → agent_prompts) |
| 0.2.5   | 2025-10-16 | System prompt enhancements: Added 4 critical instructions, renamed _35k to _40k |
| 0.2.4   | 2025-10-10 | Template cleanup: Fixed Bitbucket rendering, removed redundant sections |
| 0.2.3   | 2025-10-10 | Directory structure optimization: Simplified to 3 subdirectories with OUTPUT_DIR variable |
| 0.2.2   | 2025-10-10 | Bitbucket migration: Repository-agnostic templates with improved formatting |
| 0.2.1   | 2025-10-09 | Standardized output directory structures for all 133 templates |
| 0.2.0   | 2025-10-09 | **COMPLETE** - Multi-language expansion: 162 templates across 7 languages |
| 0.1.5   | 2025-10-08 | Code cleanup (7 languages) + Complete code review (42 files) |
| 0.1.4   | 2025-10-08 | Complete templates for code review, documentation, and test development (Python only) |
| 0.1.2   | 2025-10-07 | README refinements across review, docs, and tests |
| 0.1.0   | 2025-10-07 | Initial release with complete Python templates   |

---

[Unreleased]: https://github.com/bendourthe/DevAI-Hub/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/bendourthe/DevAI-Hub/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/bendourthe/DevAI-Hub/compare/v1.2.0...v1.2.1
[1.1.5]: https://github.com/bendourthe/DevAI-Hub/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/bendourthe/DevAI-Hub/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/bendourthe/DevAI-Hub/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/bendourthe/DevAI-Hub/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/bendourthe/DevAI-Hub/compare/v1.1.0...v1.1.1
[0.9.2]: https://github.com/bendourthe/DevAI-Hub/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/bendourthe/DevAI-Hub/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.9...v0.9.0
[0.8.9]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.8...v0.8.9
[0.8.8]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.7...v0.8.8
[0.8.7]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.6...v0.8.7
[0.8.6]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.5...v0.8.6
[0.8.5]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.4...v0.8.5
[0.8.4]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.3...v0.8.4
[0.8.3]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/bendourthe/DevAI-Hub/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/bendourthe/DevAI-Hub/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/bendourthe/DevAI-Hub/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/bendourthe/DevAI-Hub/compare/v0.6.3...v0.7.0
[0.6.3]: https://github.com/bendourthe/DevAI-Hub/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/bendourthe/DevAI-Hub/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/bendourthe/DevAI-Hub/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.6.0
[0.5.3]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.5.3
[0.5.2]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.5.2
[0.5.1]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.5.1
[0.5.0]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.5.0
[0.4.0]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.4.0
[0.3.3]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.3.3
[0.3.2]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.3.2
[0.3.1]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.3.1
[0.3.0]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.3.0
[0.2.9]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.9
[0.2.8]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.8
[0.2.7]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.7
[0.2.6]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.6
[0.2.5]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.5
[0.2.4]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.4
[0.2.3]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.3
[0.2.2]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.2
[0.2.1]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.1
[0.2.0]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.2.0
[0.1.5]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.1.5
[0.1.4]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.1.4
[0.1.2]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.1.2
[0.1.0]: https://github.com/bendourthe/DevAI-Hub/releases/tag/v0.1.0
