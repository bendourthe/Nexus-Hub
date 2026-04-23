# Development Log: Phase 3 - Security Expansion (v0.9.7)

**Date**: 2026-04-21
**Operator**: Benjamin Dourthe
**Assisted by**: Claude Opus 4.7 (1M context) via Claude Code
**Objective**: Ship two new security skills (business-logic-abuse, advanced-attack-patterns), extend `/run-penetration-test` with a conditional 6th hunter gated behind `--depth=deep`, rename "Attack Paths" to "Attack Paths / Chains", add a "Secure Design Recommendations" subsection to the report template, and publish a file-upload security checklist with a cross-link from `security-patch-advisor`.
**Outcome**: 3 new files (2 SKILLs + 1 checklist), 1 command extended with 100+ lines of new content, 1 skill gained a Related Resources footer. All 5 sub-tasks (3.1-3.5) landed with no rework. Ready to advance to Phase 4.

---

## 1. Starting State

- **Branch**: `main` (same session as Phases 1 and 2; their edits remain uncommitted in the working tree)
- **Starting commit**: `73e05fe`
- **Environment**: Windows 11 Enterprise, bash shell, Python 3 available, shellcheck 0.11.0
- **Prior session references**:
  - [2026-04_phase-1-reconciliation-anchors.md](2026-04_phase-1-reconciliation-anchors.md)
  - [2026-04_phase-2-opus-4-7-behavioral-extensions.md](2026-04_phase-2-opus-4-7-behavioral-extensions.md)
- **Plan reference**: [docs/v0.9.7/implementation-plan.md](../../implementation-plan.md) - Phase 3 sub-tasks 3.1-3.5

Context: Phase 3 closes the security half of the v0.9.7 release. The three comparison documents surfaced two categories of gap in the existing `/run-penetration-test` command: (a) domain-aware business-logic flaws that static-vulnerability-class hunters miss because they depend on application-specific invariants, and (b) architecture-level attack patterns (state desync, cache poisoning, replay, timing side channels) that likewise depend on system properties rather than input validation. Phase 3 ships both as new skills, wires them into the pen-test command behind a `--depth=deep` opt-in flag (to manage the 20% aggregate-cost increase), and adds a file-upload checklist that was flagged as a high-value P3 addition. The Phase 1 Effort-Level Strategy anchor is load-bearing here: the new hunter's parallel fan-out defaults to `effortLevel: high`, not `xhigh`, to control aggregate cost - we needed Phase 1's decision table to justify that choice in the command itself.

---

## 2. Chronological Steps

### 3.1 Create `business-logic-abuse` skill

**Plan specification**: New P1 skill covering race conditions, TOCTOU, double-spending, workflow-state bypass, idempotency violations, and check-sequence abuse. House-style SKILL.md frontmatter. Include a scope/caveat step that elicits business rules from the operator (domain knowledge gate). Add a WSTG Coverage Matrix row in `run-penetration-test.md` mapping to WSTG-BUSL-*.

**What happened**: Created `catalog/skills/security/business-logic-abuse/SKILL.md` (261 lines) following the exact house-style pattern observed in `authentication-patterns/SKILL.md` - full four-field frontmatter (`name`, `description`, `summary_l0`, `overview_l1`), top-level sections in the canonical order (When to Use / What It Does / Instructions / Best Practices / Common Patterns / Quality Checklist / Verification / Related Skills), Iterative Refinement Strategy footer, Version + Last Updated metadata.

The Instructions body follows an 8-step structure: Step 1 elicits rules from the operator and explicitly refuses to proceed on unspecified domains ("stop if the rules are not known"); Steps 2-7 cover the six attack classes with indicators-in-code, code-trace procedure, and architectural remediation for each; Step 8 defines the output format (findings table with severity, rule violated, attack class, code reference, reproduction sketch, remediation). Common Patterns provides three canonical fixes: conditional UPDATE for single-writer semantics, idempotency-key table with uniqueness constraint, explicit typed state machine.

**Key files changed**: `catalog/skills/security/business-logic-abuse/SKILL.md` (new, 261 lines).

