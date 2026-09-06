# Last-Phase Evidence - v4.4.0 Guide Depth and Training Rebuild

**Date**: 2026-08-31
**Branch**: `feat/v4.4.0-guide-depth-and-training-rebuild`
**Phase 7 base revision**: `5ddf83c34f1a6ea4e6029fe6b01942be5fb1cf53`
**Publication state**: PR #150 is open against `develop`. The approved branch publication and pull-request creation are complete; merge, tag, release, back-merge, and branch deletion are not claimed by this record.

## Architecture refactor

The final architecture pass used `project-refactor` and `docs-layout-refactor` in audit-only mode because the scan found no approved move or deletion. The detailed classification and retention table is in [`docs-cleanup-report.md`](../docs-cleanup-report.md).

```text
tracked files: 3,708
empty tracked directories: 0
duplicate content: 8 intentional sets across 30 files
obsolete-name candidates: 5 active compatibility surfaces
v4.4 release tree at Phase 7 start: 84 committed files, 24,001,901 bytes, 0 duplicate sets; untracked future-release work excluded
documentation reference graph: 108 referenced paths, 452 inbound references
lifespan contradictions: 263 historical findings, 0 in v4.2, v4.3, or v4.4
```

The intentional duplicate sets are empty package markers, platform base templates, shared extension sources or configuration, paired visual fixtures, icons, and licenses. The obsolete-name candidates are the cross-platform `old-version-docs-guard` pair, the active `deprecated-api-updater` skill and agent, and the explicit legacy deprecation notice. None is abandoned.

The render evidence contains 72 PNG files totaling 23,789,263 bytes: 8 each for Phases 1 through 5 and 32 for Phase 6. The v4.2.3 precedent allowed deletion only after an explicit retention decision; no destructive approval was given in this run, so all 72 files remain at their cited paths.

**Disposition**: PASS. The living guide remains at `guides/website/nexus-hub-guide.html`; version-bound plans, histories, measurements, and renders remain under `docs/releases/v4/v4.4/`; no reference repair or architecture mutation is required.

## Known-gaps reconciliation

The committed documentation tree contains 33 known-gap ledgers. A status and open-heading audit found 12 ledgers that remain in progress or retain open items. Concurrent user-owned edits to the v4.1, v4.2, and v4.3 ledgers were excluded from this branch's Phase 7 staging boundary, so the audit used their committed `HEAD` versions and did not overwrite them.

| Ledger | Open items observed at committed `HEAD` | Disposition |
|---|---:|---|
| v3.11 | 3 | Retain with the owning historical ledger. |
| v3.12 | 6 | Retain with the owning historical ledger. |
| v3.13 | 10 | Retain with the owning historical ledger. |
| v3.14 | 21 | Retain with the owning historical ledger. |
| v3.19 | 3 | Retain with the owning historical ledger. |
| v3.20 | 11 | Retain with the owning historical ledger. |
| v3.21 | 1 | Retain with the owning historical ledger. |
| v4.0 | 16 | Retain with the owning historical ledger. |
| v4.1 | 4 | Retain with the owning historical ledger; concurrent worktree edits were not inspected or changed. |
| v4.2 | 6 | Retain with the owning historical ledger; concurrent worktree edits were not inspected or changed. v4.4 records the independently proved MT-1 closure. |
| v4.3 | 8 | Retain with the owning historical ledger; concurrent worktree edits were not inspected or changed. The live repository description now agrees with README, but no old ledger was silently rewritten. |
| v4.4 | 1 | DF-1 remains open with owner and next step; QG-1, MT-1, BG-1 through BG-5, and QG-2 are resolved with evidence. |

The v4.4 summary is now 1 deferred item open and 8 items resolved. MT-1 closed after the approved `guide-render` CI job was wired into the required-check aggregate, 67 workflow contracts passed, and the exact job targets passed locally with fail-closed rendering; remote clean-runner execution remains pending publication. The Tier 3 pass also reproduced and closed invalid numeric Training navigation, presentation overlap, presentation focus leakage, route-transition isolation leakage, the missing in-dialog exit control, and missing harness-claim containment coverage.

**Disposition**: PASS. No prior ledger was absorbed, erased, or modified around concurrent work; the remaining v4.4 item is explicitly deferred rather than a hidden release regression.

## Living docs architecture

```text
python scripts/validate_decision_records.py
OK: 29 decision record(s) validated.

python -m pytest -q tests/skills/test_living_docs_architecture.py tests/validators/test_validate_decision_records.py
30 passed
```

`docs/README.md`, `docs/DEVLOG.md`, and `docs/todos.md` exist. The active v4.4 release records use the canonical release tree. `docs/handbooks/` contains no authored Markdown source or generated handbook HTML beyond its marker; the repository documents this as a catalog product with no product-atlas source, so the handbook generation and atlas checks are a truthful no-op rather than invented content.

The validator's count includes three pre-existing decision records whose names correspond to Phase 6 policy, process, and tooling changes:

- `docs/decisions/implemented/policy/2026-08-31-seed-high-claude-effort-for-new-installs.md`
- `docs/decisions/implemented/process/2026-08-31-canonicalize-implement-full-driver-token.md`
- `docs/decisions/implemented/tooling/2026-08-31-require-explicit-rendered-state-in-the-visual-gate.md`

The user explicitly authorized Phase 7 to inspect and include exactly those three files. Review confirmed that the policy and process records fully cover the high-effort seed and canonical `full` token decisions. The tooling record already covered explicit rendered-state activation and painted-fragment geometry; Phase 7 extended it with the approved dedicated relevant-change `guide-render` job, `ci-required` aggregation, browser-cost consequence, and rejected broad-job, local-only, and unaggregated alternatives. Fresh validation reports 29 records OK and the living-doc architecture slice passes all 30 tests.

The pre-evidence staged candidate tree `a166f4030016c4ce5feb607d3b5e7f9997a29fe0`, used for the isolated full-profile run, contains all three authorized records and excludes the untracked v4.4.1 plan. In the isolated candidate worktree, `git diff --cached --check` was clean, all 29 decision records validated, the 30 living-doc tests passed, v4.4 docs conventions passed, and the personal-path scan passed. The later staged-tree difference is limited to the plan, dashboard, and two Phase 7 evidence records that record those terminal results; their focused post-evidence gates also pass.

**Disposition**: PASS. T030 is complete for content, structure, authorization, candidate inclusion, and isolated candidate-scope validation.

## Git-tree hygiene

```text
python scripts/check_release_preconditions.py --branches --repo-settings
merged remote cleanup candidates: 13
open pull-request branches excluded: 11
closed-unmerged survivor: origin/backmerge/v3.20.0
delete_branch_on_merge: enabled
repository description: agrees with README
action: report only; no branch deleted
```

**Disposition**: PASS. The command was report-only as required. The closed-unmerged survivor remains untouched.

## CI/CD coverage

GitHub Actions is the detected CI provider. The user explicitly approved the smallest MT-1 correction: a scoped `guide-render` job in `.github/workflows/ci.yml`, with a Playwright-version-keyed Chromium cache, fail-closed `NEXUS_REQUIRE_RENDER=1`, and aggregation into `ci-required`.

| Canonical field | Evidence and disposition |
|---|---|
| Repository-native profiles | `python scripts/ci/run.py --help` exposes `fast`, `full`, `platform`, `report`, and `release`; profile listing resolves catalog, hygiene, interpreter, security, workflow, platform-contract, docs, version, hook, repository, extension, and installer groups. PASS. |
| Event separation and deployment boundary | Pull-request and merge-result validation remain separate from post-merge publication and release workflows. The new browser job changes validation only. PASS. |
| Runner selection | Existing platform coverage remains multi-runner; browser enforcement is isolated to Ubuntu with Python 3.11 and Chromium. PASS. |
| Always-resolving aggregate | `guide-render` is in `ci-required.needs`; its condition is fail-closed for relevant or detector-uncertain changes. `python scripts/check_required_check_coverage.py` reports 10 declared contexts across 2 protected branches, all unconditionally produced. PASS. |
| Permissions and immutable behavior | No permission expansion or deployment credential was introduced. Existing action-version policy is unchanged by this phase. PASS for the scoped change. |
| Caching | The new Chromium cache key derives from the resolved Playwright version. The older repository-wide manifest-keying gap remains owned by the v4.3 ledger. PASS with recorded historical gap. |
| Concurrency and path scoping | Existing workflow concurrency remains intact. The `changes` job determines relevance without a workflow-level `paths:` filter, so required checks continue to resolve for every pull request. PASS. |
| Artifact retention and structured reports | Existing report handling is unchanged; the previously recorded structured-report gap remains owned by v4.3. PASS with recorded historical gap. |
| Failure recovery | The browser job runs under `!cancelled() && needs.changes.outputs.relevant != 'false'`; a test, install, or browser-launch failure reaches the aggregate as failure. PASS. |
| Installer and platform parity | The repository ships multiple installers, so the `platform` profile is mandatory rather than a no-op. The corrected Windows profile passed overall: 4 commands passed across 3 groups, while the empty `shell-lint` group was expectedly skipped on Windows. PASS. |

Focused workflow proof:

```text
python -m pytest -q tests/validators/test_ci_workflow_contract.py tests/validators/test_ci_required_gate.py tests/workflows/test_ci_runs_every_repo_test.py
67 passed in 10.76s

python scripts/check_required_check_coverage.py
OK: 10 declared contexts across 2 branches; all unconditionally produced

NEXUS_REQUIRE_RENDER=1 python -m pytest -q tests/guides/ tests/verification/test_visual_defect_detector.py
Phase 7 pre-deep-pass baseline: 152 passed, 1 optional portfolio-copy skip
```

**Disposition**: PASS for the canonical CI/CD comparison, corrected platform profile, and separate T035 exact-candidate full-profile gate. Publication remains a separate lifecycle boundary.

## Tier 3 deep pass

The deep pass inventoried user-visible Home, Foundations, Training, Cheatsheets, offline shell, theme, motion, renderer, detector, and harness-default behaviors. It used independent rendered, convergence, and adversarial lenses plus direct browser probes. The adversarial delegate produced one valid P2 finding before a later safety-classifier termination; no further coverage is claimed from that delegate. The rendered and convergence reviewers continued independently, and every confirmed finding received a fix and focused rerun.

| Finding | Failing evidence | Correction | Fresh proof |
|---|---|---|---|
| BG-1: invalid numeric Training navigation | `window.NexusTraining.go(NaN)` and `.go(1.5)` assigned an invalid scene key, threw from `trainingSnapshot`, and left exported state corrupted. | Accept numeric indexes only when `Number.isInteger` and in range; otherwise retain the current step. | `tests/guides/test_training_explorer.py`: current focused suite 3 passed in 21.22 seconds. |
| BG-2: presentation regions overlapped | At 1440x900 the game occupied y=248..893 while the explorer occupied y=528..778; the terminal also overlapped the explorer. | Keep the presentation grid at natural content height inside the slide's existing vertical scroll boundary. | Rectangle separation passes at 1920x1080, 1440x900, 1024x768, and 900x900; independent recheck also passed 1366x768 and 1280x720 with zero horizontal overflow. |
| BG-3: presentation focus escaped | With fullscreen fallback active, Shift+Tab moved to the outside Present button and Escape left focus on `#nhTraining`. | Add dialog semantics, ancestor-sibling inert isolation, a Tab loop, early Escape routing, and focus restoration after the fullscreen exit event. | Fallback proof and real-fullscreen browser assertions pass; current focused suite 3 passed in 21.22 seconds. |
| BG-4: fallback presentation survived route changes | When `requestFullscreen()` rejected, changing the hash away from Training left presentation active and made the header and destination page inert. | Exit presentation whenever hash routing leaves Training and restore every recorded inert state. | A denied-fullscreen browser regression routes to Home and proves presentation state, dialog attributes, and both inert states are cleared. |
| BG-5: isolated presentation lacked an internal exit | The only presentation toggle sat outside `#nhTraining` and became inert, leaving touch, switch, and pointer-only users without a visible close control. | Add an `Exit presentation` button inside the dialog while retaining Escape and external-invoker focus restoration. | The focused browser suite activates the internal control through a pointer click and proves focus returns to `#nhtPresent`; 3 passed in 21.22 seconds. |
| QG-2: harness claim labels escaped unmeasured chips | `MATCHED SKILLS` exceeded its 128-unit chip by 7.1 rendered pixels per side; `prompt-independent` and `WRITTEN GATES` also escaped, while claim groups were absent from the node inventory. | Promote all five claims in both variants to measurable nodes, tighten only claim-title tracking, and widen the centered event-hooks chip without shrinking its text. | The Phase 3 rendered containment test passes all 6 widths in both motion modes: 6 passed in 12.56 seconds. |

