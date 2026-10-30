#!/usr/bin/env bash
# Git Guardrails - PreToolUse Hook for Claude Code
# Blocks dangerous git commands before execution.
# Part of Nexus-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin before each Bash tool call.
#   This script extracts the command, checks it against dangerous
#   patterns, and exits 2 (block) or 0 (allow).
#
# To customize: edit the DANGEROUS_PATTERNS array below.
# Format: "regex_pattern:::Human-readable description"
#
# Limitation (read this before trusting it): these are fixed regexes matched
# against the RAW command string, not an argv decomposition. Quoting, unusual
# spacing, environment indirection, and equivalent alternate flags can all evade
# them, and a flag nobody listed will pass silently. This hook is
# defense-in-depth, NOT a boundary. See the "Limits and Honest Boundaries"
# section of catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md.
#
# Opt-in bypass-flag mode (v4.14.4): when ~/.nexus-hub/guardrails.json sets
# "block_git_bypass_flags": true (or NEXUS_GUARD_GIT_BYPASS=1), the flags that skip
# git hooks or commit signing are blocked as well: --no-verify, git commit -n, and
# --no-gpg-sign, plus gpgsign=false set inline or persisted. It is off by default and
# the switch file is read on every run, so it needs no restart. This mode is
# defense-in-depth, NOT a boundary. Its limits: environment-variable skips (HUSKY=0,
# SKIP=, LEFTHOOK=0, GIT_CONFIG_*), git plumbing (commit-tree, update-ref), shell
# aliases and scripts, bypassPermissions mode, and an agent that edits guardrails.json
# itself. The full list is on the mode's block below and in
# docs/decisions/*/tooling/2026-10-14-opt-in-git-bypass-flag-guard.md.
#
# This hook runs for the Bash tool and the PowerShell tool (settings.json matcher
# "Bash|PowerShell"); both send the command as tool_input.command.

set -euo pipefail

# --- Dangerous patterns ---
# Each line: "extended_regex:::description"
DANGEROUS_PATTERNS=(
  'git\s+push\s+.*--force:::Force push overwrites remote history'
  'git\s+push\s+-[a-zA-Z]*f:::Force push overwrites remote history'
  'git\s+push\s+.*--force-with-lease:::Force-with-lease push overwrites remote history'
  'git\s+reset\s+--hard:::Hard reset discards all uncommitted work'
  'git\s+clean\s+-[a-zA-Z]*f:::Clean -f permanently deletes untracked files'
  'git\s+branch\s+-D:::Force-delete branch without merge check'
  'git\s+checkout\s+\.:::Discards all working tree changes'
  'git\s+checkout\s+--\s+\.:::Discards all working tree changes'
  'git\s+restore\s+\.:::Discards all working tree changes'
  'git\s+stash\s+drop:::Permanently loses stashed work'
  'git\s+stash\s+clear:::Permanently loses all stashed work'
  'rm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+\.git:::Destroys the entire repository'
  # Execution indirection via git metadata (group B of the canonical
  # execution-trigger surface list). Both settings name something git EXECUTES on
  # ordinary operations, so writing either turns a routine git command into
  # arbitrary code execution. The leading `(-c\s+\S+\s+)*` tolerates other -c
  # options appearing first, so interleaving them is not an evasion.
  'git\s+(-c\s+\S+\s+)*-c\s*core\.hooksPath\s*=:::Redirects git hooks to an agent-chosen directory, so a later git operation executes it'
  'git\s+(-c\s+\S+\s+)*-c\s*core\.fsmonitor\s*=:::Sets the filesystem-monitor command git runs on ordinary operations, which is arbitrary execution'
)

# --- Read JSON from stdin ---
INPUT=$(cat)
# Full access (Claude Code or Codex permission_mode "bypassPermissions"): the
# user chose to run without approval gates, so this Nexus-Hub guard steps aside.
# Contract: docs/policy/permission-mode-contract.md
_HOST_MODE=""
if command -v jq >/dev/null 2>&1; then
  _HOST_MODE=$(printf '%s' "$INPUT" | jq -r 'if type == "object" and (.permission_mode | type) == "string" then .permission_mode else empty end' 2>/dev/null || true)
