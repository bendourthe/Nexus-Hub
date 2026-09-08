# Known Gaps - v4.9

**Project**: Nexus-Hub
**Status**: open; seeded 2026-09-08 from post-v4.8.0 work. The v4.8 ledger is finalized, so findings after that release land here rather than reopening it.
**Last updated**: 2026-09-08 (v4.9.0 Phase 1)

## Open Items - found 2026-09-08 during post-v4.8.0 follow-up

### Missing tests / coverage gaps (MT)

#### MT-1 - Four rostered models carry no prompting profile, because no vendor publishes per-model guidance for them

- **Source**: the post-v4.8.0 `/tune-prompting` full roster sweep.
- **What was observed**: 12 of 16 rostered models are now profiled. Four are not, and each for a sourced reason rather than for lack of effort:
    - **`claude-haiku-4-5`**: Anthropic's model-specific guidance table lists dedicated prompting pages for Fable 5.1, Fable 5, Sonnet 5, Opus 5, and Opus 4.8 only. Haiku 4.5 is covered by the general best-practices reference, which is model-agnostic across current Claude models and therefore yields no model-SPECIFIC claim.
    - **`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`**: OpenAI's prompt-engineering guide documents `gpt-6-astra` (already profiled) and reasoning-versus-GPT guidance generally. It names no member of the 5.6 family, so there is nothing model-specific to record.
- **Why this is the correct outcome, not a shortfall**: the runbook is explicit that no primary source found means zero claims rather than a guess, because an unsourced claim in the layer is indistinguishable from a hallucinated one and every later phase treats recorded claims as verified input. All four are reported UNVERIFIED by `verify_model_prompting_profiles.py`, which treats that as tracked rather than as a gate failure.
- **Suggested next step**: re-check at the next `/tune-prompting` run. A vendor publishing a per-model page is the trigger; nothing else changes the answer. Do not fill these from the general guidance, which would silently convert model-agnostic advice into a model-specific claim.

### Warnings (WN)

#### WN-1 - Cursor and Gemini claims are family-scoped, recorded at per-model granularity

- **Source**: the same sweep.
- **What was observed**: Google documents Gemini 3.x as a unified family and publishes no per-version prompting guidance, and Cursor publishes no prompting guidance at all (its documentation covers pricing, cache rates, and plan constraints). The claims recorded for the four Gemini models and the four Cursor entries are therefore family-level or plan-level facts, recorded once per rostered model because that is the granularity the layer indexes. Each such claim carries a `note` stating the true scope.
- **Why it is worth recording**: a future reader comparing two Gemini entries will find identical claims and could reasonably conclude the layer is padded. It is not: the source genuinely makes one statement about the family, and the alternative (leaving all four UNVERIFIED) would discard a real, sourced constraint such as Google's recommendation to keep `temperature`, `top_p`, and `top_k` at their defaults.
- **Suggested next step**: if the layer ever grows a family or vendor tier, move these claims up to it and leave the per-model entries pointing at it. That is a schema change and belongs in a decision record, not in a research pass.

#### WN-2 - One vendor claim tensions with a shared catalog skill, recorded and not acted on

- **Source**: the sweep's `claude-opus-5` research.
- **What was observed**: Anthropic's Opus 5 page says to REMOVE explicit verification instructions and legacy harness verification scaffolding, because they cause over-verification on that model and removing them reduces wasted tokens with no loss in quality. The catalog's own `verification-before-completion` skill requires a fresh proving command before any completion claim.
- **Why they are not actually the same rule**: the vendor claim is about redundant self-re-checks inside a turn ("double-check your answer"), while the skill is about evidence for a claim made to a human. Both can hold at once. But they read as contradictory, and someone reconciling them should read both first.
- **What was done**: the claim is recorded in the profile layer scoped `model-specific`, so it structurally cannot reach a shared body through that path, with the tension stated in its `note`. No shared-body edit was proposed and the classifier ran with zero proposals.
- **Suggested next step**: if a future pass wants to reconcile them, that is a decision record about what verification-before-completion means inside a turn versus at a claim boundary, not a prompting edit.

## v4.9.0 - adoption-visa-vulnerability-agentic-harness

