#!/usr/bin/env bash
# Worktree Policy - PreToolUse hook (Bash and PowerShell tools).
# Part of Nexus-Hub
#
# Refuses a recognized `git worktree add` or `git worktree move` whose destination is
# not <root>/<identity>/<name>. The proposed command is read only from stdin
# tool_input.command and is handed to _worktree_policy.py, a pure policy check. This
# hook never runs the proposed command. Exit 0 allows; exit 2 denies.
#
# This is a mandatory guard. It does not honor NEXUS_HOOK_PROFILE=minimal or
# NEXUS_DISABLED_HOOKS, and it applies in every host permission mode. The only
# override is changing the worktree root (NEXUS_WORKTREE_ROOT or the user's own
# config file). Limits: aliases, scripts and nested shells it cannot parse are not
# certified; see docs/runbooks/worktree-organization.md.

set -uo pipefail

readonly _NEXUS_TAG="[Nexus-Hub: worktree-policy]"
# Builtins only up to the interpreter probe, so a stripped PATH still reaches the fallback.
source_path="${BASH_SOURCE[0]//\\//}"
here="${source_path%/*}"
[ "$here" != "$source_path" ] || here="."
IFS= read -r -d '' payload || true
[ -n "$payload" ] || exit 0

for py in python3 python py; do
  command -v "$py" >/dev/null 2>&1 || continue
  printf '%s' "$payload" | "$py" "$here/_worktree_policy.py"
  rc=$?
  # 0 allows and 42 is the helper's denial; any other code means this interpreter did not run it.
  if [ "$rc" -eq 0 ]; then
    exit 0
  fi
  if [ "$rc" -eq 42 ]; then
    exit 2
  fi
done

# No usable interpreter: a worktree add or move cannot be certified, anything else is allowed.
shopt -s nocasematch
if [[ "$payload" =~ worktree[[:space:]]+(add|move) ]]; then
  printf '%s BLOCKED: no Python interpreter is available to certify a worktree add or move. Use: nexus-hub worktree create --repo <checkout> --branch <branch> --base <commit> --name <name>.\n' "$_NEXUS_TAG" >&2
  exit 2
fi
exit 0
