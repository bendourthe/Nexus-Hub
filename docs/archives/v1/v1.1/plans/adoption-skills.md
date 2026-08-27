# Plan -- Adoption of anthropics/skills patterns

**Project**: DevAI-Hub
**Version**: v1.1.5
**Slug**: adoption-skills
**Plan Type**: Feature / Enhancement
**Created**: 2026-05-07
**Goal**: Adopt all 17 items (A1-A17) identified in `docs/archive/v1/v1.1/comparison-skills.md` Section 11, in reverse-engineer-first order per the MCP Registry Policy, with full cross-platform installer parity across all 5 supported IDEs (Claude Code, Cursor, Codex, Gemini, OpenCode) on Windows / macOS / Linux.

## Overview

This plan operationalizes the comparison report at [docs/archives/v1/v1.1/comparison-skills.md](../comparison-skills.md) against `github.com/anthropics/skills`. All 17 P0+P1+P2+P3 adoption candidates are in scope; the 4 dropped items (N1-N4) are recorded in the *Items explicitly NOT adopted* appendix below for traceability.

Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of [docs/archives/v1/v1.1/comparison-skills.md](../comparison-skills.md) for the ordering rationale. Phase 1 ships zero-code `skill-native` doc edits that close capability gaps without touching the catalog file tree. Phases 2-7 then build internal `re-full` and `re-partial` content -- one phase per coherent group of new artifacts -- with the layout-convention change (A13) front-loaded so every later phase can use per-skill `scripts/`, `references/`, and `assets/` subdirectories.

A hard cross-cutting constraint applies to every phase: every artifact added, modified, or removed must reach all 5 supported AI-IDE platforms (Claude Code, Cursor, Codex, Gemini, OpenCode) on Windows, macOS, and Linux through dual edits to `scripts/installer.sh` AND `scripts/installer.ps1`. Each phase's Stability Gate explicitly verifies an installer dry-run on at least one OS.

This plan ingests **0 items** carried forward from prior known-gaps files (no `docs/v*/known-gaps.md` exists in the project).

## Phases at a Glance

| Phase | Title | Outcome | RE Bucket |
|-------|-------|---------|-----------|
| 1 | Skill-native doc edits (A14, A17, A15, A11, A12) | Author-side skill-creation guidance updated; SKILL.md size norm reconciled; aesthetic-distinctiveness and static-poster lenses added to existing skills | skill-native |
| 2 | P0 cleanup + doc-coauthoring skill (A4, A9) | `claude-api` skill restored OR de-listed (decided in 2.1); new `doc-coauthoring` workflow skill | re-full |
| 3 | Per-skill `scripts/`/`references/`/`assets/` layout convention (A13) | Both installers recursively copy per-skill bundled subdirs; `make validate` detects orphaned bundles; `AGENTS.md` updated | re-full (foundational) |
| 4 | Net-new content skills, batch 1 (A1, A3, A8, A10) | `generative-art`, `theme-tokens`, `internal-comms`, `web-artifacts-builder` skills shipped, all consuming the Phase 3 layout convention | re-full |
| 5 | Skill-eval-loop + description optimizer (A6, A7) | `skill-eval-loop` workflow skill + repo-level Python scripts (viewer, aggregator, optimizer); CLI-agnostic adapter for claude/gemini/codex/opencode following the v1.1.3 four-hook precedent | re-full |
| 6 | Brand-styling + MCP-builder (A2, A5) | `brand-styling` skill (token-driven, no vendor assets) + `mcp-builder` skill (FastMCP + TS SDK runbook) | re-partial / re-full |
| 7 | `.skill` packager (optional, A16) | `scripts/package_skill.py` + dual-installer registration; emits portable `.skill` archives for Claude.ai / Anthropic API distribution | re-partial |

---

## Phase 1: Skill-native doc edits

**Goal**: Apply five doc-only changes that institutionalize patterns observed in `anthropics/skills` without adding any new file to the catalog.
**Prerequisites**: None.
**Stability Gate**: `make validate && make lint` clean; the `data/SKILL_INDEX.md` table is unchanged (no new rows; this phase only edits existing skill bodies and `AGENTS.md`); `installer.sh` and `installer.ps1` un-modified (no new copy steps needed since this phase touches only existing tracked files).

### Sub-tasks

#### 1.1 -- A14: Pushy description guidance in skill-creation skills

**Objective**: Update the two DevAI-Hub skills that teach skill / command creation so they explicitly advocate "pushy" descriptions that combat undertriggering.

**Prompt**:
> Read `catalog/skills/workflow/create-skill-or-command/SKILL.md` and `catalog/skills/workflow/create-custom-command/SKILL.md`. In each, add a new section titled `## Description Style: Combat Undertriggering` (placed right after the existing description-related guidance). The section must explain: (a) Claude has a tendency to under-trigger skills when the description is too narrow; (b) descriptions should explicitly list trigger phrases AND skip phrases (`SKIP: ...` or `Do NOT use for: ...`); (c) include a before/after example that mirrors the pattern from the comparison report's Section 4 (e.g., transform a narrow `"How to build a dashboard."` into the pushy form `"How to build a dashboard. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"`). Re-state the rule in 1-2 sentences inside the Common Rationalizations table for each skill (rationalization: "the description is short and clean, so it'll trigger fine"; reality: "Claude undertriggers; explicit phrases beat poetic brevity"). Run `make validate && make lint`. Do NOT touch any other skill or registry file. Commit with subject line `v1.2.0-wip: A14 pushy-description guidance`.

---

#### 1.2 -- A17: Three-tier loading model formalization in AGENTS.md

