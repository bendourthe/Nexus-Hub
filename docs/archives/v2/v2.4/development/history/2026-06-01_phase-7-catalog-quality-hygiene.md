# Session History - v2.4.0 (adoption-compound-engineering-plugin) Phase 7: Catalog-Quality + Hygiene Remediation

**Date**: 2026-06-01
**Plan**: [docs/archives/v2/v2.4/plans/adoption-compound-engineering-plugin.md](../../plans/adoption-compound-engineering-plugin.md)
**Phase**: 7 of 8 - Catalog-quality + hygiene remediation (the nine ingested v2.3.0 known-gaps)
**Sub-tasks**: T026 (quality-warning sweep), T027 (security-ops query examples), T028 (BOM strip), T029 (compliance-template punctuation), T030 (personal-path redaction), T031 (orphaned template deletion), T032 (CI shellcheck broadening), T033 (Ruby/PHP/C/C++ extractors), T034 (python_app precision), T035 (testing + stabilization)
**Outcome**: All nine ingested gaps resolved plus the pre-existing BG-v24-1. Quality warnings 576 -> 0 across all 245 skills; 4 new code-search languages (coverage 6 -> 10) at 100% recall/precision; python_app precision 70% -> 100%; BOM/unicode/personal-path validators now pass with their Makefile + CI exclusions removed. Full test suite green (code-search 187, validators 115, hooks 415, integrations+installer 267, skill-server 43). No new skills (registries unchanged at 245).

---

## Goal

Resolve the nine ingested v2.3.0 known-gaps that constitute Phase 7: reduce the 574 quality-heuristics warnings (T026 / WN-v23-4), enrich three high-traffic security-operations skills (T027 / DF-v23-2), strip BOMs (T028 / WN-v23-2) and non-ASCII punctuation (T029 / WN-v23-3) so their validators run with no exclusions, redact personal paths in a test fixture (T030 / DF-v23-1), delete an orphaned instruction template (T031 / DF-v23-3), broaden CI shellcheck to per-skill scripts (T032 / QG-v23-1), add the next code-search language extractors (T033 / DF-v23-4), and lift the python_app import-site precision residual (T034 / DF-v23-5). Two scope decisions were taken to the user up front: T026 ambition (chose **full sweep to near-zero** over the "worst batch" floor) and T033 breadth (chose **Ruby + PHP + C + C++** over the Ruby-only floor).

## Steps taken

1. **Phase 0 - resolve plan / phase**: parsed `7 of v2.4.0 adoption-compound-engineering-plugin.md` (filename is `compound`; invocation had a typo). Legacy flat layout `docs/archive/v2/v2.4/plans/`. Phases 1-6 closed; final-phase detection false (7 of 8, Phase 8 open) so the Phase-9 release-readiness workflow does not run. Captured baselines: 576 quality warnings, 15 BOM files, 19 strict punctuation findings in compliance-review, 8 personal-path findings, python_app precision 70%.

2. **Environment setup**: confirmed `tree-sitter` was absent on the host (the code-search suite could not run); pip-installed `tree-sitter` + the four new grammars (ruby/php/c/cpp) and the code-search package editable, getting the full suite green (168 passed) before touching it. This unblocked T033/T034 verification.

3. **T026 (parallelized)**: read the exact `--quality` rules from `validate_skills.py` (four checks: Common Rationalizations present, Verification with a binary `- [ ]` checklist, Tier-1 field budgets, Related Skills with `[[link]]`). Wrote a shared remediation spec, then fanned out nine background subagents (one per category group, disjoint file sets); each ran the scoped validator, remediated to zero, and re-verified. 218 skills across 20 categories edited.

4. **Mechanical cleanups (direct)**: T028/T029 via a one-shot text-cleaning script (BOM strip + punctuation map), then dropped the `templates/ai-instructions` unicode exclusion from Makefile + ci.yml. T030 redacted the real-username `/c/Users/<name>/...` test inputs to the allowed, shell-clean placeholder `user`, confirmed the audit still passes 172/172, dropped the `catalog/hooks/tests` exclusion from Makefile + ci.yml. T031 grep-confirmed no integration selects `base-gemini-ide.md`, deleted it, updated the `gemini.py` + `instruction_merge.py` comments. T032 broadened the CI shellcheck `find` and bash -n'd the 8 per-skill scripts. T027 delegated to one subagent (three query-examples references, distinct domains).

5. **T033 (direct, code-search)**: AST-probed each grammar against representative snippets to confirm node types, wrote four extractors modeled on `go.py`, smoke-tested them (symbols + edges all correct), registered them in `LANGUAGE_EXTRACTORS`, added the grammar deps under `<0.26`, built four eval fixtures + four unit-test files, and updated the eval-runner's fixture-set assertion.

6. **T034 (direct, code-search)**: demoted IMPORT/EXPORT nodes from default `search_fts` (gated on the existing `all_columns`/`all_fields` opt-out), added two `test_traverser.py` cases.

