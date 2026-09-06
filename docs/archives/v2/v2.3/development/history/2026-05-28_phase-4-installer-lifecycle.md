# Phase 4 -- Installer Lifecycle & Selective Install

**Plan**: [`docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md`](../../plans/adoption-ecc-cybersec-skills.md)
**Date**: 2026-05-28
**Status**: Closed
**Sub-tasks**: T010, T011, T012, T013

## Goal

Add an install-state manifest plus `doctor` / `repair` / `list-installed` lifecycle commands, selective-install profiles / modules with a `consult` advisor, and harness audit scoring -- all reverse-engineered onto the existing integration registry per the MCP Registry Policy reverse-engineer-first decision tree.

## What was built

### T010 -- Install-state manifest + doctor/repair/list-installed

The existing `scripts/lib/integrations/manifest.py::InstallManifest` was the right starting point: it already tracks paths per integration via `track()` / `untrack()`, and the runner already loads / saves it to `<target_root>/.nexus-hub/install-manifest.json`. The plan required recording per-file `FileAction`s so doctor could detect drift -- the additive design preserved every existing field and method.

Concretely, `manifest.py` gained:

1. Module-level helpers `_hash_path(path)` (SHA-256 of file content) and `_mtime(path)`.
2. A new instance field `_actions: Dict[str, List[Dict[str, object]]]` storing per-integration `{path, action, sha256, mtime}` records.
3. `record_actions(integration_key, file_actions)` -- iterate the iterable, capture hash + mtime at record time, replace any prior records for the key.
4. `actions_for(integration_key)` and `all_action_keys()` -- read accessors.
5. The `to_dict` / `from_dict` serializers were extended to round-trip `actions` alongside the existing `tracked` / `shared` / `logs` keys.

The runner's `cmd_install` now calls `manifest.record_actions(key, result.files)` after each successful install (skipped on `--dry-run`).

The new `scripts/lib/integrations/lifecycle.py` module is the home of three operations:

- `doctor(manifest, requested=None) -> DoctorReport`: walks the manifest's recorded actions, compares each recorded SHA-256 against the current on-disk bytes, and emits one of four diagnostics per file (`ok` / `missing` / `drifted` / `unknown` -- the latter for directory tree summary entries without a content hash). Entries with `action in {"not-found", "kept", "removed"}` are skipped because the runner did not own those files.
- `repair(ctx, requested=None) -> WriteResult`: runs doctor, filters to integrations whose report shows `missing` or `drifted` findings, and re-runs `integration.install(ctx)` so the marker semantics in `MarkdownIntegration._write_instruction` still apply (user edits outside the `<!-- nexus-hub:start -->...<!-- nexus-hub:end -->` markers stay; edits inside are overwritten -- the existing behavior). The new actions are re-recorded via `record_actions` so the next doctor reflects the repair.
- `list_installed(manifest) -> Dict[str, List[dict]]`: pure data accessor returning the per-integration action list.

Three new subcommands on `scripts/lib/integrations/runner.py`:

- `doctor [--target] [--integrations] [--json] [--quiet]` -- prints a counts summary and a per-file diagnostic table; exits 1 if any `missing` or `drifted` finding exists.
- `repair [--scope] [--target] [--integrations] [--project-name] [--dry-run] [--quiet]` -- re-installs drifted/missing integrations and persists the new manifest.
- `list-installed [--target] [--json]` -- enumerates the recorded files in either text or JSON form.

### T011 -- Selective install profiles / modules + consult advisor

`data/bundles.json` bumped from schema 1.3.0 to 1.4.0. Two new top-level keys:

- `profiles`: `minimal` (just `core-developer`), `core` (`core-developer` + `qa-engineer` + `pr-workflow` + `testing` + `code-review` modules), and `full` (everything). The `full` profile carries `"all": true` for clarity.
- `modules`: six capability-tagged groupings (`testing`, `code-review`, `security-ops`, `ai-engineering`, `infrastructure`, `documentation`), each with a `capability:` tag and an explicit `skills` list drawn from the existing catalog.

The existing `bundles` array is untouched so every existing consumer (the marketplace, the existing `bundles[]` schema, downstream tools) keeps working byte-identical.

The new `scripts/nexus_hub_consult.py` is the natural-language advisor:

- `tokenize(text)` -- regex tokenizer with a small stopword list and a 2-char minimum.
- `load_candidates(kinds)` -- reads `data/skills.json` and `data/bundles.json`, returns a uniform list of `Candidate(kind, id, name, description, tags, install_hint)` records.
- `score_candidate(query_tokens, candidate)` -- baseline scorer: token overlap + 2.0 boost when a token matches the candidate's `id` exactly + 1.0 boost per tag match. The `id`-exact and tag boosts are simple but effective; the actual ranking heuristic is marked as a user-contribution slot for future tuning (IDF, field weighting, embeddings).
- `consult(need, kinds, top)` -- end-to-end pipeline. Sorts descending by score, returns the top N.
- `main(argv)` -- argparse CLI with `--kind`, `--top`, `--json`. Exits 0 on match, 1 on no match, 2 on missing catalog file.

### T012 -- Harness audit scoring

`scripts/harness_audit.py` is a deterministic, read-only scorer:

- `_audit_one(key, manifest, weights)` -- builds one `IntegrationAudit` per integration. Four axes:
    - `presence` = `(present + drifted) / (present + drifted + missing)` (degrades when files vanish)
    - `integrity` = `present / (present + drifted + missing)` (degrades when files drift OR vanish)
    - `coverage` = `recorded_surfaces / declared_surfaces` (degrades when an integration declares e.g. `commands_subdir` but the manifest has no path containing `commands`)
    - `marker_integrity` = `shared_intact / len(shared_files)` (degrades when a shared instruction file lost its marker pair)
- Each axis is in [0, 1]; the four are combined via weighted average using `DEFAULT_WEIGHTS = {presence: 0.30, integrity: 0.30, coverage: 0.20, marker_integrity: 0.20}`. The combine step is a user-contribution slot.
- The aggregate score is the mean of the per-integration scores.
- `main(argv)` -- argparse CLI with `--target`, `--integrations`, `--json`, `--min-score N`. Markdown by default, JSON on demand. `--min-score` causes exit 1 when the aggregate falls below the threshold so CI can gate.

### T013 -- Installer wiring + tests

`scripts/installer.sh` and `scripts/installer.ps1` register the two new standalone scripts (`nexus_hub_consult.py`, `harness_audit.py`) under the existing v2.3.0 CI-validator block in lockstep. Each is copied to `~/.nexus-hub/scripts/<name>`. The doctor / repair / list-installed surface itself ships through the existing `scripts/lib/integrations/` registry copy step (no new installer entry needed for those).

Three new pytest modules under `tests/integrations/`:

- `test_lifecycle.py` (13 cases): manifest round-trip, doctor reports `ok` after clean install, doctor flags `missing` after delete, doctor flags `drifted` after in-place edit, doctor handles unknown integrations, repair restores drifted files, repair is a no-op when clean, list_installed enumerates recorded entries, list_installed empty manifest returns empty dict.
- `test_consult.py` (12 cases): tokenizer behavior, candidate loader returns all kinds, profile / module filters, scorer zero on no overlap, scorer boosts id matches, scorer boosts tag matches, consult sort order, empty need handling, `--top` enforcement, main CLI exit codes, JSON output parseability.
- `test_harness_audit.py` (8 cases): empty manifest returns 0.0, clean install scores >= 80, drift penalizes integrity, missing files penalize presence + integrity, score is deterministic across runs, JSON output is parseable, `--min-score 200` exits 1, unknown-integration is skipped gracefully.

## Stability Gate

| Gate | Threshold | Status |
|---|---|---|
| Full integration suite | 0 failures | 191 passed / 0 failed |
| Contract suite (50 cases) | 0 failures | green |
| `make validate` | clean | 0 errors |
| New tests for new code | every new file has a test reference | 3 modules / 33 cases |
| Additive manifest guarantee | existing `_tracked` / `_shared` API unchanged | upheld |

## Implementation choices worth recording

