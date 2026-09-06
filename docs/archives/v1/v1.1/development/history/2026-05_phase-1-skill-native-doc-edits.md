# Development Log: Phase 1 - Skill-Native Doc Edits (v1.1.5 adoption-skills plan)

**Date**: 2026-05-08
**Operator**: Benjamin Dourthe
**Assisted by**: Claude Opus 4.7 (1M context) via Claude Code
**Objective**: Execute Phase 1 of the v1.1.5 `adoption-skills` plan ([docs/archives/v1/v1.1/plans/adoption-skills.md](../../plans/adoption-skills.md)). Five doc-only edits (A14, A17, A15, A11, A12) that institutionalize patterns observed in upstream skill-authoring guidance, without adding any new file to the catalog file tree.
**Outcome**: All five sub-tasks (1.1-1.5) and the testing / stabilization step (1.6) complete. Six files changed (5 modified Markdown + 1 new known-gaps.md), one DEVLOG entry, one `[Unreleased]` CHANGELOG entry, one synced contributor doc. Test posture identical to v1.1.5 release baseline (406 passed, 1 skipped, 0 failures). One DEVIATION logged in `docs/archive/v1/v1.1/known-gaps.md` as DF-001. Ready to advance to Phase 2.

---

## 1. Starting State

- **Branch**: `main` (working tree directly on `main`; no feature branch was cut for Phase 1)
- **Starting commit**: `8952e03` - `v1.1.5: sectioned-bullet structure for commit messages`
- **Environment**: Windows 11 Enterprise, Bash via Git-for-Windows, PowerShell 5.1, Python 3.12.x, ShellCheck installed, no Node toolchain invoked.
- **Prior session reference**: none in `docs/archive/v1/v1.1/development/history/` (this is the first phase session for v1.1.5)
- **Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../plans/adoption-skills.md) (authoritative 7-phase plan, 17 adoption items A1-A17)
- **Comparison reference**: [docs/archives/v1/v1.1/comparison-skills.md](../../comparison-skills.md) (the upstream comparison report that produced the 17 adoption items)
- **User-supplied constraint**: the version bump (v1.1.5 -> v1.2.0) waits until Phase 7 wraps. All seven phases ship as a single v1.2.0 release rather than as seven incremental patch versions; intermediate phases ship under `[Unreleased]` in CHANGELOG.md with no version-string changes anywhere else.
- **User-supplied constraint**: every artifact added, modified, or removed must reach all 5 supported AI-IDE platforms (Claude Code, Cursor, Codex, Gemini, OpenCode) on Windows, macOS, and Linux through the existing installer recursive-copy logic.

Phase 1 is the "skill-native" tier of the plan: zero-code doc edits to existing tracked Markdown files. No new files in `catalog/`, no installer edits, no `data/` registry changes, no version bump. The only new file is `docs/archive/v1/v1.1/known-gaps.md` which the post-phase sequence creates regardless of phase content.

---

## 2. Chronological Steps

### 2.1 Sub-task 1.1 - A14: Pushy description guidance

**Plan specification**: Update `catalog/skills/workflow/create-skill-or-command/SKILL.md` and `catalog/skills/workflow/create-custom-command/SKILL.md` to add a new "Description Style: Combat Undertriggering" section advocating pushy descriptions (verbatim trigger phrases + `SKIP:` clauses) and a Common Rationalizations row.

**What happened**: Pre-implementation `Glob` for `catalog/skills/**/create-skill*/SKILL.md` returned no results; `Grep` for `create-skill-or-command` confirmed it appears only in plan / comparison / DEVLOG / CHANGELOG / global skills lists, never as a tracked SKILL.md file. The skill name does appear in the harness's global skill list surfaced by the system reminder, but that's an external skill (likely a Claude Code built-in or separately-installed skill), not a DevAI-Hub catalog entry. The de facto skill-authoring guide for DevAI-Hub authors is `AGENTS.md` "Adding a New Skill -> Write SKILL.md" at lines 59-112.

