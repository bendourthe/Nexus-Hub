# Session History -- v3.0.0 Phase 8: Deprecation shims + migration + count reconciliation

**Date**: 2026-06-04
**Plan**: [`docs/releases/v3/v3.0/plans/command-consolidation-skill-security.md`](../../plans/command-consolidation-skill-security.md)
**Phase**: 8 of 10 -- Deprecation shims + migration + count reconciliation
**Outcome**: complete; all sub-tasks (T036-T039) closed, all applicable quality gates green.

## Goal

Keep every old command working after the 41 -> 14 consolidation, document the migration for users, and reconcile the command count across every prose surface so a WN-v24-1-class count drift cannot ship. The phase stability gate: every old command name forwards to its new command + scope with a deprecation notice; the count prose and the platform templates are reconciled; `make validate` is green.

## Subtasks completed

1. **T036 -- Deprecation shims (40 files).** Converted the 40 old command files in `catalog/commands/` into forwarding deprecation shims. The plan says "41 old command files (except `constitution.md`)"; `constitution` was repurposed into a permanent alias in Phase 5, so the actual shim set is 40 and `constitution.md` / `commit.md` are left untouched as permanent aliases (they print no deprecation notice and are not scheduled for v4.0.0 removal). Each shim is a uniform file: a deprecation `description` frontmatter, the title `# /<old> (deprecated)`, a sentence stating the v4.0.0 removal and the forward target, a note that behavior is unchanged because the same retained skill runs, an indented one-line notice to print, and a final instruction to delegate to the new command + scope with arguments passed through. The 40 files were generated from a single template + data table so the markdown-style and ASCII contract lives in one place.
2. **T037 -- Migration doc + CHANGELOG table.** Wrote `docs/v3/v3.0/command-migration.md`: the deprecation timeline (shims through v3.x, removed v4.0.0), a scope-resolution explainer, the grouped old -> new -> scope mapping (40 rows + the 2 skill-only scopes `/update config` and `/research deep`), the 2 permanent aliases, and the new-in-v3.0.0 additions (`skill-security-scan` + `nexus-skill-scanner`, `agent-orchestration-primitives`). Added the same old -> new rename table to `CHANGELOG.md` under a new `### Deprecated` subsection of `## [Unreleased]` and corrected the Unreleased intro line that previously said the rename table only appears at release.
3. **T038 -- Count reconciliation.** Updated the command count from 41 to 14 across every live prose surface: `data/marketplace.json` description (no `total_commands` field exists), `AGENTS.md` "Current catalog" line + structure-tree comment (both annotated with the "+ 2 permanent aliases + 40 deprecated v3.x shims" breakdown), `README.md` (3 lines: opening tagline, catalog bullet, post-install summary), and -- by deliberate one-surface extension beyond the enumerated list -- `.claude-plugin/plugin.json` description, so the canonical manifest is not left stale. The 5 `templates/ai-instructions/base-*.md` files were inspected and need no edit (their `## Key Commands` block is a generic build-command placeholder, not a command enumeration).
4. **T039 -- Stabilization.** Emulated `make validate` (all green), confirmed `check_version_sync.py` stays green at 2.4.0 across all six surfaces, confirmed the new/edited files are ASCII-clean, and programmatically verified all 40 shims forward to the correct new command + scope.

## Key decisions

- **40 shims, not 41.** The plan's "41 old command files (except `constitution.md`)" reflects the original 41-command surface; `constitution` became a permanent alias in Phase 5. The shim set is therefore the 40 remaining old commands. `constitution.md` and `commit.md` are permanent aliases and were not touched.
- **Generated the shims from one template.** For 40 near-identical files, a single template + data table (run as a throwaway Python generator via stdin, never written to `scripts/`, so no installer registration is needed) is less error-prone than 40 hand-edits: one place for the blank-lines-around-fence markdown rule and the ASCII assertion. The full data table is in the commit and the generation was verified after the fact (git diff scope, notice presence, and a forward-target check).
- **`### Deprecated`, not prose.** The rename table went into the canonical Keep-a-Changelog `Deprecated` category (after `Changed`) rather than a prose paragraph, so a downstream `generate-changelog` / release-notes pass parses the scheduled removal cleanly at release.
- **Extended T038 to `plugin.json` (documented).** T038's enumerated surfaces are marketplace.json, AGENTS.md, README, and the templates. Leaving `.claude-plugin/plugin.json` reading "41 commands" would be exactly the count drift this phase exists to prevent, so the command-count token there was updated too; the rationale and the separate pre-existing skill-count drift it surfaced are recorded as WN-v30-6.
- **Scope discipline on adjacent drift.** On each edited count line, only the command-count token was changed. The adjacent pre-existing "245 curated skills" drift in `marketplace.json` / `plugin.json` (AGENTS/README are at 247) was left untouched and logged as WN-v30-6 for Phase 10, rather than fixed out of scope.

