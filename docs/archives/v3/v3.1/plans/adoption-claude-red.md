# Plan -- Adopt Claude-Red offensive methodology (selective, scope-gated)

**Project**: Nexus-Hub
**Version**: v3.1.0
**Slug**: adoption-claude-red
**Plan Type**: Feature / Enhancement
**Created**: 2026-06-04
**Goal**: Adopt a small, re-authored set of Claude-Red's offensive methodology that sharpens Nexus-Hub's existing defensive review surface (AI-attack patterns, pentest reporting, web/auth attack methodology), gated behind a mandatory nexus-skill-scanner allowlist change and an Ask-First category decision.

## Overview

This plan operationalizes [`../comparison-claude-red.md`](../comparison-claude-red.md) at full scope (P0-P3). Claude-Red is 58 offensive-security `SKILL.md` skills (MIT). Every candidate is pure-markdown `skill-native` content with zero data-flow risk, so the gating axis is scope / brand / dual-use, NOT the MCP Registry Policy's network-trust axis. The decisive practical constraint is that Nexus-Hub's own catalog skill-security gate (`nexus-skill-scanner`) is built to flag exactly the payload content these skills carry, so the scanner's producer-catalog allowlist MUST be tuned before any payload-bearing import -- this makes an internal, security-sensitive task a hard prerequisite gate even though it is not itself an adoption "item".

**Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of the source comparison for the ordering rationale.** All adoption candidates are `skill-native`; within that bucket they are ordered by collision risk and dependency: the two low-collision skills ship first (Phase 1), the scanner-allowlist prerequisite gate comes next (Phase 2), the payload-bearing web/auth methodology folds into existing skills after the gate (Phases 3-4), and the new-category decision is an Ask-First gate last (Phase 5). The `drop-outright` / scope-rejected items (the external Tessl CI optimizer, the weaponization group, and the specialist bulk) are excluded -- see the out-of-scope appendix.

All adopted content is re-authored generically per the Reverse-Engineering Attribution Rule (no references to Claude-Red, SnailSploit, or the upstream Sahar Shlichov checklist in the distributed artifacts), carries authorized-engagement preconditions in its Verification section, and gets `summary_l0` / `overview_l1` + a `SKIP:` clause to satisfy the Nexus-Hub MCP server and validator.

This plan is single-source and forward-looking; it intentionally does NOT ingest the v2.4.0 / v3.0.0 general known-gaps backlog.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/v3/v3.1/constitution.md - skipping check. Recommend running /constitution to establish project principles.

This plan aligns with the `AGENTS.md` MCP Registry Policy (all candidates are `skill-native`, zero outbound, zero new processors) and with the "Ask first: creating a new skill category" boundary (Phase 5 is explicitly a maintainer decision gate). The scanner-allowlist change (Phase 2) is treated as security-sensitive and ships with regression tests.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Low-collision skill-native ships | `security/ai-attack-patterns` + `security/pentest-reporting` re-authored and registered |
| 2 | Scanner allowlist prerequisite gate | `nexus-skill-scanner` tuned to allow authorized payloads in `security` skills; planted-malicious fixture still CRITICAL |
| 3 | Web AppSec methodology fold-in | Attacker-perspective enrichment folded into `advanced-attack-patterns` + `business-logic-abuse` |
| 4 | Auth attack methodology fold-in | jwt/oauth attack methodology folded into `authentication-patterns` |
| 5 | Ask-First category decision | Documented maintainer decision memo on an `offensive-security` category |

---

## Phase 1: Low-collision skill-native ships (skill-native)

**Goal**: Ship the two highest-value, lowest-collision offensive-knowledge skills, re-authored to Nexus-Hub's body contract and registered in all three catalog files.
**Prerequisites**: None (these carry minimal scanner collision).
**Stability Gate**: both skills exist with full frontmatter + body contract, are registered in `SKILL_INDEX.md` / `skills.json` / `marketplace.json`, and pass `make validate` + the CI skill-security gate (no HIGH/CRITICAL).

### Sub-tasks

#### 1.1 -- Re-author the AI-attack-patterns skill

- [x] T001 Create catalog/skills/security/ai-attack-patterns/SKILL.md

