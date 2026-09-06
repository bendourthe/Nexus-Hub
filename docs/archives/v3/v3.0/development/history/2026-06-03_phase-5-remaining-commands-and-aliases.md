# Session History -- v3.0.0 Phase 5: Remaining commands + permanent aliases

**Date**: 2026-06-03
**Plan**: [`docs/releases/v3/v3.0/plans/command-consolidation-skill-security.md`](../../plans/command-consolidation-skill-security.md)
**Phase**: 5 of 10 -- Remaining commands + permanent aliases
**Outcome**: complete; all sub-tasks (T018-T025) closed, all applicable quality gates green.

## Goal

Ship the remaining eight verb-first commands (`/compare`, `/research`, `/skills`, `/spec`, `/session`, `/setup`, `/memory`, `/usage`) and the two permanent convenience aliases (`/constitution` -> `/spec constitution`, `/commit` -> `/update commit`) as thin dispatchers over the retained skills, following the Phase 1 scope-mechanism contract. Completing this phase means all 14 consolidated commands exist, which unblocks plan-Phase 8 (deprecation shims, migration doc, count/template reconciliation). No existing behavior is removed: the rich skill bodies are retained as scope modules and the old command files keep functioning unchanged (shims land in Phase 8). Pure catalog content -- no new code, dependency, credential, or outbound call.

## Subtasks completed

1. **T018 -- /compare.** Created `catalog/commands/compare.md` (43 lines), renaming `compare-project`. Scope is auto-inferred from the source argument (`repo` for a Git URL, `article` for an http(s) article URL, `local` for a path) rather than menu-prompted, because the source type is almost always unambiguous. The body preserves the mandatory Security and Reverse-Engineering assessment sections (per the MCP Registry Policy reverse-engineer-first decision tree) and the chain into `/plan from-comparison`.
2. **T019 -- /research.** Created `catalog/commands/research.md` (41 lines), merging three lineages: `deep` (the `deep-research` skill -- fan-out multi-source web research with adversarial verification and a cited synthesis), `compile` (`compile-deep-research` -- merge multiple reports into one deduplicated cited document), and `report` (`generate-report` -- Markdown -> docx/pptx via a template). Bare invocation asks the scope; a research question routes to `deep`, a document list routes to `compile`.
3. **T020 -- /skills.** Created `catalog/commands/skills.md` (48 lines), merging `search-skills` (`search`), `commands-cheatsheet` (`list`), `create-skill-or-command` (`create`), and `import-skills` (`import`), plus the v3.0.0 pre-install `scan` scope backed by the Phase 2 `skill-security-scan` skill (the same lens `/review skill-scan` uses; it adjudicates manually-collected findings until the Phase 6 `nexus-skill-scanner` engine lands). The body recommends `scan` before `import` for skills sourced outside the trusted catalog.
4. **T021 -- /spec.** Created `catalog/commands/spec.md` (43 lines), merging `clarify` (`clarify-spec`), `analyze` (`analyze-spec`), and `constitution`. The `constitution` scope delegates to the `project-constitution` skill (the retained fat skill that the old `constitution` command drove end-to-end), documenting the `check <plan-path>` read-only Constitution Check sub-mode and the permanent `/constitution` alias.
5. **T022 -- /session.** Created `catalog/commands/session.md` (39 lines), merging `continue` (`continue-session`), `wrap-up` (`wrap-up-session`), and `history` (`generate-session-history`). Notes that `history` is also the sub-step the `/implement` per-phase sequence invokes.
6. **T023 -- /setup, /memory, /usage.** Created `catalog/commands/setup.md` (36 lines), merging `setup-project` (scope `project`, default) and `install-pre-commit-review-hook` (scope `hooks`); and the two zero-scope direct dispatchers `memory.md` (22 lines, -> `manage-memory`) and `usage.md` (22 lines, -> `check-usage`). The no-scope commands skip the scope-menu contract entirely and delegate directly.
7. **T024 -- Permanent aliases.** Rewrote `catalog/commands/constitution.md` (22 lines) from the prior rich command into a permanent thin alias forwarding `/constitution`, `/constitution amend`, and `/constitution check <path>` to `/spec constitution`; created `catalog/commands/commit.md` (22 lines) forwarding `/commit` to `/update commit`. Both are explicitly documented as permanent aliases, not v3.x deprecation shims (no deprecation notice, no v4.0.0 removal). `commit.md` notes the external `commit-commands` `/commit` may also be present.
8. **T025 -- Stabilization.** Verified all 14 commands + 2 aliases exist, are under the 150-line cap, and are ASCII-only; emulated `make validate` (all green); reviewed scope resolution against the authoring checklist for every new command.

## Key decisions