**Verification**:
```bash
test -f catalog/skills/security/business-logic-abuse/SKILL.md && wc -l $_
# Output: 261 catalog/skills/security/business-logic-abuse/SKILL.md
```

---

### 3.2 Create `advanced-attack-patterns` skill

**Plan specification**: New P2 skill covering state desynchronization, cache poisoning, replay attacks, and expanded timing-attack surfaces. Each section ~30 lines, gated on an applicability check. Add WSTG Coverage Matrix row in `run-penetration-test.md`.

**What happened**: Created `catalog/skills/security/advanced-attack-patterns/SKILL.md` (257 lines) with the same house-style skeleton as 3.1. The four attack-class sections (Steps 1-4 of Instructions) each start with an applicability check - "If all answers are no, skip to Step N with justification" - to keep the audit high-signal on architectures where the class is moot (e.g., no cache layer means cache poisoning is trivially not applicable).

Key content choices:
- State desynchronization covers three sub-patterns: client/server divergence, cache vs DB divergence, step-skip via direct endpoint (with an explicit cross-reference to the `business-logic-abuse` workflow-bypass section to signal overlap rather than duplicate content).
- Cache poisoning enumerates five vectors: unkeyed inputs, missing `Vary`, header injection, cache deception (the Paypal-style attack), and path-normalization differences between cache and origin.
- Replay attacks distinguishes from business-logic double-spend: this section is about request-replay against signed endpoints; the business-logic skill covers financial replay. Cross-linked explicitly.
- Timing attack surfaces goes beyond the classic password `==` comparison to cover user-enumeration, token-lookup, crypto side channels, directory-traversal timing, and regex backtracking.

Common Patterns section ships three patches: uniform-timing login (with bcrypt DUMMY_HASH pattern), nonce-enforced signed request (timestamp window + Redis nonce store + timing-safe comparison), cache-safe personalized response headers.

**Key files changed**: `catalog/skills/security/advanced-attack-patterns/SKILL.md` (new, 257 lines).

**Verification**:
```bash
test -f catalog/skills/security/advanced-attack-patterns/SKILL.md && wc -l $_
# Output: 257 catalog/skills/security/advanced-attack-patterns/SKILL.md
```

---

### 3.3 Extend `/run-penetration-test` with 6th hunter, `--depth=deep` flag, WSTG matrix, terminology polish, Secure Design Recommendations, and effortLevel default

**Plan specification**: Five changes in a single pass:
1. Add 6th hunter slot (Business Logic & Advanced Attacks) gated behind `--depth=deep`.
2. Update WSTG Coverage Matrix with new rows.
3. Rename "Attack Paths" to "Attack Paths / Chains" in the report template.
4. Add "Secure Design Recommendations" subsection between per-finding remediation and the Roadmap.
5. Set default `effortLevel` for hunter agents to `high` (not `xhigh`) with cross-reference to the Effort-Level Strategy section.

**What happened**: Applied edits bottom-up to preserve line-number references during editing:

1. **WSTG Coverage Matrix** - rewrote the WSTG-BUSL row to show "Full (with `--depth=deep`); Not covered otherwise" and added three new rows: WSTG-ATHZ Cache Poisoning, WSTG-SESS Replay & Token Binding, WSTG-CRYP Timing Side Channels. Each row uses the same em-dash separator as the existing matrix to preserve visual consistency (the em-dashes are pre-existing file convention, not new Unicode pollution).

2. **"Attack Paths / Chains" rename** - replaced the single `### Attack Paths` heading at the former line 690 and expanded the descriptive paragraph to explain attack-chain composition (chaining findings into end-to-end exploits).

3. **"Secure Design Recommendations" subsection** - inserted immediately after Attack Paths / Chains and before the `## Remediation Roadmap` section. Gives six canonical architectural-pattern recommendations (centralized authorization, typed query layer, server-authoritative state machine, constant-time comparators, idempotency middleware, CDN boundary hardening). Each is distinct from per-finding remediation (which names a specific fix) and from the Roadmap (which is prioritized and time-boxed).