**Plan**: [v4.9.0-adoption-visa-vulnerability-agentic-harness.md](plans/v4.9.0-adoption-visa-vulnerability-agentic-harness.md)
**Base**: `develop` at `843c147d` (the PR #188 merge)
**Retargeted**: from v4.8.0 on 2026-09-08, because v4.8.0 shipped carrying only its sibling plan

### Summary

Phase 1 local verification passed: 230 tests, 8 platform-dependent skips, 87.30 percent affected-script coverage. Earlier draft deferrals DF-1 through DF-4 have been implemented. Counts below apply only to this plan's subsection; unrelated post-v4.8 follow-up items above remain unchanged.

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 4 |
| BG | 0 | 0 |
| WN | 0 | 0 |
| MT | 1 | 0 |
| QG | 1 | 0 |

### Open Items

Phase 2 adds no deferred implementation gap. Its final gate passes 395 tests with 25 explicit platform skips and 87.07% coverage. MT-2 and QG-1 retain their original ownership; the additional workflow-policy skips do not constitute Windows or remote CI evidence.

#### MT-2 - Platform-specific filesystem cases need their matching host

- **Source phase**: Phase 1, T003.
- **Plan reference**: T002 Windows/POSIX containment and path-identity verification.
- **Reason**: eight tests skip on this Windows workstation: six symlink-creation cases require a capability unavailable here, one case-collision fixture collapses on the host filesystem, and one POSIX mode-bit test is inapplicable. Native Windows junction, directory-lock, hard-link, ownership, and cleanup cases execute locally. No POSIX execution is claimed from Windows results.
- **Suggested next step**: execute the matching platform cases during Phase 7 qualification and verify their first permitted remote CI run; retain explicit skip accounting.

#### QG-1 - The Windows CI job does not yet select the new filesystem tests

- **Source phase**: Phase 1, T003 CI impact record.
- **Plan reference**: Phase 7 terminal pipeline reconciliation and T002 Windows/POSIX coverage.
- **Reason**: the full repository test profile includes tests/skills on Linux; the existing Windows job selects windows-hooks and specific delivery integration files, omitting these new Windows API tests. Local Windows tests pass, but this does not prove remote Windows coverage. No gate bypass or pipeline change has been approved or performed.
- **Suggested next step**: at Phase 7, propose the smallest Windows test-selection change with its cost and obtain the required pipeline approval before applying it.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| DF-1 | Sanitized Git metadata | Phase 1 corrective implementation | Index/ref/ignore snapshots use empty config/hooks; invalid target config does not affect classification. |
| DF-2 | Index identity | Phase 1 corrective implementation | Index bytes and parsed entry digests are bound; index changes invalidate a manifest. |
| DF-3 | Submodule classification | Phase 1 corrective implementation | Each in-scope gitlink binds child HEAD, dirty and untracked state; incomplete/external metadata fails. |
| DF-4 | Windows containment primitives | Phase 1 corrective implementation | Native directory handles deny rename during operations, with identity checks before content publication; no process assurance is claimed. |

## Resolved during this follow-up

- **The intermittent org-CLI failure was a Windows directory-rename race, now fixed** (carried in as v4.8 `WN-I`, org-CLI half, and briefly tracked here as `BG-1`). It arrived as a test that failed twice on a DIFFERENT test each time, never reproduced in isolation (12 consecutive clean runs of the file, 470 passing for the whole directory), and passed on both CI test jobs. Four candidate causes were ruled out first: the `PYTHONUTF8` decoding defect that explained the PowerShell half (that file was already hardened), load (it failed inside a 4-second single-file run), order randomization (no such plugin is installed), and cross-suite pollution (1319 hook tests immediately before left the suspects passing).
- The mechanism is platform behavior, not test flakiness. On Windows `os.replace` on a DIRECTORY fails with `PermissionError` (`WinError 5`) while any process holds a handle to a file inside it, and the identical call succeeds once released. A lingering `git.exe` child from the fixture's clone or push, an on-access scanner, or a desktop indexer is enough to open the window. It is invisible on POSIX, where rename ignores open handles, which is why CI's Linux job could never see it and a clean hosted Windows runner sees it far less often than a developer workstation.
- **Reproduced deterministically before anything was changed**, which is what unblocked the fix. `tests/installer/test_org_repo_replace_retry.py` holds a real handle inside the destination and releases it from a timer; against the unfixed code it failed in 0.77s with the genuine `PermissionError: [WinError 5]` at `nexus_hub_cli.py:782`, the exact line suspected. A once-in-hundreds-of-runs intermittent became a sub-second red test.
- **Fix**: `_replace_path_with_retry` wraps both directory renames in `_replace_org_repo` with a bounded backoff (50ms, 150ms, 300ms, 500ms), then makes a final unguarded attempt so a PERMANENT permission problem still raises the real error rather than being swallowed or spun on. The module already accepted this class of Windows behavior for deletion, in `_remove_owned_path`'s chmod-and-retry handler; the rename path simply had no equivalent tolerance. The restore-on-failure path now also tolerates a blocked restore without masking the original error.
- **Five tests**, covering the baseline with nothing blocking, a transient block that clears, a block that never clears (the retry must stay bounded), the restore-on-failure guarantee, and the unmocked real-held-handle case on Windows. The last is the one that would have caught this without knowing the mechanism in advance.
- **Why the earlier record said "not fixed"**: a fix could not be verified against a failure that would not reproduce on demand, and shipping unverifiable installer code is worse than shipping an accurate finding. Building the deterministic reproduction removed that objection, and the fix followed in minutes.

- **`_owned.py` staged files world-writable under a permissive umask** (carried in as v4.8 `WN-K`). `_atomic_replace_bytes` created its staging file `0o666`, which is `0o666 & ~umask`: world-writable on a host with `umask 000`, in code that ships in `scripts/` and runs during a user's install. It also rewrote the destination's permissions on every refresh, because `os.replace` carries the source's mode. Both are fixed by adopting the convention the sibling implementation in `scripts/lib/installer/instruction_merge.py` already used: create owner-only, then reapply the destination's own mode when one exists. Seven tests in `tests/integrations/test_owned_file_modes.py`, negative-controlled by restoring the original defect and confirming three of them fail. The tests spy on `os.open` and `os.chmod` rather than reading back `stat().st_mode`, because on Windows `S_IMODE` reflects only the read-only bit and a mode-readback test would have passed against the original defect.
- **The prompting profile layer reported DRIFTED** (carried in from the v4.8.0 release as an advisory). 12 of 16 rostered models are now profiled from fetched vendor primary sources, and the advisory check reports IN SYNC. Every claim is scoped `model-specific`; the classifier proposed zero shared-body edits, so no shared surface was touched.
- **The writer generated orphan bundled files.** Every per-model mirror it emitted was unreferenced from `SKILL.md`, so the orphan-warning count grew by one per profiled model (1 after the first OpenAI profile, 11 after this sweep) and the agent would never load a Tier-3 reference nothing points at. The writer now regenerates `references/model-profiles.md` linking every mirror, which returned the audit to its exact pre-sweep baseline of 65 warnings and also closed the pre-existing `gpt-6-astra` orphan. Guarded by `tests/validators/test_model_prompting_layer_bundle.py`, negative-controlled by removing one link and confirming the guard fails.