**Objective**: Adopt offensive AI-security methodology (prompt injection / jailbreaking / RAG poisoning) as a skill that strengthens the defensive scanner's detection rationale.

**Prompt**:
> Create `catalog/skills/security/ai-attack-patterns/SKILL.md` re-authoring the offensive AI-security methodology (prompt injection, jailbreaking, RAG poisoning) GENERICALLY -- do not name Claude-Red or any upstream source. Include the required frontmatter (`name`, pushy `description` with trigger phrases AND a `SKIP:` clause, `summary_l0` <=15 words, `overview_l1` <=150 words) and the mandatory body sections (`When to Use This Skill` with authorized-use guidance, `Instructions`, `Common Rationalizations`, `Verification` with authorized-engagement preconditions, `Related Skills` cross-linking `[[skill-security-scan]]` and the `ai-development` category). Optionally add the structured `mitre_attack` / `atlas_techniques` frontmatter fields with a `references/standards.md`. Frame it as feeding defensive review, not standalone offensive engagement.

---

#### 1.2 -- Re-author the pentest-reporting skill

- [x] T002 Create catalog/skills/security/pentest-reporting/SKILL.md

**Objective**: Adopt professional pentest report-writing methodology to complement `/review pentest` and `final-report`.

**Prompt**:
> Create `catalog/skills/security/pentest-reporting/SKILL.md` re-authoring pentest report-writing methodology (CVSS scoring, evidence capture, executive summary, retest workflow) generically. Full frontmatter + body contract as in T001. Cross-link `[[final-report]]`, `[[incident-postmortem]]`, and the `/review pentest` command. No payloads -- this is report methodology, so scanner collision is near-zero.

---

#### 1.3 -- Register both skills

- [x] T003 Register the two new skills in data/SKILL_INDEX.md, data/skills.json, and data/marketplace.json

**Objective**: Add catalog registry entries per the AGENTS.md new-skill procedure.

**Prompt**:
> Register `security/ai-attack-patterns` and `security/pentest-reporting` in all three registries: add a row to `data/SKILL_INDEX.md`; add a full entry to the `skills` array in `data/skills.json` (name, title, description, long_description, summary_l0, overview_l1, version, author, category=security, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security scores defaulting 100/100/95); increment the security category `skill_count` and `statistics.total_skills` in `data/marketplace.json`. Reconcile the catalog skill-count prose if the project tracks a headline total. Do not edit any other `data/` content by hand.

---

#### 1.4 -- Testing and Stabilization

- [x] T004 Validate Phase 1 via make validate and the CI skill-security gate

**Objective**: Confirm the new skills pass integrity + security gates.

**Prompt**:
> Run `make validate` (JSON catalog integrity + skill frontmatter), `make lint`, and the `nexus-skill-scanner` over `catalog/skills` (the CI gate). Confirm both new skills score below HIGH (the pentest-reporting skill should be LOW; ai-attack-patterns may surface MEDIUM prose matches -- confirm none are HIGH/CRITICAL and that fence-aware prose capping applies). Fix any frontmatter/registry issues and iterate. After passing, run `/generate-session-history` to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: Scanner allowlist prerequisite gate (skill-native enabler)

**Goal**: Tune `nexus-skill-scanner` so authorized red-team payloads inside `security`-category skills do not break the CI gate, WITHOUT weakening detection of genuinely malicious skills.
**Prerequisites**: Phase 1 (establishes the pattern of security skills in the catalog).
**Stability Gate**: payload-bearing fenced content in `security` skills no longer scores HIGH/CRITICAL; the planted-malicious fixture STILL scores CRITICAL; the known-clean fixture still scores LOW; all scanner tests green.

### Sub-tasks

#### 2.1 -- Tune the producer-catalog allowlist

- [x] T005 Tune the producer-catalog allowlist in extensions/nexus-skill-scanner/

**Objective**: Allow authorized-methodology payloads in trusted `security`-category skills while preserving malicious-skill detection.

**Prompt**:
> Update `extensions/nexus-skill-scanner/` so that fenced payload content inside `catalog/skills/security/` skills (authorized red-team methodology) is treated as producer-catalog content and capped below HIGH, REUSING the existing fence-aware / prose-capping mechanism rather than adding a blanket suppression. Be precise: the allowlist must be scoped to the `security` category and to fenced/prose contexts, must NOT relax detection for excessive-agency, exfiltration-to-external-host, or live-malware classes, and must NOT apply to third-party skills scanned via `/skills import`. Document the exact scoping rule and its rationale in the package README.

