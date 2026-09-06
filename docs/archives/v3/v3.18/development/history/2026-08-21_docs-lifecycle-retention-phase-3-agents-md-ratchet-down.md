# Session History - Docs Lifecycle and Retention Phase 3: AGENTS.md MT-1 Ratchet-Down

**Date**: 2026-08-21
**Branch**: `feat/docs-lifecycle-retention`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.0-docs-lifecycle-retention.md`](../../plans/v3.18.0-docs-lifecycle-retention.md)
**Phase**: 3 - AGENTS.md MT-1 ratchet-down
**Environment**: Windows 11, Git Bash and PowerShell, Python 3.12, pytest; GNU Make unavailable, so `make` targets were executed as their constituent commands
**Outcome**: `AGENTS.md` went from 9,715 to 7,742 words with 2,211 words relocated verbatim, its ceiling ratcheted 10,060 to 8,150, and MT-1 is RESOLVED. Two link breakages inherent to relocation were found and repaired, one of them by reading the file rather than by the link checker.

## 1. Starting State

- **Starting commit**: `132b301f` (Phase 2: every DEVLOG writer produces the index format)
- **Worktree**: clean
- **`AGENTS.md`**: 9,715 words against a 10,060 ceiling, 345 words of headroom (3%), reported `<- tight` by `validate_doc_budgets.py --list`. MT-1 had measured it at 9,138 words; it had grown 577 words since.

The plan recorded `frontier / high`. Implementation ran on Opus 5 (`strong`), with the delta surfaced and the switch keystroke printed rather than silently accepted. This is the phase where that gap mattered most, since AGENTS.md is inlined into every session and a botched relocation removes guidance silently.

## 2. Measurement Before Editing

Sectioning `AGENTS.md` by heading and word count first was what made the phase tractable, and it corrected a false reading. A naive scan attributes 1,211 words to a `## Related Skills` section, which does not exist: those H2s (`When to Use This Skill`, `Instructions`, `Common Rationalizations`, `Verification`, `Related Skills`) sit inside a fenced `markdown` block, the required-body-sections template for skill authors. Treating them as real sections would have pointed the relocation at a code fence.

Real candidates, measured:

| Words | Block |
|---|---|
| 1,180 | `### Platform coverage caveats (current state)` |
| 1,031 | `#### Per-skill Bundled Resources` |
| 935 | `### Distribution channels the installer uses` |
| 441 | `## Per-Platform Install Defaults` |
| 427 | MCP decision tree, audit checklist, hard-no list, matrix, attribution |
| 400 | `#### Three-Tier Loading Model` |
| 367 | `## Model Routing in the Plan/Implement Loop` |

The first two alone total 2,211, clearing the plan's 2,000-word target, and both are explicitly named in the plan's candidate list. Taking only those kept the blast radius at two files.

## 3. The Pre-Move Grep, and What It Changed

The plan requires grepping `tests/`, `catalog/hooks/tests/`, and `scripts/` for assertions on `AGENTS.md` content before moving anything. A naive grep for `AGENTS.md` returns roughly 80 files, almost all of which reference the **distributed** `AGENTS.md` that the installer writes to a user's repo, not this repo's own content. Grepping for the specific heading strings instead found the real dependencies:

- `MCP Registry Policy` in `scripts/check_base_template_parity.py` and its test, as an **invariant block name across the five `base-*.md` templates**. Not about `AGENTS.md` itself, but see section 5.
- `Per-skill Bundled Resources` cited by name in `scripts/validate_skills.py` (three places), `scripts/package_skill.py`, and `catalog/hooks/tests/test_skill_bundles.py`.
- `Platform coverage caveats` cited by `docs/specs/README.md`.

Those six citations drove the central design decision of this phase: **keep the original heading names in `AGENTS.md` as the summary headings.** Every citation is to a heading name, so a summary under the same heading keeps all six valid with no lockstep edit. Deleting the headings and pointing elsewhere would have broken all six and required touching five files to fix. The plan's "replace each with a 2-4 line summary plus a repo-relative link" already implies this; the grep is what showed it was load-bearing rather than stylistic.

## 4. Relocations

**"Platform coverage caveats (current state)" (1,180 words) merged into `docs/policy/platform-read-contracts.md`.** The plan's failure-mode rule says a relocated block that would duplicate an existing policy doc must merge into it rather than become a sibling, and this is that case exactly: the policy doc already owns per-platform read paths and capabilities, and the caveats section is its narrative companion. The merge is hosted under a new `## Platform coverage tiers (relocated from AGENTS.md, 2026-08-21)` heading stating the relationship: the surface table says *where* each platform reads from, the caveats say *how much* of the catalog each receives and why.

**"Per-skill Bundled Resources" (1,031 words) to a new `guides/reference/SKILL_BUNDLED_RESOURCES.md`.** No existing file fits: it is an authoring convention, not a policy contract, and `guides/reference/` is where the developer authoring guides live. Its top heading was promoted from `####` to the file's `#` now that it owns a file.

Both destinations were verified to contain the source content verbatim, then verified again line-by-line: every non-empty source line is present at its destination, so nothing was summarized away in the move.

## 5. What Was Deliberately Not Relocated

Per the plan's do-not-touch list: the golden installer rule, the skill-registration steps, `Critical Conventions`, and `Boundaries`. All four were confirmed still present after the edit.