**Objective**: Make explicit in `AGENTS.md` that DevAI-Hub skills follow a three-tier progressive-disclosure model (matching `agentskills.io`'s spec): tier 1 metadata always loaded, tier 2 SKILL.md body loaded on trigger, tier 3 bundled resources loaded on demand -- and that bundled `scripts/*` can be EXECUTED without their text being loaded into context.

**Prompt**:
> Open `AGENTS.md` and locate the section "Adding a New Skill -> Skill Writing Guide" (or the equivalent if section names have drifted). Add a new subsection `### Three-Tier Loading Model` that says:
>
> 1. **Tier 1 (always loaded)**: `name`, `description`, `summary_l0`, `overview_l1`. Total ~150-300 tokens. Determines whether the skill triggers.
> 2. **Tier 2 (on trigger)**: the SKILL.md body. Target <=500 lines, soft cap 800 lines (see also A15 in this plan).
> 3. **Tier 3 (on demand)**: bundled resources under `scripts/`, `references/`, `assets/` (the convention introduced in Phase 3 / A13). Reference files load into context when the agent reads them; scripts EXECUTE without their source being loaded -- this is critical for skills that bundle large generators (e.g., a 2000-line PDF builder script).
>
> Cross-link from the existing `### Skill Anatomy` block. Run `make validate && make lint`. Commit with `v1.2.0-wip: A17 three-tier loading model in AGENTS.md`.

---

#### 1.3 -- A15: SKILL.md size norm reconciliation

**Objective**: Update the existing 800-line cap to a 500-line target with 800 as soft cap.

**Prompt**:
> Find the rule in `AGENTS.md` that says "Keep SKILL.md under 800 lines." (or equivalent). Replace with: "Target <= 500 lines for SKILL.md body. Soft cap 800 lines. Beyond 500 lines, add a `references/` subdirectory with a table of contents and link to it from SKILL.md rather than expanding the body. Beyond 800 lines, the skill MUST be split or refactored before merge." Do NOT retroactively shrink any existing skill -- this norm is forward-looking. Add a one-line note in the same paragraph: "Existing skills that exceed 500 lines are grandfathered; new and substantially-rewritten skills must hit the 500-line target." Run `make validate && make lint`. Commit with `v1.2.0-wip: A15 500-line SKILL.md target`.

---

#### 1.4 -- A11: Aesthetic-distinctiveness lens in frontend-ui-engineering

**Objective**: Augment the existing `frontend-ui-engineering` skill with the aesthetic-distinctiveness section adapted from `anthropics/skills/frontend-design/SKILL.md`.

**Prompt**:
> Open `catalog/skills/developer-experience/frontend-ui-engineering/SKILL.md`. Add a new `## Aesthetic Distinctiveness` section after the existing accessibility / responsiveness / state guidance. Content rules: (a) explain that AI-generated frontends often default to a generic "AI slop" aesthetic (centered hero + 3-column feature grid + gradient buttons + Inter typeface) and that production-grade UI must avoid this; (b) provide 4-6 concrete countermeasures (custom typography pairings, asymmetric layouts, intentional density, distinctive accent colors, motion that means something, copy that has a voice); (c) cite 2-3 reference patterns the agent can apply (e.g., editorial-style multi-column layouts; brutalist over-borders; restrained motion); (d) add a Common Rationalizations row: "the agent's default looks fine" / "the default IS the AI-slop default; pick a distinctive direction up-front." Do NOT copy upstream content verbatim -- generic descriptive framing only, per the AGENTS.md reverse-engineering attribution rule. Run `make validate && make lint`. Commit with `v1.2.0-wip: A11 aesthetic-distinctiveness lens`.

---

#### 1.5 -- A12: Static-poster / .pdf workflow in creative-generation

**Objective**: Augment the `creative-generation` skill with a static-art / .pdf-output workflow drawn from `anthropics/skills/canvas-design/SKILL.md`.

**Prompt**:
> Open `catalog/skills/developer-experience/creative-generation/SKILL.md`. Add a `## Static Poster / Print Workflow` section after the existing image-prompt / deck guidance. The section explains a two-step approach: (1) "Design philosophy" -- a short Markdown manifesto that fixes color palette, typography, composition principles, and 1-2 reference movements; (2) "Visual expression" -- the actual .png / .pdf output rendered via the existing `pptx-generation`, `pdf-document-generation`, or a one-off Python+Pillow / matplotlib script. Add a Common Rationalizations row: "we don't need a philosophy step for one poster" / "without it, the agent defaults to AI-slop visuals; the manifesto is 50 lines and saves a 10x rework." Do NOT introduce any p5.js or HTML-canvas content -- that lives in A1 (generative-art) under Phase 4. Run `make validate && make lint`. Commit with `v1.2.0-wip: A12 static-poster workflow in creative-generation`.

---

#### 1.6 -- Testing and Stabilization

**Objective**: Verify Phase 1 doc edits are clean and ship a single combined patch-release-style commit and CHANGELOG entry.

**Prompt**:
> Run `make validate && make lint && make test` and fix any failures. Append a `## [Unreleased]` -> `### Changed` entry to `CHANGELOG.md` summarizing all five A14/A17/A15/A11/A12 edits in sectioned-bullet form per the v1.1.5 commit-message rule. Do NOT bump the version number yet (this phase ships under `[Unreleased]`). Run `/generate-session-history` to document Phase 1.

---

### Phase 1 Exit Checklist

- [ ] All 5 sub-tasks completed (1.1-1.5)
- [ ] `make validate && make lint && make test` clean
- [ ] CHANGELOG `[Unreleased]` entry appended
- [ ] No new files created; all edits are to existing tracked files
- [ ] Session history generated for Phase 1
- [ ] Ready to advance to Phase 2

---

## Phase 2: P0 cleanup + doc-coauthoring skill (A4, A9)

**Goal**: Resolve the missing `claude-api` skill (restore from upstream OR de-list) and ship the `doc-coauthoring` 3-stage workflow skill.
**Prerequisites**: Phase 1 complete.
**Stability Gate**: Either `catalog/skills/ai-development/claude-api/SKILL.md` exists and is registered, OR the `claude-api` row is removed from all three `data/` registry files; `data/SKILL_INDEX.md` filesystem state matches the index 1:1; new `doc-coauthoring` skill renders in `data/SKILL_INDEX.md`; installer dry-run on at least one OS includes the new skill in the recursive copy.

### Sub-tasks

#### 2.1 -- A4: Decide and execute claude-api restore-or-delist

**Objective**: Resolve the index drift identified in Section 5a A4 of the comparison report.

**Prompt**:
> Step 1 -- ask the user (one consolidated question, four options): "The `claude-api` skill row exists in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`, but the file `catalog/skills/ai-development/claude-api/SKILL.md` does not exist. Which do you want? (A) Restore from the upstream `anthropics/skills/claude-api/SKILL.md` content, generic-framed and de-vendored. (B) Restore from your own previous DevAI-Hub history if a prior version had it. (C) De-list the row from all three registry files. (D) Other / I'll provide content." Step 2 -- execute the chosen option:
>
> - **If A**: re-clone `github.com/anthropics/skills` (shallow), copy `skills/claude-api/SKILL.md` into `catalog/skills/ai-development/claude-api/SKILL.md`, then rewrite the body to match DevAI-Hub conventions (add `summary_l0`, `overview_l1`, `When to Use This Skill`, `Common Rationalizations`, `Verification`, `Related Skills`). Strip Anthropic-specific framing (per the AGENTS.md reverse-engineering attribution rule). Do NOT copy the language-specific `csharp/`, `curl/`, `go/`, `java/`, `php/`, `python/`, `ruby/`, `typescript/`, `shared/` subdirs verbatim -- if those are wanted, defer to a future phase; for now ship just the SKILL.md.
> - **If B**: `git log --all --diff-filter=D -- 'catalog/skills/ai-development/claude-api/**'` to locate the deletion commit; `git show <commit>:catalog/skills/ai-development/claude-api/SKILL.md > catalog/skills/ai-development/claude-api/SKILL.md`.
> - **If C**: remove the `claude-api` row from `data/SKILL_INDEX.md`; remove the entry from the `"skills"` array in `data/skills.json`; decrement `skill_count` in the relevant category in `data/marketplace.json` and decrement `total_skills` in `statistics`. Run `make validate`.
> - **If D**: wait for user-supplied content, then proceed as A but using the user's content.
>
> Step 3 -- run `make validate && make lint`. Commit with `v1.2.0-wip: A4 claude-api {restore|delist}` (pick one).

---

#### 2.2 -- A9: doc-coauthoring 3-stage workflow skill

**Objective**: Ship a new skill that wraps the three-stage co-authoring workflow (Context Gathering -> Refinement & Structure -> Reader Testing).

**Prompt**:
> Create `catalog/skills/workflow/doc-coauthoring/SKILL.md`. Frontmatter: `name: doc-coauthoring`; `description: Guide users through a structured workflow for co-authoring documentation (specs, proposals, decision docs, technical writeups). Use whenever the user wants to co-write a doc, draft a proposal, or refine documentation iteratively. SKIP: simple READMEs that don't need a workflow, single-paragraph commit messages.`; `summary_l0: "Guide users through a 3-stage workflow for co-authoring documentation."`; `overview_l1: ...` (write a <=150-word body summary). Body sections (in order): Title heading; intro paragraph; `## When to Use This Skill` (trigger phrases + "When NOT to use"); `## Instructions` with three numbered stages (Stage 1 Context Gathering: ask about audience, purpose, prior art, constraints; Stage 2 Refinement and Structure: outline, draft, iterate on shape; Stage 3 Reader Testing: simulate the doc with a fresh reader, identify gaps); `## Common Rationalizations` table (4-5 entries: "I just need the doc fast"/"slow is smooth, smooth is fast on docs reused 100x"; "the user knows what they want"/"the user knows the OUTCOME, not the SHAPE; the workflow surfaces the shape"; etc.); `## Verification` (binary checklist); `## Related Skills` (cross-links to `business-product/technical-writer`, `developer-experience/writing-editing`, `documentation/technical-documentation`).
>
> Then register the skill: append a row to `data/SKILL_INDEX.md` table; append an entry to the `"skills"` array in `data/skills.json` (full schema -- name, title, description, long_description, summary_l0, overview_l1, version, author, category=workflow, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security with default 100/100/95); increment `skill_count` for `workflow` in `data/marketplace.json` and `total_skills` in `statistics`. Do NOT copy upstream content verbatim. Run `make validate && make lint`. Commit with `v1.2.0-wip: A9 doc-coauthoring skill`.

---

#### 2.3 -- Cross-platform installer verification for Phase 2

**Objective**: Confirm the new `doc-coauthoring` skill (and any restored `claude-api` skill) reaches all 5 IDEs on at least one OS.

**Prompt**:
> Step 1 -- run a dry-run install of the current branch into a throwaway directory: `bash scripts/installer.sh --dry-run --target /tmp/devai-hub-phase2-test` (or the PowerShell equivalent on Windows). Step 2 -- verify the installer reports `doc-coauthoring/SKILL.md` would be copied under each platform's destination (Claude Code, Gemini / Antigravity, Codex per the AGENTS.md "Installer-Aware Changes" matrix). Step 3 -- spot-check that Cursor / OpenCode / Copilot each receive the skill via the `{{SKILL_INDEX}}` block in their `templates/ai-instructions/base-{cursor,opencode,copilot}.md` rendering. Step 4 -- if any platform is missed, fix the installer and re-run. Step 5 -- if A4 was option A or B (restore), repeat the verification for `claude-api`. Document the dry-run output in a brief comment in this phase's session-history. Commit any installer fixes as `v1.2.0-wip: A4/A9 installer parity verification`.

---

#### 2.4 -- Testing and Stabilization

**Objective**: Generate and run all tests for Phase 2.

**Prompt**:
> Run `make validate && make lint && make test`. Fix any failures. Append CHANGELOG `[Unreleased]` -> `### Added` entry for `doc-coauthoring`; under `### {Fixed|Removed}` for the A4 outcome. Run `/generate-session-history` for Phase 2.

---

### Phase 2 Exit Checklist

- [ ] A4 resolved (skill restored OR row de-listed)
- [ ] `doc-coauthoring/SKILL.md` shipped and registered in all three `data/` files
- [ ] Installer dry-run confirms cross-platform reach
- [ ] `make validate && make lint && make test` clean
- [ ] CHANGELOG `[Unreleased]` updated
- [ ] Session history generated
- [ ] Ready to advance to Phase 3

---

## Phase 3: Per-skill `scripts/` / `references/` / `assets/` layout convention (A13)

**Goal**: Formalize the convention that any skill folder MAY contain `scripts/`, `references/`, `assets/` subdirectories, and update both installers + `make validate` to handle them. This phase is foundational for Phases 4-7.
**Prerequisites**: Phases 1-2.
**Stability Gate**: Both installers recursively copy per-skill bundled subdirectories; `make validate` extension detects orphan subdirs (a `scripts/` not referenced by its parent SKILL.md, a per-skill script not registered in any installer); `AGENTS.md` documents the new convention; an empty proof-of-concept per-skill `scripts/` (committed to a sentinel skill, e.g., `doc-coauthoring/scripts/.gitkeep`) actually lands at `~/.devai-hub/skills/<name>/scripts/` after a dry-run install on Windows AND macOS / Linux.

### Sub-tasks

#### 3.1 -- A13.1: Document the convention in AGENTS.md

**Objective**: Add the per-skill bundled-subdir convention to `AGENTS.md` so future skill authors follow it.

**Prompt**:
> Open `AGENTS.md` and add a new subsection under "Adding a New Skill" titled `### Per-skill Bundled Resources`. Content: a skill folder MAY (not MUST) contain three subdirectories: `scripts/` (executable code, for tier-3 deterministic operations), `references/` (Markdown docs the agent reads when needed; e.g., `references/fastmcp.md`), `assets/` (templates / icons / fonts used by scripts or referenced from SKILL.md). Document file naming: `scripts/<name>.{py,js,sh}`; `references/<topic>.md`; `assets/<descriptive-name>.<ext>`. Cross-link to A17 (three-tier loading model) and A15 (500-line target). Document the installer behavior change (3.2 + 3.3): the installer recursively copies these subdirs alongside SKILL.md when distributing the skill. Document the validation behavior change (3.4): `make validate` flags any per-skill `scripts/` that contains a file unreferenced from SKILL.md and any orphan subdirectory. Run `make validate && make lint`. Commit with `v1.2.0-wip: A13.1 document per-skill bundled-resources convention`.

---

#### 3.2 -- A13.2: installer.sh recursive copy of per-skill subdirs

**Objective**: Update `scripts/installer.sh` so the existing recursive `cp -r catalog/skills/` step preserves per-skill `scripts/`, `references/`, `assets/` subdirectories under each platform's destination.

**Prompt**:
> Open `scripts/installer.sh`. Locate the existing recursive copy of `catalog/skills/` to each platform target (Claude Code, Gemini / Antigravity, Codex per the AGENTS.md "Installer-Aware Changes" matrix). Verify that the existing `cp -r` (or rsync equivalent) already preserves subdirs. If it uses a flat copy or filters by file extension, replace with `cp -r` / `rsync -a` so per-skill subdirs are included. Add a comment block above the loop: `# Per-skill bundled resources (scripts/, references/, assets/) are copied recursively. See AGENTS.md "Per-skill Bundled Resources".`. Do not change the destination paths -- skill bundles still land at `<target>/skills/<category>/<name>/{SKILL.md,scripts/,references/,assets/}`. Run `bash -n scripts/installer.sh` to syntax-check, then `make lint` for ShellCheck. Commit with `v1.2.0-wip: A13.2 installer.sh per-skill recursive copy`.

---

#### 3.3 -- A13.3: installer.ps1 recursive copy of per-skill subdirs (lockstep with 3.2)

**Objective**: Mirror 3.2 in `scripts/installer.ps1`.

**Prompt**:
> Open `scripts/installer.ps1`. Locate the existing recursive copy logic (`Copy-Item -Recurse` or `Safe-Copy` block) for `catalog/skills/`. Verify it preserves per-skill subdirs. If not, switch to `Copy-Item -Path "$src/*" -Destination "$dst" -Recurse -Force` (or equivalent). Add a comment block matching 3.2's wording. Verify the script runs syntax-clean: `powershell -NoProfile -Command "& {$PSDefaultParameterValues['*:Encoding']='utf8'; . './scripts/installer.ps1' --dry-run --target $env:TEMP/devai-hub-test }"` -- if `--dry-run` does not exist, add it as a no-op flag that prints what would be copied without touching the filesystem (see also the dry-run requirement in Phase 2's Stability Gate). Commit with `v1.2.0-wip: A13.3 installer.ps1 per-skill recursive copy (lockstep with A13.2)`.

