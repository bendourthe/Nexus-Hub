# Known Gaps - v3.20

**Project**: Nexus-Hub
**Status**: finalized
**Last updated**: 2026-08-24

## v3.20.3

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

> Finalized on 2026-08-24 at the 3.20.3 bump. Open items will be ingested by `/generate-plan` when the next version's plan is created.

### Open Items

#### Not Implemented

None.

#### Deferred

##### DF-1 - No native invocation mapping for platforms with no vendor lever

- **Source phase**: Phase 4 - Invocation-policy metadata
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md` (sub-task 4.1)
- **Reason**: Antigravity, OpenCode, Kimi, Hermes, and Nexus-AI document no per-skill invocation-policy field. Generated command-skills still carry `disable-model-invocation: true` in SKILL.md; those hosts ignore the unknown key. Inventing a sidecar would repeat the v3.15.0 fabricated-companion failure.
- **Suggested next step**: Revisit when a first-party vendor document names a lever. Until then keep the honest gap note in `docs/policy/skill-invocation-policy-levers.md`.

##### DF-2 - Official Claude plugin directory listing not submitted

- **Source phase**: Phase 5 - Official Claude plugin marketplace listing
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md` (sub-task 5.1)
- **Reason**: The phase prepares the package and the maintainer packet. Live Anthropic process (fetched 2026-08-24) is the [plugin directory submission form](https://clau.de/plugin-directory-submission), not a PR to `anthropics/claude-plugins-official`. Opening either from the implement loop is out of scope.
- **Suggested next step**: Maintainer submits the form using `docs/v3/v3.20/development/claude-marketplace-submission.md`. After listing, add the `@claude-plugins-official` install line to README.

#### Bugs / Regressions

None.

#### Warnings

None open. WN-6 (Codex docs timeout) is resolved below.

Phase 1 reused the v3.20.2 scoped `--path` personal-paths scan (WN-3). Inherited WN-4 and WN-5 are closed in the v3.20.2 Resolved table.

#### Missing Tests / Coverage Gaps

None new. Phase 4 added emission assertions on the existing integration files plus two validator warning tests. The ubuntu `tests` job already runs `tests/integrations` and `tests/validators`. `tests-windows` now also runs the tiny-fixture emission pair (`test_catalog_adapters.py`, `test_codex_invocation_policy.py`). Full 324-skill flatten stays on ubuntu.

#### Quality-Gate Gaps

None. Existing `ci.yml` already treats `scripts/lib/integrations/**`, `tests/integrations/**`, `tests/validators/**`, and `docs/policy/**` as relevant (job-level classifier, no workflow-level `paths:` filter). Concurrency cancel-in-progress and pip cache are unchanged. Phase 4 added a cheap `tests-windows` emission step. Phase 5 structural plugin tests ride the existing `tests/validators` jobs. `python scripts/check_installer_parity.py` PASS. No new required-check context.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-6 | Codex skills docs timed out during Phase 4 | `/update release` | Re-fetched `https://learn.chatgpt.com/docs/build-skills` on 2026-08-24. Mapping unchanged: `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. Discovery still omits `~/.codex/skills` (low DRIFT, eighth cycle). |

## v3.20.2

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 1 | 2 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

> Finalized on 2026-08-23 at the 3.20.2 bump. Open items will be ingested by `/generate-plan` when the next version's plan is created.

### Open Items

#### Not Implemented

None.

#### Deferred

None open.

#### Bugs / Regressions

None open.

#### Warnings

##### WN-3 - Full-tree `validate_no_personal_paths.py` is too slow to finish in the implement loop on OneDrive

- **Source phase**: Phase 1 - Authoring-standard foundation
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.2-interface-craft-skills.md` (sub-task 1.4)
- **Reason**: The default scan walks `catalog/`, `docs/`, and `templates/`. On this host the walk sat in `validate_no_personal_paths.py` for more than 12 minutes with no output. Phase 1 therefore ran `--path` against the files this phase touched (clean) and left the default walk to CI.
- **Suggested next step**: Confirm CI's `validate` job still finishes the default walk on ubuntu-latest. If maintainers hit the same hang locally, add progress output or skip `docs/archive/`.

#### Missing Tests / Coverage Gaps

None. Cluster skills that shipped `evals/trigger-cases.json` pass `run_trigger_evals.py --gate`. Catalog-wide missing cases remain v3.20.1 MT-1.

#### Quality-Gate Gaps

None. Existing `ci.yml` already classifies non-docs paths as relevant (so `catalog/skills/**`, `data/**`, and `AGENTS.md` run the full validate job), uses concurrency cancel-in-progress, and caches pip. `--bundles-only` is unchanged (v3.14.2 WN-1). No new workflow was added.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| BG-2 | Comparison D1 truncated `agents/openai.yaml` sidecars | Phase 7 | Re-measured: 140 sidecars, 0 incomplete after YAML unfold. Comparison examples (`unit-tests` "improving test cove", `context-degradation` "mid-sessio") are folded-scalar line wraps of complete sentences. The six new cluster skills have no sidecar, so they did not inherit a generator defect. |
| DF-6 | Catalog-count drift in prose surfaces (315 vs 321) | `/update release` | README, AGENTS.md, plugin.json, and marketplace plugin.description now read 321. |
| WN-4 | `check_docs_conventions.py` pinned `docs/v3/v3.19/` | v3.20.3 | Resolves `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` from plugin.json. Future majors such as `docs/v4/` stay unscanned. Live v3.20 tree scanned clean (32 markdown files, 0 findings). |
| WN-5 | `generate_manifest.py` hashed gitignored files | v3.20.3 | Enumerates `git ls-files -co --exclude-standard` under covered roots when git is available; `os.walk` remains the non-git fallback used by `verify_install.py`. |

## v3.20.1


### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 5 | 0 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None. None of the 40 planned skills were deferred.

#### Deferred

##### DF-1 - Comparison item X1: outbound enrichment scripts

- **Source phase**: Phase 5 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.1-adoption-cybersecurity-skills.md` (comparison items, Complexity Tracking)
- **Reason**: The comparison catalog ships hundreds of scripts that call third-party intel APIs. Nexus-Hub's reverse-engineering-first policy forbids new outbound calls, credentials, and runtime dependencies. Phase 4 skills describe how a human or existing local toolchain would do the work; they do not wrap VirusTotal, urlscan, MISP, or similar.
- **Suggested next step**: Keep refused. A future skill may document how to consume a user-supplied local cache, never a new installer-copied client.

##### DF-2 - Comparison item X2: verbatim comparison-catalog prose

- **Source phase**: Phase 5
- **Plan reference**: same plan, licensing gate 4.0; decision `docs/decisions/implemented/policy/2026-08-23-security-content-independent-authorship.md`
- **Reason**: Source is Apache-2.0; Nexus-Hub is MIT. Copying or close-paraphrasing SKILL.md bodies would mix licenses in the distributed catalog.
- **Suggested next step**: Keep refused. New security skills continue to be written from public primary sources.

##### DF-3 - Comparison item X3: vendor-SKU skills

- **Source phase**: Phase 5
- **Plan reference**: same plan, Phase 4 consolidation; decision `docs/decisions/implemented/architecture/2026-08-23-vendor-neutral-capability-consolidation.md`
- **Reason**: One-skill-per-product would explode Tier-1 tokens and duplicate capability. Coverage landed as 40 vendor-neutral jobs (~4.3:1).
- **Suggested next step**: Keep refused unless a later decision re-opens vendor-named identity.

##### DF-4 - Comparison item X4: `allowed-tools` frontmatter

- **Source phase**: Phase 5
- **Plan reference**: same plan; decision `docs/decisions/rejected/policy/2026-08-23-adopt-allowed-tools-frontmatter.md`
- **Reason**: No fetched official vendor document names the field. Inventing it would repeat the fabricated companion-file failure withdrawn in v3.15.0.
- **Suggested next step**: Revisit only after a vendor document with `source_url` and a verified date classifies the lever VERIFIED.

##### DF-5 - Comparison item X5: free-text taxonomy fields

- **Source phase**: Phase 5
- **Plan reference**: same plan, comparison drop list
- **Reason**: Nexus-Hub already has a closed category list plus optional framework ID lists. A parallel free-text taxonomy would not be validated and would not route.
- **Suggested next step**: Keep refused. New routing signal belongs in `description` / `summary_l0` / `overview_l1` or in a new optional list field with the same shape contract as the framework keys.

#### Bugs / Regressions

None open. The version-directory lexical-sort defect is resolved below.

#### Warnings

##### WN-1 - Thirteen SKILL.md descriptions exceed the agentskills.io 1024-character cap

- **Source phase**: Phase 1 - Framework and conformance tooling
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.1-adoption-cybersecurity-skills.md` (sub-task 1.3)
- **Reason**: Nexus-Hub's pushy-description convention (verbatim trigger phrases plus a SKIP clause) predates the conformance guard. Enforcing 1024 as a hard error on the current catalog would fail `make validate` on 13 existing skills, contradicting the phase acceptance criterion that the guard exits 0 on the current catalog. Those names are grandfathered in `OVERLONG_DESCRIPTION_ALLOWLIST`; a new over-long description is still a hard error.
- **Suggested next step**: Trim the 13 descriptions under 1024 characters (without dropping trigger phrases or SKIP clauses), then remove each name from the allowlist.

##### WN-2 - Sixty-five SKILL.md bodies still exceed the 500-line warning tier

- **Source phase**: Phase 3 - Size-norm remediation; recounted Phase 5
- **Plan reference**: same plan, Phase 3 (plan cited 107; live count after relocation is 65; none exceed the 800-line hard cap)
- **Reason**: The 800-line cap is an error; 500 is a grandfathered warning. Relocating the remaining 65 would be a separate docs-structure pass, not this plan's content expansion.
- **Suggested next step**: Relocate long-tail sections of the longest bodies into `references/` the next time those skills are substantially edited. Do not bulk-rewrite 65 skills in a patch.

#### Missing Tests / Coverage Gaps

##### MT-1 - Most catalog skills still lack `evals/trigger-cases.json`

- **Source phase**: Phase 4 / Phase 5
- **Plan reference**: same plan, sub-task 4.3 (evals are optional; missing is WARN, never FAIL)
- **Reason**: 55 of 315 skills ship trigger cases (the 40 new security skills plus 15 pre-existing). The remaining 260 are uncovered. The gate is incremental by contract.
- **Suggested next step**: Add trigger cases when a skill is next rewritten, prioritizing dual-use and high-traffic routing collisions.

#### Quality-Gate Gaps

None. This release introduces no new opt-in capability, installer flag, or host surface.

### Resolved

##### BG-1 - Comparison skill walked version directories in lexical order

- **Source phase**: Phase 5 (confirmed; instruction already patched)
- **Resolved**: 2026-08-23. `catalog/skills/workflow/cross-project-comparison/SKILL.md` Step 6.5 now requires enumerating version directories by parsed `(major, minor)` integers, scanning every `docs/v*/v*/plans/` tree, and confirming against the highest plan on disk. The live failure (resolving v3.17.12 while plans existed through v3.20.0) is recorded in `docs/v3/v3.20/comparisons/v3.20.1-comparison-cybersecurity-skills-library.md` and in `docs/v3/roadmap-prioritization.md`. `scripts/check_docs_retention.py` already sorts minor dirs numerically. No remaining code path in this repo still sorts version directories as strings for slotting.

## v3.20.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

None.

#### Bugs / Regressions

None.

#### Warnings

None.

#### Missing Tests / Coverage Gaps

None.

#### Quality-Gate Gaps

None.

### Resolved

##### DF-census - Plan census 271 -> 272 was stale

- **Source phase**: Phase 3
- **Resolved**: 2026-08-23. Live catalog was 274 before Phase 1 and 275 after. Plan success metric and registry prompt updated to 275 / 274 -> 275. No product gap.
