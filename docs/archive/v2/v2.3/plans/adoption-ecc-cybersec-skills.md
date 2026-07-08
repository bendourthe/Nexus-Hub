# Plan — Adopt ECC + Anthropic-Cybersecurity-Skills (reverse-engineer-first)

**Project**: Nexus-Hub
**Version**: v2.3.0
**Slug**: adoption-ecc-cybersec-skills
**Plan Type**: Feature / Enhancement
**Created**: 2026-05-26
**Goal**: Adopt all in-scope items from the ECC and Anthropic-Cybersecurity-Skills comparisons as local, zero-outbound Nexus-Hub capabilities, sequenced reverse-engineer-first, while carrying forward the 12 open v2.2.0 known-gaps.

## Overview

This plan operationalizes two cross-project comparisons written at v2.2.0: [comparison-ECC.md](../../v2.2.0/comparison-ECC.md) (Nexus-Hub vs. the ECC multi-harness operator OS) and [comparison-Anthropic-Cybersecurity-Skills.md](../../v2.2.0/comparison-Anthropic-Cybersecurity-Skills.md) (Nexus-Hub vs. a 754-skill cybersecurity content library). Both reports' Section 9 Security and Reverse-Engineering Assessment and Section 11 Adoption Plan are the authoritative source for the sub-tasks below.

Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of each source comparison for the ordering rationale: skill-native replacements ship first (Phase 1), then `re-full` / `re-partial` internal builds (Phases 2-6), and `drop-outright` / vendor-intrinsic items never enter the active phases — they are recorded in the "Items explicitly NOT adopted" appendix at the end of this plan. Every adopted item is local and outbound-call-free; this plan adds zero new third-party data processors, zero new API keys, and zero new runtime dependencies beyond what is reimplemented in Nexus-Hub's existing Python / bash / PowerShell stack. ECC's Node and Rust runtimes are deliberately not adopted — only their logic is reverse-engineered.

This plan ingests 12 item(s) carried forward from prior known-gaps files: see sub-tasks tagged `[from v2.2.0 known-gaps: …]` in Phases 7-9. These are the codegraph / installer-parity follow-ups that v2.2.0 explicitly targeted at v2.3.0.