elif command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  _MODE_PYTHON=$(command -v python3 || command -v python)
  _HOST_MODE=$(printf '%s' "$INPUT" | "$_MODE_PYTHON" -c '
import json, sys
try:
    payload = json.load(sys.stdin)
    mode = payload.get("permission_mode") if isinstance(payload, dict) else None
    if isinstance(mode, str):
        print(mode)
except (ValueError, TypeError):
    pass' 2>/dev/null || true)
fi
if [ "$_HOST_MODE" = "bypassPermissions" ]; then exit 0; fi

# Extract the command from tool_input.command
# The `|| true` on both branches is load-bearing under `set -euo pipefail`: a
# grep that matches nothing, or jq on a malformed payload, returns non-zero, and a
# failing command substitution in an assignment ABORTS the script with exit 1
# instead of reaching the allow path below. Without it this hook exited 1 on any
# payload carrying no command (empty, malformed, or a non-Bash tool call).
if command -v jq >/dev/null 2>&1; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)
else
  # Fallback: basic JSON extraction via grep/sed
  COMMAND=$(echo "$INPUT" | LC_ALL=C grep -oE '"command"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//' || true)
  # Un-escape the JSON string escapes this path leaves behind. Without this the
  # extracted command is a SINGLE line carrying a literal backslash-n, which is
  # not what the user is about to run, so any line-oriented analysis below (the
  # heredoc split in particular) sees one long line instead of a script. The .ps1
  # sibling needs no equivalent step because ConvertFrom-Json already decodes
  # these; this is the cost of not having jq, not a second policy.
  #
  # An escaped backslash is parked on \x01 first, so a literal backslash sitting
  # before an n is never turned into a newline.
  COMMAND=$(printf '%s' "$COMMAND" | sed -e 's/\\\\/\x01/g' -e 's/\\n/\n/g' -e 's/\\t/\t/g' -e 's/\\"/"/g' -e 's/\\r//g' -e 's/\x01/\\/g')
fi

# Drop carriage returns however they arrived. jq on Windows can hand back CRLF
# lines, and the fallback above sees them escaped. Either way a trailing CR makes
# the closing heredoc delimiter stop matching, the body never ends, and every
# later line is swallowed unscanned - the guard fails OPEN on a destructive
# command placed after a heredoc. A CR carries no meaning in a command line.
COMMAND=${COMMAND//$(printf '\r')/}

# If we couldn't extract a command, allow (don't block non-Bash tools)
if [ -z "${COMMAND:-}" ]; then
  exit 0
fi

# --- Heredoc-body separation ---
# A command that WRITES a file (cat > doc.md <<'EOF' ... EOF) carries the file's
# text inside the same raw string the patterns are matched against. Documentation
# that merely NAMES a destructive command then reads as an attempt to RUN one.
# This is not hypothetical: writing the comparison report that introduced this
# function was blocked by exactly that false positive.
#
# The split below is deliberate about direction. Bodies are removed from the
# BLOCKING scan, but a pattern found only inside a body still emits a warning on
# stderr rather than vanishing, so the guard never silently matches less. A body
# can of course be a script that is executed later, which this cannot see -- but
# neither can it see `echo ... > x.sh`, and the header above already states that
# this hook is defense-in-depth, not a boundary. A guard that blocks ordinary
# documentation writes gets switched off, and a switched-off guard protects
# nothing.
strip_heredoc_bodies() {
  # Held in a variable because an inline bracket expression carrying BOTH quote
  # characters cannot survive bash's own quoting rules inside [[ =~ ]].
  local hd_re='<<-?[[:space:]]*["'"'"']?([A-Za-z_][A-Za-z0-9_]*)["'"'"']?'
  local line trimmed delim="" inbody=0 out=""
  while IFS= read -r line || [ -n "$line" ]; do
    if [ "$inbody" -eq 1 ]; then
      trimmed="${line#"${line%%[![:space:]]*}"}"
      if [ "$trimmed" = "$delim" ]; then
        inbody=0
      fi
      continue
    fi
    if [[ "$line" =~ $hd_re ]]; then
      delim="${BASH_REMATCH[1]}"
      inbody=1
    fi
    out+="$line"$'
'
  done
  printf '%s' "$out"
}

# SCAN drives every block decision below; COMMAND is kept for reporting and for
# the written-content warning.
SCAN=$(printf '%s' "$COMMAND" | strip_heredoc_bodies)

# --- Check command against each pattern ---
for entry in "${DANGEROUS_PATTERNS[@]}"; do
  PATTERN="${entry%%:::*}"
  DESC="${entry##*:::}"
  # git reads config keys case-insensitively, so the core.* entries must too.
  GREP_FLAGS=-qE
  case "$PATTERN" in *'core\.'*) GREP_FLAGS=-qiE ;; esac

  if echo "$SCAN" | grep "$GREP_FLAGS" "$PATTERN"; then
    echo "BLOCKED: '$COMMAND' matches dangerous git pattern. $DESC. The user has prevented you from doing this." >&2
    exit 2
  fi
  if echo "$COMMAND" | grep "$GREP_FLAGS" "$PATTERN"; then
    echo "NOTE: a dangerous git pattern ($DESC) appears inside written file content, not as a command. Allowing the write." >&2
  fi