- **The alias-loop trap, resolved at `/spec`.** The design's 41 -> 14 map lists `/spec`'s constitution delegate as `constitution`, but `/constitution` (T024) forwards *to* `/spec constitution`. Delegating `/spec constitution` back to a `constitution` command would be an infinite forward loop. The fat logic actually lives in the `project-constitution` skill (`catalog/skills/workflow/project-constitution/SKILL.md`), which the old `constitution` command "drives end-to-end," so `/spec constitution` delegates there directly. No loop, no lost behavior. Rewriting `constitution.md` into a thin alias therefore preserves the full governance workflow.
- **No-scope commands get the thinnest shape.** `/memory` and `/usage` have zero scopes per the design (rows 13-14), so they skip the numbered-menu contract entirely and delegate directly to a single skill -- closer to `implement.md`'s argument-driven shape than `review.md`'s menu shape. They are the two smallest command files in the catalog (22 lines each).
- **Auto-inferred scope for /compare.** `compare-project` already detected its source type (repo / article / local), so `/compare` infers scope from the source argument instead of showing a menu, matching the "infer where unambiguous" rule in the scope-mechanism contract (step 5).
- **Permanent aliases vs deprecation shims.** Per the design's Open Questions (Section 8), `/constitution` and `/commit` are kept as permanent first-class aliases because they are heavily cross-referenced (`/constitution` by `/plan`, `analyze-spec`, `project-constitution`) and high-frequency (`/commit`). They print no deprecation notice and are exempt from the Phase 8 shim conversion (T036) and the v4.0.0 removal.
- **Count reconciliation deferred; CHANGELOG untouched.** Consistent with Phases 3-4, `marketplace.json` `total_commands`, the AGENTS.md/README count prose, and the 5 platform templates are NOT updated this phase -- that is plan-Phase 8 (T038). Commands need no `data/*.json` registration, so Phase 5 is purely additive (ten Markdown files). Touching counts now would be premature while the originals are still active and the shims do not yet exist.

## Test results

- All ten Phase 5 files under the 150-line dispatcher cap: compare 43, research 41, skills 48, spec 43, session 39, setup 36, memory 22, usage 22, constitution 22, commit 22. ASCII-only: 0 non-ASCII characters across all ten (verified directly with a `[^\x00-\x7F]` scan); none appear in the unicode-safety WARN list.
- Roster check: all 14 consolidated commands present (describe, plan, implement, test, review, update, compare, research, skills, spec, session, setup, memory, usage) plus the 2 permanent aliases (constitution, commit). Each has valid `---` frontmatter, exactly one `# /` heading, and a Delegation/Forwarding section.
- Emulated `make validate` (each validator invoked directly, `make` unavailable on host per WN-v30-1): `skills.json` OK (247 skills), `bundles.json` (15) / `workflows.json` (17) / `templates.json` OK; orphan-bundle audit **PASS** (0 errors, 0 warnings); no-personal-paths, unicode-safety (0 errors), supply-chain IOCs, workflow-security, solution-frontmatter all exit 0; `check_version_sync.py` green at 2.4.0 across all six surfaces. **Aggregate: ALL GREEN.**
- All delegate targets confirmed present before authoring: catalog commands `compare-project`, `compile-deep-research`, `generate-report`, `search-skills`, `commands-cheatsheet`, `create-skill-or-command`, `import-skills`, `clarify-spec`, `analyze-spec`, `continue-session`, `wrap-up-session`, `generate-session-history`, `setup-project`, `install-pre-commit-review-hook`, `manage-memory`, `check-usage`, `generate-commit-message`; available skills `deep-research`, `skill-security-scan` (Phase 2), `project-constitution`. The `[[agent-orchestration-primitives]]` cross-link resolves.
- Scope-resolution review (per command): bare -> numbered menu with one recommended default (or auto-infer for `/compare`, direct delegate for `/memory` and `/usage`); recognized scope token -> skip menu; path/slug -> routed; every scope token -> explicit one-to-one delegation target. All pass the scope-mechanism authoring checklist.

## CI/CD edits

- None. GitHub Actions (`.github/workflows/ci.yml`, plus `codeql.yml`) is the active CI; its validate job runs the same validators emulated locally. Phase 5 added no new script command, environment variable, or dependency, and the ten new/modified command files auto-distribute via the recursive folder copy (no installer edit needed -- they are `catalog/commands/` artifacts, not `scripts/<name>.py`). 0 workflows touched, 0 proposed edits.

## Deviations

- None. The plan's T018-T024 prompts were followed as written. The one clarifying choice (delegating `/spec constitution` to the `project-constitution` skill rather than a `constitution` command) is a loop-free realization of the plan's stated intent, not a deviation, and is documented under Key decisions.

## Troubleshooting / environment notes

- `make` and `shellcheck` are unavailable on the Windows dev host (consistent with WN-v30-1), so `make validate` was emulated by invoking each validator directly. No shell scripts were touched this phase, so the ShellCheck pass is not applicable to the diff.
- A OneDrive Files-On-Demand placeholder gap means files under `docs/` (DEVLOG.md, known-gaps.md, the session-history tree) and `.github/` are visible to the Windows-native tools (Read/Glob/Write/Edit and git blob access) but not always to the Bash POSIX layer (`find`/`ls`). All `docs/` artifacts were therefore written with the native tools and verified via git, not via Bash directory listings.
- The pre-existing unicode-safety WARNs are punctuation debt in other files (legacy templates); the ten Phase 5 files were verified ASCII-only and are not in scope to clean adjacent files.

## Known gaps

See [`docs/releases/v3/v3.0/known-gaps.md`](../../known-gaps.md). No new open items this phase. WN-v30-1 (Phase 1, ShellCheck deferred to CI) and WN-v30-2 (Phase 2, build_skills_catalog.py drift) remain open and unchanged; the summary stays at 2 open WN.

## Next steps

- **Phase 6 -- nexus-skill-scanner engine (re-full)**: scaffold `extensions/nexus-skill-scanner/`, implement the static analyzers for detection classes 1-13/15-16, add risk scoring + SARIF/JSON/Markdown emitters + framework-ID tagging, register the `scripts/scan_skill_security.py` entry point in both installers with a `make scan` target, subsume the existing `validate_skills` secret scan / `scan_supply_chain_iocs` / `validate_workflow_security` validators behind it (behavior-preserving), and add the CI catalog gate with malicious/clean fixtures. This is the engine that backs the `/skills scan` and `/review skill-scan` scopes shipped in Phases 4-5.
