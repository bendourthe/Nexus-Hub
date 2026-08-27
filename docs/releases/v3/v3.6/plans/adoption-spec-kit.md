# Plan -- Spec Kit Delta Adoption (v3.6.0)

**Project**: Nexus-Hub
**Version**: v3.6.0
**Slug**: adoption-spec-kit
**Plan Type**: Feature / Enhancement (comparison adoption)
**Created**: 2026-06-16
**Source comparison**: [docs/releases/v3/v3.6/comparisons/v3.6.0-comparison-spec-kit.md](../comparison-spec-kit.md)
**Goal**: Operationalize the policy-clean recommendations from the v3.5.0 Spec Kit re-comparison -- folding spec-kit's post-v2.0.0 extensibility *disciplines* into Nexus-Hub's local-first equivalents -- and make the two deliberate declines durable, without adding any new outbound call, credential, or third-party data processor.

## Overview

The v3.5.0 re-comparison against GitHub Spec Kit found the prior (v2.0.0) adoption 100% complete and surfaced a new delta from spec-kit's evolution into an extensibility ecosystem (extensions, workflow engine, presets, self-upgrade, authentication, catalog infra). That delta is security-dominated: most of the new surface moves third-party code or credentials across a trust boundary. The comparison's mandatory Security and Reverse-Engineering assessment classified the candidates into **2 clean skill-native adoptions, 3 partial / local re-builds, 2 deferred items, and 2 deliberate declines** (one a hard MCP Registry Policy collision).

This plan operationalizes the recommended bucket (Section 7 of the comparison) in reverse-engineer-first order: skill-native doctrine folds first, then the three local re-builds (the high-value `base-*.md` parity-governance check leading), then a close-out phase. Crucially, the close-out phase records the two declined items (N5 authentication framework, N1b third-party extension install) in the reverse-engineering matrix so a future comparison recognizes them as already-adjudicated, and logs the two deferred items (N4 self-upgrade CLI, N2b portable workflow engine) in the known-gaps tracker. Every deliverable is additive and backward-compatible, so v3.6.0 is a MINOR bump.

Success looks like: a `make validate && make lint && make test` green run with the new parity-governance guard in the suite; updated `loop-engineering`, `agent-orchestration-primitives`, `agent-presets`, and `theme-tokens` skill bodies; a workflow-phase hooks recipe within the existing 4-event Claude hook model; a hardened `/skills import` path; matrix rows for the declines; and a CHANGELOG `[Unreleased]` block enumerating the adoptions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/v3/v3.6/constitution.md (nor at docs/v3/v3.5/constitution.md or docs/constitution.md) - skipping check. Recommend running `/constitution` to establish project principles. This is informational, not blocking.

Note: this plan's own governing principle is inherited from the comparison report and AGENTS.md - the **MCP Registry Policy** (reverse-engineer-first; hard-no on code/credential-distribution-as-service). Every phase below is designed to honor it; the close-out phase (Phase 5) makes the policy-driven declines durable.

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Skill-native doctrine folds (N2a + N3b) | Gate / resume / continue-on-error vocabulary in orchestration skills; template composition-strategy vocabulary in preset skills | Strong reasoning tier, medium effort (session: Opus 4.8, medium) - prose-only, but cross-skill consistency matters |
| 2 | `base-*.md` parity-governance check (N3a) | New repo-internal `check_base_template_parity.py` guard + make target, modeled on `check_version_sync.py`; structural (not byte) comparison | Strong reasoning tier, high effort (session: Opus 4.8, high) - false-positive risk on intentional per-platform lines |
| 3 | Workflow-phase hook recipe (N1a) | Hooks-authoring guidance + example workflow-phase hook configs within the existing 4-event Claude model; no new event types | Strong reasoning tier, high effort (session: Opus 4.8, high) - touches catalog/hooks/settings.json (ask-first area) |
| 4 | `/skills import` hygiene (N6) | HTTPS-only validation + discovery-only flag + hash-on-import on the import path, reusing existing manifest hashing | Strong reasoning tier, high effort (session: Opus 4.8, high) - security-sensitive path |
| 5 | Decline-durability + release readiness | Matrix rows for N5 + N1b declines; known-gaps entries for N4 + N2b; CHANGELOG; full validate/lint/test | Strong reasoning tier, medium effort (session: Opus 4.8, medium) - docs + verification |

