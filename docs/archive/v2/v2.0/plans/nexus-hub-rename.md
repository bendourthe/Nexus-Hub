# Plan -- Rename DevAI-Hub to Nexus-Hub and Modernize Branding

**Project**: Nexus-Hub (previously DevAI-Hub)
**Version**: v2.0.0
**Slug**: nexus-hub-rename
**Plan Type**: Refactor + Feature (rename + brand modernization)
**Created**: 2026-05-19
**Goal**: Rename the repository, distributed artifact, plugin metadata, installer, MCP servers, extensions, scripts, all 203 skills, 33 commands, 14 hooks, 10 agents, rules, templates, and every documentation surface from "DevAI-Hub" / "devai-hub" to "Nexus-Hub" / "nexus-hub"; modernize the README around the new brand with the Nexus logo and explicit linkage to the sibling Nexus desktop app; redesign the installer to print an ASCII-art "Nexus-Hub" banner and migrate users cleanly from `~/.devai-hub/` to `~/.nexus-hub/`.

## Overview

DevAI-Hub is being renamed to **Nexus-Hub** to align with the sibling product **Nexus** (the local-first desktop AI Studio at `C:\Users\bdour\Documents\Projects\Development\Nexus-AI`, v1.0.0 pivot from Gemma Code v0.22.x). The two projects are deliberately connected: Nexus's `AGENTS.md` already names DevAI-Hub as "the only external project we deliberately link to" and "the upstream feed for Nexus's skill harness". After this rename, Nexus-Hub becomes the unified harness catalog consumed by every supported agentic platform: Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, GitHub CLI, and the Nexus desktop app and VS Code extension. The two README files will cross-link in both directions so the relationship is obvious to anyone landing on either repo.

The rename is a **breaking change**: the installed root moves from `~/.devai-hub/` to `~/.nexus-hub/`, the plugin name in `.claude-plugin/plugin.json` changes from `devai-hub` to `nexus-hub`, internal MCP server names change (`devai-skill-server` to `nexus-skill-server`, etc.), all environment-variable prefixes change (`DEVAI_HUB_*` to `NEXUS_HUB_*`), and the four catalog skill/extension directory names that carry the brand are renamed on disk. Because none of those surfaces have a SemVer-stable contract today, the migration is handled by the installer itself - a one-shot detect-and-relocate pass at the top of both `installer.sh` and `installer.ps1` moves a user's existing global install in place and prints a single notice. The installer's modernized header includes an ASCII-art "NEXUS-HUB" wordmark (in the spirit of the Claude Code CLI banner), a tagline, version label, and the four supported-agent badges.

The README is rewritten from scratch around the new brand: a hero block with the Nexus logo (sourced from `C:\Users\bdour\Documents\Projects\Development\Nexus-AI\assets\nexus_primary.png`), a clear "What is Nexus-Hub?" positioning paragraph, a "Why two projects" callout that links to Nexus, an updated platform compatibility matrix, the modernized Quick Start, and a v2.0.0 What's New entry that frames the rename as the headline change. Every `/update-*` slash command listed in the user's request (`/update-documentation`, `/update-config`, `/update-devlog`, `/update-gitignore`) is invoked as part of Phase 7 to fan the rename through the rest of the documentation, configuration, devlog, and gitignore surfaces. This plan also ingests 2 carry-forward items from `docs/archive/v1/v1.3/known-gaps.md` (WN-001 framework-specialist orphan-bundle warnings, WN-002 Windows `make`/`shellcheck` environment workaround) and closes them out in Phase 8 hygiene.

Success is defined as: a clean installer run on a fresh machine produces `~/.nexus-hub/` with every skill, command, hook, agent, and rule landing at the new paths; an existing `~/.devai-hub/` install is migrated in place with one user-visible prompt; `grep -rn "DevAI-Hub\|devai-hub\|devai_hub\|DEVAI_HUB" --include="*"` returns zero matches outside `docs/archive/` and `CHANGELOG.md` historical blocks; `make validate`, `make lint`, and `make test` are all green; the new README opens with the Nexus logo and an obvious link to the Nexus sibling repo; and a fresh `git tag v2.0.0` has been cut.

This plan ingests 2 items carried forward from prior known-gaps files: see sub-tasks tagged `[from v1.3.0 known-gaps: ...]`.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1     | Foundation, Inventory, Naming Canon | Authoritative rename map, baseline validators green, backward-compat decision recorded |
| 2     | Catalog Metadata and `data/` Registries | `plugin.json`, `marketplace.json`, `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`, `data/bundles.json` all carry the new name |
| 3     | Installer Rebrand + ASCII Banner + Migration | Both installers print a NEXUS-HUB ASCII banner, write to `~/.nexus-hub/`, and migrate `~/.devai-hub/` |
| 4     | Extensions, Internal MCPs, `scripts/` Rename | All 3 extension dirs and their Python packages renamed; MCP server registry updated; `devai_mcp_benchmark.py` and `Install-DevAI-Permissions.ps1` renamed |
| 5     | Hooks, Commands, Skills, Rules, Templates Sweep | Bulk textual rename across `catalog/`, all 5 `templates/ai-instructions/base-*.md` updated in lockstep, `.cursor/rules/devai-hub.mdc` renamed |
| 6     | README Modernization + Nexus Logo + Brand Linkage | New README hero with `nexus_primary.png` copied into `assets/`, prominent Nexus connection block, updated platform matrix |
| 7     | Docs / Config / DevLog / Gitignore Sync + CHANGELOG | `/update-documentation`, `/update-config`, `/update-devlog`, `/update-gitignore` runs; v2.0.0 CHANGELOG block and `RELEASE_NOTES.md` written |
| 8     | Validation, Carry-Forward Known-Gaps, Version Bump | All validators green; WN-001/WN-002 closed or explicitly re-deferred with reason; `1.4.0` -> `2.0.0` across single-source-of-truth files; `git tag v2.0.0` and session history |

---

## Phase 1: Foundation, Inventory, Naming Canon

**Goal**: Produce an authoritative rename map (every variant -> its replacement), capture a baseline validator run so the rename can be diff'd against a known-good state, and decide the backward-compatibility policy in writing.
**Prerequisites**: None.
**Stability Gate**: `make validate` and `make lint` pass on `main` at the current `v1.4.0` head, the rename map is committed at `docs/archive/v2/v2.0/rename-map.md`, and the backward-compat decision (in-place installer migration, no shim or symlink) is recorded in the same file.

### Sub-tasks

#### 1.1 -- Capture baseline validator state

**Objective**: Record a green baseline of the pre-rename repository so the post-rename runs can be diff'd against it.

**Prompt**:
> You are starting Phase 1 of the rename plan at `docs/archive/v2/v2.0/plans/nexus-hub-rename.md`. The goal of this sub-task is to capture the **pre-rename baseline** so that after the rename we can prove nothing else regressed. Do the following:
>
> 1. Confirm the current branch is clean (`git status` shows no modifications). If dirty, stop and ask for instructions.
> 2. Run `python scripts/validate_skills.py --bundles-only` and capture the full output to `docs/archive/v2/v2.0/baselines/validate-skills-pre.txt`. On Windows the user's environment has `PYTHONUTF8=1` mismatch issues (carry-over WN-002); if `make validate` fails with cp1252 errors, fall back to direct `python` invocation with `set PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8=1`) and document this in the baseline file.
> 3. Run `python -m pytest catalog/hooks/tests -q` and capture to `docs/archive/v2/v2.0/baselines/hook-tests-pre.txt`. Expected baseline per `docs/archive/v1/v1.3/known-gaps.md`: **366 passed, 3 skipped**.
> 4. For each of `extensions/devai-skill-server`, `extensions/devai-code-search`, `extensions/devai-web-fetch`, run the project's test command (see the per-extension `pyproject.toml` for the entry point - typically `python -m pytest -q`) and capture to `docs/archive/v2/v2.0/baselines/extension-tests-pre.txt`. Expected per `docs/archive/v1/v1.3/known-gaps.md`: **37 + 36(1s) + 23 passed**.
> 5. Commit all three baseline files in a single commit with message `chore(v2.0.0): capture pre-rename validator baselines`.
>
> **Constraints**: Do not modify any catalog, extension, installer, or doc file in this sub-task. The point is a frozen baseline. If any validator fails, document the failure in the baseline file and stop - the rename cannot start from a broken baseline.

---

#### 1.2 -- Inventory every rename surface

**Objective**: Produce a complete enumeration of files, directories, env vars, package names, and string variants that need to change.

**Prompt**:
> Build the authoritative rename inventory at `docs/archive/v2/v2.0/rename-inventory.md`. Required sections:
>
> 1. **Directory renames** (run `find . -type d -name "*devai*"` excluding `node_modules` and `.git`): list each old -> new path. Confirmed list: `catalog/skills/workflow/using-devai-hub` -> `using-nexus-hub`, `extensions/devai-code-search` -> `extensions/nexus-code-search`, `extensions/devai-skill-server` -> `extensions/nexus-skill-server`, `extensions/devai-web-fetch` -> `extensions/nexus-web-fetch`, plus each `src/devai_<name>` Python package dir nested inside.
> 2. **File renames** (run `find . -type f -name "*devai*"` excluding the same): `scripts/devai_mcp_benchmark.py` -> `scripts/nexus_mcp_benchmark.py`, `scripts/Install-DevAI-Permissions.ps1` -> `scripts/Install-Nexus-Hub-Permissions.ps1`, `.cursor/rules/devai-hub.mdc` -> `.cursor/rules/nexus-hub.mdc`.
> 3. **String variant table**: list each casing/spacing variant and its replacement. The table must cover at minimum: `DevAI-Hub` -> `Nexus-Hub`, `DevAI Hub` -> `Nexus Hub`, `DEVAI-HUB` -> `NEXUS-HUB`, `devai-hub` -> `nexus-hub`, `devai_hub` -> `nexus_hub`, `DEVAI_HUB` -> `NEXUS_HUB`, `devai` -> `nexus` (only inside `devai_*` package and identifier contexts -- NOT inside the word "individual" or other false positives; flag this for manual review).
> 4. **Cross-link targets**: the Nexus README at `C:\Users\bdour\Documents\Projects\Development\Nexus-AI\README.md` references `bendourthe/DevAI-Hub` (GitHub URL). Note that after the rename the GitHub repo URL will change to `bendourthe/Nexus-Hub` and Nexus's README must be updated in a coordinated follow-up commit on that repo (out of scope for this plan, but documented as a downstream task).
> 5. **Asset transfer**: the file `C:\Users\bdour\Documents\Projects\Development\Nexus-AI\assets\nexus_primary.png` will be copied into this repo's `assets/` directory for the README hero in Phase 6.
> 6. **Reference count** (informational): run `grep -rln "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" 2>/dev/null | grep -v "^./node_modules\|^./.git/" | wc -l` and `grep -rn ...` to record total file count and total line count for the rename surface. Pre-rename count is approximately 171 files / 1432 references (from the planning interview).
>
> Commit as `docs(v2.0.0): rename inventory and authoritative variant table`.

