# Per-Model Prompting Profile Layer: Schema

This file is the contract for the per-model prompting profile layer that ships inside this skill's bundle. Two artifacts make up the layer, and one of them is authoritative:

| Artifact | Role | Authoritative? |
|---|---|---|
| `assets/profiles-index.json` | Machine-readable index: the verified roster, the freshness marker, and every claim for every profiled model | Yes |
| `references/models/<model-id>.md` | Human-readable mirror of one model's entry, read on demand as Tier-3 reference | No (mirrors the index) |

The index is authoritative because the validator, the staleness checker, the research engine, and the edit-routing classifier all read it programmatically. The Markdown profiles exist so a human (or an agent that has already decided a model matters) can read one model's guidance without parsing JSON. When the two disagree, the index wins and the Markdown file is regenerated from it.

## Why this layer exists

Model-specific prompting guidance must never land in a shared catalog body (a `SKILL.md`, a command, a `base-*.md` template). A shared body is distributed verbatim to every platform, so a line naming one model becomes wrong the moment a reader is running a different one, and `scripts/check_base_template_parity.py` fails the build when such a line diverges across the five `base-*.md` templates. This layer is where model-specific guidance lives instead: bundled under the skill, distributed as Tier-3 on-demand reference by the installer's recursive skill-folder copy, and never inlined into a shared body.

## Index schema (version 1.1.0)

### Top level

Exactly three keys. Unknown top-level keys are a validation error, because this is a versioned contract that tooling reads by key.

| Key | Type | Rule |
|---|---|---|
| `schema_version` | string | Semver. Bump the minor when adding an optional field, the major when changing or removing one. |
| `meta` | object | Roster provenance and the freshness marker. See below. |
| `models` | object | Map of model id to that model's profile entry. At least one entry. |

### `meta`

| Key | Type | Rule |
|---|---|---|
| `last_verified` | string | `YYYY-MM-DD`. The date the roster and claims were last confirmed. |
| `platform` | string | Non-empty. The platform id the roster was enumerated from (for example `claude-code`, `codex`, `antigravity`). |
| `roster_source` | string | One of `api`, `picker`, `config`, `manual`. How the roster was obtained, so a reader can judge its provenance. `picker` means live API enumeration was unavailable and the roster was read from the platform's model picker. |
| `roster` | array of string | The model ids this layer was last verified against. Sorted ascending, unique, every entry non-empty. This is the full live roster, NOT only the profiled models. |
| `roster_hash` | string | 64-character lowercase hex. `sha256` of the sorted roster joined by a single newline (`"\n".join(sorted(roster))`), UTF-8 encoded. |

| `platforms` | array of object | OPTIONAL (schema 1.1.0, v4.7.0). One entry per additional platform whose models this layer profiles, each carrying `platform`, `roster_source`, `roster`, `roster_hash`, and `last_verified` with the same rules as the keys above. The legacy single-platform keys stay authoritative for the primary platform, so a Claude roster is never rewritten by research on another vendor's models; a write for a different platform upserts its entry here. `platform` values are unique within the array. Decision: `docs/releases/v4/v4.7/development/profile-index-multi-platform-decision.md`. |

The `roster_hash` is a self-consistency check, not a freshness check: the schema validator recomputes it from `meta.roster` in the same file and fails on a mismatch, which catches a hand-edit that added a model to the list without re-stamping the hash. Comparing the recorded roster against the *live* roster is a separate, advisory concern owned by `scripts/check_model_prompting_freshness.py`.

### `models.<model-id>`

| Key | Type | Rule |
|---|---|---|
| `platform` | string | Non-empty. The platform this model was profiled on. |
| `last_verified` | string | `YYYY-MM-DD`. Per-model, so one model can be refreshed without re-stamping the whole layer. |
| `claims` | array of object | At least one claim. See below. |