The "Rec. model / effort" column is a best-effort per-phase routing assessment (skill Step 3.5). Live model enumeration was not performed at planning time; recommendations are recorded as platform-agnostic tier intent plus the current session model (Opus 4.8) and will be re-confirmed by `/implement` against the then-current model set. Phases 2-4 default to high effort under the no-degradation guarantee (validator-logic correctness, hook-system changes, and a security-sensitive path are all high-risk signals).

---

## Phase 1: Skill-native doctrine folds (N2a + N3b)

**Goal**: Fold spec-kit's workflow gate / persisted-resume / continue-on-error vocabulary and its template composition-strategy vocabulary into the existing Nexus-Hub skills, as prose - zero code, zero new files.
**Prerequisites**: None.
**Stability Gate**: `make validate` passes (orphan-bundle + JSON integrity clean); the four edited skill bodies still parse (YAML frontmatter intact, `summary_l0` / `overview_l1` present); each edit traces to a specific comparison candidate (N2a or N3b).
**Recommended model**: Strong reasoning tier, medium effort (session: Opus 4.8, medium). Rationale: prose-only, but the edits must stay consistent across four skills and respect the three-tier loading model and 500-line size norm; re-confirm at implementation time.

### Sub-tasks

#### 1.1 -- Fold gate / resume / continue-on-error vocabulary into orchestration skills (N2a)

**Objective**: Add spec-kit's workflow-control vocabulary - human **gate** checkpoints, **persisted resume from checkpoint**, and per-step **continue-on-error** - as documented patterns in Nexus-Hub's orchestration skills, where fan-out and gates already partially exist.

**Prompt**:
> In the Nexus-Hub repo, update two skill bodies to document three workflow-control patterns adopted from GitHub Spec Kit's workflow engine (see docs/v3/v3.6/comparisons/v3.6.0-comparison-spec-kit.md candidate N2a and Section 3 row 2):
> 1. `catalog/skills/workflow/loop-engineering/SKILL.md`
> 2. `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md`
>
> Add concise guidance (prose + one short example each, no new files) covering: (a) **human gate checkpoints** that pause a loop/workflow for approve/reject with an `on_reject` policy of abort/skip/retry; (b) **persisted resume-from-checkpoint** - recording per-step state so an interrupted run resumes at the failed step rather than restarting; (c) **per-step continue-on-error** - recording a step failure and continuing, with the failed step's status available to downstream conditional logic. Frame all three as agent-instruction patterns (LLM-native), explicitly NOT as a new runtime - cross-reference the harness's Dynamic Workflows where relevant. Respect the three-tier loading model and the 500-line soft target; if either skill would exceed it, push detail to a `references/` file and link it. Do NOT touch the YAML frontmatter except to bump any internal version field if present. These are body-prose edits only; no SKILL_INDEX/skills.json/marketplace.json changes are required because no skill is added or renamed.

---

#### 1.2 -- Fold template composition-strategy vocabulary into preset skills (N3b)

**Objective**: Document spec-kit's preset composition strategies (replace / prepend / append / wrap-with-placeholder) as a layering vocabulary in the skills that already do token/preset overrides.

**Prompt**:
> In the Nexus-Hub repo, update two skill bodies to document the template composition-strategy vocabulary adopted from GitHub Spec Kit's presets system (see docs/v3/v3.6/comparisons/v3.6.0-comparison-spec-kit.md candidate N3b and Section 3 row 3):
> 1. `catalog/skills/workflow/agent-presets/SKILL.md`
> 2. `catalog/skills/specialized-domains/theme-tokens/SKILL.md`
>
> Add a short "composition strategies" subsection to each: `replace` (default - fully replaces lower-priority content), `prepend` (place before, blank-line separated), `append` (place after), and `wrap` (content contains a `{CORE_TEMPLATE}` placeholder replaced with the lower-priority content). Explain when each applies to layering preset/theme overrides without forking the base. Keep it to prose plus one minimal example per strategy. Body-prose edits only; respect the three-tier model and 500-line target. No registry-file changes (no skill added or renamed).

