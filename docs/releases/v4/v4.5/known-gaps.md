# Known Gaps - v4.5

**Project**: Nexus-Hub
**Status**: v4.5.0 finalized 2026-09-04 at `/update release`; integrated via PR #162 (merge `765d9f32`) and PR #163
**Last updated**: 2026-09-04 (v4.5.0 release)

## v4.5.0 - anti-cliche-and-agent-security

**Plan**: [v4.5.0-anti-cliche-and-agent-security.md](plans/v4.5.0-anti-cliche-and-agent-security.md)
**Base**: `develop` at `8a426441` (the v4.4.5 back-merge)

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 3 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 1 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - Whether the always-on Writing Discipline clause improves replies is unverified by a person

- **Source phase**: Phase 1 - Writing Discipline rule; Phase 7 - final review.
- **Plan reference**: sub-task 1.5 (measured cost) and Human and Manual Testing Suggestions item 2.
- **Reason**: The cost is measured and justified on its own terms (163 words, roughly 215 tokens per turn per platform in use; ceilings raised by exactly the delta and recorded in `docs/policy/doc-budgets.md`). The benefit cannot be measured by a test: whether the self-check clause changes a live reply, and whether the change is an improvement or stiffness, is a judgment a person makes by asking a cliche-prone question on two platforms and reading the answers. Nobody has done that yet.
- **Suggested next step**: Run human test 2 after the release lands on at least two platforms; if the replies read as stiff rather than cleaner, shorten the prohibition list before touching the self-check clause, since the clause is the load-bearing part (see the decision record `docs/decisions/implemented/policy/2026-09-04-writing-discipline-binds-chat-replies.md`).

##### DF-2 - No transitive-reachability or shared-writable-service enumeration has been performed on this repository's own agent surface

- **Source phase**: Phase 5 - Agent isolation; Phase 7 - final review.
- **Plan reference**: sub-task 7.3 prompt ("any egress reachability or shared-service enumeration this repository has not performed on its own agent surface") and Human and Manual Testing Suggestions item 4.
- **Reason**: The security comparison raised this as an open question about Nexus-Hub itself: any write-capable service reachable from more than one agent session (a package registry, an artifact store, a CI cache) is a channel until proven otherwise, and any allowlisted destination with its own reach is part of the agent's real reachability. The v4.5.0 plan shipped the controls as catalog guidance; it did not apply them to the agents that develop this repository (CI runners, the MCP servers under `extensions/`, the memory store). That application is a design exercise on real infrastructure, not a documentation task.
- **Suggested next step**: Run human test 4: take step 3 sub-steps 6 to 8 and step 5 sub-steps 5 to 7 of `agent-execution-isolation` and apply them to this repository's CI and local agent surface, producing the two named artifacts (the shared-writable-service enumeration and the transitive-reachability union). If the controls cannot be applied as written, they are too abstract and the skill should be revised.

##### DF-3 - Mannered prose and the stranded auxiliary rely on model judgment alone

- **Source phase**: Phase 4 - Offline detector.
- **Plan reference**: sub-task 4.1 and the plan 7.3 prompt ("any cliche pattern the phase 4 detector cannot express deterministically").
- **Reason**: The catalog names nineteen patterns in seven clusters; the detector encodes 29 ids covering clusters 1 to 4 and 6 plus the rhythm rules and punctuation. Cluster 7 (mannered prose, where metaphor or flourish replaces a direct statement) has no lexical signature and is deliberately not attempted, as the module docstring says. Cluster 5 (the stranded auxiliary, a sentence ending on "can", "does", or "will" with the verb elided) has no detector id either. Both rely on the agent applying the reference file in Edit mode.
- **Suggested next step**: Leave mannered prose to judgment; it is not a regex problem. The stranded auxiliary is likely expressible (an auxiliary verb followed by sentence-final punctuation with no verb after it); add it to the LEXICAL table with a seeded fixture count in a patch release if a false-positive sweep on the repository's prose stays clean.

#### Warnings

##### WN-2 - Phases 3, 5, and 7 ran one effort level below the plan's recommendation

- **Source phase**: Phase 3 - Catalog Extension, the Uncovered Cliche Patterns; also Phase 5 and Phase 7.
- **Plan reference**: Phase 3, 5, and 7 `**Recommended model tier**: frontier` / `**Recommended effort level**: max`.
- **Reason**: The session ran `claude-fable-5-1`, which is the frontier tier on the 2026-09-04 map, at `high`. Claude Code cannot switch effort programmatically, so the `/effort max` keystroke was surfaced at each of the three phase boundaries and, with no switch made, each phase proceeded at `high` under the in-full driver. This is a recorded delta, not a silent downshift, and the tier itself agreed with the plan every time.
- **Impact**: None observed. Every gate in all three phases passed; phase 3's reference file names no upstream expression; phase 5's name scrub returned nothing; phase 7's independent review found six of six clauses converged.
- **Suggested next step**: When the next plan rates a phase `max`, decide at the pre-flight whether to make the keystroke, so the choice is deliberate rather than inherited from the driver's momentum.

##### WN-3 - The model-prompting profile layer does not match the live Claude roster

