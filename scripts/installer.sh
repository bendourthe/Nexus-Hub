#!/bin/bash
# Nexus-Hub Universal Installer V10 (macOS/Linux)
# Installs AI Skills Globally OR to a Workspace with Safe Overwrite

set -e

# --- Version ---
# Single source of truth for the installer banner version label.
# Keep in sync with .claude-plugin/plugin.json and CHANGELOG.md.
NEXUS_HUB_VERSION="3.6.0"

# --- Window Title ---
printf '\033]0;Nexus-Hub Installer\007'

# --- Colors ---
RESET='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
DARK_YELLOW='\033[0;33m' # Approximate
BRIGHT_CYAN='\033[0;96m'    # OpenCode - distinct from the teal CYAN used by Microsoft
BRIGHT_MAGENTA='\033[0;95m' # Anysphere/Cursor - distinct from the dark MAGENTA used by OpenAI
DARK_BLUE='\033[38;5;18m'   # Nexus - navy, distinct from the BLUE used by Google
# DARK_CYAN removed in v2.1.0 - only used by the legacy 120-char banner rules.

# Resolved overwrite decision (v3.7.0 / Phase 2).
#   true  = "refresh" mode: existing managed files are overwritten with the
#           Nexus-Hub version silently (the non-interactive / --yes / --force /
#           bootstrap path). Also threaded to the registry runner as --overwrite.
#   false = "conflict-collection" mode (interactive, no --yes/--force): managed
#           single files whose on-disk content differs are recorded as conflicts
#           and KEPT; after the install pass resolve_conflicts() lists them and
#           asks once whether to overwrite. Resolved once at startup; install_*
#           no longer toggle it.
OVERWRITE_ALL=false

# Non-interactive / assume-yes decision (v3.7.0 / Phase 2). True under --yes,
# --force, or when stdin is not a TTY (piped curl|bash, CI). Drives both the
# OVERWRITE_ALL refresh decision and the suppression of any remaining content
# prompts (e.g. workspace language selection).
ASSUME_YES=false

# Conflict accumulators (interactive mode only). Parallel arrays of source ->
# destination pairs for managed single files that differ on disk and were kept
# pending the single end-of-run confirmation in resolve_conflicts().
CONFLICT_SRCS=()
CONFLICT_DSTS=()

# Temp files created for deferred writes (e.g. the generated Copilot workspace
# instruction file routed through safe_copy). Cleaned on EXIT.
TEMP_FILES=()
cleanup_temp_files() {
    local f
    for f in ${TEMP_FILES[@]+"${TEMP_FILES[@]}"}; do
        [ -n "$f" ] && rm -f "$f"
    done
}
trap cleanup_temp_files EXIT

# Platform subset filter (v3.7.0 / Phase 2). Empty = install ALL platforms
# (the default). Otherwise a space-delimited set of integration keys; only the
# matching per-provider blocks run. Populated from --platforms <csv>.
PLATFORMS_FILTER=""

# should_install <integration-key> -- gate a per-provider install block on the
# --platforms subset. Returns 0 (install) when no filter is set or the key is in
# the filter; 1 (skip) otherwise.
should_install() {
    [ -z "$PLATFORMS_FILTER" ] && return 0
    case " $PLATFORMS_FILTER " in
        *" $1 "*) return 0 ;;
        *) return 1 ;;
    esac
}

# --- Formatting Helpers ---

# Modernized in v2.1.0: dropped the 120-char dash rules in favor of light
# typographical accents. Function names are preserved so call sites and smoke
# tests do not need to change.

get_provider_color() {
    # Provider-level headers (v2.1.0+)
    case "$1" in
        "ANTHROPIC")        echo -ne "${DARK_YELLOW}" ;;
        "OPENAI")           echo -ne "${MAGENTA}" ;;
        "GOOGLE")           echo -ne "${BLUE}" ;;
        "MICROSOFT")        echo -ne "${CYAN}" ;;
        "ANYSPHERE")        echo -ne "${BRIGHT_MAGENTA}" ;;
        "OPENCODE")         echo -ne "${BRIGHT_CYAN}" ;;
        "NEXUS")            echo -ne "${DARK_BLUE}" ;;
        *)                  echo -ne "${RESET}" ;;
    esac
}

write_header() {
    local provider="$1"
    local color
    color=$(get_provider_color "$provider")
    echo ""
    echo -e "  ${color}> ${provider}${RESET}"
}

write_item() {
    local message="$1"
    local color_code="$2" # e.g., $GREEN
    local indent="${3:-2}"

    local spaces=""
    for ((i=0; i<indent; i++)); do spaces+=" "; done

    if [ -z "$color_code" ]; then color_code="${RESET}"; fi
    echo -e "${spaces}${color_code}${message}${RESET}"
}

read_prompt() {
    local message="$1"
    local indent="${2:-2}"

    local spaces=""
    for ((i=0; i<indent; i++)); do spaces+=" "; done

    echo -ne "${spaces}${YELLOW}${message}: ${RESET}" >&2
    read -r response
    echo "$response"
}

write_subsection_banner() {
    local text="$1"
    local color="${2:-$YELLOW}"
    echo ""
    echo -e "  ${color}- ${text}${RESET}"
}

# Copy a single managed file with conflict-only overwrite semantics (v3.7.0 /
# Phase 2). The third parameter (`confirm`) is retained for call-site signature
# compatibility but no longer gates a prompt: conflict handling is now uniform
# and driven by the resolved OVERWRITE_ALL decision.
#
#   - source missing                -> skip-with-note
#   - destination missing           -> create
#   - destination identical to src  -> nothing to do (idempotent, silent)
#   - destination differs:
#       OVERWRITE_ALL=true (refresh)  -> overwrite now
#       OVERWRITE_ALL=false (interactive) -> record conflict + KEEP; the single
#         end-of-run resolve_conflicts() prompt decides whether to overwrite.
safe_copy() {
    local source="$1"
    local destination="$2"
    # The 3rd positional arg (formerly the per-file confirm flag) is retained so
    # the ~30 existing 4-arg call sites keep working; conflict handling is now
    # uniform and driven by OVERWRITE_ALL, so the value itself is unused.
    # shellcheck disable=SC2034
    local confirm="${3:-false}"
    local custom_message="$4"

    if [ ! -f "$source" ]; then
        write_item "Skip: Source not found ($(basename "$source"))" "$GRAY"
        return
    fi

    if [ -f "$destination" ]; then
        if cmp -s "$source" "$destination"; then
            # Already current -- nothing to write.
            return
        fi
        if [ "$OVERWRITE_ALL" != true ]; then
            # Interactive conflict: a managed file the user may have customized
            # differs from the catalog version. Keep it for now and defer to the
            # single end-of-run confirmation.
            CONFLICT_SRCS+=("$source")
            CONFLICT_DSTS+=("$destination")
            write_item "Differs (kept; pending confirmation): $destination" "$DARK_YELLOW"
            return
        fi
    fi

    mkdir -p "$(dirname "$destination")"
    cp "$source" "$destination"
    if [ -n "$custom_message" ]; then
        write_item "$custom_message" "$GREEN"
    else
        write_item "[OK] Installed to $destination" "$GREEN"
    fi
}