---

#### 1.3 -- Testing and Stabilization

**Objective**: Verify the prose folds did not break catalog integrity. Iterate until stable.

**Prompt**:
> Run `make validate` and confirm: JSON catalog integrity passes, the orphan-bundle audit is clean, and the four edited SKILL.md files (loop-engineering, agent-orchestration-primitives, agent-presets, theme-tokens) still have valid YAML frontmatter with `summary_l0` and `overview_l1` present. Run `make lint` to confirm no shell regressions. Confirm each of the four files is within the 500-line soft target (or pushes overflow to a referenced `references/` file). Fix any failure and re-run until clean. Then run `/generate-session-history` to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] `make validate` passes (JSON integrity + orphan-bundle audit clean)
- [x] `make lint` passes
- [x] All four edited skills retain valid frontmatter (`summary_l0` / `overview_l1`)
- [x] No registry files (SKILL_INDEX / skills.json / marketplace.json) changed (none required)
- [x] No known regressions from prior work
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: `base-*.md` parity-governance check (N3a)

**Goal**: Ship a repo-internal validator that enforces the AGENTS.md `base-*.md` lock-step parity constraint structurally, modeled on the existing `check_version_sync.py` guard - the highest-value item in the comparison.
**Prerequisites**: None (independent of Phase 1).
**Stability Gate**: The guard runs in `make validate` (or a dedicated `make` target wired into validate/CI), passes on the current five in-sync `base-*.md` templates, and FAILS on a deliberately-desynced fixture; it does NOT false-positive on intentional per-platform lines.
**Recommended model**: Strong reasoning tier, high effort (session: Opus 4.8, high). Rationale: the structural-vs-byte comparison design is the crux - a naive diff produces false positives on every legitimate platform-specific line (comparison Section 9 risk note); re-confirm at implementation time and consider upshifting effort if the fixture tests reveal edge cases.

### Sub-tasks

#### 2.1 -- Design the parity contract (what "in lockstep" means structurally)

**Objective**: Define, in concrete terms, what the guard compares, so it catches real drift without flagging intentional per-platform differences.

**Prompt**:
> Read `templates/ai-instructions/base-claude.md`, `base-codex.md`, `base-cursor.md`, `base-gemini.md`, and `base-opencode.md` in the Nexus-Hub repo, plus the AGENTS.md section that defines the "edit all five in lockstep ... changes must be platform-agnostic" rule. Produce a short written parity contract (in the plan's working notes, not a committed file yet) specifying exactly what MUST stay identical across the five (e.g., the set of section headings, the `{{SKILL_INDEX}}` / other placeholder tokens, the ordered list of behavioral rules) and what is ALLOWED to differ (platform names, per-platform install paths, tool-name nouns). The guard in 2.2 enforces the "MUST stay identical" set as structure, never raw bytes. Base the contract on what the five files actually share today - do not invent requirements.

---

#### 2.2 -- Implement the parity-governance guard

**Objective**: Implement the structural parity check as a repo-internal guard.

**Prompt**:
> Create `scripts/check_base_template_parity.py` in the Nexus-Hub repo, modeled on the existing repo-internal `scripts/check_version_sync.py` guard (same invocation style, same exit-code contract: 0 = pass, non-zero = fail with a clear diff to stderr). It MUST enforce the structural parity contract from sub-task 2.1 across the five `templates/ai-instructions/base-*.md` files: compare the shared structure (section-heading set, placeholder tokens, ordered behavioral-rule set) and report any file that diverges, while tolerating allowed per-platform differences (platform names, install paths, tool nouns). Include type annotations and a module docstring per the Nexus-Hub Python conventions. This is a repo-internal guard like `check_version_sync.py`, NOT a distributed artifact - do NOT add installer copy steps in installer.sh/installer.ps1. Wire it into `make validate` (or add a `make check-parity` target and call it from the validate target). Emit informational (not crashing) output when a file is missing.

---

#### 2.3 -- Testing and Stabilization

**Objective**: Prove the guard catches drift and tolerates intentional differences. Iterate until stable.

**Prompt**:
> Add a pytest module (follow the pattern in `catalog/hooks/tests/`) that: (a) asserts `check_base_template_parity.py` PASSES on the current five in-sync `base-*.md` files; (b) constructs a temporary fixture where one base file is missing a shared section heading and asserts the guard FAILS with a non-zero exit and a clear message; (c) constructs a fixture differing ONLY in an allowed per-platform line (e.g., a platform name or install path) and asserts the guard still PASSES (no false positive). Run `make test`, `make validate`, and `make lint`; fix failures and iterate until all pass. Then run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] `scripts/check_base_template_parity.py` exists with docstring + type annotations
- [x] Guard wired into `make validate` (directly or via a make target it calls)
- [x] Guard passes on the current in-sync templates; fails on a desynced fixture; no false positive on an allowed-difference fixture
- [x] No installer copy steps added (repo-internal guard, by design)
- [x] `make test`, `make validate`, `make lint` all pass (validate green incl. the new guard; the 9 parity tests pass; 4 pre-existing Windows-bash test failures are unrelated to this phase and pass on CI -- see WN-v36-1)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 3