---

#### 2.2 -- Add allowlist regression tests

- [x] T006 Add allowlist regression tests in extensions/nexus-skill-scanner/ (and tests/validators/)

**Objective**: Prove the allowlist does not create a malicious-skill blind spot.

**Prompt**:
> Add tests asserting: (a) the planted-malicious fixture STILL scores CRITICAL after the allowlist change; (b) the known-clean fixture still scores LOW; (c) a representative authorized-payload `security` skill scores below HIGH; (d) the SAME payload in a non-`security` / third-party skill is NOT allowlisted and still scores per its real class. Wire into `make test` and the CI `tests` job. Run, fix, iterate until green. After passing, run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 3

---

## Phase 3: Web AppSec methodology fold-in (skill-native)

**Goal**: Fold attacker-perspective web-app methodology into the existing defensive skills rather than importing standalone offensive skills.
**Prerequisites**: Phase 2 (scanner allowlist must exist before payload-bearing content lands).
**Stability Gate**: `advanced-attack-patterns` and `business-logic-abuse` carry the new attacker-perspective methodology; `make validate` + scanner gate green; skills within the size norm.

### Sub-tasks

#### 3.1 -- Enrich advanced-attack-patterns

- [x] T007 Fold web AppSec attack methodology into catalog/skills/security/advanced-attack-patterns/SKILL.md

**Objective**: Add concrete attacker-perspective methodology for SSRF, SSTI, XXE, deserialization, request-smuggling, and IDOR.

**Prompt**:
> Enrich `catalog/skills/security/advanced-attack-patterns/SKILL.md` with re-authored, generically-named attacker-perspective methodology for SSRF, SSTI, XXE, deserialization, request-smuggling, and IDOR, framed to strengthen `/review security` and `/review pentest`. If the body would exceed the 500-line norm, push per-vector detail into a `references/` file and link it. Add authorized-use framing to the Verification section. Ensure payloads are fenced so the Phase 2 allowlist applies. Re-register in `data/` only if metadata changed.

---

#### 3.2 -- Enrich business-logic-abuse

- [x] T008 Fold business-logic attack scenarios into catalog/skills/security/business-logic-abuse/SKILL.md

**Objective**: Add concrete attack scenarios (pricing/refund abuse, anti-fraud defeat, workflow bypass) the defensive skill can cite.

**Prompt**:
> Enrich `catalog/skills/security/business-logic-abuse/SKILL.md` with re-authored business-logic attack scenarios (pricing/refund abuse, anti-fraud defeat, workflow-step bypass) from the offensive perspective, generically named, with authorized-use framing. Keep within the size norm. Cross-link `[[advanced-attack-patterns]]`.

---

#### 3.3 -- Testing and Stabilization

- [x] T009 Validate Phase 3 via make validate and the scanner gate

**Objective**: Confirm the enriched skills stay clean and within norms.

**Prompt**:
> Run `make validate`, `make lint`, and the `nexus-skill-scanner` gate. Confirm the enriched skills score below HIGH (the Phase 2 allowlist must be doing its job) and stay within the size norm. Fix and iterate. After passing, run `/generate-session-history` to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 4

---

## Phase 4: Auth attack methodology fold-in (skill-native)

**Goal**: Fold JWT and OAuth attack methodology into the existing authentication skill.
**Prerequisites**: Phase 2 (scanner allowlist).
**Stability Gate**: `authentication-patterns` carries the new attacker-perspective auth methodology; gates green; within size norm.

### Sub-tasks

#### 4.1 -- Enrich authentication-patterns

- [x] T010 Fold JWT/OAuth attack methodology into catalog/skills/security/authentication-patterns/SKILL.md

**Objective**: Add attacker-perspective auth-flow methodology (alg:none, key confusion, secret cracking, kid injection, open redirect, token leakage, PKCE bypass).