The presentation correction intentionally permits vertical scrolling when the complete Training surface exceeds viewport height. This is the no-overlap fallback for v4.4.0; the broader v4.4.1 visual and arcade rebuild may optimize density without reopening the v4.4.0 containment contract.

Fresh independent rendered proof covered 32 route, theme, and viewport cases with zero detector findings and zero allowlisted cases. It also found one visible H1 per route, no heading-rank skips, unnamed focusables, positive tabindex, or focusables inside `aria-hidden`, and passing reduced-motion and measured-contrast contracts in both themes. After the PR guide-render portability correction, the current guide SHA256 is `C8E34A098150123D47B7799719551351BC0B8827315FA4F299B1C012A7FE52E0`.

**Disposition**: PASS. The rendered, accessibility, color, runtime, geometry, hallmark, and convergence reviewers report no remaining release-blocking finding. Real screen-reader testing, Firefox/WebKit, explicit 200 percent zoom and text-spacing overrides, Lighthouse, retained post-fix screenshots, and optional portfolio synchronization remain human or environment-specific coverage rather than claimed automation.

## Goal-vs-codebase review

The plan Goal is to leave the project organized, reconcile known gaps and living documentation, align CI with the canonical contract, independently prove that the guide rebuild landed, and then publish and integrate the branch. The plan has a valid Phase 7 Goal but no separately titled `Goals First / Definition of Done` section; this review therefore uses the authoritative Goal plus the explicit phase goals and stability gates and records the structural omission rather than inventing criteria.

| Goal surface | Artifact and proof | Status |
|---|---|---|
| Home identity, platform compatibility, installation, comparison, and command loop | `guides/website/nexus-hub-guide.html`, Home contracts, offline route sweep, and retained Phase 1/6 renders. | Satisfied locally. |
| Foundations model, tokens, prompts, context, agent platform, chatbot comparison, harness, and durable workflow teaching | Guide Foundations sections, five responsive Phase 3 diagrams, claim-containment matrix, and retained Phase 2/3/6 renders. | Satisfied locally. |
| Playable seeded-bug Training and cumulative eight-command project | Guide game/runtime, `training-scenes.json`, Training explorer and game browser suites, keyboard/touch contracts, and retained Phase 4/5/6 renders. | Satisfied locally after Tier 3 fixes. |
| Cheatsheets and shell behavior | Guide Cheatsheets contracts, hash routing, theme, reduced-motion, offline, and copy interactions in the guide sweep. | Satisfied locally. |
| v4.3 verification-discipline prerequisite | Distributed responsive rule, registered Bash/PowerShell hook pair, three skill registries, and named visual-gate language passed a 440-test prerequisite slice; the testing-module selector resolves `functional-verification`. | Satisfied locally. |
| Organized release records and reconciled gaps | Canonical v4.4 tree, cleanup report, known-gap ledger, this evidence record, progress dashboard, and three owner-authorized decision records. | Satisfied in the isolated staged candidate; 29 records, 30 living-doc tests, docs conventions, personal-path scan, and cached diff check pass. |
| Publish and integrate | PR #150 is open; the approved branch publication and CodeQL correction are published, while the guide-render portability correction remains local. | PARTIAL: publish the correction, obtain terminal-green replacement checks, then request explicit merge approval. |

The independent convergence review checked every prior implementation task and every named Goal clause against the current bytes. It reports 27 of 27 tasks satisfied, 9 of 9 Goal clauses satisfied, 0 partial, 0 missing, 0 contradictory, and no current code-vs-plan blocker. The guide is 491,812 bytes against the 500,000-byte gate. Platform-default agreement remains 13 of 13 surfaces, and the focused defaults, driver, lifecycle, and installer slice passed 96 tests with 10 explicit environment skips.

**Disposition**: PASS for current v4.4.0 code versus T001 through T027, the written Goal, the v4.3 prerequisite, the decision-record boundary, and the final local profiles. Publication remains the separate lifecycle gate.

## Human/manual testing suggestions

Automation cannot establish subjective teaching clarity, physical touch feel, vendor-specific browser behavior, or scratch-install usability. Before release acceptance, a human should:

1. Play the seeded game on a real touch device and confirm the controls are responsive without accidental page gestures.
2. Ask a reader who has not seen the implementation whether the wrap-boundary miss is visibly a bug rather than bad aim.
3. Ask a non-technical reader to explain the Foundations model, token, prompt, context, agent-platform, and harness distinctions in their own words.
4. Run Lighthouse Accessibility in light and dark themes and inspect any manual-only focus, landmark, name, or contrast warning.
5. Check Home, Foundations, Training, and Cheatsheets in current Chromium, Firefox, and Safari or WebKit at desktop and compact widths.
6. Exercise true fullscreen Training presentation, keyboard Tab and Shift+Tab cycling, Escape exit, and focus restoration on a physical display.
7. Install the release into a scratch project through each supported installer family and confirm the new HTML rule, functional-verification skill, hook pair, Claude effort default, and canonical `/implement full` behavior arrive as documented.

These are suggestions, not fabricated execution evidence. Publication may proceed only under the release process's actual acceptance decision.

## Full-suite testing and stabilization

```text
NEXUS_REQUIRE_RENDER=1 python -m pytest -q -p no:cacheprovider tests/guides/ tests/verification/test_visual_defect_detector.py
154 passed, 1 skipped in 97.72s
```

The skip is the optional portfolio-copy contract because `NEXUS_HUB_PORTFOLIO_ROOT` is unset. The first `platform` profile attempt ran 1,065.9 seconds and reported 3 groups passed and 1 failed because Windows resolved `C:\Windows\System32\bash.exe`, which could not execute a local probe, even though Git Bash was installed. That result is retained as troubleshooting evidence rather than completion evidence.

```text
PATH prefixed with C:\Program Files\Git\bin
python scripts/check_interpreter_resolution.py --gate
[interpreters] OK bash -> C:\Program Files\Git\bin\bash.EXE
[interpreters] every hook interpreter can execute a script.
```

With `C:\Program Files\Git\bin` prepended to PATH, the corrected repository-native `platform` profile passed overall in 1,100.4 seconds: 4 commands passed across 3 groups, and the empty `shell-lint` group was expectedly skipped on Windows.

The first repository-native `full` profile attempt ran in the primary dirty worktree for 4,036.7 seconds. It reported 42 commands passed and 1 failed. The only failure was `validate_no_personal_paths`, which found four personal-path forms in the untracked future-release file `docs/releases/v4/v4.4/plans/v4.4.1-guide-visual-and-arcade-rebuild.md`. That file is outside the v4.4.0 candidate and remains untouched.

The exact staged tree was then materialized in an isolated detached worktree with the v4.4.1 plan absent. Its preflight passed cached diff, decision-record, living-doc, docs-convention, and personal-path gates. The authoritative rerun was terminal green:

```text
PATH prefixed with C:\Program Files\Git\bin
python scripts/ci/run.py --profile full --reports-dir reports --quiet
PASS: 43 passed, 0 failed, 0 skipped, 0 advisory in 3685.4s
```

The structured report records all 11 groups as `pass`: catalog-parse, hygiene, interpreters, catalog, security, workflows, platform-contracts, docs, version, tests, and extension-tests.

**Disposition**: PASS. T035 is complete for the exact v4.4.0 candidate. The first contaminated-worktree attempt remains retained troubleshooting evidence rather than being rewritten as success.

### Pre-PR independent cross-check

After the user approved the first push, the Phase 7 commit was published at `560c8d4843dbabdad4b9b0c2d264a357446a9dc7`. An independent diff cross-check then found two non-runtime defects before the integration pull request opened: `guides/website/README.md` still described Playwright CI as optional despite the new required `guide-render` job, and `test_training_position_is_plain_language` ended one source assertion with `or True`.

The README now describes the fail-closed `guide-render` and `ci-required` contract. A new static regression binds that documentation to the required job, and the Training test now inspects the actual `els.where.textContent` assignment while preserving the separate legacy URL-grammar assertion. The focused correction slice passed 53 tests in 0.68 seconds. The complete fail-closed guide and detector aggregate then passed on the exact corrected pre-commit tree:

```text
NEXUS_REQUIRE_RENDER=1 python -m pytest -q -p no:cacheprovider tests/guides/ tests/verification/test_visual_defect_detector.py
155 passed, 1 skipped in 93.86s
```

The skip remains the optional portfolio-copy contract because `NEXUS_HUB_PORTFOLIO_ROOT` is unset. These fixes are recorded in a follow-up commit because the original Phase 7 commit was already published; its history is not rewritten.

## Publication and integration

Resolved branching model: feature branches start from `develop`, integration pull requests target `develop`, release promotion later moves through `main`, and release completion back-merges as required by the project flow. The configured remote is `origin`; the publication branch is `feat/v4.4.0-guide-depth-and-training-rebuild`; the integration target is `develop`.

Expected required checks are `validate`, `shellcheck`, `ci-required`, `colocation`, and `verify`.

The scoped Phase 7 local commit closed the local implementation boundary. At that checkpoint no remote action was claimed. The user explicitly approved the first push and integration pull-request creation on 2026-09-01. The feature branch was published at `560c8d4843dbabdad4b9b0c2d264a357446a9dc7`, the independent pre-PR corrections were published at `d23611a36b3056c6f09ea49f005acc1d2bdb8188`, and integration PR #150 opened against `develop`.

The initial remote run made `validate`, `shellcheck`, `colocation`, and `verify` green, but GitHub Advanced Security check-run `99885507186` failed on the `d23611a3` PR head with 9 CodeQL annotations, including 2 high-severity `js/xss-through-dom` findings. The findings traced `.typed` DOM content serialized into `data-html` and later reparsed through `innerHTML` at the former guide lines 2911 and 2950. No `.term[data-anim]` or `.term-cmd .typed` instance exists in the current guide, so the subsystem was unreachable, but the latent DOM-to-HTML sink correctly blocked integration.

The local correction deletes that orphaned typewriter subsystem rather than preserving an unused parser, adds a structural regression that first failed on the original source-to-sink pattern, and applies behavior-preserving cleanup for the other 7 CodeQL annotations. An equivalent-sink sweep leaves only 5 `innerHTML` writes built from fixed local page metadata or fixed SVG/label constants, with no DOM- or attribute-derived input. Verification on the corrected tree is terminal green:

```text
python -m pytest -q -p no:cacheprovider tests/guides/test_nexus_hub_guide.py tests/guides/test_asteroids_game.py tests/guides/test_training_explorer.py
99 passed, 1 skipped in 29.49s

NEXUS_REQUIRE_RENDER=1 python -m pytest -q -p no:cacheprovider tests/guides/ tests/verification/test_visual_defect_detector.py
156 passed, 1 skipped in 93.90s
```

The skip in each result is the optional portfolio-copy contract. Commit `7e54a6eb30da60d0658b1975275a53211d3de489` published the correction, and the replacement CodeQL composite plus its JavaScript/TypeScript and Python analyses reached terminal green. The required `validate`, `shellcheck`, `colocation`, and `verify` checks also passed on that head.

### PR guide-render portability checkpoint

GitHub Actions run `33518225492`, job `99890645036`, then executed the fail-closed browser suite on the PR merge result and reported 13 failed, 143 passed, and 1 skipped. The failures were not accepted as runner noise. They reproduced three cross-platform font-metric defects:

- At 320 px, Training's `Foundations` and `Cheatsheets` page-navigation controls used `flex: 0 0 auto`, so Linux fallback metrics made the 283 px row overflow its 272 px content box in every Training scene and both themes.
- Phase 2's 13-unit SVG text scaled to an 11 px glyph box at narrow and breakpoint widths, while several Linux fallback labels exceeded their original nodes.
- Phase 3's later generic `.fxt` rules overrode the intended role/detail hierarchy, so Linux fallback glyphs escaped agent-loop lanes, comparison headers, harness claims, and the written-gate safe area. The first assertion at each width masked the later labels until a forced DejaVu probe enumerated them.

The correction lets page-navigation controls shrink, adds a two-theme 320 px browser regression that failed at 283 versus 272 before the CSS change, restores the Phase 2 and Phase 3 font hierarchy, removes excess claim tracking, and widens or recenters only the affected SVG nodes and labels. Text remains uncompressed; no `textLength` workaround is retained. An independent correction-diff review then found that the widened output node covered the old arrowhead tip; the connector and arrowhead were aligned to the new boundary, and the Phase 2 matrix passed all 6 widths on both Windows and Ubuntu.

Fresh local proof on the corrected tree:

```text
Windows focused navigation plus Phase 2 and Phase 3 matrices
14 passed in 24.29s

Ubuntu Playwright 1.62.0 focused navigation plus Phase 2 and Phase 3 matrices
14 passed in 21.14s

Ubuntu original page, theme, and Training-scene overflow matrix
1 passed in 6.04s

Windows fail-closed guide and detector aggregate
158 passed, 1 skipped in 93.06s

Ubuntu fail-closed guide and detector aggregate
158 passed, 1 skipped in 104.90s
```

The skip remains the optional portfolio-copy contract because `NEXUS_HUB_PORTFOLIO_ROOT` is unset. Ubuntu used the official `mcr.microsoft.com/playwright/python:v1.62.0-noble` image with Playwright 1.62.0 and a read-only workspace mount.

**Disposition**: First push, PR creation, and remote CodeQL remediation are COMPLETE. The guide-render portability correction is PASS on Windows and Ubuntu but remains PENDING remote replacement execution. Integration stays NO-GO until the correction is committed and published, every replacement required check including `guide-render` and `ci-required` is terminal green, and the user explicitly approves merge. Release and back-merge remain later approval and verification gates.

### Terminal integration result (T036)

