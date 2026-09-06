# Selective-Install Baseline (v3.16.1 Phase 5.1)

**Status**: audit complete, locked for v3.16.1 Phase 5
**Date**: 2026-08-08
**Purpose**: record every path that copies or transforms a catalog surface, so the selection contract in `install-selection-contract.md` can name exactly where selection state must arrive and Phase 6 can implement it without discovering a path late.

This is a description of what exists today, before any selection logic. Every row was read from the source, not inferred.

## The three implementations

Nexus-Hub installs through three independent code paths, and all three must reach the same resolved surface plan for the same selectors.

| Path | Entry point | Size | Runtime | Can it require Python? |
|---|---|---|---|---|
| Legacy Bash | `scripts/installer.sh` | 3234 lines | bash + coreutils | **No.** Canonical on macOS/Linux hosts without Python |
| Legacy PowerShell | `scripts/installer.ps1` | 3382 lines | Windows PowerShell 5.1 and PowerShell 7 | **No.** Same constraint on Windows |
| Python registry | `scripts/lib/integrations/runner.py` | - | Python 3 stdlib | Yes, it is Python |

The legacy installers invoke the registry (`invoke_registry_platform` / `Invoke-RegistryPlatform`) for every platform, but several calls pass `instruction_only`, in which case the legacy script's own `safe_folder_copy` blocks do the catalog mirror. So a single install can copy the same catalog surface through two different code paths depending on the platform, and selection must be applied identically in both.

## Surface-by-surface ownership

| Surface | Legacy Bash | Legacy PowerShell | Registry | Selection applies? |
|---|---|---|---|---|
| Skills (nested) | `safe_folder_copy catalog/skills` | `Safe-Folder-Copy` | `SkillsIntegration._mirror_catalog` -> `_copy_tree` | **Yes** - the primary selection unit |
| Skills (flattened) | n/a | n/a | `_catalog_adapters.flatten_skills` | **Yes** - same set, different shape |
| Command-as-skill adapters | n/a | n/a | `_catalog_adapters.commands_to_skills` | **Yes** - eligibility derived from the command |
| Commands | `safe_folder_copy catalog/commands` | `Safe-Folder-Copy` | `_mirror_catalog` (`commands_subdir`) | **Yes** - gated on declared required skills |
| Slash-command mirrors | per-platform blocks | per-platform blocks | `_catalog_adapters.commands_to_slash` | **Yes** - follows the command |
| Agents | `safe_folder_copy catalog/agents` | `Safe-Folder-Copy` | `_mirror_catalog` (`agents_subdir`) | **Yes** - gated on declared required skills |
| Rules | `safe_folder_copy catalog/rules` | `Safe-Folder-Copy` | `_mirror_catalog` (`rules_subdir`) | **No** - always present |
| Hooks | copy + `settings.json` | copy + `settings.json` | `_mirror_catalog` (`hooks_subdir`, gated on `hooks_supported`) | **No** - always present |
| Context / memory | `safe_folder_copy catalog/{context,memory}` | `Safe-Folder-Copy` | - | **No** - always present |
| Templates, style-guides | `install_templates` | equivalent | - | **No** - always present |
| Data indexes (`{{SKILL_INDEX}}`) | template render | template render | `MarkdownIntegration` | **Yes, in content** - the index must not advertise an uninstalled skill |
| Instruction files | template render | template render | `MarkdownIntegration` marker merge | **No** file-level; content follows the index rule above |
| `configs/platform-defaults.json` seeding | - | - | `IntegrationBase.install` -> `platform_defaults.seed_platform_defaults` | **No** - policy infrastructure |

The last row matters for Phase 6: defaults seeding is hooked on the **dispatcher** (`IntegrationBase.install`), not on `install_global`, precisely so a subclass that forgets `super()` cannot skip it. Selection must not be threaded in a way that bypasses that dispatcher.

## Registry class hierarchy

```
IntegrationBase                 install() dispatcher; legacy cleanups; defaults seeding
├── MarkdownIntegration         instruction file + marker merge + {{SKILL_INDEX}}
├── TomlIntegration
├── YamlIntegration
└── SkillsIntegration           _mirror_catalog(): skills / commands / agents / rules / hooks
```

`SkillsIntegration._mirror_catalog` is the single chokepoint for the file-tree surfaces in the registry path. Both branches of its skills block (flattened and nested) and its four-entry `(cfg_key, src_rel)` loop are where a resolved surface plan has to be consulted.

## State objects that must carry selection

### `InstallContext` (`base.py`, dataclass)

Current fields: `repo_root`, `target_root`, `scope`, `overwrite`, `dry_run`, `manifest`, `template_vars`, `languages`, `instruction_only`.

Selection needs one additional field carrying the resolved plan. It must default to "everything", so every existing caller keeps its current behavior with no edit - the same additive pattern `languages` and `instruction_only` already follow.

### `InstallManifest` (`manifest.py`)

Current state: `_tracked`, `_shared`, `_logs`, `_actions`. Serialized by `to_dict()` to the keys `tracked` / `shared` / `logs` / `actions`.

Two findings that shape the design:

1. **There is no schema-version field.** Adding one now would be a behavior change for every existing reader, so selection is added as an additive key instead.
2. **`from_dict` reads every key with `.get(...)` and a default.** An older manifest with no `selection` key therefore loads cleanly and must be interpreted as a full install. This is the backward-compatibility guarantee Phase 5.5 tests, and it is already structurally true rather than something to build.

## Lifecycle operations that must agree on scope

| Operation | Location | Requirement under selection |
|---|---|---|
| `install` | `runner.py` `cmd_install` | Resolve, validate, then write. Record the selection in the manifest |
| `print-config` | `runner.py` `cmd_print_config` | Report the resolved set; never widen it |
| `check` | `runner.py` `cmd_check` | Verify against the recorded scope, not the full catalog |
| `doctor` | `lifecycle.py` `doctor()` | Distinguish content drift from a catalog change that alters a selector's resolution |
| `repair` | `lifecycle.py` `repair()` | Reinstall only the recorded resolved scope plus always-present infrastructure |
| `list-installed` | `lifecycle.py` `list_installed()` | Report the recorded selection |
| `teardown` | `runner.py` `cmd_teardown` | Manifest replay; already scope-correct, since it removes only what was tracked |
| `init` | `runner.py` `cmd_init` -> `wire_project_surfaces` | Project surfaces follow the recorded selection |
| `upgrade` | `scripts/nexus_hub_cli.py` | Preserve the recorded selection unless a replacement selector is supplied. Must forward selectors without string interpolation into a shell |

## Existing flag surfaces

Adding selectors must not disturb these.

- **Bash**: `--enterprise`, `--strict-permissions`, `--workspace`, `--platforms`, `--force`, `--branch`, `--print-config`, `--yes`.
- **PowerShell**: the documented equivalents (`-Enterprise`, `-Workspace`, `-Platforms`, `-Force`, `-Branch`, `-PrintConfig`, `-Yes`).
- **Registry** (`runner.py`): subcommands `list`, `install`, `print-config`, `check`, `init`, `teardown`, `doctor`, `repair`; `install` carries `--scope`, `--target`, `--integrations`, `--overwrite`, `--dry-run`, `--project-name`.

## Behavior when Python is unavailable

The legacy installers must complete a full install with no Python present. Consequences the contract must respect:

- Selection resolution cannot live only in `scripts/lib/installer/selection.py`. Each legacy installer implements the same contract natively.
- `data/bundles.json` must be parseable by each path's available tooling: `jq` when present with a native fallback in Bash, `ConvertFrom-Json` in PowerShell.
- The three implementations are kept honest by a shared fixture matrix rather than by shared code. That is why Phase 5.3 exists and why its cases carry expected exit codes and warnings, not just expected file sets.

## Selection-source inventory

`data/bundles.json` (schema 1.4.0) declares 3 profiles, 6 modules, and 15 role bundles. As of Phase 2 every skill id in every selection resolves to a real catalog directory; four did not before, and were repaired under v3.16.1 NI-1. Nothing currently declares **command-to-skill** or **agent-to-skill** dependencies, so surface eligibility metadata does not yet exist and Phase 7.1 is scoped to finalize it.

> **Forward note (Phase 7.1, added Phase 8).** The paragraph above is the state this audit found and is left as recorded. Phase 7.1 then discovered that those 6 modules reached only 105 of 271 skills, with 166 available solely under `full`, and expanded modules to be **category-complete**: schema **1.5.0**, **20 modules**, 271/271 reachable. It also added the `surface_requirements` block for 6 commands. The role bundles remain 15 and untouched. See v3.16.1 NI-4 and NI-5 in [known-gaps.md](../known-gaps.md).

## Row-to-phase map

| Baseline row | Owning phase |
|---|---|
| Selector grammar, closure, eligibility, failure, manifest shape | 5.2 contract |
| Shared expected behavior for all three paths | 5.3 fixtures |
| `selection.py` resolver; `InstallContext` and `InstallManifest` fields | 5.4 |
| Resolver and manifest-compatibility tests | 5.5 |
| Bash selector flags and copy filtering | 6.1 |
| PowerShell selector parameters and copy filtering | 6.2 |
| Registry runner args; `SkillsIntegration` and `_catalog_adapters` filtering | 6.3 |
| Upgrade / repair / doctor / list-installed preservation | 6.4 |
| Cross-implementation fixture parity | 6.5 |
| Command and agent dependency metadata | 7.1 |
| Platform read-path parity for focused installs | 7.2 |

## Open questions carried into 5.2

1. **Command and agent dependencies do not exist yet.** The contract must define where they are declared and how a surface with no declaration behaves. Defaulting an undeclared command to "always install" preserves current behavior; defaulting it to "never install under a focused selection" would silently shrink installs. The contract picks the former and Phase 7.1 adds the declarations.
2. **`{{SKILL_INDEX}}` content under a focused install.** The index is embedded in instruction files. If it lists the full catalog while only a subset is installed, every focused install advertises skills the agent cannot load.
3. **Byte-equivalence of the no-selector path.** The contract requires it, and the only way to be sure is a fixture that diffs a full install before and after the change rather than reasoning about the code.
