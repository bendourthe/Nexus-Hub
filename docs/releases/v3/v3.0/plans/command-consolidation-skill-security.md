# Plan -- v3.0.0: Command Consolidation + Skill-Security Scanner + Orchestration Adoption

**Project**: Nexus-Hub
**Version**: v3.0.0
**Slug**: command-consolidation-skill-security
**Plan Type**: Refactor + Feature (major-version consolidation + reverse-engineer-first adoption)
**Created**: 2026-06-02
**Goal**: Collapse the 41-command surface to 14 verb-first, scope-able commands (no behavior lost); adopt the SkillSpector skill-security capability as a local internal scanner; adopt the agentic-orchestration insights as catalog content; close the systemic version-sync gap that turned CI red; and carry forward every open v2.4.0 known-gap plus the one still-open v2.3.0 deferral (DF-v23-9).

## Overview

v3.0.0 is a major release with three pillars. **Pillar 1 (command consolidation)** collapses 41 slash commands into 14 verb-first commands (`describe`, `plan`, `implement`, `test`, `review`, `update`, `compare`, `research`, `skills`, `spec`, `session`, `setup`, `memory`, `usage`) using a thin-command-dispatches-to-retained-skill architecture and an interactive-scope-plus-optional-argument mechanism (bare `/review` asks for scope; `/review security` runs that scope directly). No existing behavior is removed -- the 41 rich skill bodies are retained as scope modules, and the 41 old command names ship as deprecation shims through v3.x (removed at v4.0.0). The full design is in [`docs/releases/v3/v3.0/command-consolidation-design.md`](../command-consolidation-design.md). **Pillar 2 (skill-security)** reverse-engineers NVIDIA SkillSpector's 16-class skill scanner into a local internal `nexus-skill-scanner` (static engine `re-full`; optional YARA + offline-first OSV.dev `re-partial`; LLM semantic adjudication `skill-native`), unifying the existing fragmented validators and gating Nexus-Hub's own catalog in CI. See [`docs/releases/v3/v3.0/comparisons/v3.0.0-comparison-skillspector.md`](../comparison-skillspector.md). **Pillar 3 (orchestration)** adopts the Dynamic-Workflows / subagents-vs-agent-teams insights as one decision-guide skill plus command-body fan-out guidance. See [`docs/releases/v3/v3.0/comparisons/v3.0.0-comparison-agentic-orchestration.md`](../comparison-agentic-orchestration.md).

Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first): `skill-native` adoptions ship first (Phase 2), then the command consolidation that depends on the retained skills (Phases 3-5), then the `re-full` scanner engine (Phase 6), then the `re-partial` optional modules (Phase 7), then migration/docs (Phase 8), then ingested known-gaps (Phase 9), then live verification and release (Phase 10). The v2.4.0 CI failure (installers stuck at `2.3.0` while `plugin.json` moved to `2.4.0`) was already hotfixed on `main` (commit `c68b8b9`); Phase 1 adds the *systemic* fix -- a single authoritative version-bump-set with a CI drift guard, owned by `/update version` -- so the class of bug cannot recur.

Every change is local catalog content, retained skills, or a local Python scanner that reuses the user's own model CLI. The only network surface introduced anywhere in v3.0.0 is the optional, default-off, opt-in OSV.dev dependency lookup (Phase 7), which sends only package-coordinate tuples and ships with an offline fallback. Zero new credentials, zero new third-party data processors, and (by default) zero new outbound calls.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/v3/v3.0/constitution.md - skipping check. Recommend running /constitution to establish project principles.

Informational note: although no ratified `constitution.md` exists, this plan was authored to honor Nexus-Hub's de-facto MUST principles encoded in `AGENTS.md` -- the MCP Registry Policy reverse-engineer-first decision tree, the zero-new-outbound release invariant, the cross-platform `.sh`/`.ps1` parity rule, the installer-aware change rule, and the ASCII-only Markdown convention. Consider running `/constitution` (then `/spec constitution`) to formalize these before or during v3.0.0.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Foundation: version-sync guard + scaffolding | Systemic version-drift guard in CI; thin-command template + scope mechanism reference ready |
| 2 | skill-native adoptions (RE-first) | `agent-orchestration-primitives` + `skill-security-scan` skills shipped and registered; `multi-agent-coordinator` enriched |
| 3 | Core lifecycle commands I | `/describe`, `/plan`, `/implement`, `/test` shipped (renames + merges + iterative coverage loop) |
| 4 | Review + Update commands | `/review` and `/update` shipped (the two largest merges) |
| 5 | Remaining commands + aliases | `/compare`, `/research`, `/skills`, `/spec`, `/session`, `/setup`, `/memory`, `/usage` + permanent `/constitution` and `/commit` aliases |
| 6 | nexus-skill-scanner engine (re-full) | Static 16-class scanner, scoring, SARIF/JSON/MD, validator subsumption, CI catalog gate |
| 7 | scanner optional modules (re-partial) | Optional YARA module + offline-first opt-in OSV.dev lookup |
| 8 | Deprecation shims + migration + counts | 41 old commands -> forwarding shims; migration doc; count prose + 5 templates updated |
| 9 | Ingested known-gaps | DF-v24-7 extractors, WN-v24-2 heading cleanup, NI-v24-1 decision closed |
| 10 | Live verification + release readiness | Catalog dogfood scan, env-gated re-deferrals, DF-v23-9 re-evaluation, `/update release` to v3.0.0 |

---

## Phase 1: Foundation -- version-sync guard + command scaffolding

**Goal**: Close the CI version-drift root cause systemically and scaffold the consolidation architecture.
**Prerequisites**: None (the 2-line installer hotfix already shipped to `main` as `c68b8b9`).
**Stability Gate**: `make validate` passes; the new version-sync guard runs in CI and detects an injected drift in its test; the thin-command template and scope-mechanism reference exist.

### Sub-tasks

#### 1.1 -- Version-sync drift guard

- [ ] T001 [P] Add scripts/check_version_sync.py to detect version drift across all version-carrying surfaces

**Objective**: Make the v2.4.0-class failure (installers at 2.3.0, plugin.json at 2.4.0) impossible to ship again.

