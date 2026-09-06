# Session History - Docs Lifecycle and Retention Phase 1: DEVLOG Conversion and Archive

**Date**: 2026-08-21
**Branch**: `feat/docs-lifecycle-retention`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.0-docs-lifecycle-retention.md`](../../plans/v3.18.0-docs-lifecycle-retention.md)
**Phase**: 1 - DEVLOG conversion and archive
**Environment**: Windows 11, Git Bash and PowerShell, Python 3.12, pytest; GNU Make unavailable, so `make` targets were executed as their constituent commands
**Outcome**: `docs/DEVLOG.md` is a 99-line per-release index against a 150-line gate. The prior 5,615-line body is archived and verified content-identical against git's own object. Every reference that described DEVLOG as a narrative log now describes the index. One pre-existing environment-dependent test failure was found and is unrelated to this phase.

## 1. Starting State

- **Starting commit**: `be7cc4ff` (`Merge pull request #71 from bendourthe/docs/relocate-plans-and-colocation-gate`)
- **Branch created**: `feat/docs-lifecycle-retention` off `develop`, per the develop+main model
- **Worktree**: clean
- **`docs/DEVLOG.md`**: 5,615 lines, 342 `## [` entry headings, roughly 208,000 words. The plan's design inputs recorded 3,149 lines as of 2026-08-18; the file had grown by 2,466 lines in three days, which is the growth rate the phase exists to stop.

The plan recorded `strong / medium` for this phase. Implementation-time routing confirmed that intent: the session model (Opus 5) is the `strong` tier in the plan's own current model map, so no switch was needed and none was made.

## 2. Plan Reconciliations Made Before Implementing

The plan was retargeted from v3.17.10 to v3.18.0 on 2026-08-21 and warns that body text may still cite the old version. Two citations needed reconciling, and one plan instruction conflicted with a repo convention:

1. **Decision-record path.** The plan specifies `docs/decisions/accepted/policy/...`. `docs/decisions/README.md` defines a closed lifecycle set of `proposed` / `implemented` / `rejected`, with no `accepted`. Since this phase ships the decision, the record was filed at `docs/decisions/implemented/policy/2026-08-18-devlog-index-conversion.md`. The filename date is kept at the plan's 2026-08-18 (the date the decision was made) per the README's rule that the date is the decision date, not the authoring date.
2. **Archive filename.** The plan names `docs/archive/DEVLOG-v0-v3.17.md`. The latest release is v3.17.6, so the name still describes its contents correctly and was kept unchanged.
3. **Prerequisite.** The plan requires v3.17.5 released and merged. v3.17.6 is released and merged, so the prerequisite is satisfied with margin and the archived body includes the final v3.17.6 entry.

## 3. Chronological Steps

### 3.1 Decision record (sub-task 1.1)

Wrote the record with the mandatory `## Alternatives considered` and `## Consequences` sections. Five alternatives are recorded, the fifth being the one that changed the design: a per-release line for **all** 134 releases lands at roughly 148 lines against a 150-line gate, so the very next release after the conversion would breach it. That is what drove the decision to collapse the pre-canonical era rather than enumerate it.

`scripts/validate_decision_records.py` reported 11 records OK.

### 3.2 Archive with verified content preservation (sub-task 1.2, first half)

Wrote `docs/archive/DEVLOG-v0-v3.17.md` as a three-line provenance header (archive date, decision-record link, covered version range) followed by the original bytes read in binary mode, then verified by slicing the header back off and re-hashing: SHA-256 `5f22f842e12909b5a075f11d0a1b9396a7754629596a953c6fe42bd9ea7f2989` on both sides.

That check was later re-run against a stronger reference after an unrelated incident (see section 5) and confirmed content-identical to `git show HEAD:docs/DEVLOG.md` under line-ending normalization, at SHA-256 `a5b622dccd65b2dd51a8e3a80d92b7ac4be61848de17f1fef893c72ae5fc8f4a`. The raw bytes differ from the committed blob only in line endings, which is the same LF-in-repo / CRLF-in-worktree relationship every tracked file in this repository has on Windows.