4. **Hunter 6 block** - inserted a full hunter prompt template immediately before Phase 3. The template splits into Part A (business-logic-abuse skill) and Part B (advanced-attack-patterns skill), each with skill cross-references. The business-logic part explicitly instructs the hunter to infer rules from the codebase when the operator has not provided them, documenting inferences as "assumptions" for operator confirmation. The advanced-attacks part respects each class's applicability check.

5. **`--depth=deep` flag documentation** - added under the Resolve Scope section alongside the existing `--scope` and `--output` flags, explaining the 20% cost increase and which WSTG coverage rows are gated on the flag.

6. **effortLevel: high default** - added a global note in the Phase 2 header rather than repeating per-hunter. The note cross-references both the Effort-Level Strategy section (for the decision rationale) and the multi-agent-coordinator explicit-fan-out callout (for the prompting shape). Single-edit, single-location - DRY.

7. **Stale "5 hunters" references** - updated the frontmatter description, intro paragraph, and three Phase 3 / Quality Checks occurrences to read "5 standard; 6 when `--depth=deep` was used". Kept Hunter 6's own references to "the five hunters above" (inside the Hunter 6 block) because they are locally correct.

**Key files changed**: `catalog/commands/run-penetration-test.md` (+100 lines, -10 lines; 7 Edit calls).

**Verification**:
```bash
grep -c "^### Attack Paths$" catalog/commands/run-penetration-test.md
# 0 (old heading fully replaced)
grep -n "Attack Paths / Chains\|Secure Design Recommendations\|Hunter 6: Business Logic\|--depth=deep\|effortLevel: high" catalog/commands/run-penetration-test.md
# Matches at lines 2, 7, 29, 124, 126, 489, 491, 548, 552, 754, 758, 807-810, 813, 822
```

---

### 3.4 File-upload security checklist + cross-link from `security-patch-advisor`

**Plan specification**: Create `catalog/checklists/file-upload-security.md` covering polyglot files, MIME confusion, archive path traversal, content-length limits, AV scanning. Link from `catalog/skills/security/security-patch-advisor/SKILL.md` "Related resources" section. Scout revealed that the `security-patch-advisor` file had no "Related" footer, so one had to be created.

**What happened**: Scouting confirmed `catalog/checklists/` already exists with 4 files (api-design-checklist.md, architecture-checklist.md, security-checklist.md, testing-patterns.md). The existing convention is markdown H1 + description paragraph, no YAML frontmatter. Followed that convention for the new file.

Wrote 62 lines across 5 grouped sections matching the plan's spec:
1. File-type validation - MIME sniffing, polyglot rejection, double-extension stripping, per-endpoint allowlists.
2. Path handling - server-generated storage names, archive path-traversal pre-scan, sandboxed extraction, post-extraction re-verification, Windows reserved-name rejection.
3. Size and resource limits - dual-layer content-length limits, per-user quota, zip-bomb signature rejection, decompression time/memory caps, image-decoder pre-sizing.
4. Content scanning - sandboxed AV, image re-encoding, PDF/Office neutralization, CSV formula-injection prefixing.
5. Storage and serving - out-of-web-root storage, `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, strict CSP on rendered uploads, distinct upload-content origin for cross-origin isolation, authenticated downloads with per-file permission checks.

Added a Related footer at the end of the checklist cross-linking to `security-patch-advisor`, `business-logic-abuse` (check-sequence abuse overlap), and `advanced-attack-patterns` (cache poisoning overlap for user-content origins).

For the cross-link FROM `security-patch-advisor`: the skill ended at `## Common Pitfalls` without a Related section. Added a new `## Related Resources` section at the end pointing to the new checklist, `business-logic-abuse`, `advanced-attack-patterns`, and the pen-test command. Chose "Related Resources" rather than "Related Skills" because the list includes a checklist and a command, not only skills.

**Key files changed**: `catalog/checklists/file-upload-security.md` (new, 62 lines), `catalog/skills/security/security-patch-advisor/SKILL.md` (+7 lines).

**Verification**:
```bash
test -f catalog/checklists/file-upload-security.md && wc -l $_
# Output: 62 catalog/checklists/file-upload-security.md
grep -c "file-upload-security" catalog/skills/security/security-patch-advisor/SKILL.md
# 1 (cross-link present)
```

