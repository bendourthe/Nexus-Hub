---
title: Bash Security Rules
category: bash
priority: critical
---

# Bash Security Rules

## Command Injection Prevention

- Never interpolate user-provided input directly into commands:
  ```bash
  # WRONG
  eval "$user_input"
  bash -c "$user_input"

  # RIGHT -- pass as argument, never interpolated into command string
  process_input "$user_input"
  ```
- Avoid `eval` in all cases. If dynamic command construction is unavoidable, use arrays: `cmd=("git" "commit" "-m" "$message"); "${cmd[@]}"`.

## File and Path Safety

- Validate that file paths provided by users stay within expected directories:
  ```bash
  realpath --relative-base="$allowed_root" "$user_path" >/dev/null 2>&1 || die "Path traversal attempt"
  ```
- Never use `rm -rf` with unquoted variables: `rm -rf $dir` with an empty `$dir` deletes everything from current directory.
- Use `--` to separate options from file arguments: `rm -- "$file"` prevents files named `-rf` from being misinterpreted.

## Privilege and Permissions

- Do not run scripts as root unless strictly required. Check with `[[ $EUID -ne 0 ]] && die "must not run as root"` where appropriate.
- Set restrictive permissions on files containing secrets: `chmod 600 "$secret_file"`.
- Use `umask 077` at the start of scripts that create sensitive temp files.

## Secret Handling

- Never echo, log, or print secrets. Use `set +x` before any line that expands a secret variable.
- Store secrets in environment variables, not in script files or config files committed to git.
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, or OS keychain) for long-lived credentials.

## Network and External Calls

- Validate URLs before passing to `curl` or `wget`. Reject `file://` and internal IP ranges.
- Always set timeouts: `curl --max-time 30 --connect-timeout 10`.
- Check `curl` exit codes explicitly -- `set -e` alone does not always catch curl failures in pipelines.
