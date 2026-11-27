# v4.15.9 Scope Reconciliation

Summary: local implementation evidence for a fixed native checkpoint receipt that preserves v4.15.9's original authority and records fresh acceptance of exact committed bytes. Read this when reviewing the repair, qualifying compatible helpers or preparing the later genuine checkpoint decision. Covers scope eligibility, prospective T020 permission, provenance, conflicts, tests and delivery limits.

## Scope Findings

The frozen [v4.15.9 plan](../plans/v4.15.9-adoption-agent-cost-and-delegation.md) states no implementation prerequisite. T020 does not require v4.15.11 to merge. The earlier wait came from claim serialization in a coordinator sidecar; v4.15.11 currently has no admitted implementation reservation. Ordered publication remains unchanged.

At local v4.15.9 HEAD `b57ba8e7e`, relative to contribution base `b3c678a95`, read-only classification found 41 uncovered paths: 35 within the frozen declared write scope, one coordinator-reserved plugin file and five nonliteral test/evidence files. The existing generic permission and withdrawal handlers refuse the member's bound read correction. The started-member execution route has different eligibility and does not cover this ordinary skill change. The historical supplement is fixed to v4.14.2 and cannot be reused as an existing permission for v4.15.9.

Existing coordinator claims can cover `.claude-plugin/plugin.json`. The new action excludes that path and keeps its outstanding status visible. The five narrowly declared checkpoint exceptions are:

- `docs/handbooks/_sources/distribution/evidence.json`
- `docs/handbooks/_sources/overview/evidence.json`
- `docs/releases/v4/v4.15/development/v4.15.9-coordinator-deltas.md`
- `tests/integrations/test_copilot_hermes_native.py`
- `tests/integrations/test_kimi_native.py`

The handbook files keep their required companion locations. The regression tests retain their coverage and locations. No general nonliteral-path eligibility is introduced.

## Design Review

Planning and an independent security review preceded implementation. The review required active read/write/coordinator conflict checks at rendering, consumption and effective use, with failed observations refusing permission. It also rejected historical path-name exemptions: approval of a checkpoint must compare exact Git transitions and must not become future permission for those paths.

The bounded action is `reconcile-member-checkpoint`. Native code computes the complete manifest rather than trusting a caller-authored list. It binds the original member state, record generation, clean registered worker, branch, current HEAD/tree, comparison base, integration tip, status, modes and before/after content identifiers. It appends genuinely captured provenance while preserving existing implementation, read corrections, approvals, starts, spending limits and prior history.

Acceptance covers at most 40 checkpoint paths. A separate prospective section permits only `catalog/skills/ai-development/model-prompting-research/SKILL.md` for T020. Checkpoint paths do not enter generic write permissions. Later changed checkpoint bytes require valid authority or a fresh exact reconciliation. Pending rounds bind the exact current generation; immutable receipt history remains available after legitimate later actions.

Historical use must support the repository's normal squash merges. The implementation uses existing authenticated GitHub PR evidence for the exact repository, source/base branches, head and merge commit, plus exact integrated file transitions. A caller-provided head or an unverifiable observation grants no coverage.

## Local Implementation

The central worktree is `~/.worktrees/nexus-hub-a564dd4d/v4159-scope-reconciliation`, on `fix/v4159-scope-reconciliation`. Its initial index exactly matched frozen candidate tree `880933391e62f6a3e4567ee9ce9609ac401c9ad1`. At that stage, the original `codex-native-continuation` worktree, its index and its HEAD were reserved for the earlier comprehensive qualification.

One worker owns the four native helper changes; a separate worker owns the new focused tests. The coordinator owns this evidence, completion-contract documentation and the progress tracker. The implementation delta will be measured against the recorded baseline tree, so inherited continuation and T027 changes are not mistaken for new checkpoint work.

A documentation guard window expired before the coordinator recorded its own two targeted updates. The official guard diffs matched only those known writes. Re-baselining did not change file contents, overwrite user edits or establish native approval authority.

## Qualification

The final targeted run passed all 114 cases in 317.38 seconds: 55 new checkpoint cases and 59 existing T027 disposition/archive cases. Imports, syntax checks and the final diff check passed. Independent security and code-versus-plan reviews approved the same frozen helper source after the corrections below. These results do not establish comprehensive qualification of the additional checkpoint changes.

On the qualification Windows 11 host, run from `~/.worktrees/nexus-hub-a564dd4d/v4159-scope-reconciliation` in PowerShell 5.1. The proving run used stable UV Python 3.12 with the already installed Store Python dependencies:

```powershell
$env:PYTHONUSERBASE = Join-Path $env:LOCALAPPDATA 'Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages'
& "$env:APPDATA\uv\python\cpython-3.12-windows-x86_64-none\python.exe" -B -m pytest tests/validators/test_member_checkpoint_reconciliation.py tests/validators/test_v4159_t027_disposition.py tests/validators/test_t027_archive_disposition.py -q --tb=short
```