A model listed in `meta.roster` with no entry under `models` is an UNVERIFIED model, which is a legitimate and expected state (research has not reached it yet). The validator therefore does NOT require roster coverage; unverified models are surfaced as known-gaps entries by the research run instead. What the validator does require is a bidirectional match between `models` keys and `references/models/*.md` files: every profiled model has a Markdown mirror, and every Markdown mirror has an index entry.

### `models.<model-id>.claims[]`

| Key | Type | Required | Rule |
|---|---|---|---|
| `claim` | string | Yes | Non-empty. One discrete, testable statement about how to prompt this model. Not a paragraph of several claims. |
| `source_url` | string | Yes | Must start with `http://` or `https://`. The primary source that backs the claim (vendor docs, cookbook, system card, changelog), never a secondary summary. |
| `confidence` | string | Yes | One of `high`, `medium`, `low`, `unverified`. `unverified` means the claim has not yet survived the adversarial-verify pass and must not be acted on. |
| `scope` | string | Yes | One of `model-specific`, `model-agnostic-candidate`. Determines the write target. See the routing rule below. |
| `note` | string | No | Free text. Use it for a TODO, a caveat, or the reason a claim was scoped the way it was. |

## The scope field is the hard rail

`scope` is the single field that decides where a claim may be written:

- `model-specific` routes to this profile layer and nowhere else.
- `model-agnostic-candidate` becomes eligible for a proposed edit to a shared catalog body, and even then only behind the full guard suite on an isolated branch.

When scope is ambiguous, the correct value is `model-specific`. Defaulting to the profile layer is safe (a model-specific claim sitting in a profile is merely unhelpful to other models); defaulting the other way ships a model-specific line to every platform. The seed entry in `assets/profiles-index.json` is deliberately tagged `model-specific` to demonstrate this default.

## Markdown profile format

Each `references/models/<model-id>.md` mirrors one `models` entry and carries these sections in order:

1. An H1 naming the model id, plus the platform it was profiled on.
2. Verified prompting guidance as discrete claims, each with its primary-source URL and confidence tag.
3. A "does not apply to shared bodies" reminder, so a reader who copies a line out of the file knows the constraint travels with it.
4. The `last_verified` date.

The seed mirror is `references/models/claude-opus-5.md`. Use it as the template when the research engine writes a new one.

## Validation and freshness

Two repo-level scripts read this layer, and the split between them is deliberate:

| Script | Concern | Gate |
|---|---|---|
| `scripts/verify_model_prompting_profiles.py` | Structural validity of the index and its Markdown mirrors | HARD. Wired into `make validate` and CI; a malformed layer fails the build. |
| `scripts/check_model_prompting_freshness.py` | Whether the recorded roster still matches the live roster | ADVISORY. Never a blocking gate anywhere, so a vendor shipping a new model can never wedge a release. |

Both are stdlib-only and make no network call. The freshness checker is handed a live roster on argv by its caller, which is what keeps the network dependency in the agent's own web tool rather than in a script.

## Authoring notes for later phases

- Multi-platform reads (schema 1.1.0): `write_model_prompting_profile.py plan --platform <id>` plans against that platform's entry; `check_model_prompting_freshness.py --platform <id> <live ids>` compares that entry's roster. Without `--platform` both read the legacy keys, so every 1.0.0 caller keeps working unchanged.
- Every file under this bundle's `scripts/`, `references/`, and `assets/` directories must be referenced from `SKILL.md` (or from a `references/*.md` that is itself referenced), or the orphan-bundle audit in `make validate` warns. The `SKILL.md` scaffolded in Phase 2 must therefore reference `references/schema.md`, `assets/profiles-index.json`, and `references/models/claude-opus-5.md`. This file mentions the latter two by name, so a single `SKILL.md` reference to `schema.md` chains through to both.
- Adding an optional claim field is a minor `schema_version` bump plus a validator update in the same change. The validator rejects unknown keys on purpose, so a typo like `sources_url` fails loudly instead of being silently ignored.