**Prompt**:
> Create `scripts/check_version_sync.py` (stdlib only, type-annotated, module docstring). It reads the canonical version from `.claude-plugin/plugin.json` and asserts every other version-carrying surface matches it: `scripts/installer.sh` (`NEXUS_HUB_VERSION="X.Y.Z"`), `scripts/installer.ps1` (`$script:NexusHubVersion = "X.Y.Z"`), `data/marketplace.json` plugin version, the latest `CHANGELOG.md` heading, and README/AGENTS.md catalog-version prose. Exit non-zero with a per-file diff listing on any mismatch; `--json` for CI. Add pytest at `tests/validators/test_check_version_sync.py` covering an in-sync tree (pass) and an injected-drift fixture (fail). Do not add a `.ps1` sibling (a `.py` validator is cross-platform per the NI-v24-1 precedent).

#### 1.2 -- Wire the guard into CI and the installers

- [ ] T002 Wire check_version_sync into Makefile + .github/workflows/ci.yml and register it in both installers

**Objective**: Run the guard automatically and distribute it.

**Prompt**:
> Add a `check_version_sync.py` invocation to the `make validate` target and the CI validate job so a version-drift fails the build. Register `scripts/check_version_sync.py` as an explicit-name copy step in BOTH `scripts/installer.sh` (near the `generate_report.py` block, ~line 1395) AND `scripts/installer.ps1` (~line 1656), targeting `~/.nexus-hub/scripts/`. Confirm `make validate` still exits 0 on the current in-sync tree.

#### 1.3 -- Thin-command template + scope mechanism reference

- [ ] T003 [P] Create catalog/style-guides/command-scope-mechanism.md and a thin-command template

**Objective**: Standardize how every consolidated command resolves scope and delegates.

**Prompt**:
> Create `catalog/style-guides/command-scope-mechanism.md` documenting the uniform interactive-scope-plus-optional-arg contract from `docs/v3/v3.0/command-consolidation-design.md` Section 4 (parse `$ARGUMENTS` -> recognized scope token skips the prompt; else show a numbered scope menu with a recommended default; `full`/`all` runs all focused scopes in order; delegate to the retained skill). Add a thin-command skeleton template the later phases copy. Place it under `catalog/style-guides/` (NOT `catalog/commands/`, so it does not surface as a slash command); it auto-installs to `~/.nexus-hub/style-guides/`.

#### 1.X -- Testing and Stabilization

- [ ] T004 Run and stabilize Phase 1 tests

**Objective**: Generate and run all tests for this phase. Iterate until stable.

**Prompt**:
> Run `pytest tests/validators/test_check_version_sync.py` and `make validate`. Confirm the guard detects the injected-drift fixture and passes the in-sync tree. Fix all failures. After green, run `/session history` (formerly `/generate-session-history`) to document Phase 1.

### Phase 1 Exit Checklist

- [ ] All sub-tasks completed
- [ ] check_version_sync guard green on the in-sync tree and red on injected drift
- [ ] Guard wired into make validate + CI + both installers
- [ ] Thin-command template + scope reference exist
- [ ] Ready to advance to Phase 2

---

## Phase 2: skill-native adoptions (reverse-engineer-first)

**Goal**: Ship the zero-code skill replacements that close the orchestration and skill-security intent gaps before any command or engine work.
**Prerequisites**: None beyond Phase 1.
**Stability Gate**: Both new skills parse as YAML, carry the six required body sections + pushy description + SKIP clause, pass the orphan-bundle audit, are registered in all three registries, and `make validate` is green.

### Sub-tasks

#### 2.1 -- Orchestration decision-guide skill

- [ ] T005 [P] Create catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md (+ references/five-patterns.md)

**Objective**: Adopt the Dynamic-Workflows / subagents-vs-agent-teams insights as one decision guide.

**Prompt**:
> Create `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md`. It is a decision guide naming the four primitives (single agent / subagents / agent teams / Dynamic Workflows), their envelopes (subagents = isolation + compression, no peer comms; agent teams = persistent peers + shared blockedBy task list, messy past 5; Dynamic Workflows = JS orchestration script, up to 16 concurrent / 1,000 total, intermediates off-context, adversarial convergence, crash-safe/resumable), and a "start single, escalate only on a measured problem" gate. Include the three failure modes (vague tasks -> duplication; verifiers declaring victory without verifying; compounding token cost -> tier models + budget controls) and the "don't parallelize code-writing" warning. Push the five orchestration patterns (prompt chaining, routing, parallelization, orchestrator-worker, evaluator-optimizer) into `references/five-patterns.md` and link it. Pushy description with verbatim trigger phrases + SKIP clause; cross-link `[[multi-agent-coordinator]]`, `[[adversarial-verifier]]`, `[[competitive-generation]]`, `[[ai-billing-safeguards]]`. Keep the body under 500 lines.

#### 2.2 -- Skill-security semantic-adjudication skill

- [ ] T006 [P] Create catalog/skills/security/skill-security-scan/SKILL.md (+ references/detection-classes.md)

**Objective**: Adopt SkillSpector's Stage-2 semantic analysis as a skill (no bundled LLM client, no key).

**Prompt**:
> Create `catalog/skills/security/skill-security-scan/SKILL.md`. It instructs the agent to read the deterministic findings emitted by `nexus-skill-scanner` (Phase 6) and adjudicate them: filter false positives (especially fenced-code examples in a producer catalog), explain malicious intent, and assign a final verdict, mirroring SkillSpector's two-stage design. Document the 16 detection classes + their MITRE/D3FEND/NIST framework IDs + public-source URLs in `references/detection-classes.md` and link it (this satisfies the framework-mapping companion convention). Pushy description with trigger phrases ("scan this skill", "is this skill safe to install", "check a skill for malicious patterns") + SKIP clause (offensive tooling, generic code review). Six required body sections incl. Common Rationalizations + binary Verification. Note that until Phase 6 lands, the skill can adjudicate manually-collected findings.

#### 2.3 -- Enrich multi-agent-coordinator