---

#### 3.4 -- A13.4: make validate orphan-bundle detection

**Objective**: Extend `make validate` (or whichever script `make validate` runs) to detect per-skill `scripts/` files that are not referenced from their parent SKILL.md, and per-skill subdirs that contain only `.gitkeep` (false-positive orphans).

**Prompt**:
> Locate the JSON-validator script that `make validate` runs (likely under `scripts/` or referenced from `Makefile`). Add a new validator pass that walks `catalog/skills/<cat>/<name>/` and for each entry: (a) lists files under `scripts/`, `references/`, `assets/`; (b) greps the parent SKILL.md for filename references; (c) emits a warning (not error) for each unreferenced file with the suggestion "either reference this from SKILL.md or remove it." Treat an empty `.gitkeep`-only subdir as OK. Add a Makefile target if needed: `validate-bundles: ; python scripts/validate_skill_bundles.py`. Wire it into the existing `make validate` target so it runs as part of the standard pre-commit / CI flow. Add a pytest test under `catalog/hooks/tests/test_skill_bundles.py` that builds a fixture with one referenced and one orphan file and asserts the orphan is reported. Run `make validate && make test`. Commit with `v1.2.0-wip: A13.4 make validate orphan-bundle detection`.

---

#### 3.5 -- A13.5: Smoke-test with a sentinel per-skill bundle

