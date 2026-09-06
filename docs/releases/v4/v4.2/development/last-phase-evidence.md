# Last-phase evidence - v4.2.2 guide-cinematic-rebuild

**Date**: 2026-08-29
**Plan**: `docs/releases/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md`
**Phase**: 7 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
**Branch**: `feat/v4.2.2-guide-cinematic-rebuild`

This file supersedes nothing: the v4.2.1 evidence file remains at `last-phase-evidence.md` history and `last-phase-evidence-v4.2.0.md`. Every duty below quotes the command or scan that proves it.

## Architecture refactor

Empty-directory and orphan scan over the touched trees:

```text
$ find guides docs/releases/v4/v4.2 -type d -empty
(no output)

$ git status --short --ignored=no
(clean)
```

One redundant-file finding, applied:

```text
$ python - (compare committed reference against the tag)
reference bytes: 476900  tagged bytes: 476900
byte-identical to git tag v4.1.2: True

$ git rm docs/releases/v4/v4.2/development/guide-rebuild/reference-v4.1.2.html
removed (recoverable: git show v4.1.2:guides/website/nexus-hub-guide.html)
```

`development/guide-rebuild/design-brief.md` was updated in the same commit to cite the `git show` command instead of the deleted copy, so the reference is still reachable in one step.

Render evidence was reviewed for weight and **kept**: 16.0 MB across six phase sets, against an existing 11.5 MB precedent in `assets/`. It is the artifact that closes v4.2.1 DF-1 and each phase's session history cites its own set, so deleting the intermediate sets would break those citations to save 8.7 MB. Recorded as a deliberate decision, not an oversight.

Resulting evidence tree:

```text
docs/releases/v4/v4.2/development/guide-rebuild/
  design-brief.md          foundations-script.md    hallmark-audit.md
  render-review.md         training-script.md       renders/phase-1..6/
```

## Known-gaps reconciliation

Globbed every ledger in both canonical and legacy layouts:

```text
$ find docs -name "known-gaps.md" | wc -l
31
```

Of the 31, exactly two carry `**Status**: in-progress`: `docs/releases/v4/v4.1/known-gaps.md` and `docs/releases/v4/v4.2/known-gaps.md`. All others are finalized, released, or release-ready.

**This version (`v4.2`)**:

- `## v4.2.1` DF-1 (rendered visual QA) -> **Resolved**. v4.2.2 made rendered browser QA a per-phase gate: 77 screenshots across six phase sets, each with a written verdict, and rendering caught six defects markup tests could not see. The `file://` untrusted-origin item inside DF-1 is void because the warning box was removed by maintainer decision.
- `## v4.2.1` QG-1 (full local suite unfinished) -> **Resolved**, superseded by this phase's completed local run (below).
- `## v4.2.1` gains a "Superseded note" recording that its UI was never published and that T026 was deliberately never run.
- `## v4.2.2` opens with DF-1 (`.html` outside the unicode-sanitize gate), DF-2 (five-person workshop not run - carried honestly from v4.2.1 DF-1 rather than marked satisfied by proxy evidence), and MT-1 (render harness is manual-only by design, so CI never needs a browser download).

**Other in-progress ledger (`v4.1`)**: inspected, not absorbed. Its three open items (DF-1 prompting-profile drift, WN-1 repository description advertising a stale skill count, QG-1 an unfinished local profile run) all belong to the v4.1 line and are untouched by a guide rebuild. No item was silently migrated.

## Living docs architecture

```text
$ python scripts/ci/run.py --profile fast
- docs
  [ok  ] check_docs_conventions (0.2s)
  [ok  ] validate_doc_budgets (0.1s)
  [ok  ] check_memory_integration_budget (0.8s)
  [ok  ] validate_unicode_safety (96.7s)
  [ok  ] validate_no_personal_paths (5.1s)
PASS: 12 passed, 0 failed, 0 skipped, 0 advisory
```

