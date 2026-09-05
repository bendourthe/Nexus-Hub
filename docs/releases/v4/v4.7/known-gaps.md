# Known Gaps - v4.7

**Project**: Nexus-Hub
**Status**: v4.7.0 in progress on `feat/v4.7.0-model-behavior-and-distribution-integrity`; Phases 1 to 6 and the amendment's Phase 3 complete locally, not published
**Last updated**: 2026-09-05 (v4.7.0 Phase 6)

## v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)

**Plans**: [v4.7.0-adoption-model-behavior-and-distribution-integrity.md](plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md), [v4.7.0-adoption-gpt-6-astra-prompting.md](plans/v4.7.0-adoption-gpt-6-astra-prompting.md)
**Base**: `develop` at `76bcf614` (post v4.5.0 back-merge and the v4.7 to v4.9 plans migration)

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - The v4.4.6 guide plan's model map was not reconciled from this branch

- **Source phase**: Phase 1 (amendment sub-task 1.2, T038).
- **Plan reference**: `v4.7.0-adoption-gpt-6-astra-prompting.md` sub-task 1.2.
- **Reason**: `docs/releases/v4/v4.4/plans/v4.4.6-guide-learning-experience.md` exists only on the concurrent `feat/v4.4.3-guide-illustration-rebuild` branch, where another session is still committing; editing it here would guarantee a merge conflict when that branch lands. Its map already places `gpt-6-astra` at frontier, which agrees with the 2026-09-05 decision, so the substantive disagreement the sub-task targeted no longer exists; only the one-line citation of the decision note is missing.
- **Suggested next step**: When the guide branch is merged into `develop`, add one sentence under that plan's `## Current model map` citing `docs/releases/v4/v4.7/development/astra-routing-decision.md`, or close this item as superseded if the map is treated as a historical record.

##### DF-2 - The Codex CLI does not yet list `gpt-6-astra`, so the codex profile entry reads DRIFTED

- **Source phase**: Amendment Phase 3 - the first OpenAI prompting profile (T049).
- **Plan reference**: `v4.7.0-adoption-gpt-6-astra-prompting.md` sub-task 3.3.
- **Reason**: `enumerate-models.sh codex` (`codex debug models`) on 2026-09-05 returned six models (`codex-auto-review`, `gpt-5.2`, `gpt-5.3-codex`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.5`) and not `gpt-6-astra`, which the vendor's API catalog lists as generally available. The layer's invariant (the index never claims a model it has no roster entry for) widens the codex entry's roster to include the profiled model, so `check_model_prompting_freshness.py --platform codex <live ids>` reports DRIFTED with `gpt-6-astra` as "recorded but no longer live". The profile itself is correct for the API surface the vendor documents; the drift is between the CLI's picker and the API catalog.
- **Suggested next step**: Re-run `enumerate-models.sh codex` at the next release; when the CLI lists `gpt-6-astra`, re-stamp the codex entry through the writer and this item closes. If the CLI never lists it, re-home the profile under an API-platform id in a later schema decision.

#### Warnings

##### WN-1 - Phases 2 and 6 ran one effort level below the plan's recommendation

- **Source phase**: Phase 2 - The Autonomous-Operation Block Across All Twelve Templates; also Phase 6 - Distribution Integrity.
- **Plan reference**: Phase 2 and Phase 6 `**Recommended model tier**: frontier` / `**Recommended effort level**: max`.
- **Reason**: The session ran `claude-fable-5-1` (frontier) at `high`. Claude Code cannot switch effort programmatically, so the `/effort max` keystroke was surfaced at the boundary and, with no switch made, the phase proceeded at `high` under the in-full driver. Recorded delta, not a silent downshift; the tier agreed.
- **Impact**: None observed. Every Phase 2 gate passed, including the deliberate guard-failure proof; every Phase 6 gate passed, and the one defect the phase introduced (a `set -e` return-code capture in the bash bootstrap) was caught by the manual Git Bash run inside the phase.
- **Suggested next step**: Phase 7 is also rated `max`; surface the keystroke again at that boundary so the choice is deliberate.

#### Missing tests / coverage gaps

##### MT-1 - The scheduled watch and the attestation job are unobserved until the branch merges and a tag is cut

- **Source phase**: Phase 6 - Distribution Integrity (T022, T023).
- **Plan reference**: Phase 6 Verification Expectation ("trigger the scheduled watch through `workflow_dispatch` and observe it complete without appearing in the required-check set") and sub-task 6.2.
- **Reason**: A workflow on an unpublished branch cannot be dispatched, and `publish-artifact` runs only on a `v*` tag push or a dispatch naming a tag. Both are proven statically (YAML parses, the policy tests pass, `check_required_check_coverage.py` shows the required set unchanged) but neither has been observed running. The bash leg of the parametrized bootstrap suite also skips on this Windows host by design; it was exercised by hand under Git Bash and is proven by CI's ubuntu runner at publication.
- **Suggested next step**: After the integration pull request merges, dispatch `supply-chain-watch.yml` once and confirm it completes and appears in no required context; at the v4.7.0 `/update release`, confirm `publish-artifact` attaches the two assets and the attestation to the Release, then extend the round-trip step to verify the downloaded tarball against the published `SHA256SUMS`. Close this item with both observations recorded.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|

### Notes (not gaps)

- The plan's Phase 1 stability gate "no file in the repository names `claude-fable-5` as a frontier tier value" is scoped in the test to live routing surfaces; twelve historical plans under `docs/releases/v3/` keep that id in their dated maps as records. Recorded in the Phase 1 history as a Plan delta.
- The prompting profile layer (`model-prompting-research/assets/profiles-index.json`) still lists `claude-fable-5` in its Claude roster (v4.5 `WN-3`); refreshing that roster is `/tune-prompting` work and is not this plan's scope. Amendment Phase 3 adds the first OpenAI profile beside it under a multi-platform schema and does not rewrite the Claude roster.
- The Phase 2 block measured 229 words (274 per template with its two cross-reference sentences) against the plan's 120 to 160 estimate for the block alone, because the amendment's precedence paragraph travels inside it as the plan intended. Ceilings rose by 280 each; the cost is recorded in the Phase 2 history so Phase 7's cost reckoning cannot miss it.
- v4.1.0 `DF-1` (OpenAI model ids unprofiled in the prompting layer) is narrowed by this phase: the layer now holds `gpt-6-astra` for `codex` under schema 1.1.0; the six live Codex CLI models remain unprofiled and are listed by `plan --platform codex`. Phase 7's reconciliation records the narrowing against the v4.1 ledger.
- `tests/installer/test_org_cli.py::test_connect_and_sync_git_source_with_local_bare_repo` failed once inside the full installer tier during Phase 6 and passed alone both with and without the Phase 6 changes, so it is an ordering effect in that tier and not this plan's regression; it is noted here for the next release's stabilization pass rather than recorded as a gap of this plan. Phase 6 also loosened `test_org_lifecycle.py`'s source pin on the upgrade bootstrap call from the literal `return run_bootstrap()` to the call itself, because the pinned-aware upgrade now passes a ref.