---

#### 1.3 -- Naming canon and backward-compat decision

**Objective**: Resolve every ambiguity about how the new name is written and decide what to do for users with an existing install.

**Prompt**:
> Write `docs/archive/v2/v2.0/rename-decisions.md` covering:
>
> 1. **Canonical name forms**, locked: `Nexus-Hub` (display, prose), `Nexus Hub` (UI/marketing two-word form), `nexus-hub` (kebab id, plugin name, npm-style), `nexus_hub` (snake id, Python identifiers), `NEXUS_HUB` (env-var prefix), `NEXUS-HUB` (ASCII-banner wordmark).
> 2. **GitHub repo URL**: the canonical URL is `https://github.com/bendourthe/Nexus-Hub`. Old URL `https://github.com/bendourthe/DevAI-Hub` will redirect via GitHub's automatic rename redirect; the redirect is best-effort - all in-repo string references must be updated.
> 3. **Installed root**: `~/.nexus-hub/` (mirrors the existing `~/.devai-hub/` layout exactly - no schema change inside).
> 4. **MCP server name prefix**: `nexus-<purpose>` (so `devai-skill-server` -> `nexus-skill-server`, etc.). The Python package follows the same: `nexus_skill_server`.
> 5. **Backward-compatibility policy** (decision: **in-place installer migration, no symlinks, no shims**):
>    - On installer start, detect `~/.devai-hub/`. If found and `~/.nexus-hub/` does NOT exist, prompt: "Detected existing DevAI-Hub install. Migrate to Nexus-Hub? [Y/n]". On Y (default), rename the directory in place. On N, abort and tell the user to either remove `~/.devai-hub/` manually or re-run with a force flag.
>    - If both `~/.devai-hub/` AND `~/.nexus-hub/` exist, prompt the user to choose: keep new and delete old, keep old and abort, or merge (warn that merge is best-effort).
>    - The migration is one-shot and one-way - we do NOT ship a symlink, alias, or compatibility shim. Reason: the rename is a major version bump and SemVer permits breaking changes. A shim doubles maintenance surface; an installer migration is a single user-visible event.
>    - Environment variables: any user-set `DEVAI_*` env vars become `NEXUS_*`; the installer prints a migration hint listing the variables it found in the user's shell rc files (best-effort detection via `grep DEVAI_ ~/.bashrc ~/.zshrc ~/.profile $PROFILE 2>/dev/null`). The installer does NOT modify shell rc files - that is left to the user.
> 6. **Version semantics**: this rename is a SemVer **major** bump (`v1.4.0` -> `v2.0.0`). The CHANGELOG entry must list every breaking change explicitly under a "Breaking changes" subsection (installed root path, plugin name, MCP server names, env-var prefix, extension package names, GitHub URL).
>
> Commit as `docs(v2.0.0): naming canon and backward-compatibility decision`.

---

#### 1.4 -- Phase 1 stability gate

**Objective**: Confirm Phase 1 artifacts are in place and the repository is ready for the textual rename work.

**Prompt**:
> Verify Phase 1 completeness:
>
> 1. `docs/archive/v2/v2.0/baselines/validate-skills-pre.txt`, `hook-tests-pre.txt`, and `extension-tests-pre.txt` exist and show green baselines (allowing the documented WN-001 / WN-002 carry-overs).
> 2. `docs/archive/v2/v2.0/rename-inventory.md` exists, lists every directory/file rename, the variant table, the reference count, and the asset-transfer line for `nexus_primary.png`.
> 3. `docs/archive/v2/v2.0/rename-decisions.md` exists and locks the canonical name forms, repo URL, installed root, MCP prefix, backward-compat policy, and version-bump rationale.
> 4. `git status` is clean.
>
> If any of the four items are missing or incomplete, return to the relevant sub-task. Once green, proceed to Phase 2.

---

### Phase 1 Exit Checklist

- [ ] Pre-rename validator baselines captured under `docs/archive/v2/v2.0/baselines/`
- [ ] Rename inventory committed at `docs/archive/v2/v2.0/rename-inventory.md`
- [ ] Naming canon and backward-compat decision committed at `docs/archive/v2/v2.0/rename-decisions.md`
- [ ] Working tree clean
- [ ] Ready to advance to Phase 2

---

## Phase 2: Catalog Metadata and `data/` Registries

**Goal**: Rename every machine-readable catalog metadata field so downstream installers, MCP servers, and IDE integrations see the new name first, before any textual sweep.
**Prerequisites**: Phase 1.
**Stability Gate**: `make validate` passes, `data/skills.json` parses as valid JSON with the new name, `python scripts/validate_skills.py --bundles-only` passes with no new warnings.

### Sub-tasks

#### 2.1 -- Update `.claude-plugin/plugin.json` and `marketplace.json`

**Objective**: Rename the plugin's canonical identifier, display name, repo URL, and homepage.

**Prompt**:
> Edit `.claude-plugin/plugin.json`:
>
> - `name`: `devai-hub` -> `nexus-hub`
> - `description`: replace "Enterprise-grade skill library for AI coding assistants" with: "Enterprise-grade skill harness for AI coding assistants -- the upstream catalog for the Nexus desktop app and every major agent (Claude Code, OpenAI Codex, Gemini, GitHub Copilot, Cursor, GitHub CLI). 203+ curated skills, 33 commands, 14 hooks, cross-platform."
> - `homepage`, `repository`: update both to `https://github.com/bendourthe/Nexus-Hub`
>
> Edit `.claude-plugin/marketplace.json`:
>
> - `name`: `devai-hub` -> `nexus-hub`
> - `displayName`: `DevAI Hub` -> `Nexus Hub`
> - `description`: same replacement text as above
> - `repository`, `homepage`: update to the new GitHub URL
>
> Leave the `version` field at `1.4.0` for now - the version bump happens in Phase 8 sub-task 8.5 as the final commit before the v2.0.0 tag.
>
> Validate JSON syntax after the edit: `python -c "import json; json.load(open('.claude-plugin/plugin.json'))"` and the same for `marketplace.json`. Commit as `feat(v2.0.0): rename plugin metadata to nexus-hub`.

---

#### 2.2 -- Update `data/skills.json`, `marketplace.json`, `bundles.json`, `SKILL_INDEX.md`

**Objective**: Rename the catalog registries so any IDE integration that consumes them sees the new name.

**Prompt**:
> The four files under `data/` are partially generated. Per `AGENTS.md`, manual edits to `data/*` are normally forbidden EXCEPT when registering a new skill - but a rename of the catalog itself qualifies as a registry edit and is permitted under this plan.
>
> Approach: perform a textual find/replace using the variant table from `docs/archive/v2/v2.0/rename-inventory.md`, then re-run `make build-catalog` (if the Makefile target exists and works on the current OS) to verify the registries can still be regenerated cleanly.
>
> Steps:
>
> 1. Apply the variant replacements to `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`, `data/bundles.json`. Variants to replace: `DevAI-Hub`, `DevAI Hub`, `devai-hub`, `devai_hub`, `DEVAI_HUB`, `DEVAI-HUB`. Do NOT blindly replace `devai` standalone - audit each match before applying.
> 2. The `using-devai-hub` skill name appears in `data/skills.json` and `data/SKILL_INDEX.md` and must become `using-nexus-hub` consistently. The directory rename itself happens in Phase 5 sub-task 5.3.
> 3. Validate each JSON file: `python -c "import json; json.load(open('<file>'))"`.
> 4. If `make build-catalog` works in this environment, run it and diff the output against the manually-edited files; any drift indicates the source-of-truth is `catalog/`, not `data/`, and the manual edits must be re-applied AFTER the Phase 5 catalog sweep. In that case, defer this sub-task to after Phase 5 and document the deferral here.
> 5. Run `python scripts/validate_skills.py --bundles-only` and confirm the run is green (4 known orphan warnings allowed per WN-001).
>
> Commit as `feat(v2.0.0): rename catalog registries under data/ to nexus-hub`.

---

#### 2.3 -- Update root-level config files

**Objective**: Rename references in `.pr_agent.toml`, `Makefile`, and any other root-level config that ships brand strings.

**Prompt**:
> Apply variant replacements from `docs/archive/v2/v2.0/rename-inventory.md` to:
>
> - `.pr_agent.toml`
> - `Makefile` (look for inline help text, target descriptions, comments)
> - `.github/copilot-instructions.md` (this is the per-IDE instruction file for GitHub Copilot users - high-visibility surface)
> - Any other root-level `*.toml`, `*.yml`, `*.yaml`, `*.cfg`, `*.ini` discovered via `git ls-files | grep -E '^\.?[^/]+\.(toml|yml|yaml|cfg|ini)$'`
>
> Do NOT edit `.gitignore` in this sub-task (Phase 7 handles that via `/update-gitignore`).
>
> Validate any TOML/YAML files parse: `python -c "import tomllib; tomllib.load(open('.pr_agent.toml','rb'))"` for TOML, `python -c "import yaml; yaml.safe_load(open('<file>'))"` for YAML.
>
> Commit as `feat(v2.0.0): rename root-level configs to nexus-hub`.

