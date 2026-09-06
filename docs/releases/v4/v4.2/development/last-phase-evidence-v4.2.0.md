# Last-Phase Evidence - v4.2.0 Interactive Guide Redesign

**Date**: 2026-08-29
**Branch**: `feat/v4.2.0-interactive-guide-redesign`
**Phase starting commit**: `3778d646` (Phase 6)
**Comparison base**: `origin/develop` (`337f6141`)
**Plan**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md`

## 1. Architecture refactor

Commands:

> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root docs`
>
> `InventoryExit=0`
>
> `python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py refgraph --root docs`
>
> `RefgraphExit=0`

`project-refactor` has no bundled detector scripts. Propose-only classification of files this plan added or edited, from `git diff --stat origin/develop...HEAD` plus a markup scan of the canonical guide:

- Stay: `guides/website/nexus-hub-guide.html`; `guides/website/README.md`; `guides/website/example/training-scenes.json`; `tests/guides/test_nexus_hub_guide.py`; the v4.2 plan, content-map, baseline and per-phase evidence folders, known-gaps, docs-cleanup report, session histories, and this evidence file under `docs/releases/v4/v4.2/`.
- Prune applied: unused leftover `.nht` / `.ts-` slide-deck CSS (no matching markup after Phase 5). Removed in this phase. `class="ts-slide"` and `.nht` selectors are gone from the file.
- Move / Archive: none proposed. Phase evidence folders stay under the active minor until `/update release` retention.
- Empty directories introduced by this plan: none.
- Duplicate content: maintainer JSON and the inline `#nh-training-scenes` block are intentional copies; tests assert they parse equal.
- No top-level installer-copied `scripts/*.py` was added. No `.github/workflows/` edit.

No confirmation gate for a file move was required. The CSS prune is in-scope dead-rule removal, not a layout move.

## 2. Known-gaps reconciliation

Glob of `docs/**/known-gaps.md` found 31 unique files (canonical `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` plus archive copies).

File-level Status `in-progress` in this pass:

- `docs/releases/v4/v4.2/known-gaps.md` (this plan)
- `docs/releases/v4/v4.1/known-gaps.md` (prior minor; open DF/WN/QG items remain on that ledger)

`docs/releases/v4/v4.0/known-gaps.md` is finalized. `docs/releases/v3/v3.20/known-gaps.md` and `docs/releases/v3/v3.21/known-gaps.md` are finalized. Remaining v3 and archive ledgers are historical or complete; none was rewritten. No `## v3.20.0` section was appended to v3.16 or v3.20.

This plan produced:

- DF-1: no rendered browser baseline or last-phase Lighthouse / workshop run (no browser tools, no five workshop participants). Bounded non-pass for T032.
- QG-1: unbounded local `python -m pytest -q tests` (3526 tests; CI budget 4500s) did not finish in this session. Focused guide tests and `python scripts/ci/run.py --profile fast` passed.

Not absorbed:

- v4.1.0 DF-1 / WN-1 / QG-1
- v4.1.1 DF-1
- v4.1.2 WN-1 / QG-1
- v4.0 DF-1 (report-artifact upload), declined again in the pipeline comparison below

## 3. Living docs architecture

Scan:

> `docs/handbooks/` authored files = 1 (`README.md`); `docs/handbooks/html/.gitkeep` and `docs/handbooks/markdown/.gitkeep` only; catalog atlas/companion HTML = 0
>
> No `docs/testing/` or `docs/validation/` path exists.

The living handbook root remains a scaffold. Release-bound plan, content-map, histories, known-gaps, cleanup report, hallmark re-audit, and this evidence file remain under `docs/releases/v4/v4.2/`. `docs/decisions/` was not used for this UX redesign; the plan is the attribution record. `docs/DEVLOG.md` already has a v4.2.0 index row. `docs/todos.md` tracks this plan as the active dashboard. `docs/README.md` now names `docs/releases/v4/v4.2/` as the active 4.x minor. Root `README.md` Interactive Guide blurb matches Home / Foundations / workbench.

## 4. Git-tree hygiene

Command:

> `python scripts/check_release_preconditions.py --branches --repo-settings`

Quoted result:

> Branch hygiene (merged into origin/develop)
>   9 merged branch(es) are cleanup candidates:
>     - origin/backmerge/v4.0.0-release
>     - origin/backmerge/v4.1.0-release
>     - origin/backmerge/v4.1.1-release
>     - origin/backmerge/v4.1.2-release
>     - origin/feat/v4.1.0-release
>     - origin/feat/v4.1.1-adoption-openworker-security-refinement
>     - origin/feat/v4.1.1-release
>     - origin/feat/v4.1.2-ponytail-planning
>     - origin/feat/v4.1.2-release
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

