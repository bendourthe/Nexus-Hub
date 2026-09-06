# Session History -- v3.2.0 adoption-headroom Phase 1: Foundation + SmartCrusher

**Date**: 2026-06-09
**Plan**: [`docs/releases/v3/v3.2/plans/adoption-headroom.md`](../../plans/adoption-headroom.md)
**Phase**: 1 of 7 -- Foundation + SmartCrusher (re-full)
**Branch**: `feat/adoption-headroom` (off the post-teach `develop` merge `8523281`)
**Outcome**: complete; all four sub-tasks (T001-T004) closed, all quality gates green (GO).

## Goal

Stand up the internal, local-first `extensions/nexus-context-compressor` package, register it in both installers, and ship the first deterministic strategy -- `SmartCrusher` JSON-array dedup emitting reversible CCR markers. This is the reverse-engineer-first internal build that will eventually replace the external `rtk` context-compression binary.

## Subtasks completed

1. **T001 -- Package scaffold.** Created `extensions/nexus-context-compressor/` modeled structurally on `nexus-skill-scanner` (src/ layout, hatchling build, frozen dataclasses, `tests/conftest.py` putting `src/` on `sys.path`): `pyproject.toml` (Python 3.10+, `tiktoken` the only required dependency, optional `ml`/`code`/`dev` extras), `__init__.py` exposing `compress(messages, model=...) -> CompressResult` as a Phase-1 no-op pipeline, `types.py` (`CompressResult` with token metrics + `ratio`/`reduction`), `tokens.py` (offline-safe counter), a `transforms/` subpackage marker, `__main__.py`, README, and a 6-test scaffold suite.
2. **T002 -- Installer registration.** Added a copy + editable-install block for the package into the shared `mcp-server-venv` in both `scripts/installer.sh` and `scripts/installer.ps1`, modeled on the `nexus-web-fetch` sibling. No MCP-server registration (deferred to Phase 4 T013).
3. **T003 -- SmartCrusher.** Implemented `transforms/smart_crusher.py`: deterministic, dependency-free JSON-array dedup with a global-uniqueness + adjacent-change distinctiveness score, positional anchors, a budget cap, and reversible `<<ccr:HASH N_rows>>` markers backed by a stable SHA-256 content hash. Added a top-level `smart_crusher.py` shim for the `python -m` gate command.
4. **T004 -- Tests + stabilization.** 13 SmartCrusher tests (19 total) covering every stability-gate assertion plus a lossless-accounting invariant, non-adjacent dedup, the budget cap, determinism, and the CLI. All green; `make validate` emulated green; ShellCheck clean on the installer edits.

## Key decisions

- **Token counting: required tiktoken + offline stdlib fallback.** The plan names `tiktoken` the only required runtime dep, which sits in tension with the package's zero-outbound ethos (tiktoken's first-use vocab fetch is an outbound call). Reconciled by declaring tiktoken required for accuracy but implementing `count_tokens` to degrade to a deterministic stdlib regex estimate when tiktoken or its cached vocab is unavailable -- the package never *requires* a network call, and the one-time vocab fetch carries no user data (the same offline-first posture as the v3.0.0 OSV.dev DB and the Phase 6 ML weights).
- **Distinctiveness scoring: global uniqueness + adjacent change (research-informed).** Per the maintainer's request, researched how production engines do this before committing. The headroom architecture doc revealed it uses SimHash near-dup fingerprinting + Kneedle auto-sizing, with the kept budget K split 30%/15%/55% (start/end/importance) -- confirming the cap dominates the positional rule. The decisive lesson: pure adjacent comparison fails on `A,B,A,B` repetition, so the score blends GLOBAL uniqueness (content seen earlier -> 0, a drop candidate) with ADJACENT change magnitude (novel records ranked by fields changed), which also makes `variance_threshold=2.0` a meaningful near-duplicate cutoff. SimHash/Kneedle were deliberately left out of the v1 deterministic port (DF-v32hr-1/2).
- **Exact-content dedup for v1 (lossless), near-dup deferred.** SmartCrusher dedups on exact canonical content; a record differing only in a volatile field is kept unless its adjacent field-change falls below the threshold. Fuzzy near-dup is deferred (DF-v32hr-1) -- CacheAligner (Phase 3) normalizes dynamic fields and removes most of the noise that defeats exact dedup, and the Phase 5 harness can then measure a fingerprint pass.
- **`previous = record` always.** Resolved an earlier hesitation about mixing dict and non-dict records mid-array: `_field_change_count` handles mixed types, so the predecessor is always advanced unconditionally.

## Test results