**Objective**: Prove the layout convention works end-to-end by adding an empty per-skill `scripts/` to the `doc-coauthoring` skill from Phase 2.

**Prompt**:
> Create `catalog/skills/workflow/doc-coauthoring/scripts/.gitkeep`. Reference the directory from the skill's body in a one-line note: `Future bundled scripts for this skill go under \`scripts/\`. None present at v1.2.0.` Run `make validate && make lint && make test`. Run a dry-run install on the current OS and verify `~/.devai-hub/skills/.../doc-coauthoring/scripts/` is created. Repeat the dry-run verification on a second OS if available (use a fresh VM, GitHub Actions matrix, or note the gap in session-history). Commit with `v1.2.0-wip: A13.5 sentinel per-skill bundle smoke test`.

---

#### 3.6 -- Testing and Stabilization

**Objective**: Verify Phase 3 holistically and append CHANGELOG.

**Prompt**:
> Run `make validate && make lint && make test`. Append CHANGELOG `[Unreleased]` -> `### Added` entry for the per-skill bundled-resources convention; `### Changed` entry for installer recursive-copy; `### Added` entry for orphan-bundle detection. Run `/generate-session-history` for Phase 3.

---

### Phase 3 Exit Checklist

- [ ] AGENTS.md documents the convention
- [ ] Both installers recursively copy per-skill subdirs (lockstep)
- [ ] `make validate` flags orphan bundles
- [ ] Sentinel bundle (`doc-coauthoring/scripts/.gitkeep`) survives a dry-run install on at least one OS
- [ ] Pytest covers the new validator
- [ ] CHANGELOG updated
- [ ] Session history generated
- [ ] Ready to advance to Phase 4

---

## Phase 4: Net-new content skills, batch 1 (A1, A3, A8, A10)

**Goal**: Ship four new skills that consume the Phase 3 layout convention: `generative-art`, `theme-tokens`, `internal-comms`, `web-artifacts-builder`.
**Prerequisites**: Phase 3 (per-skill subdir convention).
**Stability Gate**: All four new skills exist with full DevAI-Hub frontmatter (`name`, `description`, `summary_l0`, `overview_l1`); each is registered in `data/SKILL_INDEX.md` + `data/skills.json` + `data/marketplace.json`; bundled `templates/`, `themes/`, `examples/`, `scripts/` subdirs (where used) survive a dry-run install; `make validate && make lint && make test` clean.

### Sub-tasks

#### 4.1 -- A1: generative-art skill (specialized-domains)

**Objective**: Ship a skill that teaches the agent to produce p5.js generative art outputs (.md philosophy + .html viewer + .js generator), with seeded randomness and interactive parameters.

**Prompt**:
> Create `catalog/skills/specialized-domains/generative-art/SKILL.md` with full DevAI-Hub frontmatter. The body explains the two-step process: (1) Algorithmic Philosophy Creation (a Markdown manifesto -- aesthetic movement, principles, references); (2) Generator + Viewer (a `<name>.js` p5.js sketch with seeded randomness + an `<name>.html` viewer with parameter sliders). Include 2-3 concrete examples of philosophies (flow fields, particle systems, L-systems) WITHOUT copying upstream prose. Bundle starter templates under `catalog/skills/specialized-domains/generative-art/templates/{flow-field.html,particle-system.html,l-system.html}` -- keep each template <= 200 lines and self-contained (no external deps beyond a CDN p5.js). Add a `## Common Rationalizations` row: "the agent will figure out a sketch directly" / "without a philosophy step, generative output collapses to perlin-noise clichés." Add `## Verification`: the .html viewer opens in a browser; sliders re-render in real time; the .js exports a deterministic image given a fixed seed. Register in all three `data/` files (category=specialized-domains). Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A1 generative-art skill`.

---

#### 4.2 -- A3: theme-tokens skill (specialized-domains)

**Objective**: Ship a skill providing 10 generic curated themes (palette + font pairing tokens) consumable by `pptx-generation` / `docx-generation` / `pdf-document-generation`.

**Prompt**:
> Create `catalog/skills/specialized-domains/theme-tokens/SKILL.md` with full DevAI-Hub frontmatter. The body explains the theme schema (a JSON or YAML object with keys: `name`, `palette.{primary,secondary,accent,background,foreground,muted}`, `fonts.{heading,body,mono}`, `spacing.{base,scale}`, `radius`, `shadow`). Include the 10 generic themes -- DO NOT copy Anthropic's `theme-factory/themes/`; create 10 net-new themes from generic precedents (e.g., "Editorial Serif", "Brutalist Sans", "Pastel Soft", "Terminal Mono", "Corporate Slate", "Sunset Warm", "Forest Cool", "Mid-century Modern", "Neon Cyber", "Newsprint Mono"). Bundle each as `themes/<slug>.json` (or `.yaml`) under `catalog/skills/specialized-domains/theme-tokens/themes/`. Document how `pptx-generation` / `docx-generation` / `pdf-document-generation` should LOAD a theme (read the JSON, then map the tokens to whatever the underlying generator expects). Cross-link from those three existing skills' Related Skills sections. Register in all three `data/` files. Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A3 theme-tokens skill`.

