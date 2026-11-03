# Decision: Omitted Defaults Are Never Seeded

Status: implemented - a test fails when any platform's declared `settings` include a key that its own `omitted` map names, so a "do not seed" decision is enforced instead of being a comment.

Maintainers editing `configs/platform-defaults.json` read this before seeding a key that a platform lists under `omitted`. It records why the guard lives in a test, what it covers, and the limit it accepts.

**Date**: 2026-10-15 (decided at the v4.14.5 plan review). **Release**: v4.14.5.

## Problem

`configs/platform-defaults.json` records, per platform, the vendor-documented keys Nexus-Hub deliberately does not seed under `omitted`, each with a reason. Only one test read that map (`test_omitted_keys_state_why_they_were_not_seeded`), and it checked the reason text, not the relationship to `settings`. A contributor could declare a key under `settings` that the same platform lists under `omitted`, and the seeder would write it on every user's machine while the file still said "not seeded". The seeder already writes nested tables (`_leaf_paths` in `scripts/lib/integrations/platform_defaults.py`), so a dotted omitted key such as `memories.extract_model` is reachable. The Codex memory keys recorded in v4.14.5 are the first set whose omission is a safety and privacy decision, which made the gap worth closing for all fourteen platforms at once.

## Decision

- **A pure guard.** `omitted_keys_declared(platforms)` in `tests/validators/test_sync_platform_defaults.py` returns every `(platform, key)` pair where the platform declares a path that equals an omitted key or starts with it followed by `.`. Table nodes count, and an empty table over an omitted child (`{"memories": {}}` against `memories.extract_model`) is reported, because the seeder would write the bare table.
- **Real file and per-key red cases.** `test_no_platform_declares_a_key_it_omits` runs the guard over the file loaded with the seeder's own `load_source`, so an unreadable file fails instead of passing empty. `test_guard_catches_each_omitted_key` declares each omitted key of the real file in an in-memory copy and asserts the guard reports exactly that pair.
- **The seeder's own path rule.** Paths come from the seeder's `_leaf_paths`, imported, so the guard and the writer cannot disagree about what a nested table declares.
- **A stated rule in the source.** `meta.omitted` in `configs/platform-defaults.json` says an omitted key is never declared under `settings`, and that seeding one later means removing it from `omitted` in the same edit with a decision record.

## Alternatives considered

Rejected alternative: check inside `sync_platform_defaults.py --check`. That command validates derived artifacts against `settings`, owns no view of `omitted`, and Codex has no derived artifacts. Extending it would make the generator police a convention it does not use, and the guard still needs fixtures in a test file.

Rejected alternative: refuse at install time in the seeder. The failure would surface on a user's machine after a release instead of in the contributor's CI run, and the seeder is deliberately fail-soft (`seed_platform_defaults` never raises).

Rejected alternative: a pinned never-seed list in the test (declined 2026-10-15). A second list that must be edited beside `omitted` drifts from it; the `omitted` map is already the declaration, and the guard reads it directly.

Rejected alternative: do nothing and rely on review. The omission of Codex's memory keys is a privacy and plan-availability decision that a later edit could reverse silently in a one-line settings change.

## Consequences

- **Boundary: declared settings only.** The guard does not see keys an integration writes in code (for example the agent TOML in `scripts/lib/integrations/_codex_native.py`), profile-scoped keys such as `[profiles.<name>.memories]`, or environment variables. The Codex configuration reference read on 2026-10-29 documents no profile-scoped `memories` override, though the page tail was truncated, so the absence is an observation.
- **Documented limit.** Deleting an `omitted` entry in the same edit that seeds the key passes the test. The `meta.omitted` rule and review cover that case; a pinned list would close it and was declined above.
- **No setting changes.** The guard reads existing data. It changed no platform's seeded value, and the real file passes on every platform without a suppression.
- **Table-node reading.** An empty declared table over an omitted child is a violation, but a non-empty table that only contains the omitted key's parent is not; only its leaves can violate.
- **Cost.** New tests in an existing file already collected by the `validate` job; no new command, dependency, environment variable, or test path.