---

#### 2.4 -- Update root `AGENTS.md` and `CLAUDE.md`

**Objective**: The two top-level AI-agent instruction files are the most-read documents in the repo. They need to carry the new name and frame Nexus-Hub's role clearly.

**Prompt**:
> Edit `AGENTS.md`:
>
> 1. Replace the opening "Repository Overview" paragraph to read: "Nexus-Hub is a production-grade skill harness for AI coding assistants. It is the **upstream catalog** consumed by Nexus (the local-first desktop AI Studio, see `https://github.com/bendourthe/Nexus-AI`) and by every other major agent platform: Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, and GitHub CLI. Skills, commands, hooks, agents, and rules are distributed via installer scripts into users' `~/.nexus-hub/` directory and into their AI assistant's per-platform config locations."
> 2. Replace every other `DevAI-Hub` / `devai-hub` / `devai_hub` / `DEVAI_HUB` occurrence per the variant table.
> 3. Update the "Distribution channels the installer uses" table footer and any path examples that reference `~/.devai-hub/` to `~/.nexus-hub/`.
>
> Edit `CLAUDE.md` (which `@imports` AGENTS.md): change the headline `# Claude Code Instructions -- DevAI-Hub` to `# Claude Code Instructions -- Nexus-Hub`. Update the inline reference: rule 3's "the installer copies `catalog/style-guides/` to `~/.devai-hub/style-guides/`" -> "to `~/.nexus-hub/style-guides/`".
>
> Do NOT touch any other file in this sub-task - this is scoped specifically to the two top-level agent instruction files so that subsequent sub-tasks read them with the new name already in place.
>
> Commit as `docs(v2.0.0): rename top-level agent instruction files to nexus-hub`.

---

#### 2.5 -- Phase 2 stability gate

**Objective**: Confirm catalog metadata is internally consistent and validators are still green.

**Prompt**:
> Run:
>
> 1. `python -c "import json; [json.load(open(f)) for f in ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', 'data/skills.json', 'data/marketplace.json', 'data/bundles.json']]"` - confirm all five files parse.
> 2. `python scripts/validate_skills.py --bundles-only` - confirm green baseline (WN-001 orphan warnings allowed).
> 3. `grep -l "DevAI-Hub\|devai-hub" .claude-plugin/*.json data/*.json data/SKILL_INDEX.md AGENTS.md CLAUDE.md .pr_agent.toml Makefile .github/copilot-instructions.md` - this should return NOTHING.
>
> If the grep returns any match, fix it and re-run. Commit any fixups as `fix(v2.0.0): residual rename misses in catalog metadata`.

---

### Phase 2 Exit Checklist

- [ ] `.claude-plugin/plugin.json` and `marketplace.json` renamed
- [ ] All four `data/` registry files renamed and parsing
- [ ] Root-level configs (`.pr_agent.toml`, `Makefile`, copilot-instructions) renamed
- [ ] `AGENTS.md` and `CLAUDE.md` renamed with the new positioning paragraph
- [ ] `make validate` (or equivalent) green
- [ ] Ready to advance to Phase 3

---

## Phase 3: Installer Rebrand + ASCII Banner + Migration Path

**Goal**: Both `installer.sh` and `installer.ps1` carry the new name, print an ASCII-art `NEXUS-HUB` banner at startup, write to `~/.nexus-hub/`, and offer a one-shot migration from `~/.devai-hub/`. The `install.sh` and `install.bat` entry points also get the new branding.
**Prerequisites**: Phase 2.
**Stability Gate**: `catalog/hooks/tests/test_installer_smoke.py` passes; both installers can be invoked with `--help` or similar dry-run mode and print the new banner; a manual dry-run of `installer.sh` and `installer.ps1` writes to `~/.nexus-hub/` (use a throwaway HOME via env var, e.g. `HOME=/tmp/test-nexus ./scripts/installer.sh`).

### Sub-tasks

#### 3.1 -- Design and embed the ASCII-art banner

**Objective**: Add a "NEXUS-HUB" character-art wordmark at the very top of both installer scripts, modeled after the Claude Code CLI banner style.