**Prompt**:
> Enrich `catalog/skills/security/authentication-patterns/SKILL.md` with re-authored, generically-named JWT and OAuth attack methodology (alg:none, key confusion, secret cracking, kid injection; open redirect, token leakage, PKCE bypass), framed as what the defensive auth design must withstand. Authorized-use framing in Verification. Keep within the size norm; push detail to `references/` if needed. Re-register in `data/` only if metadata changed.

---

#### 4.2 -- Testing and Stabilization

- [x] T011 Validate Phase 4 via make validate and the scanner gate

**Objective**: Confirm the enriched auth skill stays clean.

**Prompt**:
> Run `make validate`, `make lint`, and the scanner gate. Confirm below-HIGH score and size-norm compliance. Fix and iterate. After passing, run `/generate-session-history` to document Phase 4.

---

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 5

---

## Phase 5: Ask-First category decision (gate -- maintainer sign-off)

**Goal**: Produce a decision memo on whether to open an `offensive-security` category for `offensive-cloud` and the specialist groups, and STOP for maintainer sign-off rather than implementing.
**Prerequisites**: Phases 1-4 (demonstrate the fold-in approach so the category decision is informed).
**Stability Gate**: a written decision memo exists with a clear recommendation; no new category is created without explicit maintainer approval.

### Sub-tasks

#### 5.1 -- Author the category decision memo

- [x] T012 Author an offensive-security category decision memo in docs/v3/v3.1/offensive-security-category-decision.md

**Objective**: Give maintainers a crisp Ask-First decision artifact, not an implemented category.

**Prompt**:
> Write `docs/v3/v3.1/offensive-security-category-decision.md`: a short decision memo weighing whether to open an `offensive-security` category for `offensive-cloud` plus the specialist groups (wireless / exploit-dev / fuzzing / IoT / mobile / AD / recon). Cover: brand/positioning impact, maintenance burden (fast-moving CVEs/tooling), scanner-collision load, dual-use governance, and the AGENTS.md "Ask first: creating a new skill category" requirement. Give an explicit recommendation (the comparison recommends DEFER unless maintainers choose to become offensive-capable). End with a clear GO / NO-GO checklist for maintainer sign-off. Do NOT create the category or any specialist skill in this task.

---

#### 5.2 -- Final validation and changelog

- [x] T013 Run full validation and add the CHANGELOG entry

**Objective**: Confirm the whole adoption is green and recorded.

**Prompt**:
> Run `make validate`, `make lint`, `make test`, and the scanner gate across the catalog. Add a CHANGELOG `## [Unreleased]` entry summarizing the adopted defensive-enrichment skills, the scanner-allowlist change, and the deferred category decision. Confirm no `drop-outright` item (Tessl CI optimizer, weaponization group, specialist bulk) was adopted. After passing, run `/generate-session-history` to document Phase 5.

---

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | -- | All Constitution Check items are N/A (no constitution file); no violations to justify. |

---

### Phase 5 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (all catalog gates green; the only failures are 3 pre-existing ENV bash-installer tests on the Windows host, CI-green -- WN-v31cr-6)
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Adoption complete; category decision awaiting maintainer sign-off; CHANGELOG updated

---

## Items explicitly NOT adopted (security / policy reasons)

- **N1 -- Claude-Red CI `tesslio/skill-review-and-optimize` action.** Sends skill source to a third-party optimization service. `drop-outright` under the MCP Registry Policy hard-no list (generation-as-service). Replaced by the LLM-native `skill-description-authoring` skill + `make validate`.
- **N2 -- Detection-evasion / weaponization skills** (`offensive-edr-evasion`, `offensive-shellcode`, `offensive-keylogger-arch`, `offensive-windows-mitigations`, `offensive-windows-boundaries`, `offensive-advanced-redteam`, `offensive-initial-access`). No data-flow risk (pure markdown), so not a Registry-Policy drop, but recommended AGAINST the core catalog on scope / brand / scanner-collision / dual-use grounds. Adopting them is an Ask-First maintainer decision, not part of this plan.
- **N3 -- Bulk import of the wireless / exploit-dev / fuzzing / IoT / mobile / AD / recon specialist groups (40+ skills).** Out-of-domain for software-engineering workflows and a heavy maintenance surface. Deferred to the Phase 5 category decision and a separately-governed offensive bundle if ever pursued; not folded into the core catalog.