- [ ] T007 Enrich catalog/skills/orchestration/multi-agent-coordinator/SKILL.md with context-centric decomposition

**Objective**: Fold the PDF design principles into the existing orchestration skill.

**Prompt**:
> Edit `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` to add: the context-centric-decomposition principle (split by context boundaries, not by role; the implementer should write that feature's tests because it already has the context), a cross-link to the five-pattern catalog in `[[agent-orchestration-primitives]]`, and a "when NOT to go multi-agent" gate. Keep the body under the 800-line soft cap (move long examples to a `references/` file if needed). Pure markdown; no behavior change to any script.

#### 2.4 -- Register the two new skills

- [ ] T008 Register agent-orchestration-primitives + skill-security-scan in data/SKILL_INDEX.md, data/skills.json, data/marketplace.json

**Objective**: Catalog registries reflect the two additions.

**Prompt**:
> Add both skills to all three registries per `AGENTS.md`: one row each in `data/SKILL_INDEX.md` (update the Total line), one entry each in `data/skills.json` `skills` array (full schema; security scores default 100/100/95) with recomputed `statistics`, and increment the `orchestration` and `security` category `skill_count` + `total_skills` in `data/marketplace.json`. Add both to `scripts/validate_skills.allowlist.json` if their pushy descriptions exceed the 250-char ceiling. Run `make validate` (must exit 0) and the MCP skill-server suite.

#### 2.X -- Testing and Stabilization

- [ ] T009 Run and stabilize Phase 2 tests

**Objective**: Validate the catalog and the skill-server consumption. Iterate until stable.

**Prompt**:
> Run `make validate`, the orphan-bundle audit, and the MCP skill-server pytest suite. Confirm both new skills parse, are registered consistently (counts agree across all three registries), and cross-links resolve. Fix all failures. After green, run `/session history` to document Phase 2.

### Phase 2 Exit Checklist

- [ ] All sub-tasks completed
- [ ] Both skills shipped, registered, orphan-clean, validator-green
- [ ] multi-agent-coordinator enriched, under soft cap
- [ ] Ready to advance to Phase 3

---

## Phase 3: Core lifecycle commands I (describe, plan, implement, test)

**Goal**: Ship the first four lifecycle commands as thin dispatchers over the retained skills.
**Prerequisites**: Phase 1 (thin-command template). Phase 2 recommended (orchestration skill for `/test` fan-out guidance).
**Stability Gate**: Each new command resolves scope (bare = prompt, arg = direct), delegates correctly, and the old behavior is reachable; old command files still work (shims land in Phase 8).

### Sub-tasks

#### 3.1 -- /describe

- [ ] T010 [P] Create catalog/commands/describe.md (generalized analyze-codebase)

**Objective**: Rename + generalize `analyze-codebase` to describe any directory, software or not.

**Prompt**:
> Create `catalog/commands/describe.md` as a thin dispatcher delegating to the `analyze-codebase` skill. Scopes: `full` (default), `structure`, `deps`, `architecture`, `onboarding`. Generalize the intro so it works on any selected directory (a codebase OR a non-software project) and produces a clear, well-structured description -- a way to get familiar with an inherited project. Use the scope-mechanism contract from `catalog/style-guides/command-scope-mechanism.md`. Keep under 150 lines.

#### 3.2 -- /plan

- [ ] T011 [P] Create catalog/commands/plan.md (generate-plan + goals + dynamic-workflows robustness; todos/issues scopes)

**Objective**: Make `/plan` the robust merge of `generate-plan` + goals framing + dynamic-workflows orchestration (see `docs/v3/v3.0/command-consolidation-design.md` section 2A).

**Prompt**:
> Create `catalog/commands/plan.md` delegating to `generate-plan` + `implementation-plan` + `product-strategy` + `generate-todos` + `tasks-to-issues` + `agent-orchestration-primitives`. Implement the full design in `docs/v3/v3.0/command-consolidation-design.md` section 2A. (1) Preserve everything generate-plan did: discovery interview (greenfield/feature/refactor), from-comparison mode + RE-first ordering, prior-version known-gaps ingest, knowledge-base + strategy grounding, Constitution Check + Complexity Tracking, and the strict `T###` task-line file-format contract. (2) Goals framing: a `goals` scope and a goals-first step at the top of every scope that fixes the target problem, persona, and observable definition-of-done BEFORE decomposition (seeded from `product-strategy`); `/plan goals <one-liner>` accepts an inline goal (Codex `/plan <inline>` style) and returns a crisp goal + DoD without a full plan. (3) Dynamic-workflows robustness when available: offer multi-angle drafting (draft the plan from several independent angles, adversarially weigh them, synthesize the strongest), parallel research at scale, and write large fan-out phases' prompts to recommend dynamic-workflow execution (cross-link `[[agent-orchestration-primitives]]`, carry the scope-first token caution). (4) Graceful degradation (REQUIRED): detect dynamic-workflow availability (plan-gated research-preview, Claude Code v2.1.154+, `/config` toggle) and fall back to single-agent planning when off/unavailable; never assume present, never hard-depend, always opt-in with the token caution. Scopes: `goals`, `new`/`feature`/`refactor`, `from-comparison`, `todos` (bootstrap docs/todos.md), `issues` (fan tasks.md to GitHub issues). Keep the dispatcher thin; heavy logic stays in the retained skills. Zero new outbound calls/deps/credentials (workflows are an Anthropic-runtime feature; this is skill-native guidance + command behavior).

#### 3.3 -- /implement

- [ ] T012 [P] Create catalog/commands/implement.md (rename implement-phase)

**Objective**: Rename `implement-phase` to `/implement`.

**Prompt**:
> Create `catalog/commands/implement.md` delegating to the `implement-phase` skill. Accept a positional plan slug and optional `phase-N` (or `next`). Preserve the full per-phase workflow (plan discovery, pre-implementation review, code, lint, test, troubleshoot, post-phase docs + commit) AND the final-phase auto release-readiness workflow -- but route the release step to `/update release` (Phase 4) instead of the old inline update-* sequence. Keep under 150 lines.

#### 3.4 -- /test

- [ ] T013 Create catalog/commands/test.md (merge generate-tests + generate-unit-tests + tdd; iterative coverage loop)

**Objective**: One testing command that drives coverage to a standardized threshold across tiers.

**Prompt**:
> Create `catalog/commands/test.md` delegating to `generate-tests` + `generate-unit-tests` + `tdd`. Default behavior: analyze current unit-test coverage, then generate and run unit tests iteratively until coverage reaches the standardized threshold (default 80% line per the repo's global testing rules) AND the generated-test pass-rate is 100% green, then proceed the same way to integration, then e2e, then CI/CD. Scopes: `unit`, `integration`, `e2e`, `ci`, `tdd` (red-green-refactor), `all` (the full tier sequence). For very large surfaces, offer (with confirmation) the fan-out path described in `[[agent-orchestration-primitives]]`, carrying the scope-first token warning. Make the threshold/pass-rate overridable via args.

#### 3.X -- Testing and Stabilization

- [ ] T014 Run and stabilize Phase 3 tests

**Objective**: Verify the four dispatchers resolve and delegate. Iterate until stable.

**Prompt**:
> Manually exercise each new command's scope resolution (bare -> menu; arg -> direct) against its delegate skill; confirm `make validate` stays green and no skill body was broken. Fix all issues. After green, run `/session history` to document Phase 3.

### Phase 3 Exit Checklist

- [ ] All sub-tasks completed
- [ ] /describe, /plan, /implement, /test ship and delegate correctly
- [ ] Old commands still function (shims pending Phase 8)
- [ ] Ready to advance to Phase 4

---

## Phase 4: Review + Update commands (the two largest merges)

**Goal**: Ship `/review` and `/update`, the two commands that absorb the most old commands.
**Prerequisites**: Phase 1 (template), Phase 2 (skill-security-scan skill for the `skill-scan` scope), Phase 3 (so the lifecycle is coherent).
**Stability Gate**: `/review full` orchestrates every lens; `/update release` runs the full update+commit+tag+push sequence using the version-sync guard; both resolve focused scopes; `make validate` green.

### Sub-tasks

#### 4.1 -- /review

- [ ] T015 Create catalog/commands/review.md (merge review-codebase, review-changes, run-deep-review, run-security-audit, run-penetration-test, generate-sbom, skill-scan)

**Objective**: One comprehensive, scope-able review command.

**Prompt**:
> Create `catalog/commands/review.md` delegating to `review-codebase`, `review-changes`, `run-deep-review`, `run-security-audit`, `run-penetration-test`, `generate-sbom`, and the new `skill-security-scan` skill (Phase 2/6). Bare invocation asks the scope; scopes: `full` (orchestrates structure -> quality -> coverage -> security -> changes, then synthesizes, equivalent to today's run-deep-review), `structure`, `quality`, `coverage`, `security` (run-security-audit), `pentest` (run-penetration-test), `changes` (multi-agent persona diff review), `skill-scan` (run nexus-skill-scanner over a target/the catalog), `sbom`, `deps`. For large read-only audits offer the Dynamic-Workflows fan-out path (the "audit every endpoint for missing auth" pattern) with confirmation + token warning. Keep the dispatcher thin.

#### 4.2 -- /update

- [ ] T016 Create catalog/commands/update.md (merge update-*, refactor-*, changelog, devlog, readme, commit-msg, config; release scope)

**Objective**: One command to sync the repo to current state and ship a release.

**Prompt**:
> Create `catalog/commands/update.md` delegating to `update-documentation`, `update-devlog`, `generate-devlog`, `generate-readme`, `update-gitignore`, `update-version`, `generate-changelog`, `generate-commit-message`, `refactor-docs`, `refactor-project`, and the built-in `update-config` skill. Scopes: `docs` (incl. readme), `devlog`, `gitignore`, `version` (MUST use `scripts/check_version_sync.py` so every version surface -- plugin.json, both installers, marketplace.json, README/AGENTS.md prose, CHANGELOG -- is bumped as one atomic set, closing the v2.4.0 drift class), `changelog`, `refactor`, `config`, `commit`, and `release` (= run docs + devlog + gitignore + version + changelog + refactor, then clean up, commit, tag, and push -- the "final phase of a plan" flow). Bare invocation asks the scope. This is the command `/implement` hands off to on a plan's final phase. The `config` scope MUST also validate installed platform configs and repair drift: in particular, a Codex `~/.codex/config.toml` that defines `[permissions.*]` profiles MUST set `default_permissions` (the v3.0.0 installer hotfix fixed the fresh-install copy path and the existing-config append paths in `installer.sh` / `installer.ps1` / `Install-Nexus-Hub-Permissions.ps1`; repairing an *already-broken* user config -- `[permissions.*]` present but `default_permissions` missing -- requires TOML-aware insertion of `default_permissions` before the first `[permissions...]` table, and the idempotency guard must not skip such a config). Reuse the `config-consistency-checker` skill / `nexus-hub doctor` for the validation. Optionally surface a Windows `[windows] sandbox = "unelevated"` recommendation when Codex's elevated-sandbox setup fails.

#### 4.X -- Testing and Stabilization

- [ ] T017 Run and stabilize Phase 4 tests

**Objective**: Verify both merge-commands. Iterate until stable.

**Prompt**:
> Exercise `/review` across scopes and confirm `/update version` invokes the version-sync guard. Dry-run `/update release` (without the final push) to confirm the sequence wiring. Keep `make validate` green. Fix all issues. After green, run `/session history` to document Phase 4.

### Phase 4 Exit Checklist

- [ ] All sub-tasks completed
- [ ] /review and /update ship; full/release scopes orchestrate correctly
- [ ] /update version uses the drift guard
- [ ] Ready to advance to Phase 5

---

## Phase 5: Remaining commands + permanent aliases

**Goal**: Ship the remaining eight commands and the two permanent convenience aliases.
**Prerequisites**: Phase 1 (template).
**Stability Gate**: All 14 commands exist and delegate; `/constitution` and `/commit` permanent aliases work; `make validate` green.

### Sub-tasks

#### 5.1 -- /compare and /research

- [ ] T018 [P] Create catalog/commands/compare.md (rename compare-project)

**Objective**: Rename `compare-project` to `/compare`.

**Prompt**:
> Create `catalog/commands/compare.md` delegating to the `compare-project` skill, preserving the full repo/article/local detection, the mandatory Security + RE assessment sections, and the chain into `/plan from-comparison`. Auto-infer scope from the source type. Keep under 150 lines.

- [ ] T019 [P] Create catalog/commands/research.md (merge compile-deep-research + deep-research + generate-report)

**Objective**: One research/report command.

**Prompt**:
> Create `catalog/commands/research.md` delegating to `deep-research`, `compile-deep-research`, and `generate-report`. Scopes: `deep` (fan-out web research with adversarial verification), `compile` (merge multiple reports into one cited document), `report` (export markdown to docx/pptx via the template-aware generator). Bare invocation asks the scope.

#### 5.2 -- /skills and /spec

- [ ] T020 [P] Create catalog/commands/skills.md (merge search-skills, commands-cheatsheet, create-skill-or-command, import-skills + scan)

**Objective**: One catalog command incl. the new pre-install scan.

**Prompt**:
> Create `catalog/commands/skills.md` delegating to `search-skills`, `commands-cheatsheet`, `create-skill-or-command`, `import-skills`, and the new `skill-security-scan` skill / `nexus-skill-scanner` (Phase 6). Scopes: `search`, `list` (unified skills + commands cheatsheet), `create`, `import`, `scan` (security-scan a skill before install). Bare invocation asks the scope.

- [ ] T021 [P] Create catalog/commands/spec.md (merge clarify-spec, analyze-spec, constitution)

**Objective**: One spec/governance command.

**Prompt**:
> Create `catalog/commands/spec.md` delegating to `clarify-spec`, `analyze-spec`, and `constitution`. Scopes: `clarify` (sequential clarification loop), `analyze` (cross-artifact consistency/coverage), `constitution` (author/amend the project constitution). Bare invocation asks the scope.

#### 5.3 -- /session, /setup, /memory, /usage

- [ ] T022 [P] Create catalog/commands/session.md (merge continue-session, wrap-up-session, generate-session-history)

**Objective**: One session command.

**Prompt**:
> Create `catalog/commands/session.md` delegating to `continue-session`, `wrap-up-session`, `generate-session-history`. Scopes: `continue`, `wrap-up`, `history`. Bare invocation asks the scope.

- [ ] T023 [P] Create catalog/commands/setup.md (merge setup-project + install-pre-commit-review-hook) and /memory + /usage

**Objective**: One setup command plus the two thin meta renames.

**Prompt**:
> Create `catalog/commands/setup.md` delegating to `setup-project` (scope `project`, default) and `install-pre-commit-review-hook` (scope `hooks`). Also create thin `catalog/commands/memory.md` (delegates to `manage-memory`) and `catalog/commands/usage.md` (delegates to `check-usage`). All under 150 lines each.

#### 5.4 -- Permanent aliases

- [ ] T024 Create permanent aliases catalog/commands/constitution.md -> /spec constitution and catalog/commands/commit.md -> /update commit

**Objective**: Keep two heavily-used names as permanent (non-deprecated) convenience aliases.

**Prompt**:
> Create `catalog/commands/constitution.md` as a permanent thin alias forwarding to `/spec constitution` (it is cross-referenced by `generate-plan`/`/plan`, `project-constitution`, `analyze-spec`). Create `catalog/commands/commit.md` as a permanent thin alias forwarding to `/update commit` for high-frequency mid-dev use; note the external commit-commands `/commit` may also be present. These two are NOT deprecation shims -- they are permanent aliases.

#### 5.X -- Testing and Stabilization

- [ ] T025 Run and stabilize Phase 5 tests

**Objective**: Verify all 14 commands + 2 permanent aliases resolve and delegate. Iterate until stable.

**Prompt**:
> Confirm all 14 commands and the 2 permanent aliases exist, resolve scope, and delegate; `make validate` green. Fix all issues. After green, run `/session history` to document Phase 5.

### Phase 5 Exit Checklist

- [ ] All sub-tasks completed
- [ ] All 14 commands + /constitution + /commit aliases ship
- [ ] Ready to advance to Phase 6

---

## Phase 6: nexus-skill-scanner engine (re-full)

**Goal**: Build the local internal static skill-security scanner and gate the catalog on it.
**Prerequisites**: Phase 2 (skill-security-scan skill).
**Stability Gate**: The scanner scores a planted-malicious fixture HIGH and a clean fixture LOW; the CI catalog gate is green on the current catalog; the subsumed validators' existing tests still pass.

### Sub-tasks

#### 6.1 -- Scaffold the package

- [ ] T026 Scaffold extensions/nexus-skill-scanner/ (package layout, pyproject, tests skeleton)

**Objective**: Create the internal scanner package following Nexus-Hub's extensions idiom.

**Prompt**:
> Scaffold `extensions/nexus-skill-scanner/` as a plain-Python package (no LangGraph -- rejected per comparison N1): package dir, `pyproject.toml`, a `__main__`/CLI entry, an empty analyzers module, and a `tests/` skeleton. Use generic naming with no reference to any external project (Reverse-Engineering Attribution Rule). Editable-installable so both installers resolve it via `pip install`.

#### 6.2 -- Static analyzers

- [ ] T027 Implement static analyzers for detection classes 1-13, 15-16 in extensions/nexus-skill-scanner/

**Objective**: Regex + AST + taint + MCP-check coverage.

**Prompt**:
> Implement analyzers for prompt injection, data exfiltration, privilege escalation, supply-chain (static portion), excessive agency, output handling, system-prompt leakage, memory poisoning, tool misuse, rogue agent, trigger abuse (the malicious inverse of pushy descriptions: overly broad triggers / shadow commands / keyword baiting), behavioral AST (exec/eval/dynamic import/subprocess/getattr), taint tracking (input-to-execution, file-to-network, credential chains), MCP least-privilege (under/over-declaration, wildcards), and MCP tool poisoning (hidden instructions, parameter injection, description-vs-behavior mismatch). All patterns re-authored from public security knowledge. The scanner MUST be Markdown-fence-aware (preserve the v2.4.0 secret-scanner nuance) to avoid false positives on documentation examples. Start with the highest-signal classes and record any deferred classes in `docs/v3/v3.0/known-gaps.md`.

#### 6.3 -- Scoring + output + framework tagging

- [ ] T028 Implement risk scoring, severity bands, SARIF/JSON/Markdown emitters, and framework-ID tagging

**Objective**: Unified risk score + CI-consumable output.

**Prompt**:
> Implement severity-point scoring (CRIT +50 / HIGH +25 / MED +10 / LOW +5; executable-script 1.3x multiplier) with bands (0-20 LOW, 21-50 MED, 51-80 HIGH, 81-100 CRITICAL) and `terminal`/`json`/`markdown`/`sarif` emitters. Tag each finding with its MITRE ATT&CK / D3FEND / NIST CSF control IDs (Nexus-Hub strength from `references/detection-classes.md`). `--no-llm` runs the deterministic gate only; the semantic pass is the `skill-security-scan` skill, not bundled code.

#### 6.4 -- Entry point + installer registration + make target

- [ ] T029 Add scripts/scan_skill_security.py entry, register in both installers, add make scan target

**Objective**: Expose and distribute the scanner.

**Prompt**:
> Add `scripts/scan_skill_security.py` as the thin CLI entry (`scan <target> --format ... --no-llm --osv`). Register it as an explicit-name copy step in BOTH `scripts/installer.sh` AND `scripts/installer.ps1` (`~/.nexus-hub/scripts/`). Add a `make scan` target. Lazy-import optional deps (YARA) with a clear `pip install` hint on failure.

#### 6.5 -- Subsume existing validators

- [ ] T030 Subsume validate_skills secret scan, scan_supply_chain_iocs, validate_workflow_security behind the unified scanner (behavior-preserving)

**Objective**: Unify the fragmented security surface rather than multiply it.

**Prompt**:
> Route `validate_skills.py` secret scanning, `scan_supply_chain_iocs.py`, and `validate_workflow_security.py` through `nexus-skill-scanner` as analyzer modules (or have the scanner call them), keeping their existing `make validate` entry points and ALL their existing tests green (treat as a behavior-preserving refactor with a before/after check). Do not regress the fenced-code-aware secret nuance.

#### 6.6 -- Fixtures + CI catalog gate

- [ ] T031 Add malicious/clean pytest fixtures and the CI catalog gate over catalog/skills + catalog/mcp-configs

**Objective**: Prove the scanner works and dogfood the catalog.

**Prompt**:
> Add `tests/validators/test_scan_skill_security.py` with a planted-malicious fixture skill (prompt-injection text + an exec call) that MUST score HIGH and a clean fixture that MUST score LOW. Add a CI step that runs the scanner over `catalog/skills/` and `catalog/mcp-configs/` and fails on any HIGH/CRITICAL finding; the semantic-adjudication skill is the false-positive filter before the gate fails. Confirm the current catalog passes.

#### 6.X -- Testing and Stabilization

- [ ] T032 Run and stabilize Phase 6 tests

**Objective**: Full scanner verification. Iterate until stable.

**Prompt**:
> Run the scanner test suite, the subsumed validators' suites, and the CI catalog gate locally. Confirm malicious->HIGH, clean->LOW, catalog->pass, and zero regressions in subsumed validators. Fix all failures. After green, run `/session history` to document Phase 6.

### Phase 6 Exit Checklist

- [ ] All sub-tasks completed
- [ ] Scanner scores fixtures correctly; catalog gate green; validators subsumed without regression
- [ ] scan_skill_security.py registered in both installers + make scan
- [ ] Ready to advance to Phase 7

---

## Phase 7: scanner optional modules (re-partial)

**Goal**: Add the two optional, default-off modules (YARA signatures, OSV.dev lookup).
**Prerequisites**: Phase 6.
**Stability Gate**: Both modules degrade gracefully when their dependency/network is absent; default behavior (modules off) is unchanged; no new default outbound call.

### Sub-tasks

#### 7.1 -- Optional YARA module

- [ ] T033 [P] Add optional YARA signature module + re-authored rules to extensions/nexus-skill-scanner/

**Objective**: Detection class 14 as an optional local engine.

**Prompt**:
> Add an optional YARA module (class 14: malware / webshell / cryptominer / exploit) with a small re-authored rule set (no copied signatures). YARA is a lazy optional dependency: when absent, the scanner runs all other classes and reports the YARA module as skipped with an install hint (graceful degrade, verified by a test that simulates YARA absent).

#### 7.2 -- Optional offline-first OSV.dev lookup

- [ ] T034 [P] Add optional offline-first OSV.dev dependency lookup (default off, --osv opt-in, static fallback)

**Objective**: The live portion of class 4, kept off the default path.

**Prompt**:
> Add an optional dependency-CVE lookup using stdlib `urllib` against OSV.dev, sending ONLY `{ecosystem, package, version}` tuples. Default OFF; enabled only via `--osv`. Ship a static offline fallback list so the scanner works air-gapped. Document in the comparison report's terms (the only network surface in v3.0.0; not search-as-service; opt-in). Test both the offline-fallback path and a mocked OSV response (no real network call in CI).

#### 7.X -- Testing and Stabilization

- [ ] T035 Run and stabilize Phase 7 tests

**Objective**: Verify graceful degradation and default-off behavior. Iterate until stable.

**Prompt**:
> Run tests with YARA present/absent and `--osv` on (mocked) / off. Confirm default behavior makes no outbound call and both modules degrade gracefully. Fix all failures. After green, run `/session history` to document Phase 7.

### Phase 7 Exit Checklist

- [ ] All sub-tasks completed
- [ ] YARA + OSV modules optional, default-off, graceful-degrade
- [ ] No new default outbound call
- [ ] Ready to advance to Phase 8

---

## Phase 8: Deprecation shims + migration + count reconciliation

**Goal**: Keep every old command working, document the migration, and reconcile counts/templates.
**Prerequisites**: Phases 3-5 (the 14 new commands exist).
**Stability Gate**: Every old command name forwards to its new command + scope with a deprecation notice; count prose and 5 platform templates reconciled; `make validate` green.

### Sub-tasks

#### 8.1 -- Deprecation shims

- [ ] T036 Convert the 41 old command files in catalog/commands/ into deprecation shims forwarding to the new command + scope

**Objective**: Soften the breaking rename for v3.x.

**Prompt**:
> Convert each of the 41 old command files (except `constitution.md` and any kept permanent) into a 3-5 line deprecation shim: print "/<old> is deprecated and will be removed in v4.0.0. Forwarding to /<new> <scope>." then delegate identically, per the 41->14 mapping in `docs/v3/v3.0/command-consolidation-design.md` Section 3. Do not delete the files (removal is a v4.0.0 known-gap).

#### 8.2 -- Migration doc + CHANGELOG table

- [ ] T037 [P] Write docs/v3/v3.0/command-migration.md and add the old->new rename table to CHANGELOG.md

**Objective**: User-facing migration guidance.

**Prompt**:
> Write `docs/v3/v3.0/command-migration.md` with the full old->new->scope table and the deprecation timeline (shims through v3.x, removed v4.0.0). Add the same rename table to the `## [Unreleased]` / v3.0.0 section of `CHANGELOG.md`. ASCII-only Markdown per the style guide.

#### 8.3 -- Count + template reconciliation

- [ ] T038 Update marketplace.json total_commands + AGENTS.md/README count prose + the 5 platform instruction templates

**Objective**: Prevent a WN-v24-1-class count drift.

**Prompt**:
> Update `data/marketplace.json` `total_commands` (14 active + permanent aliases; document the deprecated-shim count), the `AGENTS.md` "Current catalog" line and structure-tree comments, and `README.md` command-count prose. Update any of the 5 `templates/ai-instructions/base-*.md` files that enumerate commands, in lockstep (platform-agnostic). Run `scripts/check_version_sync.py` and `make validate`.

#### 8.X -- Testing and Stabilization

- [ ] T039 Run and stabilize Phase 8 tests

**Objective**: Verify shims and counts. Iterate until stable.

**Prompt**:
> Spot-check several deprecation shims forward correctly; confirm `make validate` and `check_version_sync` are green and counts agree everywhere. Fix all issues. After green, run `/session history` to document Phase 8.

### Phase 8 Exit Checklist

- [ ] All sub-tasks completed
- [ ] 41 old names forward via shims; migration doc + CHANGELOG table written
- [ ] Counts + 5 templates reconciled
- [ ] Ready to advance to Phase 9

---

## Phase 9: Ingested known-gaps (carried forward from v2.4.0)

**Goal**: Resolve the actionable v2.4.0 known-gaps pulled into this plan.
**Prerequisites**: None hard; Phase 6 helpful for context on extractors.
**Stability Gate**: DF-v24-7 batch clears the 80% recall gate; WN-v24-2 duplicate headings merged; NI-v24-1 decision recorded.

### Sub-tasks

#### 9.1 -- Code-search extractors

- [ ] T040 [from v2.4.0 known-gaps: DF-v24-7] Add Swift + Kotlin code-search extractors under extensions/nexus-code-search

**Objective**: Continue the language-coverage expansion (10 -> 12).

**Prompt**:
> Following the per-language extractor pattern under `extensions/nexus-code-search/.../extraction/languages/`, add Swift and Kotlin extractors, each with an eval fixture clearing the 80% recall gate and unit tests, and the matching tree-sitter grammar dep under the shared `<0.26` ceiling. Register in `LANGUAGE_EXTRACTORS`. Reason from DF-v24-7: ~10 languages remained uncovered after v2.4.0; mobile coverage (Swift/Kotlin) is the recommended next batch. Record remaining languages + framework/parameter parity as a fresh known-gap.

#### 9.2 -- Heading cleanup

- [ ] T041 [P] [from v2.4.0 known-gaps: WN-v24-2] Merge duplicate ## Quality Checklist / ## Verification headings in affected skills

**Objective**: Cosmetic consistency across grandfathered skills.

**Prompt**:
> For skills carrying BOTH `## Quality Checklist` and `## Verification`, merge into the single canonical `## Verification` binary checklist (or repurpose `## Quality Checklist` to a clearly distinct heading). Reason from WN-v24-2: the v2.4.0 quality sweep left a subset with both headings. Keep `make validate --quality` at 0 warnings.

#### 9.3 -- Close NI-v24-1

- [ ] T042 [from v2.4.0 known-gaps: NI-v24-1] Confirm and record the validate_solution_frontmatter.ps1 decision

**Objective**: Close the deliberate no-action item.

**Prompt**:
> Confirm the convention-based decision to keep `validate_solution_frontmatter.py` as a single cross-platform `.py` validator (no `.ps1` sibling), consistent with the four other top-level `.py`-only validators and now `check_version_sync.py`. Record as resolved (won't-do, by convention) in `docs/v3/v3.0/known-gaps.md`.

#### 9.X -- Testing and Stabilization

- [ ] T043 Run and stabilize Phase 9 tests

**Objective**: Verify extractors + catalog quality. Iterate until stable.

**Prompt**:
> Run the code-search eval suite (Swift/Kotlin clear 80% recall), `make validate --quality` (0 warnings), and the full `make validate`. Fix all failures. After green, run `/session history` to document Phase 9.

### Phase 9 Exit Checklist

- [ ] All sub-tasks completed
- [ ] Swift + Kotlin extractors pass; duplicate headings merged; NI-v24-1 closed
- [ ] Ready to advance to Phase 10

---

## Phase 10: Live verification + release readiness

**Goal**: Run the full green gate, dogfood the scanner, handle env-gated re-deferrals, and ship v3.0.0.
**Prerequisites**: All prior phases.
**Stability Gate**: `make validate`/`lint`/`test` green; `check_version_sync` green at 3.0.0; catalog `/review skill-scan` clean; env-gated items either run-green or re-deferred with dated reasons; v3.0.0 tagged.

### Sub-tasks

#### 10.1 -- Full green gate + catalog dogfood

- [ ] T044 Run make validate/lint/test + dogfood /review full and /review skill-scan over the catalog

**Objective**: Prove the whole release is green and the scanner is clean on Nexus-Hub itself.

**Prompt**:
> Run `make validate`, `make lint`, `make test`, and `scripts/check_version_sync.py`. Run `/review skill-scan` (nexus-skill-scanner) over `catalog/skills/` + `catalog/mcp-configs/` and confirm no HIGH/CRITICAL after semantic adjudication. Record results in `docs/v3/v3.0/review/`.

#### 10.2 -- Env-gated live evals

- [ ] T045 [from v2.4.0 known-gaps: DF-v24-8, DF-v24-9] Run live skill-eval-loop + eval-harness if a model CLI is available, else re-defer with a dated reason

**Objective**: Discharge or re-defer the model-CLI-gated evals.

**Prompt**:
> If a model CLI (`claude`/`codex`/`gemini`/`opencode`) is on PATH, run the live `skill-eval-loop` (1.0 positive / 0.0 fenced-negative) for the v3.0.0 new skills (`agent-orchestration-primitives`, `skill-security-scan`) plus the carried-forward v2.4.0 skills listed in DF-v24-8, and the three eval-harness trigger techniques (DF-v24-9). Otherwise, re-defer both with a dated reason in `docs/v3/v3.0/known-gaps.md` (the established source-release pattern; static trigger-surface checks already done).

#### 10.3 -- Env-gated cross-OS + Antigravity

- [ ] T046 [from v2.4.0 known-gaps: DF-v24-10, WN-v24-3] Run cross-OS installer smoke + live --branch + Antigravity agy probe if hosts/binaries available, else re-defer

**Objective**: Discharge or re-defer the host/binary-gated verifications.

**Prompt**:
> If a macOS/Linux host is available, run the installer smoke + live `--branch` clone+install (DF-v24-10); if the `agy` binary is installable, run the Antigravity CLI live probe and reconcile the four residuals (WN-v24-3). Otherwise re-defer with dated reasons in `docs/v3/v3.0/known-gaps.md`. Windows remains empirically green; the Linux Python suite is green via CI.

#### 10.4 -- Re-evaluate the carried-forward DF-v23-9 deferral

- [ ] T047 [from v2.3.0 known-gaps: DF-v23-9] Re-evaluate the visual-brainstorming-server deferral; build only if a user-facing need emerged, else re-defer into docs/v3/v3.0/known-gaps.md

**Objective**: Discharge or re-defer the one still-open previous-version (v2.3.0) known-gap.

**Prompt**:
> Re-evaluate DF-v23-9 (a Superpowers-style visual brainstorming server; an intentional `re-full`, local-only deferral from v2.3.0 -- binds 127.0.0.1, zero outbound, no new credential, so it would pass the MCP Registry Policy). If a concrete user-facing need for in-session visual collaboration has emerged, scope it as an `extensions/` internal MCP under the reverse-engineer-first policy and add a `docs/policy/mcp-reverse-engineering-matrix.md` row before building. Otherwise, re-defer it into `docs/v3/v3.0/known-gaps.md` with a dated reason and preserve its revisit trigger. Do not build pre-emptively (catalog-content-first identity grounds).

#### 10.5 -- Release

- [ ] T048 Run /update release to bump to v3.0.0 across all surfaces, write CHANGELOG, commit, and tag

**Objective**: Ship v3.0.0.

**Prompt**:
> Run `/update release`: bump the version to 3.0.0 across ALL surfaces via `scripts/check_version_sync.py` (plugin.json, both installers, marketplace.json, README/AGENTS.md prose), finalize the v3.0.0 `CHANGELOG.md` section (incl. the command rename table and the breaking-change notice), update `docs/v3/v3.0/known-gaps.md` status to finalized, commit, and tag `v3.0.0`. Confirm `check_version_sync` and the installer-smoke version-constant tests are green at 3.0.0 before tagging. Do not push the tag without explicit user confirmation.

#### 10.X -- Testing and Stabilization

- [ ] T049 Final release gate

**Objective**: Last full verification before release. Iterate until stable.

**Prompt**:
> Re-run the entire gate (`make validate`/`lint`/`test`, `check_version_sync`, installer smoke, catalog scan). Confirm all green at 3.0.0 and known-gaps finalized. Fix any failure. After green, run `/session history` to document Phase 10 and the release.

### Phase 10 Exit Checklist

- [ ] All sub-tasks completed
- [ ] Full gate green at v3.0.0; catalog scan clean
- [ ] Env-gated items + DF-v23-9 run-green or re-deferred with dated reasons
- [ ] v3.0.0 tagged (push pending user confirmation)

---

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

No constitution file exists, so there are no MUST-principle violations to justify. The one network-touching item (optional OSV.dev lookup, Phase 7) is justified inline in [`docs/releases/v3/v3.0/comparisons/v3.0.0-comparison-skillspector.md`](../comparison-skillspector.md) Section 13 N3: it is default-off, opt-in, sends only package-coordinate tuples, ships an offline fallback, and is therefore not the prohibited "search-as-service" under the MCP Registry Policy.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | -- | -- |

---

## Out of Scope (explicitly NOT adopted -- security / policy)

- **N1 -- LangGraph orchestration engine** (SkillSpector). Adopt the two-stage concept in plain Python; a DAG framework is unnecessary weight. (MCP Registry Policy: prefer minimal-dependency local build.)
- **N2 -- Bundled LLM-provider client + API key** (SkillSpector Stage 2). The semantic pass is a `skill-native` skill run by the user's own agent; no new credential or processor. (Policy tier 2.)
- **N3 -- Mandatory live OSV.dev lookups.** Adopted only as an optional, offline-first, opt-in module (Phase 7), never default-on. (Policy: borderline tier 3/4; permitted only because OSV.dev is a free public vuln DB queried by package coordinate, opt-in, with an offline fallback.)
- **Dynamic Workflows as a required dependency** (orchestration PDFs). Adopted as guidance + an optional offered fan-out path only; never assumed present (it is a plan-gated research-preview feature).