---

## Phase 3: Workflow-phase hook recipe (N1a)

**Goal**: Give Nexus-Hub finer-grained workflow-phase automation guidance and example hook configs *within the existing 4-event Claude hook model* (SessionStart / PreToolUse / PostToolUse / Stop) - without inventing new event types the harness does not support.
**Prerequisites**: None (independent), but best sequenced after Phase 2 so the validation muscle is warm.
**Stability Gate**: Any new/edited hook scripts pass `make test`; example hook configs are valid against `catalog/hooks/settings.json`'s supported events; the hooks-authoring guidance honestly documents the 4-event constraint and does not promise spec-kit-style per-command `before_/after_` event types.
**Recommended model**: Strong reasoning tier, high effort (session: Opus 4.8, high). Rationale: changing hook logic / `settings.json` is an explicit ask-first area in AGENTS.md; correctness and not-overpromising matter. Re-confirm at implementation time.

### Sub-tasks

#### 3.1 -- Document workflow-phase automation within the 4-event model

**Objective**: Translate spec-kit's per-command lifecycle-hook intent into honest recipes on Nexus-Hub's fixed event surface.

**Prompt**:
> In the Nexus-Hub repo, locate the hooks-authoring guidance (the hook conventions in AGENTS.md "Adding or Modifying a Hook" and any hooks-related skill/style-guide). Add a "workflow-phase automation" recipe subsection that explains how to approximate spec-kit's per-command `before_/after_` hooks using Nexus-Hub's supported events ONLY: `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`. Show how PreToolUse/PostToolUse matchers keyed on the relevant tool calls (and the Stop event) can fire automation at plan/implement/spec phase boundaries. Be explicit that Nexus-Hub does NOT add new harness event types - this is a usage pattern, not a new runtime. Cross-reference candidate N1a in docs/v3/v3.6/comparisons/v3.6.0-comparison-spec-kit.md and the comparison Section 9 "lifecycle-hook scope creep" risk note (do not import `.specify/extensions.yml`-style per-command hook registries).

---

#### 3.2 -- Ship an example workflow-phase hook config (optional, additive)

**Objective**: Provide a concrete, registered example so the recipe is runnable, not just descriptive.

**Prompt**:
> If sub-task 3.1's recipe benefits from a concrete example, add ONE example hook to `catalog/hooks/` plus its registration in `catalog/hooks/settings.json`, demonstrating a workflow-phase automation (e.g., a PostToolUse matcher that emits a phase-boundary marker, or a Stop hook that reminds about post-phase docs). Follow the bash safety rules (`#!/usr/bin/env bash`, `set -euo pipefail`, errors to stderr) or the Python hook conventions (module docstring, type annotations). Because this changes `catalog/hooks/settings.json` (an ask-first area), keep it minimal and clearly opt-in. Write a pytest for the new hook following the pattern in `catalog/hooks/tests/test_format_bash_description.py`. If a concrete example adds no real value over the recipe prose, skip this sub-task and note that decision - documentation-only is an acceptable outcome for N1a.