DEVIATION decision: applied A14 to two files instead of two non-existent files. (a) `catalog/skills/workflow/create-custom-command/SKILL.md` - the existing SKILL.md, which covers commands; commands also have descriptions and the same under-triggering risk applies. (b) `AGENTS.md` "Adding a New Skill -> Write SKILL.md" - the actual skill-authoring guide for DevAI-Hub. Both insertions carry the same pushy-description rules (verbatim trigger phrases, explicit `SKIP:` clauses, synonym coverage, action-then-trigger structure), the same 6-words-vs-60-words before / after example (adapted to commands vs. skills as appropriate), and a cross-link between them.

`create-custom-command/SKILL.md` did not previously have a Common Rationalizations table. Added one alongside the new section, with three rebuttals targeting the most common reasons authors leave descriptions narrow:

- "The description is short and clean, so it'll trigger fine." -> Claude undertriggers on narrow descriptions; explicit phrases beat poetic brevity.
- "Listing skip phrases is overkill." -> Without `SKIP:` clauses, every pushier description widens the false-positive surface.
- "The agent will figure out from the body what the command does." -> The body is tier 2 (loaded after the trigger fires); if the description doesn't trigger, the body never gets read.

**Key files changed**: `catalog/skills/workflow/create-custom-command/SKILL.md`, `AGENTS.md`.

**Troubleshooting**: the missing `create-skill-or-command` skill was the only deviation. Logged in `docs/archive/v1/v1.1/known-gaps.md` as DF-001 with the recommendation to leave skill-authoring guidance in AGENTS.md (a catalog skill that duplicates AGENTS.md would drift; AGENTS.md is the canonical authoring guide).

---

### 2.2 Sub-task 1.2 - A17: Three-tier loading model

**Plan specification**: Add a new `### Three-Tier Loading Model` subsection under "Adding a New Skill -> Skill Writing Guide" in AGENTS.md. Document tier 1 (always loaded, ~150-300 tokens, determines triggering), tier 2 (loaded on trigger, the SKILL.md body), tier 3 (loaded on demand, bundled `scripts/`, `references/`, `assets/` per the A13 convention from Phase 3) with the critical affordance that scripts EXECUTE without their text being loaded into context.