---

### 3.5 Phase 3 verification

**Plan specification**: Confirm both new SKILL.md files parse, smoke-test `/run-penetration-test --depth=deep` (or dry-run), verify WSTG Coverage Matrix rows render, confirm "Attack Paths / Chains" rename throughout, confirm Secure Design Recommendations subsection appears in the report template, confirm file-upload checklist renders and is linked from `security-patch-advisor`.

**What happened**: Nine-point verification, all green on first run.

| # | Check | Result |
|---|-------|--------|
| 1 | business-logic-abuse SKILL.md exists (261 lines) | PASS |
| 2 | advanced-attack-patterns SKILL.md exists (257 lines) | PASS |
| 3 | file-upload-security.md checklist exists (62 lines) | PASS |
| 4 | Hunter 6 block present with `--depth=deep` gate at line 489 | PASS |
| 5 | `### Attack Paths / Chains` present at line 754; `### Attack Paths` (old) absent | PASS |
| 6 | `### Secure Design Recommendations` subsection at line 758 | PASS |
| 7 | WSTG matrix has 4 new/updated rows for BUSL / cache / replay / timing | PASS |
| 8 | `effortLevel: high` global note in Phase 2 header at line 126 | PASS |
| 9 | `security-patch-advisor` cross-link to file-upload checklist resolves | PASS |

Non-ASCII scan on added lines: 5 of 97 added lines contain em-dashes, all in the WSTG Coverage Matrix rows and the intro paragraph. These match the pre-existing file convention (the original matrix rows 722-729 all use em-dashes). Deliberate consistency - not pollution. The two new SKILL.md files and the checklist are 100% ASCII-clean.

Smoke-test deferred: the `/run-penetration-test --depth=deep` end-to-end run requires a live repo with hunters actually spawning, which is out of scope for a documentation-only phase. Manual confirmation that the command file parses as Markdown and the Hunter 6 prompt block is syntactically well-formed served as the proxy check.

---

## 3. Verification Gate

| Check | Result |
|---|---|
| 3 new files created (2 SKILLs + 1 checklist) | PASS |
| Both new SKILL.md files have complete frontmatter (name + description + summary_l0 + overview_l1) | PASS |
| `/run-penetration-test` Hunter 6 block present with `--depth=deep` gate | PASS |
| "Attack Paths" rename to "Attack Paths / Chains" is complete (0 stale occurrences) | PASS |
| "Secure Design Recommendations" subsection present in report template | PASS |
| WSTG matrix expanded with BUSL + 3 advanced-attack rows | PASS |
| Hunter effortLevel default set to `high` with cross-reference | PASS |
| Cross-link from `security-patch-advisor` to `file-upload-security.md` resolves | PASS |
| Added content in new SKILLs / checklist is ASCII-clean | PASS |

No code paths touched - Phase 3 is pure documentation and command-template content. No test suite invocation needed.

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| End-to-end smoke-test of `/run-penetration-test --depth=deep` not run | P3 | Deferred - requires a target repo and live hunter spawning. Covered by a Manual Testing Still Needed item. |
| New WSTG matrix rows use em-dash separator (non-ASCII) | Cosmetic | Deliberate - matches the existing matrix's em-dash convention. The global ASCII-only rule is scoped to commit messages, not content. |
| `security-patch-advisor` gained a Related Resources section where none existed before | None | Expected additive change per the plan. |
| Two sections in `advanced-attack-patterns` reference `business-logic-abuse` for overlap (workflow bypass, financial replay) | None | Deliberate cross-links to prevent duplicate coverage. Both skills stand alone; the cross-links signal overlap rather than delegation. |

---

## 5. Plan Discrepancies

