#!/usr/bin/env bash
# detect-platform.sh - Detect the agentic platform currently running.
#
# Prints a single normalized platform id on stdout, one of:
#   claude-code | codex | antigravity | gemini-cli | cursor | copilot |
#   opencode | unknown
#
# Detection is best-effort and uses only environment cues that are already
# present: host-injected environment markers first (most reliable for the
# running host), then binary-on-PATH plus config-dir presence as an
# availability fallback. Makes ZERO outbound calls and requires no credential.
set -euo pipefail

detect_platform() {
    # 1. Host-injected environment markers (the platform you are running IN).
    if [[ -n "${CLAUDECODE:-}" || -n "${CLAUDE_CODE_ENTRYPOINT:-}" || -n "${CLAUDE_CODE_SSE_PORT:-}" ]]; then
        printf '%s\n' "claude-code"
        return 0
    fi
    if [[ -n "${CODEX_HOME:-}" || -n "${CODEX_SANDBOX:-}" ]]; then
        printf '%s\n' "codex"
        return 0
    fi
    if [[ -n "${CURSOR_TRACE_ID:-}" || -n "${CURSOR_AGENT:-}" ]]; then
        printf '%s\n' "cursor"
        return 0
    fi
    if [[ -n "${COPILOT_AGENT_ID:-}" || -n "${GITHUB_COPILOT_CLI:-}" ]]; then
        printf '%s\n' "copilot"
        return 0
    fi
    if [[ -n "${OPENCODE:-}" || -n "${OPENCODE_BIN_PATH:-}" ]]; then
        printf '%s\n' "opencode"
        return 0
    fi

    # 2. Binary-on-PATH + config-dir presence (availability fallback). Order
    #    matters: agy (Antigravity) is checked before the generic gemini binary
    #    because both live under ~/.gemini.
    if command -v agy >/dev/null 2>&1 || [[ -d "${HOME}/.gemini/antigravity-cli" ]]; then
        printf '%s\n' "antigravity"
        return 0
    fi
    if command -v codex >/dev/null 2>&1 || [[ -d "${HOME}/.codex" ]]; then
        printf '%s\n' "codex"
        return 0
    fi
    if command -v gemini >/dev/null 2>&1 || [[ -d "${HOME}/.gemini" ]]; then
        printf '%s\n' "gemini-cli"
        return 0
    fi
    if command -v opencode >/dev/null 2>&1; then
        printf '%s\n' "opencode"
        return 0
    fi

    printf '%s\n' "unknown"
}

detect_platform
