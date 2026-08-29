# Last-Phase Evidence - v4.2.1 Guide Visual Education

**Date**: 2026-08-29
**Branch**: `feat/v4.2.1-guide-visual-education`
**Phase starting commit**: `ab7b51ee` (Phase 6)
**Comparison base**: `origin/develop` (`38a63ddc`, merge of unpublished v4.2.0 PR #145)
**Plan**: `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md`

The v4.2.0 record that previously occupied this path is preserved at `docs/releases/v4/v4.2/development/last-phase-evidence-v4.2.0.md`.

## 1. Architecture refactor

Commands:

> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root docs`
>
> `InventoryExit=0`
>
> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py refgraph --root docs`
>
> `RefgraphExit=0`

Both commands ran in one pass and ended with process `exit_code: 0` after 138720 ms. `project-refactor` has no bundled detector scripts. Propose-only classification of files this plan added or edited, from `git diff --stat origin/develop...HEAD` plus a markup scan of the canonical guide:

- Stay: `guides/website/nexus-hub-guide.html`; `guides/website/README.md`; `guides/website/example/training-scenes.json`; `guides/website/example/glow-booth/`; `guides/website/example/glow-booth-shuffle-reference/`; `guides/website/glow-booth.zip`; `tests/guides/test_nexus_hub_guide.py`; the v4.2.1 plan, content-map v4.2.1 section, known-gaps, docs-cleanup report, session histories, `last-phase-evidence-v4.2.0.md`, and this evidence file under `docs/releases/v4/v4.2/`.
- Stay on disk, not taught: `guides/website/example/trivia-quiz/` and `guides/website/example/quiz-shuffle-reference/`. Grep of `guides/website/nexus-hub-guide.html` for `trivia-quiz` and `Trivia Quiz` returned zero matches.
- Move / Archive: none proposed. Phase evidence folders stay under the active minor until `/update release` retention.
- Empty directories introduced by this plan: none.
- Duplicate content: maintainer `example/training-scenes.json` and the inline `#nh-training-scenes` block are intentional copies; tests assert they parse equal.
- No top-level installer-copied `scripts/*.py` was added. No `.github/workflows/` edit.

No confirmation gate for a file move was required. Trivia Quiz is not deleted in this phase.

## 2. Known-gaps reconciliation

Glob of `docs/**/known-gaps.md` found 31 unique files (32 path hits; `docs/releases/v4/v4.2/known-gaps.md` appears twice because of mixed path separators).

File-level Status `in-progress` in this pass:

- `docs/releases/v4/v4.2/known-gaps.md` (this minor)
- `docs/releases/v4/v4.1/known-gaps.md` (prior minor; open DF/WN/QG items remain on that ledger)

`docs/releases/v4/v4.0/known-gaps.md` is finalized. `docs/releases/v3/v3.20/known-gaps.md` and `docs/releases/v3/v3.21/known-gaps.md` are finalized. Remaining v3 and archive ledgers are historical or complete; none was rewritten. No `## v3.20.0` section was appended to v3.16 or v3.20.

This plan produced:

- Closed v4.2.0 DF-1: maintainer screenshots that triggered this plan exist (visual QA ledger, 2026-08-29). Remaining human proof (Lighthouse Accessibility, rendered last-phase visual QA, workshop 4-of-5) is re-homed to v4.2.1 DF-1.
- Closed v4.2.0 QG-1: remote PR #145 `pytest tests` already passed on the unpublished substrate. This session's unbounded local `python -m pytest -q tests` (3534 collected) reached about 16 percent after eight minutes and was stopped; that honesty is v4.2.1 QG-1, not a reopening of the closed 4.2.0 row.

Not absorbed:

- v4.1.0 DF-1 / WN-1 / QG-1
- v4.1.1 DF-1
- v4.1.2 WN-1 / QG-1 (already resolved on the v4.1 ledger)
- v4.0 DF-1 (report-artifact upload), declined again in the pipeline comparison below

## 3. Living docs architecture

Scan:

> `docs/handbooks/` authored files = 1 (`README.md`); `docs/handbooks/html/.gitkeep` and `docs/handbooks/markdown/.gitkeep` only; catalog atlas/companion HTML = 0
>
> No `docs/testing/` or `docs/validation/` path exists.

The living handbook root remains a scaffold. Release-bound plan, content-map, histories, known-gaps, cleanup report, and this evidence file remain under `docs/releases/v4/v4.2/`. `docs/decisions/` was not used for this UX patch; the plan is the attribution record. `docs/DEVLOG.md` still has a v4.2.0 index row only; the v4.2.1 index line belongs to `/update release`. `docs/todos.md` tracks this plan as the active dashboard until merge. `docs/README.md` already names `docs/releases/v4/v4.2/` as the active 4.x minor. Root `README.md` Interactive Guide blurb was stale ("eight-scene IDE workbench") and is updated in this phase to Foundations four stations, Glow Booth slideshow, and Cheatsheets. `guides/website/README.md` six-node list said "Build" and is corrected to "Implement" to match the frozen node label.

## 4. Git-tree hygiene

Command:

> `python scripts/check_release_preconditions.py --branches --repo-settings`

Quoted result:

> Branch hygiene (merged into origin/develop)
>   10 merged branch(es) are cleanup candidates:
>     - origin/backmerge/v4.0.0-release
>     - origin/backmerge/v4.1.0-release
>     - origin/backmerge/v4.1.1-release
>     - origin/backmerge/v4.1.2-release
>     - origin/feat/v4.1.0-release
>     - origin/feat/v4.1.1-adoption-openworker-security-refinement
>     - origin/feat/v4.1.1-release
>     - origin/feat/v4.1.2-ponytail-planning
>     - origin/feat/v4.1.2-release
>     - origin/feat/v4.2.0-interactive-guide-redesign
>   (11 branch(es) with an open PR were excluded)
>   1 branch(es) survive a CLOSED, unmerged PR:
>     - origin/backmerge/v3.20.0
>   delete_branch_on_merge does NOT cover these. Review and delete by hand.
>   Reporting only -- nothing was deleted.
> Repository settings
>   OK: delete_branch_on_merge is enabled
>   OK: repository description agrees with README.md

No remote cleanup, settings edit, push, tag, or release was performed.

## 5. CI/CD coverage

DETECT: GitHub Actions (`.github/workflows/*.yml`).

COMPARE: existing-pipeline comparison against `catalog/skills/infrastructure/cicd-architect/references/repository-native-profiles.md` (23 canonical fields).

PROPOSE: no pipeline file changes. Silence is not approval; none is requested.

APPLY: none.

RECORD: inherited v4.0 DF-1 (report artifacts not uploaded) stays declined. Local unbounded `pytest tests` is v4.2.1 QG-1.

Coverage inventory:

> `python scripts/ci/run.py --profile fast --list`
>
> profile: fast / windows; groups: catalog-parse, hygiene, workflows, version
>
> `python scripts/check_required_check_coverage.py`
>
> `Required-check coverage: OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally.`
>
> `python scripts/check_installer_parity.py` -> `installer parity: PASS`
>
> `python scripts/check_version_sync.py` -> canonical `4.1.2` (bump belongs to `/update release`)

`git diff --name-only origin/develop...HEAD -- .github catalog/mcp-configs scripts/installer.sh scripts/installer.ps1 catalog/hooks/settings.json` is empty. No second required workflow. No workflow-level `paths:` on `ci.yml`. `ci.yml` `on:` is `pull_request` + `merge_group` + `workflow_dispatch`. No new top-level `scripts/*.py`. Two installers: parity checker PASS (hard gate in this pass).

This plan only extends `tests/guides/test_nexus_hub_guide.py`, which the existing `tests` / `tests-windows` jobs already cover. Those job names feed the `ci-required` aggregate; the declared required contexts on `develop` remain `validate`, `shellcheck`, `ci-required`, `colocation`, `verify`.

Existing-pipeline comparison:

| # | Field | State | Evidence |
|---|---|---|---|
| 1 | Provider detected | PASS | GitHub Actions; `.github/workflows/ci.yml`, `post-merge.yml`, `release.yml` |
| 2 | Profiles exist | PASS | `scripts/ci/run.py` profiles `fast`, `full`, `platform`, `report`, `release` |
| 3 | No duplicated validator | PASS | `ci.yml` jobs call `scripts/ci/run.py`; validator lists live in `scripts/ci/profiles.py` |
| 4 | Feature-push runs nothing | PASS | `ci.yml` `on:` is `pull_request` + `merge_group` + `workflow_dispatch`; no ordinary branch `push` |
| 5 | Integration gate is complete | PASS | `ci.yml` runs on PRs to `main`/`develop` including Windows and bootstrap/install-smoke jobs |
| 6 | No duplicate post-merge suite | PASS | `post-merge.yml` is smoke and provenance, not `ci.yml` again |
| 7 | Post-merge is minimal | PASS | `post-merge.yml` smoke job plus advisory version note |
| 8 | Release is separate | PASS | `release.yml` on `v*` tags and dispatch |
| 9 | Aggregate required check | PASS | `ci-required` plus `validate`, `shellcheck`, `colocation`, `verify` in `docs/policy/required-checks.json` |
| 10 | No per-leg required context | PASS | required list has no `job (leg)` names |
| 11 | Scoping is job-level | PASS | no workflow-level `paths:` on `ci.yml` |
| 12 | Runner selection | PASS | `ubuntu-latest` and `windows-latest` GitHub-hosted |
| 13 | Expensive legs pre-merge | PASS | Windows PowerShell 5.1 and installer-smoke run on the pull request |
| 14 | Immutable references | PASS | third-party actions use 40-character SHAs with version comments |
| 15 | Least-privilege permissions | PASS | `ci.yml` `permissions: contents: read` |
| 16 | Caching | PASS | pip cache keyed to manifests on CI Python jobs |
| 17 | Concurrency | PASS | `ci.yml` cancels superseded PR runs; release and post-merge do not |
| 18 | Untrusted forks | PASS | `contents: read`; no secrets in `ci.yml` |
| 19 | Reports produced | PASS | `scripts/ci/reporting.py` writes summary, JUnit, and metadata locally |
| 20 | Reports published | DECLINED (inherited) | machine-readable artifacts are not uploaded. v4.0 DF-1; not reopened |
| 21 | Deployment boundary | PASS | no application deploy job |
| 22 | Failure recovery | PASS | 9F requires local reproduction before re-push |
| 23 | External settings | PASS | `delete_branch_on_merge` enabled; description agrees with README |

Comparison conclusion: PASS for this plan. The only canonical pipeline difference is inherited v4.0 DF-1 (artifact upload). This plan adds no workflow, MCP row, installer copy line, or hook registration.

## 6. Goal-vs-codebase review

Plan Goal restated: turn the unpublished v4.2.0 guide into a concise, illustrated, highly interactive, and accessible first-contact site that teaches AI terms visually, walks a fun buggy web app to a fixed one with a new feature, and merges Workflows plus Reference into one Cheatsheets tab, without changing command semantics or the single-file offline contract.

Goals First definition of done, inspected independently of phase checkboxes:

| Observable | Artifact | Verdict |
|---|---|---|
| Opaque sticky header | `.site-header { position: sticky; background: var(--nav-bg); }` with opaque `--nav-bg` in both themes; no transparent nav | PASS (rendered constellation bleed is DF-1) |
| Icon-only GitHub | `.nav-gh` SVG plus `aria-label="Nexus-Hub on GitHub"`; `test_github_control_is_icon_only` | PASS |
| Sun/moon default dark | `test_theme_control_is_sun_moon_default_dark`; `portfolio-theme` allowlist | PASS |
| Readable light wordmark | `.brand .wordmark b { color: var(--ink); }`; `test_wordmark_uses_theme_ink` | PASS (Lighthouse contrast remains DF-1) |
| Copy at terminal end | `test_copy_button_is_not_inside_data_copy_code` | PASS |
| Light terminals in light theme | `test_light_theme_terminal_is_not_near_black` | PASS (rendered proof DF-1) |
| Modern Home loop; exact `Map and evaluate` | six `.nhg-ribbon-name` nodes including Implement; `test_home_loop_nodes_are_not_abutting_rectangles` | PASS |
| Foundations four visual stations | Prompt / Context / Harness / Loop engineering as `.nhg-station`; no `type="range"` | PASS (comprehension study is DF-1) |
| Training slideshow of Glow Booth | `#nhTraining`, `.ts-slide`, `#nhBoothHero`; file grid behind Peek; eight scenes, cap twelve | PASS |
| Cheatsheets merge | `#page-cheatsheets`; primary nav has no Workflows or Reference; `HASH_REWRITES` | PASS |
| No cinematic video engine | no `scroll-scrub-engine`; no `<video` in Foundations; local CSS/JS only | PASS |
| No hardcoded catalog counts | `test_onboarding_has_no_hardcoded_catalog_counts` | PASS |
| Every catalog command is Training, Cheatsheets, or declined | `test_every_catalog_command_is_training_cheatsheets_or_declined` | PASS |
| Trivia Quiz retired from published teaching | zero matches in the canonical HTML; trees remain on disk | PASS |
| Single-file offline; no CDN | `test_no_runtime_cdn_font_script_or_image`; `test_one_html_document` | PASS |

Root README workbench wording was a Goal miss in living docs and is fixed in this phase. Integration, merge, and release are not proven in this file until T026 completes.

Verdict: PASS for the local guide contract; human/browser evidence and remote CI are recorded gaps, not silent passes.

## 7. Human/manual testing suggestions

Emitted. Not run in this session (no browser automation in this Cursor session, no workshop cohort).

1. Re-check the ten visual QA ledger items in both themes at 1440x900, 1024x768, 390x844, and 1920x1080: opaque sticky header; icon GitHub; sun/moon default dark; copy at terminal end; light terminals and copy chip; readable light wordmark; Home loop not rigid boxes; Foundations not a range slider; Foundations not three identical text cards; Training not a default IDE workbench.
2. Keyboard: ArrowLeft / ArrowRight / Space on Training; Home / End; page-level arrows off Training; keys disengage in `[data-nhg-keys='self']`.
3. `prefers-reduced-motion`: Foundations comparison states stay static; constellation does not animate.
4. Open `guides/website/nexus-hub-guide.html` via `file://` and confirm `#untrustedCopyWarning` is visible.
5. Hash redirects: `#reference` and `#workflows` become `#cheatsheets`; `#explore` (and plan/build/harden/ship/communicate) become `#cheatsheets/<id>`.
6. Lighthouse Accessibility at least 90 in light and dark. Performance, SEO, and Best Practices remain advisory.
7. Non-engineer read-through of Foundations and Training: can they say what prompt, context, harness, and loop engineering change, and watch Glow Booth go from 4/5 stamps to a shuffle-plus-sparkle fix? Do not invent a five-person workshop. Bounded non-pass if no participants are available.

Quoted result: not run. Recorded as v4.2.1 DF-1. Do not invent a walkthrough.

## 8. Full-suite testing and stabilization

Quoted local evidence:

> `python -m pytest -q tests/guides/test_nexus_hub_guide.py` -> `38 passed, 1 skipped in 0.18s` (skipped: `NEXUS_HUB_PORTFOLIO_ROOT` unset)
>
> `python scripts/ci/run.py --profile fast` -> `PASS: 12 passed, 0 failed, 0 skipped, 0 advisory in 8.0s`
>
> `python scripts/check_installer_parity.py` -> `installer parity: PASS`
>
> `python scripts/check_required_check_coverage.py` -> `Required-check coverage: OK -- 10 declared context(s)`
>
> `python scripts/check_version_sync.py` -> canonical `4.1.2`
>
> `python scripts/check_model_prompting_freshness.py --advisory`
>
> `[profile-freshness] UNKNOWN: no live roster supplied, so drift cannot be determined.` Recorded roster (4, last verified 2026-07-27): `claude-fable-5`, `claude-haiku-4-5-20251001`, `claude-opus-5`, `claude-sonnet-5`. This is v4.1.0 DF-1, not absorbed.
>
> `python -m pytest --collect-only -q tests` -> `3534 tests collected in 8.42s`
>
> `python -m pytest -q tests` (CI timeout 4500s) reached about 16 percent after eight minutes and was stopped (QG-1). Remote `pytest tests` on the integration pull request is the remaining full-suite proof.

`.gitignore` already ignores `.coverage`; 0 patterns added.

## 9. Publication and integration

Resolved branching model (from `AGENTS.md` Branching and Release Workflow): **develop + main**. Protected release branch: `main`. Integration target: `develop`. Feature base: `develop`. Current branch: `feat/v4.2.1-guide-visual-education`. Remote: `origin`.

Required checks expected on a pull request to `develop`: `validate`, `shellcheck`, `ci-required`, `colocation`, `verify`. The `tests` and `tests-windows` jobs run inside `ci.yml` and feed `ci-required`; they are not separate declared required contexts.

This section is incomplete until explicit approval to push and open the integration pull request. Silence is not approval. No tag, no `/update release`, and no merge will run from the driver without that gate. `/update release` after a green merge cuts **v4.2.1**. Do not create a v4.2.0 GitHub Release of the pre-polish guide.
