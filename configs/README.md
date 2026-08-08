# configs/

Repo-internal configuration sources. Nothing in this directory is copied to an end user's machine as-is; each file is either read by the installers, consumed by a generator, or offered as a template a user copies deliberately.

| File | Role |
|------|------|
| `platform-defaults.json` | **Source of truth** for per-platform install-time behavioral defaults. Derived artifacts are generated or read from it. |
| `permissions/*.json`, `permissions/*.toml` | Per-provider permission templates a user copies into their own settings. Not generated. |

---

## platform-defaults.json

`configs/platform-defaults.json` is the single place a maintainer edits a per-platform install-time behavioral default. Every consuming artifact is derived from it, so one edit propagates on the next generator run, and a guard fails the build when any derived artifact drifts away from the declared value.

### Why this file exists

`catalog/hooks/settings.json` plays two roles at once: it declares Claude's install defaults AND it is the artifact copied to a user's `~/.claude/settings.json`. Because there was no separate source to point at, the same three values were copy-pasted into `scripts/lib/integrations/claude.py` for the `nexus-hub init` project stub. The v3.15.5 effort-level change consequently had to edit four declarations across two files and correct four documentation surfaces that restated the value as prose. This file resolves the dual role without changing what the installers consume: they still read `catalog/hooks/settings.json` exactly as before.

### Rules

1. **Edit here, never in a derived artifact.** `catalog/hooks/settings.json`'s core keys and the `nexus-hub init` stub are DERIVED. Hand-editing either is what the drift check exists to catch.
2. **Do not invent a lever.** A platform appears in this file ONLY when a specific official vendor document names the setting, recorded with `source_url` and a `verified` date. Never seed from a blog post, a forum, an aggregator, or an analogy to another platform. Nexus-Hub has made this mistake before: the `.kimi/agent.yaml` companion was fabricated and had to be dropped in v3.15.0.
3. **Declare env counterparts alongside their scalar.** Where a platform exposes both a scalar setting and an environment variable for the same behavior, the env value commonly outranks the scalar. Declaring only one leaves the other silently winning.
4. **Behavioral defaults only.** File-discovery paths and platform capabilities belong to `docs/policy/platform-read-contracts.json`. Neither document should grow into the other.
5. **Platform ids must match the registry.** Keys under `platforms` are the ids from `scripts/lib/integrations/__init__.py::_register_builtins`, so an entry maps to its integration with no translation table.

### Schema

Top level:

| Key | Type | Meaning |
|-----|------|---------|
| `schema_version` | integer | Bumped on a breaking shape change. Currently `1`. |
| `meta` | object | Purpose, authority, scope boundary, the do-not-invent rule, generator commands, and `last_updated`. |
| `platforms` | object | Keyed by integration-registry platform id. |

Per platform:

| Key | Type | Required | Meaning |
|-----|------|----------|---------|
| `display_name` | string | yes | Human-readable platform name. |
| `source_url` | string | yes | The official vendor document that names the lever. |
| `verified` | string (`YYYY-MM-DD`) | yes | The date that URL was fetched and the lever confirmed. |
| `doc_statement` | string | yes | What the document actually says, so a reader can audit the claim without refetching. |
| `settings` | object | yes | The literal keys and values, named exactly as the platform names them. Nested objects (such as `env`) are allowed. |
| `rationale` | object | yes | Per-key reasoning for the chosen value. Prefer the platform's own documented default unless Nexus-Hub has a specific reason to differ. |
| `derived_artifacts` | array | yes | Every artifact that consumes this platform's settings. Drives the generator and the drift check. |

Per derived artifact:

| Key | Type | Meaning |
|-----|------|---------|
| `path` | string | Repo-relative path. |
| `format` | string | `json`, `python`, and so on. |
| `strategy` | string | `merge-keys` (generator writes the listed keys in place) or `runtime-read` (the artifact reads this file itself; nothing is generated). |
| `keys` | array of string | Dotted paths into `settings`, for example `env.CLAUDE_CODE_EFFORT_LEVEL`. These are the keys the check compares and the generator writes. |
| `note` | string | Why this artifact is handled the way it is. |
| `fallback_symbol` | string | `runtime-read` only. The module constant holding the offline fallback, which the check verifies still equals the declared values. |

### Using the generator

```bash
python scripts/sync_platform_defaults.py --check    # fail on drift (runs in `make validate` and CI)
python scripts/sync_platform_defaults.py --apply    # rewrite derived artifacts from this file
```

`--apply` is idempotent: running it against an already-synced tree produces byte-identical files. It updates only the declared keys in place and preserves each file's existing key order, indentation, and line-ending convention, because `catalog/hooks/settings.json` also carries the full hook registration chains and a fresh serialization would destroy them.

`scripts/sync_platform_defaults.py` is a **repo-internal guard**. It has no meaning on an end-user install, so it is listed in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py` and requires no installer copy step. Both installers stay untouched.

### Adding a platform

1. Find the lever in that platform's **own** official documentation and fetch the page.
2. Record the classification in `docs/policy/platform-defaults-levers.md` with the URL, what the document states, and the date.
3. Add the platform entry here, keyed by its integration-registry id, with `source_url`, `verified`, `doc_statement`, `settings`, `rationale`, and `derived_artifacts`.
4. Make the platform's integration consume the declared values at its real write surface. Never synthesize a config file for a platform whose only surface is an instruction file; record it as declared-but-not-writable instead.
5. Run `python scripts/sync_platform_defaults.py --apply`, then `make validate` and `make test`.

If the platform documents no such lever, that is a valid and expected outcome: record it as UNVERIFIED in the lever contract and add nothing here.
