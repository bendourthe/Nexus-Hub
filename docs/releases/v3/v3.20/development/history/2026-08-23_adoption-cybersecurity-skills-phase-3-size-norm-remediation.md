# Session History - Cybersecurity Skills Adoption Phase 3: Size-Norm Remediation

**Date**: 2026-08-23
**Branch**: `feat/v3.20.1-adoption-cybersecurity-skills`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.1-adoption-cybersecurity-skills.md`](../../plans/v3.20.1-adoption-cybersecurity-skills.md)
**Phase**: 3 - Size-norm remediation
**Environment**: Windows 11, PowerShell, Python 3, pytest
**Outcome**: Zero SKILL.md bodies over 800 lines; the cap is a `--bundles-only` hard error. Ready for Phase 4.

## 1. Starting State and Routing

- **Starting commit**: `31dade6c` (Phase 2 coverage map and standards companions)
- **Plan recommendation**: strong model, high effort
- **Implementation route**: stayed on the current Cursor session (Grok 4.6 / frontier)

## 2. What Was Implemented

### 3.1 - Relocate over-cap bodies

47 SKILL.md files exceeded 800 body lines (max 2545, `android-development`). Long-tail `##` sections and long `###` Instruction steps were moved into `references/*.md` and replaced with on-demand links. Required sections (When to Use, What This Skill Does, Instructions, Common Rationalizations, Verification, Related Skills) remain in the body. Frontmatter bytes were verified identical to HEAD for all 47 files.

### 3.2 - Machine-enforce the cap

`scripts/validate_skills.py` counts body lines excluding frontmatter. Over 800 is a hard error in `--bundles-only` and the full validator. Over 500 is a grandfathered warning. `AGENTS.md` now states the 800 cap is machine-enforced.

### 3.3 - Tests

Body-size tests cover frontmatter exclusion, the 500 warning tier, the 800 hard cap, and `--bundles-only` failing on an 801-line fixture.

## 3. Tests

- `python -m pytest tests/validators/test_validate_skills.py -k "body_ or count_body or bundles_only_fails_when_body"`: 8 passed
- Catalog census after relocation: 0 skills over 800 body lines; 47 SKILL.md files changed; 0 frontmatter mismatches vs HEAD

## 4. Deviations

- Relocation was fence-aware and one-pass (optional `##` sections, then Instruction `###` steps, then an Instructions tail if still over). A first looping prototype created thousands of stub files under `ai-agent-development/references/`; numbered `references-*.md` leftovers are local OneDrive-locked junk and must not be committed.
- Several skills remain between 500 and 800 lines (`microservices-patterns`, `async-patterns`, `graphql-development`, `nextjs-expert`, `unit-tests`). That is the grandfathered warning tier, not a hard failure.
- DEVLOG index line deferred until `/update release`.

## 5. Next Steps

Phase 4: author 40 vendor-neutral security skills under the MIT licensing rule, after recording category-gate approval for `ot-security` and `mobile-security`.