Living roots checked and current: `docs/todos.md` refreshed to this plan and branch each phase; `docs/DEVLOG.md` is a per-release index with no per-phase rows, so it is correctly a no-op until `/update release`; per-phase session histories are written under `development/history/` (six files, one per phase). No `docs/testing/` or `docs/validation/` tree was invented.

`guides/website/README.md` was rewritten in Phase 6 to match the rebuilt architecture and is enforced by `test_website_readme_matches_redesign`.

## Git-tree hygiene

```text
$ python scripts/check_release_preconditions.py --branches --repo-settings
Branch hygiene (merged into origin/develop)
  10 merged branch(es) are cleanup candidates:
    - origin/backmerge/v4.0.0-release
    - origin/backmerge/v4.1.0-release
    - origin/backmerge/v4.1.1-release
    - origin/backmerge/v4.1.2-release
    - origin/feat/v4.1.0-release
    - origin/feat/v4.1.1-adoption-openworker-security-refinement
    - origin/feat/v4.1.1-release
    - origin/feat/v4.1.2-ponytail-planning
    - origin/feat/v4.1.2-release
    - origin/feat/v4.2.0-interactive-guide-redesign
  (11 branch(es) with an open PR were excluded)
  1 branch(es) survive a CLOSED, unmerged PR:
    - origin/backmerge/v3.20.0
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
```

Report only. No branch was deleted; the ten candidates are pre-existing and unrelated to this plan.

## CI/CD coverage

Comparison against the canonical contract, field by field. **This phase changed no pipeline file**, because the comparison found no gap requiring one.

| Contract field | Evidence | Verdict |
|---|---|---|
| Repository-native profiles | `scripts/ci/profiles.py`; `python scripts/ci/run.py --profile fast` runs locally and in CI | PASS |
| Event separation | `on: pull_request: branches: [main, develop]`, `merge_group:`, `workflow_dispatch:` | PASS |
| **Triggers unconditional** | The `on:` mapping contains no `paths:`. Verified directly after a crude grep produced a FALSE POSITIVE that matched a comment on lines 25 and 37. | PASS |
| Path scoping at job level | A `changes` job feeds job-level `if:` conditions - the correct pattern per the project rule | PASS |
| Always-resolving aggregate check | `ci-required` with `needs:` on all nine jobs, `if: always()`, and explicit per-job result assertions rather than bare `needs:` | PASS |
| Required-check coverage | `python scripts/check_required_check_coverage.py` -> `OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally.` (exit 0) | PASS |
| Permissions | `permissions: contents: read` (workflow-level least privilege) | PASS |
| Immutable action references | 2 distinct action refs, **0 not pinned to a 40-char SHA** | PASS |
| Concurrency | `concurrency:` present, cancels superseded runs of the same ref | PASS |
| Runner selection | ubuntu + macos + windows legs (`tests-windows`, `bootstrap-windows`) | PASS |
| Artifact retention / deployment boundaries | Workflow builds and tests only: no upload, no gh CLI, no comments, no pushes | PASS |
| Failure recovery | `ci-required` reports the failing job by name rather than a bare red | PASS |

**Cross-installer parity**: this repository ships two installers (`scripts/installer.sh`, `scripts/installer.ps1`). This plan added no installer-copied artifact - the render harness lives at `tests/guides/tools/render_guide.py`, outside `scripts/`, so no installer edit was required. `tests/installer/` and the installer-smoke jobs are unchanged and green in the fast profile.

**This plan's cumulative CI impact**: one optional dev dependency (Playwright, lazy-imported, proven importable without it by `test_render_harness_imports_without_playwright`), one new non-collected path (`tests/guides/tools/`), and PNG evidence under `docs/`. No new command, env var, secret, or test path that CI must learn about. The rewritten `tests/guides/test_nexus_hub_guide.py` is picked up automatically by the existing `tests` job.

## Goal-vs-codebase review

The plan Goal, restated verbatim:

> A visitor to the published guide experiences a modern, cinematic, interactive four-page site in which every complaint from the 2026-08-29 screenshot review is resolved, Foundations and Training are rebuilt from scratch as animated educational experiences (Training doubling as a fullscreen slide walkthrough with an interactive Glow Booth mockup and a simulated terminal), Cheatsheets explains every command scope in place, and every phase ships with rendered browser evidence -- judged better than both the unpublished v4.2.1 UI and the live pre-4.2.0 site.