### 3.3 Index rewrite (sub-task 1.2, second half)

The index is derived, not typed. Dates and the release set come from the `## [x.y.z] - YYYY-MM-DD` headings in `CHANGELOG.md`; the plan, history, and gaps links are resolved against the on-disk per-version tree, so a link is emitted only where its target exists. Three link-column outcomes were needed:

- A version-prefixed plan file exists (`v3.17.6-ci-gate-and-branch-hygiene.md`): link the file, labelled by its slug.
- No version-prefixed plan exists, because plan filenames before the v3.14 era were slug-only and cannot be mapped to a specific patch release without reading each one: link the minor version's `plans/` directory. This is the honest option; guessing a specific file would have produced a resolving link to possibly the wrong plan.
- No per-version tree at all (pre-v3): link the archive.

Summaries had to be authored rather than extracted. The CHANGELOG carries no one-line summary per release, and mechanical extraction of the first bold lead produced unusable text for eight releases, including five where the lead phrase is the literal word "Activation:". Each summary was written from the release's DEVLOG entry title, plan slug, and CHANGELOG lead taken together.

Result: 99 lines. 70 individual v3 rows, 19 collapsed pre-v3 minor rows, 232 links, all of which resolve on disk. The generator script is a one-off and deliberately not shipped; Phase 2 owns the self-sustaining tooling.

### 3.4 Reference corrections

Corrected four references that described DEVLOG as a narrative surface:

- `README.md`, documentation-surfaces pointer: "narrative-style updates on what changed and why" became a description of the index, with the archive linked alongside and CHANGELOG named as the authoritative change record.
- `README.md`, release-flow step 1: "DEVLOG entry" became "the DEVLOG index line".
- `guides/reference/TOKEN_OPTIMIZATION.md`: session context is restored from the version's `development/history/` files, not from DEVLOG.
- `catalog/skills/workflow/dev-progress-tracker/SKILL.md` (two places): rationale belongs in a decision record or ADR, not DEVLOG.

**Deliberately not changed**, because Phase 2 owns every writer: `catalog/skills/workflow/devlog-generation/`, `catalog/commands/update.md`, `catalog/skills/project-setup/setup-project/`, `catalog/agents/doc-updater.md`, and `catalog/hooks/auto-devlog.{sh,ps1}`. Also not changed: `docs/v*/**/history/`, `docs/v*/**/plans/`, and past `CHANGELOG.md` entries, which are historical records of what was true when written and must not be retconned.

## 4. Verification

| Check | Result |
|---|---|
| `docs/DEVLOG.md` line count | 99, against a 150-line gate |
| Archive content preservation | Content-identical to `HEAD:docs/DEVLOG.md` (normalized SHA-256 match) |
| Index link resolution | 232 links, 92 unique, 0 broken |
| Deep links into DEVLOG anchors | none exist repo-wide, so no anchor was orphaned |
| `validate_decision_records.py` | PASS, 11 records |
| `validate_skills.py --bundles-only` | PASS, 273 skills, 0 errors, 0 warnings |
| `validate_unicode_safety.py --strict` | PASS repo-wide, and per-file on the index, decision record, and CHANGELOG |
| `validate_doc_budgets.py` | PASS, 8 budgeted docs within ceiling |
| `check_registry_entries.py --check --strict` | PASS |
| `check_version_sync.py` | PASS, 3.17.6 consistent |
| `check_base_template_parity.py` | PASS |
| `check_doc_colocation.py` | PASS across docs/v3 and docs/v4 |
| `validate_no_personal_paths.py`, `scan_supply_chain_iocs.py` | PASS |
| `pytest tests` | 2,870 passed, 29 skipped, **1 failed** (pre-existing, see below) |
| `pytest catalog/hooks/tests` | 1,013 passed, 36 skipped, 0 failed |
| CI | no change needed; no workflow references DEVLOG and this phase adds no new check |

`--fix` was deliberately not passed to the Unicode validator. It reported nothing to fix, and a bulk `--fix` pass is known to repair prose while permanently destroying double-encoded text, so running it on a clean result would be risk with no benefit.

