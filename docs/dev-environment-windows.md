# Windows Dev Environment Setup

This guide documents the prerequisites for running Nexus-Hub's validators (`make validate`, `make lint`, `make test`) on Windows 11. The defaults that come with the Python.org Store distribution and PowerShell do not include `make`, `shellcheck`, or a UTF-8 default codec, so a small one-time setup is required.

## Required tooling

### 1. `make` (GNU Make)

PowerShell and `cmd.exe` do not ship `make`. The simplest install path is via Scoop:

```powershell
scoop install make
```

Alternatives:

- Chocolatey: `choco install make`
- Git Bash: `make` is bundled in newer Git for Windows installations (verify with `which make`).
- WSL: Ubuntu under WSL2 has `make` available via `sudo apt install build-essential`.

Verify with `make --version`.

### 2. `shellcheck`

Required by `make lint`. The Makefile gracefully degrades when shellcheck is missing (it prints a skip notice), but adding it gives full shell-script linting locally.

```powershell
scoop install shellcheck
```

Alternatives: `choco install shellcheck`, or download a release binary from `https://github.com/koalaman/shellcheck/releases` and add it to `PATH`.

Verify with `shellcheck --version`.

### 3. Python with UTF-8 default I/O

The Python.org Store distribution defaults to the Windows ANSI codepage (cp1252) for `open()`. Several catalog JSON and Markdown files contain non-cp1252 characters (smart quotes in historical content, em-dashes in older docs), so reads can fail with `UnicodeDecodeError`.

Two equivalent fixes:

1. **Recommended (persistent)**: set `PYTHONUTF8=1` as a User environment variable. This switches Python to UTF-8 mode globally:

    ```powershell
    [Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
    ```

    Restart your terminal after setting it.

2. **Per-session**: prefix invocations with `$env:PYTHONUTF8=1`:

    ```powershell
    $env:PYTHONUTF8=1; python scripts/validate_skills.py --bundles-only
    ```

The Makefile's `validate` target was patched in v2.0.0 to pass `encoding='utf-8'` to every inline `python -c "json.load(open(...))"` call, so `make validate` no longer relies on the default codec.

## Quick verification

After installing the three prerequisites above, the following should all run cleanly from the repository root:

```powershell
make validate    # JSON parse + skill bundle audit (0 errors / 0 warnings expected)
make lint        # shellcheck on installer.sh and install.sh
make test        # pytest sweep across all three extension test suites
```

## Common pitfalls

- **`make: command not found`**: `make` is not on PATH. Re-open the terminal after `scoop install make`, or open Git Bash where it is usually pre-installed.
- **`UnicodeDecodeError: 'charmap' codec can't decode byte ... in position ...`**: `PYTHONUTF8` is not set. Either set it (see above) or run under Git Bash where the default is usually UTF-8.
- **Pre-commit hook fails with `shellcheck not found`**: install shellcheck (see above) or run `git commit --no-verify` for the specific commit and add a follow-up cleanup commit once shellcheck is installed.
- **Path-too-long errors when running tests**: Windows long-path support must be enabled. Run as admin in PowerShell:

    ```powershell
    New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
    ```

## See also

- [permissions-setup.md](permissions-setup.md) - Claude Code / IDE permission configuration on Windows.
- [v2.0.0/known-gaps.md](v2.0.0/known-gaps.md) - WN-002 history (closed at v2.0.0).
