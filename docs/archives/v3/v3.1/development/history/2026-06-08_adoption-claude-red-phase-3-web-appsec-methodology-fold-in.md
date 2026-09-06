# Session History -- v3.1.0 adoption-claude-red Phase 3: Web AppSec methodology fold-in

**Date**: 2026-06-08
**Plan**: [`docs/releases/v3/v3.1/plans/adoption-claude-red.md`](../../plans/adoption-claude-red.md)
**Phase**: 3 of 5 -- web AppSec methodology fold-in
**Branch**: `feat/adoption-claude-red` (continued from Phase 2 tip `4595ee5`)
**Outcome**: complete; all three sub-tasks (T007-T009) closed, all quality gates green.

## Goal

Fold re-authored, generically-named attacker-perspective web-application methodology into the two existing defensive skills (`advanced-attack-patterns`, `business-logic-abuse`) rather than importing standalone offensive skills. Per the plan this is the first payload-bearing fold-in, so it depends on the Phase 2 scanner allowlist that caps fenced `catalog/skills/security/` content below the HIGH/CRITICAL CI gate. All payloads must be fenced (so the allowlist + fence-suppression apply), benign and pointed at reserved placeholders, carry authorized-engagement framing, and stay within the 500-line size norm.

## Pre-implementation analysis (before any edit)

Confirmed the Phase 2 mechanics so the payloads would land below the gate without an iteration loop:

- **Text patterns** (`text_patterns.py`): every match inside a markdown fence is suppressed entirely; prose matches are hard-capped at MEDIUM. So fenced payloads produce no finding at all.
- **Behavioral AST** (`behavioral_ast.py`): parses only `.py` files -- a markdown body (SKILL.md or `references/*.md`) is never AST-scanned, so fenced `pickle.loads` / `os.system` examples cannot trip dynamic-code-execution.
- **Secret analyzer**: the one residual HIGH path on a markdown body; capped to MEDIUM by the Phase 2 allowlist for `catalog/skills/security/` bodies. Phase 3 needs no example secrets, so this did not even come into play.
- **Never-relax classes** (`allowlist.py`: 2/5/12/13/14): keep full severity even in a security body, but they fire on executable scripts (AST/taint) or exfiltration directives -- avoided by fencing and by using `attacker.example` / metadata-IP placeholders instead of live exfil one-liners.
- **Allowlist scope**: `is_trusted_security_skill_body` matches `repo_root` + `.md`/`.markdown` under `catalog/skills/security/`, so the new `references/web-appsec-methodology.md` is covered identically to the SKILL.md.

One structure decision was surfaced to the user in the pre-flight and confirmed: keep `advanced-attack-patterns/SKILL.md` lean with a methodology-level body section and push the deep per-vector payloads into a Tier-3 `references/` file, rather than inlining everything (which would have pushed the body toward the 500-line norm).

## Subtasks completed

