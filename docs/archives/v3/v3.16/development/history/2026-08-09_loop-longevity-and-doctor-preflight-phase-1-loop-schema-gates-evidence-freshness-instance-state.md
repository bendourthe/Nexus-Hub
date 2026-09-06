# Session History - v3.16.2 Phase 1: Loop schema gates, evidence freshness, and instance state

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.2-loop-longevity-and-doctor-preflight.md](../../plans/v3.16.2-loop-longevity-and-doctor-preflight.md)
**Phase**: 1 of 6 (not the final phase; no release-readiness workflow ran)
**Branch**: `develop`
**Outcome**: Complete. Quality gate GO.

## Goal

Give the loop schema the three long-horizon concepts a static definition structurally cannot express, so a loop can pause for human judgment, distrust stale evidence, and resume after a cold start.

## Sub-tasks completed

### 1.1 - Typed human-judgment gates (L1)

Added an optional `gates` field to the Fields table in `references/loop-schema.md`, plus a `## Human-Judgment Gates` section carrying a four-type table (`owner`, `safety`, `publication`, `private-data`), the four things every gate declares (`type`, `question`, `unblocks_on`, `while_waiting`), and the two mandatory rules.

The distinction from `handoff` is stated in three places rather than once, because it is the whole point of the field: `handoff` routes work the loop could not finish AFTER the cap, while a gate interrupts a loop that is succeeding because the next step needs judgment the loop does not own.

Both mandatory rules are stated with their reason, not just their content. The one-concrete-question rule is tied back to the vibe-based `exit_condition` anti-pattern it mirrors. The no-`iteration_cap`-consumption rule is justified as an incentive-design choice: charging the cap for a pause penalizes a loop that correctly asks for judgment against one that plows ahead.

Added the matching Anti-Pattern entry (proceeding without authority on a `safety`, `publication`, or `private-data` decision) and updated the worked example to carry one gate.

### 1.2 - Evidence freshness (L6)

Added an optional `evidence_freshness` field plus an `## Evidence Freshness` section stating precisely why the existing telemetry does not already cover it: `trace_log` records what happened rather than what is still true, and `progress_check` fires when nothing is changing rather than when something that passed long ago has decayed.

Extended the Evaluation Rule so a checker evaluating `exit_condition` must confirm the corroborating evidence is still inside its window, with the cross-link to `[[verification-before-completion]]` framed as extending its fresh-evidence requirement along the time axis a single-pass gate does not have to consider. The scope limit is stated plainly rather than implied: a ten-iteration loop that finishes in an hour has no staleness problem and adding a window to it is ceremony.

### 1.3 - Resumable loop-instance state (L5)

Added an `## Instance State` section separating a loop DEFINITION (the reusable template the Fields table describes) from a loop INSTANCE (one running execution). Specified the five things the record carries and the three mandatory constraints: Nexus-Hub ships no runtime for it, it is gitignored by default under the `[[egress-redaction]]` discipline, and it composes with rather than replaces `[[filesystem-context-patterns]]` and `[[dev-progress-tracker]]` with ownership stated per layer.

Recorded the reverse-engineering provenance generically, per the MCP Registry Policy attribution rule: the doctrine transfers, the runtime is explicitly out of scope.

### Cross-references and library

`SKILL.md` Step 4 now references all three concepts (step 4 for freshness, a new step 8 for gates, an extended step 9 for instance state), and two verification-checklist items were added. `references/loop-library.md`'s `ship-pr-until-green` received the same demonstration gate as the schema's worked example.

### 1.4 - Testing and stabilization

`make` is absent on this host, so both `Makefile` targets were read and run command by command.

## Test results

| Suite | Result |
|-------|--------|
| `tests/` (full) | 2157 passed, 20 skipped, **1 failed** (pre-existing BG-1) |
| `tests/skills` (the subset that reads the catalog) | 509 passed, 3 skipped |
| `catalog/hooks/tests` | 993 passed, 36 skipped |
| `extensions/nexus-skill-server` | 43 passed |
| `extensions/nexus-code-search` | 294 passed, 1 skipped |
| `extensions/nexus-web-fetch` | 29 passed |
| `extensions/nexus-skill-scanner` | 89 passed |
| `extensions/nexus-context-compressor` | 215 passed |
| `validate` guards (7, run individually) | All pass |

