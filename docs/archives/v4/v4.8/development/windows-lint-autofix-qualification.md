# Windows lint-autofix hook qualification

This frozen v4.8 follow-up records how to run the original Bash hook test suite on the Windows development host. It is a host qualification, not a hook implementation change or a replacement for hosted CI.

## Historical failure and current run

The original `WN-3` run resolved `bash` to Windows `system32\bash.EXE` (WSL), which returned exit 127 for a Windows-path shell script. The original failure remains in the [active known-gaps ledger](../../../../releases/v4/v4.8/known-gaps.md).

On 2026-09-24, an isolated worktree at `origin/develop` (`8e55ebcb`) ran `catalog/hooks/tests/test_lint_autofix.py` with `C:\Program Files\Git\bin` and the Python user-script directory prepended to that process's `PATH`. The selected executables were Git Bash `bash.exe` and installed `ruff.exe`. The exact test file completed with **7 passed, 0 skipped** in 9.02 seconds. No hook source or test file was changed to obtain this result.

The portable setup is to resolve the Python user-script directory with `sysconfig.get_path('scripts', scheme='nt_user')`, prepend it and Git Bash's `bin` directory to `PATH` for the test process, then run `python -m pytest catalog/hooks/tests/test_lint_autofix.py -q -rs`. This path adjustment is local to the command session; it does not change a user's permanent environment or the repository's hook registration.

## Boundary

This proves the seven existing cases on this Windows host, including the Ruff-gated formatting cases. It does not prove WSL path compatibility, reproduce the original failure as a passing test, or replace the Ubuntu CI run. The historical six-behavior manual verification remains separate from this automated seven-test result.