done

# --- Persistent execution-indirection guard (group B, `git config` form) ---
# core.hooksPath and core.fsmonitor are reachable two ways: inline for a single
# invocation (`git -c key=value ...`, caught by the pattern list above) and
# PERSISTENTLY via `git config`, which writes the value into .git/config so it
# applies to every later operation. The persistent form needs its own check
# because a read of the same key is harmless: `git config --get core.hooksPath`
# only inspects, so matching the key alone would false-positive on a diagnostic
# command. Flag the write forms and let the read forms through.
if echo "$SCAN" | grep -qE '(^|[;&|]|[[:space:]])git([[:space:]]|$).*config' \
   && echo "$SCAN" | grep -qiE 'core\.(hooksPath|fsmonitor)' \
   && ! echo "$SCAN" | grep -qE '\-\-(get|get-all|get-regexp|get-urlmatch|list|unset|unset-all)([[:space:]]|=|$)'; then
  echo "BLOCKED: '$COMMAND' persists a git execution-indirection setting (core.hooksPath / core.fsmonitor). Git executes the named directory or command on ordinary operations, so this turns a later routine git call into arbitrary execution. The user has prevented you from doing this." >&2
  exit 2
fi

# --- Protected-branch guard (opt-in via NEXUS_PROTECTED_BRANCHES) ---
# When a project declares protected (release-only) branches, block a direct
# `git commit` on them so feature/version work goes through a feature branch.
# Inert by default: does nothing unless NEXUS_PROTECTED_BRANCHES is set.
#   Configure : NEXUS_PROTECTED_BRANCHES="main develop"   (space- or comma-separated)
#   Override  : NEXUS_PROTECTED_BRANCH_ALLOW=1            (allow one legitimate commit)
# Targets `git commit` only -- release merges (`git merge --no-ff` on the
# protected branch) and pushes are intentionally NOT blocked.
if [ -n "${NEXUS_PROTECTED_BRANCHES:-}" ] \
   && [ "${NEXUS_PROTECTED_BRANCH_ALLOW:-0}" != "1" ] \
   && echo "$SCAN" | grep -qE '(^|[;&|]|[[:space:]])git[[:space:]]+commit([[:space:]]|$)'; then
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  if [ -n "$CURRENT_BRANCH" ]; then
    PROTECTED_LIST=$(echo "${NEXUS_PROTECTED_BRANCHES}" | tr ',' ' ')
    for b in $PROTECTED_LIST; do
      if [ "$b" = "$CURRENT_BRANCH" ]; then
        echo "BLOCKED: direct commit to protected branch '${CURRENT_BRANCH}'. Branch off the integration branch first (e.g. 'git checkout -b feat/<slug>') and commit there; the protected branch receives release merges only. To allow this one commit, set NEXUS_PROTECTED_BRANCH_ALLOW=1." >&2
        exit 2
      fi
    done
  fi
fi