- **Source phase**: Phase 7 - advisory freshness check (runbook duty 9).
- **Plan reference**: implement-phase runbook Phase 9.0 duty 9 (`model-prompting-research`, advisory).
- **Reason**: `python scripts/check_model_prompting_freshness.py --advisory <live roster>` reports `added (live but unprofiled): claude-fable-5-1` and `removed (recorded but no longer live): claude-fable-5`. The recorded roster was last verified 2026-07-27. This is the same drift class as v4.1 `DF-1` (Codex roster); it never blocks a release and is not a CI gate.
- **Impact**: Prompting guidance tuned to `claude-fable-5` is applied to `claude-fable-5-1` without re-verification. The v4.5.0 Fable 5.1 comparison already folded the relevant guidance into this plan, so the practical gap is the profile record, not the catalog.
- **Suggested next step**: Run `/tune-prompting` to refresh the profile layer against the live roster and re-stamp the freshness marker; do it at or before the v4.7.0 plan, which is seeded by the same Fable 5.1 comparison.

#### Missing tests / coverage gaps

##### MT-1 - The four human and manual tests have not been run

- **Source phase**: Phase 7 - final phase.
- **Plan reference**: Human and Manual Testing Suggestions, items 1 to 4.
- **Reason**: All four require a person: a throwaway install across three non-Claude platforms with a read-path check; a judged comparison of replies on two platforms; a hand-judged false-positive rate on the reader's own writing; an attempt to apply the shared-storage control to this repository's own agent surface. The installer was also not run live on this host by standing instruction, so item 1's distribution check rests on the installer smoke suites until a person runs it.
- **Suggested next step**: Run items 1 and 3 before `/update release` if time allows (they are quick); items 2 and 4 after the release, since they need the installed block and real infrastructure respectively. Record outcomes here; item 2 resolves `DF-1` and item 4 resolves `DF-2`.

### Carry-forward from v4.4

Reviewed at phase 7 per sub-task 7.3. The v4.4 ledger (`docs/releases/v4/v4.4/known-gaps.md`) was not edited from this branch because a concurrent v4.4.6 session has it modified in the main checkout; the dispositions below are for that session or the release step to apply.

| v4.4 item | Disposition | Reason |
|---|---|---|
| DF-1 - three platform entries use text treatments pending approved marks | Stays open, owned by v4.4 | Vendor-dependent; nothing in v4.5 touches platform marks. |
| WN-1 - Phase 1 ran one tier below the recommendation | Closable (superseded) | Its next step (re-surface the tier at every later pre-flight) was executed at every v4.5 phase boundary and is recorded as `WN-2` above. |
| WN-2 - the superseded-assertion register was incomplete | Closable (scope complete) | Scoped to v4.4 guide phases 3 to 7, all complete and published in the v4.4.5 tag. |
| MT-1 - browser-backed guide verification in CI | Already resolved in v4.4 | Resolved at v4.4's own Phase 7 (PR #150, `guide-render` job); the plan's 7.3 prompt predates that closure. |

Older ledgers: v4.0 `DF-1` (the non-lockstep seven are not byte-locked by the release gate) is narrowed by v4.5 for one block, since the companion validator asserts byte identity of `## Writing Discipline` across all twelve templates; the general item stays open there. v4.1, v4.2, and v4.3 open items are untouched by v4.5 and remain owned by their ledgers.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-1 | Pre-existing lint and format drift in the parity guard | Phase 2 | Phase 2 edits `scripts/check_base_template_parity.py` on purpose (promoting `Writing Discipline` into both guard lists), so the two ruff findings (`UP035`, `UP045`) were fixed and the file formatted in that same deliberate edit; the whole diff is 15 insertions and 3 deletions. |

### Notes (not gaps)

- The offline detector classifies the clause-joining spaced hyphen as `advisory`, not `defect`, after the phase 4 self-scan found 182 legitimate historical uses in `CHANGELOG.md` alone. The Writing Discipline rule still forbids it in new prose; the detector reports it without gating on it. Recorded here so phase 7 reads the detector's class boundary from its docstring rather than from the plan's one-line definition.
- Coverage on `scripts/check_base_template_parity.py` reads 0 percent under `pytest --cov` because its tests drive the script as a subprocess, which the tracer does not follow. No logic changed in this phase (docstring only) and the 16 behavioral tests plus 4 new template tests pass, so this is a measurement limit, not an untested path.
- The five lockstep word ceilings were raised by the measured cost of the block (+110 on `base-claude.md`, +170 on the other four). This was a maintainer decision made before implementation, recorded under Recorded raises in `docs/policy/doc-budgets.md`; it is listed here so phase 7's cost reckoning cannot miss it.
- The deterministic response class in `agentic-endpoint-hardening` is guidance only by maintainer decision: the skill tree has no `scripts/` directory and phase 6 added no executable content. Phase 7 confirmed this by listing the tree, not by reading the body's statement.
- `construction-debt: keep both discipline validators until a third invariant block appears.` `tests/validators/test_writing_discipline_rule.py` and `test_construction_discipline_rule.py` share three roster constants and five structurally identical tests; the parity script holds a third copy of the roster. Consolidating at two would rename a module the v4.1.2 evidence cites and turn a failing file name into a parameter id. The trigger is the third block; at that point move the roster to one shared helper the parity script also reads.
- Two Partial rows in the prose-cliche comparison (`colon-triple`'s three-item payoff, `despite-challenges`) were not promoted to named patterns; the pre-existing `Colon reveals` and `Summary-recap endings` entries already flag both moves. Phase 3's scope was the uncovered register and the countable rhythm rules, which landed.
- Cross-domain chaining: nothing was scoped out of phase 6; the owner, the multi-domain framing, and both handoff references shipped.