The private native CLI proof creates a nonempty genuinely accepted read correction, verifies that old permission/withdrawal routes still refuse, then consumes the checkpoint and T027 decisions through the Codex transcript transport. It verifies real record loading, HMAC/signature domains, leases, atomic writes, replay refusal, signed projection, cross-session resume and controller transfer. A local bare origin supplies real Git ownership observations without network access or a push.

The archive proof runs the native mover, link proof, commit and refreeze writer, removes the private worker, and verifies historical coverage afterward. Release-eligibility gates and production authority were not exercised. All authority, keys, transcripts and repositories used by these tests are disposable private fixtures.

### Review Corrections

Both independent reviews found that hidden index flags could hide edits after acceptance and that byte-exact presentation-path/hash checks blocked legitimate archive rebinding. Regression tests reproduced both failures before the source fixes. Effective live use now checks index visibility; historical use does not require the retired subject worker's index. Archive identity now requires the canonical original plan, native Git witness, normalized content, reachable close commit, regular archived plan and absence of the original active path. Forged archive commits and rewritten prose refuse.

The subsequent reviews found no remaining issues in the reviewed source. Transport, checkpoint and T027 signing domains compose, and old or mixed protocol helpers refuse. The historical checkpoint-stage raw SHA-256 values were:

| File | SHA-256 |
|---|---|
| `scripts/approval_binding.py` | `26c0d030af31d19a3dd20fc91c66363293270f15eb550a22f1ec0172674f4c88` |
| `scripts/approval_page.py` | `138e02264d4545d3d0099eedef6ae1a5546db15520f6ee3e89e09f7752ff4a83` |
| `scripts/check_plan_completion.py` | `d90e37d956d492c752233a886e20f31f2f1e841f9642962ddfedbbcd9dc15c98` |
| `scripts/completion_minor.py` | `f8c39d505f6da9acaa4b5c1c6258e7ab30ef6cab654f0e4b9996d117da19d878` |
| `tests/validators/test_member_checkpoint_reconciliation.py` | `0804883edd7f1e4b52d81d28482b1ae9970373df0a71dba4ce1b56ebe6c61cdb` |

The original 12-file comprehensive run was intentionally stopped as incomplete after the reviewed 14-file candidate became ready. Its historical corrected heavy-hook report contains 1,125 cases with zero failures/errors and nine skips; its remaining-hook report contains 2,560 cases with zero failures/errors and 72 skips. These reports do not establish a full-profile verdict and are not reused as consolidated qualification.

The later 14-file attempt reported failures and validator timeouts and was stopped as FAILED/INCOMPLETE. A controlled instruction-path failure/pass pair established a temporary-location fault for that case. The replacement preserves the checkpoint implementation and tests while integrating the reviewed comparison handoff on the current base. Complete corrected canonical full-scope qualification is still required. See [combined qualification](codex-native-continuation-repair.md#combined-qualification) for the failure disposition, isolation evidence and baseline limits.

The subsequent consolidated 20-path full attempt was stopped as `INCOMPLETE: fixture path length` after a comparable synthetic Git fixture produced a 316-character file path and `git add` exited 128 with `Filename too long`. The retained interruption receipt confirms owned-process quiescence, zero interruption errors and unchanged candidate inputs. A separate short-root fixture staged its 213-character path successfully with `core.longpaths` unset; no global Git or OS setting changed. All partial dynamic passes from the stopped attempt are discarded.

The later v3 short-runtime attempt is terminal with exit 1: 67 commands passed, three failed, five timed out and four skipped across all 17 default groups. Its inputs remained unchanged, process quiescence was verified and source-side reports were preserved. The corrected runtime controls and three focused installer cases pass, but fresh whole-group qualification and an independently verified complete coverage ledger remain open. No passing command from the failed environment is reused. See the [terminal attempt and corrected qualification](codex-native-continuation-repair.md#terminal-full-attempt) for exact results and limitations.

## Delivery Limits

The subsequent self-contained validator attempt also ended with four timeouts and no passing command. Its unchanged inputs and process cleanup are preserved. A bounded 12-case timing diagnostic passed, while collection-only checks inventoried 4,866 unique cases. On 2026-11-24 the maintainer approved the independently reviewed three-file Windows partition repair and its larger aggregate time allowance. The patch is applied; revised collection and complete fresh qualification remain pending. This approval does not establish native checkpoint authority or authorize publication or installation. See the [approved Windows validator repair](codex-native-continuation-repair.md#approved-windows-validator-repair) for exact evidence and ceilings.

No production checkpoint has been rendered, captured or appended. The helper changes are not installed or published. Real use still requires a compatible reviewed delivery and a fresh genuine native decision for the exact eligible worker checkpoint. No earlier approval is synthesized or replayed, and no Claude Code session or T027 trial is started.

Completion of this local repair does not establish `MINOR COMPLETE v4.15`. The remaining implementation, integration, release, migration, installed verification and cleanup requirements remain in force.

The integration command used an unavailable bare Python alias. PowerShell continued past those guard-command failures and applied the exact reviewed delta. The resulting index matched the reviewed tree. This was a procedural guard failure, not a successful preservation check. Subsequent edits use an explicit interpreter and terminating shell errors. No unrelated edits were overwritten; no guard accept or native approval was synthesized.
