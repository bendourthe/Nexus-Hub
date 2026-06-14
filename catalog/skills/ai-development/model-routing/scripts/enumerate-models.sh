#!/usr/bin/env bash
# enumerate-models.sh - List the available models for a given agentic platform.
#
# Usage: enumerate-models.sh <platform-id>
#   where <platform-id> is one produced by detect-platform.sh.
#
# Prints the model list as JSON on stdout by calling that platform's OWN
# enumeration surface. When no scriptable enumeration surface exists (Cursor,
# Copilot, OpenCode, or a missing CLI), prints a picker sentinel telling the
# caller to read the model set from the platform's model picker.
#
# The ONLY outbound call this script can make is the Anthropic GET /v1/models
# endpoint for Claude Code, and ONLY when ANTHROPIC_API_KEY is already set in
# the environment. No other connection is opened and no new credential is
# required.
set -euo pipefail

readonly PICKER_SENTINEL='{"source":"picker","models":[],"note":"no scriptable model list; read models from the platform model picker"}'

enumerate() {
    local platform="${1:?usage: enumerate-models.sh <platform-id>}"
    case "$platform" in
        codex)
            if command -v codex >/dev/null 2>&1; then
                codex debug models || printf '%s\n' "$PICKER_SENTINEL"
            else
                printf '%s\n' "$PICKER_SENTINEL"
            fi
            ;;
        antigravity)
            if command -v agy >/dev/null 2>&1; then
                agy models || printf '%s\n' "$PICKER_SENTINEL"
            else
                printf '%s\n' "$PICKER_SENTINEL"
            fi
            ;;
        gemini-cli)
            # Gemini CLI's model set lives in its alias config rather than a
            # stable list subcommand; point the caller at the alias set.
            if [[ -f "${HOME}/.gemini/settings.json" ]]; then
                printf '%s\n' '{"source":"config","models":[],"note":"read model aliases from ~/.gemini/settings.json"}'
            else
                printf '%s\n' "$PICKER_SENTINEL"
            fi
            ;;
        claude-code)
            if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
                curl -sS --max-time 10 --connect-timeout 5 \
                    https://api.anthropic.com/v1/models \
                    -H "x-api-key: ${ANTHROPIC_API_KEY}" \
                    -H "anthropic-version: 2023-06-01" \
                    || printf '%s\n' "$PICKER_SENTINEL"
            else
                printf '%s\n' "$PICKER_SENTINEL"
            fi
            ;;
        cursor | copilot | opencode)
            printf '%s\n' "$PICKER_SENTINEL"
            ;;
        unknown)
            printf '%s\n' "$PICKER_SENTINEL"
            ;;
        *)
            printf 'error: unknown platform "%s"\n' "$platform" >&2
            return 2
            ;;
    esac
}

enumerate "${1:-}"