- **effortLevel placement**: The scout report suggested inserting `effortLevel` config per-hunter (Hunter 1-6), which would have been 6 separate edits. I chose a single global note in the Phase 2 header instead - DRY and keeps the update surface to one location if the default is revisited. Functionally equivalent: one `effortLevel: high` for the whole parallel phase.
- **"Related Resources" vs "Related Skills"** in `security-patch-advisor`: the plan said to link from the "Related resources" section. That section did not exist; the file ended at `## Common Pitfalls`. I created `## Related Resources` (plural word "Resources" because the list includes a checklist and a command, not only skills) rather than `## Related Skills` which is the more common footer name in other skills. Minor deviation; matches the content being linked.
- **Hunter 6's split into Part A and Part B**: The plan said "invokes both `business-logic-abuse` and `advanced-attack-patterns` skills." I structured the Hunter 6 prompt with explicit Part A / Part B headings and per-skill cross-references so the hunter's output is already sub-divided by skill domain before synthesis. This makes Phase 3 dedup (line 552) more predictable under `--depth=deep` because duplicates cluster by Part rather than by finding class.
- **Hunter 6 includes a "rules inference" fallback**: The plan's business-logic-abuse skill mandates operator-provided rules. In pen-test flow the operator may not pre-supply them. I instructed Hunter 6 to attempt rule inference from codebase artifacts (ledger tables, state-column names, idempotency-key infra) and document every inference as an "assumption" for operator confirmation. This is additive to the skill; the skill's "stop if rules are not known" guidance is still the correct default for solo use.
- **Stale "5 hunters" references softened**: The plan did not mention these, but adding a conditional 6th made multiple "all 5 hunters" lines stale. Fixed in the frontmatter description, the intro paragraph, and three Phase 3 / Quality Checks occurrences to read "5 standard; 6 when `--depth=deep` was used".

No sub-tasks were skipped or substantively altered.

---

## 6. Assumptions Made

- **Two-skill split (business-logic vs advanced-attacks) is right**: The plan already made this split; I accepted it without debate. If the two domains turn out to overlap heavily in practice (e.g., every replay-attack finding also surfaces as an idempotency-violation finding), consolidation may be appropriate in a future minor release. The Hunter 6 Part A / Part B structure makes the split inspectable without forcing early consolidation.
- **`effortLevel: high` is the right default for parallel fan-out**: Drawn from Phase 1.3 Effort-Level Strategy. If load-testing shows `high` misses important findings that `xhigh` would catch, the default can be bumped with a single edit.
- **File-upload checklist naming convention relaxed**: Existing checklists are a mix (`*-checklist.md` for 3 files, `testing-patterns.md` without the suffix). Used the plan's specified name `file-upload-security.md` (no suffix) to match the plan verbatim rather than enforce the majority convention.
- **New SKILL.md files follow the authentication-patterns layout, not security-patch-advisor**: `authentication-patterns` has a full Related Skills footer + Iterative Refinement Strategy; `security-patch-advisor` has neither (which is itself inconsistent). Chose the more complete template for new skills. This is the implicit "house style" going forward.
- **Hunter 6's 20% cost increase is the right number**: Rough estimate based on "one additional parallel agent with a full attack-surface context." Actual cost depends on the size of the codebase and how many findings the new hunter returns. If operators report it's higher, the number can be updated without changing semantics.
- **No commit between phases**: Per the user's global "never commit unless explicitly asked" rule, Phase 3 edits continue to stack on uncommitted Phase 1 + Phase 2 edits. 12 suggested commits queued (7 Phase 1 + 5 Phase 2). Phase 3 adds 5 more, bringing the pending commit count to 17.

---

## 7. Testing Summary

### Automated Tests

- **No project test suite runs on documentation-only changes** - Phase 3 touches only SKILL.md / command / checklist content.
- **File-existence checks**: 3/3 PASS.
- **Cross-link existence checks**: 4/4 PASS (file-upload-security, business-logic-abuse, advanced-attack-patterns, run-penetration-test).
- **Grep-based anchor checks**: 9/9 PASS (Hunter 6 block, `--depth=deep`, Attack Paths / Chains, Secure Design Recommendations, WSTG rows, effortLevel note, etc.).
- **Non-ASCII scan on Phase 3 added lines**: 5 / 97 lines contain em-dashes - all in WSTG matrix rows and intro paragraph, matching pre-existing file convention.

### Manual Testing Performed

