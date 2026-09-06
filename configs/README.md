# configs/

Repo-internal configuration sources. Nothing in this directory is copied to an end user's machine as-is; each file is either read by the installers, consumed by a generator, or offered as a template a user copies deliberately.

| File | Role |
|------|------|
| `platform-defaults.json` | **Source of truth** for per-platform install-time behavioral defaults. Derived artifacts are generated or read from it. |
| `org-bundle.schema.json` | JSON Schema for an organization-maintained knowledge bundle's `org.json` manifest. |
| `examples/org-bundle-example/` | Minimal organization bundle that validates against the schema and demonstrates core, rule, and reference layers. |
| `permissions/*.json`, `permissions/*.toml` | Per-provider permission templates a user copies into their own settings. Not generated. |

---

## Organization knowledge bundles

An organization knowledge bundle is an external directory or git repository containing the organization's coding standards, safety rules, CI/CD framework, naming conventions, documentation style, branching strategy, and testing requirements. Nexus-Hub ships the contract, validator, and a deliberately generic example; an organization's actual content remains outside this repository and is never added to the company-neutral catalog.

The bundle root contains an `org.json` manifest with this shape:

| Key | Type | Required | Default | Meaning |
|-----|------|----------|---------|---------|
| `schema_version` | integer | yes | - | Contract version. Phase 1 supports only `1`. |
| `org_name` | string | yes | - | Human-readable organization name rendered with the standards. |
| `core` | relative path | yes | `core.md` | Always-on Markdown loaded into each supported instruction surface. The field remains required so the selected document is explicit. |
| `rules_dir` | relative path | no | `rules/` | Per-language or path-scoped Markdown rules, mirroring `catalog/rules/<language>/<topic>.md`. |
| `references_dir` | relative path | no | `references/` | Detailed standards loaded on demand rather than placed in every prompt. |
| `precedence_statement` | string | no | Nexus-Hub default at render time | Organization-specific conflict-resolution wording. |

Unknown manifest keys produce a validator warning rather than an error so a newer bundle can be inspected by an older Nexus-Hub release. Required keys, declared types, relative-path containment, referenced paths, and UTF-8 readability are enforced without a third-party JSON Schema dependency.

### Content budget and layout

Keep `core.md` below 200 lines. [Anthropic recommends keeping CLAUDE.md files concise and under 200 lines](https://code.claude.com/docs/en/memory); always-loaded instructions consume context on every request and become less reliable as unrelated detail accumulates. The validator reports a warning when the core exceeds this budget but never truncates organization content.

Use three layers:

1. Put universal, binding requirements in the always-on `core.md`.
2. Put language-specific or path-scoped standards under `rules/<language>/`.
3. Put detailed procedures, examples, and frameworks under `references/` for on-demand loading.

Start from [`examples/org-bundle-example/`](examples/org-bundle-example/). Validate it or another bundle through `scripts.lib.integrations.org_knowledge.validate_bundle`; the `nexus-hub org connect` CLI will expose that validator in Phase 2 of v3.17.4.

Everything under `configs/` remains repo-internal. The schema and example are not copied as an organization's live policy, and connecting an organization bundle never modifies the source bundle.

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

### Install-time seeding (v3.16.0 Phase 3)

Beyond generating repo artifacts, a declared platform can have its default seeded into **its own config file** at global-install time. That work is done by `scripts/lib/integrations/platform_defaults.py`, invoked from `IntegrationBase.install()` for every registered integration.

Each platform declares an `install_target` describing what happens to it:

| `mode` | Meaning |
|---|---|
| `write` | Seed the declared settings into `path` using `format`. |
| `already-delivered` | An existing installer path already carries the values (Claude, whose `~/.claude/settings.json` is copied from the derived template). Seeding would race that copy. |
| `not-writable` | The lever is declared for the record but deliberately not written. `settings` is empty and `install_target.reason` says why. |

Three rules govern every write, and each exists because the alternative is hostile:

1. **Seed-if-absent, never overwrite.** A key the user already set is left exactly as they set it. A reinstall must never quietly reset someone's effort level back to the shipped default.
2. **Never destroy what we did not write.** TOML is edited through `tomlkit`, which round-trips comments and layout. YAML existing files are only ever **appended** to, because a plain PyYAML round-trip silently strips every comment; a declared key whose top-level parent already exists is skipped rather than merged, since appending a duplicate mapping would silently win or error depending on the reader.
3. **Degrade, never fail.** A missing source, a missing optional dependency, or an unreadable target config results in a skipped seed and a one-line note on stderr. An install must not break because a default could not be written.

Claude's `already-delivered` path has one precedence-specific refinement: the global installers treat `effortLevel` and `env.CLAUDE_CODE_EFFORT_LEVEL` as one upgrade pair. If either lever already exists, the pair's exact shape is user-owned and the missing partner is not added; only a config with neither lever and an absent or object-shaped `env` receives both declared defaults. A malformed user-owned `env` is preserved and cannot receive the nested default, with a warning when that shape blocks fresh effort-pair seeding. Without that rule, adding the higher-precedence env key beside an existing scalar would pin future sessions past the VS Code effort toggle even though no existing byte was overwritten.

Two further gates apply, both learned the hard way during Phase 3:

- **Undetected platforms receive nothing.** Seeding is gated on `result.detected is not False`. Creating a config file for software the user does not have installed is worse than shipping no default. The `is not False` form matters: `WriteResult.detected` is `Optional[bool]` where `None` means "not detection-gated at all".
- **`~` resolves through `Path.home()`**, never `os.path.expanduser`. The test suite isolates installs by patching `Path.home()`, and `expanduser` escapes that patch by reading the process environment.

**Optional dependencies**: `tomlkit` (TOML targets) and `PyYAML` (YAML targets). Both are lazily imported. Without them the affected platforms skip seeding with a `pip install` hint; JSON platforms are unaffected. Both installers check for them alongside the existing `python-docx` / `python-pptx` check.

### Choosing a value to seed

Seed conservatively, and record why in the entry's `rationale`:

- **Effort scalars** are seeded to `medium`, with Claude Code the deliberate exception at `high` (v4.4.0). Any departure from `medium` states its reason in that platform's `rationale`.
- **Approval-policy keys** are seeded toward the approval-required direction, or to the vendor's own documented default where one exists.
- **Model pins** are seeded ONLY where the vendor documents a safe self-selecting value (currently just Copilot's `model: "auto"`). A provider-scoped model id the user's account cannot reach would break their tool, so where no safe value is documented the key goes under `omitted` with the reason instead. Inventing one is the exact failure this file exists to prevent.

### Adding a platform

1. Find the lever in that platform's **own** official documentation and fetch the page.
2. Record the classification in `docs/policy/platform-defaults-levers.md` with the URL, what the document states, and the date.
3. Add the platform entry here, keyed by its integration-registry id, with `source_url`, `verified`, `doc_statement`, `settings`, `rationale`, and `derived_artifacts`.
4. Make the platform's integration consume the declared values at its real write surface. Never synthesize a config file for a platform whose only surface is an instruction file; record it as declared-but-not-writable instead.
5. Run `python scripts/sync_platform_defaults.py --apply`, then `make validate` and `make test`.

If the platform documents no such lever, that is a valid and expected outcome: record it as UNVERIFIED in the lever contract and add nothing here.