**Prompt**:
> Generate an ASCII-art banner for "NEXUS-HUB" using one of: `figlet -f slant`, `figlet -f standard`, `figlet -f ANSI Shadow`, or a hand-crafted minimal block style. Constraints:
>
> - Maximum 80 columns wide (terminals narrower than 80 should still render cleanly; if the banner overflows, fall back to a single-line text title).
> - Maximum 8 rows tall.
> - ASCII characters only (no Unicode block-drawing). Reason per project rules: commit messages and source files are ASCII-only on Windows.
> - The banner must be wrapped in a function in `installer.sh` and `installer.ps1` so it can be invoked at startup and reused.
>
> In `scripts/installer.sh`:
>
> 1. Add a function `print_nexus_banner()` immediately after the color definitions (~line 30). Body: `echo` lines drawing the banner in `${CYAN}` color, followed by a tagline line `"  The Skill Harness for Claude Code, Codex, Gemini, Copilot, Cursor, and Nexus"`, followed by `"  v${NEXUS_HUB_VERSION}  |  https://github.com/bendourthe/Nexus-Hub"`, then `echo`.
> 2. Replace the existing `printf '\033]0;DevAI-Hub Installer\007'` line with `printf '\033]0;Nexus-Hub Installer\007'`.
> 3. Call `print_nexus_banner` near the top of `main` (or wherever the installer's main entry runs), before the welcome prompt.
>
> In `scripts/installer.ps1`:
>
> 1. Add a function `Write-NexusBanner` near the top, modeled after the existing `Write-Header` helper. Use PowerShell's `Write-Host` with the cyan foreground (`-ForegroundColor Cyan`). Include the same tagline and version + URL line.
> 2. Update the PowerShell window title (look for `$Host.UI.RawUI.WindowTitle` or equivalent) from "DevAI-Hub" to "Nexus-Hub".
> 3. Call `Write-NexusBanner` at the start of the installer's main routine.
>
> Validation: `bash scripts/installer.sh --version` (if `--version` is supported, otherwise just `--help`) should print the banner. `pwsh scripts/installer.ps1 -Version` should do the same on Windows. Capture screenshots or terminal text into `docs/archive/v2/v2.0/installer-banner-preview.md` for the record.
>
> Commit as `feat(v2.0.0): NEXUS-HUB ASCII banner in installer.sh and installer.ps1`.

---

#### 3.2 -- Rename installer variables, paths, and labels

**Objective**: Every brand string and path inside both installers becomes `nexus-hub`.

**Prompt**:
> In `scripts/installer.sh`:
>
> 1. Rename the version variable `DEVAI_HUB_VERSION` -> `NEXUS_HUB_VERSION`. Update its comment.
> 2. Rename all installed-path string literals `~/.devai-hub/` -> `~/.nexus-hub/` and `$HOME/.devai-hub/` -> `$HOME/.nexus-hub/`. There are typically several: skills target, commands target, hooks target, agents target, rules target, templates target, mcp-configs target, plus any session-state or telemetry path.
> 3. Update any environment-variable references the installer reads: `DEVAI_*` -> `NEXUS_*`. Examples to look for: `DEVAI_OLD_DOCS_GUARD`, `DEVAI_HOOKS_DEBUG`, anything else surfaced by `grep -n "DEVAI_" scripts/installer.sh`.
> 4. Replace any user-facing prose strings: "DevAI-Hub Installer V10" -> "Nexus-Hub Installer V10", section banners that say "DevAI-Hub" -> "Nexus-Hub".
>
> Apply the same set of changes to `scripts/installer.ps1` (variable names, paths, env vars, prose).
>
> Update the two root entry points `install.sh` and `install.bat`: any "DevAI-Hub" prose -> "Nexus-Hub". These are typically thin wrappers so the diff is small.
>
> Validation:
>
> - `grep -n "DevAI-Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" scripts/installer.sh scripts/installer.ps1 install.sh install.bat` must return nothing.
> - `bash -n scripts/installer.sh` (syntax check, no execution) must succeed.
> - `pwsh -NoProfile -Command "Get-Content scripts/installer.ps1 -Raw | Invoke-Expression"` is NOT a safe validation - instead use `pwsh -NoProfile -Command "[ScriptBlock]::Create((Get-Content scripts/installer.ps1 -Raw))"` to parse-check only.
>
> Commit as `feat(v2.0.0): rename installer variables, paths, and env vars to nexus-hub`.

---

#### 3.3 -- Implement the one-shot `~/.devai-hub/` -> `~/.nexus-hub/` migration

**Objective**: A user who already installed DevAI-Hub gets a single prompt at the top of their next installer run and a clean in-place rename.

**Prompt**:
> Per the backward-compat policy locked in `docs/archive/v2/v2.0/rename-decisions.md`, implement the migration logic at the very top of both installers, before any other work.
>
> In `scripts/installer.sh`, immediately after `print_nexus_banner` and BEFORE the welcome prompt, add a `migrate_legacy_install()` function and call it. Pseudocode:
>
>     migrate_legacy_install() {
>         local legacy="$HOME/.devai-hub"
>         local current="$HOME/.nexus-hub"
>         if [ -d "$legacy" ] && [ ! -d "$current" ]; then
>             echo "  ${YELLOW}Detected existing DevAI-Hub install at $legacy${RESET}"
>             echo -n "  ${YELLOW}Migrate to Nexus-Hub ($current)? [Y/n]: ${RESET}"
>             read -r ans
>             ans=${ans:-Y}
>             if [[ "$ans" =~ ^[Yy] ]]; then
>                 mv "$legacy" "$current"
>                 echo "  ${GREEN}Migrated $legacy -> $current${RESET}"
>             else
>                 echo "  ${RED}Migration declined. Remove $legacy manually or rerun with --force.${RESET}"
>                 exit 1
>             fi
>         elif [ -d "$legacy" ] && [ -d "$current" ]; then
>             echo "  ${YELLOW}Both $legacy and $current exist.${RESET}"
>             echo "  Choose: [k]eep new + delete old, [a]bort + handle manually, [m]erge (best effort): "
>             read -r ans
>             case "$ans" in
>                 k) rm -rf "$legacy" ;;
>                 m) cp -R "$legacy"/* "$current"/ && rm -rf "$legacy" ;;
>                 *) exit 1 ;;
>             esac
>         fi
>     }
>
> Implement the same in `scripts/installer.ps1` as `Invoke-LegacyInstallMigration`, using `Move-Item`, `Remove-Item -Recurse -Force`, `Copy-Item -Recurse`, and `Read-Host` per `catalog/rules/typescript/security.md` style (no `-Confirm:$true` interactives that block CI).
>
> Add a unit-test-like smoke check to `catalog/hooks/tests/test_installer_smoke.py`: a pytest function that uses `subprocess.run` to invoke `bash scripts/installer.sh --dry-run` (add a `--dry-run` flag if one does not already exist) against a tempdir HOME containing a fake `.devai-hub/` directory, and asserts the migration prompt fires. Add an equivalent for PowerShell if the test harness already supports PowerShell invocation; otherwise document the limitation in the test docstring.
>
> Commit as `feat(v2.0.0): one-shot ~/.devai-hub -> ~/.nexus-hub installer migration`.

---

#### 3.4 -- Phase 3 stability gate

**Objective**: Confirm both installers run cleanly with the new banner, paths, and migration step.

**Prompt**:
> Run:
>
> 1. `python -m pytest catalog/hooks/tests/test_installer_smoke.py -q` - confirm the new migration smoke test passes alongside the existing tests.
> 2. `bash -n scripts/installer.sh` and `bash -n install.sh` - syntax check.
> 3. Manual smoke (Linux/macOS): `HOME=$(mktemp -d) bash scripts/installer.sh` to a throwaway home. Confirm: banner prints, no legacy dir means migration is skipped, target directory `$HOME/.nexus-hub/` is created and populated.
> 4. Manual smoke (Windows, if available): in PowerShell, set `$env:HOME = "$env:TEMP\nexus-test-$(Get-Random)"`, run `pwsh scripts/installer.ps1`, confirm equivalent behavior.
>
> Capture the smoke-run output to `docs/archive/v2/v2.0/installer-smoke-pre.txt`. If any failure surfaces, fix in a follow-up commit before advancing.

---

### Phase 3 Exit Checklist

- [ ] ASCII NEXUS-HUB banner in both installers
- [ ] All installer variables, paths, env vars, prose renamed
- [ ] `install.sh` and `install.bat` entry points renamed
- [ ] One-shot legacy-install migration implemented and smoke-tested
- [ ] `test_installer_smoke.py` extended and passing
- [ ] Manual dry-run on at least one platform produces clean output
- [ ] Ready to advance to Phase 4

---

## Phase 4: Extensions, Internal MCPs, `scripts/` Rename

**Goal**: Rename the three internal extensions, their Python package directories, the MCP server registry entries, and the brand-bearing `scripts/` files.
**Prerequisites**: Phase 3.
**Stability Gate**: All three extension test suites pass with the new names; `catalog/mcp-configs/mcp-servers.json` validates as JSON and the entries point to the new server names; `python scripts/nexus_mcp_benchmark.py --help` runs without import errors.

### Sub-tasks

#### 4.1 -- Rename extension directories and packages

**Objective**: The three internal MCP servers on disk get the new brand.

**Prompt**:
> Rename:
>
> - `extensions/devai-skill-server/` -> `extensions/nexus-skill-server/`
> - `extensions/devai-code-search/` -> `extensions/nexus-code-search/`
> - `extensions/devai-web-fetch/` -> `extensions/nexus-web-fetch/`
>
> Inside each, also rename the nested Python package:
>
> - `extensions/nexus-skill-server/src/devai_skill_server/` -> `extensions/nexus-skill-server/src/nexus_skill_server/`
> - `extensions/nexus-code-search/src/devai_code_search/` -> `extensions/nexus-code-search/src/nexus_code_search/`
> - `extensions/nexus-web-fetch/src/devai_web_fetch/` -> `extensions/nexus-web-fetch/src/nexus_web_fetch/`
>
> Use `git mv` so history is preserved.
>
> Inside each extension, update all `import` statements, `from <pkg> import ...` paths, and any string references to the old package name. Critical files: `pyproject.toml` (package name, scripts entry points), `README.md`, `tests/conftest.py`, any `__init__.py`, any CLI entry point.
>
> Update each `pyproject.toml`:
>
> - `[project] name = "devai-skill-server"` -> `"nexus-skill-server"`
> - `[project.scripts]` entries: rename any `devai-*` command names to `nexus-*`
> - `[tool.setuptools.packages.find]` or equivalent package-discovery config to point at the new package dir
>
> Validation per extension:
>
> 1. `cd extensions/nexus-<name> && pip install -e . --quiet` (or the project's equivalent install) -- must succeed.
> 2. `cd extensions/nexus-<name> && python -m pytest -q` -- expected counts per `docs/archive/v1/v1.3/known-gaps.md`: skill-server 37 passed, code-search 36 passed + 1 skipped, web-fetch 23 passed.
>
> Commit per extension as `refactor(v2.0.0): rename extensions/<old> to extensions/<new>`.

---

#### 4.2 -- Update MCP server registry

**Objective**: `catalog/mcp-configs/mcp-servers.json` is the curated MCP catalog. Its entries for the three internal servers must point at the new package names and reference paths.

**Prompt**:
> Edit `catalog/mcp-configs/mcp-servers.json`. For each of the three internal MCP entries:
>
> 1. Rename the JSON key (e.g. `"devai-skill-server"` -> `"nexus-skill-server"`).
> 2. Update the `command` and `args` fields so the spawn invocation points at the new package (typically `python -m nexus_skill_server` or equivalent).
> 3. Update any `_comment` fields per the **Five-Question Audit Checklist** in `AGENTS.md` (the existing comments should already pass; just replace brand strings).
> 4. Update any cross-reference to `docs/policy/mcp-reverse-engineering-matrix.md` if that matrix references the old names by JSON key.
>
> Edit `docs/policy/mcp-reverse-engineering-matrix.md` (or whichever version's matrix is current): rename the rows for the three internal servers to use the new keys. Per `AGENTS.md` MCP Registry Policy, the matrix is the authoritative classification document and must stay in sync with the registry.
>
> Validate: `python -c "import json; json.load(open('catalog/mcp-configs/mcp-servers.json'))"`. Commit as `feat(v2.0.0): rename internal MCP server registry to nexus-*`.

---

#### 4.3 -- Rename brand-bearing files in `scripts/`

**Objective**: The `scripts/` directory has two files that carry the brand.

**Prompt**:
> Rename (with `git mv`):
>
> - `scripts/devai_mcp_benchmark.py` -> `scripts/nexus_mcp_benchmark.py`
> - `scripts/Install-DevAI-Permissions.ps1` -> `scripts/Install-Nexus-Hub-Permissions.ps1`
>
> Inside the renamed files, replace all variant occurrences per the variant table. Update any docstring, module-level constant, or CLI banner that references the old name.
>
> Update both installers (`scripts/installer.sh` and `scripts/installer.ps1`) where they reference these files - the installer copies scripts by **explicit name** per `AGENTS.md` rule, so each copy line for `devai_mcp_benchmark.py` and `Install-DevAI-Permissions.ps1` must be updated to the new filename. Look for the existing `generate_report.py` copy block to find the pattern.
>
> Inside `scripts/installer.sh` and `scripts/installer.ps1`, also confirm the installed destination directory uses `~/.nexus-hub/scripts/` (changed in Phase 3 sub-task 3.2).
>
> Validation:
>
> - `python scripts/nexus_mcp_benchmark.py --help` must run without errors.
> - `pwsh -NoProfile -File scripts/Install-Nexus-Hub-Permissions.ps1 -WhatIf` (if `-WhatIf` is supported) or a parse-only check.
>
> Commit as `refactor(v2.0.0): rename brand-bearing scripts to nexus-*`.

---

#### 4.4 -- Phase 4 stability gate

**Objective**: Confirm extensions, MCPs, and scripts all work under the new names.

**Prompt**:
> Run the full extension test sweep:
>
> 1. `cd extensions/nexus-skill-server && python -m pytest -q` -- expect 37 passed.
> 2. `cd extensions/nexus-code-search && python -m pytest -q` -- expect 36 passed, 1 skipped.
> 3. `cd extensions/nexus-web-fetch && python -m pytest -q` -- expect 23 passed.
> 4. `python -c "import json; json.load(open('catalog/mcp-configs/mcp-servers.json'))"`.
> 5. `python scripts/nexus_mcp_benchmark.py --help`.
> 6. `grep -rln "DevAI-Hub\|devai-hub\|devai_hub" extensions/ scripts/ catalog/mcp-configs/` -- must be empty.
>
> Fix any failure or residual rename before advancing.

---

### Phase 4 Exit Checklist

- [ ] All 3 extension directories renamed (with `git mv`)
- [ ] All 3 nested Python packages renamed
- [ ] `pyproject.toml` updated for each extension
- [ ] MCP registry and reverse-engineering matrix renamed
- [ ] `scripts/devai_mcp_benchmark.py` and `scripts/Install-DevAI-Permissions.ps1` renamed
- [ ] All extension test suites green
- [ ] Ready to advance to Phase 5

---

## Phase 5: Hooks, Commands, Skills, Rules, Templates Sweep

**Goal**: Bulk textual rename across the remaining catalog (`catalog/hooks/`, `catalog/commands/`, `catalog/skills/`, `catalog/rules/`, `catalog/style-guides/`, `catalog/checklists/`, `catalog/agents/`), update all 5 AI-instruction templates in lockstep, and rename the one skill directory and one cursor rule file that carry the brand on disk.
**Prerequisites**: Phase 4.
**Stability Gate**: `grep -rn "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" catalog/ templates/ .cursor/` returns NOTHING; `make validate` is green; `python -m pytest catalog/hooks/tests -q` matches the baseline 366 passed / 3 skipped.

### Sub-tasks

#### 5.1 -- Catalog bulk textual rename

**Objective**: Apply the variant table to every file under `catalog/` that contains a brand string.

**Prompt**:
> Apply each variant from `docs/archive/v2/v2.0/rename-inventory.md` to every file under `catalog/`:
>
> 1. `catalog/hooks/*.sh` and `*.py` (14+ hooks - update DevAI references in comments, banner strings, error messages, env-var lookups like `DEVAI_OLD_DOCS_GUARD` -> `NEXUS_OLD_DOCS_GUARD`)
> 2. `catalog/commands/*.md` (33 commands - prose mentions of the project name, example paths like `~/.devai-hub/`)
> 3. `catalog/skills/**/SKILL.md` (203 skills - the most volume; many skills reference "DevAI-Hub's MCP server", `~/.devai-hub/`, the MCP Registry Policy in `AGENTS.md`, etc.)
> 4. `catalog/rules/**/*.md` (4 language families * several files each)
> 5. `catalog/style-guides/*.md`
> 6. `catalog/checklists/*.md`
> 7. `catalog/agents/*.md` (10 agents)
> 8. `catalog/context/` and `catalog/memory/` template files
>
> Approach: run a scripted find/replace for each variant separately, then audit. The variants to apply (in this exact order so longer variants are replaced before shorter ones that would over-match):
>
> 1. `DevAI-Hub` -> `Nexus-Hub`
> 2. `DEVAI-HUB` -> `NEXUS-HUB`
> 3. `DEVAI_HUB` -> `NEXUS_HUB`
> 4. `DevAI Hub` -> `Nexus Hub`
> 5. `devai-hub` -> `nexus-hub`
> 6. `devai_hub` -> `nexus_hub`
> 7. **DO NOT** blind-replace standalone `devai` -- audit each remaining match manually. Likely false positives: words containing `devai` as a substring (none expected in practice), legacy doc references that should be quoted historically.
>
> Suggested implementation: write a Python script at `scripts/apply_rename.py` that walks `catalog/`, applies each variant in order, prints a per-file changed-line count, and writes a manifest to `docs/archive/v2/v2.0/rename-manifest.txt`. Make the script idempotent so it can be re-run safely.
>
> Validation after the sweep:
>
> 1. `grep -rln "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" catalog/` -- must be empty.
> 2. `python scripts/validate_skills.py --bundles-only` -- must be green (allowing WN-001 carry-over warnings).
> 3. `python -m pytest catalog/hooks/tests -q` -- must match baseline 366 passed, 3 skipped (the hooks were edited; if any hook test now fails because of a renamed env var, fix the test in the same sub-task).
>
> Commit as `refactor(v2.0.0): catalog textual rename to nexus-hub`.

---

#### 5.2 -- Update all 5 AI-instruction templates in lockstep

**Objective**: `templates/ai-instructions/base-*.md` (claude, codex, cursor, gemini, opencode) are the five per-platform instruction files. They MUST be updated in lockstep per `AGENTS.md` ("Platform templates ... edit all five in lockstep -- changes must be platform-agnostic").

**Prompt**:
> Apply the same variant replacements from sub-task 5.1 to each of:
>
> - `templates/ai-instructions/base-claude.md`
> - `templates/ai-instructions/base-codex.md`
> - `templates/ai-instructions/base-cursor.md`
> - `templates/ai-instructions/base-gemini.md`
> - `templates/ai-instructions/base-opencode.md`
>
> Diff every two templates after the edit (`diff base-claude.md base-codex.md`, etc.) and confirm the only differences are the platform-specific blocks that already existed before this rename - the rename itself must not introduce platform-specific divergence.
>
> Also update `templates/ai-instructions/generic-instructions.md` and anything under `templates/ai-instructions/coding-instructions/` and `templates/ai-instructions/coding-snippets/`. Skip `templates/ai-instructions/legacy/` -- legacy templates are intentionally historical.
>
> Commit as `feat(v2.0.0): update all 5 AI-instruction templates to nexus-hub in lockstep`.

---

#### 5.3 -- Rename brand-bearing skill directory

**Objective**: The `using-devai-hub` skill is the on-disk artifact whose name carries the brand. Rename the directory and update the SKILL.md frontmatter.

**Prompt**:
> Run `git mv catalog/skills/workflow/using-devai-hub catalog/skills/workflow/using-nexus-hub`.
>
> Edit `catalog/skills/workflow/using-nexus-hub/SKILL.md`:
>
> 1. YAML frontmatter `name: using-devai-hub` -> `name: using-nexus-hub`
> 2. `description`, `summary_l0`, `overview_l1` -- rename per the variant table; also update the description to ride the rebrand and make Nexus connection obvious. Example new `description`: "Orient an AI session to Nexus-Hub's skill catalog, commands, and hooks in under 2 minutes. Use whenever a session starts in a Nexus-Hub repo, when a user asks 'how do I find a skill?', or when onboarding a new agent platform (Claude Code, Codex, Gemini, Copilot, Cursor) to the catalog. SKIP: external skill marketplaces unrelated to this repo."
> 3. Body content: replace all brand variants.
>
> The skill ALSO needs to be re-registered per `AGENTS.md` -- in this case the registration update has already been handled in Phase 2 sub-task 2.2 (where `data/SKILL_INDEX.md` and `data/skills.json` were renamed), so verify those entries reference `using-nexus-hub` rather than `using-devai-hub` and that the `path` and `file` fields in `data/skills.json` point at the new directory.
>
> Validation: `python scripts/validate_skills.py --bundles-only` -- must remain green.
>
> Commit as `refactor(v2.0.0): rename using-devai-hub skill to using-nexus-hub`.

---

#### 5.4 -- Rename `.cursor/rules/devai-hub.mdc`

**Objective**: The cursor-specific rule file carries the brand in its filename.

**Prompt**:
> Run `git mv .cursor/rules/devai-hub.mdc .cursor/rules/nexus-hub.mdc`.
>
> Edit the renamed file and apply the variant replacements per sub-task 5.1.
>
> If the file's frontmatter or body references the file's own name (e.g. "rule devai-hub"), update accordingly.
>
> Commit as `refactor(v2.0.0): rename .cursor/rules/devai-hub.mdc to nexus-hub.mdc`.

---

#### 5.5 -- Phase 5 stability gate

**Objective**: Confirm the catalog sweep is complete and consistent.

**Prompt**:
> Run:
>
> 1. `grep -rln "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" catalog/ templates/ .cursor/` -- must return NOTHING.
> 2. `python scripts/validate_skills.py --bundles-only` -- green with only WN-001 carry-over warnings.
> 3. `python -m pytest catalog/hooks/tests -q` -- 366 passed, 3 skipped (baseline).
> 4. `make lint` (or `bash -n` over `catalog/hooks/*.sh`) -- no syntax errors.
>
> If any of the four fails, fix and re-run.

---

### Phase 5 Exit Checklist

- [ ] Catalog bulk rename complete across hooks, commands, skills, rules, style-guides, checklists, agents, context, memory
- [ ] All 5 `base-*.md` templates updated in lockstep
- [ ] `using-devai-hub` skill renamed to `using-nexus-hub` (dir + SKILL.md + data/ entries)
- [ ] `.cursor/rules/devai-hub.mdc` renamed
- [ ] Validators green and matching baseline
- [ ] Ready to advance to Phase 6

---

## Phase 6: README Modernization + Nexus Logo + Brand Linkage

**Goal**: Rewrite the top-level `README.md` around the Nexus-Hub brand. Hero with the Nexus logo. Clear "What is Nexus-Hub?" positioning. Explicit linkage to the sibling Nexus desktop app. Updated platform matrix. Modernized layout. The README becomes the headline artifact of the v2.0.0 release.
**Prerequisites**: Phase 5.
**Stability Gate**: The new README renders correctly on GitHub (hero image visible, links work), passes the project's Markdown style guide (`catalog/style-guides/markdown.md`), and contains no `DevAI-Hub` / `devai-hub` text outside an explicit "Renamed from DevAI-Hub at v2.0.0" callout.

### Sub-tasks

#### 6.1 -- Copy the Nexus logo into this repo's `assets/`

**Objective**: The Nexus README hero uses `nexus_primary.png` from the sibling repo's `assets/` directory. Copy that file (and a monochrome variant) into this repo so the README can reference it without cross-repo path dependencies.

**Prompt**:
> Create the directory `assets/` at the repo root if it does not exist.
>
> Copy two files from the sibling Nexus repo:
>
> - `C:\Users\bdour\Documents\Projects\Development\Nexus-AI\assets\nexus_primary.png` -> `assets/nexus_primary.png`
> - `C:\Users\bdour\Documents\Projects\Development\Nexus-AI\assets\nexus_monochrome.png` -> `assets/nexus_monochrome.png` (for use in dark-mode previews or alternative branding)
>
> Confirm both files are PNG (not corrupted) by checking magic bytes: `python -c "print(open('assets/nexus_primary.png','rb').read(8))"` should print `b'\\x89PNG\\r\\n\\x1a\\n'`.
>
> Update `.gitignore` if needed to allow `assets/*.png` (it should already be allowed - this is a verification step). Confirm `git add assets/*.png` does not error.
>
> Add a `LICENSE-ASSETS.md` (or append to `LICENSE`) noting that `nexus_primary.png` and `nexus_monochrome.png` are reused from the sibling `bendourthe/Nexus-AI` project with permission from the author (Benjamin Dourthe is the author of both projects, so this is internal).
>
> Commit as `feat(v2.0.0): add Nexus brand assets to assets/`.

---

#### 6.2 -- Rewrite the top-level README.md

**Objective**: Modernize the README around the new brand. Hero, positioning, Nexus connection, updated platform matrix, Quick Start, What's New for v2.0.0.

**Prompt**:
> Rewrite `README.md` from the ground up using the structure below. The current README is 287 lines and contains a `What's New in v1.3.0` section -- that section becomes historical and is moved to `docs/archive/v1/v1.3/RELEASE_NOTES.md` (verify it is already there; if not, copy it before deleting from README).
>
> New README structure (use the style and tone of the existing one as the template -- engineering-clear, no marketing fluff, no emoji except the existing minimal use of the rocket/book emojis if you choose to keep them):
>
> 1. **Hero block** (center-aligned `<p>` tag with the `nexus_primary.png` logo at width 200, like the Nexus README's hero).
>
> 2. **Title line**: `# Nexus-Hub` followed by a tagline `**The Skill Harness for Every AI Coding Assistant.**`
>
> 3. **One-paragraph pitch**: 2-3 sentences. Suggested opening: "Nexus-Hub is the upstream skill catalog for AI coding assistants - 203+ skills, 33 commands, 14 hooks, 10 agents, 4 rules families. It installs in one step on Windows, macOS, and Linux, and it works the same across Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, GitHub CLI, and the Nexus desktop app and VS Code extension."
>
> 4. **Renamed callout** (one short block): "Previously known as **DevAI-Hub** through v1.4.0. Renamed to **Nexus-Hub** at v2.0.0 to align with the sibling project [Nexus](https://github.com/bendourthe/Nexus-AI), a local-first desktop AI Studio that consumes Nexus-Hub as its skill harness. Existing DevAI-Hub installs are migrated in place by the v2.0.0 installer; see [the v2.0.0 migration notes](docs/archive/v2/v2.0/RELEASE_NOTES.md)."
>
> 5. **Nexus connection block** (titled `## How Nexus-Hub fits with Nexus`): two-three paragraphs explaining the relationship. Nexus-Hub is the catalog source-of-truth; Nexus consumes it as an upstream feed. Other AI assistants also consume the same catalog. Link to `https://github.com/bendourthe/Nexus-AI` and to the Nexus `AGENTS.md` quote: "the only external project we deliberately link to". This is the "make the connection obvious" requirement from the planning interview.
>
> 6. **What's New in v2.0.0** (titled `## What's New in v2.0.0`): three subsections -- (a) the rename itself, listing the breaking changes; (b) the modernized installer with the ASCII banner and migration path; (c) the Nexus brand integration. Reference `CHANGELOG.md` and `docs/archive/v2/v2.0/RELEASE_NOTES.md` at the end.
>
> 7. **Platform compatibility matrix** (titled `## Supported Agentic Platforms`): a Markdown table listing each platform, the install target it writes to, and the per-platform surface (skills + commands vs. instructions-only). Rows: Claude Code, OpenAI Codex, Gemini (Antigravity), GitHub Copilot, Cursor, GitHub CLI, Nexus desktop app, Nexus VS Code extension. The matrix must reflect the actual per-platform coverage caveats per `AGENTS.md` "Platform coverage caveats" section (Cursor/OpenCode/Copilot get behavioral guardrails only; Claude/Gemini/Codex get full per-file file-tree copy).
>
> 8. **Quick Start (The 30-Second Setup)**: keep the existing structure (clone, run installer, drag-and-drop, confirm, optional project). Update path references: target dir is now `~/.nexus-hub/`. Update count totals to whatever `data/skills.json` reports.
>
> 9. **What is Nexus-Hub?**: keep the "AI assistants are generic, this makes them specialist" framing from the existing README but rewrite for the new brand.
>
> 10. **Catalog overview**: link to `data/SKILL_INDEX.md` and the catalog landing pages.
>
> 11. **Contributing, license, links**: standard footer with links to `CONTRIBUTING.md` if present, `LICENSE`, `CHANGELOG.md`, `docs/DEVLOG.md`, the Nexus sibling repo, and the author's GitHub.
>
> Style requirements (per `catalog/style-guides/markdown.md`):
>
> - ASCII-only (no em-dashes, no curly quotes, no ellipsis characters - use hyphens, straight quotes, and `...`)
> - Blank line before and after every list, code block, table, and heading
> - One H1 per document
> - Each paragraph is a single continuous line in source (no hard wrap)
>
> After writing, validate:
>
> - `python scripts/validate_skills.py --bundles-only` still green
> - Open the file and visually confirm hero image path renders (`![Nexus](assets/nexus_primary.png)` or `<img src="assets/nexus_primary.png">`)
> - `grep -n "DevAI-Hub\|devai-hub" README.md` -- only matches should be in the "Renamed from" callout and the "What's New" breaking-changes list
>
> Commit as `feat(v2.0.0): rewrite README around Nexus-Hub brand with logo and Nexus linkage`.

---

#### 6.3 -- Sync any nested README files

**Objective**: The repo has nested READMEs (in `extensions/*/README.md`, possibly in `scripts/`, `docs/`, etc.). Apply the rename to each.

**Prompt**:
> Run `find . -name "README.md" -not -path "./node_modules/*" -not -path "./.git/*"` and apply the variant table to every README.
>
> For each extension README under `extensions/nexus-*/README.md`, also add a one-line cross-link at the top: "Part of [Nexus-Hub](../../README.md), the skill harness for AI coding assistants. See the parent README for installation and platform coverage."
>
> Commit as `docs(v2.0.0): sync nested READMEs to nexus-hub brand`.

---

#### 6.4 -- Phase 6 stability gate

**Objective**: Confirm the README modernization is internally consistent and renders cleanly.

**Prompt**:
> 1. `grep -rln "DevAI-Hub\|devai-hub" README.md $(find . -name "README.md" -not -path "./node_modules/*" -not -path "./.git/*" -not -path "./docs/archive/*" -not -path "./docs/v[0-1].*/*")` - matches are allowed only inside an explicit "renamed from" / migration callout block.
> 2. Hero image renders: confirm `assets/nexus_primary.png` exists and is referenced from `README.md`.
> 3. Markdown style: open `README.md` and walk the verification list at the end of `catalog/style-guides/markdown.md`.
> 4. Link audit: at minimum, the links to `https://github.com/bendourthe/Nexus-AI`, `CHANGELOG.md`, `docs/archive/v2/v2.0/RELEASE_NOTES.md`, `data/SKILL_INDEX.md`, and `LICENSE` must resolve to existing targets (the RELEASE_NOTES file is written in Phase 7 sub-task 7.5; until then a stub at that path is acceptable).