### The one test failure

`tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` fails locally. `install.ps1` in standalone mode shells out to `tar`, which on this host resolves to Git Bash's `/usr/bin/tar` because the test invokes PowerShell from a Git Bash session; it then fails to decompress the test's stub tarball with "unexpected end of file / Child returned status 128".

This is not caused by this phase. The diff is seven documentation files; the failing path reads `install.ps1`, `scripts/installer.ps1`, and a stub tarball built in a temp directory, none of which were touched. It is an environment-dependent failure of the same class this repository has now been bitten by twice: a bare tool name on Windows resolving through PATH to the wrong binary (v3.15.6 Phase 4 and v3.17.6 Phase 6, both `bash` resolving to the WSL stub). It is recorded here for Phase 5's known-gaps reconciliation rather than fixed in scope.

An attempt to prove the failure pre-existing by stashing and re-running is what triggered the incident in section 5, and the proof was abandoned in favor of the diff-scope argument above.

## 5. Incident: a partially-failed `git stash -u`

`git stash -u`, run to test the failure against a clean tree, aborted partway with `warning: failed to remove Microsoft/Windows/PowerShell: Permission denied`. It created the stash entry but left the working tree unchanged, so the subsequent `git stash pop` refused to apply over "local changes" that were in fact the same changes.

State was verified before doing anything else: HEAD still `be7cc4ff` on the feature branch, all seven files present and correct, and the archive re-verified against the git blob. Nothing was lost. The only residue is `stash@{0}`, a redundant duplicate of the intact working tree, which was **left in place** rather than dropped, because dropping a stash is destructive and the tree it duplicates is already safe.

The blocking path is a stray empty `Microsoft/Windows/PowerShell` directory in the repo root, created as a side effect of the PowerShell installer tests. Git does not track empty directories, so it never appears in `git status`. Phase 5's layout refactor is where it belongs.

Two lessons worth carrying:

1. **Do not use `git stash` as a verification technique in this working tree.** OneDrive-backed directories can be locked mid-operation, and this repository's project memory already records a case where an aborted checkout corrupted a release tag. Use a diff-scope argument, a separate clone, or a worktree instead.
2. **`pytest -q ... | tail -N` produces no output until the run ends.** The first attempt at the suite was piped to `tail`, so 30 minutes of a 46-minute run looked indistinguishable from a hang, and the run was killed and restarted for no reason. Redirect to a file and tail the file.

## 6. Ending State

- **Files added**: `docs/archive/DEVLOG-v0-v3.17.md`, `docs/decisions/implemented/policy/2026-08-18-devlog-index-conversion.md`, this history file
- **Files modified**: `docs/DEVLOG.md` (rewritten), `README.md`, `CHANGELOG.md`, `guides/reference/TOKEN_OPTIMIZATION.md`, `catalog/skills/workflow/dev-progress-tracker/SKILL.md`
- **Catalog counts**: unchanged at 273 skills, 18 commands, 31 hooks, 23 agents
- **Stability gate**: met. Archive holds the prior body with content preservation proven, the index is 99 lines, the decision record exists and validates, and every repo reference to DEVLOG resolves.

## 7. Next Steps

1. **Phase 2 is the one that matters, and it is now urgent rather than merely next.** Every writer of DEVLOG still emits the narrative format. The opt-in `auto-devlog` hook parses `^## \[` to find the last entry date; the index has no such heading, so a user with `AUTO_DEVLOG=1` set would have a narrative entry prepended into the index. It is off by default, but until Phase 2 lands, the format is held only by the decision record and by whoever reads it.
2. Phase 3 (AGENTS.md MT-1 ratchet-down) is independent of Phases 1 and 2 and can proceed in either order.
3. Phase 4's retention policy references this index as the navigation surface, so it depends on this phase.
4. Carry the `test_ps_standalone_extracts_and_hands_off` PATH failure and the stray `Microsoft/` directory into Phase 5's known-gaps reconciliation.
