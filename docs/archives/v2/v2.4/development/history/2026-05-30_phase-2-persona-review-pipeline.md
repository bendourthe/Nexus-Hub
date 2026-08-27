# Session History - v2.4.0 (adoption-compound-engineering-plugin) Phase 2: Persona review pipeline

**Date**: 2026-05-30
**Plan**: [docs/archives/v2/v2.4/plans/adoption-compound-engineering-plugin.md](../../plans/adoption-compound-engineering-plugin.md)
**Phase**: 2 of 8 - Persona review pipeline (A2 persona code review, A3 persona plan review, A8 agent-native lens)
**Sub-tasks**: T008 (persona agent library), T009 (multi-agent-code-review skill + 3 references + review-changes command), T010 (plan-review skill + 5 plan-lens agents), T011 (agent-native-reviewer + tool-design extension), T012 (testing + stabilization)
**Outcome**: Two new code-review skills (`multi-agent-code-review`, `plan-review`) shipped and registered (code-review 11 -> 13; total 239 -> 241); 13 new generic persona/lens reviewer agents added under `catalog/agents/` (10 -> 23); `tool-design` extended with the action+context-parity principle. All validators green; orphan-bundle 0/0 across 241 skills; repo-level tests 331 passed. A real persona-dispatch benchmark over a seeded fixture PASSED. Live skill-eval-loop run + full end-to-end pipeline run deferred (DF-v24-2). Ready to advance to Phase 3.

---

## Goal

Adopt the compound-engineering persona-fanout review: a multi-agent code review (A2), a persona review of plans/requirements before code (A3), and an agent-native review lens (A8), backed by a re-authored generic persona agent library. Every adopted item is local catalog content (markdown skills + agents) re-authored generically with no source-repo attribution and zero new outbound calls / credentials / dependencies. The pipeline consumes the Phase-1 `confidence-anchored-scoring.md` reference (A4) for its dedup / promotion / gate discipline.

## Steps taken

1. **Pre-implementation review**: read the full plan and the Phase-2 sub-tasks; the Phase-1 `confidence-anchored-scoring.md` (the finding schema + scoring policy the pipeline depends on); the existing agents (`code-reviewer`, `security-reviewer`, `architect`, `refactor-cleaner`) to learn the agent frontmatter format and decide the reuse mapping; an exemplar skill (`solution-knowledge-base`) for the SKILL.md contract; `tool-design/SKILL.md` (T011 target) and `security-review/SKILL.md` (the Phase-1 forward-reference); the comparison Section 4/5/9/11 for the CE pipeline stages and persona catalog; the Makefile and the three data registries (skills.json schema, marketplace structure, SKILL_INDEX format) to register correctly.

2. **T008 - persona agent library** (7 new agents under `catalog/agents/`): `maintainability-reviewer`, `testing-reviewer`, `performance-reviewer`, `reliability-reviewer`, `api-contract-reviewer`, `adversarial-reviewer`, `project-standards-reviewer`. Each is read-only, single-lens, language-agnostic, and returns the JSON findings contract (title / severity P0-P3 / file / line / confidence 0/25/50/75/100 / persona / requires_verification / pre_existing / autofix_class / suggested_fix). Reuse mapping (documented, not duplicated): `code-reviewer` = correctness, `security-reviewer` = security, `architect` = deep-design escalation, `refactor-cleaner` = autofix applier. CE's Rails/Swift personas were not imported (language-agnostic posture).

3. **T009 - multi-agent-code-review** (`SKILL.md` + `references/{persona-selection,findings-schema,validator-template}.md` + `catalog/commands/review-changes.md`): the seven-stage pipeline (scope resolution -> intent discovery -> per-diff persona selection -> bounded parallel dispatch with backpressure -> confidence-anchored merge in fixed order -> independent refutation pass for externalizing modes -> model tiering) with four modes (interactive / autofix / report-only / headless). Registered in all three data files.

4. **T010 - plan-review** (`SKILL.md` + 5 plan-lens agents): `coherence-reviewer`, `feasibility-reviewer`, `product-lens-reviewer`, `design-lens-reviewer`, `scope-guardian-reviewer`; reuses `security-reviewer` + `adversarial-reviewer` for those lenses. Read-only document review emitting a severity-tagged table + coverage note. Distinguishes the persona-fanout from the single-agent `cross-artifact-analyzer` / `analyze-spec`. Registered in all three data files.

5. **T011 - agent-native lens** (`catalog/agents/agent-native-reviewer.md` + `tool-design` extension): the action+context-parity reviewer, wired as a conditional persona in the T009 selection table; a new "Agent-native design" section added to `tool-design/SKILL.md` teaching the parity principle and cross-linking the agent.

6. **T012 - stabilization**: ran the validators directly (make unavailable on the host), the repo-level pytest, an ASCII scan + fix on all new/modified files, and a real persona-dispatch benchmark over a seeded fixture; recorded the live-eval / full-pipeline deferral (DF-v24-2); ran the post-phase documentation sequence.

## Troubleshooting

