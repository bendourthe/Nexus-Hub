# Session History -- v3.2.0 adoption-headroom Phase 2: CCR reversible store

**Date**: 2026-06-09
**Plan**: [`docs/releases/v3/v3.2/plans/adoption-headroom.md`](../../plans/adoption-headroom.md)
**Phase**: 2 of 7 -- CCR reversible store (re-full)
**Branch**: `feat/adoption-headroom` (continuing from Phase 1)
**Outcome**: complete; all three sub-tasks (T005-T007) closed, all quality gates green (GO).

## Goal

Make the compression non-lossy. Phase 1's SmartCrusher already emits `<<ccr:HASH N_rows>>` markers and returns the dropped spans (`CrushResult.dropped`); Phase 2 persists those originals in a local store keyed by the marker hash and exposes a retrieval interface that resolves a marker back to the exact dropped records. Local SQLite only, zero outbound.

## Subtasks completed

1. **T005 -- CCR store + SmartCrusher wiring.** Added the `ccr/` subpackage. `ccr/store.py` is a local SQLite `CCRStore` mapping a span's content hash to its JSON-serialized originals: content-addressed idempotent `put(hash, original)` (`INSERT ... ON CONFLICT`), `get(hash) -> list | None`, `__contains__` / `__len__`, an oldest-first `prune(max_entries=..., older_than_seconds=...)` eviction primitive, WAL + busy-timeout for concurrent hook/MCP access, context-manager lifecycle, and a `default_store_path()` resolving `NEXUS_CCR_STORE_PATH` -> `NEXUS_HUB_ROOT`/cache -> `~/.nexus-hub/cache/ccr-store.db`. SmartCrusher is wired to it through **optional dependency injection**: `smart_crush(records, config, store=None)` persists each dropped span via `store.put` only when a store is passed.
2. **T006 -- retrieval interface.** `ccr/retrieve.py` exposes `retrieve(marker_or_hash, store=None) -> list | NOT_FOUND`. It parses a marker string, a marker object, or a bare hash, looks the hash up in the store, and returns the originals -- or the named `NOT_FOUND` singleton sentinel on a malformed marker or an absent/evicted span. It never raises (the documented hot-path contract): even an unopenable store path degrades to `NOT_FOUND`. With no store it opens a transient one at the default location.
3. **T007 -- tests + stabilization.** 49 new tests (68 total) across four files: the marker codec, the store (put/get/idempotency/prune/restart), retrieve (hit/miss/garbage/sentinel/transient), and the end-to-end round-trip. All green; 100% line coverage on `ccr/`; `make validate` emulated green.

## Key decisions

- **Store wiring via optional dependency injection, not a side-effecting `smart_crush`.** The plan's T005 says "wire SmartCrusher to call `put` when it drops a span", but Phase 1 documents and tests `smart_crush` as pure, deterministic, and dependency-free (`smart_crush(x).records == smart_crush(x).records`). Making it unconditionally open a SQLite file would break that contract, add a filesystem side effect to a function tested as side-effect-free, and invert the layering (a strategy reaching into the storage layer). Resolved with an optional `store` parameter: `store=None` (every existing test) stays pure; passing a store persists drops. The transform depends only on a tiny `CCRWriter` Protocol (`put(hash, original)`), not on the concrete SQLite class, so it stays decoupled and a test can inject a fake. A regression test (`test_result_is_identical_with_and_without_store`) pins that the returned result is byte-identical either way.
- **A shared marker codec (`ccr/marker.py`) as the single source of truth.** The producer (`_assemble` in SmartCrusher) builds the `<<ccr:HASH N_rows>>` string and the consumer (`retrieve`) must parse it. Rather than duplicate the format in two regexes that can drift, the codec owns both `format_marker` / `make_marker_object` and `parse_marker` / `extract_hash`. SmartCrusher's `_assemble` now calls `make_marker_object` instead of an inline f-string. The codec is a pure leaf (imports only `re`), so `transforms` importing it introduces no dependency cycle (`ccr` never imports `transforms`).
- **A named `NOT_FOUND` sentinel for retrieve, `None` for the low-level store.** The store's `get` returns `None`-on-miss (dict-like, per the T005 spec verbatim). The higher-level `retrieve` returns a dedicated falsy singleton with a self-describing repr (`<ccr:not-found>`), per the T006 "clear sentinel" requirement -- so a consumer branches on `result is NOT_FOUND`, unambiguous since a stored span is always a `list`. The slight asymmetry is intentional and spec-driven.
- **Eviction primitive now, eviction policy in Phase 4 (DF-v32hr-4).** A reversible store grows with every drop, so it needs a bound. `put` only inserts (keeping the hot path deterministic and IO-light); the store ships `prune()` (size cap + TTL, oldest-first by a `created_at` column) as an explicit, opt-in maintenance step. *Who* calls it and *when* belongs to the runtime that owns the store lifecycle, which does not exist until Phase 4 wires the hook + MCP -- so auto-scheduling is deferred and logged as DF-v32hr-4. A pruned span resolves to `NOT_FOUND`, which the consumer already handles.
- **WAL for concurrent access.** Phase 4 will have a PreToolUse hook writing the store while an MCP `retrieve` tool reads it. WAL journal mode + a busy timeout let a reader and a writer work the single local file without blocking each other.

