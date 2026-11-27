# v4.15.6 Distribution Handbook Claim Review

Re-review of the distribution handbook's claims after v4.15.6 changed three of its evidence inputs: `scripts/installer.sh`, `scripts/installer.ps1` and `scripts/nexus_hub_cli.py`. Read by whoever refreshes `docs/handbooks/_sources/distribution/evidence.json` or audits why its snapshot moved. Topics: changed inputs, affected claims, disposition.

## Changed Inputs

| Input | Change in v4.15.6 |
|---|---|
| `scripts/installer.sh` | One `safe_copy` block installs `scripts/nexus_worktrees.py` beside the CLI core (9 added lines, nothing removed). |
| `scripts/installer.ps1` | The matching `Safe-Copy` block (9 added lines, nothing removed). |
| `scripts/nexus_hub_cli.py` | A `worktree` subcommand that loads the installed `nexus_worktrees.py` sibling in-process and forwards its arguments; help text lists it (33 added lines, nothing removed). |

## Claims Reviewed

- `docs/handbooks/_sources/distribution/source.md` (27 lines) and `model.json` were searched for claims about the installed script list, CLI subcommands, worktrees and per-script copy behavior. None exists.
- The ownership and overwrite claim (source.md line 17: owned-file writing consults the installation manifest; copy paths may differ in overwrite behavior) still holds: the new copy uses the existing `safe_copy` / `Safe-Copy` helper with the same overwrite flag as its neighbors.
- No claim about attribution hooks, Claude core settings, platform defaults or bootstrap download changed.

## Disposition

No handbook claim is affected, so the handbook text and its rendered output are unchanged. The snapshot input digests for the three files are refreshed, and the content check now cites this review. Build and render receipts stay valid because the handbook output digest is unchanged.