---

#### 4.3 -- A8: internal-comms skill (business-product)

**Objective**: Ship a skill providing structured templates for internal communications (3P updates, status reports, leadership updates, FAQs, incident reports, project updates).

**Prompt**:
> Create `catalog/skills/business-product/internal-comms/SKILL.md` with full DevAI-Hub frontmatter. The body provides 6 named templates: (1) 3P Update (Progress / Plans / Problems); (2) Weekly Status Report; (3) Leadership Update (executive briefing format); (4) Company FAQ entry; (5) Incident Report (timeline + root cause + remediation); (6) Project Update (one-pager). For each, give: when to use, structure (with explicit section headers), example length, common pitfalls (3-5 bullets each). Bundle full-text examples under `catalog/skills/business-product/internal-comms/examples/{3p,status,leadership,faq,incident,project}.md`. Examples must be GENERIC -- use placeholder team / project / company names (e.g., "Project Aurora", "Team Phoenix"); explicitly NOT modeled on any specific real company. Add a `## Common Rationalizations` row: "I'll just write it freeform" / "freeform updates lose readers; templates are scaffolding that lets you focus on content." Cross-link from `developer-experience/writing-editing` and `business-product/technical-writer`. Register in all three `data/` files. Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A8 internal-comms skill`.

---

#### 4.4 -- A10: web-artifacts-builder skill (developer-experience)

**Objective**: Ship a skill that scaffolds multi-component HTML artifacts (Vite + React + Tailwind + shadcn/ui) for any deployment target -- not just Claude.ai.

**Prompt**:
> Create `catalog/skills/developer-experience/web-artifacts-builder/SKILL.md` with full DevAI-Hub frontmatter. Drop all "claude.ai artifact" framing -- describe it as "multi-component HTML artifact builder for in-browser deployable apps." The body documents when to use (any artifact with state management, routing, or shadcn/ui components -- NOT for simple single-file HTML/JSX). Bundle a scaffolder script at `catalog/skills/developer-experience/web-artifacts-builder/scripts/init-artifact.sh` (and a PowerShell sibling `init-artifact.ps1` for Windows parity) that: (a) checks for Node + npm; (b) runs `npm create vite@latest <name> -- --template react-ts`; (c) installs Tailwind (`@tailwindcss/vite` or `@tailwindcss/postcss` per current Tailwind v4 conventions); (d) installs `shadcn` and runs `npx shadcn init`; (e) prints next-step instructions. Register both scripts in BOTH installers per the AGENTS.md installer-aware changes rule (this is a per-skill bundled script under the new A13 convention -- the installer's recursive copy from 3.2/3.3 handles it; verify the dry-run lands `init-artifact.{sh,ps1}` at the right path). Document fallback behavior if `npm` is missing (clear error message, link to Node install instructions). Add Common Rationalizations: "we can do this without a scaffolder" / "scaffolding is 30 seconds and erases version-mismatch bugs that would have eaten an hour." Register in all three `data/` files. Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A10 web-artifacts-builder skill`.

---

#### 4.5 -- Cross-platform installer verification for Phase 4

**Objective**: Confirm all four new skills + their bundled subdirs reach all 5 IDEs on Windows AND macOS / Linux.

**Prompt**:
> Run dry-run installs on at least two OSes (use a Linux VM / Docker + a Windows VM, or document the gap if only one OS is available). For each, verify: (a) all four SKILL.md files land under each platform's destination (Claude Code, Gemini / Antigravity, Codex per the matrix); (b) per-skill `templates/` (generative-art), `themes/` (theme-tokens), `examples/` (internal-comms), `scripts/` (web-artifacts-builder) all land alongside SKILL.md; (c) `init-artifact.sh` is marked executable on macOS / Linux (`chmod +x`); (d) `init-artifact.ps1` runs without execution-policy issues on Windows; (e) Cursor / OpenCode / Copilot's `{{SKILL_INDEX}}` block renders the four new skills in their `templates/ai-instructions/base-*.md` outputs. Fix any installer gaps and commit as `v1.2.0-wip: A1/A3/A8/A10 installer parity verification`.

---

#### 4.6 -- Testing and Stabilization

**Objective**: Verify Phase 4 and append CHANGELOG.

**Prompt**:
> Run `make validate && make lint && make test`. Append CHANGELOG `[Unreleased]` -> `### Added` entries for each of the four new skills (one bullet per skill, sectioned-bullet form per the v1.1.5 commit-message rule). Run `/generate-session-history` for Phase 4.

---

### Phase 4 Exit Checklist

- [ ] All 4 SKILL.md files exist with full frontmatter
- [ ] All 4 are registered in all three `data/` files
- [ ] Bundled subdirs land correctly on Windows + macOS / Linux dry-run
- [ ] `init-artifact.sh` and `init-artifact.ps1` parity verified
- [ ] `make validate && make lint && make test` clean
- [ ] CHANGELOG updated
- [ ] Session history generated
- [ ] Ready to advance to Phase 5

---

## Phase 5: skill-eval-loop + description optimizer (A6, A7)

**Goal**: Ship the eval-iteration workflow + browser viewer + description optimizer as a single integrated skill, with CLI-agnostic adapter following the v1.1.3 four-hook precedent (claude / gemini / codex / opencode).
**Prerequisites**: Phases 1-4 (especially A13 layout convention and A17 three-tier loading model).
**Stability Gate**: New skill `catalog/skills/workflow/skill-eval-loop/SKILL.md` exists; repo-level scripts `scripts/skill_eval_viewer.py`, `scripts/aggregate_benchmark.py`, `scripts/optimize_skill_description.py` exist and are registered in BOTH installers per the AGENTS.md installer-aware-changes rule (every standalone repo script MUST be registered by name); a parametrized pytest test class `TestEvalLoopCLIAdapter` (modeled on `TestPlatformIndependence` from `test_diff_review_hooks.py`) asserts the four CLI adapter modules do not cross-reference each other; the eval-viewer can be launched with `--static <path>` for headless environments; `make validate && make lint && make test` clean.