---

### Phase 6 Exit Checklist

- [ ] `assets/nexus_primary.png` and `nexus_monochrome.png` copied in
- [ ] `README.md` rewritten around Nexus-Hub brand with Nexus connection block
- [ ] Platform compatibility matrix accurate
- [ ] Nested READMEs updated
- [ ] All asset references render
- [ ] Markdown style guide compliance verified
- [ ] Ready to advance to Phase 7

---

## Phase 7: Docs / Config / DevLog / Gitignore Sync + CHANGELOG

**Goal**: Run the four `/update-*` skills the user explicitly named (`/update-documentation`, `/update-config`, `/update-devlog`, `/update-gitignore`) to fan the rename through the remaining doc, config, and gitignore surfaces. Write the v2.0.0 CHANGELOG block and RELEASE_NOTES.
**Prerequisites**: Phase 6.
**Stability Gate**: `grep -rn "DevAI-Hub\|devai-hub\|devai_hub\|DEVAI_HUB" 2>/dev/null | grep -v "^./node_modules\|^./.git/\|^./docs/archive/\|^./docs/v[01]\\.\|^./CHANGELOG.md:" | wc -l` returns 0; `CHANGELOG.md` has a complete `## [2.0.0]` block listing every breaking change; `docs/archive/v2/v2.0/RELEASE_NOTES.md` exists.

