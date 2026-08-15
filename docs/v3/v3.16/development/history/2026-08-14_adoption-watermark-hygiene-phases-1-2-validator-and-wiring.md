# Session History - v3.16.8 Phases 1-2: Unicode validator coverage, fix mode, and workflow wiring

**Date**: 2026-08-14
**Plan**: [plans/v3.16.8-adoption-watermark-hygiene.md](../../plans/v3.16.8-adoption-watermark-hygiene.md)
**Phase**: 1 and 2 of 3 (Phase 3, the terminal refactor / reconciliation / CI-CD phase, is not started)
**Branch**: `feat/v3.16.8-adoption-watermark-hygiene`
**Status**: COMPLETE for both phases. Two pre-existing suite failures remain open and are documented as not introduced here.

Phases 1 and 2 were implemented in one session and share one commit. Phase 1 reached its quality gate with two unresolved pre-existing failures and was awaiting a gate decision when Phase 2 was requested, so Phase 1's post-phase sequence never ran independently. Recorded as `QG-1` in the known-gaps file rather than left implicit.

## Phase 1: validator coverage and fix mode

### 1.1 Extended detection

Three character families were added to `scripts/validate_unicode_safety.py`, split across the two existing severity classes by whether the character has any legitimate use in this repository:

- **Hard errors**: Unicode tag characters `U+E0001` and `U+E0020`-`U+E007F`. They mirror printable ASCII and render as nothing, which makes them a general-purpose hidden-text channel with no legitimate use here. Their finding description carries the mirrored ASCII character, so smuggled text is readable straight off the report (verified in the smoke test: two injected tags reported as `mirroring 'H'` and `mirroring 'I'`).
- **Strict class** (warn by default, error under `--strict`, Markdown only): the space homoglyphs `U+2000`-`U+200A`, `U+1680`, `U+202F`, `U+205F`, `U+3000`; soft hyphen; and the variation selectors `U+FE00`-`U+FE0F` plus the `U+E0100`-`U+E01EF` supplement.

Every new entry is built from codepoint integers, preserving the module's self-detection-free property.

### The VS16 measurement, and the deviation it produced

The plan prescribed a blanket VS16 rule. Applying it literally raised the repo-wide warning count from 1049 to 1139, which failed the phase's own stability gate, so the additions were measured before being accepted rather than after.