### Sub-tasks

#### 5.1 -- A6.1: skill-eval-loop SKILL.md and workspace layout

**Objective**: Ship the workflow skill that drives the iteration loop.

**Prompt**:
> Create `catalog/skills/workflow/skill-eval-loop/SKILL.md` with full DevAI-Hub frontmatter. The body describes the loop: (1) capture user intent and write a draft skill (or use an existing one); (2) write 2-3 realistic test prompts to `evals/evals.json`; (3) for each test prompt, spawn TWO parallel runs in the same turn -- one with the skill, one baseline (same prompt, no skill); (4) save outputs to `<skill-name>-workspace/iteration-N/eval-<id>/{with_skill,without_skill}/outputs/`; (5) capture timing via `total_tokens` + `duration_ms`; (6) grade via assertions in `eval_metadata.json`; (7) aggregate to `benchmark.json` via `scripts/aggregate_benchmark.py`; (8) launch viewer; (9) read user feedback from `feedback.json`; (10) improve and re-run as `iteration-N+1`. Document the workspace layout, JSON schemas (link to a per-skill `references/schemas.md`), and the pushy-description / "explain the why" / "look for repeated work" improvement heuristics from the comparison report. Bundle `references/schemas.md`, `references/improvement-heuristics.md`, and per-skill `agents/` (subagent prompt files: `grader.md`, `comparator.md`, `analyzer.md`) under the skill folder per the A13 convention. Cross-link from `developer-experience/ai-output-evaluation`, `workflow/create-skill-or-command`, `workflow/create-custom-command`. Register in all three `data/` files. Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A6.1 skill-eval-loop SKILL.md and workspace layout`.

---

#### 5.2 -- A6.2: CLI-agnostic adapter design (claude / gemini / codex / opencode)

**Objective**: Decide and document the adapter pattern for routing eval runs through whichever AI CLI the user has installed, with strict no-cross-reference parity per v1.1.3.

**Prompt**:
> Read `catalog/hooks/{claude,gemini,codex,opencode}-diff-review.sh` to understand the v1.1.3 four-hook pattern (each hook is fully self-contained, no shared library, no cross-CLI fallbacks). Decide adapter design for the eval loop: option A -- four parallel scripts (`scripts/eval_loop_{claude,gemini,codex,opencode}.py`) each ~150 lines, no cross-imports; option B -- one `scripts/eval_loop.py` with a `--cli` flag and a hard `assert cli in {"claude","gemini","codex","opencode"}; if cli == ...: subprocess.run(["claude", "-p", ...])` dispatch (same no-cross-reference invariant enforced via a pytest test that greps each `if cli == "X":` branch and verifies it imports / shells out to ONLY that CLI). Pick option B (single file, parametrized) -- it minimizes code duplication while preserving the parity invariant. Document this decision in `references/cli-adapter.md` under the new skill. Add a pytest test `TestEvalLoopCLIAdapter` in `catalog/hooks/tests/test_eval_loop.py` (or similar) that, for each `if cli == "X":` branch, asserts: (a) only `subprocess.run` / `subprocess.Popen` is called with the matching CLI binary as argv[0]; (b) no other CLI binary appears in the same branch. The test inspects the source file directly (like `test_diff_review_hooks.py::TestPlatformIndependence`). Run `make test`. Commit with `v1.2.0-wip: A6.2 CLI-agnostic adapter design + parity test`.

---

#### 5.3 -- A6.3: scripts/skill_eval_viewer.py + aggregate_benchmark.py

**Objective**: Implement the browser-based eval viewer and the benchmark aggregator. These are the two scripts users invoke directly during the loop.

**Prompt**:
> Create `scripts/skill_eval_viewer.py` -- a self-contained Python script (Python 3.10+) that: (a) takes an `iteration-N/` directory, an optional `--benchmark <path>` JSON, and an optional `--previous-workspace <path>` for diff view; (b) renders an HTML report with two tabs ("Outputs" and "Benchmark"); (c) starts a local HTTP server (default `http.server`) and opens the user's browser via `webbrowser.open()`, OR writes a standalone HTML file when `--static <output_path>` is given (for headless environments); (d) collects feedback into `feedback.json` when the user clicks "Submit All Reviews" (server mode: POST endpoint; static mode: download via JS Blob). Use only Python stdlib + a single optional dep (`jinja2` if present, else inline template strings). Lazy-import per the `scripts/generate_report.py` precedent: clear "pip install jinja2" hint on ImportError if unavailable.
>
> Create `scripts/aggregate_benchmark.py` -- takes an `iteration-N/` directory and emits `benchmark.json` + `benchmark.md` with per-eval pass_rate / time / tokens (mean +- stddev) and the with_skill-vs-baseline delta. Document the JSON schema at the top of the file in a docstring; reference it from the skill's `references/schemas.md`.
>
> Register BOTH scripts in `scripts/installer.sh` AND `scripts/installer.ps1` per AGENTS.md "Installer-Aware Changes" rule -- model after the existing `generate_report.py` block. Both must land at `~/.devai-hub/scripts/{skill_eval_viewer.py,aggregate_benchmark.py}`. Run `python -m py_compile scripts/skill_eval_viewer.py scripts/aggregate_benchmark.py`. Run `make validate && make lint`. Commit with `v1.2.0-wip: A6.3 eval viewer + benchmark aggregator scripts (cross-platform installer-registered)`.

---

#### 5.4 -- A7: scripts/optimize_skill_description.py

**Objective**: Implement the description optimizer with 60/40 train-test split, 5-iteration loop, held-out test scoring, and `best_description` selection.

**Prompt**:
> Create `scripts/optimize_skill_description.py` -- a standalone Python 3.10+ script that: (a) takes an eval set JSON (the trigger-eval format with `query` + `should_trigger` fields), a target skill path, a `--cli {claude,gemini,codex,opencode}` flag, and a `--max-iterations` flag; (b) splits the eval set 60% train / 40% held-out; (c) for the current description, evaluates each train query 3 times via the chosen CLI to get a stable trigger rate; (d) calls the CLI to PROPOSE 3 candidate description rewrites based on what failed; (e) evaluates each candidate on train AND held-out test; (f) iterates up to `--max-iterations`; (g) emits a JSON result with `best_description` selected by HELD-OUT TEST score (avoids overfitting). Reuse the CLI dispatch from 5.2's adapter pattern (no cross-CLI fallback; parity-test enforced). Provide a `--dry-run` mode that does not call the CLI -- prints what would be evaluated. Lazy-import `requests` or any HTTP lib if needed.
>
> Register the script in BOTH installers per AGENTS.md. Add a pytest test that runs `--dry-run` with a fixture eval set and asserts the train/test split and the schema of the output. Document in `catalog/skills/workflow/skill-eval-loop/references/description-optimizer.md`. Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A7 description optimizer (CLI-agnostic, installer-registered)`.

---

#### 5.5 -- A6.4: Sub-agent prompt files under skill-eval-loop/agents/