Beyond that list, the **MCP decision tree** (427 words) was left in place despite being named as a candidate. The five `base-*.md` templates each carry an `MCP Registry Policy` block that `check_base_template_parity.py` treats as an **invariant** and that points at `AGENTS.md` for the full policy and five-question audit. Relocating the detail would have required editing all five templates in lockstep, under a guard that fails on divergence, for 427 words the phase did not need to clear its target. The cost/benefit did not justify it; recorded in the MT-1 resolution so the next author does not rediscover it.

## 6. Two Link Breakages, and Why Only One Was Caught by Tooling

Relocation moves content to a different directory depth, so every relative link in it is suspect. Both failures showed up:

1. **Two repo-root-relative links** (`docs/v3/v3.11/development/roster-verification.md`, `docs/archive/v2/v2.2/antigravity-cli-probe.md`) were correct from the repo root and broken from `docs/policy/`. Caught by the link check, repaired to `../v3/...` and `../archive/...`.
2. **Three anchor-only links** (`#distribution-channels-the-installer-uses`, `#skill-md-size-norm`, `#three-tier-loading-model`) were intra-`AGENTS.md` anchors. Once the block owned its own file they pointed at headings that do not exist in it. The link check **did not catch these**, because it skips `#`-only targets as same-page anchors, which they no longer were. Found by reading the relocated file. Repaired to `../../AGENTS.md#...`.

The second is the more useful lesson: a same-page anchor becomes a cross-file link the instant its content moves, and a checker that treats `#` as always-local is blind to exactly that transition.

## 7. The Ceiling, and a Deviation From the Plan

The plan says to lower the ceiling to "the new word count plus ~200 headroom". At 7,742 words that is 7,942, which `--list` still reports `<- tight` at 3%. `docs/policy/doc-budgets.md` requires at least 5% headroom on the stated grounds that a tighter ceiling effectively freezes the doc, which is the condition MT-1 was opened about. The policy floor was followed over the plan's literal number.

Getting there took two attempts, because the validator computes `headroom / ceiling` rather than `headroom / words`. Clearing a 5% floor at 7,742 words therefore needs 8,150, not the 8,130 that a naive "words plus 5%" gives. Recorded in the MT-1 resolution for the next ratchet.

Final: ceiling 10,060 to 8,150, headroom 408 words (5%), no `<- tight` marker. Phase 4 adds a 2-3 line retention-policy pointer to `AGENTS.md` and fits inside that headroom.

## 8. Verification

| Check | Result |
|---|---|
| `AGENTS.md` word count | 9,715 to 7,742; 2,211 relocated, 1,973 net |
| Destination completeness | both blocks verbatim; 0 source lines missing at either destination |
| `validate_doc_budgets.py --list` | AGENTS.md 7,742 / 8,150, +408 (5%), no tight marker |
| `validate_doc_budgets.py` (gate) | PASS, 8 budgeted docs within ceiling |
| `check_base_template_parity.py` | PASS |
| `verify_platform_contracts.py` | PASS |
| `check_platform_contract_freshness.py` | PASS |
| Link check, `AGENTS.md` + both destinations | 0 broken after repair (5 broken found and fixed) |
| Do-not-relocate items present | golden rule, register-the-skill, Critical Conventions, Boundaries, required-steps checklist, MCP Registry Policy: all 6 present |
| `validate_unicode_safety.py --strict` | PASS repo-wide |
| `validate_decision_records.py`, `check_version_sync.py`, `validate_no_personal_paths.py` | PASS |
| `pytest tests/validators tests/skills tests/plans tests/integrations catalog/hooks/tests` | **3,371 passed, 39 skipped, 0 failed** |

On the plan's instruction to "run a link check over AGENTS.md and every file it now links to": this was read as checking `AGENTS.md` plus every file this phase created or edited. Link-checking the full transitive closure of everything `AGENTS.md` references is a repo-wide documentation audit, which is `[[documentation-consistency]]` work and is not what a relocation needs to prove.

`tests/installer` was excluded, as in Phase 2: it is unaffected by a documentation relocation and carries the pre-existing bare-`tar` PATH failure recorded in the Phase 1 history.

## 9. Ending State

- **Files added**: `guides/reference/SKILL_BUNDLED_RESOURCES.md`, this history file
- **Files modified**: `AGENTS.md`, `docs/policy/platform-read-contracts.md`, `docs/policy/doc-budgets.json`, `docs/v3/v3.17/known-gaps.md` (MT-1 resolved), `CHANGELOG.md`, `docs/todos.md`
- **Catalog counts**: unchanged at 273 skills, 18 commands, 31 hooks, 23 agents
- **Stability gate**: met. 2,211 words relocated against a 2,000 target, every relocated section replaced by a summary plus link, ceiling ratcheted down, and `make validate`'s constituent gates including the budget gate and base-template parity all pass.

## 10. Next Steps

1. **Phase 4 (history retention policy)** is next and depends on Phase 1, which is complete. It adds a 2-3 line pointer to `AGENTS.md`, which fits in the 408-word headroom.
2. Carry to Phase 5's known-gaps reconciliation:
   - The anchor-link blind spot from section 6: a documentation link checker that treats `#` targets as always same-page cannot see an anchor orphaned by relocation. Worth a general check if `[[documentation-consistency]]` grows a link gate.
   - The MCP decision tree relocation, deferred here with its reason, if a future ratchet needs the words.
   - Everything already carried from Phases 1 and 2: the bare-`tar` PATH failure, the stray `Microsoft/` directory, and the SKIP-clause / routing-scorer tension.