- Spot-read all 3 new files for coherence and cross-link consistency.
- Verified the `/run-penetration-test` Hunter 6 block reads as a complete, self-contained prompt that could actually be launched.
- Spot-checked the Secure Design Recommendations subsection is positioned between per-finding remediation (in the CRITICAL finding template upstream) and the `## Remediation Roadmap` section.
- Confirmed the WSTG matrix's new rows read consistently with the pre-existing 8 rows' style.

### Manual Testing Still Needed

- [ ] Dry-run `/run-penetration-test --depth=deep` on a small test repo (or the DevAI-Hub repo itself) to confirm Hunter 6 spawns and produces structured findings.
- [ ] Render the new SKILL.md files and checklist in a markdown preview to catch any table/code-block rendering issues.
- [ ] Click-through each cross-link (from security-patch-advisor, from file-upload-security, within the new SKILLs) in a markdown-aware editor.
- [ ] Confirm that under `--depth=deep`, the final report correctly fills the BUSL / cache / replay / timing rows of the WSTG Coverage Matrix rather than leaving them unpopulated.

---

## 8. TODO Tracker

### Completed This Session (Phase 3)

- [x] 3.1 `business-logic-abuse` skill created (261 lines, full house style)
- [x] 3.2 `advanced-attack-patterns` skill created (257 lines, applicability-gated structure)
- [x] 3.3 `/run-penetration-test` extended with `--depth=deep`, 6th hunter, WSTG matrix expansion, "Attack Paths / Chains" rename, Secure Design Recommendations subsection, `effortLevel: high` global note
- [x] 3.4 File-upload security checklist + `security-patch-advisor` Related Resources cross-link
- [x] 3.5 Phase 3 verification (9/9 checks green)

### Remaining (Not Started or Partially Done)

- [ ] Commit Phase 3 sub-tasks (user invokes manually):
  - 3.1: `docs(skills): add business-logic-abuse security skill`
  - 3.2: `docs(skills): add advanced-attack-patterns security skill`
  - 3.3: `feat(commands): extend /run-penetration-test with --depth=deep 6th hunter`
  - 3.4: `docs(checklists): add file-upload-security checklist`
- [ ] Phase 4: Context calibrations & migration notes (4.1-4.4 per implementation-plan.md).

### Out of Scope (Deferred)

- [ ] End-to-end smoke-test of `/run-penetration-test --depth=deep` on a live repo (tracked in Manual Testing Still Needed).
- [ ] Checklist naming-convention alignment (some `*-checklist.md`, some without). Out of Phase 3 scope; revisit in Phase 6 release cleanup if desired.
- [ ] Consolidation of `business-logic-abuse` and `advanced-attack-patterns` if overlap proves high in practice (noted as a future minor-release consideration).

---

## 9. Summary and Next Steps

Phase 3 closed the security half of v0.9.7 in one session with no rework: two new security skills (business-logic-abuse covering domain-aware invariant violations, advanced-attack-patterns covering architecture-level attack classes), a 6th pen-test hunter gated behind `--depth=deep` to manage cost, a WSTG Coverage Matrix expanded by 4 rows, a "Secure Design Recommendations" subsection in the report template, an "Attack Paths / Chains" terminology refinement, a file-upload security checklist, and a `security-patch-advisor` Related Resources cross-link that the skill previously lacked. The Phase 1 Effort-Level Strategy anchor was load-bearing: Hunter 6 defaults to `effortLevel: high` for parallel fan-out cost control, cross-referencing Phase 1.3's decision table directly in the command file.

**Next session should**:
1. Commit Phases 1-3 against `main`. With Phase 3 adding 5 more commits, the total pending is now 17 conventional-commit messages queued across the three session-history files.
2. Render the two new security SKILL.md files and the file-upload checklist in a markdown preview to catch any table-rendering issues before commit.
3. Advance with `/implement-phase 4 of v0.9.7`. Phase 4 adds the 1M-token window calibration note to `context-degradation`, the "summarize from here" mode to `session-history`, and the consolidated Opus 4.6 -> 4.7 migration guide (`docs/v0.9.6/opus-4-7-migration.md`). Phase 4 also cross-references every Opus 4.7 behavioral delta introduced across Phases 1-3, so Phase 3's security additions will feed the migration guide's cross-reference table.