1. **T007 -- enrich `advanced-attack-patterns`.** Added "Step 5: Injection and Access-Control Attack Surfaces" (5a SSRF, 5b SSTI, 5c XXE, 5d insecure deserialization, 5e HTTP request smuggling, 5f IDOR/BOLA), each following the skill's applicability-check -> attacker-approach -> indicators -> remediation shape, framed to strengthen `/review security` and `/run-penetration-test --depth=deep`. The existing "Step 5: Output Format" became "Step 6" (existing Steps 1-4 untouched). Created `references/web-appsec-methodology.md` with the deep per-vector payloads, engine-specific probes, filter-bypass catalogs, language-specific deserialization sinks, and an OWASP-WSTG / CWE mapping table. Updated frontmatter (description with a `SKIP:` clause + new trigger phrases, summary_l0, overview_l1), When-to-Use, What-This-Skill-Does (two-family framing), the Output-Format example table (SSRF/IDOR rows), Common-Rationalizations (SSRF/IDOR/SSTI), Verification (authorized-engagement preconditions + per-vector re-test items), Related Skills, and the version footer (1.0.0 -> 1.1.0). Body 366 lines (within norm).
2. **T008 -- enrich `business-logic-abuse`.** Added "Step 8: Attacker Playbooks" with three concrete offensive scenarios (8a pricing/refund abuse, 8b anti-fraud and rate-limit defeat, 8c workflow-step bypass), each ending in the invariant broken + the defensive control; the existing "Step 8: Output Format" became "Step 9". Added the `[[advanced-attack-patterns]]` cross-link required by T008 (it was missing from this skill's Related Skills) plus `[[pentest-reporting]]`; added an Attacker-Playbooks bullet to What-This-Skill-Does; added authorized-use framing to When-to-Use and Verification; added two playbook rationalizations; updated frontmatter (pushy description + trigger phrases, summary_l0, overview_l1) and the version footer (1.0.0 -> 1.1.0). Body 324 lines (within norm).
3. **T009 -- validation.** `make`-absent host, so the gate was emulated directly; all green (see Test results).

## Registry re-registration

Both skills changed metadata, so per the plan ("re-register in `data/` only if metadata changed") their entries were updated by hand:

- `data/skills.json`: description, summary_l0, overview_l1, and the `size` block for both; `long_description` for `advanced-attack-patterns` (its first body paragraph changed; `business-logic-abuse`'s did not).
- `data/SKILL_INDEX.md`: the two summary rows.
- `data/marketplace.json`: deliberately NOT touched -- the catalog still has 250 skills (enrichment, not addition), so `skill_count` / `total_skills` are unchanged.

`size` values were computed with the build script's own metric (`len(content.split('\n'))` / `len(content)` / `len(content.split())`): `advanced-attack-patterns` 366/37022/5148, `business-logic-abuse` 324/27839/3971. `make build-catalog` was intentionally NOT run -- it regenerates all 250 entries and would have surfaced unrelated pre-existing drift (the registry is hand-maintained, not last-generated).

## Key decisions

- **Tier-3 references split for the dense vector family.** SKILL.md carries the methodology (applicability + approach + indicators + remediation per vector) and links to `references/web-appsec-methodology.md` for the fenced payload catalog. Keeps the on-trigger body lean (366 lines) and matches the AGENTS.md bundled-resource convention; the references file is referenced multiple times from SKILL.md, so the orphan audit passes.
- **Fenced payloads + placeholder destinations as the gate-safety discipline.** Every SSRF/SSTI/XXE/deserialization/smuggling/IDOR payload sits in a fence and uses `attacker.example` or a metadata/RFC-1918 placeholder, so fence-suppression keeps them silent and nothing depends on relaxing a never-relax class. This is the discipline the Phase 1 `ai-attack-patterns` skill modeled.
- **Reconciled a pre-existing summary_l0 drift in passing.** `business-logic-abuse`'s SKILL.md summary_l0 ("Find business-logic flaws...") differed from the registry ("Identify business-logic vulnerabilities..."). Since the field was being legitimately re-registered, both surfaces were set to one consistent new value rather than perpetuating the drift -- this is part of the in-scope metadata change, not an out-of-scope cleanup.
- **No business-rule / architectural scope bleed.** SSRF/SSTI/XXE/etc. went into `advanced-attack-patterns`; pricing/refund/anti-fraud playbooks went into `business-logic-abuse`; the two skills cross-link rather than duplicate.

## Test results

- Catalog scanner gate (`scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high`): **exit 0** -- 537 files, critical=0, high=0, medium=13, low=2; no regression.
- Targeted scan of the two enriched skills + `references/web-appsec-methodology.md`: **5/100 (LOW)**, 0 HIGH / 0 CRITICAL / 0 MEDIUM; the single LOW is a pre-existing Step-4 "leak the secret" timing-attack prose line (not new content). Every Step-5 / references payload produced zero findings (fence-suppressed) -- the Phase 2 allowlist + fence-suppression doing their job.
- Scanner package suite: **87 passed** (`python -m pytest -q`) -- no regression from catalog content.
- `make validate` emulated: JSON catalogs valid (250 skills); `validate_skills.py --bundles-only` PASS (`web-appsec-methodology.md` referenced; the only orphan warning is a pre-existing `.pyc` in `workflow/demo-capture`); `validate_no_personal_paths.py`, `validate_unicode_safety.py` (both skills ASCII-clean; warnings are a pre-existing legacy template), `scan_supply_chain_iocs.py` (the metadata-IP / `attacker.example` teaching addresses not flagged), `validate_workflow_security.py`, and `check_version_sync.py` (green; no project-version surface touched -- the skill `**Version**: 1.1.0` footers are per-skill) all exit 0.
- Size norm: 366 / 324 lines, both under the 500-line norm.

## CI/CD edits

- None. The `references/` file is auto-copied by both installers (recursive skill-dir copy; no installer edit, per AGENTS.md row 1). No new script, env var, or dependency. The CI `validate` job already loads `skills.json` and runs the scanner gate over `catalog/skills` (which now includes the references file); the `tests` job runs the scanner package suite. 0 workflows touched.

## Deviations

- None. The plan was followed exactly (T007-T009 as written). The only judgment call -- the Tier-3 references split for T007 -- is explicitly sanctioned by the T007 prompt ("if the body would exceed the 500-line norm, push per-vector detail into a `references/` file") and was user-confirmed in the pre-flight.

## Troubleshooting / environment notes

- `make` and `shellcheck` are unavailable on the Windows dev host (consistent with prior phases' WN-v31cr-2), so `make validate` / `make scan` / `make test` were emulated by invoking the validators and the scanner directly. `make lint` (ShellCheck) is not applicable -- the phase added only Markdown + JSON, no shell surface.
- `validate_skills.py` run in its bare default mode reports 150 description-length "errors" (now including the two enriched skills' pushy descriptions). This is the known non-gate WN-v31cr-1 -- neither `make validate` nor the CI `validate` job runs that mode (they use `--bundles-only` / `--quality`). The pushy descriptions are kept by design.
- The Bash tool's working directory persists between calls; one `cd` into the scanner package dir for pytest was reset back to the repo root afterward.

## Known gaps

See [`docs/releases/v3/v3.1/known-gaps.md`](../../known-gaps.md). 0 new open items this phase, 0 resolved. WN-v31cr-1 was extended to record that the two Phase 3 enriched skills now also carry >250-char pushy descriptions (same non-gate). Carried forward: WN-v31cr-1/-2/-3/-4. Total 4 WN open.

## Next steps

- **Phase 4 -- Auth attack methodology fold-in**: enrich `catalog/skills/security/authentication-patterns/SKILL.md` with re-authored JWT and OAuth attack methodology (alg:none, key confusion, secret cracking, kid injection; open redirect, token leakage, PKCE bypass), framed as what the defensive auth design must withstand, fenced so the Phase 2 allowlist applies, with detail pushed to `references/` if it exceeds the size norm. This is the second payload-bearing fold-in and the last before the Phase 5 Ask-First category decision memo.
