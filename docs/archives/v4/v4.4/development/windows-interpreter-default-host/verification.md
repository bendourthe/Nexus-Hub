# Windows default-host interpreter qualification

This is the post-release v4.4 QG-446-1 local qualification. It records the current managed Windows hook interpreter, a default-PATH functional probe, and a complete native Windows profile. The original failed v4.4 run and the earlier process-qualified full-profile record remain unchanged. Protected integration and post-merge observation are separate gates.

## Boundary and implementation

The original gate probed `bash` on Windows even though current Windows installers register PowerShell `.ps1` siblings for managed shell hooks. The WSL Bash launcher on the unmodified host PATH was unusable, so that probe failed for an interpreter the managed Windows registrations no longer select. The gate now probes `powershell -NoProfile -ExecutionPolicy Bypass -File` on Windows and retains the Bash probe on non-Windows hosts. It requires the exact marker and zero exit, so a banner-only or success-without-execution shim cannot pass. A separate full-profile test fixture now waits for fullscreen to become observable before asserting it, removing a timing-dependent false failure without altering guide behavior.

A read-only inspection of the installed Claude settings counted 35 managed `.ps1` hook targets, six `.py` targets, and zero `.sh` targets. This count does not expose command text or user settings. It supports the selected-interpreter contract on this host; it does not claim that arbitrary user-authored hooks or every Windows installation use the same commands.

## Verification

| Check | Result |
|---|---|
| `python scripts/check_interpreter_resolution.py --gate` on unmodified host PATH | Exit 0; selected `powershell`, resolved to Windows PowerShell, and executed the probe script |
| Interpreter and related focused tests | 42 passed before the full run |
| Native fast profile | 17 passed before the full run |
| Unfiltered native Windows full profile | 61 passed, zero failed, skipped, or advisory; 7,446.3 seconds; all 13 repository test partitions passed |
| Attribution | `VERIFIED` for the maintainer's configured Git identity and active hooks |

The full run started at `2026-09-25T18:15:21Z` and finished at `2026-09-25T20:19:27Z` on Windows 11 with Python 3.12.10. It ran all groups without `--base`, on the five-file working diff based on `c1ac45f0`. No implementation file was changed during that run. The [archived summary](summary.md) and [environment metadata](environment.json) retain the terminal receipt. The original ignored JUnit files remain local and are not represented as archived artifacts here.

| Archived file | SHA-256 |
|---|---|
| `summary.md` | `73c60ab063cc04eb2fd677ffa47853ee540b45628743277434801fce7f60120a` |
| `environment.json` | `2b450f5cfc3f162575910ebf1085d29a13cb4274424efca8eaecbe839e842f85` |

## Disposition

QG-446-1 has a local default-host candidate and a complete green native profile. It remains open until this branch passes protected PR validation, merges to `develop`, and the minimal post-merge smoke and provenance checks pass. The user-superseded v4.4.6 T027 is not retroactively marked complete.
