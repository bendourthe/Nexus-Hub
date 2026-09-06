# Session History - Interface-Craft Skills Phase 6: interface-review coordinator

**Date**: 2026-08-23
**Branch**: `feat/v3.20.2-interface-craft-skills`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.2-interface-craft-skills.md`](../../plans/v3.20.2-interface-craft-skills.md)
**Phase**: 6 - interface-review coordinator (A8)
**Environment**: Windows 11, PowerShell, Python 3
**Outcome**: Coordinator registered. Catalog 320 -> 321 (net +6 from 315). Routing evals passed lexically against delegates and code-review. Dry-run on a real fixture produced one consolidated report. Ready for Phase 7.

## 1. Starting State and Routing

- **Starting commit**: `aaeebe1c` (Phase 5 hallmark merge)
- **Plan recommendation**: strong reasoning tier, high effort
- **Implementation route**: current Cursor session; no downshift
- **Installer edit**: none

## 2. What Was Implemented

### 6.1 - Coordinator body

`catalog/skills/developer-experience/interface-review/SKILL.md` (description 222 characters, body 143 lines). Canonical rule-ownership table. Review order accessibility -> layout -> copy -> typography -> color -> polish, with why. Ignore delegate output formats. Missing-delegate honesty. Quick cap 5 (blocker/major); full cap 20. Read-only default. Considered-but-Rejected required.

### 6.2 - Registration and evals

Hand-registered index/skills.json/marketplace (developer-experience 38) / bundles. Matrix row `skill-native`. `evals/trigger-cases.json`: three holistic positives; negatives for accessibility-engineering, color-systems, and multi-agent-code-review. All stayed `lexical: true`. `run_trigger_evals.py --gate` PASS.

### 6.3 - Dry run

Target: `extensions/nexus-code-search/tests/fixtures/benchmark/blog_ts/components.tsx` (real UI in this repo; no CSS, so color measurement marked not verified).

Mode: full, cap 20, mutating no. Thin file, not padded.

Headline findings (not a dump of six skill formats):

| ID | Severity | Domain | Location | Current | Owner rule |
|---|---|---|---|---|---|
| F1 | blocker | Accessibility | `components.tsx:13` | `<article onClick=...>` | Keyboard: primary open action is pointer-only |
| F2 | major | Copy | `components.tsx:42` / `:48` | Visible "Prev" / "Next" | Name the object ("Previous page") |
| F3 | major | Accessibility | `components.tsx:27` | `<div>Loading comments...</div>` | Loading status needs a live region / polite status |

Coverage: color **not verified** (no computed styles in the fixture). Typography/polish had no rendered tokens to score; recorded as inspected-with-no-finding rather than reconstructed rules.

Considered-but-Rejected: `CommentList` native `ul`/`li` (permitted); `PostCard` `h2` skip-rank unknown without page `h1` (insufficient evidence); disabled Prev on page 1 (permitted).

Verdict: fail. The primary card cannot be opened from the keyboard. One verdict paragraph; no second summary table.

## 3. Tests

- `python scripts/validate_skills.py --bundles-only`: PASS (321)
- `python scripts/check_registry_entries.py --check --strict`: PASS
- `python scripts/check_agentskills_conformance.py`: PASS
- `python scripts/run_trigger_evals.py --gate`: PASS (391 lexical cases, 0 routing failures)
- Unicode scan on the new skill: PASS

## 4. Deviations

- CI path filters unchanged (unfiltered triggers + job-level `changes` already cover `catalog/skills/**`).
- DEVLOG deferred until `/update release`.

## 5. Next Steps

Phase 7: project-refactor + docs-layout-refactor (propose-then-apply), known-gaps (D1 truncation, WN-3, catalog-count drift to `/update release`), CI/CD optimize without switching `--bundles-only` off.
