#!/usr/bin/env bash
# switch-model.sh - Apply a model + effort switch for a given agentic platform.
#
# Usage: switch-model.sh <platform-id> <model-id> [effort-level]
#   <platform-id>   one produced by detect-platform.sh
#   <model-id>      a model from the platform's enumerated set (enumerate-models.sh)
#   [effort-level]  optional reasoning effort (low|medium|high|xhigh|max), where
#                   the platform exposes an effort knob; ignored otherwise.
#
# Behavior follows the three-tier switch spectrum:
#   - Scriptable (codex, antigravity, gemini-cli): validate the model against
#     the enumerated set, then print the exact NON-INTERACTIVE switch command
#     that applies it on the next invocation. Emitting the command is the
#     switch artifact: a subprocess helper cannot mutate a sibling CLI's live
#     session, and silently rewriting a user config file would be a surprising
#     side effect, so the deterministic, idempotent action is to print the
#     documented mechanism.
#   - One user action (claude-code): the main loop cannot switch its own model
#     mid-session; print the exact /model (+ /effort) keystroke to type.
#   - Manual only (cursor, copilot, opencode): print the model-picker step.
#
# Model validation: the requested model must appear in the enumerated set
# before a scriptable switch is emitted. The set is taken from
# NEXUS_ROUTING_MODELS when that env var is set (a comma/space/newline list the
# caller already enumerated for the session - this avoids re-enumerating),
# otherwise from the sibling enumerate-models.sh. When the set cannot be
# enumerated (the CLI is absent and no NEXUS_ROUTING_MODELS is supplied), the
# helper refuses rather than guess.
#
# Idempotent, zero outbound calls, no new credential. The only network surface
# in this skill is the optional Anthropic GET /v1/models inside
# enumerate-models.sh, which this script may invoke for validation and which is
# itself gated on ANTHROPIC_API_KEY already being present.
#
# Exit codes: 0 success; 2 usage/unknown platform; 3 model not in enumerated
# set; 4 enumeration unavailable so the model could not be validated.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR

log_error() { printf '[ERROR] %s\n' "$*" >&2; }
log_info()  { printf '[INFO]  %s\n' "$*" >&2; }

# Resolve the enumerated model set into a newline-delimited list on stdout, or
# return non-zero when no scriptable set is available.
enumerated_models() {
    local platform="$1"

    # 1. Caller-supplied set (already enumerated for the session).
    if [[ -n "${NEXUS_ROUTING_MODELS:-}" ]]; then
        printf '%s\n' "${NEXUS_ROUTING_MODELS}" | tr ', ' '\n\n' | grep -v '^$' || true
        return 0
    fi

    # 2. Enumerate via the sibling helper.
    local enumerate="${SCRIPT_DIR}/enumerate-models.sh"
    if [[ ! -x "$enumerate" && ! -f "$enumerate" ]]; then
        return 1
    fi
    local out
    out="$(bash "$enumerate" "$platform" 2>/dev/null || true)"
    if [[ -z "$out" ]]; then
        return 1
    fi
    # A picker/config sentinel carries no scriptable list -> cannot validate.
    if printf '%s' "$out" | grep -Eq '"source":"(picker|config)"'; then
        return 1
    fi
    # Print the raw enumeration blob. Different platforms name the model field
    # differently (Codex uses "slug", the Anthropic API uses "id"), and the JSON
    # also carries unrelated ids (e.g. service-tier ids), so a targeted field
    # extraction is fragile. The caller validates by substring against this
    # blob, which accepts any model id that appears in the live enumeration.
    printf '%s\n' "$out"
    return 0
}

# Return 0 if model is present in the enumerated set, 3 if absent, 4 if the set
# cannot be determined.
validate_model() {
    local platform="$1" model="$2"
    local set_out
    if ! set_out="$(enumerated_models "$platform")"; then
        return 4
    fi
    if printf '%s\n' "$set_out" | grep -qxF -- "$model"; then
        return 0
    fi
    # Fallback substring match for raw-blob sets (non-line-delimited JSON).
    if printf '%s' "$set_out" | grep -qF -- "$model"; then
        return 0
    fi
    return 3
}

# Validate then print the scriptable switch command, or refuse.
emit_scriptable_switch() {
    local platform="$1" model="$2" effort="$3"
    local rc=0
    validate_model "$platform" "$model" || rc=$?
    case "$rc" in
        3)
            log_error "model '${model}' is not in the enumerated set for '${platform}'; refusing to switch."
            return 3
            ;;
        4)
            log_error "cannot validate '${model}' for '${platform}': model enumeration is unavailable."
            log_info  "install the platform CLI, or pass the enumerated set via NEXUS_ROUTING_MODELS."
            return 4
            ;;
    esac

    case "$platform" in
        codex)
            if [[ -n "$effort" ]]; then
                printf 'codex -c model=%s -c model_reasoning_effort=%s\n' "$model" "$effort"
            else
                printf 'codex -c model=%s\n' "$model"
            fi
            ;;
        antigravity)
            printf 'agy -m %s\n' "$model"
            [[ -n "$effort" ]] && log_info "antigravity exposes no documented effort knob; effort '${effort}' ignored."
            ;;
        gemini-cli)
            printf 'gemini --model %s\n' "$model"
            log_info "or set GEMINI_MODEL=${model} / settings.json model.name=${model} for a persistent switch."
            [[ -n "$effort" ]] && log_info "gemini-cli exposes no documented effort knob; effort '${effort}' ignored."
            ;;
    esac
    log_info "scriptable switch for '${platform}' -> ${model}${effort:+ (effort: ${effort})}: run the command above to apply on the next invocation."
    return 0
}

main() {
    local platform="${1:?usage: switch-model.sh <platform-id> <model-id> [effort-level]}"
    local model="${2:?usage: switch-model.sh <platform-id> <model-id> [effort-level]}"
    local effort="${3:-}"

    case "$platform" in
        codex | antigravity | gemini-cli)
            emit_scriptable_switch "$platform" "$model" "$effort"
            ;;
        claude-code)
            printf 'Type in this session: /model %s\n' "$model"
            [[ -n "$effort" ]] && printf 'Then type: /effort %s\n' "$effort"
            log_info "claude-code cannot switch its own model from a script; type the instruction(s) above. Delegated subagent work can be routed via the Task/Workflow model parameter."
            ;;
        cursor | copilot | opencode)
            printf 'Select "%s" in the %s model picker.\n' "$model" "$platform"
            log_info "${platform} exposes no scriptable switch surface; select the model manually."
            ;;
        unknown | "")
            log_error "platform is unknown; cannot switch. Run detect-platform.sh first."
            return 2
            ;;
        *)
            log_error "unrecognized platform '${platform}'."
            return 2
            ;;
    esac
}

main "$@"
