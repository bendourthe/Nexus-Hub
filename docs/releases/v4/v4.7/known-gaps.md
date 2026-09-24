# Known Gaps - v4.7

**Project**: Nexus-Hub
**Status**: released. v4.7.0 was published on 2026-09-06 at tag `v4.7.0` (`667cc465`) after integration in PR #167 (`ca8e663e`). MT-1's hosted observation gate was verified after release; WN-2 records the separate failing default-branch schedule.
**Last updated**: 2026-09-24

## v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)

**Plans**: [v4.7.0-adoption-model-behavior-and-distribution-integrity.md](../../../archives/v4/v4.7/plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md), [v4.7.0-adoption-gpt-6-astra-prompting.md](../../../archives/v4/v4.7/plans/v4.7.0-adoption-gpt-6-astra-prompting.md)
**Base**: `develop` at `76bcf614` (post v4.5.0 back-merge and the v4.7 to v4.9 plans migration)

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 4 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-2 - The Codex CLI does not yet list `gpt-6-astra`, so the codex profile entry reads DRIFTED

- **Source phase**: Amendment Phase 3 - the first OpenAI prompting profile (T049).
- **Plan reference**: `v4.7.0-adoption-gpt-6-astra-prompting.md` sub-task 3.3.
- **Reason**: `enumerate-models.sh codex` (`codex debug models`) on 2026-09-05 returned six models (`codex-auto-review`, `gpt-5.2`, `gpt-5.3-codex`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.5`) and not `gpt-6-astra`, which the vendor's API catalog lists as generally available. The layer's invariant (the index never claims a model it has no roster entry for) widens the codex entry's roster to include the profiled model, so `check_model_prompting_freshness.py --platform codex <live ids>` reports DRIFTED with `gpt-6-astra` as "recorded but no longer live". The profile itself is correct for the API surface the vendor documents; the drift is between the CLI's picker and the API catalog.
- **Suggested next step**: Re-run `enumerate-models.sh codex` at the next release; when the CLI lists `gpt-6-astra`, re-stamp the codex entry through the writer and this item closes. If the CLI never lists it, re-home the profile under an API-platform id in a later schema decision.

**2026-09-24 recheck**: The installed Codex CLI picker still lists six models and omits `gpt-6-astra`; the [archived read-only result](../../../archives/v4/v4.7/development/model-map-followup/verification.md) keeps API availability separate from CLI availability. DF-2 remains open and no profile was re-stamped.

##### DF-3 - Four template validators share one roster and one shape

- **Source phase**: Phase 7 - Architecture refactor (T027).
- **Plan reference**: main plan sub-task 7.1; v4.5.0's `construction-debt:` note named the third invariant block as the consolidation trigger.
- **Reason**: `test_construction_discipline_rule.py`, `test_writing_discipline_rule.py`, `test_autonomy_block_rule.py`, and `test_communication_contract_rule.py` each carry a twelve-template roster (two hardcoded, two derived from the directory) and the same presence, identity, and shim checks. The parity script holds a fifth copy of the lockstep list. Consolidating in the final phase of a release means renaming modules that three releases' evidence cites by file name, which is why it was recorded rather than applied.
- **Suggested next step**: On the next plan that adds or edits a template block, move the roster derivation and the section-body helper into one shared module under `tests/validators/`, have the parity script read the lockstep list from the same place, and parametrize the four modules over their block markers; keep four files so a failure still names the block.

##### DF-4 - Reusable `workflow_call` CI factoring (report item E5) deliberately excluded

- **Source phase**: Phase 7 - Known-gaps reconciliation (T028), as the plan directs.
- **Plan reference**: `comparisons/v4.7.0-comparison-ecc-agent-catalog.md` item E5 (P3); main plan sub-task 7.2.
- **Reason**: A refactor of working CI whose benefit is maintainer ergonomics, carrying the required-context risk the v3.17.6 policy exists to prevent: a reusable workflow changes which workflow produces a context, and a context produced by a filtered or conditionally called workflow sits Pending forever. Not rejected on principle; not worth a release that also changes twelve templates and the install path.
- **Suggested next step**: If ever done, its own release, with `check_required_check_coverage.py` and `tests/validators/test_ci_required_gate.py` extended first to resolve contexts through `workflow_call` producers.

##### DF-5 - Per-skill presentation metadata (report item E6) deliberately excluded

- **Source phase**: Phase 7 - Known-gaps reconciliation (T028), as the plan directs.
- **Plan reference**: `comparisons/v4.7.0-comparison-ecc-agent-catalog.md` item E6 (P3); main plan sub-task 7.2.
- **Reason**: Display name, short description, brand colour, and default prompt per skill have no rendering host in Nexus-Hub today; frontmatter that nothing reads is Tier 1 cost on every session for no consumer.
- **Suggested next step**: Revisit when a consumer exists (the guide, the MCP skill server, or a downstream app asks for it), and add the fields to `data/skills.json` first rather than to every `SKILL.md`.

#### Warnings

##### WN-1 - Phases 2, 6, and 7 ran one effort level below the plan's recommendation

- **Source phase**: Phase 2 - The Autonomous-Operation Block Across All Twelve Templates; also Phase 6 - Distribution Integrity and Phase 7 - the final phase.
- **Plan reference**: Phases 2, 6, and 7 `**Recommended model tier**: frontier` / `**Recommended effort level**: max`.
- **Reason**: The session ran `claude-fable-5-1` (frontier) at `high`. Claude Code cannot switch effort programmatically, so the `/effort max` keystroke was surfaced at the boundary and, with no switch made, the phase proceeded at `high` under the in-full driver. Recorded delta, not a silent downshift; the tier agreed.
- **Impact**: None observed. Every Phase 2 gate passed, including the deliberate guard-failure proof; every Phase 6 gate passed, and the one defect the phase introduced (a `set -e` return-code capture in the bash bootstrap) was caught by the manual Git Bash run inside the phase.
- **Suggested next step**: When the next plan rates a phase `max`, decide at the pre-flight whether to make the keystroke, so the choice is deliberate rather than inherited from the driver's momentum. Phase 7's independent review found ten of ten Goal clauses converged at high.

##### WN-2 - Scheduled `main` supply-chain audit remains red

- **Source phase**: Post-release hosted verification on 2026-09-24.
- **Plan reference**: v4.7.0 Phase 6 Distribution Integrity, T022 and T023.
- **Reason**: Three scheduled `main` runs failed, most recently run 35599558573 on 2026-09-21. Its report found `setuptools` 79.0.1, affected by `PYSEC-2026-3447`; current `main` lacks the newer `develop` constraint that pins 84.0.0. A passing manual `develop` run does not prove default-branch schedule health. The [archived verification](../../../archives/v4/v4.7/development/supply-chain-watch-followup/verification.md) retains both outcomes.
- **Suggested next step**: The CI/release maintainer must bring a fixed `setuptools` into the default-branch audit environment through the protected release path, then observe a passing `main` dispatch or schedule without suppressing the advisory.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| DF-1 | v4.4.6 guide-plan model-map citation missing | 2026-09-24 follow-up | The map already placed `gpt-6-astra` at frontier; the user later rejected and superseded the v4.4.6 redesign. [Archived evidence](../../../archives/v4/v4.7/development/model-map-followup/verification.md) closes the citation-only task without editing the historical plan. |
| MT-1 | Hosted watch and attested release artifact were unobserved | 2026-09-24 follow-up | [Manual `develop` run 36034068237](https://github.com/bendourthe/Nexus-Hub/actions/runs/36034068237) passed, with no required-check context; v4.7.0 tarball and `SHA256SUMS` matched after download, and GitHub verified the repository attestation. See [archived evidence](../../../archives/v4/v4.7/development/supply-chain-watch-followup/verification.md). WN-2 separately tracks the red `main` schedule. |

### Notes (not gaps)

- The plan's Phase 1 stability gate "no file in the repository names `claude-fable-5` as a frontier tier value" is scoped in the test to live routing surfaces; twelve historical plans under `docs/releases/v3/` keep that id in their dated maps as records. Recorded in the Phase 1 history as a Plan delta.
- The prompting profile layer (`model-prompting-research/assets/profiles-index.json`) still lists `claude-fable-5` in its Claude roster (v4.5 `WN-3`); refreshing that roster is `/tune-prompting` work and is not this plan's scope. Amendment Phase 3 adds the first OpenAI profile beside it under a multi-platform schema and does not rewrite the Claude roster.
- The Phase 2 block measured 229 words (274 per template with its two cross-reference sentences) against the plan's 120 to 160 estimate for the block alone, because the amendment's precedence paragraph travels inside it as the plan intended. Ceilings rose by 280 each; the cost is recorded in the Phase 2 history so Phase 7's cost reckoning cannot miss it.
- v4.1.0 `DF-1` (OpenAI model ids unprofiled in the prompting layer) is narrowed by this phase: the layer now holds `gpt-6-astra` for `codex` under schema 1.1.0; the six live Codex CLI models remain unprofiled and are listed by `plan --platform codex`. Phase 7's reconciliation records the narrowing against the v4.1 ledger.
- `tests/installer/test_org_cli.py::test_connect_and_sync_git_source_with_local_bare_repo` failed once inside the full installer tier during Phase 6 and passed alone both with and without the Phase 6 changes, so it is an ordering effect in that tier and not this plan's regression; it is noted here for the next release's stabilization pass rather than recorded as a gap of this plan. Phase 6 also loosened `test_org_lifecycle.py`'s source pin on the upgrade bootstrap call from the literal `return run_bootstrap()` to the call itself, because the pinned-aware upgrade now passes a ref.

- `tests/guides/test_nexus_hub_guide.py::test_file_size_budget` fails on a Windows checkout and passes on CI. The test measures `GUIDE.stat().st_size`, which is the ON-DISK size, while `.gitattributes` declares `* text=auto` so the guide is stored and distributed with LF endings. The distributed blob is 498,806 bytes against the 500,000 ceiling; the same file checked out with CRLF is 503,211 bytes, the 4,405-byte difference being one added byte per line. This is a host artifact of the checkout, not a budget breach, so the ceiling was NOT raised and the guide was NOT trimmed to accommodate it. Anyone reproducing the guide tier on Windows should expect this one failure.

- `tests/guides/test_models_learning_lab.py::test_world_camera_rotates_and_moves_through_depth_mesh` failed once inside the full guide tier during this stabilization and passed on the next full run, on its own module, and under a hand-driven replay of its exact sequence. The reported camera was the value written by the first draw, so the demo never left its paused state for the whole mocked interval. The replay confirmed the click leaves the pointer on the mode button rather than the board, so nothing in the layout pauses it; the remaining explanation is that the visibility callback that starts the demo had not fired yet under the tier's load. Recorded as a load-sensitive test, not a guide defect and not a regression of the heading-fitting change.

### Carry-forward from other ledgers

Reviewed at Phase 7 per sub-task 7.2. Files that a concurrent session has modified in the main checkout (the v4.4 ledger, `docs/todos.md`) were not edited from this branch; dispositions are recorded here for that session or the release step to apply.

| Item | Disposition | Reason |
|---|---|---|
| v4.4 `DF-1` - three platform entries use text treatments pending approved marks | Stays open, owned by v4.4 | Guide-specific; nothing in v4.7 touches platform marks (carried forward unchanged, as the plan directs). |
| v4.4 `WN-1` - a phase ran one tier below its recommendation because the map resolved frontier to a legacy model | Closable (superseded) | Phase 1 re-verified the map: frontier Anthropic is `claude-fable-5-1`; the condition that produced the warning no longer exists. |
| v4.4 `WN-2` - the superseded-assertion register was incomplete | Closable (scope complete) | Scoped to v4.4 guide phases 3 to 7, published in the v4.4.5 tag. |
| v4.5 `WN-3` - profile layer lists `claude-fable-5`, live roster `claude-fable-5-1` | Stays open, owned by v4.5 | Re-checked this cycle: still DRIFTED; this plan added an OpenAI profile under a multi-platform schema and did not refresh the Claude roster, which is `/tune-prompting` work. |
| v4.1 `DF-1` - prompting profile layer does not match the live Codex roster | Narrowed | The layer now holds `gpt-6-astra` for `codex` (schema 1.1.0, live-enumerated roster); the six live Codex CLI models remain unprofiled and `plan --platform codex` lists them. The v4.1 file is a finalized record and is not edited. |
| v4.0 `DF-1` - the non-lockstep seven are not byte-locked by the release gate | Narrowed | The Autonomous Operation block's validator byte-compares all twelve, as v4.5.0's did for Writing Discipline; the general item stays open there. |
| v4.4.6 `T026` - the guide's human/manual review is unanswered | Stays open, owned by v4.4 | The v4.4.6 plan's last phase asks a human for two unassisted reader-response sets and native browser observations. Silence is not approval, so it cannot be closed from this session. The guide merges into v4.7.0 with its automated gates green and this reader review still outstanding. |
| v4.4.6 `T027` - full-suite stabilization | Closed by this cycle | The guide tier runs green on the merge branch apart from one Windows-only on-disk byte measurement recorded in the notes above. |
| v4.4.6 `T028` - publication and integration | Closed by this cycle | The guide work publishes through this branch's pull request into develop rather than through its own v4.4.6 release. |
| v4.5 `DF-1`, `DF-2`, `DF-3`, `MT-1`; v4.2 and v4.3 open items | Untouched | Outside this plan's scope; owned by their ledgers. |
