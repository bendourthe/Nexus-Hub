# Development Log: Skills-Craft CI Budget Fix and Inherited Gap Closure

**Date**: 2026-08-24
**Operator**: Ben
**Assisted by**: Cursor Grok 4.6
**Objective**: Unblock PR CI after Phase 6 push, then close the inherited v3.20.2 warnings that were actually fixable before `/update release`.
**Outcome**: AGENTS.md is back under its 8150-word ceiling. WN-4 and WN-5 are closed. DF-1, DF-2, WN-3, and WN-6 remain open with the same rationale as Phase 6.

---

## 1. Starting State

- **Branch**: `feat/v3.20.3-skills-craft-and-prime-agent`
- **Starting tag/commit**: `4d416a83` (Phase 6)
- **Environment**: Windows 11, PowerShell
- **Prior session reference**: [`2026-08-24_skills-craft-phase-6-refactor-gaps-ci.md`](2026-08-24_skills-craft-phase-6-refactor-gaps-ci.md)
- **Plan reference**: [`docs/releases/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md`](../../plans/v3.20.3-skills-craft-and-prime-agent.md)
- **PR**: https://github.com/bendourthe/Nexus-Hub/pull/113

Context: Phases 1-6 were committed and pushed. PR `validate` failed on `scripts/validate_doc_budgets.py`: `OVER AGENTS.md: 8382 words exceeds the 8150 ceiling by 232`. Cause was the Phase 4 invocation-policy section plus the Phase 5 plugin.json category sentence.

---

## 2. Chronological Steps

### 2.1 Relocate invocation-policy convention (CI blocker)

**What happened**: Moved the long command-derived-skill convention into `docs/policy/skill-invocation-policy-levers.md` (`## Catalog convention (v3.20.3)`). Folded a short pointer into the existing Optional Invocation-Policy Frontmatter section in AGENTS.md and shortened the new-category / plugin.json sentence. Did not raise the ceiling (ratchet-down policy).

**Result**: `validate_doc_budgets.py` reports AGENTS.md at 8086 words / 8150 ceiling (+64, 1% headroom, still marked tight).

---

### 2.2 Close WN-4 (docs-convention active minor)

**What happened**: First pass picked the newest version directory on disk, which resolved to `docs/v4/v4.1` (future planning) and skipped live v3.20. That is the same fail-open class as the old colocation gate. The fix reads `.claude-plugin/plugin.json` and scans `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` for that version, ignoring future majors. Pre-change live scan of `docs/v3/v3.20/` was 32 markdown files, 0 findings.

---

### 2.3 Close WN-5 (gitignore-aware manifest)

**What happened**: `generate_manifest.py` enumerates covered paths with `git ls-files -co --exclude-standard` when git is usable. Empty git listing is a valid "nothing eligible" result, not a reason to fall back to `os.walk` (that fallback was the defect). Non-git trees still walk disk. `verify_install.py` is unchanged and still walks an extracted tarball.

---

### 2.4 Left open on purpose

- **DF-1**: no vendor lever to invent.
- **DF-2**: official Claude plugin directory form is maintainer-submitted, not this loop.
- **WN-3**: full-tree personal-paths walk remains too slow on this OneDrive host; CI still owns it.
- **WN-6**: Codex skills docs timed out 2026-08-24; re-fetch during `/update release`.

---

## 3. Verification Gate

| Check | Result |
|---|---|
| `python scripts/validate_doc_budgets.py` | PASS (AGENTS.md 8086 / 8150) |
| `python scripts/check_docs_conventions.py` | PASS under `docs/v3/v3.20` (not `docs/v4/v4.1`) |
| `pytest tests/validators/test_check_docs_conventions.py tests/validators/test_verify_install.py` | 44 passed |
| Unicode `--strict` on touched Markdown | PASS |

---

## 4. Known Issues

Unchanged open set after this follow-up: DF-1, DF-2, WN-3, WN-6.

---

## 5. Plan Discrepancies

None. This follow-up is post-Phase-6 CI repair plus inherited gap closure the user asked for before `/update release`.

---

## 6. Assumptions Made

- Raising the AGENTS.md ceiling was the wrong fix; the invocation-policy convention is on-demand reference material.
- Scanning the canonical plugin minor (not the highest directory on disk) is required because `docs/v4/` already exists as planning.

---

## 7. Testing Summary

Targeted pytest for `test_check_docs_conventions.py` and `test_verify_install.py` (including the new gitignore test) is recorded in the commit that lands this change.

---

## 8. TODO Tracker

- [x] Unblock AGENTS.md word-budget CI failure
- [x] Close WN-4
- [x] Close WN-5
- [ ] Re-fetch Codex skills docs (WN-6) during `/update release`
- [ ] `/update release` after PR CI is green

---

## 9. Summary and Next Steps

PR validate failed because Phase 4/5 added always-loaded prose to AGENTS.md. That convention now lives in the invocation-policy levers doc. The two inherited warnings that were actually code bugs (pinned minor, gitignored manifest entries) are fixed.

**Next session should**:

1. Push this follow-up and wait for PR #113 CI.
2. Re-fetch Codex `learn.chatgpt.com` docs for WN-6.
3. Run `/update release` only after the PR is green.