The seven guards run individually were `validate_skills.py --bundles-only`, `validate_skills.py --quality`, `run_trigger_evals.py --gate`, `validate_no_personal_paths.py`, `validate_unicode_safety.py`, `check_version_sync.py`, and `check_base_template_parity.py`.

Coverage is **not applicable** to this phase: it changed three Markdown files and zero executable lines. The honest substitutes are the bundle-reference audit in `validate_skills.py` and the 509-test `tests/skills` suite that parses the catalog.

## Deviations and design corrections

1. **The worked-example gate type was changed mid-implementation.** The first draft used a `publication` gate on the PR body before push. That gate would fire on every iteration of `ship-pr-until-green`, turning an automated loop into a manual one and teaching the opposite of the intended lesson. Replaced with a `safety` gate on the rare force-push that rewrites shared history, plus an explicit note that a gate tripping every iteration means the loop's authority was drawn too narrowly.

2. **A pre-existing internal collision was reconciled rather than left standing.** `SKILL.md` already carried a "Human gate checkpoint" workflow-control pattern with an `on_reject` policy. Adding a typed `gates` field beside it without comment would have shipped two competing gate concepts in one skill. Both now cross-link with an explicit split (schema = WHICH and WHAT, pattern = HOW), and the `retry` interaction is resolved once: a retry counts against `iteration_cap` because re-running the gated step is real work, the wait before it does not. This edit was outside the literal sub-task text but inside the plan's stated intent that gates be "clearly distinguished".

3. **The library entry received the demonstration gate too.** The plan made this optional ("if any library loop would now be better with a gate"). It was taken because the schema's worked example and the library entry are literally the same loop, so gating only one would have shipped an internal contradiction. The cost is a duplicated block in two files, recorded as MT-1.

4. **One stale cross-reference was corrected.** A first draft of Step 4 pointed at "the post-cap `handoff` destination in step 9"; step 9 covers state persistence and never names `handoff`. Reworded to drop the false step pointer.

## Troubleshooting trail

No implementation failures. Two environmental frictions:

1. **`make` is unavailable** (inherited WN-1). Resolved by extracting every command from the `validate` and `test` targets and running each directly.
2. **Several suites exceeded the 120s foreground window** and were auto-backgrounded. `nexus-code-search` initially appeared to hang; on a second run it completed in 18.59s, so the first run was cold-cache index building rather than a fault. Two suites were truncated by inner `timeout` values I set myself, which produced partial dot output that could have been misread as a pass. Both were re-run without an inner timeout to get a real terminal line.

## Post-phase steps

| Step | Result |
|------|--------|
| 8.1 gitignore | 0 patterns added (no new artifact; `git status` shows only tracked-file modifications) |
| 8.2 Test review | Re-run complete. Every modified file is covered by the `tests/skills` suite and the bundle audit; the content-level gap is logged as MT-1 |
| 8.3 CI/CD | No change needed. `catalog/skills/**` already inside the `'**'` path filter; concurrency cancel-in-progress and caching already present; skill gate stays `--bundles-only` per v3.14.2 WN-1 |
| 8.4 Known gaps | MT-1 raised; WN-1 and BG-1 re-verified as inherited environmental. Summary table and Last-updated line refreshed |
| 8.5 Docs cleanup audit | No-op. This phase added, moved, and renamed no documentation file; the existing v3.16 report stands |
| 8.6 Devlog | Entry added at the top of `docs/DEVLOG.md` |
| 8.7 Docs | No-op. No frontmatter, no skill count, and no public surface changed, so README, AGENTS.md, and `data/skills.json` are all untouched |
| 8.8 Session history | This file |

## Next steps

Phase 2: the release capability usage gate in `catalog/commands/update.md`, plus its `AGENTS.md` cross-reference. Phase 2 has no prerequisite on Phase 1 and can start immediately. Note that Phase 5 depends on Phase 2, and that Phase 5 is also the owner of MT-1 raised here.