### Sub-tasks

#### 7.1 -- Run `/update-documentation`

**Objective**: The `/update-documentation` skill (per its description) discovers, audits, and updates all documentation files. Run it to catch any guides, manuals, or nested docs the previous phases missed.

**Prompt**:
> Invoke the `/update-documentation` skill. Goal: audit every file under `docs/`, `guides/`, and any other doc surface for stale `DevAI-Hub` references, broken cross-links resulting from the rename, and prose that needs to reflect the v2.0.0 brand.
>
> Specific surfaces the skill must check:
>
> - `docs/DEVLOG.md` (will be appended in 7.3, but flag any stale brand strings in the prose)
> - `docs/CATALOG-COVERAGE.md`
> - `docs/permissions-research.md`, `docs/permissions-setup.md`
> - `docs/security/`
> - `guides/` (any developer guides like `RTK_CONTEXT_COMPRESSION.md`)
> - Every `docs/v<x>/` directory that is NOT under `docs/archive/`. Historical `docs/v0.*` and `docs/v1.*` directories are FROZEN and must not be edited per the `old-version-docs-guard` hook -- the skill should respect that and only flag, not edit, those.
>
> For docs under archived versions (`docs/archive/`) and frozen older-version directories, do nothing -- those are historical snapshots and must reflect what was true at the time.
>
> Output: a manifest at `docs/archive/v2/v2.0/documentation-sync-manifest.md` listing every file the skill touched and every file it flagged for manual review.
>
> Commit as `docs(v2.0.0): /update-documentation sync of stale brand references`.

---

#### 7.2 -- Run `/update-config`