- **A stray CJK character (U+771F) landed in `validator-template.md`**: the first draft of the refutation prompt embedded a literal non-ASCII character mid-sentence. Caught by a targeted non-ASCII scan, removed with a unique-match edit, and the awkward note it had spawned was deleted.
- **Em-dashes (U+2014) across the 13 new agents + the command**: the agent prose used em-dashes as separators, which violates the ASCII-only English-Markdown rule and would add to the exact debt Phase 7 (T029) is clearing. The unicode-safety validator treats them as warnings (not errors), and the two pre-existing agents (`code-reviewer`, `security-reviewer`) already contain them, but introducing new ones is wrong. A scoped replacement (em/en-dash -> `-`, curly quotes -> straight, ellipsis -> `...`, NBSP -> space) was applied to ONLY the 14 files this phase created - the pre-existing agents were left untouched (out of scope). All 20 new/modified files re-verified ASCII-clean.
- **The dedicated persona agents are not dispatchable subagent types in the authoring harness**: the benchmark could not dispatch `maintainability-reviewer` et al. by name (they ship as catalog templates for end-user environments). The two reused agents that ARE registered (`code-reviewer`, `security-reviewer`) were dispatched instead, which validates the lens discipline and the JSON contract end-to-end; the full-pipeline run is deferred (DF-v24-2).

## Assumptions

- Agents do not require `data/` registry updates (only skills do, per AGENTS.md); creating 13 agents needed no skills.json / marketplace / SKILL_INDEX edit, and the recursive installer copy distributes them without an installer edit.
- The reuse mapping honors the plan's "reuse existing agents where they map; add only the missing personas": `code-reviewer` (broad correctness focus) backs correctness, `security-reviewer` backs security, and `refactor-cleaner` (a mutating action agent) is the autofix applier rather than a read-only review persona.
- The benchmark is an LLM-judged verification artifact appropriate for `docs/.../development/`, not a `make test` unit test; the seeded fixture is intentionally not imported by any test (its planted defects are deliberate).
- Catalog count-prose updates (skills + the "10 agents" line in AGENTS.md/README) are deferred to the version bump per WN-v24-1; per-phase doc sync does not touch them.
- `make` / `shellcheck` / a model CLI are unavailable on this Windows host, so validators were invoked directly, lint is N/A (no shell scripts added), and the live skill-eval-loop run is deferred (same constraint as Phase 1's DF-v24-1).

## Testing results

- Registry reconciliation: skills.json array 241 == statistics.total_skills 241; code-review = 13 in skills.json / statistics / marketplace; marketplace category sum 241; SKILL_INDEX 241 skill rows; no duplicate skill names; both new skills present.
- `make validate` equivalent (direct): JSON catalogs OK, orphan-bundle audit PASS 0/0 across 241 skills (the 3 pipeline references all linked from SKILL.md), quality pass 0 errors / 575 warnings (pre-existing Phase-7 debt; neither new skill flagged), no-personal-paths / unicode-safety / supply-chain-iocs / workflow-security / solution-frontmatter all exit 0.
- ASCII scan: all 20 new/modified files clean after the em-dash / CJK fix.
- `tests/` (repo-level validators): 331 passed in ~5m25s (no test hardcodes a skill count, so the registry edits regress nothing).
- `make lint`: N/A - Phase 2 added no shell scripts.
- **Benchmark (PASS)**: dispatched the correctness persona (`code-reviewer`) and the security persona (`security-reviewer`) over `docs/archive/v2/v2.4/development/phase-2-benchmark/seeded_diff.py`. Correctness surfaced only the planted off-by-one in `paginate()` (P1, confidence 100); security surfaced only the planted SQL injection in `find_user()` (P0, confidence 100); each stayed in its lane; both emitted valid findings-schema JSON; the clean control `clamp()` drew zero findings. Recorded in `phase-2-benchmark/README.md`.

## Deviations

- **DF-v24-2**: the live `skill-eval-loop` trigger run (1.0 positive / 0.0 fenced-negative) and the full end-to-end pipeline run (all conditional personas, the independent validation pass, cross-reviewer promotion, model tiering) were deferred - no model CLI on PATH, and the dedicated persona agents are not dispatchable subagent types in the authoring harness. Substituted with a static trigger-surface check (both descriptions carry verbatim trigger phrases + a SKIP clause and cross-fence each other) and a real two-persona dispatch benchmark. Foldable into the Phase-8 T037 live run.
- **WN-v24-1 extended**: the agent-count prose in AGENTS.md ("10 agents") is now stale (23 agents). Folded into the existing WN-v24-1 count-prose deferral rather than edited per-phase.
- No `# DEVIATION:` markers were left in any artifact; the plan was followed as written (the reuse mapping is a documented design choice within the plan's "reuse where they map" latitude).

## Next steps

- Phase 3: close the compound loop - add the STRATEGY anchor (A5), wire `generate-plan` / `implement-phase` / `continuous-learning` to read the `docs/solutions/` knowledge base, and add the cross-tool `session-query` skill (A7).
- Fold `multi-agent-code-review` and `plan-review` into the Phase-8 T037 live skill-eval-loop run (clears DF-v24-2); optionally run the full pipeline once the dedicated persona agents are registered as dispatchable subagents in a consuming environment.
- At the v2.4.0 version bump, refresh the AGENTS.md / README catalog-count prose (241 skills / 21 categories, 23 agents) per WN-v24-1 and update the CHANGELOG (T040).
