# Development Log: Skills-Craft and Prime Agent Phase 2 - New Skills

**Date**: 2026-08-24
**Operator**: Ben
**Assisted by**: Cursor Grok 4.6
**Objective**: Ship three new registered skills (design-interview, setup-wizard-generator, decision-questionnaire) with trigger evals, three-file plus bundles registration, and cross-links into idea-refine, implementation-plan, and business-analyst.
**Outcome**: Catalog count 321 to 324. Trigger evals green (66 skills with cases, 0 routing failures). Ready for Phase 3.

---

## 1. Starting State

- **Branch**: `feat/v3.20.3-skills-craft-and-prime-agent` (ahead of `backmerge/v3.20.2-release` by Phase 1 commit `3792663a`)
- **Starting tag/commit**: `3792663a` (`feat(skills): add agent-writing discipline and out-of-scope register`)
- **Environment**: Windows 11, PowerShell, Python 3, WSL `bash.exe` at `C:\windows\system32\bash.EXE` (not Git Bash)
- **Prior session reference**: [`2026-08-24_skills-craft-phase-1-agent-writing-and-out-of-scope.md`](2026-08-24_skills-craft-phase-1-agent-writing-and-out-of-scope.md)
- **Plan reference**: [`docs/releases/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md`](../../plans/v3.20.3-skills-craft-and-prime-agent.md)

Context: Phase 1 landed the agent-writing discipline and the out-of-scope register. Phase 2 authors three skill-native capabilities under that discipline, without installer edits (skill trees copy recursively).

---

## 2. Chronological Steps

### 2.1 Grilling primitive + CONTEXT.md domain glossary (A3)

**Branch**: `feat/v3.20.3-skills-craft-and-prime-agent` | **PR**: none | **Merged to**: n/a

**Plan specification**: Create `design-interview` as a reusable one-question-at-a-time interview engine plus a `CONTEXT.md` glossary convention. Fence idea-refine, ambiguity-detector, and requirement-enhancer. Register by hand. Cross-link from idea-refine and implementation-plan.

**What happened**: Authored `catalog/skills/developer-experience/design-interview/SKILL.md` with pushy description, SKIP fences, Common Rationalizations, Verification, and Related Skills. `CONTEXT.md` is documented as a sibling of `.claude/context/architecture.md`, never a replacement. Added `evals/trigger-cases.json` (4 positive / 3 negative). Cross-linked from `idea-refine` and `implementation-plan`.

**Key files changed**: `catalog/skills/developer-experience/design-interview/SKILL.md`, `catalog/skills/developer-experience/design-interview/evals/trigger-cases.json`, `catalog/skills/developer-experience/idea-refine/SKILL.md`, `catalog/skills/workflow/implementation-plan/SKILL.md`

**Troubleshooting**: Unquoted YAML `description:` containing `SKIP:` failed `validate_skills.py` (`mapping values are not allowed`). Rewrote the SKIP marker as `SKIP -` in the three new skills and matching `data/skills.json` strings.

**Verification**: `python scripts/validate_skills.py --bundles-only` PASS after the SKIP fix.

---

### 2.2 Wizard-generator skill (A5)

**Branch**: `feat/v3.20.3-skills-craft-and-prime-agent` | **PR**: none | **Merged to**: n/a

**Plan specification**: Create `setup-wizard-generator` with bundled `wizard-template.sh` and mandatory `wizard-template.ps1`. Agent adapts templates and does not run privileged steps.

**What happened**: Authored the skill plus both templates. Bash uses `set -euo pipefail`, quoted expansions, no eval. PowerShell sibling targets 5.1 and UTF-8 without BOM. SKILL.md references both paths so the orphan-bundle audit stays clean.

**Key files changed**: `catalog/skills/developer-experience/setup-wizard-generator/SKILL.md`, `scripts/wizard-template.sh`, `scripts/wizard-template.ps1`, `evals/trigger-cases.json`

**Troubleshooting**:

- **Problem**: Early `step_done` used a failing `grep` as the last command, so `set -e` aborted on a non-match.
- **Attempted**: Resume smoke with a pre-filled state file still showed `== welcome ==`.
- **Root cause**: `set -e` plus grep non-match. Separately, WSL `bash.exe` on this host drops Windows env vars (`WIZARD_STATE_FILE` arrives empty), so a Windows-path resume smoke is not a valid template test.
- **Resolution**: `tr -d '\r' <"$STATE_FILE" | grep -Fxq -- "$id" || return 1`. Resume through WSL env-passthrough classified ENV, not IMPL. Templates still lint: `bash -n` OK, PowerShell AST parse OK.

**Verification**: `bash -n` on the `.sh` PASS; PowerShell 5.1 AST parse of the `.ps1` PASS.

---

### 2.3 Decision-questionnaire skill (A6)

**Branch**: `feat/v3.20.3-skills-craft-and-prime-agent` | **PR**: none | **Merged to**: n/a

**Plan specification**: Create `decision-questionnaire` for the one absent stakeholder. Interview the requester about the send. Default path `docs/questionnaires/<date>-<topic>.md`. SKIP design-interview and ambiguity-detector. Cross-link to design-interview, business-analyst, internal-comms.