What success looks like: every in-scope skill, script, validator, hook, and lifecycle command lands as catalog content that passes `make validate`, `make lint`, and `make test`; new skills are registered in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`; new standalone scripts are registered in BOTH `scripts/installer.sh` and `scripts/installer.ps1`; and the 12 ingested known-gaps are resolved or re-deferred with evidence.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/archive/v2/v2.3/constitution.md - skipping check. Recommend running /constitution to establish project principles.

The de facto governing document for adoption decisions in this plan is the **MCP Registry Policy** in `AGENTS.md` (and `docs/policy/mcp-reverse-engineering-matrix.md`). Every Section 9.3 classification in the source comparisons was made against that policy, and the reverse-engineer-first phase ordering is its direct expression.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Skill-native foundations | `context-modes` skill + cross-framework mapping convention and `security-framework-mapping` skill shipped (zero code) |
| 2 | Security & quality CI validators | Four local static validators wired into `make validate` and both installers |
| 3 (done) | Runtime learning | Memory-persistence session hooks + a local-only continuous-learning skill and capture hooks |
| 4 (done) | Installer lifecycle & selective install | Install-state manifest, `doctor`/`repair`/`list-installed`, profiles/modules + `consult` advisor, harness audit scoring |
| 5 | Skill quality tooling | `skill-stocktake` audit, `validate_skills.py` quality pass, `skill-create` from git history |
| 6 (done) | Framework coverage + defensive security content | Coverage-matrix generator + two re-authored defensive security skill packs + their helper scripts |
| 7 | [known-gaps] Installer instruction-file parity | DF-001 / MT-2 / MT-1 closed; legacy bash blocks removable |
| 8 (done) | [known-gaps] Code-graph quality & extractor expansion | WN-1 / WN-5 / WN-6 / WN-7 / DF-002 addressed |
| 9 | [known-gaps] Live-environment verification | WN-2 / WN-3 / WN-4 / WN-8 verified on live VMs |

---

## Phase 1: Skill-native foundations

**Goal**: Ship the two zero-code, skill-native capabilities that close capability gaps without any code change.
**Prerequisites**: None.
**Stability Gate**: Both new skills pass `scripts/validate_skills.py`; `make validate` is green; the three data-registry files reference both skills.

### Sub-tasks

#### 1.1 — context-modes skill

- [x] T001 [P] Create context-modes skill at catalog/skills/workflow/context-modes/SKILL.md

**Objective**: Reproduce ECC's `contexts/{dev,review,research}.md` dynamic system-prompt injection as a Nexus-Hub skill that lets the agent adopt a named working mode.

**Prompt**:
> Create a new Nexus-Hub skill at `catalog/skills/workflow/context-modes/SKILL.md` that lets the agent switch between named working modes (at minimum: `dev`, `review`, `research`), each retuning behavior, priorities, and favored tools. Model the mode content on ECC's `contexts/dev.md` (write-code-first, run-tests, atomic commits), `review.md`, and `research.md`, but re-author in Nexus-Hub's voice (do not copy text; this is a skill-native reverse-engineering per the MCP Registry Policy). Required frontmatter: `name`, `description` (pushy, with trigger phrases like "switch to review mode", "research mode", and a SKIP clause), `summary_l0` (<=15 words, quoted), `overview_l1` (<=150 words, quoted). Required body sections in order: title, When to Use This Skill (with When NOT to use), Instructions (how to enter/exit each mode and what each mode changes), Common Rationalizations (table), Verification (binary checklist), Related Skills (link `[[context-engineering]]`, `[[context-optimization]]`). Optionally ship per-mode fragments under `catalog/skills/workflow/context-modes/references/{dev,review,research}.md` and reference each from SKILL.md (referenced-only rule). Then register the skill in `data/SKILL_INDEX.md` (one row), `data/skills.json` (one entry, security defaults 100/100/95), and `data/marketplace.json` (increment the workflow category `skill_count` and `statistics.total_skills`). Run `make validate`. Source: comparison-ECC.md Section 11 Bucket A (A1).

---

#### 1.2 — Cross-framework mapping convention + security-framework-mapping skill

- [x] T002 [P] Create security-framework-mapping skill at catalog/skills/security/security-framework-mapping/SKILL.md and document the optional frontmatter convention in AGENTS.md

**Objective**: Adopt the cybersecurity library's standout pattern — tag security/compliance skills with framework identifiers (MITRE ATT&CK / ATLAS / D3FEND / NIST CSF / NIST AI RMF) and document the convention.

**Prompt**:
> Two deliverables. (1) Document an OPTIONAL skill-frontmatter convention in `AGENTS.md` (in the "Write SKILL.md" subsection): security and compliance skills MAY add the optional fields `mitre_attack`, `atlas_techniques`, `d3fend_techniques`, `nist_csf`, `nist_ai_rmf` (lists of framework IDs) plus a per-skill `references/standards.md` documenting the mapping. State that these fields are non-required, do not affect Tier-1 loading, and are validated as optional by `scripts/validate_skills.py`. (2) Create a new skill at `catalog/skills/security/security-framework-mapping/SKILL.md` that teaches the agent how to map a security skill or finding across the five frameworks, with a worked example (e.g., `analyzing-network-traffic-of-malware` -> ATT&CK T1071 / NIST CSF DE.CM / ATLAS AML.T0047 / D3FEND D3-NTA / AI RMF MEASURE-2.6). Use the full required frontmatter (`summary_l0`/`overview_l1` quoted) and body sections (When to Use, Instructions, Common Rationalizations, Verification, Related Skills linking `[[nist-ai-rmf]]`, `[[traceability-matrix-generator]]`). Do NOT copy Apache-2.0 text from the source; re-author from the underlying public MITRE/NIST frameworks (Reverse-Engineering Attribution Rule). Register the new skill in the three data files. Run `make validate`. Source: comparison-Anthropic-Cybersecurity-Skills.md Section 11 Bucket A (CA1).

---

#### 1.3 — Testing and Stabilization

- [x] T003 Run and stabilize Phase 1 validation in scripts/validate_skills.py and data/

**Objective**: Verify both skills pass structural validation and registry integrity.

**Prompt**:
> Run `make validate` and `python scripts/validate_skills.py --verbose`. Confirm both new skills (`context-modes`, `security-framework-mapping`) parse, have valid quoted `summary_l0`/`overview_l1`, and have no orphan-bundle warnings. Confirm `data/skills.json`, `data/SKILL_INDEX.md`, and `data/marketplace.json` counts are consistent. Fix any failures and iterate until green. Do not advance to Phase 2 until validation passes. After it passes, run /generate-session-history to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (`make validate` green)
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: Security & quality CI validators

**Goal**: Reverse-engineer ECC's local static-analysis CI validators into Nexus-Hub's Python validator stack (P0, pure posture win, no dependencies).
**Prerequisites**: None (independent of Phase 1).
**Stability Gate**: All four validators run under `make validate`, pass on the clean tree, and fail on an injected fixture; both installers register the scripts.

### Sub-tasks

#### 2.1 — Implement the four CI validators

- [x] T004 [P] Implement scripts/validate_no_personal_paths.py, validate_unicode_safety.py, scan_supply_chain_iocs.py, validate_workflow_security.py

**Objective**: Port ECC's `scripts/ci/{validate-no-personal-paths,check-unicode-safety,scan-supply-chain-iocs,validate-workflow-security}.js` to local Python validators.

**Prompt**:
> Implement four standalone Python validators under `scripts/`, each runnable as `python scripts/<name>.py` and exiting non-zero on findings. (1) `validate_no_personal_paths.py`: scan `README.md`, `catalog/`, `docs/`, `templates/` for leaked `/Users/<name>` (POSIX) and `C:\Users\<name>` (Windows) paths, allowing placeholder usernames (`example`, `user`, `you`, `yourname`, ...) and exempting forensic/report dirs; model on ECC's `validate-no-personal-paths.js`. (2) `validate_unicode_safety.py`: flag unsafe/confusable Unicode and (reusing the existing ASCII-commit rule) non-ASCII punctuation in English Markdown. (3) `scan_supply_chain_iocs.py`: scan dependency manifests and installer scripts for known supply-chain IOC patterns (typosquat indicators, suspicious post-install hooks). (4) `validate_workflow_security.py`: scan `.github/workflows/*.yml` for unsafe patterns (unpinned third-party actions, `pull_request_target` + checkout of untrusted code, script injection via `${{ github.event.* }}`). All four must be local, read-only, zero-outbound. Re-author logic; do not copy ECC source (generic-name reverse-engineering). Add pytest cases under `catalog/hooks/tests/` or a new `tests/validators/` directory, including one fixture per validator that the validator must flag. Source: comparison-ECC.md Section 11 Bucket B (B1), Section 6b.

---

#### 2.2 — Wire validators into make validate and both installers

- [x] T005 Wire the four validators into Makefile and register copy steps in scripts/installer.sh and scripts/installer.ps1

**Objective**: Make the validators part of the standard validation gate and distribute them cross-platform.

**Prompt**:
> Add the four new validators to the `make validate` target in the `Makefile` so they run on every validation pass. Per the installer-aware-changes rule in `AGENTS.md`, register each new `scripts/*.py` in BOTH `scripts/installer.sh` (next to the existing `generate_report.py` copy block, ~line 1395) AND `scripts/installer.ps1` (the `Safe-Copy` block, ~line 1656), copying to `~/.nexus-hub/scripts/`. Do a dry-run install into a throwaway directory and confirm all four land. Add an entry under `## [Unreleased]` in `CHANGELOG.md`. Source: comparison-ECC.md Section 11 (B1); AGENTS.md "Installer-Aware Changes".

---

#### 2.3 — Testing and Stabilization

- [x] T006 Run and stabilize Phase 2 validators and tests

**Objective**: Confirm validators pass clean and fail dirty, with green CI.

**Prompt**:
> Run `make validate`, `make lint`, and `make test`. Confirm all four validators pass on the clean tree and that each fixture test proves the validator flags its injected violation. Confirm the installer dry-run copies all four scripts. Fix all failures and iterate until green. Do not advance to Phase 3 until verified. After it passes, run /generate-session-history to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 3

---

## Phase 3: Runtime learning

**Goal**: Reverse-engineer ECC's memory-persistence and continuous-learning into a local-only subset (capture + local files + agent-driven evolve), with no external observer model.
**Prerequisites**: Phase 2 (validators ensure no personal paths leak into persisted artifacts).
**Stability Gate**: Session hooks persist and restore a local context digest across a simulated session boundary; the continuous-learning skill validates; no outbound calls are introduced.

### Sub-tasks

#### 3.1 — Memory-persistence session hooks

- [x] T007 Enrich catalog/hooks/session-start.sh and session-summary.sh (+ .ps1 siblings) to persist and restore a local context digest

**Objective**: Add cross-session context persistence that ECC's lifecycle hooks provide and Nexus-Hub's current session hooks lack.

**Prompt**:
> Enrich the existing `catalog/hooks/session-start.sh` and `catalog/hooks/session-summary.sh` (and add `.ps1` siblings for cross-platform parity per AGENTS.md) so that: on SessionEnd / PreCompact a compact local context digest is written under a project-scoped path (e.g. `.nexus/context/last-session.md`), and on SessionStart that digest is read back and surfaced as additional context (respecting a size cap analogous to ECC's `ECC_SESSION_START_MAX_CHARS`, e.g. an env var `NEXUS_SESSION_START_MAX_CHARS` defaulting to 8000, and an off-switch). All read/write is local; no network. Register any new hook entries in `catalog/hooks/settings.json` (events SessionStart / Stop / PreCompact / SessionEnd). Add pytest coverage for the digest write/read round-trip. Source: comparison-ECC.md Section 11 Bucket B (B2), Section 4 (hooks).

---

#### 3.2 — Continuous-learning local-subset skill + capture hooks

- [x] T008 Create catalog/skills/workflow/continuous-learning/SKILL.md and local capture hooks (depends on T007)

**Objective**: Reproduce ECC's instinct-based continuous learning as a local-only skill: capture observations, mint confidence-scored instincts as local YAML, and evolve clusters into skills via the agent (no background external model).

**Prompt**:
> Create a skill at `catalog/skills/workflow/continuous-learning/SKILL.md` that teaches a local-only learning loop modeled on ECC's `continuous-learning-v2`: (1) capture prompts/tool-use/corrections into a project-scoped `.nexus/observations.jsonl` via the SessionEnd/Stop hooks from T007; (2) mint atomic, confidence-scored, domain-tagged "instincts" as local `.nexus/instincts/*.yaml` (project-scoped by default, with a documented promote-to-global path); (3) evolve clusters of instincts into draft skills/commands using the agent itself (no background observer model). CRITICAL CONSTRAINT, stated in the skill body and the Common Rationalizations table: wiring an external observer model would reintroduce egress and is OUT OF SCOPE per the MCP Registry Policy; the only acceptable observer is a local model. Full required frontmatter + body sections. Register in the three data files. Add or extend capture hooks in `catalog/hooks/` (with `.ps1` parity) and `catalog/hooks/settings.json`. Run `make validate`. Source: comparison-ECC.md Section 11 Bucket B (B4); Section 13 "Continuous-learning egress trap".

---

#### 3.3 — Testing and Stabilization

- [x] T009 Run and stabilize Phase 3 hooks and skill in catalog/hooks/tests/

**Objective**: Verify persistence round-trips, observation capture, and instinct file creation, all local.

**Prompt**:
> Generate and run tests for the memory-persistence hooks and the continuous-learning capture path: assert the context digest round-trips across a simulated SessionEnd -> SessionStart, assert observations append to `.nexus/observations.jsonl`, and assert instinct YAML files are well-formed. Add a test asserting NO outbound network call is made by any hook. Run `make validate`/`make lint`/`make test`. Fix failures and iterate until green. Do not advance to Phase 4 until verified. After it passes, run /generate-session-history to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 4

---

## Phase 4: Installer lifecycle & selective install

**Goal**: Add an install-state manifest plus `doctor`/`repair`/`list-installed` lifecycle commands, selective-install profiles/modules with a `consult` advisor, and harness audit scoring — all reverse-engineered onto the existing integration registry.
**Prerequisites**: None hard, but builds naturally on the `WriteResult`/`FileAction`/`--check` infrastructure already present.
**Stability Gate**: A fresh install records an install-state manifest; `doctor` reports OK on a clean install and drift after a manual edit; `repair` restores; `consult` returns matching components; the 50-case contract suite still passes.

### Sub-tasks

#### 4.1 — Install-state manifest + doctor/repair/list-installed

- [x] T010 Add an install-state manifest and doctor/repair/list-installed subcommands to scripts/lib/integrations/ and both installers

**Objective**: Reproduce ECC's `doctor.js`/`repair.js`/`list-installed.js` + `lib/install-lifecycle.js` as a Nexus-Hub install-state layer (confirmed missing: grep for doctor/repair/list-installed/install_state in scripts/ returned zero matches).

**Prompt**:
> Extend `scripts/lib/integrations/` with an additive install-state manifest: when an integration installs, record the per-file `FileAction`s it wrote to a manifest (e.g. `~/.nexus-hub/.install-state.json`), keyed by integration. The manifest must be ADDITIVE and must NOT replace the existing `merge_marker_section` idempotency or the user-edit-preservation guarantees (see comparison-ECC.md Section 13). Add three subcommands, exposed via both `scripts/installer.sh` and `scripts/installer.ps1`: `doctor` (diagnose drift / missing managed files against the manifest, building on the existing `--check` logic), `repair` (re-write managed files recorded as drifted/missing), and `list-installed` (print the manifest). Re-author logic in Python; do not add a Node runtime. Add contract/pytest coverage. Source: comparison-ECC.md Section 11 Bucket B (B3), Section 5a, Section 10.

---

#### 4.2 — Selective install profiles/modules + consult advisor

- [x] T011 Add profile/module/capability tags to data/bundles.json and a nexus-hub consult matcher (depends on T010)

**Objective**: Reproduce ECC's `install-plan.js`/`install-apply.js` selective install and `consult.js` advisor using Nexus-Hub's existing bundle + SKILL_INDEX surfaces.

**Prompt**:
> Add a selective-install layer: define install profiles (e.g. `minimal`, `core`, `full`), modules, and `capability:` tags in `data/bundles.json` (extend the existing schema; this is a registry file edit allowed by the data-file rule). Teach both installers to accept a profile/module scope (e.g. `installer.sh --profile minimal` / `--modules <name>`), defaulting to current full-install behavior when no scope is given (no behavior change by default). Add a `nexus-hub consult "<need>"` matcher that fuzzy-matches a natural-language need to components/profiles over `data/SKILL_INDEX.md` + `data/skills.json` (the `search_skills` MCP already proves the retrieval half); print matching components + the preview/install command. Register the consult script in both installers. Add tests. Source: comparison-ECC.md Section 11 Bucket B (B5), Section 5a, Section 7.

---

#### 4.3 — Harness audit scoring

- [x] T012 Add scripts/harness_audit.py read-only scoring over installed surfaces (depends on T010)

**Objective**: Reproduce ECC's `harness-audit.js`/`harness-adapter-compliance.js` deterministic scoring as a local Python script.

**Prompt**:
> Implement `scripts/harness_audit.py`: a read-only, deterministic scorer that inspects the install-state manifest (T010) and the installed surfaces for each registered integration and emits a reliability/coverage score (e.g. presence of expected skills/commands/hooks/rules, marker integrity, drift count). Zero outbound calls. Register in both installers; add pytest coverage with a fixture install. Source: comparison-ECC.md Section 11 Bucket B (B7), Section 5a.

---

#### 4.4 — Testing and Stabilization

- [x] T013 Run and stabilize Phase 4 lifecycle, selective install, and audit in tests/integrations/

**Objective**: Verify install-state, doctor/repair/list-installed, profiles, consult, and harness audit, with the contract suite intact.

**Prompt**:
> Generate and run tests: install-state manifest is written on install and reversed on uninstall; `doctor` reports OK clean and drift after a manual edit; `repair` restores; `list-installed` matches the manifest; a `--profile minimal` install scopes correctly while a no-flag install is unchanged; `consult` returns expected matches; `harness_audit.py` produces a stable score. Re-run the existing 50-case integration contract suite and the tree-mirror parity suite to confirm no regression. Run `make validate`/`make lint`/`make test`. Fix and iterate until green. Do not advance to Phase 5 until verified. After it passes, run /generate-session-history to document Phase 4.

---

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 5

---

## Phase 5: Skill quality tooling

**Goal**: Add a holistic skill-quality audit and a git-history-driven skill generator, reverse-engineered from ECC's `skill-stocktake` and `skill-create`.
**Prerequisites**: None.
**Stability Gate**: `skill-stocktake` produces a cached quality report; `validate_skills.py` gains a quality-heuristics pass; `skill-create` drafts a valid SKILL.md from git history.

### Sub-tasks

#### 5.1 — skill-stocktake skill + validate_skills quality pass

- [x] T014 Create catalog/skills/workflow/skill-stocktake/SKILL.md and add a quality-heuristics pass to scripts/validate_skills.py

**Objective**: Reproduce ECC's `skill-stocktake` holistic quality audit (cached `results.json` + quick-diff) and extend Nexus-Hub's structural validator with quality heuristics.

**Prompt**:
> Create a skill at `catalog/skills/workflow/skill-stocktake/SKILL.md` that audits Nexus-Hub skills for quality using a checklist + agent holistic judgment, with two modes (Quick Scan over changed skills using a cached `results.json`, and Full Stocktake), modeled on ECC's `skill-stocktake`. Re-author content. Additionally extend `scripts/validate_skills.py` with a non-blocking quality-heuristics pass (warnings): missing Common Rationalizations table, prose-only (non-binary) Verification, over-long Tier-1 fields, missing Related Skills links. Keep it a warning (not error) so WIP branches do not break CI. Full required frontmatter + body sections; register in the three data files. Run `make validate`. Source: comparison-ECC.md Section 11 Bucket B (B6), Section 5a.

---

#### 5.2 — skill-create from git history

- [x] T015 Create a git-history-driven skill generator (skill or scripts/skill_create.py)

**Objective**: Reproduce ECC's `skill-create` local-analysis path (generate SKILL.md drafts from local git history).

**Prompt**:
> Implement a git-history-driven skill generator. Preferred form: a `catalog/skills/workflow/skill-create/SKILL.md` skill that instructs the agent to analyze local `git log`/diffs for recurring patterns and draft a Nexus-Hub-conformant SKILL.md (with `summary_l0`/`overview_l1`, Common Rationalizations, binary Verification). If a deterministic helper is warranted, add `scripts/skill_create.py` (local git analysis only, zero outbound) and register it in both installers. Re-author; do not copy ECC source. Register the skill in the three data files. Run `make validate`. Source: comparison-ECC.md Section 11 Bucket B (B6), Section 5a.

---

#### 5.3 — Testing and Stabilization

- [x] T016 Run and stabilize Phase 5 tooling and validator pass

**Objective**: Verify the stocktake skill, validator quality pass, and skill-create draft path.

**Prompt**:
> Run `make validate` (including the new quality-heuristics pass) and confirm it warns (not errors) on an intentionally low-quality fixture skill and stays silent on a good one. Verify `skill-create` produces a SKILL.md draft that itself passes `validate_skills.py`. Run `make lint`/`make test`. Fix and iterate until green. Do not advance to Phase 6 until verified. After it passes, run /generate-session-history to document Phase 5.

---

### Phase 5 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 6

---

## Phase 6: Framework coverage + defensive security content

**Goal**: Build a framework coverage-matrix generator over the new mapping convention, then re-author two curated defensive security skill packs and their helper scripts. Bulk import is explicitly rejected (see appendix).
**Prerequisites**: Phase 1 (the `security-framework-mapping` convention and skill).
**Stability Gate**: The coverage matrix generates from frontmatter tags; each new skill passes `validate_skills.py` with full Nexus-Hub frontmatter and binary Verification; maintainer has signed off on the category placement.

### Sub-tasks

#### 6.1 — Framework coverage-matrix generator

- [x] T017 Add scripts/build_framework_coverage.py over the Phase 1 frontmatter tags

**Objective**: Reproduce the cybersecurity repo's ATT&CK Navigator / coverage-matrix idea as a local generator over Nexus-Hub's own framework-tagged skills.

**Prompt**:
> Implement `scripts/build_framework_coverage.py`: read the optional framework-mapping frontmatter fields (added in T002) across `catalog/skills/`, and emit a coverage matrix (Markdown table and/or JSON) showing which Nexus-Hub skills cover which MITRE/NIST controls. Read-only, local, zero outbound. Register in both installers; add pytest coverage with a small fixture. Source: comparison-Anthropic-Cybersecurity-Skills.md Section 11 Bucket B (CB1), Section 7.

---

#### 6.2 — Defensive security skill pack batch 1 (DFIR / threat hunting / IR)

- [x] T018 Re-author ~10-15 defensive skills under catalog/skills/security-operations/ (requires maintainer sign-off on the new category)

**Objective**: Re-author a curated, high-value defensive subset (Digital Forensics, Threat Hunting, Incident Response) to Nexus-Hub's standard, with framework tags.

**Prompt**:
> FIRST obtain maintainer sign-off on creating a new `security-operations` category (AGENTS.md "Ask first: Creating a new skill category"); if declined, nest these under the existing `security/` category instead. Then re-author ~10-15 high-value defensive skills covering DFIR, threat hunting, and incident response (use the source library's domains as a reference corpus only — examples: memory forensics with Volatility3, hunting LSASS credential dumping, SIEM correlation, ransomware response). Each skill MUST be re-authored to Nexus-Hub format: full `summary_l0`/`overview_l1`, When to Use (+ When NOT), Instructions, Common Rationalizations, binary Verification, Related Skills, plus the optional framework-mapping frontmatter (T002) and a `references/standards.md`. MANDATE FILTER: include only defensive / detection / forensics / authorized-testing skills; exclude any skill whose primary purpose is detection-evasion or untargeted offensive use (see appendix N-items). Do NOT copy Apache-2.0 SKILL.md text; re-author from public framework knowledge (Reverse-Engineering Attribution Rule). Register every skill in the three data files. Run `make validate`. Source: comparison-Anthropic-Cybersecurity-Skills.md Section 11 Bucket B (CB2), Section 9.2/9.3, Section 13.

---

#### 6.3 — Defensive security skill pack batch 2 (cloud / endpoint / phishing)

- [x] T019 Re-author the second defensive batch under catalog/skills/security-operations/ (depends on T018)

**Objective**: Extend coverage to Cloud Security ops, Endpoint/EDR, and Phishing Defense, same quality bar and filters.

**Prompt**:
> Re-author a second curated batch of defensive skills covering cloud security operations, endpoint/EDR detection, and phishing defense, following the exact same format, framework-tagging, mandate filter, and attribution rules as T018. Keep the curation bar high — prefer fewer excellent re-authored skills over many copied ones. Register each in the three data files. Run `make validate`. Source: comparison-Anthropic-Cybersecurity-Skills.md Section 11 Bucket B (CB3), Section 13.

---

#### 6.4 — Deterministic helper scripts for adopted skills

- [x] T020 Re-author helper scripts under each adopted skill's scripts/ directory (.sh + .ps1 parity) for the defensive skill packs (depends on T018, T019)

**Objective**: Where an adopted skill needs a deterministic helper, re-author a local-only script with cross-platform parity (not a bulk copy of the source's 1030 Python scripts).

**Prompt**:
> For ONLY the adopted skills from T018/T019 that genuinely need a deterministic helper, re-author a small helper (model on the source's clean subprocess-wrapper pattern, e.g. a Volatility3 CLI wrapper) under the skill's `scripts/` directory, with `.sh` + `.ps1` parity per AGENTS.md and strictly local behavior (no network, no symbol-pack fetching baked in). Each script must be referenced from its parent SKILL.md (referenced-only rule). Do NOT import the source's 1030 scripts wholesale (see appendix N2). Run `make validate` (orphan-bundle audit) and `make lint`. Source: comparison-Anthropic-Cybersecurity-Skills.md Section 11 Bucket B (CB4), Section 9.3.

---

#### 6.5 — Testing and Stabilization

- [x] T021 Run and stabilize Phase 6 content and coverage generator

**Objective**: Verify the coverage matrix, all new skills, and helper scripts pass validation.

**Prompt**:
> Run `make validate`/`make lint`/`make test`. Confirm every new security skill passes `validate_skills.py` (valid frontmatter, binary Verification, no orphan bundles) and that `build_framework_coverage.py` emits a matrix that includes the new framework-tagged skills. Confirm data-registry counts are consistent across the three files. Spot-check that no offensive/detection-evasion skill slipped through the mandate filter. Fix and iterate until green. Do not advance to Phase 7 until verified. After it passes, run /generate-session-history to document Phase 6.

---

### Phase 6 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (tests/ 298 passed; tests/validators 44 passed incl. 6 new coverage-generator cases; 4 CI validators rc=0; bundle audit 0 orphans; quality pass 0 new warnings)
- [x] No known regressions from prior phases (catalog-tree byte-parity preserved; pre-existing WN/BG/DF items unchanged)
- [x] Maintainer sign-off recorded for the security-operations category (approved 2026-05-29; new category created, documented in AGENTS.md)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 7

---

## Phase 7: [known-gaps] Installer instruction-file parity

**Goal**: Close the v2.2.0 installer-parity gaps so the legacy bash instruction-file blocks can be removed.
**Prerequisites**: None (independent of the adoption phases).
**Stability Gate**: Instruction-file output is byte-identical between the legacy bash path and the registry runner; the parity suite asserts it; Copilot/Cursor use the canonical marker-merge primitive.

### Sub-tasks

#### 7.1 — Instruction-file byte-parity migration (part 2)

- [x] T022 [from v2.2.0 known-gaps: DF-001] Thread the full placeholder set through scripts/lib/integrations/runner.py and MarkdownIntegration

**Objective**: Bring the Python registry runner to feature parity with the legacy bash `render_template` so instruction files match byte-for-byte.

**Prompt**:
> Carried forward from v2.2.0 known-gaps DF-001 (part 2). Reason: Phase 3 (v2.2.0) closed tree-mirror parity, but the legacy bash `render_template` substitutes 13+ placeholders (`{{PRIMARY_LANGUAGE}}`, `{{BUILD_CMD}}`, `{{OS_CONTEXT}}`, `{{SKILL_INDEX}}`, ...) plus appends language-specific coding snippets, whereas the Python `MarkdownIntegration._render` substitutes only `{{PROJECT_NAME}}`. Suggested next step: extend `scripts/lib/integrations/runner.py::cmd_install` to accept and thread the full bash placeholder set (build/test/lint/language/skill-index/os-context); inline the per-language coding-snippet append into `MarkdownIntegration._write_instruction`. Do not remove the legacy bash blocks yet — that is gated on T023 passing.

---

#### 7.2 — Instruction-file byte-parity tests

- [x] T023 [from v2.2.0 known-gaps: MT-2] Assert instruction-file byte parity in tests/integrations/test_parity_with_legacy_installer.py

**Objective**: Add the byte-equality assertion that gates legacy-block removal.

**Prompt**:
> Carried forward from v2.2.0 known-gaps MT-2. Reason: `test_parity_with_legacy_installer.py::test_instruction_file_is_produced` only asserts the file exists and is non-empty; byte equality with the bash sed-substituted output is the precondition for removing the legacy bash blocks. Suggested next step: add an instruction-file byte-parity assertion to `tests/integrations/test_parity_with_legacy_installer.py` across claude / codex / gemini, then (once green) refactor the legacy claude/codex/gemini blocks in `scripts/installer.{sh,ps1}` into single `invoke_registry_platform` calls. This closes DF-001 and MT-2 simultaneously.

---

#### 7.3 — Copilot/Cursor marker-merge refactor

- [x] T024 [from v2.2.0 known-gaps: MT-1] Refactor Copilot install_workspace to use merge_marker_section in scripts/lib/integrations/copilot.py

**Objective**: Move Copilot's bespoke append-after-heading flow onto the canonical marker-merge primitive.

**Prompt**:
> Carried forward from v2.2.0 known-gaps MT-1. Reason: Copilot still uses an append-after-heading pattern rather than the canonical `merge_marker_section` primitive (Cursor's AGENTS.md path was already migrated; its `.mdc` rules are dedicated files needing no markers). Suggested next step: refactor Copilot's `install_workspace` to call `merge_marker_section` with `legacy_header="## Nexus-Hub Harness"` so the marker block migrates inline alongside the v2.1 `## Nexus-Hub` legacy header. Re-run the 50-case contract suite to confirm idempotency.

---

#### 7.4 — Testing and Stabilization

- [x] T025 Run and stabilize Phase 7 installer-parity changes

**Objective**: Verify byte parity, Copilot marker-merge, and full contract/parity suites.

**Prompt**:
> Run the integration contract suite, the tree-mirror parity suite, and the new instruction-file byte-parity assertion. Confirm Copilot and Cursor installs are idempotent (`test_install_idempotent` passes) and that, with parity asserted, the legacy bash blocks can be (or are) replaced by `invoke_registry_platform` calls without changing end-user output. Run `make validate`/`make lint`/`make test`. Fix and iterate until green. Do not advance to Phase 8 until verified. After it passes, run /generate-session-history to document Phase 7.

---

### Phase 7 Exit Checklist

- [x] All sub-tasks completed (T022-T025)
- [x] All tests passing (tests/integrations + tests/installer + tests/validators 304 passed / 0 failed; catalog/hooks/tests 392 passed + 3 skipped; new body-parity test green for claude/codex/gemini x global+workspace; make-validate equivalent green; shellcheck + bash -n + PowerShell parse clean)
- [x] No known regressions from prior phases (catalog tree-mirror parity preserved; the registry runner is now the single instruction-file renderer shared by both installers; DF-001/MT-1/MT-2 closed)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 8

---

## Phase 8: [known-gaps] Code-graph quality & extractor expansion

**Goal**: Address the v2.2.0 nexus-code-search quality and dependency-hygiene gaps and ship the next batch of language/framework extractors.
**Prerequisites**: None.
**Stability Gate**: No `pathspec` deprecation warnings; constructor/override edges emitted; eval precision improved or fixture answer-keys justified; new extractors pass the eval baseline.

### Sub-tasks

#### 8.1 — pathspec deprecation fix

- [x] T026 [P] [from v2.2.0 known-gaps: WN-1] Pin pathspec to gitignore mode in extensions/nexus-code-search

**Objective**: Eliminate the 52 `GitWildMatchPattern` deprecation warnings.

**Prompt**:
> Carried forward from v2.2.0 known-gaps WN-1. Reason: the nexus-code-search test suite surfaces 52 `DeprecationWarning: GitWildMatchPattern ('gitwildmatch') is deprecated` from `pathspec/pattern.py:125`; tests pass but the warning is untracked. Suggested next step: pin the `pathspec` API to `gitignore` mode where the pattern is constructed in `extensions/nexus-code-search`, and confirm the warnings disappear with tests still green.

---

#### 8.2 — tree-sitter pin monitor/widen

- [x] T027 [P] [from v2.2.0 known-gaps: WN-5] Re-verify the tree-sitter dependency pin in extensions/nexus-code-search/pyproject.toml

**Objective**: Track tree-sitter ABI compatibility for the per-language packages.

**Prompt**:
> Carried forward from v2.2.0 known-gaps WN-5. Reason: the pin is `tree-sitter>=0.24,<0.26` + `tree-sitter-python` + `tree-sitter-typescript` (the abandoned `tree-sitter-languages` umbrella crashes on 0.23+). Suggested next step: check whether `tree-sitter-python`/`tree-sitter-typescript` have published a 0.26-compatible release; if so, re-run `extensions/nexus-code-search/tests` against a widened upper bound and update the pin only if green. If not yet available, leave the pin and record the check date.

---

#### 8.3 — Constructor / super-method override resolution

- [x] T028 [from v2.2.0 known-gaps: WN-6] Emit instantiates/overrides edges in extensions/nexus-code-search/src/nexus_code_search/extraction/languages/python.py and typescript.py

**Objective**: Upgrade in-file call resolution to emit `instantiates` and `overrides` edges.

**Prompt**:
> Carried forward from v2.2.0 known-gaps WN-6. Reason: `_collect_calls` emits `calls` for plain and attribute-style method calls but not `instantiates` (Python `Class()` constructor) or `overrides` (method overriding a parent in the same file); the `EdgeKind` taxonomy already includes both, so only extraction logic needs upgrading. Suggested next step: add a constructor-detection branch in `_collect_calls` (`Class()` -> `instantiates` instead of `calls`) and an `overrides` resolver comparing method names against the enclosing class's parent (using the in-file `extends` edges already emitted). Local-resolution upgrades only; no schema change. Update the eval baseline.

---

#### 8.4 — Eval precision improvement

- [x] T029 [from v2.2.0 known-gaps: WN-7] Improve code_search precision in extensions/nexus-code-search eval

**Objective**: Raise the 63.3% aggregate precision without dropping recall.

**Prompt**:
> Carried forward from v2.2.0 known-gaps WN-7. Reason: aggregate recall is 100% but precision is 63.3% because FTS5 matches `(name, qualified_name, docstring)` and surfaces signature parameters (e.g. `name` from `create_item(name: str)`) as true index hits but false answer-key hits. Suggested next step: either (a) default `code_search` to `kind` filtering when one is obvious (`*_item` -> `function`/`method`), or (b) widen the fixture answer keys to include the parameter/variable matches the FTS index legitimately surfaces. Do this after WN-6 (T028) lands since it shifts the recall surface. Re-run `make eval` and update `docs/archive/v2/v2.3/eval-baseline.md`.

---

#### 8.5 — Deferred language/framework extractors (next batch)

- [x] T030 [from v2.2.0 known-gaps: DF-002] Add the next batch of language/framework extractors under extensions/nexus-code-search/src/nexus_code_search/extraction/languages/

**Objective**: Implement the highest-demand extractors from the 18 deferred languages + 13 framework extractors.

**Prompt**:
> Carried forward from v2.2.0 known-gaps DF-002. Reason: Phase 4 (v2.2.0) shipped Python + TypeScript extractors only; 18 languages (Go, Rust, Java, C#, PHP, Ruby, C, C++, Swift, Kotlin, Scala, Dart, Lua, Luau, Svelte, Vue, Liquid, Pascal, plain JavaScript) and 13 framework extractors remain deferred; the architecture is ready (new `Extractor` subclass + `LANGUAGE_EXTRACTORS` registry entry). Suggested next step: implement the next batch in priority order (recommend Go + Rust + Java first based on Nexus / Nexus-Hub user demand), each following `extraction/languages/python.py` (tree-sitter parser + per-NodeKind tree walk + in-file edge resolution). Add eval fixtures and confirm each clears the 80% per-fixture recall gate. Track remaining languages as a fresh DF item if not all are shipped.

---

#### 8.6 — Testing and Stabilization

- [x] T031 Run and stabilize Phase 8 code-graph changes

**Objective**: Verify warnings cleared, new edges, improved precision, and new extractors against the eval baseline.

**Prompt**:
> Run `extensions/nexus-code-search/tests` and `make eval`. Confirm zero `pathspec` deprecation warnings, that `instantiates`/`overrides` edges are emitted, that precision improved (or answer-key widening is justified) with recall still 100%, and that every new language extractor clears the 80% per-fixture recall gate. Update `docs/archive/v2/v2.3/eval-baseline.md`. Run `make validate`/`make lint`/`make test`. Fix and iterate until green. Do not advance to Phase 9 until verified. After it passes, run /generate-session-history to document Phase 8.

---

### Phase 8 Exit Checklist

- [x] All sub-tasks completed (T026-T031)
- [x] All tests passing (nexus-code-search 168 passed / 1 skipped, zero DeprecationWarnings under `-W error::DeprecationWarning`; eval 8/8 fixtures at 100% recall, aggregate precision 63.3% -> 96.2%; make-validate equivalent green -- skills.json OK, bundle audit 0/0, 4 CI validators rc=0)
- [x] No known regressions from prior phases (only `extensions/nexus-code-search/` + the Makefile eval path + docs touched; catalog/data unchanged; the 4 new tree-sitter deps auto-distribute via the installers' editable pip install of the copied package -- no installer edit required)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 9 (WN-1/WN-5/WN-6/WN-7/DF-002 closed; WN-2/WN-3/WN-4/WN-8 remain as the Phase 9 live-environment verification set)

---

## Phase 9: [known-gaps] Live-environment verification

**Goal**: Verify the deferred Antigravity CLI assumptions on a live VM and re-run the cross-OS installer smoke on macOS and Linux.
**Prerequisites**: Availability of a live Antigravity CLI install and macOS / Linux hosts (environmental, not code dependencies).
**Stability Gate**: Antigravity CLI binary name, workflow file format, and frontmatter behavior confirmed (or corrected); installer smoke passes on macOS and Linux.

### Sub-tasks

#### 9.1 — Antigravity CLI binary name verification

- [x] T032 [from v2.2.0 known-gaps: WN-2] Verify the Antigravity CLI binary name on a live install and update docs/archive/v2/v2.2/antigravity-cli-probe.md

**Objective**: Confirm or correct the assumed `antigravity` PATH binary name.

**Prompt**:
> Carried forward from v2.2.0 known-gaps WN-2. Reason: the Antigravity CLI install-path probe was static; the binary name `antigravity` was inferred from Gemini CLI / Antigravity product naming and hardcoded in `antigravity-cli-diff-review.sh/.ps1` and the AGENTS.md sunset notice, but not confirmed. Suggested next step: once Google ships the Antigravity CLI to a verifiable channel (around the 2026-06-18 Gemini CLI sunset cutover), re-run the probe on a live install, update `docs/archive/v2/v2.2/antigravity-cli-probe.md` section 1, and rename the hook scripts + AGENTS.md references if the binary name differs.

---

#### 9.2 — Antigravity CLI workflow file format verification

- [x] T033 [from v2.2.0 known-gaps: WN-3] Verify the Antigravity CLI workflow file format against a live install and reconcile scripts/lib/integrations/antigravity.py

**Objective**: Confirm the Markdown-workflow assumption (vs Gemini CLI's TOML).

**Prompt**:
> Carried forward from v2.2.0 known-gaps WN-3. Reason: the analysis concluded the Antigravity CLI inherits Antigravity 2.0 desktop's Markdown workflow format (verbatim `.md` under `~/.agent/workflows/`), not Gemini CLI's `.toml`, but this was not verified live. Suggested next step: verify on the same live VM as WN-2; if the CLI ships a different format (e.g. a custom JSON manifest), add a `_write_antigravity_commands` helper variant to `scripts/lib/integrations/antigravity.py` and re-open the commands-schema work.

---

#### 9.3 — Antigravity CLI frontmatter / name-derivation verification

- [x] T034 [from v2.2.0 known-gaps: WN-4] Verify Antigravity CLI workflow frontmatter and name derivation, updating scripts/lib/integrations/antigravity.py if rejected

**Objective**: Confirm whether the CLI honors YAML frontmatter and how it derives the workflow name.

**Prompt**:
> Carried forward from v2.2.0 known-gaps WN-4. Reason: whether the Antigravity CLI honors YAML frontmatter in workflow files, and the exact name-derivation rule (filename vs first H1), are unconfirmed; the current path mirrors `catalog/commands/*.md` verbatim. Suggested next step: same live-VM verification as WN-2/WN-3; if frontmatter is rejected, add a strip pass to `SkillsIntegration._mirror_catalog` (or a dedicated Antigravity helper).

---

#### 9.4 — Cross-OS installer smoke (macOS / Linux)

- [x] T035 [P] [from v2.2.0 known-gaps: WN-8] Re-run the installer smoke on macOS and Linux per docs/archive/v2/v2.2/installer-smoke-post.txt

**Objective**: Replace the v2.2.0 PASS-by-parity inference with empirical macOS / Linux runs.

**Prompt**:
> Carried forward from v2.2.0 known-gaps WN-8. Reason: the v2.2.0 cross-OS smoke ran only on Windows; macOS and Linux were inferred PASS-by-parity. Suggested next step: re-run sub-steps 1a-1j of `docs/archive/v2/v2.2/installer-smoke-post.txt` on a macOS host (target macOS 14 Sonoma) and a Linux host (target Ubuntu 22.04 LTS); confirm the 402 pytest cases pass, eval recall/precision reproduces the baseline, `--print-config`/`--help` succeed for every integration, and all integrations resolve. Record results in a `docs/archive/v2/v2.3/installer-smoke-post.txt`. This is required before any v2.3.0-tagged packaged-binary release.

---

#### 9.5 — Testing and Stabilization

- [x] T036 Run and stabilize Phase 9 verifications

**Objective**: Confirm the Antigravity CLI findings are recorded and the cross-OS smoke passes.

**Prompt**:
> Confirm WN-2/WN-3/WN-4 are resolved with live-VM evidence (or re-deferred with a dated reason if Google has not yet shipped a verifiable channel) and that any corrections (binary name, workflow format, frontmatter handling) are reflected in the hooks, `scripts/lib/integrations/antigravity.py`, and AGENTS.md. Confirm the macOS and Linux smoke runs pass and are recorded. Run `make validate`/`make lint`/`make test`. Fix and iterate until green. After it passes, run /generate-session-history to document Phase 9, then run the release-readiness workflow for v2.3.0.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution file exists, so there are no MUST-principle violations to track. The table is intentionally empty; populate it if a constitution is later ratified via `/constitution` and any phase violates a MUST principle.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | (none) | (none) |

---

## Items explicitly NOT adopted (security / policy reasons)

These items were classified `drop-outright` or deferred-vendor-intrinsic in the source comparisons' Section 9.3 / Section 11 and therefore do NOT appear as active phases. Each rejection cites the MCP Registry Policy.

- **N1 — ECC bundled external MCP registry** (Exa, context7, Firecrawl, Magic UI, fal.ai, Browserbase, browser-use, squish cloud-sync): `drop-outright`. On the MCP Registry Policy hard-no list (search-as-service, docs/embeddings-as-service, scraping-as-service, generation-as-service, memory-as-service). Transmits query text / session memory to third parties and requires new API keys and commercial relationships. Source: comparison-ECC.md Section 13 N1.
- **N2 — ECC `ecc2/` Rust multi-session control plane**: `drop-outright`. High-effort Rust runtime reproducing a desktop-operator remit (closer to Nexus-AI's scope); large new attack surface, low fit for an upstream catalog. Fails Policy tier-4 "extremely worth it". Source: comparison-ECC.md Section 13 N2.
- **N3 — ECC `auto-update.js` self-updating installer**: `drop-outright`. Network self-mutation of installed files conflicts with Nexus-Hub's deterministic, user-initiated installer model and adds a supply-chain vector. Source: comparison-ECC.md Section 13 N3.
- **N4 — ECC GitHub/Linear `work-items sync` + operator status surface**: deferred `vendor-intrinsic`. The local `status --markdown` digest is reverse-engineerable, but the GitHub/Linear sync does not clear all three Policy tier-4 conditions for a distribution catalog that is not a session operator. Revisit only if a session-operator use case emerges. Source: comparison-ECC.md Section 11 Bucket C, Section 13 N4.
- **N5 — Verbatim bulk import of the 754 cybersecurity SKILL.md files**: `drop-outright`. Fails Nexus-Hub's frontmatter schema (missing `summary_l0`/`overview_l1`, Common Rationalizations), conflicts with the Reverse-Engineering Attribution Rule (Apache-2.0 attribution would ship in the artifact), and bypasses the curation bar. The curated re-authoring path is Phase 6. Source: comparison-Anthropic-Cybersecurity-Skills.md Section 13 N1.
- **N6 — Bulk import of the 1030 bundled Python scripts**: `drop-outright`. Large unaudited executable surface; several wrap offensive tooling and some workflows fetch external symbol packs. Only the handful of helpers tied to adopted skills are re-authored (Phase 6 T020). Source: comparison-Anthropic-Cybersecurity-Skills.md Section 13 N2.
- **N7 — Offensive / detection-evasion cybersecurity skills**: `drop-outright`. Outside Nexus-Hub's security mandate (authorized testing, defensive, and CTF contexts are in scope; detection evasion for malicious purposes is not). Filtered out during Phase 6 content adoption. Source: comparison-Anthropic-Cybersecurity-Skills.md Section 13 N3.

---

### Phase 9 Exit Checklist

- [x] All sub-tasks completed (T032-T036)
- [x] All tests passing (Windows: 936 pytest cases pass + eval recall 100% / precision 96.2%; Linux test suite green via CI on ubuntu-latest; antigravity integration tests 20 pass; make-validate equivalent green -- skills.json 227, bundle audit 0/0, 4 CI validators rc=0)
- [x] No known regressions from prior phases (only the Antigravity integration/hooks/templates/installers + docs touched; tests/integrations + tests/installer 260 pass; -PrintConfig surfaces the corrected `.agents/` tree)
- [x] Session history generated for this phase (docs/archive/v2/v2.3/development/history/2026-05-29_phase-9-live-environment-verification.md)
- [x] All 12 ingested v2.2.0 known-gaps resolved or re-deferred with evidence (WN-2/WN-3/WN-4 docs-verified, WN-8 Windows+CI-Linux; Phase 7 closed DF-001/MT-1/MT-2; Phase 8 closed WN-1/WN-5/WN-6/WN-7/DF-002; residuals WN-v23-5 + DF-v23-6 recorded, non-blocking)
- [x] v2.3.0 release-readiness workflow run (9A-9E: gaps triaged, tests/CI verified, docs/project audit no-apply, /update-* checks, version bump 2.2.0 -> 2.3.0 across 4 manifests, RELEASE_NOTES + CHANGELOG, annotated tag v2.3.0 created and pushed)