# --- Opt-in git bypass-flag guard (v4.14.4) ---
# Blocks the flags that skip git hooks or commit signing, when a team opts in.
# Inert by default. Specification: docs/decisions/*/tooling/2026-10-14-opt-in-git-bypass-flag-guard.md
#   Switch   : ~/.nexus-hub/guardrails.json  {"block_git_bypass_flags": true}
#              Read on EVERY run, so editing it takes effect on the next command.
#   Override : NEXUS_GUARD_GIT_BYPASS=1 (on) or =0 (off), read ONLY from this
#              hook's own environment. It is never parsed from the command text.
#   A missing file means off. A malformed file means off plus one stderr warning
#   naming the file; it never crashes the hook, which would block every command.
#
# Blocked when on: --no-verify (and prefixes from --no-v) on commit, push, merge,
# rebase, am; -n as a `git commit` option (the short-option scan stops at an
# option that takes an argument, so -mn and -uno are not -n); --no-gpg-sign (and
# prefixes from --no-g) on commit, merge, rebase, cherry-pick, revert; inline
# -c commit.gpgsign=<false-like> and persistent `git config commit.gpgsign|
# tag.gpgsign <false-like>`, key in any letter case; all of these after git
# global options (git -C repo commit -n). Not blocked: git push -n, git log -n,
# git commit --no-edit.
#
# Before matching, quoted -m/--message/-F/--file values and heredoc bodies that
# only write a file are stripped; a heredoc body fed to an interpreter (bash, sh,
# zsh, pwsh, powershell, python) is kept and scanned.
#
# Documented limits (this is defense-in-depth, NOT a boundary):
#   - environment-variable skips (HUSKY=0, SKIP=, LEFTHOOK=0, GIT_CONFIG_*)
#   - git plumbing (commit-tree, update-ref, hash-object)
#   - shell aliases, wrapper scripts, and git aliases
#   - bypassPermissions mode (this whole hook steps aside)
#   - an agent that edits guardrails.json or this hook itself
#   - a flag built at run time (variables, command substitution, eval), quoted
#     as a separate word, or handed to a program that runs git later
#   - git invoked through a path that contains spaces
#   - git config --unset commit.gpgsign
#   - without jq, a malformed guardrails.json is detected best effort only
bypass_mode_on() {
  case "${NEXUS_GUARD_GIT_BYPASS:-}" in
    1) return 0 ;;
    0) return 1 ;;
  esac
  local home_dir="${HOME:-${USERPROFILE:-}}"
  local cfg="$home_dir/.nexus-hub/guardrails.json"
  if [ -z "$home_dir" ] || [ ! -f "$cfg" ]; then return 1; fi
  local content verdict="" flat bom=$'\xEF\xBB\xBF'
  content=$(cat "$cfg" 2>/dev/null || true)
  content=${content#"$bom"}
  content=${content//$'\r'/}
  if command -v jq >/dev/null 2>&1; then
    verdict=$(printf '%s' "$content" | jq -r 'if type == "object" then (.block_git_bypass_flags == true | tostring) else "invalid" end' 2>/dev/null || true)
    verdict=${verdict//$'\r'/}
  else
    flat=$(printf '%s' "$content" | tr -d '[:space:]')
    case "$flat" in
      '{'*'}')
        if printf '%s' "$flat" | grep -qE '"block_git_bypass_flags":true([,}]|$)'; then verdict=true; else verdict=false; fi ;;
      *) verdict=invalid ;;
    esac
  fi
  case "$verdict" in
    true) return 0 ;;
    false) return 1 ;;
  esac
  echo "WARNING: git-guardrails: $cfg is not a valid JSON object; the git bypass-flag guard stays off." >&2
  return 1
}

# Like strip_heredoc_bodies, but keeps a body whose opener line names an
# interpreter, and does not mistake a here-string (<<<) for a heredoc.
bypass_strip_heredocs() {
  local hd_re='(^|[^<])<<-?[[:space:]]*["'"'"']?([A-Za-z_][A-Za-z0-9_]*)["'"'"']?'
  local interp_re='(^|[^A-Za-z0-9_.-])(bash|sh|zsh|pwsh|powershell|python[0-9.]*)(\.exe)?([^A-Za-z0-9_.-]|$)'
  local line trimmed delim="" inbody=0 keep=0 out="" nl=$'\n'
  while IFS= read -r line || [ -n "$line" ]; do
    if [ "$inbody" -eq 1 ]; then
      trimmed="${line#"${line%%[![:space:]]*}"}"
      if [ "$trimmed" = "$delim" ]; then
        inbody=0
      elif [ "$keep" -eq 1 ]; then
        out+="$line$nl"
      fi
      continue
    fi
    if [[ "$line" =~ $hd_re ]]; then
      delim="${BASH_REMATCH[2]}"
      inbody=1
      keep=0
      if [[ "$line" =~ $interp_re ]]; then keep=1; fi
    fi
    out+="$line$nl"
  done
  printf '%s' "$out"
}

# Replace each quoted -m/--message/-F/--file value (also attached to a short
# cluster such as -am "text") with "", so a message that names a flag is not one.
bypass_strip_messages() {
  local s="$1" m out=""
  local re='(^|[[:space:]])(-[a-zA-Z]*[mF]|--message|--file)[[:space:]]*=?[[:space:]]*("[^"]*"|'"'"'[^'"'"']*'"'"')'
  while [[ "$s" =~ $re ]]; do
    m="${BASH_REMATCH[0]}"
    out+="${s%%"$m"*}${BASH_REMATCH[1]}${BASH_REMATCH[2]} \"\""
    s="${s#*"$m"}"
  done
  printf '%s' "$out$s"
}