**Objective**: Bundle the three sub-agent prompt files (grader, comparator, analyzer) under the new skill per the A13 convention.

**Prompt**:
> Create `catalog/skills/workflow/skill-eval-loop/agents/grader.md` (instructions for evaluating assertions against a run's outputs and writing `grading.json` with the exact field names `text`, `passed`, `evidence`); `catalog/skills/workflow/skill-eval-loop/agents/comparator.md` (instructions for blind A/B comparison: judge two outputs without knowing which is which, then return a structured verdict); `catalog/skills/workflow/skill-eval-loop/agents/analyzer.md` (instructions for analyzing a benchmark.json: surface non-discriminating assertions, high-variance evals, time/token tradeoffs). All three files explicitly tell the sub-agent NOT to read other files unless instructed -- they are tier-3 resources. Cross-reference them from SKILL.md "Reference files" section. Run `make validate`. Commit with `v1.2.0-wip: A6.4 sub-agent prompts under skill-eval-loop/agents/`.

---

#### 5.6 -- Cross-platform installer verification for Phase 5

**Objective**: Verify the eval skill + 3 scripts + 3 sub-agent prompts reach all 5 IDEs on Windows AND macOS / Linux.

**Prompt**:
> Run dry-run installs on Windows + macOS/Linux. Verify: (a) `~/.devai-hub/scripts/{skill_eval_viewer,aggregate_benchmark,optimize_skill_description}.py` exist; (b) `~/.devai-hub/skills/.../skill-eval-loop/{SKILL.md,references/,agents/}` exist; (c) `python -c "import http.server"` works on the target OS (it should -- stdlib); (d) `python <viewer> --static /tmp/test.html <fixture-iteration>` produces an HTML file. Fix any installer gaps. Commit with `v1.2.0-wip: A6/A7 installer parity verification`.

---

#### 5.7 -- Testing and Stabilization

**Objective**: Verify Phase 5 and append CHANGELOG.

**Prompt**:
> Run `make validate && make lint && make test`. Append CHANGELOG `[Unreleased]` -> `### Added` entries (sectioned-bullet form): skill-eval-loop / scripts / sub-agent prompts. Note explicitly under `### Why CLI-agnostic`: cite the v1.1.3 four-hook precedent. Run `/generate-session-history` for Phase 5.

---

### Phase 5 Exit Checklist

- [ ] `skill-eval-loop` SKILL.md + references/ + agents/ shipped
- [ ] `scripts/skill_eval_viewer.py`, `aggregate_benchmark.py`, `optimize_skill_description.py` created and installer-registered (BOTH installers)
- [ ] CLI-adapter parity test passes
- [ ] Dry-run install verifies cross-platform reach for the skill AND the three scripts
- [ ] Headless / `--static` mode of the viewer works
- [ ] `make validate && make lint && make test` clean
- [ ] CHANGELOG updated
- [ ] Session history generated
- [ ] Ready to advance to Phase 6

---

## Phase 6: brand-styling + mcp-builder (A2, A5)

**Goal**: Ship two more skills consuming the A13 convention: a generic `brand-styling` skill (token pattern only -- no vendor assets per N1) and an `mcp-builder` skill with FastMCP + TS SDK runbook content.
**Prerequisites**: Phases 3 (A13 layout) and 4 (A3 theme-tokens, since brand-styling depends on theme tokens).
**Stability Gate**: Both skills exist with full frontmatter; both registered in `data/`; both ship without ANY vendor-specific tokens, palettes, fonts, logos, or brand identifiers; `make validate && make lint && make test` clean; cross-platform installer dry-run passes.

### Sub-tasks

#### 6.1 -- A2: brand-styling skill (specialized-domains)

**Objective**: Ship a skill that applies user-supplied brand tokens to artifacts (slides, docs, HTML, PDFs).

**Prompt**:
> Create `catalog/skills/specialized-domains/brand-styling/SKILL.md`. EXPLICITLY ship with EMPTY palette / fonts / logo placeholders -- the user MUST supply their own brand. Do NOT include any vendor-specific colors, fonts, or logos (this is the N1 dropped-outright item). The body describes: (a) the brand-token schema (extends or imports the A3 theme-tokens schema); (b) where to put the user's brand under `~/.devai-hub/brand/<brand-name>/{tokens.json, fonts/, logo.{svg,png}}`; (c) how to wire the brand into `pptx-generation` / `docx-generation` / `pdf-document-generation` / `web-artifacts-builder` (the four downstream consumers). Bundle a placeholder template at `catalog/skills/specialized-domains/brand-styling/templates/tokens.template.json` with the schema but empty values. Add a STRONG `## Common Rationalizations` row: "the user wants 'professional' colors -- I'll just pick navy and gray" / "no -- ASK the user for their brand tokens; if they don't have any, OFFER to set up an empty `~/.devai-hub/brand/default/tokens.json` for them to fill." Cross-link from the four downstream skills' Related Skills sections. Register in all three `data/` files. Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A2 brand-styling skill (token-pattern only, no vendor assets)`.

---

#### 6.2 -- A5: mcp-builder skill (ai-development)

**Objective**: Ship a skill that walks the agent through building an MCP server in FastMCP (Python) or MCP SDK (Node / TS), with bundled scaffolding scripts.

**Prompt**:
> Create `catalog/skills/ai-development/mcp-builder/SKILL.md` with full DevAI-Hub frontmatter. The body covers: (a) when to build an MCP (vs. a skill, vs. a hook -- cross-link AGENTS.md MCP Registry Policy); (b) FastMCP setup (Python): `pip install "mcp[cli]"`; minimal example (3-4 tools); structured output; auth; testing with `mcp dev`; (c) MCP SDK setup (Node / TS): `npm install @modelcontextprotocol/sdk`; minimal example; structured output; testing; (d) how to register the MCP in `~/.claude/settings.json` and the equivalent for Cursor / Codex / Gemini / OpenCode (link to `templates/ai-instructions/base-*.md`). Bundle reference docs: `references/fastmcp.md`, `references/ts-sdk.md`. Bundle scaffolding scripts: `scripts/init-mcp-fastmcp.sh` (and `.ps1` Windows sibling), `scripts/init-mcp-ts.sh` (and `.ps1` sibling) -- each scaffolds a minimal "hello world" MCP server with one tool. The scripts MUST work without internet on top of pre-existing `pip` / `npm` -- they only generate file scaffolds, not download anything beyond the package manager's normal behavior. Cross-link from `developer-experience/tool-design`. Cite the AGENTS.md MCP Registry Policy in the body so users see the governance posture before building. Register in all three `data/` files. Register the four bundled scripts in BOTH installers per AGENTS.md. Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A5 mcp-builder skill (FastMCP + TS SDK runbook)`.

---

#### 6.3 -- Cross-platform installer verification for Phase 6

**Objective**: Verify both new skills + their bundled scripts reach all 5 IDEs on Windows AND macOS / Linux.

**Prompt**:
> Run dry-run installs on Windows + macOS / Linux. Verify: (a) both SKILL.md files exist at the expected destinations; (b) per-skill bundled `templates/` (brand-styling), `references/` + `scripts/` (mcp-builder) all land alongside SKILL.md; (c) `init-mcp-fastmcp.sh` is executable on macOS / Linux; (d) `init-mcp-fastmcp.ps1` runs on Windows; (e) `init-mcp-ts.sh` / `.ps1` similarly. Fix any installer gaps. Commit with `v1.2.0-wip: A2/A5 installer parity verification`.

---

#### 6.4 -- Testing and Stabilization

**Objective**: Verify Phase 6 and append CHANGELOG.

**Prompt**:
> Run `make validate && make lint && make test`. Append CHANGELOG `[Unreleased]` -> `### Added` entries for both skills (sectioned-bullet form). Run `/generate-session-history` for Phase 6.

---

### Phase 6 Exit Checklist

- [ ] `brand-styling` and `mcp-builder` SKILL.md files shipped
- [ ] Both registered in all three `data/` files
- [ ] Bundled scripts (init-mcp-*) registered in both installers (not just recursively copied)
- [ ] No vendor-specific tokens / palettes / fonts / logos / identifiers anywhere in the bundle (verified via `git grep -i 'anthropic\|claude.brand'`)
- [ ] Cross-platform installer dry-run passes
- [ ] `make validate && make lint && make test` clean
- [ ] CHANGELOG updated
- [ ] Session history generated
- [ ] Ready to advance to Phase 7

---

## Phase 7: .skill packager (optional, A16)

**Goal**: Add a portable `.skill` archive packager so users can distribute DevAI-Hub-shaped skills to Claude.ai or the Anthropic API skill-upload endpoint -- a delivery channel DevAI-Hub does not currently reach.
**Prerequisites**: Phase 5 (skill-eval-loop -- the packager is the last step in the eval loop's "ship the skill" workflow).
**Stability Gate**: `scripts/package_skill.py` exists, registered in BOTH installers; produces a `.skill` archive (zip) containing SKILL.md + bundled subdirs; archive is parseable by an upstream consumer (best-effort verification: round-trip extraction + frontmatter parse); `make validate && make lint && make test` clean.

**NOTE**: This phase is OPTIONAL. Only execute it if the user confirms Claude.ai / Anthropic API distribution is a goal. Otherwise skip and close out the plan after Phase 6.

### Sub-tasks

#### 7.1 -- A16: Packager script + installer registration

**Objective**: Implement `scripts/package_skill.py`.

**Prompt**:
> Create `scripts/package_skill.py` -- takes a path to a `catalog/skills/<cat>/<name>/` directory, creates a zip archive at `<name>.skill` containing SKILL.md + `scripts/` + `references/` + `assets/` (and any other bundled subdirs from the A13 convention). Validate the SKILL.md frontmatter (required: `name`, `description`; optional: `summary_l0`, `overview_l1`, `license`) before packaging -- abort with a clear error if invalid. Print the output path on success. Register the script in BOTH installers per AGENTS.md. Add a pytest test that packages a fixture skill and asserts the resulting `.skill` is a valid zip with SKILL.md at the root. Run `make validate && make lint && make test`. Commit with `v1.2.0-wip: A16 .skill packager script`.

---

#### 7.2 -- Cross-platform installer verification

**Objective**: Verify the packager script reaches all 5 IDEs on Windows + macOS / Linux.

**Prompt**:
> Dry-run install on both OSes. Verify `~/.devai-hub/scripts/package_skill.py` exists. Run a fixture pack on each OS to confirm the zip is produced. Commit with `v1.2.0-wip: A16 installer parity verification`.

---

#### 7.3 -- Testing and Stabilization

**Objective**: Verify Phase 7 and append CHANGELOG.

**Prompt**:
> Run `make validate && make lint && make test`. Append CHANGELOG `[Unreleased]` -> `### Added` entry. Run `/generate-session-history` for Phase 7.

---

### Phase 7 Exit Checklist

- [ ] `package_skill.py` created and registered in both installers
- [ ] Round-trip pack-and-extract works on Windows + macOS / Linux
- [ ] Pytest covers happy path + invalid frontmatter
- [ ] `make validate && make lint && make test` clean
- [ ] CHANGELOG updated
- [ ] Session history generated
- [ ] Plan complete -- ready for `/update-version` to bump to v1.2.0

---

## Items explicitly NOT adopted (security / policy reasons)

These items from `docs/archive/v1/v1.1/comparison-skills.md` Section 13 are out of scope and will NOT be implemented in this plan. They are recorded here for traceability:

- **N1: Anthropic's actual brand colors / fonts / logo from `brand-guidelines/`.** Rejected per the company-neutral framing rule (memory `feedback_no_employer_refs.md`) and the AGENTS.md reverse-engineering attribution rule. Phase 6's A2 implements the PATTERN with empty placeholders; the user MUST supply their own brand.
- **N2: Verbatim claude-only optimization loop from upstream `run_loop.py`.** Rejected per platform-agnostic policy and the v1.1.3 four-hook precedent. Phase 5's A6.2 + A7 implement the LOOP DESIGN with a CLI-agnostic adapter (claude / gemini / codex / opencode parity, no cross-CLI fallback).
- **N3: Claude.ai-specific instructions verbatim (`skill-creator/SKILL.md` lines 420-456).** Rejected because DevAI-Hub targets 5 platforms equally. Phase 5's A6.1 includes Claude.ai as ONE branch in a multi-platform decision table inside SKILL.md, not as the dominant narrative.
- **N4: Anthropic `.skill` consumer-side validation.** Rejected because DevAI-Hub can EMIT a `.skill` archive (Phase 7 / A16) but cannot validate that an Anthropic consumer parses it correctly. Phase 7 ships best-effort round-trip validation only.

## Cross-cutting constraint -- cross-platform installer parity

User-supplied hard constraint (recorded in this plan's Goal): every artifact added, modified, or removed in any phase must reach all 5 supported AI-IDE platforms (Claude Code, Cursor, Codex, Gemini, OpenCode) on Windows, macOS, and Linux. Operationally this means:

- Every new skill folder under `catalog/skills/` is auto-distributed by the existing recursive-copy logic (verified after Phase 3's A13 update to ensure per-skill subdirs are included).
- Every new standalone script under `scripts/` MUST have explicit copy lines added to BOTH `scripts/installer.sh` AND `scripts/installer.ps1`, modeled after the existing `generate_report.py` block.
- Every new template under `templates/documentation/` is auto-copied by the existing `install_templates` logic.
- Every phase ends with a dry-run installer verification on at least one OS; cross-OS verification is performed at minimum once per phase that adds bundled scripts (Phases 3, 4, 5, 6, 7).
- `templates/ai-instructions/base-*.md` (claude / cursor / codex / gemini / opencode) are touched ONLY when the platform-agnostic `{{SKILL_INDEX}}` placeholder needs updating; if any phase requires a platform-specific instruction change, ALL FIVE are edited in lockstep per the AGENTS.md "platform-agnostic" rule.
