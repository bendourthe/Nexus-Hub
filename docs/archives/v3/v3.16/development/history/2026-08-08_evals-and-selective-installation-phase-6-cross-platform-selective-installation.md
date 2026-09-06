# Session History - v3.16.1 Phase 6: Cross-platform selective installation

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md](../../plans/v3.16.1-evals-and-selective-installation.md)
**Phase**: 6 of 8 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/v3.16.1-evals-and-selective-installation`
**Outcome**: Complete. Selection is live on all three install paths. Four real bugs found and fixed during implementation; one plan deviation taken with user approval.

## Goal

Implement the Phase 5 selection contract across Bash, PowerShell, the integration registry, manifests, repairs, and upgrades, so the same selectors produce the same install everywhere.

## How the phase was run

At the user's direction the phase ran in two segments with a checkpoint between them, because it is by far the largest in the plan and the second half edits two user-facing installers:

- **Segment A** - the registry (6.3) and lifecycle (6.4), which are Python and immediately testable against the Phase 5 fixtures.
- **Segment B** - Bash (6.1), PowerShell (6.2), upgrade forwarding, parity tests (6.5), and stabilization (6.6).

## Sub-tasks completed

### 6.3 - Registry and catalog adapters (T036, T037)

`InstallContext` gained `selects_skill` / `selects_command` / `selects_agent` / `is_filtered`. `selection is None` short-circuits before any set is built, so a full install stays on its exact pre-v3.16.1 code path. Filtering was added to `flatten_skills`, `commands_to_skills`, and `commands_to_slash`, plus two new filtered-path-only helpers (`nested_skills_selected`, `flat_md_selected`). `runner.py` gained `--profile` / `--modules` / `--bundles` on `install` and `repair`, resolution before any write with exit 2/3 propagation, the plan recorded in the manifest, and the selection carried into the summary JSON the installers read.

### 6.4 - Lifecycle preservation (T038)

`repair` reuses the recorded selection when no selector is supplied and replaces it when one is. `doctor` reports **selector drift** separately from content drift and never as an error. `list-installed` reports the recorded scope. `nexus_hub_cli.py` re-applies recorded selectors to the upgrade bootstrap.

### 6.1 / 6.2 - Bash and PowerShell (T032-T035)

Both installers gained the three selectors in their own idiom, resolution placed beside the existing `--platforms` validation and before any write, a filtered staging tree, and a one-line helper (`catalog_src` / `Get-CatalogSource`) at each copy site. Both forward selectors to the registry and now copy `scripts/lib/` wholesale (NI-3).

### 6.5 / 6.6 - Parity tests and stabilization (T039, T040)

`tests/installer/test_selection_parity.py`, 28 assertions: 26 fast contract checks plus 2 `slow`-marked end-to-end installs.

## Decisions made

- **Both installers delegate resolution instead of implementing it natively (DF-5, user-approved).** A jq implementation was written first, then discovered to be untestable: jq is not installed on the development host and nothing in CI installs or asserts it. Shipping an unverifiable second implementation of a *hashed* contract is worse than one shared implementation, because divergence would surface as a silent hash mismatch on a user's machine. The jq file was deleted unshipped. What the plan's wording protects survives intact: a no-selector full install still needs neither Python nor jq, because both installers return from the selection path before touching Python when no selector was given, and a Python-less host already skipped every registry-backed platform anyway.
- **Filtering is applied by staging, not at each copy site.** A filtered copy of `skills`, `commands`, and `agents` is built once, and every downstream copy reads it through one helper. Only 6 of 25 catalog references in `installer.sh` needed changing, per-platform copy sites need no per-site logic, and the three surfaces cannot drift apart. Hooks, rules, context, memory, style-guides, and mcp-configs are never routed through it.
- **The filtered nested-skills path is a separate function from the unfiltered whole-tree copy.** A per-skill walk that must be *proven* identical to a bulk `_copy_tree` is a much weaker guarantee than simply not taking that path when unfiltered. That is what makes the byte-equivalence result structural rather than lucky.
- **`-Profile` is an alias, not the parameter name.** `$Profile` is a PowerShell automatic variable; the parameter is `$InstallProfile` with `[Alias("Profile")]`, so the user-facing spelling matches Bash's `--profile` without shadowing anything.
- **Upgrade selectors are validated, not quoted.** Recorded ids are checked against `^[a-z0-9][a-z0-9-]*$` before being placed in the bootstrap command string. An id that cannot contain a quote, space, semicolon, or backtick cannot break out of it; anything failing the check is dropped rather than escaped.

## Troubleshooting trail

Four real bugs, all found by running the thing rather than by reading it.

- **`set -e` swallowed the Bash selector error message (BG-2).** `resolve_selection` captured the resolver with a bare `out=$(...)` then checked `$?`. Under `set -e` a non-zero resolver exit aborts at the assignment, so the handler that prints *which* selector was wrong never ran. Observed: exit 2 with completely empty stderr. Fixed with `|| rc=$?`.
- **Windows CRLF made the Bash staging loop select nothing (BG-3).** A Windows Python invoked from Git Bash writes CRLF, so every parsed `value` carried a trailing `\r`, `find -name` matched nothing, and the stage was built empty. The install then completed **successfully having copied zero skills** - a green run that shipped nothing, which is the worst failure shape available. Found because the summary line read "0 skills, 0 commands, 1 agents" while the hash was correct, proving resolution was fine and staging was not.
- **PowerShell `2>&1` produced NativeCommandError noise (BG-4).** Redirecting a native command's stderr on PS 5.1 wraps each line in an ErrorRecord and sets `$?` false even on a clean exit. Removed; the resolver's stderr already reaches the console.
- **`-Profile` shadowed a PowerShell automatic variable (BG-5).** Caught by the editor's PSScriptAnalyzer diagnostics, not by a test.

Each now has a named regression test, because all four are invisible to a reader and only one of them (BG-5) had a linter that would catch it.

## Verification

- `python -m pytest -q tests/installer/test_install_selection.py tests/installer/test_selection_parity.py -m "not slow"` - 116 passed
- `python -m pytest -q tests/installer/test_selection_parity.py -m slow` - 2 passed (real Bash and PowerShell installs into temp targets)
- Segment A regression (`tests/installer` + `tests/integrations`) - 847 passed, 17 skipped, 1 failed (BG-1, the inherited MSYS `tar` bootstrap failure; unrelated)
- **Byte-equivalence**: a no-selector install and an explicit `--profile full` install produce **811 files each, identical set**
- **Three-way hash agreement**: Python, Bash, and PowerShell independently produced `sha256:74e72e2bc3bd...` for `--modules ai-engineering`
- Live installs verified by inspection: Bash `--modules ai-engineering` -> 6 skills with rules/commands/agents intact; PowerShell same; PowerShell `-Profile minimal` -> 10 skills
- Fail-closed verified on both: an unknown profile exits 2 with a message naming it and **writes zero files**
- `bash -n` and PS 5.1 `Parser::ParseFile` both clean; catalog validators, trigger gate, version sync, personal-paths, supply-chain, workflow-security, platform contracts, and platform-defaults drift all PASS; `git diff --check` clean

## CI impact

None required. `tests/installer` already runs as its own CI step on the Linux and Windows legs, so the new module is picked up automatically. The two `slow` tests run in CI (nothing deselects them there) and are skipped gracefully when their shell is unavailable. The `slow` marker is registered in `tests/conftest.py` rather than a new root `pytest.ini`, because this repo deliberately runs several separate pytest roots and a root config would apply to invocations that never asked for it.

## Files changed

| File | Change |
|---|---|
| `scripts/lib/installer/selection.py` | resolver CLI (`--emit json\|lines`) both installers call |
| `scripts/lib/integrations/base.py` | selection predicates; `_mirror_catalog` filtered branch |
| `scripts/lib/integrations/_catalog_adapters.py` | filtering in 3 adapters; 2 new filtered-path helpers |
| `scripts/lib/integrations/runner.py` | selector args, resolution, manifest recording, summary, doctor drift, list-installed |
| `scripts/installer.sh` | selectors, staging resolver, `catalog_src`, registry forwarding, wholesale lib copy, help |
| `scripts/installer.ps1` | same in PowerShell, with `-Profile` as an alias |
| `scripts/nexus_hub_cli.py` | upgrade re-applies recorded selectors, id-validated |
| `tests/installer/test_selection_parity.py` | new, 28 assertions |
| `tests/conftest.py` | register the `slow` marker |
| `docs/v3/v3.16/known-gaps.md` | DF-5, BG-2..BG-5, NI-3 closed |

## Next steps

Phase 7 proves distribution parity at every platform read path, finalizes bundle and dependency metadata (including the `surface_requirements` that currently do not exist, which is why every selection still installs all 20 commands and 23 agents), and writes the command-first documentation. NI-2 (118 truncated agent descriptors) remains open and is a natural fit for 7.1's generated-catalog verification.