7. **T035 - stabilization**: ran the `make validate` validator set directly (make unavailable on host), the code-search eval, and every pytest suite; closed BG-v24-1; ran the post-phase documentation sequence.

## Troubleshooting

- **No tree-sitter on host**: the code-search suite had 21 collection errors at start. Resolved by pip-installing the core + grammars (network access confirmed) and the package editable; the four new grammars all resolve under the shared `<0.26` ceiling.
- **PowerShell here-string quote-stripping**: an inline `python -c @'...'@` analysis mangled the embedded quotes; rewrote it as a temp script file (later removed).
- **Integration idempotency false failure**: an early `tests/integrations` run failed `test_install_idempotent[antigravity]` because it ran concurrently with the T026 subagents still editing `catalog/skills/`; re-running on the stable tree passed (267 passed).
- **Windows bash-stub mass failure**: catalog/hooks/tests showed 73 failures whose tracebacks revealed UTF-16 "install WSL from the Store" output - the host's `bash.EXE` resolves to the Windows App-Execution-Alias stub. Prepending Git-for-Windows bash to PATH dropped it to 1 failure (the pre-existing BG-v24-1), proving the 72 were an environment artifact, not regressions.
- **pytest rootdir collision**: combining `catalog/hooks/tests` with `extensions/nexus-skill-server/tests` in one invocation mis-attributed module paths (the documented nested-pyproject rootdir issue); ran each suite as a separate pytest invocation, as CI does.
- **PHP method-name collision in the unit test**: `speak` is declared on both the interface and the class, so the call edge can attach to either; made the assertion robust by checking across all `speak` method nodes.

## Assumptions

- T026 "full sweep to near-zero" and T033 "Ruby + PHP + C + C++" were the user's explicit scope choices (over the plan's stated floors), confirmed via a pre-flight question.
- The four new tree-sitter grammar wheels auto-distribute via the editable `pip install` (the extension is pip-installed in CI and by the installer), so no installer copy-step is needed - consistent with the v2.3.0 Go/Rust/Java/C# batch.
- Dropping the matching unicode / personal-path exclusions from `ci.yml` (not just the Makefile) is the correct intent: the subtrees are now clean, so the exclusions are obsolete in both places.
- BG-v24-1 is in scope for Phase 7: the known-gaps file explicitly names "Phase 7 (catalog-quality/hygiene)" as a close point, the installer's dynamic-seed design is canonical, and it is a one-line test-assertion fix that greens the suite.
- A subset of skills now carrying both `## Quality Checklist` and `## Verification` is acceptable (validator-clean cosmetic redundancy), recorded as WN-v24-2 rather than forced into a uniform pass.
- `make` / shellcheck are unavailable on the host; validators ran directly and `bash -n` substituted for shellcheck locally (full shellcheck runs in CI on Linux).

## Testing results

- `make validate` equivalent (direct, with reduced exclusions): JSON catalogs OK (registries unchanged at 245), orphan-bundle 0/0, quality 0 warnings, no-personal-paths exit 0 (no catalog/hooks/tests exclusion), unicode-safety exit 0 (no templates/ai-instructions exclusion), supply-chain-iocs / workflow-security / solution-frontmatter all exit 0.
- Code-search eval: all 10 fixtures at 100% recall / 100% precision (ruby_app / php_app / c_app / cpp_app new; python_app precision 70% -> 100%).
- nexus-code-search: 187 passed / 1 skipped (incl. 17 new extraction tests + 2 new traverser tests).
- tests/validators: 115 passed. nexus-skill-server: 43 passed.
- catalog/hooks/tests: 415 passed / 3 skipped (with Git bash on PATH; BG-v24-1 fixed).
- tests/integrations + tests/installer: 267 passed.
- `bash -n` clean across all 8 per-skill `catalog/**/*.sh` scripts (T032).

## Deviations

- **BG-v24-1 closed in Phase 7** (not strictly one of the 9 ingested T-items): the known-gaps file authorized Phase 7 as a close point; the stale test now asserts the installer's current dynamic-template-seed fallback hint.
- **CI exclusions also dropped** (T028/T030 plan text names only the Makefile): the same exclusions in `ci.yml` were removed for consistency now that the subtrees are clean.
- **WN-v24-2 added**: cosmetic `## Quality Checklist` + `## Verification` redundancy in some remediated skills (low priority, validator-clean).
- **DF-v24-7 added**: remaining code-search languages (Swift, Kotlin, etc.) + framework/parameter parity carried forward from DF-v23-4's broader scope.
- No `# DEVIATION:` markers were left in any artifact; the plan was followed as written.

## Next steps

- Phase 8 (live verification + release readiness): the four live-environment gaps (T036-T039 - live skill-eval-loop runs, eval-harness trigger techniques, Antigravity probe, macOS/Linux smoke) and the final catalog-green release-readiness gate (T040).
- The host now has a working tree-sitter install and Git bash is the way to run the hook-subprocess suites locally; fold both into any Phase 8 verification.
- WN-v24-1 (stale "230 skills" prose + pushy-description allowlist reconciliation) remains for the version bump.
