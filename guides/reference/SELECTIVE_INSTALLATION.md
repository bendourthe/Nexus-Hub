# Selective Installation Reference

How to install a subset of the Nexus-Hub catalog, what each selector means, and what to do when one does not behave as expected.

The normative rules live in [`docs/releases/v3/v3.16/development/install-selection-contract.md`](../../docs/releases/v3/v3.16/development/install-selection-contract.md). This guide is the user-facing view of them.

## The short version

```bash
bash scripts/installer.sh --profile core                       # a coarse scope
bash scripts/installer.sh --modules ai-engineering,testing     # capability areas
bash scripts/installer.sh --bundles ai-engineer                # a curated role
bash scripts/installer.sh --profile core --modules security-operations
```

```powershell
.\scripts\installer.ps1 -Profile core
.\scripts\installer.ps1 -Modules ai-engineering,testing
.\scripts\installer.ps1 -Bundles ai-engineer
```

No selector installs everything, exactly as before.

## The three selector kinds

| Selector | What it is | Cardinality |
|---|---|---|
| `--profile` / `-Profile` | Coarse scope: `minimal`, `core`, or `full` | At most one |
| `--modules` / `-Modules` | Capability areas, one per catalog category | Any number |
| `--bundles` / `-Bundles` | Curated cross-category role sets | Any number |

Repeatable and comma-separated forms are identical: `--modules a,b` and `--modules a --modules b` produce the same install and the same hash.

**Profiles compose.** They carry no skill list of their own; they are built from bundles, modules, and a few extra skills. That is why `core` grows when a module it composes from grows.

**Modules are category-complete** (schema 1.5.0). There is one module per catalog category, so every skill in the catalog is reachable through at least one module. Before this, 166 of 271 skills could only be installed via `full`.

## What gets filtered, and what never does

Only three surfaces are ever filtered:

- **skills** - the selection unit
- **commands** - filtered only when declared (see below)
- **agents** - currently none are declared, so all install

Everything else installs under **every** selection, including `minimal`:

- hooks, rules, templates and style guides, settings and permission configs, context and memory templates, data indexes and instruction files, and platform install-time defaults.

This is deliberate. Narrowing your skill set asks for fewer capabilities, never for fewer guardrails; a focused install that dropped the secret-scan hook would be less safe than the default one.

## Why a command disappeared

Six commands are thin pointers over a single skill. Each installs only when its skill is selected:

| Command | Requires |
|---|---|
| `/constitution` | `project-constitution` |
| `/describe` | `analyze-codebase` |
| `/implement` | `implement-phase` |
| `/presentify` | `document-to-interactive-html` |
| `/route` | `model-routing` |
| `/tune-prompting` | `model-prompting-research` |

Every other command installs regardless of selection. The rule is one-directional: a command is dropped only when the skill that does its work is absent, because in that case the command is a pointer to nothing.

To keep `/implement` in a focused install, include the module that contains `implement-phase` (`workflow`), or add the skill through any other selector.

## Inspecting a selection before installing

The resolver writes nothing, so it is safe to run at any time:

```bash
# Full plan as JSON: resolved skills, commands, agents, reasons, warnings, hash
python scripts/lib/installer/selection.py --repo-root . --modules ai-engineering

# Compact form, one record per line
python scripts/lib/installer/selection.py --repo-root . --profile core --emit lines
```

`reasons` answers "why is this skill here": `selector:module:ai-engineering` for a directly selected skill, `dependency:<skill>` for one pulled in transitively.

After installing, the recorded plan lives in the install manifest:

```bash
python scripts/lib/integrations/runner.py list-installed --target .
```

## Upgrades, repairs, and going back to everything

- **`nexus-hub upgrade`** re-applies whatever you selected. An upgrade never quietly widens a focused install back to the full catalog.
- **`repair`** reinstalls the recorded scope, not the full catalog.
- **`doctor`** reports *selector drift* separately from content drift. Selector drift means your selectors still resolve but now resolve to a different set, because the catalog changed - a skill was added to a module you selected. That is not corruption, and `repair` moves you to the new resolution if you want it.
- **To change scope**, pass a new selector. **To go back to everything**, pass `--profile full`.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Unknown profile: 'x'. Known profiles: ...` (exit 2) | A typo. Ids are matched exactly, with no fuzzy fallback, so a near-miss is never silently guessed at. |
| `Profile 'full' cannot be combined with other selectors` (exit 2) | `full` already means everything. Drop `full` to narrow, or drop the others to widen. |
| `Selection resolved to no skills` (exit 2) | The selectors are valid but select nothing. An empty install is never a useful end state. |
| `Selection references skill(s) with no catalog directory` (exit 3) | A catalog defect, not your input: `data/bundles.json` names a skill that does not exist. |
| `--profile / --modules / --bundles need Python to resolve` (exit 2) | Selectors are resolved by a Python module. Install Python 3, or drop the selector - a full install needs no selector resolution. (Since v3.17.0 the permission baseline is merged by a Python helper on every host, replacing a `jq` dependency that silently installed nothing on a stock macOS; a Python-less host therefore skips the baseline with a warning, as it already skips every registry-backed platform.) |
| Warning: selection resolved to the entire catalog | Your selectors happened to union to everything. Not an error; `--profile full` says it directly. |
| A command you expected is missing | See "Why a command disappeared" above. |
| Nothing was filtered at all | Check the install output for a `Selection:` line. If it is absent, no selector reached the installer. |

Exit codes are consistent across all three install paths: **2** means your selector was wrong, **3** means the catalog is wrong. You can fix the first; the second needs a catalog change.

## Guarantees

- A no-selector install is byte-for-byte what the pre-selection installer produced.
- Validation happens before anything is written, so an invalid selector never leaves a half-installed tree.
- The same selectors produce the same install through the Bash installer, the PowerShell installer, and the Python registry - verified by comparing a hash of the resolved plan across all three.
- Nothing here adds an outbound call, a credential, or a runtime dependency.

## Related

- [`install-selection-contract.md`](../../docs/releases/v3/v3.16/development/install-selection-contract.md) - the normative rules
- [`selective-install-baseline.md`](../../docs/releases/v3/v3.16/development/selective-install-baseline.md) - which install path owns which surface
- [`data/bundles.json`](../../data/bundles.json) - profiles, modules, bundles, and `surface_requirements`
- [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md) - local security-audit procedure for a `security-specialist` (or equivalent) install
