# Last-Phase Evidence - v4.4.0 Guide Depth and Training Rebuild

**Date**: 2026-08-31
**Branch**: `feat/v4.4.0-guide-depth-and-training-rebuild`
**Phase 7 base revision**: `5ddf83c34f1a6ea4e6029fe6b01942be5fb1cf53`
**Publication state**: Local-only; no Phase 7 commit, push, pull request, merge, tag, or release is claimed by this record.

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

Fresh independent rendered proof covered 32 route, theme, and viewport cases with zero detector findings and zero allowlisted cases. It also found one visible H1 per route, no heading-rank skips, unnamed focusables, positive tabindex, or focusables inside `aria-hidden`, and passing reduced-motion and measured-contrast contracts in both themes. The current guide SHA256 is `C3655425490DA85754FFD94B1EDCC5DA634389A0CA54FA4A3F3258B0310D8A77`.

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
| Publish and integrate | No remote mutation has occurred. | PENDING explicit push approval, terminal required checks, and explicit merge approval. |

The independent convergence review checked every prior implementation task and every named Goal clause against the current bytes. It reports 27 of 27 tasks satisfied, 9 of 9 Goal clauses satisfied, 0 partial, 0 missing, 0 contradictory, and no current code-vs-plan blocker. The guide is 495,319 bytes against the 500,000-byte gate. Platform-default agreement remains 13 of 13 surfaces, and the focused defaults, driver, lifecycle, and installer slice passed 96 tests with 10 explicit environment skips.

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

The skip in each result is the optional portfolio-copy contract. The remote CodeQL detector has not yet rerun against this local correction, so no remote closure is claimed.

**Disposition**: First push and PR creation COMPLETE. The local CodeQL correction is PASS, but remote integration remains PENDING / NO-GO until the correction is published, the same detector and every expected required check are terminal and green, and the user explicitly approves the merge. Release and back-merge remain later approval and verification gates.
