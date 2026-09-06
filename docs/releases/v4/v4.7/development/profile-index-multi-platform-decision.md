# Decision Note - How does the profile index hold more than one platform roster?

**Plan**: `docs/releases/v4/v4.7/plans/v4.7.0-adoption-gpt-6-astra-prompting.md`, sub-task 3.2 (T047)
**Date**: 2026-09-05

## Context

`assets/profiles-index.json` (schema 1.0.0) records one `platform`, one `roster`, and one `roster_hash` in its `meta` block; the structural validator recomputes the hash from that roster, the freshness checker compares it against a live roster, and the writer re-stamps it on every write. Profiling `gpt-6-astra`, an OpenAI model, into a Claude-only index would either rewrite the Claude roster or fail the hash check.

## Options

- **(a) Bump the schema minor and add an optional `meta.platforms` array** of `{platform, roster_source, roster, roster_hash, last_verified}` entries, keeping the legacy single-platform keys for the primary platform. Each `models.<id>` entry already carries its `platform`. Readers without `--platform` behave exactly as before.
- **(b) One index file per platform.** Clean separation, but every reader, the orphan audit, the installer's flattened layout, and both test suites key on one index path; the change touches more surfaces for the same information.
- **(c) Replace the single-platform keys with the array (major bump).** Breaks every 1.0.0 reader and the shipped seed at once, for no gain over (a).

## Decision

**(a).** `schema_version` becomes `1.1.0`. `meta.platforms` is optional; the validator accepts it, validates each entry with the same roster and hash rules as the legacy block, and rejects duplicate platform ids or a mismatched per-platform hash. The writer records a write for the primary platform in the legacy keys (unchanged behavior) and a write for any other platform as an upserted `platforms` entry whose roster is the live roster supplied, widened to cover the models profiled on that platform (the layer's existing invariant: the index never claims a model it has no roster entry for). The freshness checker and the planner gain `--platform <id>`; without it they read the legacy keys. `references/schema.md` documents the field.

## Consequences

- Every 1.0.0 caller keeps working: the four readers were updated in the same change and the existing test suites pass unchanged.
- A per-platform entry can drift independently and is reported per platform by `check_model_prompting_freshness.py --platform <id>`.
- The Codex entry written by this plan records the live `codex debug models` roster on 2026-09-05 (six ids) widened by `gpt-6-astra`, which the vendor catalog lists but the Codex CLI does not yet enumerate; that entry therefore reads DRIFTED against the CLI until Codex lists the model. Recorded as a known gap.
