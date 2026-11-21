# Centralized Worktrees Phase 1

**Version**: v4.15.6
**Phase**: 1, Inventory and Identity
**Base**: `e6f53fa04ca814521a6b04616afb875a328380fd`
**Worktree**: `~/.worktrees/nexus-hub/v4.15.6`

## Subtasks

| Task | Outcome |
|---|---|
| T001 | Queue refresh, baseline, frozen command contract and fixture list appended to `v4.15.6-worktree-policy-review.md` (the planning review that already existed was kept; the implementation baseline is a new section at its end). |
| T002 | `scripts/nexus_worktrees.py`: root policy, name sanitizing, repository identity from the canonical Git common directory, relocation and copy handling, destination checks. |
| T003 | Resumable read-only discovery with a coverage ledger, a non-executing Git profile, per-directory read timeouts, concurrent registry reads and progress lines. |
| T004 | `tests/validators/test_worktree_policy.py` (43 tests), live read-only audit, this history, one local commit. |

## Evidence

Focused tests: `python -m pytest tests/validators/test_worktree_policy.py -q` gave 43 passed. They cover names (Windows reserved names, Unicode, case, truncation), root refusals (relative, UNC, inside a repository, tool directory, Nexus-Hub home, synchronized folder, traversal, unmounted volume, malformed config), identity (same basename, copied repository, relocated main repository, conflicting mapping), and discovery on synthetic main, linked, bare, submodule, unregistered, dangling and malformed fixtures. Each audit result is compared with `git worktree list --porcelain -z` for the same repository (equal sets), and a full tree snapshot before and after the audit is identical (no file written, no mtime changed).

Hostile Git configuration: a fixture sets `filter.*.clean/smudge`, `core.fsmonitor`, `diff.external`, `core.editor`, `core.pager` and a hooks path to a program that writes a marker. Discovery and state fingerprinting leave the marker absent and the tree unchanged. A control step runs plain `git status` against the same fixture and does create the marker, so the fixture is live. User-wide filters (Git LFS) are neutralized but are not reported as repository findings.

Live machine, read-only. The audit ran from the new helper with its state and report written under a scratch directory, and mutated nothing. A first pass hit its time budget; it was resumed from its checkpoint. A resumed run then appeared hung and was stopped. The cause was real: one scanned volume is cloud-backed and reports as fixed storage, and a directory read on it blocked, and the later report-building phase read each repository's registry one at a time with no progress. Both are fixed (per-directory read timeout with a `storage-unresponsive` stop after three abandoned reads, concurrent registry reads, progress lines). The final resumed run produced:

- Status `partial`, exit 3, `full_machine_claim_allowed: false`.
- 2,692,395 directories scanned on the two fixed volumes. Two other volumes were recorded as excluded storage (not fixed local volumes).
- 35 permission-denied directories, 504 reparse points skipped, 19,142 directories skipped by the dependency-folder hints. All are listed in the ledger, not treated as absence.
- 9,828 repositories and 1,119 linked worktrees, the large majority of them test fixtures inside virtual environments and temporary folders. 9,511 identities, all unique.
- Findings: 317 unreadable registries, 309 malformed markers, 18 dangling markers, 64 repositories whose own configuration sets an executable key, 5 prunable registrations.
- The main Nexus-Hub repository lists 96 worktrees in the report and 96 in `git worktree list --porcelain -z`; the sets are equal.
- No existing worktree is at its canonical destination, because the identity folder gains an eight-character suffix. See the Phase 4 decision below.

No write to any repository was observed: the registry comparison is unchanged and the audit's only outputs were the report, checkpoint and progress lines.

Fast gate: `python scripts/ci/run.py --profile fast` passed (18 groups, 0 failed) before the commit.

## Plan delta

Disposition: Minor deltas, no change to later phases. Evidence: (1) `cleanup_merged.Host` calls the GitHub CLI, which discovery must not do, so the registry parser is a small separate function with the same record format. (2) The plan named a single resumable pass; the live run showed it also needs a per-directory timeout and a bounded report phase, both added. (3) `in_policy` means the worktree sits at `<root>/<its identity>/<name>`, not merely under the root. Consequence for remaining phases: Phase 4 inherits a partial live baseline (35 permission denials and two excluded volumes need explicit dispositions) and the identity-suffix decision.

## CI impact

No pipeline file, command, dependency or environment variable changed. The new test file `tests/validators/test_worktree_policy.py` needs a shard entry in `scripts/ci/profiles.py`; that file belongs to the coordinator and the request is recorded in `coordinator-deltas.md`.

## Deviations

None in code. No `# DEVIATION:` markers.

## Phase 4 decision to raise

All 96 Nexus-Hub worktrees live under `~/.worktrees/nexus-hub/<name>`. The contract's identity adds a hash suffix, so each would move to `~/.worktrees/nexus-hub-<8 hex>/<name>`. Recommendation: keep the suffix, which is what keeps two clones with one name apart. The alternative is a bare folder name when the slug is unique on the machine, which is easier to read but changes when a second clone appears. This is a user decision before any move.

## Next steps

Phase 2 ships `create` and `list`, the CLI wiring, both installers, the guard pair and the skill and template updates.
