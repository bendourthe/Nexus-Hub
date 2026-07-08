#!/usr/bin/env bash
# Nexus-Hub "seed on project open" hook (v3.11.0 Phase 7.3).
#
# Project-only-surface platforms (Antigravity 2.0 reads workflows/skills/rules
# ONLY from an open project's .agents/) are not served by a global install. Source
# this file from your shell rc to auto-seed a repo's project surfaces (Antigravity
# .agents/, Cursor rules, Claude settings stub) the first time you cd into it.
#
#   Enable:  add to ~/.bashrc or ~/.zshrc:  source "$HOME/.nexus-hub/hooks/nexus-hub-autoseed.sh"
#   Disable: export NEXUS_HUB_NO_AUTOSEED=1
#
# Design: fail-open (a hook error never disrupts the shell), idempotent (a
# .nexus-hub/seeded marker prevents re-seeding), and opt-out via the env var. The
# installer NEVER auto-edits your shell rc; enabling this hook is your explicit
# opt-in. Lockstep with nexus-hub-autoseed.ps1.

_nexus_hub_autoseed() {
    [ "${NEXUS_HUB_NO_AUTOSEED:-0}" = "1" ] && return 0
    command -v nexus-hub >/dev/null 2>&1 || return 0
    local top
    top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 0
    [ -n "$top" ] || return 0
    # Never seed the Nexus-Hub source cache; skip already-seeded repos.
    case "$top" in "$HOME/.nexus-hub"|"$HOME/.nexus-hub"/*) return 0 ;; esac
    [ -f "$top/.nexus-hub/seeded" ] && return 0
    # Fail-open: swallow every error so the prompt is never disrupted.
    (
        nexus-hub init --target "$top" --quiet >/dev/null 2>&1 \
            && mkdir -p "$top/.nexus-hub" \
            && : > "$top/.nexus-hub/seeded"
    ) 2>/dev/null || true
}

# Register on directory change: zsh chpwd hook, else bash PROMPT_COMMAND.
if [ -n "${ZSH_VERSION:-}" ]; then
    autoload -Uz add-zsh-hook 2>/dev/null && add-zsh-hook chpwd _nexus_hub_autoseed 2>/dev/null || true
elif [ -n "${BASH_VERSION:-}" ]; then
    case "${PROMPT_COMMAND:-}" in
        *_nexus_hub_autoseed*) : ;;
        *) PROMPT_COMMAND="_nexus_hub_autoseed;${PROMPT_COMMAND:-}" ;;
    esac
fi