- Package suite: **19 passed** (`PYTHONPATH=src python -m pytest -q`). 6 scaffold + 13 SmartCrusher. Coverage of the stability gate: 1000 identical -> 2 kept + 1 marker (<=3); 12-record high-variance array preserved verbatim; CCR hashes stable across two runs; `CrushResult` metrics correct; plus a lossless-accounting invariant (`kept_count + sum(dropped span counts) == original_count`), non-adjacent `A,B,A,B` dedup, the budget cap (60 distinct -> <=15 kept), mixed types, determinism, marker-format regex, and the `--demo` CLI.
- Stability-gate command: `python -m nexus_context_compressor.smart_crusher --demo` -> `100 -> 5 kept + 4 CCR marker(s)` (<=15 representative items, with markers). The documented command works verbatim via the top-level shim.
- `make validate` emulated (each validator invoked directly; `make` unavailable on host): catalog JSON parses (skills.json unchanged at 251 -- this phase adds an extension, not a skill), `validate_skills.py --bundles-only` PASS, `check_version_sync.py` consistent at canonical 3.1.1, and `validate_unicode_safety.py` / `validate_no_personal_paths.py` / `scan_supply_chain_iocs.py` / `validate_workflow_security.py` all exit 0 with **zero warnings in the new package** (the unicode WARNs are pre-existing AGENTS.md em-dashes).
- `make lint` (ShellCheck): **clean** -- this phase has a shell surface (the installer.sh edit), so `bash -n` + `shellcheck -S error` were run; both pass. The installer.ps1 edit passes a PowerShell tokenizer parse.

## CI/CD edits

- None. The `validate` job re-runs the same validators. The package auto-distributes via the installer blocks added in T002 (the editable install runs on the CI/install path). No new GitHub Actions workflow, env var, or top-level `scripts/<name>.py` artifact, so no `scripts/installer.*` copy-by-name step beyond the package block was needed.

## Deviations

Two plan inconsistencies were caught in the pre-implementation review and handled in-flight:

1. **Installer auto-copy assumption (T002).** The plan assumed `extensions/` is copied recursively so the package auto-distributes. Tracing both installers disproved this -- each extension has its own explicit copy + editable-install block. Surfaced to the maintainer (ask-first installer gate); per their choice, added a matching explicit block in both installers.
2. **Stability-gate module path (T003).** The gate names `python -m nexus_context_compressor.smart_crusher`, but T003's prompt places the file at `transforms/smart_crusher.py` (a deeper module path). Added a thin top-level `smart_crusher.py` shim that re-exports the strategy and provides the `-m` entry, so the documented command works verbatim while the implementation stays under `transforms/`.

Neither changes plan scope; both are recorded here and in the DEVLOG.

## Troubleshooting / environment notes

- `make` and `shellcheck` are not on PATH on the Windows dev host, so `make validate` was emulated by invoking each validator directly; ShellCheck for the installer edit was run via the `shellcheck` binary that *is* available to the Bash tool (`-S error`, clean). (WN-v32-2, re-confirmed; covered by CI.)
- The Bash tool's working directory persists between calls: an early `cd extensions/nexus-context-compressor` left subsequent relative `cd` calls failing until paths were recomputed from the new cwd. Resolved by running with `PYTHONPATH=src` from the package dir.
- tiktoken IS installed and cached on this host, so `python -m nexus_context_compressor` reports `token counter: tiktoken`; the stdlib-fallback path is independently covered by a test that exercises `_estimate_tokens` directly.

## Known gaps

See [`docs/releases/v3/v3.2/known-gaps.md`](../../known-gaps.md). **3 new DF this phase**, 0 resolved; 6 open total (3 DF + the 3 carried-over teach WN). DF-v32hr-1 (fuzzy near-duplicate fingerprinting), DF-v32hr-2 (information-theoretic auto-sizing of the keep budget), and DF-v32hr-3 (explicit error/outlier preservation) are all intentionally out of scope for the v1 deterministic port and are referenced from the SmartCrusher docstring; each has a suggested follow-up tied to Phase 3 (CacheAligner / ContentRouter) or the Phase 5 accuracy harness.

## Next steps

- **Phase 2 (CCR reversible store)**: implement the local SQLite-backed store (`ccr/store.py`) keyed by the CCR marker hash, plus the retrieval interface (`ccr/retrieve.py`) that resolves a `<<ccr:HASH N_rows>>` marker back to the original dropped records. `CrushResult.dropped` (the `CCRSpan` list) is already the store's input -- SmartCrusher emits exactly what Phase 2 persists.
- **Commit + push**: commit Phase 1 on `feat/adoption-headroom` and push the branch (its first commit makes the branch real on origin).