Provider detected: GitHub Actions (`.github/workflows/*.yml`). `git diff --name-only origin/develop...HEAD -- .github catalog/mcp-configs scripts/installer.sh scripts/installer.ps1 catalog/hooks/settings.json` is empty. No pipeline file change is proposed. Silence is not approval; none is requested.

This plan added `tests/guides/test_nexus_hub_guide.py`, which the existing `pytest tests` job already covers. No second required workflow. No workflow-level `paths:` on `ci.yml`. No new top-level `scripts/*.py`. Two installers: parity checker PASS (hard gate in this pass).

Existing-pipeline comparison (canonical fields from `catalog/skills/infrastructure/cicd-architect/references/repository-native-profiles.md`):

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

Plan Goal restated: redesign the Nexus-Hub interactive guide into a concise, distinctive, portfolio-aligned learning experience that lets software engineers understand the model-versus-harness distinction, install Nexus-Hub immediately, and follow a realistic command-to-result workflow inside an interactive IDE simulation of the post-v4.1.2 product.

Goals First definition of done, inspected independently of phase checkboxes:

| Observable | Artifact | Verdict |
|---|---|---|
| Visitor can state model vs harness | Foundations copy "Model = the brain"; harness as experience; user-initiated range comparison with both states in markup | PASS (comprehension study is DF-1) |
| Install from Home without Installation nav | `#nhg-install`, OS tabs, canonical curl/irm constants; `page-setup` absent; nav has no Installation | PASS |
| Eight-scene workbench with input, tools, artifact, gate | `#nhWorkbench`, `training-scenes.json`, eight ids including `presentify`, `applyState` via `textContent` | PASS |
| Every catalog command is Training, Reference, or declined | 21 `catalog/commands/*.md` files; product-currency test | PASS |
| Light/dark, `portfolio-theme` allowlist, constellation dark-only, reduced motion | theme tests; constellation CSS/JS; `prefers-reduced-motion` | PASS (rendered proof DF-1) |
| Canonical copy path; sibling repo not required | `guides/website/README.md`; env-gated skip test | PASS |
| No cinematic engine / no CDN / one HTML file | no `scroll-scrub-engine`; no `ts-slide`; `test_no_runtime_cdn` | PASS |
| No hardcoded catalog counts on Home | `test_onboarding_has_no_hardcoded_catalog_counts` | PASS |

Gaps that remain visible: DF-1 (browser, Lighthouse Accessibility, workshop 4-of-5) and QG-1 (local full `pytest tests` not finished here). Integration, merge, and release are not proven in this file until T034 completes.

Verdict: PASS for the local guide contract; human/browser evidence and remote CI are recorded gaps, not silent passes.

## 7. Human/manual testing suggestions

Emitted. Not run in this session (no browser automation, no workshop cohort).

1. Workshop: at least 4 of 5 participants explain model versus harness and name the next command after the workbench. Bounded non-pass is accepted if five people are unavailable.
2. Lighthouse Accessibility >=90 in light and dark.
3. Viewports 1440x900, 1024x768, 390x844, 1920x1080 (light and dark).
4. `prefers-reduced-motion`: slider and constellation stay static.
5. Keyboard-only: Home, Foundations, Training, one workflow page, Reference.
6. `file://` boot (untrusted-origin warning visible) and https theme-sharing if the portfolio origin is available.
7. Record Performance, SEO, and Best Practices as advisory only.

Quoted result: not run. Recorded as DF-1. Do not invent a walkthrough.

Hallmark re-audit from markup: `docs/releases/v4/v4.2/development/guide-redesign-phase-7-hallmark.md`. No open high-severity markup finding from the Phase 1 baseline table. Contrast and Lighthouse remain DF-1.

## 8. Full-suite testing and stabilization

Quoted local evidence:

> `python -m pytest -q tests/guides/test_nexus_hub_guide.py` -> `30 passed, 1 skipped in 0.78s` (skipped: `NEXUS_HUB_PORTFOLIO_ROOT` unset)
>
> `python scripts/ci/run.py --profile fast` -> `PASS: 12 passed, 0 failed, 0 skipped, 0 advisory in 13.5s`
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
> `python -m pytest -q tests` (3526 collected; CI timeout 4500s) did not complete in this session (QG-1). Remote `pytest tests` on the integration pull request is the remaining full-suite proof.

`.gitignore` already ignores `.coverage`; 0 patterns added.

## 9. Publication and integration

Resolved branching model (from `AGENTS.md` Branching and Release Workflow): **develop + main**. Protected release branch: `main`. Integration target: `develop`. Feature base: `develop`. Current branch: `feat/v4.2.0-interactive-guide-redesign`. Remote: `origin`.

Required checks expected on a pull request to `develop`: `validate`, `shellcheck`, `ci-required`, `colocation`, `verify`.

This section is incomplete until explicit approval to push and open the integration pull request. Silence is not approval. No tag, no `/update release`, and no merge will run from the driver without that gate.