## Test results

- Package suite: **68 passed** (`python -m pytest -q`). 19 Phase 1 + 49 Phase 2 (18 marker codec + 14 store + 11 retrieve + 6 round-trip). **100% line coverage on `ccr/`** (`--cov=nexus_context_compressor.ccr`: marker 100%, store 100%, retrieve 100%, `__init__` 100%).
- Stability gate (Phase 2): a compressed payload's CCR marker resolves back to the exact dropped records (`test_each_marker_resolves_back_to_exact_originals`); the full round-trip is lossless -- kept records + retrieved dropped records reconstruct the entire input (`test_round_trip_is_lossless`); the store survives a process restart by re-opening the same SQLite file (`test_store_survives_process_restart`, `test_round_trip_survives_a_store_restart`); a missing/evicted hash and a malformed marker both return `NOT_FOUND` without raising. SQLite only; no outbound call.
- `make validate` emulated (each validator invoked directly; `make` unavailable on host): catalog JSON parses (skills.json unchanged at 251 -- this phase adds extension code, not a skill), `validate_skills.py --bundles-only` PASS (0 errors), `check_version_sync.py` consistent at canonical 3.1.1, and `validate_no_personal_paths.py` / `validate_unicode_safety.py` / `scan_supply_chain_iocs.py` / `validate_workflow_security.py` / `validate_solution_frontmatter.py` all exit 0 with **zero warnings in the new package** (the unicode WARNs are pre-existing legacy template files).
- `make lint` (ShellCheck): **N/A** -- this phase added only Python + Markdown, no shell surface (WN-v32-2, re-confirmed).

## CI/CD edits

- None. The `validate` job re-runs the same validators. The `ccr/` subpackage auto-distributes via the Phase 1 installer copy + editable-install blocks (no new top-level `scripts/<name>.py` artifact, so no copy-by-name installer step). No new GitHub Actions workflow or env var.

## Deviations

- None that change plan scope. The optional-dependency-injection wiring (vs. a side-effecting `smart_crush`) is the faithful reading of "wire SmartCrusher to call put" that preserves the Phase 1 purity contract -- recorded under Key decisions, not a scope change. The shared `ccr/marker.py` codec is an addition within the `ccr/` package the plan names; it is the maintainable way to keep the producer's and consumer's marker grammar in lockstep.

## Troubleshooting / environment notes

- `make` and `shellcheck` are not on PATH on the Windows dev host (WN-v32-2), so `make validate` was emulated by invoking each validator directly; no shell surface this phase, so ShellCheck was not applicable.
- The Bash tool's working directory persists between calls; an early `cd extensions/nexus-context-compressor` made later relative `cd` calls fail, resolved by using absolute paths.
- An initial `Write` landed at the wrong path (`extensions/nexus_context_compressor/...`, missing the `nexus-context-compressor/src/` prefix); the errant directory was removed before writing to the correct `src/` location.
- A test used a literal non-ASCII `e`-acute to exercise the unicode JSON round-trip; rewritten as `chr(233)` so the source file stays ASCII-only (repo convention) while still testing the `ensure_ascii=False` path.

## Known gaps

See [`docs/releases/v3/v3.2/known-gaps.md`](../../known-gaps.md). **1 new DF this phase** (DF-v32hr-4: CCR-store auto-eviction scheduling deferred to the Phase 4 hook/MCP runtime; the `prune` primitive exists and is tested, only the policy/scheduling is deferred), 0 resolved; 7 open total (4 DF + 3 carried-over teach WN). The Phase 1 SmartCrusher deferrals (DF-v32hr-1..3) are unaffected.

## Next steps

- **Phase 3 (remaining deterministic strategies)**: CacheAligner (KV-cache prefix stabilizer), ContentRouter (content-type classify + dispatch), and the AST-aware CodeCompressor (reusing nexus-code-search tree-sitter). Any strategy that drops data now persists through the Phase 2 CCR store via the same `store=` injection seam.
- **Commit + push**: commit Phase 2 on `feat/adoption-headroom` and push the branch.