**Objective**: The `/update-config` skill configures `settings.json` and similar harness config. Run it to ensure any settings files reference the new brand and the new installed path.

**Prompt**:
> Invoke the `/update-config` skill. Goal:
>
> 1. Audit `catalog/hooks/settings.json` for any inline references to the old brand or the old installed path. The hooks themselves were renamed in Phase 5; the settings file may carry path examples or comments that need updating.
> 2. Audit any user-facing `settings.json` examples in skill bodies and command bodies (some commands embed `settings.json` snippets in their documentation).
> 3. If the `/update-config` skill supports auditing user-level Claude Code settings, note in the manifest that user `~/.claude/settings.json` files may carry references to the old `~/.devai-hub/` paths -- but DO NOT edit user-level files; only flag them.
>
> Output: changes captured in a `docs/archive/v2/v2.0/config-sync-manifest.md`.
>
> Commit as `chore(v2.0.0): /update-config sync of settings references`.

---

#### 7.3 -- Run `/update-devlog`

**Objective**: Append a v2.0.0 entry to `docs/DEVLOG.md` documenting the rename, the modernization scope, the breaking changes, and the migration story.

**Prompt**:
> Invoke `/update-devlog`. The skill analyzes recent changes and writes a DEVLOG entry.
>
> The entry must cover:
>
> 1. Context: why the rename happened (alignment with the Nexus sibling product, per the planning interview).
> 2. Scope: every artifact category that was renamed (extensions, MCPs, scripts, hooks, commands, skills, rules, templates, plugin metadata, installer, README, docs).
> 3. Breaking changes: installed root path, plugin name, MCP names, env-var prefix, GitHub URL.
> 4. Migration: one-shot installer migration on first run after upgrade.
> 5. The Nexus connection: explicit cross-link to the sibling project; one-paragraph framing of "why two repos".
> 6. Modernization beyond the rename: ASCII installer banner, README hero with logo, modernized platform compatibility matrix.
> 7. Carry-forward known-gaps cleanup (WN-001 / WN-002 status from Phase 8 sub-task 8.3).
>
> Date the entry `2026-05-19` (today's date per the planning context).
>
> Commit as `docs(v2.0.0): DEVLOG entry for the Nexus-Hub rename and modernization`.

---

#### 7.4 -- Run `/update-gitignore`

**Objective**: Audit `.gitignore` for any patterns that reference the old name, and add any new patterns that the rename surfaces (e.g. preventing accidental commits of `~/.devai-hub/` symlinks if a contributor still has one on their machine).

**Prompt**:
> Invoke `/update-gitignore`. The skill audits `.gitignore`, identifies wrongly-tracked files, missing patterns, and large-binary candidates.
>
> Specific items to address:
>
> 1. If `.gitignore` had any `devai-hub` patterns (e.g. ignoring a local install symlink), rename or remove them.
> 2. Add patterns for any v2.0.0-introduced artifacts (e.g. `docs/archive/v2/v2.0/baselines/*.txt` is intentional but heavy; keep or ignore at the maintainer's discretion).
> 3. Verify `assets/*.png` is not accidentally ignored.
> 4. Run the skill's full audit pass.
>
> Output: a `docs/archive/v2/v2.0/gitignore-audit.md` summary of the changes applied and any patterns flagged but not applied.
>
> Commit as `chore(v2.0.0): /update-gitignore audit for the rename`.

---

#### 7.5 -- Write CHANGELOG and RELEASE_NOTES for v2.0.0

**Objective**: A complete `## [2.0.0]` CHANGELOG block listing every breaking change and a corresponding RELEASE_NOTES file.

**Prompt**:
> Edit `CHANGELOG.md`. Insert a new `## [2.0.0] -- 2026-05-19` block at the top of the file (above the existing `## [1.4.0]` block), following the Keep a Changelog format already in use.
>
> Required subsections under `## [2.0.0]`:
>
> - `### Renamed` (the headline change): list the project name, installed root, plugin name, MCP server names, env-var prefix, GitHub URL, extension package names, brand-bearing skill directory, cursor rule file, scripts files.
> - `### Breaking changes`: explicit list of what users must do to upgrade. Each line should be one-sentence actionable: "Update any `DEVAI_*` environment variables in your shell rc to `NEXUS_*`", "Update any direct path references to `~/.devai-hub/` in your scripts to `~/.nexus-hub/`", "Re-pin the plugin if you reference it by name in any GitHub Action or marketplace integration", etc.
> - `### Added`: ASCII-art NEXUS-HUB installer banner; Nexus logo in README; explicit cross-linkage block to the sibling Nexus project; v2.0.0 RELEASE_NOTES.md.
> - `### Changed`: modernized README; modernized installer prompts and prose; updated platform compatibility matrix.
> - `### Migration`: one-paragraph description of the installer's one-shot legacy-install migration; mention that the migration is one-way and that users who want a backup should copy `~/.devai-hub/` to a safe place before running the v2.0.0 installer.
> - `### Carry-overs`: WN-001 (4 framework-specialist orphan-bundle warnings) and WN-002 (Windows `make`/`shellcheck` env workaround) -- their status as of v2.0.0 (open / closed / re-deferred), and a link to `docs/archive/v2/v2.0/known-gaps.md`.
>
> Create `docs/archive/v2/v2.0/RELEASE_NOTES.md` with:
>
> 1. Headline ("Nexus-Hub v2.0.0 -- The Rename")
> 2. Short summary paragraph
> 3. The Nexus connection block (cross-link to the sibling project)
> 4. The migration story (paragraph form, friendlier than the CHANGELOG)
> 5. Reference table of new file paths vs. old file paths
> 6. Links to the CHANGELOG block, the migration commit, and `docs/archive/v2/v2.0/plans/nexus-hub-rename.md`
>
> Commit as `docs(v2.0.0): CHANGELOG entry and RELEASE_NOTES for the rename`.

---

#### 7.6 -- Phase 7 stability gate

**Objective**: Confirm the documentation, config, devlog, gitignore, CHANGELOG, and RELEASE_NOTES are all in place and consistent.

**Prompt**:
> Run:
>
> 1. `grep -rn "DevAI-Hub\|devai-hub\|devai_hub\|DEVAI_HUB" 2>/dev/null | grep -v "^./node_modules\|^./.git/\|^./docs/archive/\|^./docs/v[01]\\.\|^./CHANGELOG.md:" | grep -v "Renamed from DevAI-Hub\|previously known as DevAI-Hub\|formerly DevAI-Hub" | wc -l` -- this should return 0. Any non-zero result lists residual misses that must be addressed before advancing.
> 2. `CHANGELOG.md` contains `## [2.0.0]` and `docs/archive/v2/v2.0/RELEASE_NOTES.md` exists.
> 3. `docs/archive/v2/v2.0/documentation-sync-manifest.md`, `config-sync-manifest.md`, `gitignore-audit.md` exist.
> 4. `docs/DEVLOG.md` has a 2026-05-19 entry covering the rename.

---

### Phase 7 Exit Checklist

- [ ] `/update-documentation` run and manifest committed
- [ ] `/update-config` run and manifest committed
- [ ] `/update-devlog` run and DEVLOG entry committed
- [ ] `/update-gitignore` run and audit committed
- [ ] `CHANGELOG.md` v2.0.0 block written
- [ ] `docs/archive/v2/v2.0/RELEASE_NOTES.md` written
- [ ] Residual-rename grep returns 0
- [ ] Ready to advance to Phase 8

---

## Phase 8: Validation, Carry-Forward Known-Gaps, Version Bump

**Goal**: Run all validators one final time, address (or explicitly re-defer) the two carry-forward known-gaps from v1.3.0, bump every single-source-of-truth version literal from 1.4.0 to 2.0.0, write `docs/archive/v2/v2.0/known-gaps.md`, and cut the `v2.0.0` git tag.
**Prerequisites**: Phase 7.
**Stability Gate**: All validators green; cross-platform installer dry-run successful on at least one platform; `git tag v2.0.0` cut; session history generated.

### Sub-tasks

#### 8.1 -- Full validation sweep

**Objective**: Confirm the post-rename repository is functionally indistinguishable from the pre-rename baseline (except for the rename itself).

**Prompt**:
> Run the full validation matrix and capture each output to `docs/archive/v2/v2.0/baselines/<file>-post.txt` (mirroring the pre-rename baselines from Phase 1 sub-task 1.1):
>
> 1. `python scripts/validate_skills.py --bundles-only` -- expected: green with the same 4 WN-001 orphan warnings as baseline (or fewer, if WN-001 is closed in sub-task 8.3).
> 2. `python -m pytest catalog/hooks/tests -q` -- expected: 366 passed, 3 skipped (plus 1 new test added in Phase 3 sub-task 3.3 for the migration smoke check).
> 3. Each extension's test suite: `cd extensions/nexus-skill-server && python -m pytest -q` and the other two extensions. Expected counts unchanged from baseline.
> 4. JSON parse-check on every metadata file: `python -c "import json; [json.load(open(f)) for f in ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', 'data/skills.json', 'data/marketplace.json', 'data/bundles.json', 'catalog/mcp-configs/mcp-servers.json']]"`.
> 5. `make lint` (or `bash -n` over every `.sh` file in `catalog/hooks/` and `scripts/` and `install.sh`).
> 6. Final residual-rename grep: `grep -rln "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" 2>/dev/null | grep -v "^./node_modules\|^./.git/\|^./docs/archive/\|^./docs/v[01]\\.\|^./CHANGELOG.md\|^./docs/archive/v2/v2.0/RELEASE_NOTES.md\|^./README.md"` -- must return nothing (the README and CHANGELOG carry intentional "renamed from" prose; archived and frozen historical docs are excluded).
>
> Diff each post baseline against its pre baseline. Document any differences in `docs/archive/v2/v2.0/validation-diff.md`. If any test newly fails compared to baseline, fix it before advancing.

---

#### 8.2 -- Cross-platform installer dry-run

**Objective**: Confirm both installers run end-to-end on a fresh HOME with the new name, banner, and migration.

**Prompt**:
> On the available platform (Windows per the planning context):
>
> 1. PowerShell: set `$env:HOME = "$env:TEMP\nexus-test-$(Get-Random)"; pwsh scripts/installer.ps1`. Confirm: banner prints; no legacy migration prompt (because the fresh HOME has no `.devai-hub/`); `~/.nexus-hub/` populated with skills, commands, hooks, agents, rules, scripts.
> 2. Bash (via Git Bash or WSL): `HOME=$(mktemp -d) bash scripts/installer.sh`. Same expected behavior.
> 3. Now test the migration path. Manually create a fake `~/.devai-hub/` (`mkdir $env:TEMP\nexus-test-mig\.devai-hub; New-Item -ItemType File $env:TEMP\nexus-test-mig\.devai-hub\sentinel.txt`), set `$env:HOME = "$env:TEMP\nexus-test-mig"`, run the installer, answer Y to the migration prompt, confirm `~/.nexus-hub/` exists and contains `sentinel.txt`, and `~/.devai-hub/` is gone.
>
> Capture each smoke-run terminal output to `docs/archive/v2/v2.0/installer-smoke-post.txt`. If macOS or Linux is unavailable on the local machine, document the limitation in the file -- a follow-up CI smoke matrix is part of the open WN-002 carry-over, not a blocker for v2.0.0.

---

#### 8.3 -- Address or re-defer carry-forward known-gaps `[from v1.3.0 known-gaps: WN-001, WN-002]`

**Objective**: Close out or explicitly re-defer the two open items from `docs/archive/v1/v1.3/known-gaps.md`.

**Prompt**:
> The v1.3.0 known-gaps file (`docs/archive/v1/v1.3/known-gaps.md`) carries two open items into v2.0.0:
>
> **WN-001 -- Pre-existing 4 framework-specialist orphan-bundle warnings**.
> Reason: `fastapi-expert/references/dependency-injection-patterns.md`, `nextjs-expert/references/data-fetching-patterns.md`, `react-expert/references/performance-patterns.md`, `react-expert/references/testing-recipes.md` are not referenced from their parent SKILL.md. Per `AGENTS.md` reference-rule audit, every file under per-skill `references/` MUST be referenced. The suggested-next-step is one of: (a) wire each into the parent SKILL.md as a "see references/<file>.md for ..." link; (b) inline if short; (c) leave as carry-over with explicit annotation.
>
> Action for v2.0.0: option (a) for all four. Open each parent SKILL.md (`catalog/skills/framework-specialists/fastapi-expert/SKILL.md`, `nextjs-expert/SKILL.md`, `react-expert/SKILL.md`) and add a "## References" section near the bottom (above "## Related Skills") with one bullet per orphan file: "- `references/<file>.md` -- <one-line topic summary derived from the file's H1 and first paragraph>". After the edit, re-run `python scripts/validate_skills.py --bundles-only` and confirm the 4 orphan warnings are gone.
>
> **WN-002 -- Windows `make` and `shellcheck` unavailable; cp1252 default codec breaks inline `python -c json.load`**.
> Reason: the Makefile's `validate` target uses inline `python -c "import json; d = json.load(open('data/skills.json'))"` which fails on Windows because the Python store distribution defaults to cp1252 for `open()`. The fix is a one-line change to pass `encoding='utf-8'`.
>
> Action for v2.0.0: patch the `Makefile` `validate` target so every inline `python -c` invocation that opens a file passes `encoding='utf-8'`. Document Windows-developer prerequisites at `docs/dev-environment-windows.md` (or append to `docs/permissions-setup.md`) covering `scoop install make`, `scoop install shellcheck`, and `PYTHONUTF8=1`. After the edit, `make validate` should succeed on Windows.
>
> Both items resolved. Write `docs/archive/v2/v2.0/known-gaps.md` with `Status: in-progress` (per the lifecycle: `/wrap-up-session` sweeps to in-progress, `/update-version` finalizes). Move WN-001 and WN-002 to a `## Resolved` table with `Resolved in: v2.0.0 Phase 8 sub-task 8.3` and a one-sentence note pointing at the fix commit. The Open Items section starts empty for v2.0.0.
>
> Commit as `fix(v2.0.0): close v1.3.0 carry-over known-gaps WN-001 and WN-002`.

---

#### 8.4 -- Version bump to 2.0.0

**Objective**: Bump every single-source-of-truth version literal from `1.4.0` (or `v1.4.0`) to `2.0.0` (or `v2.0.0`).

**Prompt**:
> Bump the version literal in every authoritative location. Locations (verify each):
>
> 1. `.claude-plugin/plugin.json` -- `"version": "1.4.0"` -> `"version": "2.0.0"`
> 2. `.claude-plugin/marketplace.json` -- same key
> 3. `scripts/installer.sh` -- `NEXUS_HUB_VERSION="1.4.0"` -> `NEXUS_HUB_VERSION="2.0.0"`
> 4. `scripts/installer.ps1` -- equivalent version variable
> 5. Any nested `package.json`, `pyproject.toml`, or `Cargo.toml` that ships a version literal AND that participates in distribution (extensions' `pyproject.toml` files - bump each)
> 6. `CHANGELOG.md` -- the v2.0.0 block was written in Phase 7 sub-task 7.5; confirm the date and version match
>
> Use `grep -rn '"version":\|VERSION="1\\.4\\.0"\|version *= *"1\\.4\\.0"'` to find every spot before editing.
>
> Commit as `chore(v2.0.0): version bump 1.4.0 -> 2.0.0`.

---

#### 8.5 -- Generate session history and cut the v2.0.0 tag

**Objective**: Capture a comprehensive session-history document of the rename effort, then cut the release tag.

**Prompt**:
> 1. Invoke `/generate-session-history` to produce a session-history file under `docs/archive/v2/v2.0/development/history/2026-05-19_nexus-hub-rename.md`. The skill should reconstruct the chronological steps from git history (every commit made during this plan's execution carries the `v2.0.0` scope tag and is filterable), document troubleshooting points (any reverts, any orphan-bundle false positives, any installer smoke failures), and list next steps (cross-repo follow-up on the Nexus side to update its README's link to `bendourthe/Nexus-Hub`, and any other downstream coordination).
>
> 2. Finalize `docs/archive/v2/v2.0/known-gaps.md`: set `Status: finalized`, lock in the `## Open Items` section (should be empty for v2.0.0 unless new items surfaced during validation), and confirm `## Resolved` lists WN-001 and WN-002.
>
> 3. Cut the git tag: `git tag -a v2.0.0 -m "Nexus-Hub v2.0.0 -- rename from DevAI-Hub, modernized installer, Nexus brand integration"`. Do NOT `git push --tags` automatically -- per `CLAUDE.md` global rules, destructive or remote-mutating git operations require user confirmation. Document the pending push as a final user action.

---

#### 8.6 -- Phase 8 stability gate

**Objective**: Confirm the v2.0.0 release is ready to push.

**Prompt**:
> Final acceptance check:
>
> 1. All baselines under `docs/archive/v2/v2.0/baselines/` are green and diff'd against pre-rename baselines (no regressions).
> 2. Installer dry-runs in `docs/archive/v2/v2.0/installer-smoke-post.txt` show banner + migration working end-to-end.
> 3. `docs/archive/v2/v2.0/known-gaps.md` finalized; WN-001 and WN-002 closed.
> 4. Every authoritative version literal reads `2.0.0`.
> 5. `git tag --list "v2.0.0"` returns `v2.0.0`.
> 6. `git status` clean.
> 7. README hero renders, Nexus connection block links resolve, CHANGELOG v2.0.0 block is complete.
>
> Final residual-rename grep over the working tree (excluding `node_modules`, `.git`, `docs/archive`, and historical `docs/v0.*` / `docs/v1.*` directories) returns zero unintended matches.

---

### Phase 8 Exit Checklist

- [ ] All validators green; post-baselines captured under `docs/archive/v2/v2.0/baselines/`
- [ ] Cross-platform installer smoke captured
- [ ] WN-001 (orphan-bundle) closed by linking the 4 reference files into their parent SKILL.md
- [ ] WN-002 (Windows `make`/`shellcheck`) closed by Makefile UTF-8 patch + dev-environment-windows.md
- [ ] Version literals bumped to 2.0.0 in plugin.json, marketplace.json, both installers, every extension pyproject.toml
- [ ] `docs/archive/v2/v2.0/known-gaps.md` finalized
- [ ] Session history generated at `docs/archive/v2/v2.0/development/history/`
- [ ] `git tag v2.0.0` cut (push deferred to user)
- [ ] Working tree clean

---

## Items NOT in scope (deferred or out-of-scope)

- **Pushing the v2.0.0 tag to the remote** -- destructive/remote-mutating op; deferred to explicit user action after final review.
- **Renaming the GitHub repo from `DevAI-Hub` to `Nexus-Hub`** -- requires the user to perform this on GitHub.com; the in-repo URLs are already updated to point at the new name and GitHub's automatic redirect handles the transition window.
- **Updating the sibling Nexus repo's README** to point at `bendourthe/Nexus-Hub` (currently links to `bendourthe/DevAI-Hub`) -- handled in a follow-up commit on the `Nexus-AI` repo, out of scope here.
- **Per-CI matrix smoke (Windows + macOS + Linux installer dry-runs in CI)** -- noted in the cross-platform installer dry-run sub-task; if not currently in CI, tracked as a v2.0.x or v2.1.0 hygiene item rather than blocking v2.0.0.
- **A separate `compatibility-shim` branch that ships `~/.devai-hub/` as a symlink to `~/.nexus-hub/`** -- explicitly rejected in Phase 1 sub-task 1.3 (backward-compat decision). Rationale recorded there.