The `guide-render` portability correction was published as `78255a3e`, and every required check reached a terminal state on the replacement run before merge. Full check roster on pull request [#150](https://github.com/bendourthe/Nexus-Hub/pull/150), all 24 contexts terminal with zero failures:

```text
Analyze (javascript-typescript)  pass   1m28s
Analyze (python)                 pass   2m14s
CodeQL                           pass   4s
bootstrap (macos-latest)         pass   2m37s
bootstrap (ubuntu-latest)        pass   4m9s
bootstrap-windows                pass   3m55s
build-and-test                   pass   50s
changes                          pass   8s
ci-required                      pass   2s
colocation                       pass   9s
detect                           pass   8s
guide-render                     pass   1m51s
install-smoke (macos-latest)     pass   16s
install-smoke (ubuntu-latest)    pass   8s
install-smoke (windows-latest)   pass   1m3s
installer-smoke (macos-latest)   pass   17s
installer-smoke (ubuntu-latest)  pass   12s
installer-smoke (windows-latest) pass   24s
shellcheck                       pass   18s
tests                            pass   12m6s
tests-windows                    pass   10m56s
validate                         pass   45s
verify                           pass   1m3s
render                           skipping
```

The five named required checks (`validate`, `shellcheck`, `ci-required`, `colocation`, `verify`) are all green, and the approved `guide-render` job executed on clean remote runners, closing the PENDING remote-execution condition recorded above for MT-1. The single `skipping` context is `render`, whose path filter did not match this diff; it is not a required check.

Merged with the user's explicit approval as a merge commit:

```text
pull request #150  state MERGED  mergedAt 2026-09-01T16:12:44Z
merge commit 46518d015534f2d0a21654d12db98e0f54705a4d
develop HEAD 46518d01 Merge pull request #150 from bendourthe/feat/v4.4.0-guide-depth-and-training-rebuild
```

Post-merge workflow run [`33530447033`](https://github.com/bendourthe/Nexus-Hub/actions/runs/33530447033) on `46518d01` performed only its intended work and did not rerun the complete suite:

```text
smoke        success  16:12:51-16:13:07
provenance   success  16:12:51-16:13:00
```

Two jobs totalling 25 seconds of runner time, versus the 12-minute `tests` job on the pull request, confirms the post-merge event is scoped to smoke and provenance only.

**Disposition**: PASS. Publication and integration are COMPLETE. The single authorized push, the green integration pull request, the approved merge, and the scoped post-merge result are all recorded. Phase 7 is closed and the release flow may proceed to `/update release`, which owns the version bump, changelog, tag, push, and GitHub Release behind its own confirmation gates.

<!-- BEGIN v4.4.1-guide-visual-and-arcade-rebuild -->

# Last-Phase Evidence - v4.4.1 Guide Visual and Arcade Rebuild

**Version**: v4.4.1
**Slug**: `guide-visual-and-arcade-rebuild`
**Branch**: `feat/v4.4.1-guide-visual-and-arcade-rebuild`
**Phase 7 verification base SHA**: `12c40a987619407d818e4252c5c09731e8f4a940`
**Date**: 2026-09-01
**Publication state**: GO recorded 2026-09-02 after the operator's explicit decision (see `## Publication and integration preflight`). Push, pull request, required-check results, and merge are PR/CI artifacts appended by the release-owned handoff, not claimed by this block.

## Architecture refactor

Read-only scan; no move or deletion was proposed, so `project-refactor` and `docs-layout-refactor` ran in audit-only mode and no reference repair was required.

```text
tracked files: 3,850
empty tracked directories: 0
v4.4 release tree: 219 tracked files
personal-path scan (validate_no_personal_paths.py): exit 0, 0 findings
docs retention: nothing due for archival (current v4.4, threshold 2 minors)
```

Unrelated candidates recorded WITHOUT mutation, per this plan's narrowed mutation authority: 16 merged remote branches remain as cleanup candidates (see `## Git-tree hygiene`), and a stale `tests/guides/__pycache__/test_asteroids_game.cpython-312-pytest-7.4.4.pyc` artifact remains from the deleted v4.4.0 suite. The `.pyc` is untracked build output, not a repository file.

**Disposition**: PASS.

## Known-gaps reconciliation

Both canonical (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md`) and legacy (`docs/archives/...`) layouts were globbed from `git ls-files`.

```text
known-gaps ledgers found: 34
genuinely open (in-progress status OR non-empty Open Items): 19
this plan's ledger: docs/releases/v4/v4.4/known-gaps.md
```

Only `docs/releases/v4/v4.4/known-gaps.md` was edited, because this plan's mutation authority is limited to v4.4.1-traceable work. The other 18 open ledgers are recorded here without modification; they belong to earlier, separately owned release cycles.

v4.4.1 dispositions written this cycle: `BG-1` through `BG-11` are closed with their fixes described, and one item is deferred with an owner and next step (the Outline panel reflowing the presentation slide while open, which restores exactly on close and is covered by no acceptance criterion).

**Disposition**: PASS for this version; 18 foreign ledgers recorded, not touched.

## Living docs architecture

```text
docs/handbooks/          README.md, html/.gitkeep, markdown/.gitkeep
docs/decisions/          README.md, implemented/, proposed/, rejected/
docs/README.md           present
docs/DEVLOG.md           present
docs/todos.md            present
docs/testing/            absent (correct - never invented)
docs/validation/         absent (correct - never invented)
```

The empty `handbooks/markdown/` and `handbooks/html/` trees are a DELIBERATE documented state, not drift. `docs/handbooks/README.md` records that this repository is the Nexus-Hub catalog rather than an application with a product walkthrough, so a non-technical atlas and per-component companion HTML are deliberately not invented here, and the regenerate-and-fail-on-stale check is a no-op while `markdown/` has no authored pages. The backing decision is `docs/decisions/implemented/architecture/2026-08-24-living-docs-handbooks-and-decisions.md`. Markdown remains the source of truth; no HTML disagreed with it, because none exists to disagree.

**Disposition**: PASS.

## Git-tree hygiene

```text
python scripts/check_release_preconditions.py --branches --repo-settings

Branch hygiene (merged into origin/develop)
  16 merged branch(es) are cleanup candidates
  (11 branch(es) with an open PR were excluded)
  1 branch(es) survive a CLOSED, unmerged PR:
    - origin/backmerge/v3.20.0
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
exit=0
```

Report only. No branch was deleted, and no repository setting was mutated; the external-settings contract forbids automatic mutation.

**Disposition**: PASS.

## CI/CD coverage

DETECT: GitHub Actions, 11 workflow files under `.github/workflows/`. Recorded as detected rather than assumed.

COMPARE, field by field against `docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md`:

| Canonical field | Verdict | Observable evidence |
|---|---|---|
| Repository-native profiles | PASS | `scripts/ci/run.py` is invoked 5x in `ci.yml`; no test logic is reimplemented in YAML |
| Event separation | PASS | `ci.yml` = pull_request + workflow_dispatch; `post-merge.yml` = push; `release.yml` = push (tag). The merge result is not revalidated on the merge commit |
| Single always-resolving aggregate | PASS | `ci-required` is guarded by `if: always()`, the contract's named permitted form |
| Allowlist verdict, fails closed | PASS | Verdict is an allowlist over `success`/`skipped`; an unfamiliar result value fails closed |
| Cost scoping is job-level | PASS | 7 job-level `if: ${{ !cancelled() && ... }}` guards in `ci.yml`; no required check sits behind a workflow-level filter |
| No required check from a path-filtered workflow | PASS | 6 workflows carry top-level `paths:`; none produces any of the 5 required contexts (their jobs are `build-and-test`, `analyze`, `test`, `test-network-blocked`, `e2e-cursor-profile`, `test-locking-matrix`). `verify` comes from `presentify-extractor.yml` and `colocation` from `doc-colocation.yml`, neither path-filtered |
| No per-leg matrix context | PASS | Declared contexts are `ci-required`, `colocation`, `shellcheck`, `validate`, `verify`; none carries a matrix-leg suffix |
| Required-check coverage guard | PASS | `check_required_check_coverage.py`: 10 declared contexts across 2 branches, every one produced unconditionally |
| Immutable action references | PASS | 52/52 third-party `uses:` pinned to a 40-character commit SHA |
| Explicit least-privilege permissions | PASS | Every one of the 11 workflows declares a top-level `permissions:` block; none inherits silently |
| Caches keyed to manifests | PASS | `extensions/*/pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml` |
| Concurrency | PASS | Declared in all 11 workflows; `release.yml` sets `cancel-in-progress: false` so an in-flight release is never cancelled |
| Artifact retention + unconditional upload | PASS | `retention-days: 7`; 6 `if: always()` steps in `ci.yml` |
| Structured reports | PASS | `--reports-dir` used; summary published to `GITHUB_STEP_SUMMARY` |
| Deployment boundaries | PASS | No deploy or environment step in `ci.yml`; publication lives in `release.yml` behind a tag |
| `MT-1` fail-closed guide browser coverage | PASS | The `guide-render` job sets `NEXUS_REQUIRE_RENDER=1`, runs `tests/guides/` plus the visual detector, and is listed in `ci-required`'s `needs` |

PROPOSE / APPROVE / APPLY: no difference was found, so nothing was proposed and NO pipeline file was edited in this phase. `MT-1` needs no new approval for v4.4.1: the `guide-render` job approved and proven in v4.4.0 runs the whole `tests/guides/` tree, so this plan's new `test_v441_phase6_workspace.py` is covered fail-closed in the integration gate without a pipeline change.

Cross-installer parity (declarative):

```text
python scripts/check_installer_parity.py   ->  installer parity: PASS
python -m pytest -q tests/installer/       ->  458 passed, 36 skipped in 337.55s
```

RECORD: one difference is recorded as a known gap rather than applied - the 16 merged remote branches are an external-settings cleanup item, not a pipeline field, and the contract forbids automatic mutation.

**Disposition**: PASS on every required field, with zero pipeline edits. The real current-host installer duty is INCOMPLETE and is recorded honestly under `## Publication and integration preflight`.

## Tier 3 deep pass

Every artifact this plan produced was exercised through its real boundary, in a real browser where the artifact's contract is a rendered or interactive one.

| Artifact | How it was exercised | Observed result |
|---|---|---|
| `guides/website/nexus-hub-guide.html` | 110-case browser matrix across 4 pages, 2 themes, 7 viewport groups, native and fallback fullscreen, reduced motion, and 200 percent zoom | 110/110 cases, 84/84 screenshots, 0 failures, 0 external requests |
| Same file, defect scan | `detect_visual_defects.py`, 4 pages x 2 themes x 6 viewports | 0 findings, except 60 documented allowlisted Gemini blur-filter entries on Home |
| Same file, byte contract | Measured against the strict 500,000-byte ceiling | 292,339 bytes; 207,661 headroom |
| Same file, offline contract | Static scan for external script/stylesheet/URL plus per-case request capture | 0 external scripts, 0 external stylesheets, 0 runtime requests. All 9 absolute URLs are inert: 6 SVG `xmlns` namespaces, 1 CC BY 4.0 license link, 3 install commands as copyable text |
| `guides/website/example/training-scenes.json` + inline `#nh-training-scenes` | Parsed and compared for equality; hostile fixture strings asserted to survive as text | Equal after parse; escaping preserved so a closing script tag in fixture content cannot terminate the carrier |
| `window.NexusShooter` engine | 29 browser tests driving the real engine: seed equality, frozen snapshots, damage modes, terminal lifecycle, key ownership | All pass |
| Phase 6 workspace contracts | 12 browser tests measuring real pairwise intersection area with each region clipped to its clipping ancestors | All pass |
| Staged platform and media assets | SHA-256 of every staged file matched against the approved provenance ledger | 9/9 staged files present in the ledger; 0 unapproved bytes |
| `tests/guides/tools/render_guide.py` | Executed through its own test suite | Passes |
| v4.4.0 sweep suite (regression) | `test_phase6_verification_sweep.py` re-run untouched | 3 passed |
| Repository catalog and policy surface | All 12 `make validate` guards; `tests/workflows/` + `tests/validators/` | Every guard exit 0; 1236 passed, 15 skipped |

Global iteration budget: 11 defects were found and fixed across the plan (`BG-1` through `BG-11`), each recorded in `known-gaps.md` with its root cause.

One P3 residual is carried, with an owner and next step in `known-gaps.md`: the Outline disclosure panel is in-flow, so in presentation mode it squeezes the game panel while open. State restores exactly on close (proven by the `BG-11` fix), no acceptance criterion covers the open state, and overlaying the panel was deliberately left out of a late unvalidated layout diff.

No P0 and no P1 finding survived.

**Disposition**: PASS with one owned P3.

## Goal-vs-codebase review

**Plan Goal restated**: deliver a self-contained Nexus-Hub guide whose Home identity and five-platform compatibility rail are polished and accurate, whose Foundations page teaches the requested AI concepts in a compact and professionally ordered visual narrative, and whose Training page remains readable in and out of fullscreen while the eight-command walkthrough operates a deterministic arcade shooter with the requested lives bug, asteroid hazard, and vertical-movement feature.

This review inspected the shipped file directly rather than reading the plan's checkboxes, because completing sub-tasks is not evidence the Goal landed.

| Definition-of-Done clause | Artifact that satisfies it | Observed |
|---|---|---|
| Home renders the exact title `Nexus Hub` | `#page-home h1` | `Nexus Hub` |
| Rail is exactly Claude, ChatGPT, Gemini, Cursor, GitHub Copilot in that order; OpenCode removed | `.platform-mark[data-mark]` | `claude`, `chatgpt`, `gemini`, `cursor`, `github-copilot`; the string `OpenCode` is absent from the file |
| Loop keeps its command sequence, command on line one and description on line two | `.loop-step` | 6 pills, each 59 px (two lines): `/describe map it`, `/review judge it`, `/plan decompose it`, `/implement build it`, `/test harden it`, `/update ship it` |
| Foundations has exactly the eight accepted sections in order, with professional titles rather than `What Is` / `What Are` | `#page-foundations .fx-scene .fx-title` | 8 scenes in the accepted order; zero titles match `What Is` or `What Are` |
| `Full screen` with a four-corner icon sits immediately left of Outline and survives fullscreen | `.nht-bar` button order | `Full screen` then `Outline`, adjacent, `svg path` icon present, inside the fullscreen root |
| Training begins idle behind `Click to start` | `[data-arcade-start]` | Present; ticks hold at zero until clicked |
| The shooter replaces Asteroids | `window.NexusShooter` / `window.NexusAsteroids` | Shooter is an object; `NexusAsteroids` is `undefined` |
| Fullscreen shows every region simultaneously with no pairwise intersection or horizontal overflow at the four desktop sizes | 110-case matrix + 12 geometry tests | 0 overlaps, 0 horizontal overflow at 1920x1080, 1440x900, 1366x768, 1280x720, plus the narrow reflow sizes |
| One self-contained offline file at or below 500,000 bytes | Filesystem + request capture | 292,339 bytes, 0 runtime requests |
| Dark, light, keyboard-only, 200 percent zoom, reduced-motion, canvas-unavailable, hostile-fixture, deterministic-replay cases have observable evidence | Browser matrix + 29 engine tests + detector | All covered by automated evidence; no completion claim rests on structural scoring alone |

**Gaps found**: two, neither a Goal miss.

1. Last-phase human comprehension testing has no participant cohort. This is a Definition-of-Done clause the plan itself anticipates could be unavailable, and it explicitly directs recording an owned known gap rather than a fabricated pass. See `## Human/manual testing suggestions`.
2. The real current-host installer execution is incomplete and produced an unintended side effect. See `## Publication and integration preflight`.

No Definition-of-Done clause is unmet by the code or docs.

**Disposition**: the Goal landed. PASS.

## Human/manual testing suggestions

Automated evidence covers rendering, geometry, determinism, accessibility wiring, and offline delivery. It cannot cover whether a newcomer actually UNDERSTANDS the material, which is this plan's primary persona goal, so that is what a human cohort is for.

Ask each participant, with no maintainer coaching, to:

1. Distinguish a prompt from context, using the Prompt Engineering and Context Engineering scenes.
2. Distinguish provider training and release from a later live request, using the Models scene.
3. State the relationship between higher effort and the work cycle, and say whether the guide promises a specific hidden iteration count. (Correct answer: it does not; the visual is an abstract work cycle, never a transcript of hidden reasoning.)
4. Distinguish chatbot output from permitted agentic action, using the Chatbot vs. Agentic Platform scene.
5. Place a platform's built-in harness relative to the Nexus-Hub portable workflow layer, using the Harnesses and Nexus-Hub Harness scenes.
6. In Training: identify the lives rule and the asteroid rule, then use `Click to start`, Escape, and `Full screen` unaided.

Environment-specific cases automated tests cannot reach: real native fullscreen on a physical multi-monitor setup, a real projector or presentation display, actual touch input on a tablet, and a real screen reader announcing the HUD lives changes.

**Participants**: 0. No representative newcomer cohort was available in this session.
**Disposition**: OPEN, recorded as an owned known gap. NOT a pass. This is recorded honestly rather than fabricated, exactly as the plan's Definition of Done requires.

## Full-suite testing and stabilization

```text
python -m pytest -q tests/workflows/ tests/validators/
1236 passed, 15 skipped in 294.99s

NEXUS_REQUIRE_RENDER=1 python -m pytest -q tests/guides/ tests/verification/test_visual_defect_detector.py
238 passed, 1 skipped in 143.83s

python -m pytest -q tests/installer/
458 passed, 36 skipped in 337.55s

make validate equivalents (12 guards, each run individually)
validate_skills.py --bundles-only            PASS (0 errors, 64 warnings)
check_agentskills_conformance.py             PASS (0 errors, 329 skills scanned)
build_framework_coverage.py --check          OK: framework coverage in sync
validate_permission_baseline.py              read-only at the side-effect level
check_installer_parity.py                    installer parity: PASS
validate_no_personal_paths.py                exit 0
validate_unicode_safety.py --strict          exit 0
scan_supply_chain_iocs.py                    exit 0
validate_workflow_security.py                exit 0
check_required_check_coverage.py             OK -- 10 contexts, all unconditional
check_doc_colocation.py                      no docs/v<N> tree; nothing to check
validate_solution_frontmatter.py             exit 0

Browser evidence matrix (110 declared cases)
cases: 110/110  screenshots: 84/84
runtime: 106s / 1200s   evidence: 7.1 MiB / 30 MiB
failures: 0

Byte guard
page bytes: 292,339 | strict ceiling 500,000 | headroom 207,661

Asset ledger
ledger SHA-256 entries: 14 | staged asset files: 9
staged files whose hash is absent from the ledger: none
```

One reconciled discrepancy, recorded because a green summary that hides an investigated failure is worse than a red one. The canonical CI profile run (`python scripts/ci/run.py --profile full --only tests,extension-tests`) reported `6 failed, 3833 passed, 56 skipped`, with all six failures in `tests/installer/test_core_settings_seeding.py` PowerShell variants. Those six were NOT a code defect: that run's `repo-tests` group spanned 16:33 to 17:30, and the interrupted installer executions described in the preflight section were concurrently writing the same platform settings files between 17:04 and 17:15. Re-running the identical tree with nothing else mutating config returned `458 passed, 36 skipped`. The affected tests seed and compare settings files, so a concurrent installer writing those files is a direct and sufficient explanation, and the isolated re-run is the proof.

**Disposition**: the local gate is GREEN.

## Publication and integration preflight

| Item | Value |
|---|---|
| Branching model | `develop` + `main`; feature branches integrate through `develop` |
| Remote | `origin` |
| Branch | `feat/v4.4.1-guide-visual-and-arcade-rebuild` |
| Local commits on the branch | 6 (one per phase, Phases 1 through 6) |
| Phase 7 commit | created after this preflight (the sole Phase 7 commit; also carries the v4.4.2 plan file at the operator's request) |
| Pull-request target | `develop` |
| Required checks | `validate`, `shellcheck`, `ci-required`, `colocation`, `verify` |
| Target-OS installer matrix | Windows (current host, INCOMPLETE), Ubuntu and macOS deferred to integration evidence |
| Approval status | GRANTED 2026-09-02: push, pull request to `develop`, and merge once every required check is green, all explicitly approved by the operator |

### Blocking finding: an unintended host side effect during the installer duty

Task 7.5 requires a real installer execution on the current host. To avoid mutating the operator's live configuration, the installer was run with `HOME` redirected to a scratch directory. That isolation was INEFFECTIVE, and the failure mode is worth recording precisely because it is not obvious: the Nexus-Hub home itself honored the override and landed in the sandbox, but the per-platform integration paths resolve through Python's `expanduser`, which reads `USERPROFILE` on Windows rather than `HOME`. Those writes therefore reached the real user profile.

The runs were also interrupted mid-execution, so the result is a PARTIAL install rather than a valid one. Uneven skill counts are the direct evidence:

```text
~/.claude   352 skills   modified 16:49
~/.codex    370 skills   modified 17:15
~/.gemini   373 skills   modified 17:05
~/.cursor   351 skills   modified 17:06
~/.qwen     350 skills   modified 17:06
~/.copilot  untouched    modified 2026-08-30
```

A complete install produces consistent counts across these surfaces, so the current state is internally inconsistent.

NOT affected: `~/.nexus-hub` was never written by these runs. It still reports `VERSION` 4.4.0 and `nexus-hub verify` returns `PASS` with 1835/1835 files matching `MANIFEST.sha256`. The repository working tree is unmodified, and no push, pull request, or remote CI run occurred.

Two installer processes were still running when this was discovered and were terminated.

The repair is one idempotent command that reinstalls from the pristine hash-verified v4.4.0 source tree:

```text
cd ~/.nexus-hub/src && bash scripts/installer.sh --yes
```

Attempting that repair automatically was refused by the host permission layer, so it was not worked around. On 2026-09-02 the operator chose to run the repair themselves and to accept the unmet real-install duty as owned known gap `HT-2`; no sandboxed installer run will be attempted again by this plan.

**GO / NO-GO: GO** (recorded 2026-09-02). Basis: no P0 or P1 finding in the shipped artifact; no Goal or Definition-of-Done miss; the only residuals are explicitly accepted P3 items with an owner and next step (`HT-1` no human cohort, `HT-2` real-install duty accepted as an owned gap by the operator on 2026-09-02, `HT-3` merged-branch cleanup, and the Outline-reflow P3). The local gate is green as quoted above.

The operator further approved, in the same decision: adding the v4.4.2 plan file to this phase's sole commit so it reaches `develop` through this pull request, and merging once every required check is green. Remote results are recorded by the release-owned handoff, never by re-pushing this branch to quote them.


### Red-check stabilization (2026-09-02)

PR #154's first run: `shellcheck`, `colocation`, `verify`, `guide-render`, every bootstrap and installer-smoke leg PASS; `validate` FAIL. Cause, from the job log: the `end-of-file-fixer` pre-commit hook rewrote the seven staged SVG assets under `docs/releases/v4/v4.4/development/guide-visual-and-arcade-rebuild/assets/` to append a trailing newline. Those files are approved-bytes-only evidence whose SHA-256 is pinned in `asset-provenance.md` and matched against the bytes embedded in the guide; appending a newline would change every hash and break that discipline, so the fixer, not the assets, was wrong.

Reproduced locally with `python -m pre_commit run end-of-file-fixer --files <assets>` (same two-file rewrite), then the approved asset bytes were restored from HEAD. Fix: a five-line `exclude: '^docs/releases/.*/assets/'` on that one hook in `.pre-commit-config.yaml`, with a comment recording why. `pre-commit run --all-files` then passes `end-of-file-fixer`. The local `mixed-line-ending --fix=lf` hook rewrote 1,983 CRLF working-copy files on this Windows checkout; `git diff --ignore-cr-at-eol` proved the only real change was the config edit, and the operator approved restoring the tree. This is a pipeline-adjacent configuration edit, not a workflow edit, and it traces to v4.4.1's own evidence assets.

The operator explicitly approved amending the sole Phase 7 commit and updating the remote with `--force-with-lease`, per Task 7.10; no second Phase 7 commit exists.

<!-- END v4.4.1-guide-visual-and-arcade-rebuild -->

<!-- BEGIN v4.4.2-guide-production-ready-rebuild -->

# Last-Phase Evidence - v4.4.2 Guide Production-Ready Rebuild

**Version**: v4.4.2
**Slug**: `guide-production-ready-rebuild`
**Branch**: `feat/v4.4.2-guide-production-ready-rebuild`
**Phase 8 verification base SHA**: `e1f676f1585071dea1486d1203dcc02d77772dc3`
**Date**: 2026-09-02
**Publication state**: GO recorded below. Push, pull request, required-check results, and merge are PR/CI artifacts appended by the release-owned handoff, not claimed by this block.

## Architecture refactor

Read-only scan; no move or deletion was proposed, so `project-refactor` and `docs-layout-refactor` ran in audit-only mode. Mutation authority for this plan is limited to v4.4.2-traceable work.

```text
tracked files: 3,994
empty tracked directories: 0
v4.4 release tree: 355 tracked files (124 of them the Phase 7 render PNGs, 12.7 MiB)
personal-path scan (validate_no_personal_paths.py): exit 0
docs retention: nothing due for archival (current v4.4, threshold 2 minors)
```

Unrelated candidates recorded without mutation: 17 merged remote branches (see `## Git-tree hygiene`), and three user-owned untracked release trees (`docs/releases/v4/v4.5/`, `v4.6/`, `v4.7/`) plus a root `image.png`, which are not this plan's files and were never staged.

**Disposition**: PASS.

## Known-gaps reconciliation

```text
known-gaps ledgers found (canonical + legacy layouts, from git ls-files): 34
genuinely open (in-progress status OR non-empty Open Items): 19
edited by this plan: docs/releases/v4/v4.4/known-gaps.md only
```

The v4.4.2 section records two closed defects (`BG-13` sequencer contrast, `BG-14` ghost contrast), the closed carried P3 (Outline reflow, now an overlay proven by test), per-phase notes for every phase, and the deviations (title-scale minimum bound, stage-height floor 0.45, `fx-stack` on four scenes, the token tuned to 2.4). `HT-1` (no human cohort) is re-issued below. `HT-2` (real current-host installer duty) stays owned by the v4.4.1 release; see `## CI/CD coverage`. The other 18 open ledgers belong to earlier cycles and are recorded, not touched.

**Disposition**: PASS for this version; 18 foreign ledgers recorded, not touched.

## Living docs architecture

```text
docs/handbooks/          README.md, html/.gitkeep, markdown/.gitkeep (deliberate: this repo is the catalog, not an app)
docs/decisions/          README.md, implemented/, proposed/, rejected/ -- validate_decision_records.py: 30 record(s) OK
docs/README.md, docs/DEVLOG.md, docs/todos.md   present
docs/testing/, docs/validation/                absent (correct - never invented)
```

One decision record was added by this plan: `docs/decisions/implemented/policy/2026-09-02-platform-mark-attribution-in-footer.md` (the plan named a `product/` class that does not exist; `policy/` was used and the trace is in the Phase 2 history). Markdown remains the source of truth; no HTML disagreed with it.

**Disposition**: PASS.

## Git-tree hygiene

```text
python scripts/check_release_preconditions.py --branches --repo-settings
  17 merged branch(es) are cleanup candidates (11 with an open PR excluded)
  1 branch(es) survive a CLOSED, unmerged PR: origin/backmerge/v3.20.0
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
```

Report only; the external-settings contract forbids automatic mutation. The count rose from 16 to 17 because `feat/v4.4.1-guide-visual-and-arcade-rebuild` merged during this cycle.

**Disposition**: PASS.

## CI/CD coverage

DETECT: GitHub Actions, 11 workflow files. COMPARE against `docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md`, field by field, with the same detector script as v4.4.1:

| Canonical field | Verdict | Observable evidence |
|---|---|---|
| Repository-native profiles | PASS | `scripts/ci/run.py` invoked 5x in `ci.yml` |
| Event separation | PASS | `ci.yml` pull_request + dispatch; `post-merge.yml` push; `release.yml` push (tag) |
| Single always-resolving aggregate | PASS | `ci-required` guarded by `if: always()` (the contract's permitted form; the detector's literal `!cancelled()` probe is the same artifact as in v4.4.1) |
| Allowlist verdict | PASS | `success` / `skipped` allowlist |
| Job-level cost scoping | PASS | 7 job-level `if:` guards; the 6 path-filtered workflows produce none of the 5 required contexts |
| Required contexts, no matrix leg | PASS | `ci-required`, `colocation`, `shellcheck`, `validate`, `verify`; `check_required_check_coverage.py`: 10 contexts across 2 branches, all unconditional |
| Immutable action refs | PASS | 52/52 pinned to a 40-character SHA |
| Explicit permissions | PASS | all 11 workflows |
| Caches keyed to manifests | PASS | `extensions/*/pyproject.toml`, `.pre-commit-config.yaml`, `ci.yml` |
| Concurrency | PASS | all 11; `release.yml` `cancel-in-progress: false` |
| Artifact retention + unconditional upload | PASS | `retention-days: 7`; 6 `if: always()` steps |
| Structured reports | PASS | `--reports-dir`, `GITHUB_STEP_SUMMARY` |
| Deployment boundaries | PASS | none in `ci.yml`; `release.yml` behind a tag |
| `MT-1` fail-closed guide browser coverage | PASS | `guide-render` sets `NEXUS_REQUIRE_RENDER=1`, runs `tests/guides/` (which now holds every v4.4.2 suite), aggregated into `ci-required` |

PROPOSE / APPROVE / APPLY: zero workflow differences; no `.github/workflows/` file was edited by this plan. One repository-native profile edit WAS required and is a finding (`BG-15`): `make validate` gained `stamp_guide_counts.py --check` in Phase 1 with the note that the `validate` job already covered it, but that job executes `scripts/ci/profiles.py` groups rather than `make validate`, so the new guard was unreachable from CI until this phase registered it in the DOCS group. `test_every_validator_make_validate_runs_is_reachable_from_ci` is the gate that caught it.

Cross-installer parity (declarative): `check_installer_parity.py` PASS; `tests/installer/` see the full-suite section. Real current-host installer run: NOT performed, by design. v4.4.1 proved a `HOME`-redirected run is not a sandbox on Windows (`USERPROFILE` resolution) and mutated live configuration; this plan never attempts one. The duty is recorded as owned gap `HT-2` (v4.4.1's), which the operator accepted on 2026-09-02, and Ubuntu / macOS installer legs run in the integration pull request's `install-smoke` and `installer-smoke` jobs.

**Disposition**: PASS on every field with zero pipeline edits; the real-install duty is an accepted owned gap.

## Tier 3 deep pass

Every artifact this plan produced was exercised through its real boundary.

| Artifact | Exercised how | Observed |
|---|---|---|
| `guides/website/nexus-hub-guide.html` | Declared 150-case matrix (`browser_matrix.py --label phase-7`), 13 groups, both themes | 150/150 cases, 124/124 screenshots, 0 failures, 165 s, 12.7 MiB; fullscreen min coverage 0.93, min stage 0.468; 0 external requests, 0 console errors |
| Same file, visual detector | 4 pages x 2 themes x 6 viewports in the gate | 0 findings beyond the documented Gemini allowlist |
| Same file, byte and offline contracts | filesystem + static scan + request capture | 345,623 bytes (ceiling 500,000); 0 external scripts or stylesheets; the only absolute URLs are an SVG namespace, the CC BY link, the repository link, and two install commands as copyable text; 0 runtime requests |
| `NexusSeq` | 5 Phase 1 browser tests + every scene that uses it | order, offscreen pause, hidden-tab pause, reduced-motion end state, malformed step skipped |
| `NexusFlow` | 6-width connector geometry test | 3 roots, 7 connectors, 0 card crossings |
| Annotated prompt | Phase 3 tests | 4 parts in order, 0 nesting, in-order reveal, all-at-once under reduced motion |
| Waveform | Phase 4 tests | static without gesture, live frames while playing, frozen on pause, static under reduced motion |
| Layered harness | Phase 4 tests | model / platform / nexus-hub layers, 9 ports, 7 steps, text inside viewBox at 6 widths |
| Arena engine v2 | 34 shooter tests + pure `spawnSample` seam | beats unchanged (buggy hit tick 75, fixed walk 3-2-1-0), 3 bands, 3 size and 3 speed tiers, pointer contract, key guide vs touch |
| Three-pane presentation | 21 workspace tests | coverage 0.93-0.95, stage 0.47-0.61, 0 below the fold, Outline invariance, short-window reflow |
| `scripts/stamp_guide_counts.py` | 6 unit tests + `--check` in `make validate` | 5 markers equal the catalog |
| `tests/guides/tools/browser_matrix.py` | ran twice (before and after the Phase 7 fixes) | identical 150/150 result on the committed bytes |
| `guides/website/README.md` | v4.4.0 CI-contract test + `check_docs_conventions.py` | required phrases present; conventions clean |
| Decision record, contract, geometry doc, histories | `validate_decision_records.py`, unicode and personal-path scans | 30 records OK; clean |

Iteration budget: 14 defects found and fixed across the plan (`BG-13`, `BG-14`, and twelve first-run test failures each traced to its cause and fixed in code or copy, never by loosening a test to fit). No P0 and no P1 survived. No residual finding remains open in the shipped artifact.

**Disposition**: PASS.

## Goal-vs-codebase review

**Plan Goal restated**: ship a production-ready single-file Nexus Hub guide whose Home restores the v4.1.2 hero and its five explanatory sections at a readable scale, whose Foundations page teaches each concept through one coherent title system, balanced layouts, annotated prompt and context examples, and choreographed animations that show a model nested inside a platform harness wrapped by the Nexus Hub harness, and whose Training arena supports pointer play with dense varied threats inside a fullscreen presentation that uses the entire window at every desktop size.

Measured directly in a browser on the committed file, not read from the plan's checkboxes:

| Definition-of-Done clause | Observed |
|---|---|
| Hero: exact `Nexus Hub`, v4.1.2 subtitle and lead, credits out of Home, attribution in footer | `Nexus Hub`; `Upgrade your agentic AI platforms with an autonomous team of world experts`; lead begins `Nexus Hub is an advanced harness for agentic AI platforms.`; 0 credits elements in Home; footer carries the CC BY 4.0 link |
| Section titles share one style at one token, with eyebrows | 24 `.section-title` at 65 px (token 2.4); no title wraps past two lines at 1440 |
| Home order | 9 headings in exactly the agreed order |
| Counts stamped, `--check` gated | `skills=329` x2, `hooks=30` x2, `pretooluse=15`; `make validate` step green |
| Zero visible `Nexus-Hub` | 0 (case-insensitive) |
| Foundations centred title, no kicker, eight scenes in order | `The concepts behind every AI-assisted project`; kicker absent; 8 titles in the accepted order; subtitles above titles |
| No empty column | balance `stacked, stacked, 1.07, stacked, 1.06, stacked, stacked, stacked` |
| Annotated prompt | `goal, material, done, format`; 0 nesting |
| Outputs `Text`, `Image`, `Video`, `Audio`; waveform | labels exact; waveform static at rest, live while playing (tested) |
| Layered harness with choreography and static end state | 2 instances; layers `model`, `nexus-hub`, `platform`; 7 steps |
| Arena: Space or click fires; leaving pauses; key guide vs touch | `pointer` pause reason supported; guide hints present; touch controls hidden under a fine pointer |
| Continuous varied spawning; beats unchanged | 3 bands, 3 tiers, speeds `45, 75, 110`; buggy hit at tick 75 with lives 3; fixed walk `3, 2, 1, 0` |
| Fullscreen coverage >= 0.88, stage floor, nothing below the fold, no overflow, `Full screen` before `Outline` | 0.93 / 0.93 / 0.93 / 0.95; stage 0.47 / 0.50 / 0.53 / 0.61; 0 below; 0 overflow; bar order `Full screen`, `Outline` |
| One self-contained offline file <= 500,000 bytes | 345,623 bytes; 0 external script or style; 0 runtime requests |
| Automated evidence for dark, light, keyboard, zoom, reduced motion, canvas-unavailable, offscreen, hidden tab, hostile fixture, deterministic replay | all in the gate and the matrix; no completion claim rests on structural scoring alone |

**Gaps**: two, neither a Goal or Definition-of-Done miss in the code. (1) The stage-height floor is 0.45, not 0.70: the plan's own acceptance text named 0.70, and the arithmetic in `presentation-geometry.md` shows that number cannot coexist with the toolbar, progress strip, head, takeaway, and controls the same Definition of Done requires visible; the deviation is recorded in the contract and the achieved 0.47 to 0.61 is measured. (2) Human comprehension testing has no cohort (`HT-1`), which the Definition of Done anticipates and directs to be recorded, not fabricated.

**Disposition**: the Goal landed. PASS.

## Human/manual testing suggestions

Automated evidence covers rendering, geometry, determinism, accessibility wiring, motion contracts, and offline delivery. It cannot cover whether a newcomer understands the page or whether the arena feels right under a hand, which is what a cohort is for.

Ask each participant, with no maintainer coaching, to:

1. Point at each highlighted part of the Prompt Engineering example and say what it is for (goal, material, done, format), then do the same for the request and its attached material in Context Engineering.
2. Describe in their own words what the harness animation shows, and say where Nexus Hub sits relative to the platform and the model.
3. Distinguish a prompt from context; provider training from a live request; qualified effort from a guaranteed hidden iteration count; chatbot output from permitted agentic action.
4. Read the Guardrails section and say what a hook does that the platform's permission prompt does not.
5. Play the arena with the mouse only: start, fire by clicking, pause by moving the pointer out, resume, then use `Full screen` and `Outline`.
6. Say which of the restored Home sections they would remove, and why.

Environment-specific checks only a human can make: native fullscreen on a projector or second monitor; touch play on a tablet (the five touch controls appear under a coarse pointer); a real screen reader reading the HUD lives changes and the sequence captions; audio through real speakers with the waveform in view.

**Participants**: 0. No representative newcomer cohort was available in this session. **Disposition**: OPEN, owned gap `HT-1`, recorded honestly rather than fabricated.

## Full-suite testing and stabilization

```text
NEXUS_REQUIRE_RENDER=1 python -m pytest -q tests/guides/ tests/verification/test_visual_defect_detector.py
302 passed, 1 skipped in 264.09s   (at e1f676f1, the Phase 8 base)

python tests/guides/tools/browser_matrix.py --label phase-7
cases: 150/150  screenshots: 124/124   runtime: 165s / 1200s   evidence: 12.7 MiB / 30 MiB   failures: 0

make validate equivalents: 27 guards, every exit 0 (stamp_guide_counts --check: 5 markers match the catalog)
python -m pytest -q catalog/hooks/tests/test_installer_smoke.py      33 passed

Canonical CI profile (no installer running concurrently this time):
python scripts/ci/run.py --profile full --only tests,extension-tests
  hook-tests ok (614s) | repo-tests: 7 failed, 3896 passed, 56 skipped in 3184s | six extension suites ok | compression gate ok
  The seven were investigated, not accepted:
  - 1 x tests/validators/test_ci_workflow_contract.py::test_every_validator_make_validate_runs_is_reachable_from_ci
    REAL, caused by this plan (BG-15): Phase 1 wired stamp_guide_counts.py --check into make validate and recorded it as
    "covered by the existing validate job", but that job runs scripts/ci/profiles.py groups, not make validate, so the guard
    was unreachable from CI. Fixed in this phase by registering it in the DOCS group; the reachability test and
    tests/workflows/ pass.
  - 6 x tests/installer/test_core_settings_seeding.py [powershell] variants
    PRE-EXISTING and environment-only (QG-1): they pass standalone and fail only under the profile runner, which sets
    PYTHONUTF8=1; with that variable alone the six fail identically on the develop worktree at 68f3d082, before any
    v4.4.2 commit. The v4.4.1 evidence attributed the same six failures to concurrent installer processes; that attribution
    was incomplete and is corrected here. They cannot reach CI's Ubuntu legs (PowerShell variant skipped there).

Byte guard: 345,623 bytes | strict ceiling 500,000 | headroom 154,377
```

**Disposition**: GREEN for everything this plan owns. One real finding (`BG-15`) was fixed in this phase and re-verified; six pre-existing, environment-only failures reproduced on `develop` are recorded as owned gap `QG-1`, not accepted silently and not fixed here because the defect is outside this plan's mutation authority.

## Publication and integration preflight

| Item | Value |
|---|---|
| Branching model | `develop` + `main`; feature branches integrate through `develop` |
| Remote | `origin` (`git@github-bendourthe:bendourthe/Nexus-Hub.git`) |
| Branch | `feat/v4.4.2-guide-production-ready-rebuild`, cut from `develop` at `46f18986` (the v4.4.1 merge) |
| Local commits on the branch | 8 after the Phase 8 commit (one per phase) |
| Phase 8 verification base SHA | `e1f676f1585071dea1486d1203dcc02d77772dc3` (the Phase 7 commit) |
| Pull-request target | `develop` |
| Required checks | `validate`, `shellcheck`, `ci-required`, `colocation`, `verify` |
| Target-OS installer matrix | Ubuntu, macOS, Windows via the `install-smoke` and `installer-smoke` jobs in the integration run; no local live-profile run (see CI/CD coverage) |
| Approval status | GRANTED 2026-09-02 by the operator before the plan started: push once, open the pull request to `develop`, and merge once every required check is green |

**GO / NO-GO: GO.** No P0 or P1 finding; no Goal or Definition-of-Done miss in the shipped artifact. Residuals: `HT-1` (no cohort), the 0.45 stage-height floor deviation, and `QG-1`, a pre-existing P3 test-harness defect (six PowerShell seeding tests fail only under the profile runner's `PYTHONUTF8=1`, proven on `develop` before this plan) recorded with owner and next step; the operator's standing approval covers publication, and `QG-1` is surfaced explicitly in the handoff for acknowledgement. The local gate is green as quoted. Remote results are recorded by the release-owned handoff, never by re-pushing this branch to quote them.

<!-- END v4.4.2-guide-production-ready-rebuild -->
<!-- BEGIN v4.4.3-guide-illustration-clarity-rebuild -->

# Last-Phase Evidence - v4.4.3 Guide Illustration Clarity Rebuild

**Version**: v4.4.3
**Slug**: `guide-illustration-clarity-rebuild`
**Branch**: `feat/v4.4.3-guide-illustration-clarity-rebuild`
**Base**: `develop` at `a376c1ae` (the v4.4.2 merge)
**Phase 9 verification base SHA**: `1fe0322952e83b09509b5ac5b8b20b45d46de571`
**Date**: 2026-09-03
**Publication state**: DELIBERATELY UNPUBLISHED. The operator asked to review Home and Foundations before Training work begins, so this version stops at a green local gate. Nothing was pushed, no pull request was opened, and no remote CI ran.

## What this version was for

A direct visual review of the shipped v4.4.2 build, across ten screenshots. Ten complaints, each traced to a phase and each measured rather than eyeballed:

| Review item | Where it went |
|---|---|
| Segment label too small, segment title too big, titles wrapping | Phase 1 |
| Table column headers too quiet | Phase 1 |
| Never address the reader | Phase 1 |
| The guardrails figure is messy: text outside its bubbles, misplaced content | Phase 2 |
| The command loop wastes its width; the arrows are invisible | Phase 3 |
| Request and context boxes cramped; dotted noun boxes; the two budget boxes make no sense | Phase 4 |
| The nonsensical circle; empty space; the video needs a click; a weak example; name real models | Phase 5 |
| Agentic Platform should be plural and should name platforms with logos | Phase 6 |
| Chatbot versus agentic platform needs a real illustration | Phase 7 |
| One harness segment, no overlapping text, animate the journey | Phase 8 |

## The one idea behind most of the fixes

Six of the ten complaints had the same root cause: a figure that positions text in a scaled coordinate space cannot keep that text inside the shape behind it. SVG `<text>` does not wrap, does not shrink, and does not know how wide the `<rect>` it sits on is, so at some column width it collides with something. Every rebuilt figure in this version is nested HTML elements with geometry-only SVG, because a box that sizes to its own text cannot overflow it. The guardrails figure, the material kinds, the chatbot comparison, and the harness all changed for this one reason, and the tests assert the property rather than the appearance.

## Verification

```text
NEXUS_REQUIRE_RENDER=1 pytest -q tests/guides/ tests/verification/test_visual_defect_detector.py
    347 passed, 1 skipped in 351.20s (5m51s)

python tests/guides/tools/browser_matrix.py --label phase-9
    cases: 164/164   screenshots: 138/138
    runtime: 183s / 1200s    evidence: 13.7 MiB / 30 MiB
    failures: 0

python scripts/ci/run.py --profile fast --quiet          PASS: 13 passed, 0 failed
python scripts/ci/run.py --profile full --only docs,catalog,security --quiet
                                                         PASS: 16 passed, 0 failed
pytest -q tests/validators/                              1139 passed, 2 skipped
pytest -q tests/workflows/                               97 passed, 13 skipped
pytest -q catalog/hooks/tests/test_installer_smoke.py    33 passed
python scripts/stamp_guide_counts.py --check             OK -- 5 markers match the catalog
validate_unicode_safety.py --strict / validate_no_personal_paths.py       clean
check_docs_conventions.py                                OK
```

The matrix grew from 150 declared cases to 164: the harness group now drives six stops instead of seven, and two groups were added for the scenes this version made choreographed (the chatbot comparison at 420 and 1440, and the platforms flow). Three figures gained ids, because the matrix addresses a sequence root by id and the new ones were built with class selectors only. The tool also had the previous version's slug hardcoded, so the run first wrote into the v4.4.2 evidence directory; the path and the plan label now derive from one constant and the run was moved under this plan's slug. The 138 screenshots are regenerable and are not committed (the v4.4.2 set is already 28 MB); the per-run summary JSON is, and the renders README records the reasoning.

## Byte ledger, closed

| Phase | Change | Bytes | Running total |
|---|---|---:|---:|
| start | v4.4.2 final | | 345,623 |
| 1 | two size tokens, NexusFit, table-header grade, second-person sweep | +4,282 | 349,905 |
| 2 | guardrails figure rebuilt in HTML, its SVG retired, table column shares | +2,584 | 352,489 |
| 3 | loop fills the column, larger box type, CSS triangles | +966 | 353,455 |
| 4 | two-line legend rows, illustrated material grid, legend-free budget meters | +1,985 | 355,440 |
| 5 | ring retired from both scenes, one-pass block, model names, autoplaying video, thicker connectors | +3,920 | 359,360 |
| 6 | plural title, four platform chips with reused approved marks, shorter copy, five-stage choreography | +13,989 | 373,349 |
| 7 | chatbot comparison rebuilt as a two-zone reach illustration | +4,365 | 377,714 |
| 8 | two harness scenes merged into one HTML figure, two SVG figures retired | -7,490 | 370,224 |
| 9 | three sequence-root ids | +47 | 370,271 |

Final: **370,271 bytes**, 129,729 under the 500,000 ceiling and 35,352 under this plan's own 405,623 target. The file is smaller than at Phase 7 close: replacing two SVG figures with nested elements returned more bytes than the four inlined platform marks cost.

## Defect ledger

Seven defects were introduced by this plan and fixed inside it; two pre-existing defects were found and closed; one regression shipped for four commits before Phase 8 caught it. All are in `known-gaps.md` with IDs `BG-17` through `BG-25`. The three worth carrying forward as rules:

1. **Never measure available space against a track the measured element can widen.** Three separate instances: a `nowrap` label inflating a `1fr` scene track, `width: max-content` on a label doing the same, and `width: max-content` on the harness model box pushing both rings 88px outside the scene at 320px. Bound the track with `minmax(0, 1fr)` AND set `min-width: 0` on the intrinsically sized item.
2. **A usage count cannot tell you where a class is used.** Phase 4 deleted CSS after counting four usages of `fx-budget` and reading that as the two boxes it was replacing. The other two were in the harness trail, which rendered with no border, no background, and no columns for four commits. Phase 8 added a guard tying every class in the Foundations markup to a style rule; it found one more gap immediately.
3. **A replace without an assertion is a wish, not an edit.** Four byte-ledger rows never reached the phase contract because the scripts that wrote them used a plain string replace with no assertion, so a mismatched anchor did nothing and said nothing. The ledger above was rebuilt from measured file sizes.

## Superseded assertions

Thirty-one register rows in [`guide-illustration-clarity-rebuild/phase-1-contract.md`](guide-illustration-clarity-rebuild/phase-1-contract.md), each naming the literal it pinned and what replaced it. Two are worth surfacing because they retired a rule rather than repointing one:

- **Press-to-play.** v4.4.1 required a press before any motion. The review asked for the opposite. The rule was inverted and the half of it that was about access rather than about asking was kept and asserted: reduced motion shows the still frame.
- **The two harness instances.** A rule that the two harness scenes share a byte-identical glyph cannot survive their merge into one scene. It is recorded as retired, not quietly deleted.

One assertion was found to be VACUOUS rather than merely superseded: the harness containment test selected `.fx-hstack svg text`, which after the rebuild matches nothing, so it would have passed by inspecting an empty set. It is rewritten over the HTML figure and measures every leaf's glyph run against its own box at six widths.

## Documentation

`guides/website/README.md` records what shipped: the two heading tokens and the measured no-wrap rule with its floor and its stated deviation, the no-second-person rule and its honest scope, the read-not-recalled rule for model names, the reuse-from-the-ledger rule for vendor marks with the id-namespacing caveat, the inverted motion rule, the class-coverage guard, and the intrinsic-width rule. Foundations is documented as seven scenes with each rebuild described. The asset provenance ledger carries a new section for the mark reuse, the product-versus-vendor substitution, and the one documented second sanitization.

## GO / NO-GO

**GO for the operator's review, NO-GO for publication until that review happens.**

No P0 and no P1. Every Definition-of-Done clause is measured except `D2`, which is met at 720px and wider and relaxed below it with the arithmetic recorded. Two residuals are the operator's to judge rather than defects: the label now renders larger than the title, which is exactly what the review's two numbers produce, and the platform chips carry vendor marks under product names because the linked aggregator serves a client-rendered page with no stated licence. `HT-4` records the honest gap: no reader has been asked whether the rebuilt pictures land, and that is what the review is for.
<!-- END v4.4.3-guide-illustration-clarity-rebuild -->

<!-- BEGIN v4.4.4-guide-teaching-clarity-rebuild -->

# Last-Phase Evidence - v4.4.4 Guide Teaching Clarity Rebuild

**Date**: 2026-09-03
**Branch**: `feat/v4.4.3-guide-illustration-rebuild` (v4.4.3 was never published, so v4.4.4 continues on it)
**Base revision**: `bcfa3413`, the v4.4.3 closeout
**Publication state**: NOT published. Nine phases are committed locally. Nothing was pushed, no pull request was opened, and no remote pipeline ran. The operator reviews Home and Foundations before Training work begins, which is what they asked for.

## What the second review changed

The first review round fixed how the illustrations LOOKED. This round changed what several of them SAY, which is a different kind of edit and a larger one: six scenes were rebuilt around their teaching rather than their layout.

| Phase | Scene | What it now teaches |
|---|---|---|
| 1 | Guardrails & Safety | Named for what it does. Both rings state their behavior in centred text: hooks block flagged actions even when approved, permissions ask and then allow. |
| 2 | One Harness, Multiple Platforms | BOTH benefits, where there was one. One install reaches four platforms and a task can move between them mid-run; and the commands are built on the generic ones rather than replacing them. |
| 3 | Foundations, all six scenes | The scene NAME first, its description under it. The pair was inverted. |
| 4 | Prompt Engineering | A vague prompt beside the specific reasons it fails, then one engineered prompt at full width with quiet labelled parts. |
| 5 | Context Engineering | The request beside the material it can name, with concrete examples; then the cost of dumping everything against the gain from naming it, each stated in four items. |
| 6 | Models | How a model works: one token at a time, base against reasoning, three modality tiers. One family per provider, no version numbers. |
| 7 | Agentic Platforms | One scene, not two. The same request to two lanes over the same two zones, differing only in reach. |
| 8 | Harnesses | One flow: request, model like a powerful brain, platform harness like a graduate degree with its limits stated, Nexus Hub harness like decades of practice, reviewed work. |

## Verification

```text
NEXUS_REQUIRE_RENDER=1 pytest -q tests/guides/ tests/verification/test_visual_defect_detector.py
                                                        354 passed, 1 skipped in 308s

python tests/guides/tools/browser_matrix.py
    cases 154/154 | screenshots 128/128 | failures 0
    runtime 153s / 1200s | evidence 12.3 MiB / 30 MiB

python scripts/ci/run.py --profile fast --quiet                 13 passed, 0 failed
python scripts/ci/run.py --profile full --only docs,catalog,security --quiet
                                                                16 passed, 0 failed
python scripts/stamp_guide_counts.py --check
    5 markers match the catalog (skills=329, hooks=30, pretooluse=15, commands=18)
python scripts/check_docs_conventions.py                        OK
```

The matrix count fell from 164 to 154 because Phase 7 merged a scene away and Phase 6 retired the waveform group. Each retired group is recorded in the browser-matrix source next to the group it replaced, so the drop is a stated consequence rather than silent coverage loss.

## Byte ledger

Closed in [`guide-teaching-clarity-rebuild/phase-1-contract.md`](guide-teaching-clarity-rebuild/phase-1-contract.md).

Final: **366,529 bytes**, 133,471 under the 500,000 ceiling and 3724 bytes BELOW where v4.4.3 finished. Rebuilding six scenes made the file smaller, because Phase 6 retired an audio asset whose teaching had left the page and Phase 7 deleted a whole scene by merging it.

## Defect ledger

Four defects were introduced by this plan and fixed inside it; two pre-existing defects were found and closed. All are in `known-gaps.md` as `BG-26` through `BG-31`. Three are worth carrying forward as rules:

1. **Recompute offsets immediately before a splice.** v4.4.3 Phase 8 lost half a scene this way and v4.4.4 Phase 7 landed a merged scene inside a base64 payload the same way. The same mistake twice is a process defect, not an accident. The recompute now sits directly above every splice with a comment naming both failures.
2. **A non-greedy match will happily stop at the wrong closer.** Phase 6 left two stray closing tags: one orphaned a note, the other closed the request region early, dropping a flow root and cutting the connectors from seven to two. Nothing looked broken. Re-emitting the section from harvested parts with a per-part balance assertion is what caught it.
3. **A contrast sweep that skips hidden text will pass a palette it never measured.** Making sequence steps visible under reduced motion, which was itself the right fix, immediately exposed three light-theme WCAG AA failures at 3.92, 4.08, and 1.90. Two of those shipped in v4.4.3.

## Superseded assertions

Recorded in the same contract's register. The two that retired a rule rather than repointing one:

- **The audio output and its waveform.** v4.4.2 asserted a hash-matched WAV and a waveform canvas. The Models teaching no longer covers audio, so the asset, the element, the canvas, and the engine were all removed and the assertion INVERTED to require their absence. The provenance row stays as the record of what was approved.
- **The nested harness rings.** A geometric-nesting assertion cannot survive the rings becoming a flow. It is recorded as retired and replaced by one that measures the teaching: three layers in order, each with its ports, the analogy on each, and the platform layer's limits named.

## Documentation

`guides/website/README.md` carries four new v4.4.4 rules: the two pages use the heading pair in opposite orders on purpose, a model is named by family and maker with no version number, an asset leaves the page when its teaching leaves, and a sequence step is never hidden under reduced motion. Foundations is now documented as six scenes with the title first.

## GO / NO-GO

**GO for the operator's review, NO-GO for publication until that review happens.**

No P0 and no P1. Every task in the plan is measured. Two items are the operator's to judge rather than defects, both recorded in `known-gaps.md`: the Models scene names `xAI Grok` rather than `Cursor Grok` as the brief listed, because Grok is xAI's model and Cursor is a platform that offers models; and the Home label still renders slightly larger than its title, which is what tripling one and halving the other produces.

<!-- END v4.4.4-guide-teaching-clarity-rebuild -->

<!-- BEGIN v4.4.5-guide-mockup-integration -->

# Last-Phase Evidence - v4.4.5 Guide Mockup Integration

**Date**: 2026-09-04
**Branch**: `feat/v4.4.3-guide-illustration-rebuild` (neither v4.4.3 nor v4.4.4 was published, so v4.4.5 continues on it)
**Base revision**: `3ac90bb2`, the v4.4.4 closeout
**Publication state**: NOT published. Eight phases are committed locally. Nothing was pushed, no pull request was opened, and no remote pipeline ran. The operator reviews Home and Foundations before Training work begins.

## What the third review round asked for

Two different kinds of change, kept apart by the plan on purpose.

**Precise corrections** to scenes that already worked (Phases 1 to 4): stop an animation that made a figure hard to read, add the platform logos, centre the connectors, widen a strip, double the block tags, rename the prompt's four parts, re-lay out two figures, and restyle two captions.

**Three full scene rebuilds** from operator-supplied mockups (Phases 5 to 7). This is the part worth recording carefully, because the mockups and this guide have incompatible constraints.

| Phase | Scene | What the mockup gave | What it could not give |
|---|---|---|---|
| 5 | Models | The eight-stage spine, and two stages the guide lacked: Select and Predict | Two tablists, a ring whose labels and arrows lived in unrelated coordinate systems, a `<select>`, a `<textarea>`, and a run button |
| 6 | Agentic Platforms | The model-plus-harness equation, the boundary's three settings, the six-part anatomy | Scenario tabs, boundary buttons, a run button, a 720x520 SVG map |
| 7 | Harnesses | A limit or guarantee on every layer, the five-step work sequence, the artifact chain | Layer, mode, and host buttons, a run button, a hero orbit, a 760x470 SVG map |

Each mockup hid at least one of its best lessons behind a control. The agentic one only teaches that a boundary REPORTS a refusal rather than routing around it if the reader presses read-only and watches step 03 stop. Those states are all on the page now, and the tests assert multiplicity rather than presence.

## Verification

```text
NEXUS_REQUIRE_RENDER=1 pytest -q tests/guides/ tests/verification/test_visual_defect_detector.py
                                                        376 passed, 1 skipped in 341s

python tests/guides/tools/browser_matrix.py --label phase-8-v445
    cases 158/158 | screenshots 132/132 | failures 0
    runtime 151s / 1200s | evidence 12.9 MiB / 30 MiB

python scripts/ci/run.py --profile fast --quiet                 13 passed, 0 failed
python scripts/ci/run.py --profile full --only docs,catalog,security --quiet
                                                                16 passed, 0 failed
python scripts/stamp_guide_counts.py --check
    5 markers match the catalog (skills=329, hooks=30, pretooluse=15, commands=18)
python scripts/check_docs_conventions.py                        OK
```

The matrix grew from 154 to 158 cases. Phase 8 gave the rebuilt Models scene its own group at a narrow and a wide width in both themes, because **a rebuilt scene that nothing photographs is a scene whose duplication ships** - which is precisely what Phase 5 did for one commit.

## Byte ledger

Closed in [`guide-mockup-integration/phase-1-contract.md`](guide-mockup-integration/phase-1-contract.md).

Final: **396,425 bytes**, 103,575 under the ceiling. The plan named the ceiling as this round's real constraint, and it was the right thing to watch: three scene rebuilds plus four copied vendor marks spent 29,896 of 133,471 bytes of headroom. The largest single line item is not a rebuild but the 12 KB of duplicated vendor artwork, which bought one thing worth buying: the approved bytes stayed where the ledger pinned them.

## Defect ledger

Six defects were introduced by this plan and fixed inside it, and one pre-existing defect was found and closed. All are in `known-gaps.md` as `BG-32` through `BG-38`. One theme runs through them and it is the finding of this plan:

**Three of the six shipped past a passing test, and they passed for the same reason.** A vendor mark asserted as an ELEMENT rendered blank. A rebuilt scene asserted for presence, order, balance, and containment said everything TWICE. An artifact chain asserted as `lefts == sorted(lefts)` stacked one chip per line, because four identical offsets sort perfectly well. In each case the assertion described the INTENT and the failure mode slipped underneath it. The three replacements measure a painted box larger than 8px, an exact occurrence count, and four distinct increasing offsets on one row.

**Two of the six were found by looking at a screenshot, not by the suite.** That is now the second plan in a row where the rendered image caught what 300-plus tests could not, and it is worth treating as a standing practice rather than a lucky habit.

The pre-existing defect is the sharpest one. `.fx-copy .fx-tokfig-cap` has matched NOTHING since the token figure moved into `.fx-diagram`, so two captions and a note have been rendering as plain body text for versions. The v4.4.3 class-coverage guard cannot catch this class: it proves a class USED in the markup has a rule, and says nothing about whether a rule's selector matches anything. Those are different questions and only one was being asked. `GA-1` records that the other direction is still unguarded.

## Superseded assertions

Six register rows in the same contract. The two that retired a rule rather than repointing one:

- **The portability figure's three-step reveal.** v4.4.4 asserted `NexusSeq.state(fig).total == 3`. The review said the animation made the figure hard to read, so the assertion is INVERTED to require no sequence root at all.
- **The flaws beside the vague prompt.** v4.4.4 asserted that arrangement, having itself corrected v4.4.3's. This round asked for a third arrangement. Recorded as inverted, not deleted, because the previous two were also requested and a reader of this file should be able to see that.

## Documentation

`guides/website/README.md` carries five new v4.4.5 rules: an assertion has to describe the failure rather than the intent; a rename is not finished until every sentence about the old name has been read; one tag size from one token, with the in-cell exception asserted in both directions; an approved asset is copied rather than shared when sharing would rewrite it; and a mockup is a source of teaching rather than markup to paste.

## GO / NO-GO

**GO for the operator's review, NO-GO for publication until that review happens.**

No P0 and no P1. Every task in the plan is measured. Three items are the operator's to judge rather than defects, all in `known-gaps.md`: the Models scene names `xAI Grok` rather than `Cursor Grok` as the brief listed, because Grok is xAI's model and Cursor is a platform that serves models; `Context Engineering Best Practices` now reads quieter than the two tags below it, because "match the subtitle" and "double the tags" were both followed exactly and pull against each other; and the Home label still renders larger than its title, which is what the first round's two numbers produce.

<!-- END v4.4.5-guide-mockup-integration -->


## v4.4.6 final record - 2026-09-04

This append-only record belongs to [v4.4.6 guide-learning-experience](../plans/v4.4.6-guide-learning-experience.md). Earlier v4.4.0-v4.4.5 records above remain historical evidence. Current status: six phases committed; final local evidence prepared, with the full repository result, reader review, and publication gates open. The [phase history](guide-learning-experience/phase-7/verification.md) is the detailed receipt.

## Architecture refactor

> Scan: 4,286 tracked files; 12 empty marker files; 97 deep paths; one guide duplicate group; 1,545 documentation inventory records; 735 lifespan candidates.

The [repository audit](guide-learning-experience/phase-7/repository-audit.json) records the inputs and dispositions. The duplicate is the intentionally retained pair of Glow Booth pose fixtures. Empty package markers and supported skill paths remain intentional. Lifespan candidates require review against patch-release ownership, not automatic deletion or a claim of 735 defects. No current guide artifact needs moving, and no unrelated refactor was applied.

## Known-gaps reconciliation

> Discovery: 33 canonical and legacy known-gap files, each with a source hash and status observation. Current guide ledger: nine open items (three bugs, three coverage gaps, two warnings, one quality-gate gap) and seven resolved defects.

The [current ledger](../known-gaps.md#v446---guide-learning-experience) carries technical/non-technical review, native zoom/occlusion observation, retained CI reports, the historical CodeQL rescan, and the timed-out full-suite result. Fresh isolated Windows/Linux installer proof addresses the available part of HT-2; retired illustration issues are superseded. Other release owners and their history are preserved. Counts describe this release's current section, not all historical open rows.

## Living docs architecture

> Present: docs/handbooks/markdown, docs/handbooks/html, docs/decisions, docs/README.md, docs/DEVLOG.md, docs/todos.md.

The handbook README declares no authored handbook pages, so there is no existing atlas or generated counterpart to reconcile. Building new handbooks is outside this guide plan. The guide maintainer README now describes the actual seven lessons, explicit motion, safe inline data, and current audit commands. DEVLOG and the dashboard point to this plan and its evidence. No docs/testing or docs/validation tree was invented.

## Git-tree hygiene

> Report-only branch scan: three merged-branch cleanup candidates, one closed-unmerged candidate, and thirteen open-PR branches excluded. delete_branch_on_merge is enabled; repository description agrees with README.

The [raw preconditions](guide-learning-experience/phase-7/git-preconditions.txt) are retained. Nothing was deleted. The plan uses the existing feature branch, with origin pointing to bendourthe/Nexus-Hub and develop as the integration target. Unrelated v4.7-v4.9 planning work and image.png remain excluded from this phase's commit.

## CI/CD coverage

> Provider: GitHub Actions. Required-check coverage: ten declared contexts across two branches, all unconditionally produced. Installer parity PASS; thirteen platform contracts match. Real isolated Windows PowerShell and Ubuntu Bash installer smoke: PASS on both.

The [field comparison](guide-learning-experience/phase-7/ci-comparison.md) covers native profiles, events, runners, aggregate status, permissions, pinning, caching, concurrency, path scoping, reports, deployment boundaries, and recovery. The existing report-retention difference is WN-446-1 with a minimal proposal, owner, and next step. No pipeline change was applied. The comparison is partial with an owned gap, not blanket conformance. Real installers ran with identical postconditions; the user's existing installation was not modified or certified.

## Tier 3 deep pass

> Bounded result: three product correction cycles completed. Final guide suite: 258 passed, one optional portfolio-mirror skip. Render audit: 72 cases, zero overflow/errors/requests/hidden essentials. Offline reflow audit: 88 cases. Detector: eight route/theme runs across eleven widths, zero unallowlisted findings. Sequential performance comparison: final budgets met, including the separate 4x CPU run.

The [entry](guide-learning-experience/phase-7/deep-pass-start.md), [history](guide-learning-experience/phase-7/verification.md), [performance report](guide-learning-experience/phase-7/performance.md), and [visual receipt](guide-learning-experience/phase-7/visual-review.json) retain scope, exact artifact hash, measurements, and actually inspected captures. The independent adversarial review exercised real Training/lesson boundaries and verified the prerequisite/focus corrections. Expanded review of all 296 Phase 2-7 images found two residual Training layout defects, BG-46/BG-47. D06/D12 remain partial; a separately tested candidate awaits the additional bounded-pass decision. Linux installer proof does not establish Linux browser coverage. Remaining environment, reader, and broad-suite gaps are owned in the ledger; they are not converted into a clean overall release gate.

## Goal-vs-codebase review

> Goal: technical and non-technical readers understand seven AI concepts, distinguish Nexus from its platform, and follow action to evidence through a concise, illustrated, responsive guide. Independent review found the requested product artifacts present; human comprehension remains unverified.

The [independent goal review](guide-learning-experience/phase-7/goal-review.md) maps D01-D13, identifies the corrected graph-output contradiction, and records the remaining gates. Home uses a responsibility map and one brief example; Foundations has seven concrete lessons; Training demonstrates truthful state and deterministic evidence. Meeting the implementation criteria does not prove D13.

## Human/manual testing suggestions

> Pending: one technical and one non-technical unassisted response set, final visual feedback, and native browser/OS observations.

The [reader exercise](guide-learning-experience/phase-7/manual-review.md) asks six transfer questions and names the browser behaviors automation cannot establish. The user has been asked for feedback. No answer or approval has been inferred from silence. T026 remains open until evidence arrives and any feedback is addressed.

## Full-suite testing and stabilization

> Complete guide suite: 258 passed, one optional skip in 174.24s. Full native repository profile: 40 passing commands, three failures, one timeout; no complete local green gate is claimed.

The [guide log](guide-learning-experience/phase-7/guide-suite.txt) is terminal evidence. The native command is `python scripts/ci/run.py --profile full --base bdd57cee --reports-dir <temporary-report-directory> --quiet`. The [terminal disposition](guide-learning-experience/phase-7/full-profile-disposition.md) retains native output, the explicit stop record, corrected encoding, and separate environment/scope findings. Historical QG-1 is not re-confirmed by the absent repository-test terminal output. T027 remains open.

## Publication and integration

> Not executed. Branch: feat/v4.4.3-guide-illustration-rebuild. Remote: origin, git@github-bendourthe:bendourthe/Nexus-Hub.git. Integration target: develop. Merge base: bdd57cee4eb776304a09e862c1d956534db59e1e.

The final phase remains uncommitted while its required gates are not green; the six completed phase commits are preserved. T028 requires explicit approval before the first push, then fresh PR required-check evidence and separate merge approval. Release/tag/back-merge and any portfolio copy remain separate gates. NEXUS_HUB_PORTFOLIO_ROOT is unset, so no external mirror is inferred or written. No remote CI, push, PR, merge, or release is claimed by this record.

Late content finding: BG-48 records the hostile-input fixture visible in the describe reply. The bounded follow-up must remove production test text while retaining test-local escape coverage. The complete guide has not been declared approved or released.

## User-directed v4.4.5 restoration

The user rejected the v4.4.6 removal and restructuring of Home and Foundations content. The guide, canonical Training data, README, and guide tests were restored from bdd57cee. The [restoration record](guide-learning-experience/restoration/verification.md) supersedes the v4.4.6 implementation and pending three-fix proposal as the current product disposition. Further changes must preserve the v4.4.5 sections, order, and substantive content and focus on selected existing visuals and animations. Previous records remain historical; they are not approval of the rejected guide.