## Test results

- **Emulated `make validate`** (`make` not on PATH on the Windows host per WN-v30-1/-5): edited `marketplace.json` / `plugin.json` are valid JSON; `skills.json` OK (247 skills); bundle audit PASS (0 errors, 1 pre-existing warning in `catalog/skills`, unrelated to this phase); unicode-safety 0 errors; no-personal-paths / supply-chain-IOCs / workflow-security / solution-frontmatter all exit 0; `check_version_sync.py` green at 2.4.0 across all six version surfaces.
- **ASCII check**: all 40 shims and `command-migration.md` are ASCII-clean (0 non-ASCII). The only non-ASCII in this phase's touched files is pre-existing -- AGENTS.md size-norm `<=` glyphs and old v2.4.0 CHANGELOG em-dashes -- none introduced this phase.
- **Shim forward-target check**: a script extracted the delegate from each shim and compared it to the expected new command + scope; 40/40 matched, 0 mismatches.
- **Change-set check**: git shows exactly 40 command files modified, both permanent aliases (`constitution.md`, `commit.md`) untouched, and 1 new untracked file (`command-migration.md`); no stray build artifacts.
- `make test` was not run: Phase 8 changed no Python/hook/shell code (40 markdown shims + 1 doc + count prose only), so there is no new-code test surface; the existing pytest suites are unaffected.

## CI/CD edits

- None. Phase 8 added no new script command, environment variable, dependency, or test path. The existing `.github/workflows/ci.yml` `validate` job (which runs the validators emulated here, plus the catalog scan gate) and `tests` job already cover the change. 0 workflows touched, 0 proposed edits.

## Deviations

- **T038 extended to `.claude-plugin/plugin.json`** beyond the prompt's enumerated surfaces, to avoid leaving the canonical manifest at "41 commands" while every other surface reads "14". Recorded with its rationale in WN-v30-6; it strengthens the anti-drift goal of the phase rather than leaving a gap.

## Known gaps

See [`docs/releases/v3/v3.0/known-gaps.md`](../../known-gaps.md). Three new open items this phase: DF-v30-4 (the 40 deprecation shims and the historical "41 -> 14" count references are intentionally retained through v3.x and removed at v4.0.0), WN-v30-5 (local `make` unavailable on the Windows host, gate emulated directly all-green; no shell surface this phase; covered by CI), and WN-v30-6 (the pre-existing 245-vs-247 skill-count prose drift in the `marketplace.json` / `plugin.json` descriptions; reconcile at the Phase 10 `/update release`, and consider extending the count-consistency guard to non-version counts). Summary: 10 open (4 DF, 6 WN), 0 resolved.

## Next steps

- **Phase 9 -- Ingested known-gaps (carried forward from v2.4.0)**: add Swift + Kotlin code-search extractors under `extensions/nexus-code-search` clearing the 80% recall gate (DF-v24-7), merge the duplicate `## Quality Checklist` / `## Verification` headings in the affected skills (WN-v24-2), and confirm + record the `validate_solution_frontmatter.ps1` no-action decision (NI-v24-1).
- **Phase 10 -- Live verification + release readiness**: the final phase, which runs the full green gate, dogfoods `/review skill-scan` over the catalog, handles the env-gated re-deferrals and DF-v23-9, and runs `/update release` to bump every surface to v3.0.0 (where WN-v30-6's skill-count drift should also be reconciled).
