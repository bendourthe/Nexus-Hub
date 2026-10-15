---
title: Bash Code Style
category: bash
priority: medium
---

# Bash Code Style Rules

## Safety Flags

- Begin every script with `set -euo pipefail`:
  - `-e` exits on non-zero return codes
  - `-u` treats unset variables as errors
  - `-o pipefail` propagates pipeline failures

```bash
#!/usr/bin/env bash
set -euo pipefail
```

- Use `#!/usr/bin/env bash` (not `#!/bin/bash`) for portability across macOS and Linux.

## Variables and Quoting

- Always double-quote variable expansions: `"$variable"`, `"${array[@]}"`.
- Use `${VAR:-default}` for default values; `${VAR:?error message}` to require a variable.
- Use `local` for all variables inside functions to prevent scope leakage.
- Use `readonly` for constants: `readonly MAX_RETRIES=3`.
- Prefer `$(command)` over backticks for command substitution -- it nests cleanly.

## Functions

- Declare functions before use. Use lowercase names with underscores: `install_dependencies`.
- One function per logical task. Functions over 30 lines should be split.
- Return status codes explicitly: `return 0` for success, non-zero for errors.
- Capture output from functions via `local result; result=$(my_function)` not global variables.

## Error Handling and Logging

- Check command exit codes explicitly for commands run inside conditionals: `if ! command; then`.
- Use a consistent logging pattern:
  ```bash
  log_info()  { echo "[INFO]  $*" >&2; }
  log_error() { echo "[ERROR] $*" >&2; }
  ```
- Send informational messages to stderr (`>&2`), keep stdout for actual output.
- Clean up temp files on exit: `trap 'rm -f "$tmpfile"' EXIT`.

## Portability

- Avoid bash 4+ features (associative arrays, `mapfile`) if the script must run on macOS (bash 3.2).
- Use `command -v tool >/dev/null 2>&1` to check for a binary before using it.
- Avoid GNU-only flags (e.g., `sed -i ''` on macOS vs. `sed -i` on Linux) -- test on both.
- Prefer `printf` over `echo` for formatted output; `echo` behaves inconsistently across shells.
