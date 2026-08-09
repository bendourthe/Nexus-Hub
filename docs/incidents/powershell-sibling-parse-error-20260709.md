# Incident: a catalog PowerShell hook shipped with a parse error and stayed dead for four minor versions

**Date**: 2026-07-09 (diagnosed during the v3.15.6 hook-parity work)
**Audience**: Nexus-Hub maintainers touching `catalog/hooks/` or either installer / owning skill: [[incident-postmortem]]

## Summary

`catalog/hooks/session-summary.ps1` shipped in v3.11.0 carrying a PowerShell parse error. The file therefore never executed: any Windows user running hooks through PowerShell received no session summary at all, while the `.sh` sibling worked normally everywhere else.

Nothing detected it for four minor versions. The reason is narrow and worth stating precisely: no part of the validation surface parsed catalog `.ps1` files. ShellCheck covers `.sh` and has no PowerShell equivalent in the pipeline, and the hook tests that would have executed the file skipped when no PowerShell interpreter was present on the runner. A skip produces no output in a green run, so the absence of coverage looked identical to coverage that passed.

The defect was a broken feature rather than a broken build, which is why it survived: the failure surfaced only as an absence on a platform the maintainers were not running.

## Public-Safe Shape

This is shape [S-1: An unverified cross-platform sibling is silently non-functional](shapes.md#s-1-an-unverified-cross-platform-sibling-is-silently-non-functional), failure mode 1 (the file never runs at all).

The specific lesson this instance contributes to the shape: **a conditional skip is not coverage, and a green run containing skips is not evidence.** The gate that closes this mode must be unconditional - it has to fail on a parse error even when no interpreter is available to run the file - because the moment it can be skipped, it will be skipped on exactly the runner where it mattered.

## Durable fix

| Fix | Link |
|---|---|
| Unconditional `.ps1` AST-parse gate in CI's `shellcheck` job, iterating every file in `catalog/hooks` and failing on any parse error. Explicitly written to hold even if the runner image ever drops `pwsh` | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) (the `shellcheck` job's PowerShell AST-parse step) |
| `test_hook_sibling_parity.py`, which fails in BOTH directions when a `.sh` has no `.ps1` or a `.ps1` has no `.sh`, and fails when a `.ps1` does not parse | [`catalog/hooks/tests/test_hook_sibling_parity.py`](../../catalog/hooks/tests/test_hook_sibling_parity.py) |
| The sibling requirement written into the canonical agent guidance, so a new hook is authored with both halves rather than having the second one requested in review | [`AGENTS.md`](../../AGENTS.md) (Adding or Modifying a Hook) |

**What this would catch on a recurrence**: any catalog `.ps1` that fails to parse, on every CI run, on the commit that introduces it rather than four versions later.

**What it still misses**: a file that parses cleanly and then behaves differently from its sibling at runtime. That is failure mode 2 of the same shape, and it is what the second incident in this directory is about - which is the strongest available evidence that the shape is real rather than a one-off.