---

#### 3.3 -- Testing and Stabilization

**Objective**: Verify hooks and registration. Iterate until stable.

**Prompt**:
> Run `make test` (the pytest hook suite), `make validate`, and `make lint`. Confirm: any new hook script passes its test; `catalog/hooks/settings.json` remains valid and only references supported events (SessionStart / PreToolUse / PostToolUse / Stop); the hooks-authoring guidance does not claim unsupported event types exist. Fix failures and iterate until all pass. Then run `/generate-session-history` to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] Workflow-phase automation recipe documented honestly within the 4-event model (concise pointer in AGENTS.md "Adding or Modifying a Hook" + full recipe in `guides/CLAUDE_CODE_SETTINGS_REFERENCE.md`; framed on the four phase-relevant events SessionStart / PreToolUse / PostToolUse / Stop without asserting they are the only events the harness defines)
- [x] Example hook registered in settings.json and passes `make test` (the example `catalog/hooks/workflow-phase-notice.sh` is registered in the default `catalog/hooks/settings.json` `PostToolUse` `Write|Edit` block per the maintainer's "activate for all installs" decision; advisory-only, disable via `NEXUS_DISABLED_HOOKS` / `NEXUS_HOOK_PROFILE=minimal`; 9-case pytest passes)
- [x] No unsupported event types introduced; no `.specify/extensions.yml`-style registry imported
- [x] `make test`, `make validate`, `make lint` all pass (run via direct equivalents per WN-v33-1: validate chain green incl. base-parity guard + compression eval; `catalog/hooks/tests/` 441 passed + 14 jq-skips; repo-level `tests/` 540 passed; hook 9/9 with jq. Fixed a pre-existing Phase 2 gap -- `check_base_template_parity.py` was missing from `test_installer_smoke.py`'s `DEV_ONLY_SCRIPTS`, failing at HEAD -- see BG-v36-1)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 5 (Phase 4 already complete; N1a now lands, so Phase 5's CHANGELOG can enumerate all five adoptions)

---

## Phase 4: `/skills import` hygiene (N6)

**Goal**: Harden the existing local `/skills import` path with the catalog-hygiene disciplines reverse-engineered from spec-kit's catalog infra: HTTPS-only source validation, an `install_allowed` discovery-only flag, and hash-on-import - WITHOUT adopting any credentialed remote-catalog fetch.
**Prerequisites**: None, but sequenced after Phase 2 to reuse the validation patterns.
**Stability Gate**: The import path rejects non-HTTPS sources, honors a discovery-only flag, and records a SHA-256 of each imported artifact using the existing `manifest.py` hashing; no new outbound call or credential is introduced; tests cover the reject/allow/hash branches.
**Recommended model**: Strong reasoning tier, high effort (session: Opus 4.8, high). Rationale: this is a security-sensitive path; the guardrails must be airtight and must not accidentally introduce the remote-fetch surface the comparison declined. Re-confirm at implementation time.

### Sub-tasks

#### 4.1 -- Locate and scope the import path

**Objective**: Find exactly where skill import happens and confirm the boundary stays local.

**Prompt**:
> In the Nexus-Hub repo, locate the `/skills import` implementation (start from `catalog/commands/skills.md` and trace into any backing skill or script, plus the `nexus-skill-server` / `nexus-skill-scanner` internal MCPs under `extensions/`). Document the current import flow and where an external source (path or URL) enters it. Confirm the scope of this phase is LOCAL hygiene only: we are NOT adding remote credentialed catalog fetch (comparison candidate N5 is declined). Identify the precise insertion points for: (a) HTTPS-only validation, (b) a discovery-only `install_allowed` flag, (c) hash-on-import.

---

#### 4.2 -- Add HTTPS-only validation + discovery-only flag + hash-on-import

**Objective**: Implement the three hygiene disciplines on the import path.

**Prompt**:
> Implement on the `/skills import` path identified in 4.1: (a) **HTTPS-only validation** - reject any non-HTTPS source URL (allow `http://localhost` only, mirroring spec-kit's `catalogs.py` CatalogStackBase rule); (b) an **`install_allowed` discovery-only flag** - a catalog/source entry marked discovery-only can be listed but not installed, surfacing a clear message; (c) **hash-on-import** - record a SHA-256 of each imported artifact, reusing the hashing in `scripts/lib/integrations/manifest.py` (`_hash_path`) rather than writing new hashing. Reinforce, in code comments and any user-facing message, that import still routes through the existing `skill-security-scan` / `nexus-skill-scanner` pre-install gate - this hygiene layer is additive to that gate, not a replacement. Introduce NO new outbound call, dependency, or credential. Follow Nexus-Hub Python/Bash conventions; if a new distributed script is added under `scripts/`, register copy steps in BOTH installer.sh and installer.ps1 (per AGENTS.md) - but prefer extending existing code over adding a new distributed script.

---

#### 4.3 -- Testing and Stabilization

**Objective**: Cover the reject/allow/hash branches. Iterate until stable.

**Prompt**:
> Add tests (pytest, following the repo pattern) covering: a non-HTTPS source is rejected; an `http://localhost` source is allowed; a discovery-only (`install_allowed: false`) entry can be listed but not installed; an imported artifact gets a recorded SHA-256. Assert no new outbound call is introduced (the import path remains local; remote fetch is out of scope). Run `make test`, `make validate`, `make lint`; if a distributed script was added, dry-run both installers into a throwaway directory and confirm it lands under `~/.nexus-hub/scripts/`. Fix failures and iterate until all pass. Then run `/generate-session-history` to document Phase 4.

---

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [x] Import path rejects non-HTTPS sources (allows http://localhost only)
- [x] Discovery-only (`install_allowed: false`) entries listable but not installable
- [x] Hash-on-import recorded via existing manifest hashing (no new hashing code)
- [x] No new outbound call, dependency, or credential introduced; existing scan gate still referenced
- [x] If a distributed script was added: registered in BOTH installers and dry-run-verified
- [x] `make test`, `make validate`, `make lint` all pass (run via direct equivalents per WN-v33-1: validate chain green, 540 passed / 0 failed, `bash -n` + PowerShell AST clean)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 5 (Phase 3 / N1a now complete -- NI-v36-1 resolved; Phase 5's CHANGELOG can enumerate N1a)

---

## Phase 5: Decline-durability and release readiness

**Goal**: Make the comparison's two declines durable (so a future comparison recognizes them as already-adjudicated), log the two deferred items, and bring v3.6.0 to a verifiable, documented, release-ready state.
**Prerequisites**: Phases 1-4 complete (their changes feed the CHANGELOG and the final validation run).
**Stability Gate**: Reverse-engineering matrix has rows for N5 + N1b with policy grounds; known-gaps tracker has entries for N4 + N2b; CHANGELOG `[Unreleased]` enumerates the Phase 1-4 adoptions; a full `make validate && make lint && make test` run is green.
**Recommended model**: Strong reasoning tier, medium effort (session: Opus 4.8, medium). Rationale: documentation + verification synthesis; lower logic-correctness risk than Phases 2-4 but must accurately reflect what shipped. Re-confirm at implementation time.

### Sub-tasks

#### 5.1 -- Record the declines in the reverse-engineering matrix

**Objective**: Add authoritative matrix rows for the two dropped candidates so the policy decision is durable.

**Prompt**:
> Edit `docs/policy/mcp-reverse-engineering-matrix.md` to add a row for each declined candidate from docs/v3/v3.6/comparisons/v3.6.0-comparison-spec-kit.md Section 6.3 / Bucket D:
> 1. **N5 - Spec Kit authentication framework** (GitHub/Azure DevOps PAT for private remote catalogs): classification `drop-outright`; rationale - plaintext credential storage contradicts the secret-handling rules and remote credentialed catalog fetch is N/A for a local-first catalog that ships in the repo.
> 2. **N1b - Spec Kit third-party extension install** (unsandboxed community-catalog code): classification `drop-outright`; rationale - code-distribution-as-service is on the MCP Registry Policy hard-no spectrum; the capability is already met by the skill catalog WITH a pre-install scanner (skill-security-scan + nexus-skill-scanner) that spec-kit lacks, so adopting spec-kit's model would be a trust regression.
> Follow the matrix's existing row format and the Reverse-Engineering Attribution Rule (generic descriptive naming in the artifact; upstream evidence in the Rationale column). Cross-reference the comparison report.

---

#### 5.2 -- Log the deferred items in the known-gaps tracker

**Objective**: Capture N4 and N2b so the next plan can pick them up if priorities change.

**Prompt**:
> Using the known-gaps-tracker convention, create or update the v3.6.0 known-gaps file (e.g., `docs/v3/v3.6/known-gaps.md`, matching the format of existing `docs/v*/known-gaps.md` files) with two deferred items from docs/v3/v3.6/comparisons/v3.6.0-comparison-spec-kit.md Bucket C: (1) **N4 self-upgrade CLI** - deferred, low ROI (the installer re-run already covers in-place upgrade); (2) **N2b portable YAML workflow engine** - deferred, policy-disfavored as a runtime (the harness's Dynamic Workflows cover Claude Code; revisit only if cross-agent orchestration becomes a stated goal). Note each item's source candidate ID and the condition under which it would be reconsidered.

---

#### 5.3 -- CHANGELOG and final verification

**Objective**: Document what shipped and prove the catalog is green end to end.

**Prompt**:
> Add a `## [Unreleased]` block (or extend the existing one) in `CHANGELOG.md` enumerating the v3.6.0 Spec Kit delta adoptions: N2a (workflow gate/resume/continue-on-error vocabulary in loop-engineering + agent-orchestration-primitives), N3b (template composition strategies in agent-presets + theme-tokens), N3a (base-*.md parity-governance guard), N1a (workflow-phase hook recipe within the 4-event model), N6 (/skills import hygiene: HTTPS-only + discovery-only flag + hash-on-import). Add a short "Reverse-engineer-first declines" note referencing the N5 + N1b matrix rows. Keep CHANGELOG entries ASCII-only (hyphens, straight quotes, `...`) per the project rule. Then run the full gate: `make validate && make lint && make test`. Confirm all green, including the new parity-governance guard from Phase 2 and the import-hygiene tests from Phase 4. Fix any failure and re-run until clean. Then run `/generate-session-history` to document Phase 5 and the v3.6.0 adoption as a whole.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none - no constitution file; no violations) | | |

---

### Phase 5 Exit Checklist

- [x] All sub-tasks completed
- [x] Matrix rows added for N5 + N1b with policy grounds and upstream attribution (new "Declined in v3.6.0 (Drop-Outright under the MCP Registry Policy)" section in `docs/policy/mcp-reverse-engineering-matrix.md`)
- [x] Known-gaps entries added for deferred N4 + N2b with reconsideration conditions (DF-v36-1, DF-v36-2 in `docs/v3/v3.6/known-gaps.md`; summary DF 0->2, total open 3->5)
- [x] CHANGELOG `[Unreleased]` enumerates all five adoptions + the declines note (ASCII-only; N3a/N1a/N6 under Added, N2a/N3b under Changed, declines + deferrals under Notes; unicode-safety confirmed my block introduced 0 non-ASCII punctuation)
- [x] Full `make validate && make lint && make test` run is green (run via direct equivalents per WN-v33-1: full validate chain green incl. base-parity guard + compression gate at CCR 100%; `tests/validators` 199 passed incl. the v3.6.0 guards 51/51 (base-parity + import-skills); `catalog/hooks/tests/` 441 passed + 14 jq-skips. The bash-invoking suites (`tests/installer`, `tests/integrations` parity, one `session_query` test) HANG on this space-containing checkout (WN-v36-1, refined this phase) and so cannot run here; they pass on CI / space-free checkouts, and Phase 5 changed no code so no regression is possible. `make lint`: ShellCheck not on PATH and no shell script changed this phase -- docs-only)
- [x] No new outbound call, credential, or third-party data processor introduced anywhere in v3.6.0 (Phase 5 is docs-only: matrix + known-gaps + CHANGELOG; the prior phases were skill-native / re-engineered-to-local by design)
- [x] Session history generated for this phase
- [x] v3.6.0 ready for release readiness / `/update release`