# Returns 0 and prints a short reason when $1 holds a bypass flag.
bypass_detect() {
  local text seg nl=$'\n'
  text=$(printf '%s' "$1" | bypass_strip_heredocs)
  text=$(bypass_strip_messages "$text")
  text=${text//\\$nl/ }
  text=${text//\`$nl/ }
  local q=$'["\']'
  local val=$'("[^"]*"|\'[^\']*\'|[^[:space:]]+)'
  local gopt="(-C[[:space:]]+$val|-c[[:space:]]+$val|--(git-dir|work-tree|namespace|super-prefix|config-env)(=|[[:space:]]+)$val|--exec-path(=[^[:space:]]+)?|--(no-pager|paginate|bare|no-replace-objects|literal-pathspecs|glob-pathspecs|noglob-pathspecs|icase-pathspecs|no-optional-locks|no-lazy-fetch|html-path|man-path|info-path)|-p|-P)"
  local pre="(^|[[:space:](\`{\"'])([^[:space:]]*[/\\\\])?git(\\.exe)?$q?([[:space:]]+$gopt)*"
  local end="([[:space:]\"'=]|\$)"
  local re_nv="${pre}[[:space:]]+(commit|push|merge|rebase|am)[[:space:]]+(.*[[:space:]])?$q?--no-v(e(r(i(f(y)?)?)?)?)?$end"
  local re_n="${pre}[[:space:]]+commit[[:space:]]+(.*[[:space:]])?-[ABDEGHIJKLMNOPQRTUVWXYZabdefghijklnopqrsvwxyz]*n[^[:space:]\"']*([[:space:]\"']|\$)"
  local re_ng="${pre}[[:space:]]+(commit|merge|rebase|cherry-pick|revert)[[:space:]]+(.*[[:space:]])?$q?--no-g(p(g(-(s(i(g(n)?)?)?)?)?)?)?$end"
  local re_inline="${pre}[[:space:]]+-c[[:space:]]*$q?(commit|tag)\\.gpgsign[[:space:]]*=[[:space:]]*$q?(false|no|off|0)?$q?([[:space:]]|\$)"
  local re_cfg="${pre}[[:space:]]+config(([[:space:]]+(--file|-f|--blob)[[:space:]]+$val)|([[:space:]]+-{1,2}[A-Za-z][A-Za-z-]*(=[^[:space:]]+)?))*[[:space:]]+$q?(commit|tag)\\.gpgsign$q?[[:space:]]+($q?(false|no|off|0)$q?|\"\"|'')([[:space:]]|\$)"
  local segments
  # shellcheck disable=SC2020
  segments=$(printf '%s' "$text" | tr ';|&' '\n\n\n')  # three separators, each mapped to a newline
  while IFS= read -r seg; do
    case "$seg" in *git*) ;; *) continue ;; esac
    if grep -qE "$re_nv" <<<"$seg"; then echo "--no-verify skips git hooks"; return 0; fi
    if grep -qE "$re_n" <<<"$seg"; then echo "-n skips git hooks"; return 0; fi
    if grep -qE "$re_ng" <<<"$seg"; then echo "--no-gpg-sign skips commit signing"; return 0; fi
    if grep -qEi "$re_inline" <<<"$seg"; then echo "an inline gpgsign=false setting skips commit signing"; return 0; fi
    if grep -qEi "$re_cfg" <<<"$seg"; then echo "persisting gpgsign=false skips commit signing"; return 0; fi
  done <<<"$segments"
  return 1
}

# The pre-filter keeps the switch file unread (and a malformed-file warning
# unprinted) for commands that do not mention git at all.
case "$COMMAND" in
  *git*)
    if bypass_mode_on; then
      if BYPASS_REASON=$(bypass_detect "$COMMAND"); then
        echo "BLOCKED: '$COMMAND' skips git hooks or commit signing ($BYPASS_REASON). The opt-in bypass-flag guard is on (~/.nexus-hub/guardrails.json key block_git_bypass_flags; override NEXUS_GUARD_GIT_BYPASS=0 or 1 in the hook environment). To turn this mode off, set block_git_bypass_flags to false in that file; the next command is judged by the new value, with no restart. The user has prevented you from doing this." >&2
        exit 2
      fi
    fi
    ;;
esac

# Command is safe
exit 0
