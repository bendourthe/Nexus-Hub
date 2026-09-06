# Session History - v3.16.0 Phase 3: Wire the verified levers into the defaults and their consumers

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.0-platform-defaults-config.md](../../plans/v3.16.0-platform-defaults-config.md)
**Phase**: 3 of 5 (not the final phase)
**Branch**: `feat/platform-defaults-config`
**Outcome**: Complete. All four quality gates passed. Two defects found by the test suite and fixed in-phase.

## Goal

Declare every VERIFIED lever in `configs/platform-defaults.json` and make its platform's real write surface consume it, skipping every UNVERIFIED platform.

## Result

| Disposition | Platforms |
|---|---|
| **Written** at install time | `codex`, `copilot`, `cursor`, `gemini-cli`, `hermes`, `kimi`, `qwen` |
| **Already delivered** by an existing installer path | `claude` |
| **Declared, not writable** (reasons recorded) | `aider`, `antigravity2`, `opencode`, `openclaw` |
| **Absent** (UNVERIFIED) | `antigravity`, `gemini`, `nexus-ai`, `windsurf` |

**No installer copy step was required.** Both installers already route every platform through `runner.py install`, so a hook in `IntegrationBase.install()` reaches all of them. This was verified against the installers rather than assumed from AGENTS.md, whose "original 4 via legacy copy blocks" description is stale.

## Decisions

- **The hook lives in the dispatcher, not `install_global`.** Subclasses override `install_global`; one that forgot `super()` would silently skip its defaults.
- **Model pins were seeded almost nowhere, on purpose.** Effort and autonomy are seedable because vendors enumerate their values. Model ids are provider-scoped, and most vendors document their default as `undefined`. Exactly one model pin ships (Copilot's `model: "auto"`, documented as self-selecting); every other model key sits under `omitted` with its reason, so the refusal is legible rather than silent.
- **Autonomy seeds toward approval-required**: codex `on-request`, cursor `allowlist`, kimi `manual`, hermes write-approval gates on, gemini-cli left at the vendor's own documented default. Qwen deliberately differs from its vendor default of `auto` in favour of `default`, because tightening a default the user can loosen is the safe direction.
- **`tomlkit` over a plain TOML writer.** A user's `config.toml` carries their comments and layout; re-serializing it would be Phase 1's hooks-block hazard transplanted onto someone else's file.

## Test results

| Suite | Result |
|-------|--------|
| `tests/validators` | 527 passed |
| `tests/integrations` | 597 passed, 1 skipped |
| Coverage, the two defaults modules | **95%** (`platform_defaults.py` 88%, `sync_platform_defaults.py` 99%) |
| ShellCheck / `installer.ps1` AST parse | Clean |
| `validate` guards (7) + drift check | All pass |

**Throwaway-HOME install verification** was the most valuable check, because it exercised the merge against files another writer had already produced: `~/.qwen/settings.json` received the seeded keys alongside the large `hooks` block the qwen integration writes, and `~/.codex/config.toml` received them while preserving its pre-existing `[features]` table.

## Troubleshooting trail

Two defects, both caught by the integration suite rather than by review.

1. **Seeding escaped the test sandbox and wrote into the real home directory.** `_expand()` used `os.path.expanduser`, which reads `USERPROFILE` / `HOME` from the process environment, while the suite isolates installs by patching `Path.home()`. Four real files were created in the developer's home and removed (each contained only the Nexus-Hub banner and declared keys); the one genuine pre-existing user file, `~/.codex/config.toml`, was left untouched. Fixed by resolving `~` through `Path.home()`.
2. **Undetected platforms were seeded.** The hook ran unconditionally, so a detection-gated integration that had marked itself not-detected still received a config file -- meaning an install would create `~/.hermes/config.yaml` on a machine with no Hermes. Fixed with `result.detected is not False`; the `is not False` form is load-bearing, because `detected=None` means "not detection-gated at all" and truthiness would have wrongly suppressed codex, cursor, and claude.
3. **Aider was declared writable and should not have been.** Its own `install_global` docstring says `~/.aider.conf.yml` is a surface Nexus-Hub does not touch, and it performs no Aider detection. Reclassified to not-writable per the plan's instruction-file-only rule.
4. **A CI gap that would have read green.** The TOML/YAML tests use `pytest.importorskip`, so without the libraries two of the four writable formats would have skipped rather than failed. CI now installs them explicitly.

## Deviations from the plan

- **`--check` was not extended to the new install targets** (the plan's 3.2 asks for it). Those targets are files on a user's machine, not repo artifacts, so a repo-side drift check cannot see them. Repo-artifact coverage is unchanged; per-platform propagation is asserted by the 41 seeding tests and the throwaway-HOME install instead.
- **Both installers were edited**, which the plan scoped as untouched. This was the plan's own mandated stop-and-confirm, approved by the maintainer, and is limited to an optional-dependency check for `tomlkit` / `PyYAML` mirroring the existing `python-docx` pattern. No copy step was added and no platform requires one.
- **Copilot's surface was expanded deliberately** (NI-2), adopting the Copilot CLI config as a new surface Nexus-Hub writes.

## Known gaps

BG-2, BG-3, DF-3, QG-2 closed in-phase; NI-2 resolved. NI-5 (four declared-but-not-writable platforms) and NI-6 (hermes is seedable but not installed by default) opened. Recorded in [docs/releases/v3/v3.16/known-gaps.md](../../known-gaps.md).

## Next steps

**Phase 4 - Freshness governance and documentation.** Fold lever re-verification into the existing `platform-contract-verification` remit without adding a new blocking gate, and document the new surface in AGENTS.md. Note for that phase: AGENTS.md's description of the installer/registry split is stale (every platform now routes through the registry), so the documentation pass should correct it rather than describe around it.