**What happened**: Authored the skill plus evals (4+/3-). Added a Related Skills link from `business-analyst`. Registered under business-product.

**Key files changed**: `catalog/skills/business-product/decision-questionnaire/SKILL.md`, `evals/trigger-cases.json`, `catalog/skills/business-product/business-analyst/SKILL.md`

**Troubleshooting**: Same `SKIP:` YAML colon defect as 2.1; same `SKIP -` fix.

**Verification**: Trigger evals `--gate` PASS with no cross-routing against design-interview.

---

### 2.4 Registration and stabilization

**Plan specification**: Hand-edit `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`. Do not run `build_skills_catalog.py`. Confirm installer needs no edit.

**What happened**: Incremented catalog to 324. Updated developer-experience 38 to 40 and business-product 6 to 7. Added the three names to `data/bundles.json` modules so `check_registry_entries.py --strict` treats them as reachable. Installer copy is not required: skill trees including `scripts/` and `evals/` copy recursively.

**Key files changed**: `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`, `data/bundles.json`, `CHANGELOG.md`

---

## 3. Verification Gate

| Check | Result |
|---|---|
| `python scripts/validate_skills.py --bundles-only` | PASS (324 skills) |
| `python scripts/check_agentskills_conformance.py` | PASS (324) |
| `python scripts/check_registry_entries.py --check --strict` | PASS |
| `python scripts/run_trigger_evals.py --gate` | PASS (66 skills with cases, 426 lexical, 0 routing failures) |
| `python scripts/validate_unicode_safety.py --strict --path` on Phase 2 files | PASS |
| `bash -n` wizard-template.sh | PASS |
| PowerShell AST parse wizard-template.ps1 | PASS |
| Wizard resume smoke via WSL bash.exe | NOT RUN as a valid test (ENV: WSL drops `WIZARD_STATE_FILE`) |
| Full `make test` / repo-wide pytest | NOT RUN locally (OneDrive host; same WN-3 as Phase 1; left to CI) |
| CI path-filter change | NOT NEEDED (`catalog/skills/**` already relevant) |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| WSL `bash.exe` on Windows does not inherit `WIZARD_STATE_FILE`, so a resume smoke against that binary is not a template proof | Cosmetic / ENV | Accepted. Native bash and the `.ps1` sibling remain the supported runtimes. |
| Full-tree `validate_no_personal_paths.py` and full pytest remain too slow on this OneDrive host | P2 | Reused v3.20.2 WN-3; scoped `--path` only. Left full tree to CI. |

---

## 5. Plan Discrepancies

- Plan path citations still name `docs/v3/v3.17/plans/v3.19.2-...`. Work landed against `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md`.
- Plan asked for three data files. `check_registry_entries.py --strict` also requires a `data/bundles.json` module entry; those three names were added so the skills are reachable.
- DEVLOG index line deferred until `/update release`.

---

## 6. Assumptions Made

- **Installer recursive copy**: New `scripts/` and `evals/` subdirs ride along without an installer edit (AGENTS.md recursive-copy rule). Impact if wrong: Phase 6 / installer-parity would catch a missing copy.
- **WSL bash is not Git Bash**: Treating `C:\windows\system32\bash.EXE` env-drop as ENV is correct for this host. Impact if a user runs the template under WSL: they must set the state file inside WSL or use the `.ps1` sibling.

---

## 7. Testing Summary

### Automated Tests

- Trigger evals `--gate`: 0 routing failures across 66 skills
- Registry strict check: PASS
- Skill bundle validation: PASS
- Wizard template syntax: bash `-n` PASS, PowerShell AST PASS

### Manual Testing Performed

- Confirmed `SKIP:` (colon) is invalid in unquoted YAML descriptions; `SKIP -` parses
- Confirmed marketplace developer-experience count 40 and business-product count 7

### Manual Testing Still Needed

- [ ] Resume a generated wizard under native Git Bash or a POSIX host (not WSL `bash.exe` from PowerShell)
- [ ] CI `tests` + `tests-windows` jobs on the eventual PR

---

## 8. TODO Tracker

### Completed This Session

- [x] 2.1 design-interview + CONTEXT.md convention + evals + cross-links
- [x] 2.2 setup-wizard-generator + bash/ps1 templates + evals
- [x] 2.3 decision-questionnaire + evals + business-analyst cross-link
- [x] 2.4 hand-edit registries, bundles modules, changelog, session history

### Remaining (Not Started or Partially Done)

- [ ] Phase 3 Prime Agent loop-discipline enrichments

### Out of Scope (Deferred)

- [ ] DEVLOG index line (`/update release`)
- [ ] Full local pytest (CI)

---

## 9. Summary and Next Steps

Three new skills are registered, evaluated, and cross-linked. Catalog is 324. The wizard templates lint; a WSL-from-PowerShell resume smoke is not evidence against the template. No installer change.

**Next session should**:

1. Implement Phase 3 (B1-B6, A8) as additive edits only.
2. Keep frontmatter changes limited to `overview_l1` where scope actually changed.
3. Commit Phase 3, then continue to Phase 4 invocation-policy (installer edits already in user scope).
