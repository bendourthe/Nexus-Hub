#!/usr/bin/env bash
# Interactive, resumable wizard template.
# Adapt step ids, titles, and checks to the human-only sequence.
# Do not eval. Do not echo secrets. Quote every expansion.
#
# Usage:
#   ./wizard-template.sh
#   WIZARD_STATE_FILE=/tmp/my-wizard-state ./wizard-template.sh
#
# State file: one completed step id per line. Lines starting with # are ignored.

set -euo pipefail

readonly STATE_FILE="${WIZARD_STATE_FILE:-.wizard-state}"

log() {
  printf '%s\n' "$*"
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

step_done() {
  local id="$1"
  [[ -f "$STATE_FILE" ]] || return 1
  # Strip CR so a Windows-edited state file still matches.
  # `|| return` is required under `set -e`: a non-match must not abort the script.
  tr -d '\r' <"$STATE_FILE" | grep -Fxq -- "$id" || return 1
  return 0
}

mark_done() {
  local id="$1"
  local dir
  dir="$(dirname -- "$STATE_FILE")"
  mkdir -p -- "$dir"
  printf '%s\n' "$id" >>"$STATE_FILE"
}

confirm() {
  local prompt="$1"
  local reply
  printf '%s' "$prompt"
  read -r reply
  case "$reply" in
    ""|y|Y|yes|YES) return 0 ;;
    *) die "aborted at confirmation" ;;
  esac
}

# Return 0 when the observable holds.
check_file_exists() {
  local path="$1"
  [[ -e "$path" ]]
}

# Example human-only steps. Replace ids, copy, and checks.
# Keep ids identical to the PowerShell sibling.

step_welcome() {
  local id="welcome"
  step_done "$id" && { log "skip $id (already completed)"; return 0; }
  log ""
  log "== $id =="
  log "This wizard walks human-only setup. The agent that generated it must not run privileged steps for you."
  log "Why: a resumable script beats a half-remembered checklist."
  confirm "Press Enter to start (or type n to abort): "
  mark_done "$id"
}

step_example_observable() {
  local id="example-observable"
  local marker="${WIZARD_EXAMPLE_MARKER:-.wizard-example-marker}"
  step_done "$id" && { log "skip $id (already completed)"; return 0; }
  log ""
  log "== $id =="
  log "Do: create the marker file the check expects."
  log "Why: the next steps assume this observable exists."
  log "Expected: a file at $marker"
  log "Create it yourself (the wizard will not write secrets or privileged files)."
  confirm "Press Enter after the file exists: "
  if ! check_file_exists "$marker"; then
    die "expected file missing: $marker (step not marked complete; re-run to retry)"
  fi
  mark_done "$id"
}

step_complete() {
  local id="complete"
  step_done "$id" && { log "skip $id (already completed)"; return 0; }
  log ""
  log "== $id =="
  log "All adapted steps finished. State file: $STATE_FILE"
  mark_done "$id"
}

main() {
  umask 077
  step_welcome
  step_example_observable
  step_complete
  log "wizard finished"
}

main "$@"
