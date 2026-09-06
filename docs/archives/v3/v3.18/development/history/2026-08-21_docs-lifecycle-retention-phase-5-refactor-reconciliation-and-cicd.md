# Session History - Docs Lifecycle and Retention Phase 5: Refactor, Reconciliation, and CI/CD

**Date**: 2026-08-21
**Branch**: `feat/docs-lifecycle-retention`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.0-docs-lifecycle-retention.md`](../../plans/v3.18.0-docs-lifecycle-retention.md)
**Phase**: 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD (terminal phase)
**Environment**: Windows 11, Git Bash and PowerShell, Python 3.12, pytest, ShellCheck; GNU Make unavailable, so `make` targets were executed as their constituent commands
**Outcome**: The first retention archive pass is executed (216 files, 75 files of reference repair), and executing it corrected the policy it was implementing. Known gaps are reconciled with zero release blockers. CI gained one advisory step; its optimization is a deliberate no-op for a reason worth recording.

## 1. Starting State

- **Starting commit**: `2e9455d3` (Phase 4: the retention policy and its advisory checker)
- **Worktree**: clean
- **`scripts/check_docs_retention.py`**: reporting 16 versions, 306 files due for archival
- **Routing decision**: the plan recorded `frontier / max`. Implementation ran on Opus 5 (`strong`), with the delta surfaced and the switch keystroke printed rather than silently accepted.

## 2. The Archive Pass Was a User Decision, Not a Default

Phase 5.1 names the archive pass as "this version's natural candidate", and the plan specifies propose-then-apply. Three options were presented with a plain-language walkthrough of what the pass does, what it risks, and a recommendation to defer:

1. Defer to its own change (recommended, on OneDrive-hazard grounds)
2. Execute now in this branch
3. Execute a partial pass

**The user chose to execute now.** The recommendation to defer was recorded, overruled, and the work proceeded. The deferral reasoning is preserved in the decision record's Consequences, because the OneDrive hazard is real regardless of this particular pass succeeding.

Phase 4 was committed first, deliberately, so a 306-file move had a clean revert point immediately behind it.

## 3. What Executing It Found

The plan and the Phase 4 policy both said "archive the `development/` subtree". Building the inbound-reference index **before** moving anything, which is the whole point of propose-then-apply, returned **227 occurrences across 128 files**. Counting them would have been useless; reading them was decisive:

| Reference kind | Example | Consequence of archiving |
|---|---|---|
| CI `run:` step | `.github/workflows/presentify-extractor.yml` executes `docs/v3/v3.12/development/fixtures/gen_fixtures.py` and five siblings | **CI breaks outright** |
| Shipped hook comment | `catalog/hooks/_notify_common.{sh,ps1}` cites `docs/v3/v3.15/development/end-of-task-notification-contract.md` | A shipped code citation dangles |
| Test skip message | `tests/workflows/test_cursor_usage_monitor_workflow.py` names `cursor-usage-live-smoke.md` | A test's guidance points nowhere |
| Documentation link | plans, known-gaps, session histories | Ordinary link repair |

`development/` in this repository is not only per-phase working notes. v3.9, v3.12, and v3.13 hold `fixtures/` and `worked-example/` trees with 68 non-Markdown files between them, six of which CI executes directly. v3.15 holds eleven contract documents that shipped hooks and tests reference by path.

**So the rule narrowed: the unit that ages out is `development/history/`, not `development/`.** That correction is the most valuable output of the phase. It is now stated in four places so it cannot be widened back by accident: the policy (with a table naming each category that stays and why), the checker's `AGING_SUBDIR` comment, the decision record's Consequences, and a dedicated test (`test_non_history_development_content_is_never_reported`).

A retention rule that silently archived live CI inputs would have been a worse outcome than having no rule at all, because the failure would have surfaced as a red CI run on an unrelated change weeks later.

## 4. The Move

216 files, 16 versions, `git mv` one version at a time with a per-version file-count assertion rather than one bulk operation. All 16 reported OK with matching counts.

Reference repair: **75 files**, via a one-off script that handled two link shapes, because they are genuinely different:

- Repo-root paths (`docs/v3/v3.9/development/history/...`), used everywhere
- Docs-relative paths (`](v3/v3.9/development/history/`), used only by `docs/DEVLOG.md`, whose links resolve against `docs/`

Version strings were processed **longest-first**, so `v3.1` could not shadow `v3.15` or `v3.10`. Getting that wrong would have produced `docs/archive/v3/v3.15` for some rows and a mangled `docs/archive/v3/v3.1` + `5` for others, and the damage would have looked like a typo rather than a systematic error.

The single largest repaired artifact was `docs/DEVLOG.md`: **54 of its rows**, the history links for every archived version, in the index built three phases earlier. That is the reference-repair cost the policy warned about, paid on the policy author's own artifact.

Nine `development/` directories were left empty and removed. No empty directory remains in the tracked tree.

## 5. Layout Refactor (5.1)

Beyond the archive pass:

- **Removed the stray `Microsoft/Windows/PowerShell` tree** (zero files) and added `/Microsoft/` to `.gitignore`. It is created by the installer and hook suites invoking `powershell.exe` with the repo as CWD. Git does not track empty directories, so it never appeared in `git status` while still being real enough to abort this plan's Phase 1 `git stash -u` with a permission error.
- **No duplicate or orphan documentation** in scope. Both files created by the Phase 3 and Phase 4 relocations are linked from `AGENTS.md`.
- The other empty directories found (`.antigravitycli`, `.claude/worktrees`, `.nexus-hub/`, `node_modules/.vite-temp`) are all gitignored local artifacts and were left alone.

## 6. Known-Gaps Reconciliation (5.2)

`docs/v3/v3.18/known-gaps.md` opened with nine items: 3 resolved here or in earlier phases, 6 open with an explicit disposition, **0 release blockers**. v3.17's MT-1 was ingested and closed by Phase 3.

## 7. CI/CD (5.3), and a Trap in the Plan's Own Prompt

**Added**: one advisory step running `check_docs_retention.py` in the `validate` job. It sits inside the existing job rather than in a new one, so no new required status context is created. It mirrors the `make validate` step of the same name, which is a stated convention of that job.

**Optimization: a deliberate no-op**, and this needs saying because the plan's prompt actively suggests the wrong thing. Phase 5.3 says to reduce action minutes via "path filters, concurrency cancel-in-progress, dependency caching, gating expensive-OS or matrix jobs". Following the first item literally would **re-introduce the exact antipattern v3.17.6 removed at the cost of six administrator bypasses**: GitHub leaves a required check from an untriggered workflow Pending forever, so an event-level `paths:` filter makes a required check unsatisfiable. `AGENTS.md` has a whole section on this and `scripts/check_required_check_coverage.py` exists to prevent it.

The audit found the optimizations already correct and in place:

| Optimization | State |
|---|---|
| Event-level path filters | **Deliberately absent** (the antipattern) |
| Job-level `if:` gating | 7 of 10 jobs |
| `concurrency` with `cancel-in-progress` | Present |
| Dependency caching | `validate` and `tests` |
| `ci-required` aggregate | Present, replacing 10 per-leg contexts with 5 |

`check_required_check_coverage.py` passes: 10 declared contexts across 2 branches, every one produced unconditionally.

## 8. Cross-Installer Parity (5.4)

`check_installer_parity.py`: PASS. `check_docs_retention.py` appears in neither installer and is listed in `DEV_ONLY_SCRIPTS`, so the no-copy rule is asserted rather than assumed.

One plan correction: 5.4's prompt states this plan "adds one repo-internal script under DEV_ONLY_SCRIPTS and no distributed artifacts". It actually changed **14** distributed catalog artifacts (the `devlog-generation` bundle, `update.md`, `doc-updater.md`, both `auto-devlog` siblings, three cross-linked skills, and the setup-project skill). None require an installer edit because they are folder-auto-copied, which is presumably what the prompt meant, but the claim as written is inaccurate.

## 9. Verification

| Check | Result |
|---|---|
| `git mv` per version | 16/16 OK, file counts matched |
| Files moved | 216 |
| Reference repair | 75 files; **0** dangling references to moved paths repo-wide |
| `docs/DEVLOG.md` | 92 unique links, **0 broken**; 54 rows repointed at the archive; 0 still pointing at the moved-away paths |
| Every workflow-referenced `docs/` path | 13/13 resolve |
| Every hook / extension-referenced `docs/` path | 3/3 resolve |
| Empty directories in the tracked tree | 0 (10 removed) |
| All 22 `make validate` validators | PASS |
| `check_docs_retention.py` | exit 0, nothing due |
| `check_installer_parity.py` | PASS |
| `check_required_check_coverage.py` | PASS, 10 contexts, all unconditional |
| `pytest tests catalog/hooks/tests` (full, including installer) | **3,919 passed, 65 skipped, 1 failed** |

**The one failure is WN-1**, `test_ps_standalone_extracts_and_hands_off`, which was already failing before this plan began and is recorded as pre-existing in the Phase 1 history. During this phase its root cause was **proven rather than assumed**, by reproduction:

```text
tar (child): Cannot connect to C: resolve failed
gzip: stdin: unexpected end of file
/usr/bin/tar: Child returned status 128
```

GNU tar (the one Git Bash puts on PATH) parses a Windows drive-letter path as a remote `host:path` specification, so `tar -xzf a drive-letter path` attempts to connect to a host named `C`. The "unexpected end of file" is downstream noise from the gzip child, which is why the error has read as a corrupt archive rather than a path-parsing problem. Windows ships bsdtar at `System32\tar.exe`, which handles drive letters correctly.

This is the **third** instance in this repository of a bare tool name on Windows resolving through PATH to the wrong binary; the other two are `bash` finding the System32 WSL stub, documented in v3.15.6 Phase 4 and re-diagnosed from scratch in v3.17.6 Phase 6. The fix follows immediately after this commit, per the user's instruction to address the known gaps.

## 10. Ending State

- **Files added**: `docs/v3/v3.18/known-gaps.md`, `docs/v3/v3.18/docs-cleanup-report.md`, this history file
- **Files moved**: 216, from `docs/v3/v3.<MINOR>/development/history/` to `docs/archive/v3/v3.<MINOR>/development/history/`
- **Files modified**: 75 for reference repair, plus `.github/workflows/ci.yml`, `.gitignore`, `scripts/check_docs_retention.py`, `docs/policy/docs-retention.md`, the retention decision record, `tests/validators/test_check_docs_retention.py`, `CHANGELOG.md`, `docs/todos.md`
- **Directories removed**: 10 empty (9 from the move, 1 test artifact)
- **Catalog counts**: unchanged at 273 skills, 18 commands, 31 hooks, 23 agents
- **Stability gate**: met. The layout is clean, gaps are reconciled with zero blockers, CI covers every change and is verified optimal, and the suite is green apart from the one pre-existing failure now root-caused and queued for fix.

## 11. Next Steps

1. Commit and push (the first push of this plan; Phases 1-4 were committed locally only, by instruction).
2. Address the open known gaps: WN-1 (the `tar` resolution, root cause proven above), DF-2 (SKIP clauses feeding the routing scorer positive vocabulary), DF-3 (anchor links orphaned by relocation), and a decision on MT-2 (the DEVLOG line ceiling's home).
3. Hand off to `/update release` for the version bump, changelog finalization, tag, and GitHub Release.