Inspected against the file itself, not against phase checkboxes. **17 of 17 clauses satisfied:**

| Goal clause (from the screenshot review) | Artifact in the codebase |
|---|---|
| GitHub icon not cropped or misplaced | `a.nav-gh, .nhg-theme` 36px square, `padding: 0`, canonical octocat path |
| Hero text shares the title's measure | `--measure: 700px` on both `h1` and `.lead`, plus `text-wrap: balance` |
| Copy button slimmer | `.copy-btn { height: 24px }` |
| Warning box and its logic removed | `untrustedCopyWarning` and `isDocumentedGuideOrigin` both absent |
| Windows first, macOS/Linux second | `data-tab="win"` precedes `data-tab="posix"`; `aria-selected="true"` on Windows |
| Verify commands copyable | `data-copy="/skills list"` and `data-copy="/commands"` cells |
| Compact section spacing | `--sec-pad: 32px` (v4.2.x used 54px+) |
| Light-mode logo backdrop | rounded dark chip rule under `html[data-theme="light"] .brand .mark` |
| Foundations: no persistent overlay, no mode selector | 5 `.fx-scene` sections; station/compare/carousel code absent |
| Foundations: animated, with charts | 5 inline SVG diagrams, dash-draw entry, `offset-path` pulses |
| Training: interactive mockup of the example app | booth component reproducing the frozen `captured.length - 1` bug |
| Training: simulated terminal per command | Run affordance plus typed output pane driven by scene data |
| Training: fullscreen slide capability | `requestFullscreen` with an `is-present` overlay fallback |
| Cheatsheets: no meaningless band labels | "Band 1" / "Band 2" absent |
| Cheatsheets: per-scope descriptions | **79** documented scopes, anti-drift-tested against `catalog/commands/` |
| Rendered evidence per phase | **77** screenshots across 6 phase sets |
| Single self-contained offline file preserved | no runtime network references; 377 KB against a 500 KB budget |

**Gaps**: none blocking. Two honest limits are recorded as known gaps rather than claimed: DF-2 (no five-person workshop cohort exists, so that validation is genuinely un-run) and DF-1 (`.html` sits outside the unicode-sanitize gate, which is a repo-wide validator limitation, not a defect in this work).

**The comparative clause** ("judged better than both") is the one clause a script cannot settle. It is put to the maintainer in human testing below, with the rendered evidence and the baseline recovery command supplied so the comparison is direct.

## Human/manual testing suggestions

Automated checks cover structure, contrast, keyboard reachability, reduced motion, and the simulated interactions. These need a person:

1. **The comparative judgement.** Open the rebuilt guide beside the live site (`git show v4.1.2:guides/website/nexus-hub-guide.html > /tmp/old.html`) and confirm the rebuild is the better experience. This is the plan Goal's only subjective clause.
2. **Real-device touch.** Training's booth and pose buttons, and Present mode, on a phone and a tablet. The harness renders at 420px but does not touch.
3. **Fullscreen for real.** Headless Chromium denies the Fullscreen API, so only the overlay fallback was exercised. Press Present in a real browser and confirm true fullscreen, then Escape.
4. **Lighthouse Accessibility** in both themes, target >= 90. Contrast and keyboard were measured directly, but Lighthouse checks things this sweep did not.
5. **Cross-browser and platform fonts.** Firefox and Safari, and the system font stack on macOS - all rendering evidence here is Chromium on Windows.
6. **Clipboard.** Copy buttons under a real browser permission prompt, and the `execCommand` fallback path.
7. **The published copy.** After deploying to the portfolio host, confirm the page renders identically and that no warning box appears (its removal is the fix for the host never having been allowlisted).
8. **Workshop (DF-2).** Five people through the eight-step walkthrough, if a cohort becomes available. Not run; not claimed.

## Full-suite testing and stabilization

Guide suite:

```text
$ python -m pytest -q tests/guides/test_nexus_hub_guide.py
55 passed, 1 skipped in 0.35s
```

Fast repository profile:

```text
$ python scripts/ci/run.py --profile fast
PASS: 12 passed, 0 failed, 0 skipped, 0 advisory in 6.1s
```

Full repository suite, run to completion:

```text
$ python -m pytest -q tests
................................................................ [ 66%]
...
..sssss.ss.ss.....s.sss                                                  [100%]
3513 passed, 38 skipped in 3037.47s (0:50:37)

[exited with code 0]
```

**0 failures across 3,513 tests.** This is the local gate the plan requires before publication, and it is what closes v4.2.1's QG-1 (which existed only because that session's run never finished). The refactor in this phase deleted one redundant documentation file and changed no code; the suite confirms no behavior moved.

## Publication and integration

### Push 1 - 2026-08-29

Approved by the maintainer, then pushed once. PR [#146](https://github.com/bendourthe/Nexus-Hub/pull/146) opened against `develop` (never against `main`).

First run: **18 of 20 checks passed; `validate` failed, cascading to `ci-required`.**

```text
$ gh pr checks 146
ci-required                   fail   4s
validate                      fail   28s
bootstrap (macos-latest)      pass   1m46s
bootstrap (ubuntu-latest)     pass   2m1s
bootstrap-windows             pass   3m4s
changes                       pass   8s
colocation                    pass   6s
detect                        pass   10s
install-smoke (macos-latest)  pass   11s
install-smoke (ubuntu-latest) pass   10s
install-smoke (windows-latest) pass  27s
installer-smoke (macos-latest) pass  12s
installer-smoke (ubuntu-latest) pass 9s
installer-smoke (windows-latest) pass 28s
shellcheck                    pass   23s
tests                         pass   10m12s
tests-windows                 pass   10m34s
verify                        pass   2s
render                        skipping
```

The aggregate behaved exactly as the contract intends: `ci-required` turned red because a needed job failed, rather than reporting green off a bare `needs:`.

**Failure classified: IMPL, inherited.**

```text
$ gh run view --job 99175355325 --log-failed
fix end of files.........................................................Failed
- hook id: end-of-file-fixer
- exit code: 1
- files were modified by this hook

Fixing docs/releases/v4/v4.2/docs-cleanup-report.md
```

**Reproduced locally before any re-push** (the rule is never to re-run a red check on a guess):

```text
develop version trailing newline bytes: 1
this branch                            : 4   (a trailing blank line, CRLF file)

$ git log --oneline origin/develop..HEAD -- docs/releases/v4/v4.2/docs-cleanup-report.md
89e8e3dc docs(v4.2.1): record last-phase visual-education evidence
... (7 v4.2.1 commits; NO v4.2.2 commit touches this file)
```

**Root cause**: the defect was introduced by the v4.2.1 commits, which ride along in this PR because the branch was cut from the never-merged v4.2.1 head. v4.2.1 never reached CI, so `end-of-file-fixer` had never seen the file. None of the v4.2.2 work touched it. This is precisely the risk surfaced to the maintainer before the push was approved.

**Blast-radius check before fixing** - scanned all 47 text files this PR delivers for the same class of defect, so the fix would not become a fix-and-fail loop:

```text
files checked: 47
MISSING final newline:      none
EXTRA trailing blank lines: [('docs/releases/v4/v4.2/docs-cleanup-report.md', 4)]
TRAILING whitespace:        none
```

Exactly one file affected. **Narrow fix applied**: normalized to a single trailing `\r\n`, preserving the file's own CRLF endings (the `mixed line ending` hook passes on CRLF). No content changed.

### Push 2 - v4.2.3 folds in

Maintainer decision 2026-08-29: rather than pushing the v4.2.2 stabilization fix on its own, the v4.2.3 refinement plan was implemented on the same branch. PR #146 will therefore deliver v4.2.2, its fix, and all of v4.2.3 in one merge. Nothing was ever published, so no user saw an intermediate state.

See the v4.2.3 sections below for that plan's own last-phase evidence.

---

# v4.2.3 guide-refinement - last-phase evidence

**Date**: 2026-08-29
**Plan**: `docs/releases/v4/v4.2/plans/v4.2.3-guide-refinement.md`
**Phase**: 7 of 7
**Branch**: `feat/v4.2.2-guide-cinematic-rebuild` (shared with v4.2.2 by maintainer decision)

## Architecture refactor

```text
$ find guides docs/releases/v4/v4.2 -type d -empty
(no output)
```

**Render-evidence consolidation.** Evidence had grown to 38.4 MB across twelve phase sets, against an 11.5 MB precedent in `assets/`, in a repository users clone. Decided deliberately (the plan's T025 asks for a decision either way) and applied:

```text
before: 38.4 MB across 12 sets
removed 30.3 MB of superseded standard sweeps
after:   8.1 MB
```

Kept: the final full sweep (`renders/v423-phase-6/`, 24 captures) and all six captures that exist nowhere else - reduced motion, present mode before and after a run, and the diagram and command crops. Removed: superseded 24-shot sweeps, including all six v4.2.2 sets, which document pages this release then rewrote. Every pruned image remains in git history at the commit that added it, and both render-review files carry a note recording the consolidation, so no citation dangles silently.

## Known-gaps reconciliation

Two ledgers carry `Status: in-progress`: `docs/releases/v4/v4.1/known-gaps.md` and `docs/releases/v4/v4.2/known-gaps.md`.

- A `## v4.2.3` section carries v4.2.2's three gaps forward honestly rather than closing them by assertion: DF-1 (`.html` outside the unicode-sanitize gate), DF-2 (no five-person workshop cohort exists), MT-1 (render harness is manual-only by design).
- DF-1 earned a concrete illustration this cycle: writing the v4.2.3 plan introduced a stray CJK character that `validate_unicode_safety.py` scanned and passed, because it flags invisible characters and smart punctuation, not a valid-but-wrong-script glyph. A separate scan caught it. The gap is real and now has evidence.
- v4.1's three open items were inspected and deliberately not absorbed.

## Living docs architecture

```text
$ python scripts/ci/run.py --profile fast
PASS: 12 passed, 0 failed, 0 skipped, 0 advisory
```

`docs/todos.md` was refreshed to this plan at Phase 1 and ticked each phase. Six session histories written, one per phase. `guides/website/README.md` updated in Phase 6, including four stale statements corrected in sections this plan did not otherwise touch. No `docs/testing/` or `docs/validation/` tree invented.

## Git-tree hygiene

```text
$ python scripts/check_release_preconditions.py --branches --repo-settings
  (12 branch(es) with an open PR were excluded)
  1 branch(es) survive a CLOSED, unmerged PR:
    - origin/backmerge/v3.20.0
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
```

Report only. The one flagged branch is pre-existing and unrelated.

## CI/CD coverage

```text
$ python scripts/check_required_check_coverage.py
Required-check coverage: OK -- 10 declared context(s) across 2 branch(es),
every one produced unconditionally.
```

**No pipeline file changed.** The v4.2.2 field-by-field comparison against the canonical contract concluded PASS on all twelve fields, and nothing in v4.2.3 alters any of them: no new command, dependency, environment variable, secret, test path, or artifact. The rewritten test module and the pruned render PNGs both sit inside paths the existing `tests` job already collects.

Per the plan's explicit warning, the workflow-level `paths:` check was read from the `on:` mapping directly rather than grepped, since a naive grep matches the explanatory comments in `ci.yml` and produced a false positive in v4.2.2. The trigger block carries no path filter.

## Goal-vs-codebase review

The plan Goal restated: every defect from the 2026-08-29 second review resolved - fluid text, bare copy icons, a readable verify block, an animated comparison, project-generic Foundations with repaired and consistently-ordered diagrams, a full-screen Training present mode with icon controls and loop-stage progress, Cheatsheets terminal usage with commands coloured apart from arguments, and correctly scaled page-nav buttons - all verified by rendered screenshots before each commit.

Inspected against the file itself, item by item, as if this agent had not implemented the phases. **19 of 19 review items satisfied, 0 outstanding:**

| Review item | Artifact |
|---|---|
| Text fills the page, no hardcoded width | no `--measure`, no `ch` cap; `.container --maxw` is the only constraint |
| Copy icon not a bubble in a bubble | `.copy-btn--bare`, transparent and borderless, inside `.cmd-cell` hosts |
| Verify segment readable | `.verify-steps`, two numbered steps, one type size |
| Comparison visual and animated | `nhg-compare` gone; six animated rows with drawing connectors |
| Foundations numbers removed | no `.fx-num` markup |
| Project-generic, not coding-only | no coding-only vocabulary in Foundations teaching copy |
| Arrowheads are full chevrons | closed filled `.fx-head` paths; `fx-arrow` gone |
| Loop labels clear and differentiated | dim uppercase role over plain-weight detail |
| Dots pass behind the boxes | every pulse declared before its node groups |
| Clear with/without difference via colour | amber unaided vs accent harnessed, across nodes and connectors |
| Without first, with second | unaided state leads in both comparisons |
| Present mode uses the screen | full-height flex column, measured 823 of 900 px |
| Top-right text is clear | "Understand . 1 of 8 . /describe full"; no step/beat jargon |
| Controls bottom-right, icons | icon cluster after the takeaway, right-aligned |
| Progress shows the loop stage | eight labelled stages, current marked with `aria-current` |
| Cheatsheets single column | no `grid-template-columns` on `.cs-scopes` |
| Terminal illustration for usage | 21 usage terminals, one per command |
| Command coloured apart from argument | `.inv-cmd` accent, `.inv-arg` plain ink |
| Nav buttons fit their text | `flex: 0 0 auto`; the 260 px slab is gone |

**Gaps**: none blocking. The three carried gaps above are recorded rather than claimed closed.

## Human/manual testing suggestions

Automated checks now cover structure, contrast, keyboard reachability, reduced motion, and the simulated interactions. These still need a person:

1. **The comparative judgement.** Whether the refined guide is now shippable. That is the question this cycle exists to answer, and no script settles it.
2. **Real-device touch.** The booth, the new bottom-right icon controls, and the loop-stage segments on a phone and a tablet. The harness renders at 420 px but does not touch.
3. **True fullscreen.** Headless Chromium denies the Fullscreen API, so only the overlay fallback is ever exercised automatically. Press Present in a real browser, then Escape.
4. **Lighthouse Accessibility** in both themes, target >= 90.
5. **Cross-browser and platform fonts.** Firefox and Safari, and the macOS system font stack. All rendering evidence is Chromium on Windows.
6. **Clipboard** behind a real permission prompt, including the bare-icon variant, which no longer has a chip to signal it is a button.
7. **Long-line readability.** The maintainer chose container-filling text over a measure. Worth reading a full paragraph at 1920 px to confirm the choice still feels right at the widest common desktop.
8. **Workshop (DF-2).** Five people through the walkthrough, if a cohort becomes available. Not run; not claimed.

## Full-suite testing and stabilization

Guide suite:

```text
$ python -m pytest -q tests/guides/test_nexus_hub_guide.py
73 passed, 1 skipped
```

Fast repository profile:

```text
$ python scripts/ci/run.py --profile fast
PASS: 12 passed, 0 failed, 0 skipped, 0 advisory
```

Full repository suite, run to completion:

```text
$ python -m pytest -q tests
....................sssss.ss.ss.....s.sss                                [100%]
3531 passed, 38 skipped in 3192.61s (0:53:12)

[exited with code 0]
```

**0 failures across 3,531 tests** (18 more than v4.2.2's 3,513, the net of this release's new guards). The only non-test change in Phase 7 was deleting superseded PNGs; the suite confirms no behavior moved.

## Publication and integration

Pending: sub-task 7.9, after explicit maintainer approval. This push UPDATES the existing PR #146 rather than opening a new one, and carries v4.2.2, its stabilization commit `f4203850`, and all of v4.2.3.