**What happened**: AGENTS.md does not have a "Skill Writing Guide" subsection by name; the equivalent location is `### 3. Write SKILL.md` under `## Adding a New Skill`. Inserted a new `#### Three-Tier Loading Model` block immediately after the A14 description-style block (which I'd just inserted), keeping all skill-content authoring guidance together inside `### 3. Write SKILL.md`.

The new block documents the three tiers with token-budget characterizations, then adds three practical authoring implications: push some-of-the-time content to references; push deterministic steps to scripts; keep tier 1 fields tight because they pay tokens on every catalog read across every session, while tier 2 / tier 3 budgets are per-trigger. Cross-links to the size-norm rule (immediately below in the same section, updated by sub-task 1.3) and to the bundled-subdir convention (which gets added separately in Phase 3 as the "Per-skill Bundled Resources" section).

**Key files changed**: `AGENTS.md`.

**Troubleshooting**: heading-level decision was the only call. The parent `### 3. Write SKILL.md` is H3, so `#### Three-Tier Loading Model` is H4. Avoids creating a peer-level H3 that would confuse the section structure under "Adding a New Skill".

---

### 2.3 Sub-task 1.3 - A15: SKILL.md size norm reconciliation

**Plan specification**: Replace the existing "Keep SKILL.md under 800 lines." rule with a 500-line target and 800 soft cap, plus a grandfather clause for existing skills.

**What happened**: Single-line replacement of the existing rule. New text:

> **SKILL.md size norm.** Target ≤500 lines for the SKILL.md body. Soft cap 800 lines. Beyond 500 lines, add a `references/` subdirectory with a table of contents and link to it from SKILL.md rather than expanding the body. Beyond 800 lines, the skill MUST be split or refactored before merge. Existing skills that exceed 500 lines are grandfathered - this norm is forward-looking and applies to new and substantially-rewritten skills only.

Did not retroactively shrink any existing skill (per the explicit instruction in the plan's sub-task 1.3 prompt).

**Key files changed**: `AGENTS.md`.

**Troubleshooting**: none.

---

### 2.4 Sub-task 1.4 - A11: Aesthetic-distinctiveness lens in frontend-ui-engineering

**Plan specification**: Add a new "Aesthetic Distinctiveness" section to `catalog/skills/developer-experience/frontend-ui-engineering/SKILL.md` after the existing Step 7 (Component Testing) and before Common Rationalizations. Include 4-6 concrete countermeasures, 2-3 reference patterns, and a Common Rationalizations row.

**What happened**: Added a 70-line section structured as "What the AI default looks like (avoid)" -> six countermeasures -> three reference patterns -> process step. The "AI default" sub-section names the visual pattern explicitly (centered hero + three-column feature grid + gradient call-to-action button + Inter typeface + uniform padding + 12px border-radius) so the agent recognizes when it's about to ship that exact shape. Six countermeasures: custom typography pairing, asymmetric layout, intentional density, distinctive accent color, motion that means something, copy with a voice. Three reference patterns: editorial multi-column, brutalist over-borders, restrained motion - the agent picks one direction, not a mash-up.

Added one row to the existing Common Rationalizations table:

- "The agent's default visual style looks fine, we can polish later." -> The agent's default IS the AI-slop default; "polish" applied to a generic foundation produces a polished generic foundation.

Added one entry to the existing Verification checklist:

- "Aesthetic direction note exists for the project (typography pairing, accent color, layout posture, motion philosophy, copy voice) and the shipped UI deviates from the AI-default 'centered hero + three-card grid + gradient button + Inter' pattern in at least 2-3 of those dimensions"

Per the plan's reverse-engineering attribution rule: did not copy any upstream content verbatim; framed everything in generic descriptive terms.

**Key files changed**: `catalog/skills/developer-experience/frontend-ui-engineering/SKILL.md`.

**Troubleshooting**: voice-matching call. The existing skill already has an opinionated voice in its Common Rationalizations table ("Your next hire, your investors, your customers on the train..."), so the new section was written to match that voice rather than copy the upstream's flatter checklist style. Result reads as part of the skill, not an annexe.

---

### 2.5 Sub-task 1.5 - A12: Static-poster / print workflow in creative-generation

**Plan specification**: Add a "Static Poster / Print Workflow" section to `catalog/skills/developer-experience/creative-generation/SKILL.md` after the existing image-prompt / deck guidance. Two-step approach: design philosophy (Markdown manifesto) then visual expression (.png / .pdf via existing skills or Pillow / matplotlib). Add a Common Rationalizations row. Explicitly do NOT introduce p5.js content.

**What happened**: The existing `creative-generation/SKILL.md` is short (35 lines pre-edit) and didn't follow the standard DevAI-Hub skill structure (no Common Rationalizations table, no Verification, no When-to-Use). Adding a full restructure would have exceeded Phase 1's scope. Compromise: A12 ships the Static Poster section AND a Common Rationalizations table specifically about the static-poster decision, leaving the rest of the file's structure unchanged. Future plan items can normalize the file if needed.

Added a 50-line section structured as "Step 1: Design philosophy" (a 30-80 line Markdown manifesto fixing color palette, typography, composition principles, and 1-2 reference movements) -> "Step 2: Visual expression" (route to `pptx-generation` / `docx-generation` / `pdf-document-generation` for standard formats, or a single-purpose Pillow / matplotlib script for one-off bespoke layouts) -> "Out of scope for this skill" (explicitly fences off p5.js / interactive HTML canvas, which belong to the `generative-art` skill being added in Phase 4 / A1).

Added a Common Rationalizations table with three rebuttals:

- "We don't need a philosophy step for one poster." -> Without it, the agent defaults to AI-slop visuals; the manifesto is 50 lines and saves a 10x rework.
- "I'll iterate on the rendered image directly." -> Rendered iteration is expensive and hard to compare; iterating on the manifesto first lets you fix direction in 5 minutes of writing instead of 30 minutes of re-rendering.
- "The user only said 'make a poster', so any poster is fine." -> The user said "poster" because they don't have the vocabulary to specify direction; the manifesto is how you offer a direction back to them.

**Key files changed**: `catalog/skills/developer-experience/creative-generation/SKILL.md`.

**Troubleshooting**: the file's lack of a standard skill structure was the only call. Decided to add what A12 explicitly required (the Static Poster section and a related Common Rationalizations table) without restructuring the rest, on the grounds that "no scope creep beyond the user's request" is a tighter constraint than "make every file conform to the latest skill template".

---

### 2.6 Sub-task 1.6 - Testing and stabilization

**Plan specification**: Run `make validate && make lint && make test` and fix any failures. Append a `## [Unreleased]` -> `### Changed` entry to `CHANGELOG.md` summarizing all five A14/A17/A15/A11/A12 edits. Do NOT bump the version number yet.

**What happened**: `make` is not on PATH on this Windows host, so the Makefile targets were executed manually with the same commands the Makefile would invoke.

JSON validation - all four catalog files load cleanly:

```bash
python -c "import json; d = json.load(open('data/skills.json', encoding='utf-8')); print(f'skills.json OK -- {len(d[\"skills\"])} skills')"
# skills.json OK -- 188 skills
python -c "import json; d = json.load(open('data/bundles.json', encoding='utf-8')); print(f'bundles.json OK -- {len(d[\"bundles\"])} bundles')"
# bundles.json OK -- 11 bundles
python -c "import json; d = json.load(open('data/workflows.json', encoding='utf-8')); print(f'workflows.json OK -- {len(d[\"workflows\"])} workflows')"
# workflows.json OK -- 17 workflows
python -c "import json; d = json.load(open('data/templates.json', encoding='utf-8')); print('templates.json OK')"
# templates.json OK
```

Note: needed `encoding='utf-8'` explicitly because Python on Windows defaults to cp1252, which fails on non-ASCII glyphs in the catalog (e.g. ≤ in `summary_l0` strings). Not a regression - just a Windows-host quirk for the manual invocation; the Makefile target on a POSIX host doesn't need the explicit encoding.

ShellCheck - clean against `scripts/installer.sh` and `install.sh`:

```bash
shellcheck --severity=warning scripts/installer.sh install.sh
# (no output - all warnings suppressed at requested severity)
```

Test suites - all green:

```bash
cd extensions/devai-skill-server && python -m pytest -q
# 37 passed in 1.84s
cd extensions/devai-code-search && python -m pytest -q
# 36 passed, 1 skipped, 52 warnings in 5.77s
cd extensions/devai-web-fetch && python -m pytest -q
# 23 passed in 4.11s
python -m pytest catalog/hooks/tests -q  # from repo root
# 310 passed in 23.34s
```

Total: 406 passed, 1 skipped, 0 failures. The 52 deprecation warnings in `devai-code-search` are pre-existing - they come from the third-party `pathspec` library's `GitWildMatchPattern` deprecation notice and are unrelated to any Phase 1 change. The 1 skipped test in `devai-code-search` is also pre-existing.

CHANGELOG `[Unreleased]` populated with a `### Changed` block in sectioned-bullet form per the v1.1.5 commit-message rule. Sections: Skill-authoring guidance in AGENTS.md / Skill body edits / Tests / Known gaps. No version-string bump anywhere - the entry stays under `[Unreleased]` until Phase 7 wraps.

**Key files changed**: `CHANGELOG.md`.

**Troubleshooting**: only the `make`-not-on-PATH issue and the Python default-encoding issue, both Windows-host quirks resolved by invoking the underlying commands directly with explicit UTF-8 encoding.

---

## 3. Quality Gate Results

| Gate | Threshold | Status |
|---|---|---|
| All tests passing | 0 failures | PASS - 406 passed, 1 skipped (pre-existing), 0 failures |
| Line coverage | >= 80% | N/A - doc-only changes; no code added |
| Lint errors | 0 | PASS - ShellCheck clean |
| Build / compile | succeeds | PASS - all four JSON catalogs valid |

GO. No quality gate bypassed.

---

## 4. Cross-Platform Reach

User-supplied constraint: every change must reach all 5 supported AI-IDE platforms on Windows, macOS, and Linux through the existing installer recursive-copy logic. Phase 1 audit:

| Edit | Target file | Distribution path | Reaches all 5 platforms? |
|---|---|---|---|
| A14 (commands) | `catalog/skills/workflow/create-custom-command/SKILL.md` | `catalog/skills/` recursive copy to Claude / Gemini / Codex; `{{SKILL_INDEX}}` block to Cursor / OpenCode / Copilot | YES |
| A14 (skills) + A17 + A15 | `AGENTS.md` | `templates/ai-instructions/base-*.md` rendering for Cursor / OpenCode / Copilot; AGENTS.md is the open-standard instruction file Codex / Cursor / OpenCode read directly; Claude Code reads it via the `@AGENTS.md` import in `CLAUDE.md` | YES |
| A11 | `catalog/skills/developer-experience/frontend-ui-engineering/SKILL.md` | same as A14 (commands) | YES |
| A12 | `catalog/skills/developer-experience/creative-generation/SKILL.md` | same as A14 (commands) | YES |

Per AGENTS.md "Platform coverage caveats": per-skill body content (the SKILL.md body) only lands as separate files on Claude Code / Gemini / Codex. Cursor / OpenCode / Copilot get the skill metadata via `{{SKILL_INDEX}}` and the AGENTS.md content directly. This is the existing platform-coverage state; Phase 1 does not change it. No installer dry-run was run because no installer file was modified - the existing recursive-copy logic already handles every modified path.

---

## 5. Deviations and Known Gaps

One DEVIATION logged. See `docs/archive/v1/v1.1/known-gaps.md` for the structured entry. Summary:

- **DF-001**: `create-skill-or-command` skill referenced in plan sub-task 1.1 prompt does not exist in catalog. A14 was applied to `create-custom-command/SKILL.md` and to AGENTS.md "Adding a New Skill -> Write SKILL.md" instead. Original A14 intent met. Suggested next step: leave skill-authoring guidance in AGENTS.md (recommendation: don't formalize a dedicated catalog skill; AGENTS.md is canonical and a duplicate would drift).

No other gaps. No suppressed lint rules, no skipped tests added by this phase, no quality-gate bypasses, no DEFERRED items.

---

## 6. Files Touched

```
M  AGENTS.md
M  CHANGELOG.md
M  CONTRIBUTING.md
M  catalog/skills/developer-experience/creative-generation/SKILL.md
M  catalog/skills/developer-experience/frontend-ui-engineering/SKILL.md
M  catalog/skills/workflow/create-custom-command/SKILL.md
M  docs/DEVLOG.md
A  docs/archive/v1/v1.1/known-gaps.md
A  docs/archive/v1/v1.1/development/history/2026-05_phase-1-skill-native-doc-edits.md  (this file)
```

Five sub-task target files modified, plus three post-phase artifacts (DEVLOG entry, CONTRIBUTING.md sync, this session history) and one new gap log.

---

## 7. Next Steps

Phase 2 of the plan: P0 cleanup + doc-coauthoring skill (A4, A9). Two sub-tasks:

- **2.1 - A4**: Resolve the `claude-api` skill index drift. Four user-options: restore from upstream, restore from prior DevAI-Hub history, de-list from registry, or supply content. Decision is asked of the user before execution begins.
- **2.2 - A9**: Ship a new `doc-coauthoring` workflow skill with full DevAI-Hub frontmatter. First skill that gets registered in all three `data/` files during this plan.

Phase 2 also exercises the cross-platform installer-verification step for the first time in this plan (a dry-run install on at least one OS to confirm the new skill reaches all 5 IDEs).