# Recursively copies an entire folder tree from source to destination.
#
# Per-skill bundled resources (scripts/, references/, assets/) under
# catalog/skills/<cat>/<name>/ are copied recursively as part of the parent
# skill folder copy - both the rsync -a path and the cp -R fallback preserve
# arbitrary subdirectory depth. This is the auto-distribution behavior
# documented in AGENTS.md "Per-skill Bundled Resources"; no per-skill
# explicit-name copy step is needed for skill-bundled content.
safe_folder_copy() {
    local source="$1"
    local destination="$2"
    local custom_message="$3"

    if [ ! -d "$source" ]; then
        return
    fi

    local do_copy=true

    # Catalog trees (skills/commands/agents/rules) are Nexus-owned content meant
    # to be refreshed on every install/upgrade, so they no longer prompt
    # (v3.7.0 / Phase 2). The resolved OVERWRITE_ALL decision picks the sync mode:
    #   refresh (true)      -> full sync: refresh files AND remove stale ones
    #                          (the non-interactive / --yes / --force / bootstrap
    #                          path; matches the previous "[A]ll" behavior).
    #   interactive (false) -> merge-only: add/update files but keep any extras
    #                          the user added (never destructive, no prompt).
    local full_sync=true
    [ "$OVERWRITE_ALL" = true ] || full_sync=false

    if [ ! -d "$destination" ]; then
        mkdir -p "$destination"
    fi

    if [ "$do_copy" = true ]; then
        if [ "$full_sync" = true ]; then
            write_item "Syncing (stale files in destination will be removed)..." "$GRAY"
            # Use rsync if available, otherwise cp
            if command -v rsync >/dev/null 2>&1; then
                rsync -a --delete "$source/" "$destination/"
            else
                rm -rf "${destination:?}"/*
                cp -R "$source/"* "$destination/"
            fi
        else
            write_item "Merging (adding/updating files, keeping extras)..." "$GRAY"
            if command -v rsync >/dev/null 2>&1; then
                rsync -a "$source/" "$destination/"
            else
                cp -R "$source/"* "$destination/"
            fi
        fi

        if [ -n "$custom_message" ]; then
            write_item "$custom_message" "$GREEN"
        else
            write_item "[OK] Installed to $destination" "$GREEN"
        fi
    fi
}

# Resolve any conflicts accumulated by safe_copy during an interactive install
# (v3.7.0 / Phase 2). Conflicts are only ever recorded in interactive mode
# (OVERWRITE_ALL=false), so this prints the list, asks ONCE, and -- on
# confirmation -- overwrites the kept files with the Nexus-Hub version. The
# non-interactive / --yes / --force path overwrites inline and reaches here with
# an empty list (no-op).
resolve_conflicts() {
    local count="${#CONFLICT_DSTS[@]}"
    [ "$count" -eq 0 ] && return 0

    write_subsection_banner "Existing customizations detected"
    write_item "${count} managed file(s) on disk differ from the Nexus-Hub version:" "$YELLOW"
    local i
    for ((i=0; i<count; i++)); do
        write_item "- ${CONFLICT_DSTS[$i]}" "$DARK_YELLOW"
    done

    local resp
    resp=$(read_prompt "Overwrite these with the Nexus-Hub version? [y/N]")
    if [[ "$resp" =~ ^[Yy] ]]; then
        for ((i=0; i<count; i++)); do
            mkdir -p "$(dirname "${CONFLICT_DSTS[$i]}")"
            cp "${CONFLICT_SRCS[$i]}" "${CONFLICT_DSTS[$i]}"
            write_item "[OK] Refreshed ${CONFLICT_DSTS[$i]}" "$GREEN"
        done
    else
        write_item "Kept your ${count} customized file(s). Re-run with --yes (or --force) to refresh them." "$GRAY"
    fi
}

# --- Hook Installation ---

install_git_guardrails() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"  # "Global" or "Workspace"

    # Copy hook script
    local hooks_dir="$target_claude_dir/hooks"
    mkdir -p "$hooks_dir"
    safe_copy "$repo_root/catalog/hooks/git-guardrails.sh" "$hooks_dir/git-guardrails.sh" true "[OK] $scope git guardrails hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/git-guardrails.sh" 2>/dev/null || true

    # compress-output.sh is the other PreToolUse Bash hook; it ships alongside
    # git-guardrails because the settings.json merge below pulls the whole
    # PreToolUse array (which now includes it). It is opt-in / default-off
    # (inert unless NEXUS_CONTEXT_COMPRESS=1), so copying the file is harmless.
    safe_copy "$repo_root/catalog/hooks/compress-output.sh" "$hooks_dir/compress-output.sh" true "[OK] $scope output-compression hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/compress-output.sh" 2>/dev/null || true

    # Merge hook config into settings.json
    local settings_file="$target_claude_dir/settings.json"
    local template_file="$repo_root/catalog/hooks/settings.json"

    if [ ! -f "$template_file" ]; then
        write_item "Skip: Hook template not found" "$GRAY"
        return
    fi

    if [ -f "$settings_file" ]; then
        # Check if guardrails already installed
        if grep -q "git-guardrails" "$settings_file" 2>/dev/null; then
            write_item "[OK] Git guardrails hook already configured in settings.json" "$GREEN"
            return
        fi

        # Merge using jq if available
        if command -v jq >/dev/null 2>&1; then
            local merged
            merged=$(jq -s '
                .[0] as $existing | .[1] as $template |
                if $existing.hooks then
                    if $existing.hooks.PreToolUse then
                        $existing | .hooks.PreToolUse += $template.hooks.PreToolUse
                    else
                        $existing | .hooks.PreToolUse = $template.hooks.PreToolUse
                    end
                else
                    $existing + {hooks: $template.hooks}
                end
            ' "$settings_file" "$template_file" 2>/dev/null)

            if [ -n "$merged" ]; then
                echo "$merged" > "$settings_file"
                write_item "[OK] $scope settings.json updated with git guardrails hook" "$GREEN"
            else
                write_item "Warning: Could not merge into existing settings.json" "$YELLOW"
                write_item "  You may need to manually add the hook config" "$YELLOW"
            fi
        else
            write_item "Warning: jq not found, cannot merge settings.json automatically" "$YELLOW"
            write_item "  Please manually add hook config from: $template_file" "$YELLOW"
        fi
    else
        # No existing settings.json, copy template
        cp "$template_file" "$settings_file"
        write_item "[OK] $scope settings.json created with git guardrails hook" "$GREEN"
    fi
}

install_usage_display() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"  # "Global" or "Workspace"

    # Copy hook script
    local hooks_dir="$target_claude_dir/hooks"
    mkdir -p "$hooks_dir"
    safe_copy "$repo_root/catalog/hooks/usage-display.sh" "$hooks_dir/usage-display.sh" true "[OK] $scope usage display hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/usage-display.sh" 2>/dev/null || true

    # Merge Stop hook config into settings.json
    local settings_file="$target_claude_dir/settings.json"
    local template_file="$repo_root/catalog/hooks/settings.json"

    if [ ! -f "$template_file" ]; then
        write_item "Skip: Hook template not found" "$GRAY"
        return
    fi

    if [ -f "$settings_file" ]; then
        # Check if usage-display already installed
        if grep -q "usage-display" "$settings_file" 2>/dev/null; then
            write_item "[OK] Usage display hook already configured in settings.json" "$GREEN"
            return
        fi

        # Merge using jq if available
        if command -v jq >/dev/null 2>&1; then
            local merged
            merged=$(jq -s '
                .[0] as $existing | .[1] as $template |
                if $existing.hooks then
                    if $existing.hooks.Stop then
                        $existing | .hooks.Stop += $template.hooks.Stop
                    else
                        $existing | .hooks.Stop = $template.hooks.Stop
                    end
                else
                    $existing + {hooks: {Stop: $template.hooks.Stop}}
                end
            ' "$settings_file" "$template_file" 2>/dev/null)

            if [ -n "$merged" ]; then
                echo "$merged" > "$settings_file"
                write_item "[OK] $scope settings.json updated with usage display hook" "$GREEN"
            else
                write_item "Warning: Could not merge usage display hook into settings.json" "$YELLOW"
                write_item "  You may need to manually add the Stop hook config" "$YELLOW"
            fi
        else
            write_item "Warning: jq not found, cannot merge settings.json automatically" "$YELLOW"
            write_item "  Please manually add Stop hook config from: $template_file" "$YELLOW"
        fi
    fi
    # If no settings.json exists, install_git_guardrails will create it from the
    # template (which now includes both PreToolUse and Stop hooks).
}

install_require_description() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"  # "Global" or "Workspace"

    # Copy hook scripts
    local hooks_dir="$target_claude_dir/hooks"
    mkdir -p "$hooks_dir"
    safe_copy "$repo_root/catalog/hooks/require-description.sh" "$hooks_dir/require-description.sh" true "[OK] $scope require-description hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/require-description.sh" 2>/dev/null || true
    safe_copy "$repo_root/catalog/hooks/format-bash-description.py" "$hooks_dir/format-bash-description.py" true "[OK] $scope format-bash-description hook installed at: $hooks_dir"
    safe_copy "$repo_root/catalog/hooks/require-powershell-description.sh" "$hooks_dir/require-powershell-description.sh" true "[OK] $scope require-powershell-description hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/require-powershell-description.sh" 2>/dev/null || true
    safe_copy "$repo_root/catalog/hooks/format-powershell-description.py" "$hooks_dir/format-powershell-description.py" true "[OK] $scope format-powershell-description hook installed at: $hooks_dir"

    # Merge hook config into settings.json
    local settings_file="$target_claude_dir/settings.json"

    if [ ! -f "$settings_file" ]; then
        # install_git_guardrails will create it from the template (which includes both Bash and PowerShell description hooks)
        return
    fi

    if ! command -v jq >/dev/null 2>&1; then
        write_item "Warning: jq not found, cannot merge description hooks into settings.json automatically" "$YELLOW"
        write_item "  Please manually add the PreToolUse hooks for require-description.sh and require-powershell-description.sh" "$YELLOW"
        return
    fi

    # Bash require-description: check uses a more specific pattern so it does
    # not match require-powershell-description.
    if grep -qE 'require-description\.sh|require-description"' "$settings_file" 2>/dev/null; then
        write_item "[OK] Require-description (Bash) hook already configured in settings.json" "$GREEN"
    else
        local merged_bash
        merged_bash=$(jq '.hooks.PreToolUse |= (. + [{"matcher": "Bash", "hooks": [{"type": "command", "command": "bash .claude/hooks/require-description.sh"}]}])' "$settings_file" 2>/dev/null)
        if [ -n "$merged_bash" ]; then
            echo "$merged_bash" > "$settings_file"
            write_item "[OK] $scope settings.json updated with require-description (Bash) hook" "$GREEN"
        else
            write_item "Warning: Could not merge require-description (Bash) hook into settings.json" "$YELLOW"
        fi
    fi

    # PowerShell require + format hooks: registered independently from Bash so
    # an upgrade path that already has the Bash hook still picks these up.
    if grep -q "require-powershell-description" "$settings_file" 2>/dev/null; then
        write_item "[OK] Require-description (PowerShell) hook already configured in settings.json" "$GREEN"
    else
        local merged_ps
        merged_ps=$(jq '.hooks.PreToolUse |= (. + [
            {"matcher": "PowerShell", "hooks": [{"type": "command", "command": "python3 .claude/hooks/format-powershell-description.py"}]},
            {"matcher": "PowerShell", "hooks": [{"type": "command", "command": "bash .claude/hooks/require-powershell-description.sh"}]}
        ])' "$settings_file" 2>/dev/null)
        if [ -n "$merged_ps" ]; then
            echo "$merged_ps" > "$settings_file"
            write_item "[OK] $scope settings.json updated with PowerShell description hooks" "$GREEN"
        else
            write_item "Warning: Could not merge PowerShell description hooks into settings.json" "$YELLOW"
            write_item "  You may need to manually add the PowerShell PreToolUse hooks" "$YELLOW"
        fi
    fi
}

install_core_settings() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"

    local settings_file="$target_claude_dir/settings.json"
    local template_file="$repo_root/catalog/hooks/settings.json"

    if [ ! -f "$settings_file" ]; then
        write_item "Skip: settings.json not found, will be created by hook installer" "$GRAY"
        return
    fi

    if ! command -v jq >/dev/null 2>&1; then
        write_item "Warning: jq not found, cannot set core settings (effortLevel, model, env)" "$YELLOW"
        write_item "  Manually copy effortLevel/model/env from $template_file to $settings_file" "$YELLOW"
        return
    fi

    # Core defaults seeded from the template: effortLevel + model, plus the
    # env.CLAUDE_CODE_EFFORT_LEVEL override. The env var is the highest-precedence
    # effort lever per the Claude Code docs, so it forces the effort past the VS
    # Code effort toggle (which otherwise resets to the model default each session).
    local template_effort template_model template_env_effort
    template_effort=$(jq -r '.effortLevel' "$template_file" 2>/dev/null)
    template_model=$(jq -r '.model' "$template_file" 2>/dev/null)
    template_env_effort=$(jq -r '.env.CLAUDE_CODE_EFFORT_LEVEL' "$template_file" 2>/dev/null)

    # Idempotency: skip only if all three already match the template.
    if jq -e -s '
        .[0] as $e | .[1] as $t |
        ($e.effortLevel == $t.effortLevel)
        and ($e.model == $t.model)
        and ($e.env.CLAUDE_CODE_EFFORT_LEVEL == $t.env.CLAUDE_CODE_EFFORT_LEVEL)
    ' "$settings_file" "$template_file" >/dev/null 2>&1; then
        write_item "[OK] Core settings (effortLevel, model, env effort) already current in settings.json" "$GREEN"
        return
    fi

    # Merge scalars and deep-merge the env key, preserving any sibling env vars.
    local merged
    merged=$(jq -s '
        .[0] as $e | .[1] as $t |
        $e
        + {effortLevel: $t.effortLevel, model: $t.model}
        | .env = ((.env // {}) + {CLAUDE_CODE_EFFORT_LEVEL: $t.env.CLAUDE_CODE_EFFORT_LEVEL})
    ' "$settings_file" "$template_file" 2>/dev/null)

    if [ -n "$merged" ]; then
        echo "$merged" > "$settings_file"
        write_item "[OK] $scope settings.json updated core settings (effortLevel: ${template_effort}, model: ${template_model}, env CLAUDE_CODE_EFFORT_LEVEL: ${template_env_effort})" "$GREEN"
    else
        write_item "Warning: Could not merge core settings into settings.json" "$YELLOW"
    fi
}

# --- Permission Installation ---

# Ensure the OpenAI Codex CLI is present before writing its config. Nexus-Hub
# configures Codex permissions on every install; when the CLI is absent the
# config is never validated until the user installs Codex later, so install it
# now (via npm) when missing. Non-fatal: a failed or skipped install only prints
# a hint and never aborts the installer.
ensure_codex_cli() {
    if command -v codex >/dev/null 2>&1; then
        write_item "[OK] Codex CLI detected" "$GREEN"
        return 0
    fi
    if command -v npm >/dev/null 2>&1; then
        write_item "Codex CLI not found; installing (npm install -g @openai/codex)..." "$GRAY"
        if npm install -g @openai/codex >/dev/null 2>&1 && command -v codex >/dev/null 2>&1; then
            write_item "[OK] Codex CLI installed" "$GREEN"
        else
            write_item "Warning: could not auto-install Codex CLI. Install manually: npm install -g @openai/codex" "$YELLOW"
        fi
    else
        write_item "Codex CLI not found and npm is unavailable. Install Node.js, then run: npm install -g @openai/codex" "$YELLOW"
    fi
}

install_permissions() {
    local repo_root="$1"
    local platform="$2"    # "CLAUDE", "GEMINI", "CODEX", "COPILOT"
    local scope="$3"       # "Global" or "Workspace"
    local user_home="$HOME"
    local perm_dir="$repo_root/configs/permissions"

    case "$platform" in
        CLAUDE)
            local config_dir="$user_home/.claude"
            local settings_file="$config_dir/settings.json"
            local template_file="$perm_dir/claude-permissions.json"

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Claude permissions template not found" "$GRAY"
                return
            fi

            if [ -f "$settings_file" ]; then
                if ! command -v jq >/dev/null 2>&1; then
                    write_item "Warning: jq not found, cannot merge permissions automatically" "$YELLOW"
                    write_item "  Copy permissions manually from: $template_file" "$YELLOW"
                    return
                fi

                # Compute how many template entries are not already present.
                # Counting BEFORE merging avoids the stale-sentinel bug where a
                # single fixed marker (e.g. 'Bash(gh pr list)') made the
                # installer think permissions were "already installed" and skip
                # merging new entries shipped in later versions.
                local new_count
                new_count=$(jq -sr '
                    .[0] as $existing | .[1] as $template |
                    ($existing.permissions.allow // []) as $ea |
                    ($template.permissions.allow // []) as $ta |
                    (($ea + $ta | unique) | length) - ($ea | length)
                ' "$settings_file" "$template_file" 2>/dev/null)

                if [ "$new_count" = "0" ]; then
                    write_item "[OK] Auto-approve permissions up to date in settings.json (0 new entries)" "$GREEN"
                    return
                fi

                # Backup before modifying
                local backup_path
                backup_path="$settings_file.bak.$(date +%Y%m%d-%H%M%S)"
                cp "$settings_file" "$backup_path"
                write_item "  Backup created: $backup_path" "$GRAY"

                local merged
                merged=$(jq -s '
                    .[0] as $existing | .[1] as $template |
                    ($existing.permissions.allow // []) as $ea |
                    ($template.permissions.allow // []) as $ta |
                    $existing | .permissions.allow = ($ea + $ta | unique)
                ' "$settings_file" "$template_file" 2>/dev/null)

                if [ -n "$merged" ]; then
                    echo "$merged" > "$settings_file"
                    write_item "[OK] $scope auto-approve permissions added to settings.json (${new_count} new entries)" "$GREEN"
                else
                    write_item "Warning: Could not merge permissions into settings.json" "$YELLOW"
                    return
                fi
            else
                mkdir -p "$config_dir"
                # Create settings.json with just the permissions key
                if command -v jq >/dev/null 2>&1; then
                    jq '{permissions: .permissions}' "$template_file" > "$settings_file"
                else
                    cp "$template_file" "$settings_file"
                fi
                write_item "[OK] $scope settings.json created with auto-approve permissions" "$GREEN"
            fi

            write_item "  Auto-approved: file reads, search (Glob/Grep), web search, git read-only commands" "$GRAY"
            write_item "  WebFetch: scoped to trusted domains (see $settings_file to customize)" "$GRAY"
            write_item "  NOT auto-approved: file writes, destructive commands, git mutations, package installs" "$GRAY"
            write_item "  Config: $settings_file" "$GRAY"
            ;;

        GEMINI)
            local config_dir="$user_home/.gemini"
            local settings_file="$config_dir/settings.json"
            local template_file="$perm_dir/gemini-permissions.json"

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Gemini permissions template not found" "$GRAY"
                return
            fi

            if [ -f "$settings_file" ]; then
                # Sentinel: docker ps was added in v0.10+ with the expanded command set
                if grep -q 'run_shell_command(docker ps)' "$settings_file" 2>/dev/null; then
                    write_item "[OK] Auto-approve permissions already configured in settings.json" "$GREEN"
                    return
                fi

                local backup_path
                backup_path="$settings_file.bak.$(date +%Y%m%d-%H%M%S)"
                cp "$settings_file" "$backup_path"
                write_item "  Backup created: $backup_path" "$GRAY"

                if command -v jq >/dev/null 2>&1; then
                    local merged
                    merged=$(jq -s '
                        .[0] as $existing | .[1] as $template |
                        ($existing.tools.allowed // []) as $et |
                        ($template.tools.allowed // []) as $tt |
                        ($existing.allowedDomains // []) as $ed |
                        ($template.allowedDomains // []) as $td |
                        $existing
                        | .tools.allowed = ($et + $tt | unique)
                        | .allowedDomains = ($ed + $td | unique)
                    ' "$settings_file" "$template_file" 2>/dev/null)

                    if [ -n "$merged" ]; then
                        echo "$merged" > "$settings_file"
                        write_item "[OK] $scope auto-approve permissions added to settings.json" "$GREEN"
                    else
                        write_item "Warning: Could not merge permissions into Gemini settings.json" "$YELLOW"
                        return
                    fi
                else
                    write_item "Warning: jq not found, cannot merge permissions automatically" "$YELLOW"
                    return
                fi
            else
                mkdir -p "$config_dir"
                if command -v jq >/dev/null 2>&1; then
                    jq '{tools: .tools, allowedDomains: .allowedDomains}' "$template_file" > "$settings_file"
                else
                    cp "$template_file" "$settings_file"
                fi
                write_item "[OK] $scope settings.json created with auto-approve permissions" "$GREEN"
            fi

            write_item "  Auto-approved: file reads, search, web search, git read-only shell commands" "$GRAY"
            write_item "  Domains: scoped to trusted list (see $settings_file to customize)" "$GRAY"
            write_item "  Limitation: piped commands bypass allowlists (upstream issue)" "$GRAY"
            write_item "  Config: $settings_file" "$GRAY"
            ;;

        CODEX)
            ensure_codex_cli
            local config_dir="$user_home/.codex"
            local config_file="$config_dir/config.toml"
            local template_file="$perm_dir/codex-permissions.toml"

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Codex permissions template not found" "$GRAY"
                return
            fi

            if [ -f "$config_file" ]; then
                # Repair an already-broken config: if it defines [permissions.*]
                # but lacks default_permissions, the newer Codex CLI refuses to
                # load it. Insert the key before the FIRST table header of any
                # kind (the only valid spot for a root-level key in TOML) rather
                # than appending it after a table, where it would silently bind
                # to that table and stay broken.
                if grep -q '^\[permissions' "$config_file" 2>/dev/null && ! grep -q 'default_permissions' "$config_file" 2>/dev/null; then
                    cp "$config_file" "$config_file.bak.$(date +%Y%m%d-%H%M%S)"
                    if awk 'BEGIN{ins=0} /^\[/ && ins==0 {print "default_permissions = \"default\""; print ""; ins=1} {print}' "$config_file" > "$config_file.nexus.tmp"; then
                        mv "$config_file.nexus.tmp" "$config_file"
                        write_item "[OK] Repaired Codex config.toml: inserted missing default_permissions" "$GREEN"
                    else
                        rm -f "$config_file.nexus.tmp"
                        write_item "Warning: could not repair Codex config.toml; review it manually" "$YELLOW"
                    fi
                fi

                # Already fully configured (managed block complete, incl. default_permissions)?
                if grep -q 'permissions.default.network' "$config_file" 2>/dev/null && grep -q 'allowed_domains' "$config_file" 2>/dev/null && grep -q 'default_permissions' "$config_file" 2>/dev/null; then
                    write_item "[OK] Auto-approve permissions already configured in config.toml" "$GREEN"
                    return
                fi

                local backup_path
                backup_path="$config_file.bak.$(date +%Y%m%d-%H%M%S)"
                cp "$config_file" "$backup_path"
                write_item "  Backup created: $backup_path" "$GRAY"

                # Append permission sections if not present
                printf '\n\n# --- Nexus-Hub auto-approve permissions ---\n' >> "$config_file"
                if ! grep -q 'approval_policy' "$config_file" 2>/dev/null; then
                    printf 'approval_policy = "on-request"\n\n' >> "$config_file"
                fi
                # default_permissions selects the profile defined below; the newer
                # Codex CLI rejects a config with [permissions.*] but no default_permissions.
                if ! grep -q 'default_permissions' "$config_file" 2>/dev/null; then
                    printf 'default_permissions = "default"\n\n' >> "$config_file"
                fi
                if ! grep -q '\[permissions.default.filesystem\]' "$config_file" 2>/dev/null; then
                    grep -A2 '\[permissions.default.filesystem\]' "$template_file" >> "$config_file"
                    printf '\n' >> "$config_file"
                fi
                if ! grep -q '\[permissions.default.network\]' "$config_file" 2>/dev/null; then
                    sed -n '/\[permissions.default.network\]/,$p' "$template_file" >> "$config_file"
                fi
                write_item "[OK] $scope config.toml updated with auto-approve permissions" "$GREEN"
            else
                mkdir -p "$config_dir"
                cp "$template_file" "$config_file"
                write_item "[OK] $scope config.toml created with auto-approve permissions" "$GREEN"
            fi

            write_item "  Auto-approved: filesystem read access to project roots, network access to trusted domains" "$GRAY"
            write_item "  NOT auto-approved: file writes, arbitrary network access" "$GRAY"
            write_item "  Note: Codex does not support per-command Bash allowlisting" "$GRAY"
            write_item "  Config: $config_file" "$GRAY"
            ;;

        COPILOT)
            local template_file="$perm_dir/copilot-permissions.json"

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Copilot permissions template not found" "$GRAY"
                return
            fi

            # Locate VS Code settings.json
            local vscode_settings=""
            case "$(uname -s)" in
                Darwin*) vscode_settings="$user_home/Library/Application Support/Code/User/settings.json" ;;
                Linux*)  vscode_settings="$user_home/.config/Code/User/settings.json" ;;
                *)       write_item "Skip: Copilot permission config not supported on this OS via bash" "$GRAY"; return ;;
            esac

            if [ ! -f "$vscode_settings" ]; then
                write_item "Skip: VS Code settings.json not found at $vscode_settings" "$GRAY"
                write_item "  Copilot permissions require VS Code. Install VS Code and retry." "$GRAY"
                return
            fi

            if grep -q 'useInstructionFiles.*true' "$vscode_settings" 2>/dev/null; then
                write_item "[OK] Copilot useInstructionFiles already enabled in VS Code settings" "$GREEN"
                return
            fi

            local backup_path
            backup_path="$vscode_settings.bak.$(date +%Y%m%d-%H%M%S)"
            cp "$vscode_settings" "$backup_path"
            write_item "  Backup created: $backup_path" "$GRAY"

            if command -v jq >/dev/null 2>&1; then
                local merged
                merged=$(jq '. + {"github.copilot.chat.codeGeneration.useInstructionFiles": true}' "$vscode_settings" 2>/dev/null)
                if [ -n "$merged" ]; then
                    echo "$merged" > "$vscode_settings"
                    write_item "[OK] $scope VS Code settings updated with Copilot instruction file support" "$GREEN"
                else
                    write_item "Warning: Could not merge Copilot settings into VS Code settings.json" "$YELLOW"
                    return
                fi
            else
                write_item "Warning: jq not found, cannot merge Copilot settings automatically" "$YELLOW"
                return
            fi

            write_item "  Limitation: Copilot lacks per-command/per-domain auto-approve" "$GRAY"
            write_item "  Only useInstructionFiles is enabled (behavioral guardrails via .github/copilot-instructions.md)" "$GRAY"
            write_item "  Blanket auto-approve is NOT set (cannot distinguish reads from writes)" "$GRAY"
            write_item "  Config: $vscode_settings" "$GRAY"
            ;;
    esac
}

# --- Git Commit-Msg Hook ---

install_git_commit_msg_hook() {
    local repo_root="$1"
    local user_home="$HOME"
    local hook_src="$repo_root/catalog/hooks/commit-msg"
    local template_hooks_dir="$user_home/.git-templates/hooks"

    if [ ! -f "$hook_src" ]; then
        write_item "Skip: catalog/hooks/commit-msg not found" "$GRAY"
        return
    fi

    mkdir -p "$template_hooks_dir"
    cp "$hook_src" "$template_hooks_dir/commit-msg"
    chmod +x "$template_hooks_dir/commit-msg"
    write_item "[OK] Git commit-msg hook installed at: $template_hooks_dir/commit-msg" "$GREEN"

    # Register the template directory so all future repos inherit the hook
    git config --global init.templateDir "$HOME/.git-templates" 2>/dev/null || true
    write_item "[OK] git config --global init.templateDir set to $HOME/.git-templates" "$GREEN"
    write_item "  Note: run 'git init' in existing repos to apply the hook there too" "$GRAY"
}

# --- Install Functions ---

install_global() {
    local repo_root="$1"
    local user_home="$HOME"

    # OVERWRITE_ALL is resolved once at startup (refresh vs interactive-conflict);
    # the install functions no longer toggle it.
    echo ""
    echo -e "${CYAN}> Global install${RESET}"

    write_subsection_banner "Skills & Commands"

    echo -e "${GRAY}Checking User Profile ($user_home)...${RESET}"

    # Instruction-template placeholders, set unconditionally so every selected
    # provider renders a complete instruction body even when --platforms excludes
    # Claude (these globals are threaded to every invoke_registry_platform call).
    PROJECT_NAME="Global"
    OS_CONTEXT=""
    case "$(uname -s)" in
        Darwin*) OS_CONTEXT="I am a macOS user." ;;
        Linux*)  OS_CONTEXT="I am a Linux user." ;;
        *)       OS_CONTEXT="I am a Windows user." ;;
    esac
    PRIMARY_LANGUAGE=""
    PACKAGE_MANAGER=""
    BUILD_TOOL=""
    TEST_FRAMEWORK=""
    LINT_TOOL=""
    BUILD_CMD="# specify build command"
    TEST_CMD="# specify test command"
    LINT_CMD="# specify lint command"
    NON_OBVIOUS_TOOLING="- (configure per project with /setup project)"

    # Per-provider install blocks. Each is gated on the --platforms subset via
    # should_install <integration-key> (no filter => all run). The output groups
    # by organization (Anthropic / OpenAI / Google / Microsoft / Anysphere /
    # OpenCode / Nexus); each provider has a single colored write_header line and
    # its platforms listed underneath.

    # --- Anthropic -- Claude Code ---------------------------------------
    if should_install claude; then
    write_header "ANTHROPIC"
    write_item "Claude Code" "$GRAY"
    local global_claude="$user_home/.claude"
    mkdir -p "$global_claude"

    # DF-001: the registry runner renders CLAUDE.md (marker-merged, full
    # placeholder substitution). --instruction-only leaves the catalog mirror to
    # the safe_folder_copy block below.
    invoke_registry_platform "$repo_root" "global" "" "claude" "CLAUDE.md (instruction file)" "" "true"

    safe_folder_copy "$repo_root/catalog/skills"   "$global_claude/skills"   "[OK] Skills catalog installed at: $global_claude/skills"
    safe_folder_copy "$repo_root/catalog/commands" "$global_claude/commands" "[OK] Commands installed at: $global_claude/commands"
    safe_folder_copy "$repo_root/catalog/agents"   "$global_claude/agents"   "[OK] Agents installed at: $global_claude/agents"
    safe_folder_copy "$repo_root/catalog/rules"    "$global_claude/rules"    "[OK] Rules installed at: $global_claude/rules"

    mkdir -p "$global_claude/mcp-configs"
    safe_copy "$repo_root/catalog/mcp-configs/mcp-servers.json" "$global_claude/mcp-configs/mcp-servers.json" false "[OK] MCP server config installed at: $global_claude/mcp-configs"

    install_git_guardrails    "$repo_root" "$global_claude" "Global"
    install_usage_display     "$repo_root" "$global_claude" "Global"
    install_require_description "$repo_root" "$global_claude" "Global"
    install_core_settings     "$repo_root" "$global_claude" "Global"
    fi

    # --- OpenAI -- Codex ------------------------------------------------
    if should_install codex; then
    write_header "OPENAI"
    write_item "Codex" "$GRAY"
    local global_codex_dir="$user_home/.codex"
    mkdir -p "$global_codex_dir"

    safe_folder_copy "$repo_root/catalog/skills"   "$global_codex_dir/skills"  "[OK] Skills catalog installed at: $global_codex_dir/skills"
    safe_folder_copy "$repo_root/catalog/commands" "$global_codex_dir/prompts" "[OK] Custom prompts installed at: $global_codex_dir/prompts"

    # AGENTS.md (open standard read by Codex, Jules, Cursor, Aider, OpenCode)
    invoke_registry_platform "$repo_root" "global" "" "codex" "AGENTS.md (instruction file)" "" "true"
    fi

    # --- Google -- Gemini / Antigravity 1.0 + 2.0 / Gemini CLI ---------
    if should_install gemini || should_install antigravity2 || should_install gemini-cli; then
    write_header "GOOGLE"
    if should_install gemini; then
    write_item "Gemini IDE + Antigravity 1.0" "$GRAY"
    local global_gemini_dir="$user_home/.gemini"
    mkdir -p "$global_gemini_dir"

    invoke_registry_platform "$repo_root" "global" "" "gemini" "GEMINI.md (instruction file)" "" "true"
    fi

    # Antigravity 2.0 + CLI: the antigravity2 integration below owns the entire
    # Antigravity mirror. It flattens skills to skills/<name>/SKILL.md (the flat
    # folder-per-skill layout the IDE actually scans), mirrors commands to
    # workflows/, installs the curated hooks + hooks.json, and writes to BOTH the
    # IDE global root (~/.gemini/antigravity) and the CLI global root
    # (~/.gemini/antigravity-cli). The previous verbatim copies here buried every
    # SKILL.md under a category folder the IDE could not read and only targeted
    # the CLI root, so skills and commands never surfaced in the 2.0 IDE.
    if should_install antigravity2; then
    invoke_registry_platform "$repo_root" "global" "" "antigravity2" "Antigravity 2.0 + CLI"
    write_item "Antigravity 2.0 IDE: slash commands appear only inside an OPEN project folder (its .agents/workflows/). Run a workspace/project install in your repo so the commands show; a global-only install is not scanned by the IDE for slash commands." "$DARK_YELLOW"
    fi
    if should_install gemini-cli; then
    if [ "${ENTERPRISE:-0}" = "1" ]; then
        invoke_registry_platform "$repo_root" "global" "" "gemini-cli"   "Gemini CLI (enterprise)"
    else
        write_item "Gemini CLI: skipped (sunset on 2026-06-18 for free / Google AI Pro / Ultra / GitHub-installed users). Re-run with --enterprise to install (requires paid Gemini API key); Antigravity CLI above covers the same functionality." "$DARK_YELLOW"
    fi
    fi
    fi

    # --- Microsoft -- GitHub Copilot -----------------------------------
    if should_install copilot; then
    write_header "MICROSOFT"
    invoke_registry_platform "$repo_root" "global" "" "copilot" "GitHub Copilot (global prompt files)"
    fi

    # --- Anysphere -- Cursor -------------------------------------------
    if should_install cursor; then
    write_header "ANYSPHERE"
    invoke_registry_platform "$repo_root" "global" "" "cursor" "Cursor"
    fi

    # --- OpenCode ------------------------------------------------------
    if should_install opencode; then
    write_header "OPENCODE"
    invoke_registry_platform "$repo_root" "global" "" "opencode" "OpenCode"
    fi

    # --- Aider ---------------------------------------------------------
    if should_install aider; then
    write_header "AIDER"
    invoke_registry_platform "$repo_root" "global" "" "aider" "Aider (CONVENTIONS.md)"
    write_item "Aider: reads a project-root CONVENTIONS.md; there is no global instruction surface. Run a workspace/project install in your repo to get it." "$DARK_YELLOW"
    fi

    # --- Windsurf ------------------------------------------------------
    if should_install windsurf; then
    write_header "WINDSURF"
    invoke_registry_platform "$repo_root" "global" "" "windsurf" "Windsurf (global_rules.md)"
    write_item "Windsurf: global rules are written to ~/.codeium/windsurf/memories/global_rules.md only when Windsurf is detected (~/.codeium present); the project-root .windsurfrules installs at workspace scope." "$DARK_YELLOW"
    fi

    # --- Kimi ----------------------------------------------------------
    if should_install kimi; then
    write_header "KIMI"
    invoke_registry_platform "$repo_root" "global" "" "kimi" "Kimi (.kimi/agent.yaml + system.md)"
    write_item "Kimi: global files are written to ~/.kimi/ only when Kimi is detected (~/.kimi present); the project-local .kimi/ pair installs at workspace scope." "$DARK_YELLOW"
    fi

    # --- Qwen ----------------------------------------------------------
    if should_install qwen; then
    write_header "QWEN"
    invoke_registry_platform "$repo_root" "global" "" "qwen" "Qwen Code (QWEN.md)"
    write_item "Qwen: ~/.qwen/QWEN.md is written only when Qwen is detected (~/.qwen present); the project-root QWEN.md installs at workspace scope." "$DARK_YELLOW"
    fi

    # --- OpenClaw ------------------------------------------------------
    if should_install openclaw; then
    write_header "OPENCLAW"
    invoke_registry_platform "$repo_root" "global" "" "openclaw" "OpenClaw (.openclaw/ SOUL+AGENTS+IDENTITY)"
    write_item "OpenClaw: global files are written to ~/.openclaw/ only when OpenClaw is detected (~/.openclaw present); the project-local .openclaw/ split installs at workspace scope." "$DARK_YELLOW"
    fi

    # --- Nexus -- Nexus-AI (Local Desktop Studio) ----------------------
    if should_install nexus-ai; then
    write_header "NEXUS"
    invoke_registry_platform "$repo_root" "global" "" "nexus-ai" "Nexus-AI (Local Desktop Studio)"
    fi

    # --- Auto-Approve Permissions sub-section --------------------------
    # Permissions only apply to the legacy 4 (CLAUDE / GEMINI / CODEX /
    # COPILOT). Mirrored to provider headers for visual consistency. Each is
    # gated on the same --platforms subset as its provider block above.
    write_subsection_banner "Auto-Approve Permissions"

    if should_install claude; then
    write_header "ANTHROPIC"
    install_permissions "$repo_root" "CLAUDE" "Global"
    fi

    if should_install codex; then
    write_header "OPENAI"
    install_permissions "$repo_root" "CODEX" "Global"
    fi

    if should_install gemini; then
    write_header "GOOGLE"
    install_permissions "$repo_root" "GEMINI" "Global"
    fi

    if should_install copilot; then
    write_header "MICROSOFT"
    install_permissions "$repo_root" "COPILOT" "Global"
    fi

    # --- Claude Code Utilities sub-section ---
    write_subsection_banner "Claude Code Utilities"
    install_vscode_extensions "$repo_root"

    # --- Skill Discovery sub-section ---
    write_subsection_banner "Skill Discovery (All Platforms)"
    install_skill_discovery "$repo_root"

    # --- Git Commit-Msg Hook sub-section ---
    write_subsection_banner "Git Commit-Msg Hook (All Platforms)"
    echo ""
    install_git_commit_msg_hook "$repo_root"
    echo ""
}

detect_languages() {
    local target_path="$1"
    local detected_langs=""

    # Simple count check
    if [ "$(find "$target_path" -maxdepth 3 -name "*.py" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="Python,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.js" -o -name "*.jsx" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="JavaScript,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="TypeScript,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.java" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="Java,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.cs" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="C#,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.go" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="Go,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.cpp" -o -name "*.h" -o -name "*.hpp" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="C++,"; fi

    # Remove trailing comma
    echo "${detected_langs%,}"
}

detect_project_metadata() {
    local target_path="$1"
    local languages="$2"

    # Project name from directory
    PROJECT_NAME=$(basename "$target_path")

    # OS detection
    case "$(uname -s)" in
        Darwin*) OS_CONTEXT="I am a macOS user. Ensure shell commands are POSIX-compatible." ;;
        Linux*)  OS_CONTEXT="I am a Linux user. Ensure shell commands are POSIX-compatible." ;;
        *)       OS_CONTEXT="I am a Windows user. Ensure shell commands are PowerShell-compatible." ;;
    esac

    # Primary language (first detected)
    PRIMARY_LANGUAGE=$(echo "$languages" | cut -d',' -f1)

    # Package manager detection
    PACKAGE_MANAGER=""
    BUILD_TOOL=""
    TEST_FRAMEWORK=""
    LINT_TOOL=""
    BUILD_CMD=""
    TEST_CMD=""
    LINT_CMD=""
    NON_OBVIOUS_TOOLING=""

    if [ -f "$target_path/pyproject.toml" ]; then
        PACKAGE_MANAGER="uv (or pip with venv)"
        BUILD_TOOL="uv"
        TEST_FRAMEWORK="pytest"
        LINT_TOOL="ruff"
        BUILD_CMD="uv run python src/main.py"
        TEST_CMD="uv run pytest tests/"
        LINT_CMD="uv run ruff check . && uv run ruff format ."
        NON_OBVIOUS_TOOLING="- Use \`uv\` not \`pip\` for Python package management (10-100x faster)"
    elif [ -f "$target_path/requirements.txt" ]; then
        PACKAGE_MANAGER="pip with venv"
        BUILD_TOOL="pip"
        TEST_FRAMEWORK="pytest"
        LINT_TOOL="ruff"
        BUILD_CMD="python src/main.py"
        TEST_CMD="pytest tests/"
        LINT_CMD="ruff check . && ruff format ."
    fi

    if [ -f "$target_path/package.json" ]; then
        PACKAGE_MANAGER="npm"
        if [ -f "$target_path/yarn.lock" ]; then PACKAGE_MANAGER="yarn"; fi
        if [ -f "$target_path/pnpm-lock.yaml" ]; then PACKAGE_MANAGER="pnpm"; fi
        if [ -f "$target_path/bun.lockb" ]; then
            PACKAGE_MANAGER="bun"
            NON_OBVIOUS_TOOLING="- Use \`bun\` not \`npm\` for package management and script execution"
        fi
        BUILD_TOOL="$PACKAGE_MANAGER"
        TEST_FRAMEWORK="jest"
        LINT_TOOL="eslint + prettier"
        BUILD_CMD="$PACKAGE_MANAGER run build"
        TEST_CMD="$PACKAGE_MANAGER test"
        LINT_CMD="$PACKAGE_MANAGER run lint"
    fi

    if [ -f "$target_path/go.mod" ]; then
        PACKAGE_MANAGER="go mod"
        BUILD_TOOL="go"
        TEST_FRAMEWORK="go test"
        LINT_TOOL="golangci-lint"
        BUILD_CMD="go build ./..."
        TEST_CMD="go test ./..."
        LINT_CMD="golangci-lint run"
    fi

    if [ -f "$target_path/pom.xml" ]; then
        PACKAGE_MANAGER="Maven"
        BUILD_TOOL="mvn"
        TEST_FRAMEWORK="JUnit 5"
        LINT_TOOL="Checkstyle"
        BUILD_CMD="mvn compile"
        TEST_CMD="mvn test"
        LINT_CMD="mvn checkstyle:check"
    elif [ -f "$target_path/build.gradle" ] || [ -f "$target_path/build.gradle.kts" ]; then
        PACKAGE_MANAGER="Gradle"
        BUILD_TOOL="gradle"
        TEST_FRAMEWORK="JUnit 5"
        LINT_TOOL="Checkstyle"
        BUILD_CMD="./gradlew build"
        TEST_CMD="./gradlew test"
        LINT_CMD="./gradlew checkstyleMain"
    fi

    if ls "$target_path"/*.csproj >/dev/null 2>&1 || ls "$target_path"/*.sln >/dev/null 2>&1; then
        PACKAGE_MANAGER="NuGet (dotnet)"
        BUILD_TOOL="dotnet"
        TEST_FRAMEWORK="xUnit"
        LINT_TOOL="dotnet format"
        BUILD_CMD="dotnet build"
        TEST_CMD="dotnet test"
        LINT_CMD="dotnet format"
    fi

    if [ -f "$target_path/CMakeLists.txt" ]; then
        PACKAGE_MANAGER="CMake"
        BUILD_TOOL="cmake"
        TEST_FRAMEWORK="GoogleTest"
        LINT_TOOL="clang-format"
        BUILD_CMD="cmake --build build"
        TEST_CMD="ctest --test-dir build"
        LINT_CMD="clang-format -i src/*.cpp include/*.h"
    fi

    if [ -f "$target_path/Makefile" ] && [ -z "$BUILD_CMD" ]; then
        BUILD_CMD="make"
        TEST_CMD="make test"
    fi

    # Set defaults for unfilled values
    [ -z "$PACKAGE_MANAGER" ] && PACKAGE_MANAGER="(detect or specify)"
    [ -z "$BUILD_TOOL" ] && BUILD_TOOL="(detect or specify)"
    [ -z "$TEST_FRAMEWORK" ] && TEST_FRAMEWORK="(detect or specify)"
    [ -z "$LINT_TOOL" ] && LINT_TOOL="(detect or specify)"
    [ -z "$BUILD_CMD" ] && BUILD_CMD="# specify build command"
    [ -z "$TEST_CMD" ] && TEST_CMD="# specify test command"
    [ -z "$LINT_CMD" ] && LINT_CMD="# specify lint command"
    [ -z "$NON_OBVIOUS_TOOLING" ] && NON_OBVIOUS_TOOLING="- (add project-specific tooling notes here)"
}

# render_template() was removed in v2.3.0 / Phase 7 (DF-001). Instruction-file
# rendering now flows through scripts/lib/integrations/runner.py via
# invoke_registry_platform (single renderer shared with installer.ps1), which
# substitutes the same placeholder set and marker-merges the body. The detected
# globals above (PROJECT_NAME, BUILD_CMD, OS_CONTEXT, ...) are threaded to the
# runner by invoke_registry_platform.

get_language_selection() {
    local detected="$1"

    # Non-interactive (--yes / --force / piped / CI): auto-accept the detected
    # languages with no prompt; fall back to Python when nothing was detected.
    # This keeps a `--workspace <path>` install promptless (v3.7.0 / Phase 2).
    if [ "$ASSUME_YES" = true ]; then
        if [ -n "$detected" ]; then echo "$detected"; else echo "Python"; fi
        return
    fi

    if [ -n "$detected" ]; then
        echo -e "${YELLOW}Detected languages: $detected${RESET}" >&2
        local resp
        resp=$(read_prompt "Use these? [Y]es / [N]o")
        if [[ "$resp" =~ ^[Yy] ]]; then
            echo "$detected"
            return
        fi
    fi

    echo -e "  ${RESET}Select languages (comma separated):${RESET}" >&2
    echo -e "  ${RESET}1. Python  2. JS  3. TS  4. Java  5. C#  6. Go  7. C++${RESET}" >&2
    local input_str
    input_str=$(read_prompt "Selection")

    local result=""
    IFS=',' read -ra ADDR <<< "$input_str"
    for i in "${ADDR[@]}"; do
        case $(echo "$i" | xargs) in # trim whitespace
            1|Python) result+="Python," ;;
            2|JS|JavaScript) result+="JavaScript," ;;
            3|TS|TypeScript) result+="TypeScript," ;;
            4|Java) result+="Java," ;;
            5|"C#"|CS) result+="C#," ;;
            6|Go) result+="Go," ;;
            7|"C++"|CPP) result+="C++," ;;
        esac
    done

    if [ -z "$result" ]; then
        echo "Python"
    else
        echo "${result%,}"
    fi
}

install_workspace() {
    local repo_root="$1"
    local target_path="$2"  # pre-validated by main() in v0.9.7+

    echo ""
    echo -e "${CYAN}> Workspace install${RESET}"

    if [ -z "$target_path" ] || [ ! -d "$target_path" ]; then
        write_item "Invalid target path: $target_path" "$RED"
        return 1
    fi

    # Single-pass workspace install. To install into multiple workspaces, re-run the installer.
    write_item "Target: $target_path" "$DARK_YELLOW"

        local detected
        detected=$(detect_languages "$target_path")
        local languages
        languages=$(get_language_selection "$detected")
        write_item "Selected: $languages" "$YELLOW"

        # Auto-detect project metadata for template rendering
        detect_project_metadata "$target_path" "$languages"

        # --- Install Logic (provider-grouped) ---
        # Each provider block is gated on the --platforms subset via
        # should_install <integration-key> (no filter => all run).

        # --- Anthropic -- Claude Code -------------------------------
        if should_install claude; then
        write_header "ANTHROPIC"
        write_item "Claude Code" "$GRAY"
        local claude_dir="$target_path/.claude"
        mkdir -p "$claude_dir"

        invoke_registry_platform "$repo_root" "workspace" "$target_path" "claude" "CLAUDE.md (instruction file)" "$languages" "true"

        safe_folder_copy "$repo_root/catalog/skills"   "$claude_dir/skills"   "[OK] Skills catalog installed at: $claude_dir/skills"
        safe_folder_copy "$repo_root/catalog/commands" "$claude_dir/commands" "[OK] Commands installed at: $claude_dir/commands"
        safe_folder_copy "$repo_root/catalog/agents"   "$claude_dir/agents"   "[OK] Agents installed at: $claude_dir/agents"
        safe_folder_copy "$repo_root/catalog/rules"    "$claude_dir/rules"    "[OK] Rules installed at: $claude_dir/rules"

        mkdir -p "$claude_dir/mcp-configs"
        safe_copy "$repo_root/catalog/mcp-configs/mcp-servers.json" "$claude_dir/mcp-configs/mcp-servers.json" false "[OK] MCP server config installed at: $claude_dir/mcp-configs"

        safe_folder_copy "$repo_root/catalog/context" "$claude_dir/context" "[OK] Context installed at: $claude_dir/context"
        safe_folder_copy "$repo_root/catalog/memory"  "$claude_dir/memory"  "[OK] Memory installed at: $claude_dir/memory"

        install_git_guardrails    "$repo_root" "$claude_dir" "Workspace"
        install_usage_display     "$repo_root" "$claude_dir" "Workspace"
        install_require_description "$repo_root" "$claude_dir" "Workspace"
        fi

        # --- OpenAI -- Codex ----------------------------------------
        if should_install codex; then
        write_header "OPENAI"
        write_item "Codex" "$GRAY"
        local codex_dir="$target_path/.codex"
        mkdir -p "$codex_dir"

        safe_folder_copy "$repo_root/catalog/skills"   "$codex_dir/skills"  "[OK] Skills catalog installed at: $codex_dir/skills"
        safe_folder_copy "$repo_root/catalog/commands" "$codex_dir/prompts" "[OK] Custom prompts installed at: $codex_dir/prompts"

        # AGENTS.md (open standard read by Codex, Jules, Cursor, Aider, OpenCode)
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "codex" "AGENTS.md (instruction file)" "$languages" "true"
        fi

        # --- Google -- Gemini / Antigravity 1.0 + 2.0 / Gemini CLI -
        if should_install gemini || should_install antigravity2 || should_install gemini-cli; then
        write_header "GOOGLE"
        if should_install gemini; then
        write_item "Gemini IDE + Antigravity 1.0" "$GRAY"
        local gemini_dir="$target_path/.gemini"
        mkdir -p "$gemini_dir"

        invoke_registry_platform "$repo_root" "workspace" "$target_path" "gemini" "GEMINI.md (instruction file)" "$languages" "true"
        fi

        # Antigravity 2.0 + CLI: the antigravity2 integration below owns the
        # .agents/ mirror -- it flattens skills to .agents/skills/<name>/SKILL.md,
        # mirrors commands to .agents/workflows/, and installs .agents/hooks/ +
        # .agents/hooks.json. The previous verbatim copies buried SKILL.md under a
        # category folder the IDE could not read.
        if should_install antigravity2; then
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "antigravity2" "Antigravity 2.0 + CLI"
        fi
        if should_install gemini-cli; then
        if [ "${ENTERPRISE:-0}" = "1" ]; then
            invoke_registry_platform "$repo_root" "workspace" "$target_path" "gemini-cli"   "Gemini CLI (enterprise)"
        else
            write_item "Gemini CLI: skipped (sunset on 2026-06-18 for free / Google AI Pro / Ultra / GitHub-installed users). Re-run with --enterprise to install (requires paid Gemini API key); Antigravity CLI above covers the same functionality." "$DARK_YELLOW"
        fi
        fi
        fi

        # --- Microsoft -- GitHub Copilot ----------------------------
        if should_install copilot; then
        # Prepare the Copilot instruction body.
        local merged_content="# $PROJECT_NAME - Copilot Instructions\n\n"
        merged_content+="## Tech Stack\n"
        merged_content+="- **Language**: $PRIMARY_LANGUAGE\n"
        merged_content+="- **Package Manager**: $PACKAGE_MANAGER\n"
        merged_content+="- **Test**: $TEST_FRAMEWORK\n"
        merged_content+="- **Lint**: $LINT_TOOL\n\n"
        merged_content+="## Working Conventions\n"
        merged_content+="- Destructive git commands require explicit user confirmation before running\n"
        merged_content+="- Never add \`Co-Authored-By\` lines, AI attribution footers, or AI-generated signatures to commit messages\n"
        merged_content+="- **MANDATORY: Every Bash/shell command approval MUST be preceded by a one-sentence plain-language explanation** of what the command does and what its impact will be. This applies to ALL commands regardless of complexity. No exceptions.\n"
        merged_content+="- Ask clarifying questions before coding if requirements are ambiguous\n\n"

        IFS=',' read -ra LANGS <<< "$languages"
        for lang in "${LANGS[@]}"; do
            lang_key=$(echo "$lang" | tr '[:upper:]' '[:lower:]')
            if [ "$lang_key" == "c++" ]; then lang_key="cpp"; fi
            if [ "$lang_key" == "c#" ]; then lang_key="csharp"; fi
            src="$repo_root/templates/ai-instructions/coding-snippets/${lang_key}.md"
            if [ -f "$src" ]; then
                merged_content+="\n"
                merged_content+=$(cat "$src")
                merged_content+="\n"
            fi
        done

        write_header "MICROSOFT"
        write_item "GitHub Copilot" "$GRAY"
        local copilot_dir="$target_path/.github"
        mkdir -p "$copilot_dir"
        local copilot_file="$copilot_dir/copilot-instructions.md"

        # Route the generated body through safe_copy via a temp file so the
        # Copilot instruction file participates in the unified conflict-only
        # overwrite flow (v3.7.0 / Phase 2) instead of its own inline prompt.
        local copilot_tmp
        copilot_tmp=$(mktemp)
        TEMP_FILES+=("$copilot_tmp")
        printf '%b' "$merged_content" > "$copilot_tmp"
        safe_copy "$copilot_tmp" "$copilot_file" true "[OK] Workspace instructions installed at: $copilot_file"
        fi

        # --- Anysphere -- Cursor ------------------------------------
        if should_install cursor; then
        write_header "ANYSPHERE"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "cursor" "Cursor"
        fi

        # --- OpenCode -----------------------------------------------
        if should_install opencode; then
        write_header "OPENCODE"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "opencode" "OpenCode"
        fi

        # --- Aider --------------------------------------------------
        if should_install aider; then
        write_header "AIDER"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "aider" "Aider (CONVENTIONS.md)" "$languages"
        fi

        # --- Windsurf -----------------------------------------------
        if should_install windsurf; then
        write_header "WINDSURF"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "windsurf" "Windsurf (.windsurfrules)" "$languages"
        fi

        # --- Kimi ---------------------------------------------------
        if should_install kimi; then
        write_header "KIMI"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "kimi" "Kimi (.kimi/agent.yaml + system.md)" "$languages"
        fi

        # --- Qwen ---------------------------------------------------
        if should_install qwen; then
        write_header "QWEN"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "qwen" "Qwen Code (QWEN.md)" "$languages"
        fi

        # --- OpenClaw -----------------------------------------------
        if should_install openclaw; then
        write_header "OPENCLAW"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "openclaw" "OpenClaw (.openclaw/ SOUL+AGENTS+IDENTITY)" "$languages"
        fi

        # --- Nexus -- Nexus-AI --------------------------------------
        if should_install nexus-ai; then
        write_header "NEXUS"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "nexus-ai" "Nexus-AI (Local Desktop Studio)"
        fi

        echo ""
}

resolve_python_executable() {
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"; return 0
    fi
    if command -v python >/dev/null 2>&1; then
        echo "python"; return 0
    fi
    return 1
}

# Run runner.py for a single registry-backed integration. Caller is
# responsible for printing the provider header (write_header). This
# function prints a sub-item label for the platform display name and
# the [OK] / error line.
#
# The instruction-template placeholders (PRIMARY_LANGUAGE, BUILD_CMD,
# OS_CONTEXT, ...) are threaded from the globals that the global block and
# detect_project_metadata set, so the registry renders the same instruction
# body the legacy bash render_template produced (DF-001). Passing them to every
# registry platform is harmless and fixes the latent literal-placeholder bug for
# the platforms that were already registry-driven.
#
# Args: $1=repo_root  $2=scope (global|workspace)  $3=target_path (workspace only)
#       $4=integration_key  $5=display_name
#       $6=languages (csv, optional)  $7=instruction_only ("true" to render only
#       the instruction file and skip the catalog mirror -- used when the bash
#       block already copied catalog/ via safe_folder_copy)
invoke_registry_platform() {
    local repo_root="$1"
    local scope="$2"
    local target_path="$3"
    local key="$4"
    local display="$5"
    local languages="${6:-}"
    local instruction_only="${7:-}"

    local runner="$repo_root/scripts/lib/integrations/runner.py"
    if [ ! -f "$runner" ]; then return 0; fi
    local py
    if ! py=$(resolve_python_executable); then
        write_item "Python not found -- skipping $display." "$DARK_YELLOW"
        return 0
    fi

    write_item "$display" "$GRAY"
    local args=("$runner" "install" "--scope" "$scope" "--integrations" "$key" "--quiet")
    if [ "$scope" = "workspace" ]; then
        args+=("--target" "$target_path")
    fi
    if [ "$OVERWRITE_ALL" = true ]; then
        args+=("--overwrite")
    fi
    if [ "$instruction_only" = "true" ]; then
        args+=("--instruction-only")
    fi
    if [ -n "$languages" ]; then
        args+=("--languages" "$languages")
    fi
    # Thread the instruction-template placeholders from the detected globals.
    args+=("--project-name" "${PROJECT_NAME:-}")
    args+=("--var" "PRIMARY_LANGUAGE=${PRIMARY_LANGUAGE:-}")
    args+=("--var" "PACKAGE_MANAGER=${PACKAGE_MANAGER:-}")
    args+=("--var" "BUILD_TOOL=${BUILD_TOOL:-}")
    args+=("--var" "TEST_FRAMEWORK=${TEST_FRAMEWORK:-}")
    args+=("--var" "LINT_TOOL=${LINT_TOOL:-}")
    args+=("--var" "BUILD_CMD=${BUILD_CMD:-}")
    args+=("--var" "TEST_CMD=${TEST_CMD:-}")
    args+=("--var" "LINT_CMD=${LINT_CMD:-}")
    args+=("--var" "NON_OBVIOUS_TOOLING=${NON_OBVIOUS_TOOLING:-}")
    args+=("--var" "OS_CONTEXT=${OS_CONTEXT:-}")
    if "$py" "${args[@]}"; then
        write_item "[OK] Installed (${scope} scope)" "$GREEN"
    else
        write_item "${display} install reported non-zero exit; continuing." "$YELLOW"
    fi
}

install_vscode_extensions() {
    local repo_root="$1"

    echo ""
    echo -e "  ${DARK_YELLOW}> Claude Usage Monitor${RESET}"

    write_item "The Claude Usage Monitor is a VS Code extension that displays your Claude" "$RESET"
    write_item "Code usage limits in the status bar and recommends when to switch models" "$RESET"
    write_item "(e.g., Opus to Sonnet) to stay within your session and weekly limits." "$RESET"
    echo ""

    local extension_dir="$repo_root/extensions/claude-usage-monitor"

    if [ ! -d "$extension_dir" ]; then
        write_item "Extension source not found at: $extension_dir" "$RED"
        return
    fi

    # Check for Node.js
    if ! command -v node >/dev/null 2>&1; then
        write_item "Node.js is not installed (required to build the extension)." "$DARK_YELLOW"

        # Detect platform and suggest install method
        if command -v brew >/dev/null 2>&1; then
            # A non-interactive run (the piped one-command bootstrap, --yes, or CI)
            # installs without asking so every dependency is present in one pass;
            # an interactive run prompts first.
            local install_resp
            if [ "$ASSUME_YES" = true ]; then install_resp="y"; else install_resp=$(read_prompt "Install Node.js LTS via Homebrew? [Y]es / [N]o"); fi
            if [[ "$install_resp" =~ ^[Yy] ]]; then
                write_item "Installing Node.js LTS via Homebrew..." "$RESET"
                brew install node@22 || {
                    write_item "Homebrew install failed. Please install Node.js from https://nodejs.org" "$RED"
                    return
                }
                write_item "[OK] Node.js installed successfully." "$GREEN"
            else
                write_item "Skipped. Install Node.js from https://nodejs.org and re-run." "$GRAY"
                return
            fi
        elif command -v apt-get >/dev/null 2>&1; then
            local install_resp
            if [ "$ASSUME_YES" = true ]; then install_resp="y"; else install_resp=$(read_prompt "Install Node.js via apt? [Y]es / [N]o"); fi
            if [[ "$install_resp" =~ ^[Yy] ]]; then
                write_item "Installing Node.js via apt..." "$RESET"
                sudo apt-get update -qq && sudo apt-get install -y -qq nodejs npm || {
                    write_item "apt install failed. Please install Node.js from https://nodejs.org" "$RED"
                    return
                }
                write_item "[OK] Node.js installed successfully." "$GREEN"
            else
                write_item "Skipped. Install Node.js from https://nodejs.org and re-run." "$GRAY"
                return
            fi
        else
            write_item "Please install Node.js from https://nodejs.org and re-run the installer." "$YELLOW"
            return
        fi
    else
        local node_version
        node_version=$(node --version)
        write_item "Found Node.js $node_version" "$GREEN"
    fi

    # Check for npm
    if ! command -v npm >/dev/null 2>&1; then
        write_item "npm not found. Please ensure Node.js is properly installed." "$RED"
        return
    fi

    # Build the extension
    write_item "Building Claude Usage Monitor extension..." "$RESET"

    pushd "$extension_dir" > /dev/null || return

    # Clean compiled output so deleted source files don't linger as stale JS
    if [ -d "$extension_dir/out" ]; then
        rm -rf "$extension_dir/out"
    fi

    # A node_modules tree copied in from another OS (e.g. zipping a Windows
    # checkout) leaves Windows .cmd/.ps1 bin shims that a Unix shell cannot
    # exec, so `tsc` resolves to "command not found" and the build fails with a
    # confusing error. Removing it forces a clean, OS-correct dependency tree.
    if [ -d node_modules ]; then
        rm -rf node_modules
    fi

    write_item "  Installing dependencies..." "$GRAY"
    local npm_log
    if ! npm_log=$(npm install --silent 2>&1); then
        write_item "npm install failed:" "$RED"
        echo "$npm_log" | tail -n 20
        popd > /dev/null
        return
    fi

    write_item "  Compiling TypeScript..." "$GRAY"
    local compile_log
    if ! compile_log=$(npm run compile 2>&1); then
        write_item "TypeScript compilation failed:" "$RED"
        echo "$compile_log" | tail -n 30
        popd > /dev/null
        return
    fi

    write_item "[OK] Extension built successfully." "$GREEN"

    # Package as VSIX (uses locally installed @vscode/vsce from devDependencies).
    # A bundled LICENSE file removes the only packaging warning, so vsce no longer
    # shows its interactive "Do you want to continue? [y/N]" prompt. Piping "y" is
    # belt-and-suspenders: if any future warning reappears it auto-confirms instead
    # of blocking an unattended install (harmless when there is no prompt).
    write_item "Packaging extension as VSIX..." "$RESET"
    echo "y" | npx vsce package --no-dependencies 2>/dev/null
    local vsix_file
    vsix_file=$(ls -t "$extension_dir"/*.vsix 2>/dev/null | head -1)

    if [ -z "$vsix_file" ]; then
        write_item "VSIX packaging failed." "$RED"
        write_item "You can still use the extension in development mode (F5 in VS Code)." "$YELLOW"
        popd > /dev/null
        return
    fi

    write_item "[OK] Packaged: $(basename "$vsix_file")" "$GREEN"

    popd > /dev/null

    # Locate a VS Code-family CLI. On a fresh Mac the `code` command is not on
    # PATH unless the user ran "Shell Command: Install 'code' command in PATH", so
    # fall back to the standard application-bundle / install locations. This lets
    # the VSIX auto-install instead of leaving the user to do it by hand.
    local code_cli=""
    local code_label="VS Code"
    if command -v code >/dev/null 2>&1; then
        code_cli="code"
    else
        local candidate
        for candidate in \
            "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" \
            "$HOME/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" \
            "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code" \
            "/usr/share/code/bin/code" \
            "/usr/bin/code" \
            "/snap/bin/code" \
            "/var/lib/flatpak/exports/bin/com.visualstudio.code" \
            "/Applications/Cursor.app/Contents/Resources/app/bin/cursor" \
            "$HOME/Applications/Cursor.app/Contents/Resources/app/bin/cursor" \
            "/Applications/VSCodium.app/Contents/Resources/app/bin/codium"; do
            if [ -x "$candidate" ]; then
                code_cli="$candidate"
                case "$candidate" in
                    *Cursor*) code_label="Cursor" ;;
                    *VSCodium*) code_label="VSCodium" ;;
                esac
                break
            fi
        done
    fi

    # Install into the detected editor
    if [ -n "$code_cli" ]; then
        # Uninstall any existing version first so the editor does not skip the reinstall
        "$code_cli" --uninstall-extension "nexus-hub.claude-usage-monitor" 2>/dev/null || true
        # --force ensures reinstall even when the version number has not changed
        if "$code_cli" --install-extension "$vsix_file" --force 2>/dev/null; then
            write_item "[OK] Claude Usage Monitor extension installed in $code_label!" "$GREEN"
            write_item "  Restart $code_label to activate. Look for 'Claude: --%' in the status bar." "$RESET"
        else
            write_item "$code_label install failed. Install manually:" "$YELLOW"
            write_item "  \"$code_cli\" --install-extension \"$vsix_file\"" "$RESET"
        fi
    else
        write_item "VS Code CLI ('code') not found in PATH or standard install locations." "$YELLOW"
        write_item "VSIX saved at: $vsix_file" "$RESET"
        write_item "Install manually via VS Code: Extensions > ... > Install from VSIX" "$GRAY"
    fi

    echo ""
    echo -e "  ${GREEN}[OK] Claude Usage Monitor Installation Complete.${RESET}"
}

# --- Template & Script Installation ---

install_templates() {
    local repo_root="$1"

    echo ""
    write_subsection_banner "Templates & Report Generator Installation"
    echo ""
    write_item "Nexus-Hub can generate professional Word (.docx) and PowerPoint (.pptx)" "$RESET"
    write_item "reports from Markdown files using the /research report command." "$RESET"
    echo ""

    # Ensure global directories exist
    local nexus_home="$HOME/.nexus-hub"
    local templates_dest="$nexus_home/templates/documentation"
    local scripts_dest="$nexus_home/scripts"

    mkdir -p "$templates_dest"
    mkdir -p "$scripts_dest"

    # Copy bundled templates from repo
    local builtin_templates="$repo_root/templates/documentation"
    if [ -d "$builtin_templates" ]; then
        safe_folder_copy "$builtin_templates" "$templates_dest" "[OK] Built-in templates installed at: $templates_dest"
    fi

    # Copy report generator script
    local script_source="$repo_root/scripts/generate_report.py"
    if [ -f "$script_source" ]; then
        safe_copy "$script_source" "$scripts_dest/generate_report.py" true "[OK] Report generator installed at: $scripts_dest/generate_report.py"
    fi

    # Copy MCP benchmark script (v1.0.0+). Benchmarks the three internal MCPs
    # (nexus-skill-server, nexus-code-search, nexus-web-fetch). Pure-local.
    local benchmark_source="$repo_root/scripts/nexus_mcp_benchmark.py"
    if [ -f "$benchmark_source" ]; then
        safe_copy "$benchmark_source" "$scripts_dest/nexus_mcp_benchmark.py" true "[OK] MCP benchmark installed at: $scripts_dest/nexus_mcp_benchmark.py"
    fi

    # Copy skill-eval-loop dispatcher scripts (v1.2.0-wip / Phase 5 / A6 + A7).
    # Three repo-level scripts that work alongside the catalog/skills/workflow/
    # skill-eval-loop/ skill: the iteration aggregator, the browser-based
    # viewer, and the description optimizer. All three follow the v1.1.3
    # four-hook precedent for CLI dispatch (single dispatcher with --cli
    # flag, no cross-CLI fallback, parity-test enforced via pytest).
    local eval_aggregator_source="$repo_root/scripts/aggregate_benchmark.py"
    if [ -f "$eval_aggregator_source" ]; then
        safe_copy "$eval_aggregator_source" "$scripts_dest/aggregate_benchmark.py" true "[OK] Eval-loop benchmark aggregator installed at: $scripts_dest/aggregate_benchmark.py"
    fi
    local eval_viewer_source="$repo_root/scripts/skill_eval_viewer.py"
    if [ -f "$eval_viewer_source" ]; then
        safe_copy "$eval_viewer_source" "$scripts_dest/skill_eval_viewer.py" true "[OK] Eval-loop browser viewer installed at: $scripts_dest/skill_eval_viewer.py"
    fi
    local eval_optimizer_source="$repo_root/scripts/optimize_skill_description.py"
    if [ -f "$eval_optimizer_source" ]; then
        safe_copy "$eval_optimizer_source" "$scripts_dest/optimize_skill_description.py" true "[OK] Skill-description optimizer installed at: $scripts_dest/optimize_skill_description.py"
    fi

    # Copy .skill packager script (v1.2.0-wip / Phase 7 / A16). Produces a
    # portable .skill ZIP archive from a catalog/skills/<cat>/<name>/ directory
    # for distribution to Claude.ai or the Anthropic API skill-upload endpoint
    # - delivery channels Nexus-Hub does not currently reach. Lockstep with
    # the same block in scripts/installer.ps1.
    local skill_packager_source="$repo_root/scripts/package_skill.py"
    if [ -f "$skill_packager_source" ]; then
        safe_copy "$skill_packager_source" "$scripts_dest/package_skill.py" true "[OK] Skill packager installed at: $scripts_dest/package_skill.py"
    fi

    # Copy the /skills import hygiene gate (v3.6.0 Phase 4 / N6). Hardens the
    # LOCAL import path with HTTPS-only source validation, an install_allowed
    # discovery-only flag, and hash-on-import (the hashing reuses
    # scripts/lib/integrations/manifest.py, copied separately under lib/). It
    # adds NO outbound call or credential and is additive to the pre-install
    # skill-security scan. Lockstep with the same block in scripts/installer.ps1.
    local import_hygiene_source="$repo_root/scripts/import_skills.py"
    if [ -f "$import_hygiene_source" ]; then
        safe_copy "$import_hygiene_source" "$scripts_dest/import_skills.py" true "[OK] Skill-import hygiene gate installed at: $scripts_dest/import_skills.py"
    fi

    # Copy nexus-hub affected CLI dispatcher (v2.2.0 / codegraph Phase 5 /
    # T032). Thin wrapper around the nexus-code-search code_affected_tests
    # graph query so users can pipe `git diff --name-only` into a test-impact
    # query without booting the MCP server. Lockstep with the same block in
    # scripts/installer.ps1.
    local affected_source="$repo_root/scripts/nexus_hub_affected.py"
    if [ -f "$affected_source" ]; then
        safe_copy "$affected_source" "$scripts_dest/nexus_hub_affected.py" true "[OK] Affected-tests CLI installed at: $scripts_dest/nexus_hub_affected.py"
    fi

    # Copy the nexus-hub CLI core (v3.7.0 Phase 3). The logic behind the
    # `nexus-hub` launcher on PATH: `nexus-hub --version` and `nexus-hub
    # upgrade`. Stdlib-only, cross-platform single .py (NI-v24-1), so no .ps1
    # sibling. The launcher itself + the VERSION file are installed by
    # install_cli_launcher below. Lockstep with the same block in
    # scripts/installer.ps1.
    local cli_source="$repo_root/scripts/nexus_hub_cli.py"
    if [ -f "$cli_source" ]; then
        safe_copy "$cli_source" "$scripts_dest/nexus_hub_cli.py" true "[OK] nexus-hub CLI installed at: $scripts_dest/nexus_hub_cli.py"
    fi

    # Copy v2.3.0 CI validators (Phase 2 / T004-T005). Four standalone static
    # validators that run on the clean tree and fail non-zero on a finding:
    # validate_no_personal_paths.py scans distributed docs for leaked
    # /Users/<name> or C:\Users\<name> paths; validate_unicode_safety.py
    # flags unsafe / confusable Unicode (Trojan Source, zero-width chars);
    # scan_supply_chain_iocs.py inspects dependency manifests and installers
    # for curl-pipe-bash, lifecycle shell-outs, floating GitHub Action refs,
    # and known typosquats; validate_workflow_security.py audits
    # .github/workflows/*.yml for pull_request_target + head checkout,
    # ${{ github.event.* }} injection in run: blocks, and write-all
    # permissions. Lockstep with the same block in scripts/installer.ps1.
    local no_paths_source="$repo_root/scripts/validate_no_personal_paths.py"
    if [ -f "$no_paths_source" ]; then
        safe_copy "$no_paths_source" "$scripts_dest/validate_no_personal_paths.py" true "[OK] No-personal-paths validator installed at: $scripts_dest/validate_no_personal_paths.py"
    fi
    local unicode_source="$repo_root/scripts/validate_unicode_safety.py"
    if [ -f "$unicode_source" ]; then
        safe_copy "$unicode_source" "$scripts_dest/validate_unicode_safety.py" true "[OK] Unicode-safety validator installed at: $scripts_dest/validate_unicode_safety.py"
    fi
    local iocs_source="$repo_root/scripts/scan_supply_chain_iocs.py"
    if [ -f "$iocs_source" ]; then
        safe_copy "$iocs_source" "$scripts_dest/scan_supply_chain_iocs.py" true "[OK] Supply-chain IOC scanner installed at: $scripts_dest/scan_supply_chain_iocs.py"
    fi
    local workflow_source="$repo_root/scripts/validate_workflow_security.py"
    if [ -f "$workflow_source" ]; then
        safe_copy "$workflow_source" "$scripts_dest/validate_workflow_security.py" true "[OK] Workflow-security validator installed at: $scripts_dest/validate_workflow_security.py"
    fi
    # validate_solution_frontmatter.py (v2.4.0) is a parser-safety linter for
    # solution-knowledge-base docs (docs/solutions/<category>/<slug>.md); it
    # uses Python stdlib only. Lockstep with scripts/installer.ps1.
    local solution_fm_source="$repo_root/scripts/validate_solution_frontmatter.py"
    if [ -f "$solution_fm_source" ]; then
        safe_copy "$solution_fm_source" "$scripts_dest/validate_solution_frontmatter.py" true "[OK] Solution-frontmatter validator installed at: $scripts_dest/validate_solution_frontmatter.py"
    fi
    # check_version_sync.py (v3.0.0): version-drift guard. Reads the canonical
    # version from .claude-plugin/plugin.json and asserts every other
    # version-carrying surface (both installers, marketplace.json, the latest
    # CHANGELOG heading, README/AGENTS markers) matches it. Stdlib-only, so it
    # is a single cross-platform .py file with no .ps1 sibling (NI-v24-1
    # convention). Lockstep with scripts/installer.ps1.
    local version_sync_source="$repo_root/scripts/check_version_sync.py"
    if [ -f "$version_sync_source" ]; then
        safe_copy "$version_sync_source" "$scripts_dest/check_version_sync.py" true "[OK] Version-sync guard installed at: $scripts_dest/check_version_sync.py"
    fi
    # scan_skill_security.py (v3.0.0): thin CLI launcher for the
    # nexus-skill-scanner static skill-security engine (extensions/nexus-skill-scanner).
    # Stdlib-only launcher; it locates the bundled package src under extensions/.
    # Single cross-platform .py file with no .ps1 sibling (NI-v24-1 convention).
    # Lockstep with scripts/installer.ps1.
    local scan_skill_source="$repo_root/scripts/scan_skill_security.py"
    if [ -f "$scan_skill_source" ]; then
        safe_copy "$scan_skill_source" "$scripts_dest/scan_skill_security.py" true "[OK] Skill-security scanner installed at: $scripts_dest/scan_skill_security.py"
    fi
    # generate_release_changelog.py / .ps1 (v2.4.0): local conventional-commit
    # release helper - computes the next semver bump + a Keep-a-Changelog
    # section from git history. Zero-outbound (local git only); an optional
    # helper for the /update version / /update changelog flows, NOT a GitHub
    # Action. Both siblings ship. Lockstep with scripts/installer.ps1.
    local release_changelog_py="$repo_root/scripts/generate_release_changelog.py"
    if [ -f "$release_changelog_py" ]; then
        safe_copy "$release_changelog_py" "$scripts_dest/generate_release_changelog.py" true "[OK] Release-changelog helper installed at: $scripts_dest/generate_release_changelog.py"
    fi
    local release_changelog_ps1="$repo_root/scripts/generate_release_changelog.ps1"
    if [ -f "$release_changelog_ps1" ]; then
        safe_copy "$release_changelog_ps1" "$scripts_dest/generate_release_changelog.ps1" true "[OK] Release-changelog helper (PowerShell) installed at: $scripts_dest/generate_release_changelog.ps1"
    fi

    # Copy v2.3.0 Phase 4 lifecycle scripts (T011 consult advisor + T012
    # harness audit). The doctor / repair / list-installed surface itself
    # lives on `scripts/lib/integrations/runner.py` so it ships via the
    # registry copy step further down; no separate file is needed for it.
    # Lockstep with the matching block in scripts/installer.ps1.
    local consult_source="$repo_root/scripts/nexus_hub_consult.py"
    if [ -f "$consult_source" ]; then
        safe_copy "$consult_source" "$scripts_dest/nexus_hub_consult.py" true "[OK] Consult advisor installed at: $scripts_dest/nexus_hub_consult.py"
    fi
    local audit_source="$repo_root/scripts/harness_audit.py"
    if [ -f "$audit_source" ]; then
        safe_copy "$audit_source" "$scripts_dest/harness_audit.py" true "[OK] Harness audit installed at: $scripts_dest/harness_audit.py"
    fi

    # Copy v2.3.0 Phase 6 framework-coverage generator (T017). Read-only,
    # zero-outbound: reads the optional framework-mapping frontmatter fields
    # (mitre_attack / atlas_techniques / d3fend_techniques / nist_csf /
    # nist_ai_rmf) across catalog/skills/ and emits a coverage matrix
    # (Markdown or JSON) of which skills cover which MITRE/NIST controls.
    # Lockstep with the matching block in scripts/installer.ps1.
    local coverage_source="$repo_root/scripts/build_framework_coverage.py"
    if [ -f "$coverage_source" ]; then
        safe_copy "$coverage_source" "$scripts_dest/build_framework_coverage.py" true "[OK] Framework coverage generator installed at: $scripts_dest/build_framework_coverage.py"
    fi

    # Copy feature-directory bootstrap scripts (v2.1.0 / adoption-spec-kit
    # Phase 7 / G5). The two scripts resolve the next specs/<NNN>-<slug>/
    # prefix (sequential or timestamp per .specify/init-options.json),
    # create the directory, and persist .specify/feature.json so downstream
    # commands (/spec clarify, /spec analyze, /plan issues) can locate
    # the active feature directory without git-branch coupling. Lockstep
    # with the same block in scripts/installer.ps1.
    local new_feature_sh_source="$repo_root/scripts/new-feature.sh"
    if [ -f "$new_feature_sh_source" ]; then
        safe_copy "$new_feature_sh_source" "$scripts_dest/new-feature.sh" true "[OK] Feature directory bootstrap (bash) installed at: $scripts_dest/new-feature.sh"
        chmod +x "$scripts_dest/new-feature.sh" 2>/dev/null || true
    fi
    local new_feature_ps1_source="$repo_root/scripts/new-feature.ps1"
    if [ -f "$new_feature_ps1_source" ]; then
        safe_copy "$new_feature_ps1_source" "$scripts_dest/new-feature.ps1" true "[OK] Feature directory bootstrap (PowerShell) installed at: $scripts_dest/new-feature.ps1"
    fi

    # Copy integration registry module (v2.1.0+). The integrations registrar
    # ships the per-platform install logic for the extended platforms (Windsurf,
    # Antigravity 2.0, Gemini CLI, Nexus-AI). The recursive folder copy lands
    # the whole class hierarchy under ~/.nexus-hub/scripts/lib/integrations/.
    local integrations_src="$repo_root/scripts/lib/integrations"
    local integrations_dest="$scripts_dest/lib/integrations"
    if [ -d "$integrations_src" ]; then
        safe_folder_copy "$integrations_src" "$integrations_dest" "[OK] Integration registry installed at: $integrations_dest"
    fi
    # Empty package markers so the module can be imported from the installed location.
    if [ -d "$scripts_dest/lib" ]; then
        : > "$scripts_dest/lib/__init__.py" 2>/dev/null || true
    fi

    # Copy style-guides (v1.0.0+). Reference content for /research compile
    # and /research report; deliberately not in catalog/commands/ so the files
    # do not surface as slash commands.
    local style_guides_src="$repo_root/catalog/style-guides"
    local style_guides_dest="$nexus_home/style-guides"
    if [ -d "$style_guides_src" ]; then
        safe_folder_copy "$style_guides_src" "$style_guides_dest" "[OK] Style guides installed at: $style_guides_dest"
    fi

    # Copy opt-in git pre-commit hook sources (v1.1.2+; expanded to four
    # platform-parallel variants in v1.1.3). Each hook calls only its own
    # CLI - they are independent of each other. The hooks themselves are
    # NEVER auto-wired into a repository; users opt in by running the
    # /setup hooks slash command from inside the target
    # repo, which copies the chosen platform's script to .git/hooks/pre-commit.
    local nexus_hooks_dest="$nexus_home/hooks"
    mkdir -p "$nexus_hooks_dest"
    for diff_review_variant in claude-diff-review.sh gemini-diff-review.sh antigravity-cli-diff-review.sh codex-diff-review.sh opencode-diff-review.sh; do
        local diff_review_src="$repo_root/catalog/hooks/$diff_review_variant"
        if [ -f "$diff_review_src" ]; then
            safe_copy "$diff_review_src" "$nexus_hooks_dest/$diff_review_variant" true "[OK] Pre-commit review hook source installed at: $nexus_hooks_dest/$diff_review_variant"
            chmod +x "$nexus_hooks_dest/$diff_review_variant" 2>/dev/null || true
        fi
    done

    # Check Python availability
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        write_item "Note: Python 3 is required to generate reports." "$YELLOW"
        write_item "Install via your package manager (e.g., brew install python3, apt install python3)." "$YELLOW"
    else
        local python_cmd="python3"
        if ! command -v python3 >/dev/null 2>&1; then python_cmd="python"; fi

        if $python_cmd -c "import docx; import pptx" 2>/dev/null; then
            write_item "[OK] Python dependencies (python-docx, python-pptx) are available" "$GREEN"
        else
            write_item "Note: Install report dependencies with: pip install python-docx python-pptx" "$YELLOW"
        fi
    fi

    # v0.9.7: The interactive "Import custom Word/PowerPoint templates?" prompt has been
    # removed. Custom template selection is now handled at report-generation time by the
    # `/research report` command (generic vs custom path gate). Bundled generic templates
    # are still copied silently above so the command has a default to offer.

    # List installed templates
    echo ""
    write_item "Installed templates:" "$RESET"
    local found_templates=false
    for t in "$templates_dest"/*.docx "$templates_dest"/*.pptx; do
        if [ -f "$t" ]; then
            write_item "  $(basename "$t")" "$GREEN"
            found_templates=true
        fi
    done
    if [ "$found_templates" = false ]; then
        write_item "  (none)" "$GRAY"
    fi
    echo ""
}

# --- nexus-hub CLI launcher (v3.7.0 Phase 3) ---

# Writes the installed-version marker and drops the `nexus-hub` launcher on PATH
# (~/.nexus-hub/bin/nexus-hub). The launcher is a thin shim over the CLI core
# (scripts/nexus_hub_cli.py, copied by install_templates) that powers
# `nexus-hub --version` and `nexus-hub upgrade`. `upgrade`'s only outbound call
# is to the project's own GitHub. PATH wiring is best-effort: a clear hint is
# printed and shell-rc files are NEVER auto-edited (a no-prompt install must not
# silently mutate a user dotfile). Lockstep with Install-CliLauncher in
# scripts/installer.ps1.
install_cli_launcher() {
    local repo_root="$1"
    local nexus_home="$HOME/.nexus-hub"
    local bin_dest="$nexus_home/bin"

    echo ""
    write_subsection_banner "nexus-hub CLI"
    echo ""

    # Installed-version marker (install-mode independent; read by the CLI's
    # --version and upgrade). Written from the canonical $NEXUS_HUB_VERSION, so
    # it is deliberately NOT a check_version_sync surface (never hand-edited).
    printf '%s\n' "$NEXUS_HUB_VERSION" > "$nexus_home/VERSION"
    write_item "[OK] Version marker written: $nexus_home/VERSION ($NEXUS_HUB_VERSION)" "$GREEN"

    mkdir -p "$bin_dest"
    local launcher_source="$repo_root/scripts/nexus-hub"
    if [ -f "$launcher_source" ]; then
        safe_copy "$launcher_source" "$bin_dest/nexus-hub" true "[OK] nexus-hub launcher installed at: $bin_dest/nexus-hub"
        chmod +x "$bin_dest/nexus-hub" 2>/dev/null || true
    fi

    # PATH hint (best-effort; never auto-edits a shell rc file).
    case ":${PATH:-}:" in
        *":$bin_dest:"*)
            write_item "[OK] $bin_dest is already on your PATH -- run: nexus-hub --version" "$GREEN"
            ;;
        *)
            # The tildes below are intentional display text in a user-facing
            # hint (shown literally as "~/.zshrc"), not paths to be expanded.
            # shellcheck disable=SC2088
            local rc="your shell profile (e.g. ~/.bashrc or ~/.zshrc)"
            # shellcheck disable=SC2088
            case "$(basename "${SHELL:-}")" in
                zsh)  rc="~/.zshrc" ;;
                bash) rc="~/.bashrc" ;;
            esac
            write_item "To use the 'nexus-hub' command, add its bin directory to your PATH." "$YELLOW"
            write_item "  Add this line to $rc, then restart your shell:" "$RESET"
            write_item "    export PATH=\"\$HOME/.nexus-hub/bin:\$PATH\"" "$CYAN"
            write_item "  Until then, run it directly: $bin_dest/nexus-hub --version" "$GRAY"
            ;;
    esac
    echo ""
}

# --- Skill Discovery ---

install_skill_discovery() {
    local repo_root="$1"

    # --- Skill Index (all platforms) ---
    echo ""
    write_item "Installing skill index for all platforms..." "$RESET"

    local nexus_home="$HOME/.nexus-hub"
    local nexus_data="$nexus_home/data"
    mkdir -p "$nexus_data"

    local skill_index="$repo_root/data/SKILL_INDEX.md"
    if [ -f "$skill_index" ]; then
        cp "$skill_index" "$nexus_data/SKILL_INDEX.md"
        write_item "  Skill index copied to $nexus_data" "$GREEN"
    else
        write_item "  SKILL_INDEX.md not found. Run 'python infrastructure/tools/build_skills_catalog.py' first." "$YELLOW"
    fi

    # Copy skills.json and bundles.json
    [ -f "$repo_root/data/skills.json" ] && cp "$repo_root/data/skills.json" "$nexus_data/skills.json"
    [ -f "$repo_root/data/bundles.json" ] && cp "$repo_root/data/bundles.json" "$nexus_data/bundles.json"
    write_item "  Skill data installed to $nexus_data" "$GREEN"

    # --- MCP Skill Server (Claude Code only) ---
    echo ""
    write_item "MCP Skill Server (Claude Code integration)" "$RESET"

    # Check Python >= 3.10.
    # Ask the interpreter for its own version instead of parsing `--version`
    # output with grep. BSD grep (the macOS default) lacks `-P` (PCRE), so the old
    # `grep -oP` approach printed "grep: invalid option -- P" and silently left
    # python_cmd empty, skipping the entire MCP server install on macOS.
    detect_python_310() {
        local cmd ver
        for cmd in python3 python; do
            if command -v "$cmd" >/dev/null 2>&1; then
                ver=$("$cmd" -c 'import sys; print(sys.version_info[0] * 100 + sys.version_info[1])' 2>/dev/null)
                if [ -n "$ver" ] && [ "$ver" -ge 310 ]; then
                    echo "$cmd"
                    return 0
                fi
            fi
        done
        return 1
    }

    local python_cmd=""
    python_cmd=$(detect_python_310) || python_cmd=""

    # Offer to auto-install Python when it is missing or too old, mirroring the
    # Node.js auto-install flow so every dependency is handled in a single run. A
    # non-interactive run (the piped one-command bootstrap, --yes, or CI) installs
    # without asking; an interactive run prompts first. This only fires when no
    # usable Python exists, so it never shadows an existing conda/pyenv interpreter.
    if [ -z "$python_cmd" ]; then
        local py_resp=""
        if command -v brew >/dev/null 2>&1; then
            if [ "$ASSUME_YES" = true ]; then py_resp="y"; else py_resp=$(read_prompt "Python 3.10+ not found. Install it via Homebrew? [Y]es / [N]o"); fi
            if [[ "$py_resp" =~ ^[Yy] ]]; then
                write_item "  Installing Python via Homebrew..." "$RESET"
                brew install python@3.12 >/dev/null 2>&1 || true
                python_cmd=$(detect_python_310) || python_cmd=""
            fi
        elif command -v apt-get >/dev/null 2>&1; then
            if [ "$ASSUME_YES" = true ]; then py_resp="y"; else py_resp=$(read_prompt "Python 3.10+ not found. Install it via apt? [Y]es / [N]o"); fi
            if [[ "$py_resp" =~ ^[Yy] ]]; then
                write_item "  Installing Python via apt..." "$RESET"
                sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-venv python3-pip >/dev/null 2>&1 || true
                python_cmd=$(detect_python_310) || python_cmd=""
            fi
        fi
    fi

    if [ -z "$python_cmd" ]; then
        write_item "  Python 3.10+ not found. MCP server requires Python 3.10 or newer." "$YELLOW"
        write_item "  Install Python 3.10+ (macOS: brew install python@3.12; Linux: apt install python3) and re-run." "$YELLOW"
        return
    fi

    write_item "  Found $python_cmd" "$GREEN"

    # Copy MCP server source
    local mcp_src="$repo_root/extensions/nexus-skill-server"
    local mcp_dest="$nexus_home/mcp-server"
    rm -rf "$mcp_dest"
    cp -r "$mcp_src" "$mcp_dest"
    write_item "  MCP server source copied to $mcp_dest" "$GREEN"

    # Create venv and install
    local venv_path="$nexus_home/mcp-server-venv"

    if command -v uv >/dev/null 2>&1; then
        write_item "  Creating venv with uv..." "$RESET"
        uv venv "$venv_path" >/dev/null 2>&1
        uv pip install --python "$venv_path/bin/python" -e "$mcp_dest" >/dev/null 2>&1
    else
        write_item "  Creating venv with $python_cmd..." "$RESET"
        "$python_cmd" -m venv "$venv_path" >/dev/null 2>&1
        "$venv_path/bin/pip" install -q -e "$mcp_dest" >/dev/null 2>&1
    fi

    write_item "  MCP server venv created at $venv_path" "$GREEN"

    # Register in ~/.claude/settings.json
    local claude_dir="$HOME/.claude"
    local claude_settings="$claude_dir/settings.json"
    mkdir -p "$claude_dir"

    if [ ! -f "$claude_settings" ]; then
        echo '{}' > "$claude_settings"
    fi

    # Install nexus-code-search into the same venv (v1.0.0+).
    # Local-only code-search MCP. Zero outbound calls. See AGENTS.md MCP Registry Policy.
    local code_search_src="$repo_root/extensions/nexus-code-search"
    local code_search_dest="$nexus_home/code-search"
    if [ -d "$code_search_src" ]; then
        rm -rf "$code_search_dest"
        cp -r "$code_search_src" "$code_search_dest"
        if command -v uv >/dev/null 2>&1; then
            uv pip install --python "$venv_path/bin/python" -e "$code_search_dest" >/dev/null 2>&1
        else
            "$venv_path/bin/pip" install -q -e "$code_search_dest" >/dev/null 2>&1
        fi
        write_item "  nexus-code-search installed at $code_search_dest" "$GREEN"
    fi

    # Install nexus-web-fetch into the same venv (v1.0.0+).
    # Local-only web-fetch MCP (fetches user-specified URLs only). See AGENTS.md.
    local web_fetch_src="$repo_root/extensions/nexus-web-fetch"
    local web_fetch_dest="$nexus_home/web-fetch"
    if [ -d "$web_fetch_src" ]; then
        rm -rf "$web_fetch_dest"
        cp -r "$web_fetch_src" "$web_fetch_dest"
        if command -v uv >/dev/null 2>&1; then
            uv pip install --python "$venv_path/bin/python" -e "$web_fetch_dest" >/dev/null 2>&1
        else
            "$venv_path/bin/pip" install -q -e "$web_fetch_dest" >/dev/null 2>&1
        fi
        write_item "  nexus-web-fetch installed at $web_fetch_dest" "$GREEN"
    fi

    # Install nexus-context-compressor into the same venv (v3.2.0+).
    # Local-first context-compression engine. Zero outbound by default; tiktoken
    # is the only required dependency, with an offline stdlib fallback. Installed
    # with the [mcp] extra so the Phase 4 (T013) compress/retrieve MCP server runs;
    # the server is registered in the settings.json merge block below.
    # See AGENTS.md MCP Registry Policy.
    local context_compressor_src="$repo_root/extensions/nexus-context-compressor"
    local context_compressor_dest="$nexus_home/context-compressor"
    if [ -d "$context_compressor_src" ]; then
        rm -rf "$context_compressor_dest"
        cp -r "$context_compressor_src" "$context_compressor_dest"
        if command -v uv >/dev/null 2>&1; then
            uv pip install --python "$venv_path/bin/python" -e "${context_compressor_dest}[mcp]" >/dev/null 2>&1
        else
            "$venv_path/bin/pip" install -q -e "${context_compressor_dest}[mcp]" >/dev/null 2>&1
        fi
        write_item "  nexus-context-compressor installed at $context_compressor_dest" "$GREEN"
    fi

    # Use python to safely merge MCP server config into settings.json (all three internal servers).
    "$python_cmd" -c "
import json, sys
path = sys.argv[1]
venv = sys.argv[2]
hub = sys.argv[3]
with open(path, 'r') as f:
    data = json.load(f)
if 'mcpServers' not in data:
    data['mcpServers'] = {}
data['mcpServers']['nexus-skill-server'] = {
    'command': venv + '/bin/python',
    'args': ['-m', 'nexus_skill_server'],
    'env': {'NEXUS_HUB_ROOT': hub}
}
data['mcpServers']['nexus-code-search'] = {
    'command': venv + '/bin/python',
    'args': ['-m', 'nexus_code_search'],
    'env': {'NEXUS_HUB_ROOT': hub}
}
data['mcpServers']['nexus-web-fetch'] = {
    'command': venv + '/bin/python',
    'args': ['-m', 'nexus_web_fetch'],
    'env': {'NEXUS_HUB_ROOT': hub}
}
data['mcpServers']['nexus-context-compressor'] = {
    'command': venv + '/bin/python',
    'args': ['-m', 'nexus_context_compressor', 'serve'],
    'env': {'NEXUS_HUB_ROOT': hub}
}
# Remove superseded legacy (devai-hub) MCP entries left by pre-rename installs;
# they are replaced one-for-one by the nexus-* servers registered above.
for legacy in ('devai-skill-server', 'devai-code-search', 'devai-web-fetch'):
    data['mcpServers'].pop(legacy, None)
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
" "$claude_settings" "$venv_path" "$nexus_home"

    write_item "  MCP servers registered in $claude_settings (nexus-skill-server, nexus-code-search, nexus-web-fetch, nexus-context-compressor)" "$GREEN"
    write_item "  Servers will auto-start with Claude Code. No manual steps needed." "$GREEN"
}

# --- Banner ---

# ASCII-art NEXUS-HUB wordmark. Printed at startup ahead of the welcome banner.
# Constraints: <=80 columns wide, <=8 rows tall, ASCII-only (no Unicode block
# characters - commit messages and source files are ASCII-only on Windows per
# project rules). Modeled after the Claude Code CLI banner style.
print_nexus_banner() {
    echo ""
    echo -e "${CYAN}"
    cat <<'NEXUS_BANNER_EOF'
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗      ██╗  ██╗██╗   ██╗██████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝      ██║  ██║██║   ██║██╔══██╗
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗█████╗███████║██║   ██║██████╔╝
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║╚════╝██╔══██║██║   ██║██╔══██╗
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║      ██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝      ╚═╝  ╚═╝ ╚═════╝ ╚═════╝
NEXUS_BANNER_EOF
    echo -e "${RESET}"
    echo -e "  ${GRAY}Multi-platform AI skill harness  -  v${NEXUS_HUB_VERSION}  -  https://github.com/bendourthe/Nexus-Hub${RESET}"
    echo ""
}

# Detects an existing ~/.devai-hub/ install and migrates it to ~/.nexus-hub/.
# One-shot, one-way per the backward-compat decision in
# docs/archive/v2/v2.0.0/rename-decisions.md. The installer does NOT ship a symlink or
# compatibility shim. Three branches:
#   1. legacy only            -> prompt to migrate (default Y), then `mv`.
#   2. legacy AND new co-exist -> ask user: keep-new, abort, or merge.
#   3. neither / new only      -> no-op (fresh or already-migrated install).
# Uninstalls the legacy DevAI-Hub VS Code extension if present. The
# Claude Usage Monitor was published under `devai-hub.claude-usage-monitor`
# before the rename; the current build ships as `nexus-hub.claude-usage-monitor`.
# Leaving both installed produces a duplicate entry in VS Code's Extensions
# pane and two status-bar items. Called unconditionally at startup -- the
# function silently no-ops when nothing legacy is installed, so it is safe
# (and necessary) to re-run on every install, including for users who
# migrated ~/.devai-hub/ in an earlier installer run.
remove_legacy_vscode_extensions() {
    command -v code >/dev/null 2>&1 || return 0
    local installed
    installed=$(code --list-extensions 2>/dev/null) || return 0

    local legacy_ids=("devai-hub.claude-usage-monitor")
    local id emitted=0
    for id in "${legacy_ids[@]}"; do
        if printf '%s\n' "$installed" | grep -qx "$id"; then
            if [ "$emitted" -eq 0 ]; then echo ""; fi
            echo -e "  ${YELLOW}Removing legacy VS Code extension: $id${RESET}"
            if code --uninstall-extension "$id" >/dev/null 2>&1; then
                echo -e "  ${GREEN}[OK] Removed $id${RESET}"
            else
                echo -e "  ${YELLOW}Could not auto-remove $id (uninstall it manually from VS Code)${RESET}"
            fi
            emitted=1
        fi
    done
    if [ "$emitted" -eq 1 ]; then echo ""; fi
}

migrate_legacy_install() {
    local legacy="$HOME/.devai-hub"
    local current="$HOME/.nexus-hub"

    if [ -d "$legacy" ] && [ ! -d "$current" ]; then
        echo ""
        echo -e "  ${YELLOW}Detected existing DevAI-Hub install at $legacy${RESET}"
        echo -ne "  ${YELLOW}Migrate to Nexus-Hub ($current)? [Y/n]: ${RESET}"
        local ans
        read -r ans
        ans=${ans:-Y}
        if [[ "$ans" =~ ^[Yy] ]]; then
            mv "$legacy" "$current"
            echo -e "  ${GREEN}Migrated $legacy -> $current${RESET}"
        else
            echo -e "  ${RED}Migration declined. Remove $legacy manually or rerun and accept.${RESET}"
            exit 1
        fi
        echo ""
    elif [ -d "$legacy" ] && [ -d "$current" ]; then
        echo ""
        echo -e "  ${YELLOW}Both $legacy and $current exist.${RESET}"
        echo -e "  Choose: [k]eep new + delete old, [a]bort + handle manually, [m]erge (best effort)"
        echo -ne "  ${YELLOW}Selection [k/a/m]: ${RESET}"
        local ans
        read -r ans
        case "$ans" in
            [Kk]*)
                rm -rf "$legacy"
                echo -e "  ${GREEN}Removed $legacy. Keeping $current.${RESET}"
                ;;
            [Mm]*)
                cp -R "$legacy"/. "$current"/
                rm -rf "$legacy"
                echo -e "  ${GREEN}Merged $legacy into $current (best effort).${RESET}"
                ;;
            *)
                echo -e "  ${RED}Aborted. Resolve $legacy and $current manually before rerunning.${RESET}"
                exit 1
                ;;
        esac
        echo ""
    fi
}

print_banner() {
    # The Nexus-Hub Universal Installer welcome line. The ASCII wordmark above
    # (and migrate_legacy_install when active) already produces a trailing
    # blank line, so this function deliberately does not add its own leading
    # blank. Title text is preserved for the installer-smoke test contract.
    echo -e "${CYAN}Welcome to the Nexus-Hub Universal Installer (v${NEXUS_HUB_VERSION})${RESET}"
}

# --- Main ---

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# --- Flag parsing (v2.2.0+) ----------------------------------------------
# Currently supported:
#   --enterprise        Opt in to the standalone Gemini CLI install path. After
#                       2026-06-18, Gemini CLI only serves enterprise tenants
#                       with a paid Gemini API key (per the 2026-05-21 Google
#                       Developers Blog announcement). Non-enterprise users
#                       install Antigravity CLI instead.
#   -h | --help         Show usage and exit.
ENTERPRISE=0
SUBCOMMAND=""
SUBCOMMAND_ARGS=()
BRANCH_NAME=""
PASSTHRU_ARGS=()

# v3.7.0 / Phase 2 -- no-prompt install controls.
WORKSPACE_PATH=""   # set by --workspace <path>; empty => global scope (default)
PLATFORMS_ARG=""    # set by --platforms <csv>; empty => all platforms (default)
YES_FLAG=0          # --yes : non-interactive, auto-confirm + refresh
FORCE_FLAG=0        # --force : overwrite existing managed files without asking

# Map an arbitrary git branch name to a filesystem-safe cache token: every
# character outside [A-Za-z0-9._-] becomes '-', parent-dir tokens are
# neutralized, and a leading dot/dash is stripped so the result is never a
# hidden dir or a path-traversal vector.
sanitize_branch_name() {
    local raw="$1" s
    s="${raw//[!A-Za-z0-9._-]/-}"
    s="${s//../-}"
    s="${s#[-.]}"
    [ -n "$s" ] || s="branch"
    printf '%s' "$s"
}

show_installer_usage() {
    cat <<EOF
Usage:
  bash scripts/installer.sh [--workspace PATH] [--platforms LIST] [--yes]
                            [--force] [--enterprise] [-h | --help]
  bash scripts/installer.sh init [--target PATH] [--dry-run]
  bash scripts/installer.sh --print-config <integration-key>
  bash scripts/installer.sh --check
  bash scripts/installer.sh --branch <name> [--enterprise]

By default the installer runs with NO prompts: a global install across ALL
supported platforms (absent platforms skip-with-note). Existing managed files
that you have customized are detected and you are asked ONCE whether to
overwrite them; with --yes / --force (or any non-interactive / piped run) they
are refreshed to the latest version automatically.

Subcommands:
  init           Bootstrap project-local surfaces (Cursor rules, Claude
                 settings.json stub) from a global install. Walks every
                 registered integration that defines wire_project_surfaces()
                 and writes the corresponding files. --target defaults to the
                 current directory.

Read-only modes (no disk writes):
  --print-config <key>  Dump the Markdown readout of what the given integration
                        would install. Use --print-config=<key> or
                        --print-config <key>.
  --check               Dry-run every integration and exit non-zero if any
                        action would create / update / remove a file. Useful in
                        CI to detect install drift.

Options:
  --workspace <path>  Install into a single project directory instead of the
                 default global (all-projects) scope. Use --workspace=<path> or
                 --workspace <path>.
  --platforms <list>  Install only the given comma-separated integration keys
                 instead of all platforms. Valid keys: claude, codex, gemini,
                 antigravity2, gemini-cli, copilot, cursor, opencode, nexus-ai,
                 aider, windsurf, kimi, qwen, openclaw. Use --platforms=<list>
                 or --platforms <list>.
  --yes, -y      Non-interactive: never prompt, and refresh existing managed
                 files to the latest version (also implied when stdin is not a
                 TTY, e.g. a piped curl|bash install).
  --force        Overwrite existing managed files with the Nexus-Hub version
                 without asking (implies --yes for prompting).
  --enterprise   Install the standalone Gemini CLI integration. Requires a paid
                 Gemini API key. After 2026-06-18 (per the 2026-05-21 Google
                 Developers Blog announcement), Gemini CLI stops serving free /
                 Google AI Pro / Ultra / GitHub-installed users; this flag is
                 the only way to keep the integration after that date.
                 Default (without --enterprise): the installer prints a sunset
                 warning and skips the Gemini CLI install, but still installs
                 Antigravity CLI (which covers the same functionality via the
                 antigravity2 integration).
  --branch <name>  Install the catalog from a pushed branch instead of the
                 current checkout. Shallow-clones the repo at <name> into a
                 deterministic cache directory (~/.nexus-hub/branches/<name>/),
                 then runs the install from that checkout -- the user's working
                 copy is never touched. Combine with --check / --dry-run to
                 print the resolved cache path and clone source without cloning
                 (a probe). Use --branch=<name> or --branch <name>.
  -h, --help     Show this help and exit.
EOF
}
PRINT_CONFIG_KEY=""
CHECK_MODE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --enterprise)
            ENTERPRISE=1
            PASSTHRU_ARGS+=("--enterprise")
            shift
            ;;
        --workspace)
            WORKSPACE_PATH="${2:-}"
            if [ -z "$WORKSPACE_PATH" ]; then
                echo "--workspace requires a path" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--workspace" "$WORKSPACE_PATH")
            shift 2
            ;;
        --workspace=*)
            WORKSPACE_PATH="${1#--workspace=}"
            if [ -z "$WORKSPACE_PATH" ]; then
                echo "--workspace requires a path" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--workspace=$WORKSPACE_PATH")
            shift
            ;;
        --platforms)
            PLATFORMS_ARG="${2:-}"
            if [ -z "$PLATFORMS_ARG" ]; then
                echo "--platforms requires a comma-separated list" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--platforms" "$PLATFORMS_ARG")
            shift 2
            ;;
        --platforms=*)
            PLATFORMS_ARG="${1#--platforms=}"
            if [ -z "$PLATFORMS_ARG" ]; then
                echo "--platforms requires a comma-separated list" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--platforms=$PLATFORMS_ARG")
            shift
            ;;
        --yes|-y)
            YES_FLAG=1
            PASSTHRU_ARGS+=("--yes")
            shift
            ;;
        --force)
            FORCE_FLAG=1
            PASSTHRU_ARGS+=("--force")
            shift
            ;;
        --branch)
            BRANCH_NAME="${2:-}"
            if [ -z "$BRANCH_NAME" ]; then
                echo "--branch requires a branch name" >&2
                exit 2
            fi
            shift 2
            ;;
        --branch=*)
            BRANCH_NAME="${1#--branch=}"
            if [ -z "$BRANCH_NAME" ]; then
                echo "--branch requires a branch name" >&2
                exit 2
            fi
            shift
            ;;
        --print-config)
            PRINT_CONFIG_KEY="${2:-}"
            if [ -z "$PRINT_CONFIG_KEY" ]; then
                echo "--print-config requires an integration key" >&2
                exit 2
            fi
            shift 2
            ;;
        --print-config=*)
            PRINT_CONFIG_KEY="${1#--print-config=}"
            shift
            ;;
        --check|--dry-run)
            CHECK_MODE=1
            shift
            ;;
        -h|--help)
            show_installer_usage
            exit 0
            ;;
        init)
            SUBCOMMAND="init"
            shift
            SUBCOMMAND_ARGS=("$@")
            break
            ;;
        *)
            echo "Unknown installer flag: $1" >&2
            show_installer_usage >&2
            exit 2
            ;;
    esac
done

# --- Branch-based install (v2.4.0+) --------------------------------------
# When --branch <name> is given, install the catalog from a shallow clone of
# that pushed branch in a deterministic cache dir, leaving the user's working
# copy untouched. NEXUS_HUB_BRANCH_RESOLVED guards against re-cloning once we
# have re-exec'd into the cached checkout. This block runs before the read-only
# dispatch so that --branch + --check is a clone-free probe.
if [ -n "$BRANCH_NAME" ] && [ "${NEXUS_HUB_BRANCH_RESOLVED:-0}" != "1" ]; then
    branch_token="$(sanitize_branch_name "$BRANCH_NAME")"
    branch_cache_dir="$HOME/.nexus-hub/branches/$branch_token"
    branch_src_url="$(git -C "$REPO_ROOT" config --get remote.origin.url 2>/dev/null || true)"
    [ -n "$branch_src_url" ] || branch_src_url="file://$REPO_ROOT"

    if [ "$CHECK_MODE" = "1" ]; then
        # Probe: print the resolution and exit without cloning or installing.
        echo "nexus-hub branch install (dry-run):"
        echo "  branch:    $BRANCH_NAME"
        echo "  sanitized: $branch_token"
        echo "  source:    $branch_src_url"
        echo "  cache dir: $branch_cache_dir"
        exit 0
    fi

    if ! command -v git >/dev/null 2>&1; then
        echo "git is required for --branch installs but was not found on PATH." >&2
        exit 2
    fi

    echo "Installing Nexus-Hub from branch '$BRANCH_NAME' (cache: $branch_cache_dir)..."
    mkdir -p "$(dirname "$branch_cache_dir")"
    if [ -d "$branch_cache_dir/.git" ]; then
        git -C "$branch_cache_dir" fetch --depth 1 origin "$BRANCH_NAME" \
            && git -C "$branch_cache_dir" checkout -f FETCH_HEAD \
            || { echo "Failed to refresh branch cache at $branch_cache_dir" >&2; exit 2; }
    else
        rm -rf "$branch_cache_dir"
        git clone --depth 1 --branch "$BRANCH_NAME" "$branch_src_url" "$branch_cache_dir" \
            || { echo "Failed to clone branch '$BRANCH_NAME' from $branch_src_url" >&2; exit 2; }
    fi

    cached_installer="$branch_cache_dir/scripts/installer.sh"
    if [ ! -f "$cached_installer" ]; then
        echo "Cached checkout has no scripts/installer.sh at $cached_installer" >&2
        exit 2
    fi
    exec env NEXUS_HUB_BRANCH_RESOLVED=1 bash "$cached_installer" ${PASSTHRU_ARGS[@]+"${PASSTHRU_ARGS[@]}"}
fi

# Dispatch read-only subcommands BEFORE the interactive banner so they remain
# pipeable / scriptable.
if [ "$SUBCOMMAND" = "init" ] || [ -n "$PRINT_CONFIG_KEY" ] || [ "$CHECK_MODE" = "1" ]; then
    runner="$REPO_ROOT/scripts/lib/integrations/runner.py"
    if [ ! -f "$runner" ]; then
        echo "Runner not found at $runner" >&2
        exit 2
    fi
    if ! py=$(resolve_python_executable); then
        echo "Python not found on PATH; cannot run read-only subcommand." >&2
        exit 2
    fi
    if [ "$SUBCOMMAND" = "init" ]; then
        exec "$py" "$runner" init "${SUBCOMMAND_ARGS[@]}"
    elif [ -n "$PRINT_CONFIG_KEY" ]; then
        exec "$py" "$runner" print-config "$PRINT_CONFIG_KEY"
    else
        exec "$py" "$runner" check
    fi
fi

# --- Resolve no-prompt install configuration (v3.7.0 / Phase 2) ----------
# Validate --platforms into the space-delimited PLATFORMS_FILTER (empty = all).
if [ -n "$PLATFORMS_ARG" ]; then
    known_platform_keys="claude codex gemini antigravity2 gemini-cli copilot cursor opencode nexus-ai aider windsurf kimi qwen openclaw"
    PLATFORMS_FILTER=""
    IFS=',' read -ra _requested_platforms <<< "$PLATFORMS_ARG"
    for _pk in "${_requested_platforms[@]}"; do
        _pk="$(printf '%s' "$_pk" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
        [ -z "$_pk" ] && continue
        case " $known_platform_keys " in
            *" $_pk "*) PLATFORMS_FILTER="$PLATFORMS_FILTER $_pk" ;;
            *)
                echo "Unknown platform key: '$_pk'" >&2
                echo "Valid keys: $known_platform_keys" >&2
                exit 2
                ;;
        esac
    done
    PLATFORMS_FILTER="$(printf '%s' "$PLATFORMS_FILTER" | sed 's/^ *//;s/ *$//')"
    if [ -z "$PLATFORMS_FILTER" ]; then
        echo "--platforms produced an empty platform set" >&2
        exit 2
    fi
fi

# Resolve the assume-yes / overwrite decision. --yes or --force force it; a
# non-interactive stdin (piped curl|bash, CI) also implies it. In that case
# existing managed files are refreshed silently; otherwise interactive conflicts
# are collected and resolved once via resolve_conflicts().
if [ "$YES_FLAG" = 1 ] || [ "$FORCE_FLAG" = 1 ] || [ ! -t 0 ]; then
    ASSUME_YES=true
    OVERWRITE_ALL=true
else
    ASSUME_YES=false
    OVERWRITE_ALL=false
fi

print_nexus_banner
migrate_legacy_install
# Idempotent cleanup -- safe to run every install. Catches the case where the
# user already migrated ~/.devai-hub/ in an earlier run (before this cleanup
# existed) but still has devai-hub.claude-usage-monitor installed in VS Code.
remove_legacy_vscode_extensions
print_banner

# Scope is resolved from --workspace (no interactive scope/platform prompt).
# Default = global install across all platforms.
if [ -n "$WORKSPACE_PATH" ]; then
    SCOPE_LABEL="Workspace"
    # Strip pasted surrounding quotes and expand a leading tilde.
    WORKSPACE_PATH="${WORKSPACE_PATH%\"}"
    WORKSPACE_PATH="${WORKSPACE_PATH#\"}"
    WORKSPACE_PATH="${WORKSPACE_PATH/#\~/$HOME}"
    if [ ! -d "$WORKSPACE_PATH" ]; then
        echo "Workspace path not found: $WORKSPACE_PATH" >&2
        exit 2
    fi
    install_workspace "$REPO_ROOT" "$WORKSPACE_PATH"
else
    SCOPE_LABEL="Global"
    install_global "$REPO_ROOT"
fi

# Bundled report-generator templates + scripts are user-scope and always install silently.
# Interactive custom-template import moved to /research report at use time (v0.9.7).
install_templates "$REPO_ROOT"

# Install the nexus-hub CLI launcher + version marker (v3.7.0 Phase 3).
install_cli_launcher "$REPO_ROOT"

# Resolve any managed-file conflicts collected during an interactive install
# (single end-of-run prompt). No-op on the non-interactive / --yes / --force path.
resolve_conflicts

echo ""
echo -e "${GREEN}✓ Nexus-Hub v${NEXUS_HUB_VERSION} installed (${SCOPE_LABEL} scope).${RESET}"
echo ""
echo -e "${YELLOW}Restart any running AI assistant sessions (Claude Code, Cursor, Gemini CLI, Codex, Copilot, OpenCode) so they pick up the new settings, hooks, skills, and rules.${RESET}"
echo ""