All 90 VS16 occurrences follow an emoji base (`U+26A0` warning sign 76, `U+1F5FA` world map 7, `U+2764` heart 7, plus `U+2328` keyboard and `U+2139` information source). VS1-VS15 and the 240-value supplement occur zero times. The literal rule would therefore have flagged 90 legitimate characters, caught nothing, and (once Phase 2's release gate landed) silently rewritten emoji in `CHANGELOG.md` and the active docs tree, which are exactly the artifacts that gate exists to protect.

The measurement was put to the maintainer with three options. The chosen one covers the full variation-selector range but exempts a VS16 immediately following a symbol (`So` / `Sk`) or keycap base, and still reports a stray VS16 with no base. `unicodedata.category` supplies the predicate, so no emoji-range table is maintained. The accepted residual (a CJK ideographic variation sequence would be reported) is stated in both the function and module docstrings and recorded as `WN-1`.

### 1.2 Fix mode

`--fix` removes hard-error characters always, and applies ASCII replacements only when `--strict` is also passed. Design points worth keeping:

- **Detection and repair share one policy function** (`punct_finding_applies`). The classic failure of a fixer bolted onto a linter is a rule one half applies and the other does not, producing either an unfixable loop or a silent rewrite. A round-trip test asserts `repair_text` output has zero findings under `scan_text`.
- **A separate `_FIX_REPLACEMENTS` table**, because the existing human-readable suggestion (`-- or ()`) is advice, not a substitution. A drift-guard test asserts the two tables cover exactly the same codepoints.
- **Newline style survives by construction**, not by configuration: `repair_text` never inspects `\r` or `\n`. Verified on the real 5095-line `CHANGELOG.md`, which came through the fix pass with 5095 CRLF and 0 lone LF.
- **`shutil.copymode` before `os.replace`**, because `mkstemp` creates 0600 and a repaired `.sh` would otherwise silently lose its executable bit.
- **A strict decode gates the write path.** The scanner previously decoded with `errors="replace"`; writing that back would corrupt the undecodable bytes into U+FFFD. All 1682 scanned files decode strictly, so the baseline is untouched, but an unreadable or undecodable file is now reported (exit 2) instead of silently skipped.

### The stability gate

The phase's gate was a pre/post baseline diff, captured before any edit: `0 errors, 1049 warning(s)`, exit 0. After both sub-tasks the no-argument run was **byte-identical**, confirmed with `diff` rather than by comparing summary counts.

## Phase 2: workflow wiring

### Two silent-failure defects found by testing the wiring

Before writing the instruction text, the exact command was run against a scratch project. Two defects surfaced that the phase's own unit tests could not reach, because those always pass a `--root` that contains the target:

1. **A `--path` that did not resolve under `--root` exited 0 reporting a clean scan.** `iter_target_files` skipped missing targets. A gate wired that way reports success while checking nothing, which is precisely the silent-failure class this plan exists to eliminate. Now: an explicitly requested missing path exits 2 and names it; a missing *default* target is still tolerated, since not every repo has an `AGENTS.md`.
2. **An absolute `--path` outside root raised a bare `ValueError` traceback** from `relative_to` during reporting. Now routed through `display_path`.

Both matter because Phase 2's entire value is that `/plan` and `/update release` can trust the exit code. Three regression tests cover them.

### 2.1 The `/plan` closing sanitize pass

`catalog/skills/workflow/implementation-plan/SKILL.md` Step 4 gained a mandatory closing pass, with a matching verification-checklist item, and Step 5 re-runs it when user feedback rewrites the plan (the guarantee is about the file the user receives, not the first draft). `catalog/commands/plan.md` surfaces it in one paragraph and stays a thin dispatcher.

The documented form is `--strict --fix --root . --path <plan-file>`. The explicit `--root .` is load-bearing rather than decorative: the script's default root is derived from its own location, so an installed copy at `~/.nexus-hub/scripts/` would otherwise resolve `--path` against `~/.nexus-hub` and (before the fix above) report a clean scan of nothing. The smoke test was deliberately run from a foreign project root to prove the documented form works for a consuming project, not only inside this repo.

### 2.2 The `/update` gates

- **`docs` and `changelog` scopes**: detect-first, deliberately not fix. These scopes touch hand-edited prose whose punctuation may be intentional, and an automatic rewrite would silently overrule the author.
- **`release` scope**: governance step 7, a blocking fix-and-block gate scoped to release-cycle artifacts only, ordered before the manifest regeneration so the manifest always hashes post-sanitize bytes. Today's artifact list sits outside the manifest roots, so the ordering is currently harmless; fixing it anyway makes correctness a property of the flow rather than a coincidence.

### The one-time historical normalization

A changelog is one file holding both the new entry and all history, so file-level scoping cannot spare its old sections. The gate's first run was measured before being executed: exactly 7 findings, all in `CHANGELOG.md` (`README.md` and all 59 files under `docs/v3/v3.16/` were already clean), in sections released between v0.8.2 and v1.2.1. The fix produced exactly 7 character-level replacements (6 em dashes to `--`, 1 en dash to `-` in the range `G0-G3`) with nothing else altered on those lines, verified by an opcode-level diff. The repo-wide warning count moved 1049 to 1042 accordingly.

This was done deliberately in the release that introduces the gate, because the alternative was shipping a blocking gate that fails on its first real use. The command text records it so a future release seeing a large `CHANGELOG.md` diff from this gate investigates rather than accepts it.

## Verification

| Gate | Result |
|---|---|
| Detect-mode baseline (Phase 1 stability gate) | byte-identical to pre-change: 0 errors, 1049 warnings, exit 0 |
| `validate` sequence (12 gates, run directly since `make` is unavailable) | all green; unicode now 0 errors / 1042 warnings (the 7 normalized dashes) |
| `tests/validators/` | 604 passed then 607 passed with the new cases |
| `tests/skills/` | 685 passed |
| `tests/plans` + `tests/workflows` + `tests/validators` | 788 passed, 1 skipped, 1 failed (pre-existing `BG-2`) |
| `catalog/hooks/tests/` | 993 passed, 36 skipped |
| Extension suites (5) | 670 passed |
| `tests/` (full) | 2417 passed, 18 skipped, 2 failed (both pre-existing) |
| Smoke: plan sanitize from a foreign root | 4 unsafe removed, 1 replacement, exit 0 |
| Smoke: release gate, detect mode | exit 0 |

New tests: 28 in `tests/validators/test_validate_unicode_safety.py` (8 to 36), covering each added character class in both severity paths, the emoji exemption in both detection and repair, fix-mode round-trips, BOM and CRLF and file-mode preservation, the undecodable-input refusal, the two table-drift guards, and the three `--path` resolution cases.

## CI/CD

No change required, verified rather than assumed. The CI step at `.github/workflows/ci.yml` calls the validator in detect mode with no arguments and is untouched by every change here. The workflow's `paths` filter is `**` minus `docs/**`, so `scripts/**`, `tests/**`, and `catalog/**` all trigger the full run. `tests/validators` runs on the Linux leg, which is where the Windows-skipped file-mode test executes.

## Known issues

Six items recorded in [known-gaps.md](../../known-gaps.md) under `## v3.16.8`. Two are pre-existing suite failures that this cycle observed but did not cause:

- **`BG-1`**: the PowerShell bootstrap tarball test, already root-caused as v3.16.0 `BG-1` (Git Bash's MSYS `tar` resolving ahead of the system binary). Cross-referenced, not re-filed.
- **`BG-2`**: `test_bundled_snapshot_parses_and_renders_dated_fallback` asserts `stale as of 2026-08-03` while the renderer emits `2026-08-14`. Commit `b29a0ffa` refreshed the model-map snapshot without updating the test. The suggested fix derives the expectation from the snapshot's `verified_as_of`, since the current hardcoded form is a time bomb that fires on every legitimate refresh.

Neither failing test reads any file this cycle modified.

## Next steps

- Phase 3: architecture refactor, known-gaps reconciliation, and CI/CD, then release readiness.
- The two pre-existing failures are the natural first items for Phase 3's reconciliation.