1. **Additive manifest, not replacement.** The plan called for recording per-file `FileAction`s, but the existing `_tracked` dict (path-only) is what the 50-case contract suite is built on. Replacing it would have broken the suite. The chosen path -- a parallel `_actions` field that records the action vocabulary plus SHA-256 plus mtime -- gives doctor / repair / list-installed everything they need while leaving the legacy API surface untouched. This is the textbook expand-and-contract schema migration done in one deploy.
2. **Repair goes through `install()`, not a bespoke re-write loop.** The temptation when "repairing" a drifted file is to just overwrite it with the recorded content. That would break marker semantics on shared instruction files (CLAUDE.md, AGENTS.md): the user's edits outside the markers would be lost. Routing through `integration.install(ctx)` means `MarkdownIntegration._write_instruction` runs and `merge_marker_section` does the right thing automatically. The cost is that repair is slightly slower (re-renders templates, re-checks every file) -- acceptable for a recovery operation.
3. **User-contribution slots for the two scoring heuristics.** Both `consult.score_candidate()` and `harness_audit._audit_one()`'s combine step are marked as user-contribution slots with TODO comments explaining the trade-offs. The baselines work today and are tested -- but the right ranking algorithm for "match a need to skills" and the right weighting for "is this integration healthy?" both depend on domain priorities that the user is better positioned to set than the agent.
4. **`bundles.json` schema migration is additive, not breaking.** Adding `profiles` and `modules` as new top-level keys (rather than mutating the existing `bundles[]` array) keeps every existing consumer of the registry working byte-identical. The schema version bumped from 1.3.0 to 1.4.0 to mark the additive change.
5. **Pre-existing personal-path findings redacted.** Four pre-existing `/Users/<user>/...` findings in `docs/DEVLOG.md` (1) and `docs/archive/v2/v2.3/development/history/2026-05-28_phase-3-runtime-learning.md` (3) were redacted to `<user>` so `make validate` stays clean on the v2.3.0 tree. These predated Phase 4; the Phase 3 close note had flagged the redaction pattern.

## Known gaps added

None. The Summary counts in `docs/archive/v2/v2.3/known-gaps.md` are unchanged (5 open: 1 BG, 1 DF, 3 WN). The `Last updated` line records the Phase 4 close. The v2.2.0 carryover gaps continue to wait for Phases 7-9.

## CI/CD readiness

`make validate` invokes all four Phase 2 validators with the standard exclusion set and they pass on the new tree. CI's `pytest tests/integrations tests/integrations -v` step automatically picks up the three new test modules; no workflow edit needed.

## Files written / modified

Created:

- `scripts/lib/integrations/lifecycle.py`
- `scripts/nexus_hub_consult.py`
- `scripts/harness_audit.py`
- `tests/integrations/test_lifecycle.py`
- `tests/integrations/test_consult.py`
- `tests/integrations/test_harness_audit.py`
- `docs/archive/v2/v2.3/development/history/2026-05-28_phase-4-installer-lifecycle.md` (this file)

Modified:

- `scripts/lib/integrations/manifest.py` (added `_hash_path`, `_mtime`, `_actions`, `record_actions`, `actions_for`, `all_action_keys`; extended `to_dict` / `from_dict`)
- `scripts/lib/integrations/runner.py` (added imports from lifecycle; auto-record in `cmd_install`; new `cmd_doctor` / `cmd_repair` / `cmd_list_installed`; new parser subcommands)
- `scripts/installer.sh` (added copy steps for `nexus_hub_consult.py` and `harness_audit.py`)
- `scripts/installer.ps1` (mirror of bash block)
- `data/bundles.json` (schema 1.3.0 -> 1.4.0; added `profiles` and `modules` top-level keys)
- `docs/archive/v2/v2.3/known-gaps.md` (Status line advanced to "Phases 1-4 of 9 closed"; Last updated line records the Phase 4 close; Summary annotated as unchanged)
- `docs/archive/v2/v2.3/plans/adoption-ecc-cybersec-skills.md` (checked T010-T013 off and the Phase 4 Exit Checklist; flagged Phase 4 as "done" in Phases at a Glance)
- `CHANGELOG.md` (added six Unreleased entries: T010 manifest extension, T010 lifecycle subcommands, T011 profiles + modules, T011 consult advisor, T012 harness audit, T013 test coverage)
- `docs/DEVLOG.md` (added Phase 4 entry; redacted one pre-existing personal-path occurrence)
- `docs/archive/v2/v2.3/development/history/2026-05-28_phase-3-runtime-learning.md` (redacted three pre-existing personal-path occurrences)

## Test counts

- `tests/integrations/`: 158 passed (pre-Phase-4) -> 191 passed (post-Phase-4); +33 new cases; 0 failures, 0 skips, 0 errors.
- `tests/validators/`: 31 passed (no change).
- `catalog/hooks/tests/`: 392 passed + 3 skipped (no change).

## Next steps

Phase 5 (Skill quality tooling) is ready to start. The Phase 4 deliverables are an enabler for Phase 5's `skill-stocktake` (it can read the manifest to find which skills are actually installed) and for Phase 6's framework coverage matrix (it can use the install-state to scope which integrations to inspect for framework-tagged skills).
