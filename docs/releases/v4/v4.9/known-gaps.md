# Known Gaps - v4.9

**Project**: Nexus-Hub
**Status**: open; seeded 2026-09-08 from post-v4.8.0 work. The v4.8 ledger is finalized, so findings after that release land here rather than reopening it.
**Last updated**: 2026-09-08

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

### Bugs (BG)

#### BG-1 - The org-CLI intermittent failure is a Windows directory-rename race; mechanism confirmed, occurrence not yet reproduced

Carried in from v4.8 `WN-I` (org-CLI half), and substantially advanced. This is the honest state: the MECHANISM is proven on this platform, a specific code path is identified, but the failure itself has not been reproduced on demand, so nothing was changed.

- **What was observed, twice, on a different test each time**: `test_disconnect_requires_confirmation_and_yes_removes_state_and_cache` failed inside a `tests/workflows tests/installer tests/ci` run, and `test_connect_and_sync_git_source_with_local_bare_repo` failed inside a `tests/installer tests/validators tests/skills` run. Both live in `tests/installer/test_org_cli.py`; both exercise the `bare_bundle_repo` fixture, which shells out to real `git` seven times.
- **Never reproduces in isolation**: 12 consecutive runs of the whole file clean, plus the single test alone clean, plus the whole `tests/installer` directory clean (470 passed). It has only ever failed as part of a larger multi-directory run.
- **Suspected code path**: `scripts/nexus_hub_cli.py::_replace_org_repo` performs two `os.replace` calls on DIRECTORIES (`destination` to `backup`, then `candidate` to `destination`), with a restore-on-failure path.
- **Mechanism CONFIRMED on this platform.** Holding one file handle open inside a directory and calling `os.replace` on that directory fails immediately:

    ```
    PermissionError: [WinError 5] Access is denied: '...\destination' -> '...\backup'
    ```

    Releasing the handle and repeating the identical call succeeds. So a lingering handle inside the cached clone (a `git.exe` child that has not fully exited after the fixture's `push`, an indexer, or an on-access scanner) is sufficient to make this call fail, with no bug in the calling logic at all.
- **Why this fits every observation**: it is transient by nature (intermittent), it depends on which test happens to hit the window (moves between tests), it needs concurrent filesystem pressure to be likely (only in large runs), and it is INVISIBLE on POSIX, where rename does not care about open handles. That last point is why CI's Linux `tests` job can never see it.
- **Why CI's Windows job does not catch it either**: the same rename is performed there, but a clean hosted runner has no on-access scanner or desktop indexer competing for handles, so the window is far narrower than on a developer workstation.
- **NOT changed, deliberately.** The obvious accommodation is a bounded retry with backoff around the rename, and the module already accepts this class of Windows behavior elsewhere (`_remove_owned_path` passes an `onerror` handler that chmods and retries for `shutil.rmtree`). A retry here would very likely work. It was still not added, because a fix cannot be verified against a failure that does not reproduce on demand, and shipping an unverifiable change to installer code is worse than shipping an accurate finding. That would be the temporary fix this project's own rules reject.
- **Suggested next step, in order**: (1) reproduce deterministically by injecting a held handle in a test that drives `_replace_org_repo`, which the experiment above shows is straightforward; (2) with a red test in hand, add the bounded retry and watch it go green; (3) keep the red test as the regression guard. Step 1 is the whole job -- steps 2 and 3 are then routine.
- **Do not** mark the test flaky, add a blanket retry to the test, or widen a timeout. Each converts a visible intermittent failure into a silent one, and the product code is the thing implicated here, not the test.

## Resolved during this follow-up

- **`_owned.py` staged files world-writable under a permissive umask** (carried in as v4.8 `WN-K`). `_atomic_replace_bytes` created its staging file `0o666`, which is `0o666 & ~umask`: world-writable on a host with `umask 000`, in code that ships in `scripts/` and runs during a user's install. It also rewrote the destination's permissions on every refresh, because `os.replace` carries the source's mode. Both are fixed by adopting the convention the sibling implementation in `scripts/lib/installer/instruction_merge.py` already used: create owner-only, then reapply the destination's own mode when one exists. Seven tests in `tests/integrations/test_owned_file_modes.py`, negative-controlled by restoring the original defect and confirming three of them fail. The tests spy on `os.open` and `os.chmod` rather than reading back `stat().st_mode`, because on Windows `S_IMODE` reflects only the read-only bit and a mode-readback test would have passed against the original defect.
- **The prompting profile layer reported DRIFTED** (carried in from the v4.8.0 release as an advisory). 12 of 16 rostered models are now profiled from fetched vendor primary sources, and the advisory check reports IN SYNC. Every claim is scoped `model-specific`; the classifier proposed zero shared-body edits, so no shared surface was touched.
- **The writer generated orphan bundled files.** Every per-model mirror it emitted was unreferenced from `SKILL.md`, so the orphan-warning count grew by one per profiled model (1 after the first OpenAI profile, 11 after this sweep) and the agent would never load a Tier-3 reference nothing points at. The writer now regenerates `references/model-profiles.md` linking every mirror, which returned the audit to its exact pre-sweep baseline of 65 warnings and also closed the pre-existing `gpt-6-astra` orphan. Guarded by `tests/validators/test_model_prompting_layer_bundle.py`, negative-controlled by removing one link and confirming the guard fails.
