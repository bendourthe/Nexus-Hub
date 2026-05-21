#!/bin/bash
# Nexus-Hub Universal Installer V10 (macOS/Linux)
# Installs AI Skills Globally OR to a Workspace with Safe Overwrite

set -e

# --- Version ---
# Single source of truth for the installer banner version label.
# Keep in sync with .claude-plugin/plugin.json and CHANGELOG.md.
NEXUS_HUB_VERSION="2.0.0"

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
DARK_CYAN='\033[0;36m'   # Approximate

OVERWRITE_ALL=false

# --- Formatting Helpers ---

get_provider_color() {
    case "$1" in
        "CLAUDE") echo -ne "${DARK_YELLOW}" ;;
        "GEMINI") echo -ne "${BLUE}" ;;
        "CODEX") echo -ne "${MAGENTA}" ;;
        "COPILOT") echo -ne "${GRAY}" ;;
        *) echo -ne "${RESET}" ;;
    esac
}

write_header() {
    local provider="$1"
    local color
    color=$(get_provider_color "$provider")
    echo ""
    echo -e "  [ ${color}---------- $provider ----------${RESET} ]"
}

write_item() {
    local message="$1"
    local color_code="$2" # e.g., $GREEN
    local indent="${3:-1}"

    local spaces=""
    for ((i=0; i<indent*2; i++)); do spaces+=" "; done

    if [ -z "$color_code" ]; then color_code="${RESET}"; fi
    echo -e "${spaces}${color_code}${message}${RESET}"
}

read_prompt() {
    local message="$1"
    local indent="${2:-1}"

    local spaces=""
    for ((i=0; i<indent*2; i++)); do spaces+=" "; done

    echo -ne "${spaces}${YELLOW}└─> ${message} ${RESET}" >&2
    read -r response
    echo "$response"
}

write_subsection_banner() {
    local text="$1"
    local color="${2:-$YELLOW}"
    local width=${COLUMNS:-120}
    if [ "$width" -lt 40 ]; then width=40; fi
    local text_len=$(( ${#text} + 2 ))
    local total_dashes=$(( width - text_len ))
    local left_dashes=$(( total_dashes / 2 ))
    local right_dashes=$(( total_dashes - left_dashes ))
    local left
    left=$(printf '%*s' "$left_dashes" '' | tr ' ' '-')
    local right
    right=$(printf '%*s' "$right_dashes" '' | tr ' ' '-')
    echo ""
    echo -e "${color}${left} ${text} ${right}${RESET}"
}

safe_copy() {
    local source="$1"
    local destination="$2"
    local confirm="${3:-false}"
    local custom_message="$4"

    if [ ! -f "$source" ]; then
        write_item "Skip: Source not found ($(basename "$source"))" "$GRAY"
        return
    fi

    local do_copy=true

    if [ -f "$destination" ]; then
        if [ "$confirm" = true ] && [ "$OVERWRITE_ALL" = false ]; then
            write_item "File exists: $destination" "$YELLOW"
            local resp
            resp=$(read_prompt "Overwrite? [Y]es / [N]o / [A]ll")
            if [[ "$resp" =~ ^[Aa] ]]; then
                OVERWRITE_ALL=true
            elif [[ ! "$resp" =~ ^[Yy] ]]; then
                write_item "Skipped by user." "$GRAY"
                do_copy=false
            fi
        fi
    fi

    if [ "$do_copy" = true ]; then
        mkdir -p "$(dirname "$destination")"
        cp "$source" "$destination"
        if [ -n "$custom_message" ]; then
            write_item "$custom_message" "$GREEN"
        else
            write_item "[OK] Installed to $destination" "$GREEN"
        fi
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

    local full_sync=true

    if [ -d "$destination" ]; then
        if [ "$OVERWRITE_ALL" = false ]; then
            write_item "Folder exists: $destination" "$YELLOW"
            local resp
            resp=$(read_prompt "Full sync? [Y]es (delete stale files) / [N]o (add/update only) / [A]ll")
            if [[ "$resp" =~ ^[Aa] ]]; then
                OVERWRITE_ALL=true
            elif [[ "$resp" =~ ^[Nn] ]]; then
                # Merge-only: copy new/updated files but do not remove extras
                full_sync=false
            fi
            # Any other response (including Y) proceeds with full_sync=true
        fi
    else
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

    # Idempotency: skip if effortLevel already matches the template value
    local template_effort
    template_effort=$(jq -r '.effortLevel' "$template_file" 2>/dev/null)
    if jq -e --arg v "$template_effort" '.effortLevel == $v' "$settings_file" >/dev/null 2>&1; then
        write_item "[OK] effortLevel already set to ${template_effort} in settings.json" "$GREEN"
        return
    fi

    if command -v jq >/dev/null 2>&1; then
        local merged
        merged=$(jq -s '
            .[0] as $existing | .[1] as $template |
            $existing + {effortLevel: $template.effortLevel}
        ' "$settings_file" "$template_file" 2>/dev/null)

        if [ -n "$merged" ]; then
            echo "$merged" > "$settings_file"
            write_item "[OK] $scope settings.json updated with effortLevel: ${template_effort}" "$GREEN"
        else
            write_item "Warning: Could not merge effortLevel into settings.json" "$YELLOW"
        fi
    else
        write_item "Warning: jq not found, cannot set effortLevel" "$YELLOW"
        write_item "  Manually add: \"effortLevel\": \"${template_effort}\" to $settings_file" "$YELLOW"
    fi
}

# --- Permission Installation ---

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
            local config_dir="$user_home/.codex"
            local config_file="$config_dir/config.toml"
            local template_file="$perm_dir/codex-permissions.toml"

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Codex permissions template not found" "$GRAY"
                return
            fi

            if [ -f "$config_file" ]; then
                if grep -q 'permissions.default.network' "$config_file" 2>/dev/null && grep -q 'allowed_domains' "$config_file" 2>/dev/null; then
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

    OVERWRITE_ALL=false
    echo ""
    echo -e "${CYAN}------------------------------------------------------------------------------------------------------------------------${RESET}"
    echo -e "${CYAN}                                                  Global Installation${RESET}"
    echo -e "${CYAN}------------------------------------------------------------------------------------------------------------------------${RESET}"
    echo ""

    write_subsection_banner "Skills & Commands"

    echo -e "${GRAY}Checking User Profile ($user_home)...${RESET}"

    # 1. Claude
    write_header "CLAUDE"
    write_item "Checking Global Configuration..."
    local global_claude="$user_home/.claude"
    mkdir -p "$global_claude"

    # Global CLAUDE.md (new concise template with WHAT/WHY/HOW structure)
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
    NON_OBVIOUS_TOOLING="- (configure per project with /setup-project)"
    render_template "$repo_root/templates/ai-instructions/base-claude.md" "$global_claude/CLAUDE.md" "$repo_root" ""

    # Global Skills
    safe_folder_copy "$repo_root/catalog/skills" "$global_claude/skills" "[OK] Global skills catalog installed at: $global_claude/skills"

    # Global Commands
    safe_folder_copy "$repo_root/catalog/commands" "$global_claude/commands" "[OK] Global commands installed at: $global_claude/commands"

    # Global Agents
    safe_folder_copy "$repo_root/catalog/agents" "$global_claude/agents" "[OK] Global agents installed at: $global_claude/agents"

    # Global Rules
    safe_folder_copy "$repo_root/catalog/rules" "$global_claude/rules" "[OK] Global rules installed at: $global_claude/rules"

    # Global MCP Server Config
    mkdir -p "$global_claude/mcp-configs"
    safe_copy "$repo_root/catalog/mcp-configs/mcp-servers.json" "$global_claude/mcp-configs/mcp-servers.json" false "[OK] MCP server config installed at: $global_claude/mcp-configs"

    # Git Guardrails Hook
    install_git_guardrails "$repo_root" "$global_claude" "Global"

    # Usage Display Hook
    install_usage_display "$repo_root" "$global_claude" "Global"

    # Require Description Hook
    install_require_description "$repo_root" "$global_claude" "Global"

    # Core Settings (effortLevel)
    install_core_settings "$repo_root" "$global_claude" "Global"

    # 2. Gemini / Antigravity
    write_header "GEMINI"
    write_item "Checking Global Configuration..."
    local global_gemini_dir="$user_home/.gemini"
    local global_agent_dir="$user_home/.agent"

    mkdir -p "$global_gemini_dir"
    mkdir -p "$global_agent_dir"

    # Global GEMINI.md (concise template without Claude-specific concepts)
    render_template "$repo_root/templates/ai-instructions/base-gemini.md" "$global_gemini_dir/GEMINI.md" "$repo_root" ""

    # Mirror Skills to Agent (Antigravity)
    safe_folder_copy "$repo_root/catalog/skills" "$global_agent_dir/skills" "[OK] Global skills catalog installed at: $global_agent_dir/skills"

    # Mirror Commands to Agent Workflows
    safe_folder_copy "$repo_root/catalog/commands" "$global_agent_dir/workflows" "[OK] Global workflows installed at: $global_agent_dir/workflows"

    # 3. OpenAI Codex
    write_header "CODEX"
    write_item "Checking Global Configuration (OpenAI Codex)..."
    local global_codex_dir="$user_home/.codex"

    mkdir -p "$global_codex_dir"

    # Global Skills
    safe_folder_copy "$repo_root/catalog/skills" "$global_codex_dir/skills" "[OK] Global skills catalog installed at: $global_codex_dir/skills"

    # Global Custom Prompts (Codex equivalent of commands)
    safe_folder_copy "$repo_root/catalog/commands" "$global_codex_dir/prompts" "[OK] Global custom prompts installed at: $global_codex_dir/prompts"

    # Global AGENTS.md (open standard instruction file for Codex, Jules, Cursor, Aider)
    render_template "$repo_root/templates/ai-instructions/base-codex.md" "$global_codex_dir/AGENTS.md" "$repo_root" ""

    # 4. Microsoft - Github Copilot
    write_header "COPILOT"
    # Copilot usually doesn't have a global config file in the same way, skipped as per Windows version or add if known.
    write_item "Check skipped (No global file support standard)." "$GRAY"

    # --- Auto-Approve Permissions sub-section ---
    write_subsection_banner "Auto-Approve Permissions"

    write_header "CLAUDE"
    install_permissions "$repo_root" "CLAUDE" "Global"

    write_header "GEMINI"
    install_permissions "$repo_root" "GEMINI" "Global"

    write_header "CODEX"
    install_permissions "$repo_root" "CODEX" "Global"

    write_header "COPILOT"
    install_permissions "$repo_root" "COPILOT" "Global"

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

render_template() {
    local template="$1"
    local output="$2"
    local repo_root="$3"
    local languages="$4"
    local confirm="${5:-true}"

    if [ ! -f "$template" ]; then
        write_item "Skip: Template not found ($(basename "$template"))" "$GRAY"
        return
    fi

    # Check for existing file (reuse safe_copy overwrite logic)
    local do_write=true
    if [ -f "$output" ]; then
        if [ "$confirm" = true ] && [ "$OVERWRITE_ALL" = false ]; then
            write_item "File exists: $output" "$YELLOW"
            local resp
            resp=$(read_prompt "Overwrite? [Y]es / [N]o / [A]ll")
            if [[ "$resp" =~ ^[Aa] ]]; then
                OVERWRITE_ALL=true
            elif [[ ! "$resp" =~ ^[Yy] ]]; then
                write_item "Skipped by user." "$GRAY"
                do_write=false
            fi
        fi
    fi

    if [ "$do_write" = true ]; then
        mkdir -p "$(dirname "$output")"

        # Replace placeholders with detected values
        sed \
            -e "s|{{PROJECT_NAME}}|$PROJECT_NAME|g" \
            -e "s|{{PROJECT_DESCRIPTION}}|(Add a 2-3 sentence project description here, or run /setup-project)|g" \
            -e "s|{{PRIMARY_LANGUAGE}}|$PRIMARY_LANGUAGE|g" \
            -e "s|{{LANGUAGE_VERSION}}||g" \
            -e "s|{{PACKAGE_MANAGER}}|$PACKAGE_MANAGER|g" \
            -e "s|{{BUILD_TOOL}}|$BUILD_TOOL|g" \
            -e "s|{{TEST_FRAMEWORK}}|$TEST_FRAMEWORK|g" \
            -e "s|{{LINT_TOOL}}|$LINT_TOOL|g" \
            -e "s|{{PROJECT_STRUCTURE_BRIEF}}|(Run /setup-project to generate project layout)|g" \
            -e "s|{{BUILD_CMD}}|$BUILD_CMD|g" \
            -e "s|{{TEST_CMD}}|$TEST_CMD|g" \
            -e "s|{{LINT_CMD}}|$LINT_CMD|g" \
            -e "s|{{NON_OBVIOUS_TOOLING}}|$NON_OBVIOUS_TOOLING|g" \
            -e "s|{{LANGUAGE_CONVENTIONS}}|(See coding-snippets or run /setup-project)|g" \
            -e "s|{{OS_CONTEXT}}|$OS_CONTEXT|g" \
            "$template" > "$output"

        # Replace {{SKILL_INDEX}} with actual skill index content (multi-line, can't use sed)
        local skill_index_file="$repo_root/data/SKILL_INDEX.md"
        if [ -f "$skill_index_file" ] && grep -q '{{SKILL_INDEX}}' "$output" 2>/dev/null; then
            python3 -c "
import sys
with open(sys.argv[1], 'r') as f:
    content = f.read()
with open(sys.argv[2], 'r') as f:
    index = f.read()
content = content.replace('{{SKILL_INDEX}}', index)
with open(sys.argv[1], 'w') as f:
    f.write(content)
" "$output" "$skill_index_file" 2>/dev/null || true
        fi

        # Append language-specific snippets if available
        if [ -n "$languages" ]; then
            IFS=',' read -ra LANGS <<< "$languages"
            for lang in "${LANGS[@]}"; do
                local lang_key
                lang_key=$(echo "$lang" | tr '[:upper:]' '[:lower:]')
                if [ "$lang_key" == "c++" ]; then lang_key="cpp"; fi
                if [ "$lang_key" == "c#" ]; then lang_key="csharp"; fi

                local snippet="$repo_root/templates/ai-instructions/coding-snippets/${lang_key}.md"
                if [ -f "$snippet" ]; then
                    echo "" >> "$output"
                    cat "$snippet" >> "$output"
                fi
            done
        fi

        write_item "[OK] Installed to $output" "$GREEN"
    fi
}

get_language_selection() {
    local detected="$1"

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
    echo -e "${CYAN}------------------------------------------------------------------------------------------------------------------------${RESET}"
    echo -e "${CYAN}                                                  Workspace Installation${RESET}"
    echo -e "${CYAN}------------------------------------------------------------------------------------------------------------------------${RESET}"
    echo ""

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

        # --- Install Logic ---

        # 1. Claude
        write_header "CLAUDE"
        write_item "Installing Workspace Resources..."
        local claude_dir="$target_path/.claude"
        mkdir -p "$claude_dir"

        # CLAUDE.md (rendered from template with detected project metadata)
        render_template "$repo_root/templates/ai-instructions/base-claude.md" "$target_path/CLAUDE.md" "$repo_root" "$languages"

        # Skills
        safe_folder_copy "$repo_root/catalog/skills" "$claude_dir/skills" "[OK] Workspace skills catalog installed at: $claude_dir/skills"

        # Commands
        safe_folder_copy "$repo_root/catalog/commands" "$claude_dir/commands" "[OK] Workspace commands installed at: $claude_dir/commands"

        # Agents
        safe_folder_copy "$repo_root/catalog/agents" "$claude_dir/agents" "[OK] Workspace agents installed at: $claude_dir/agents"

        # Rules
        safe_folder_copy "$repo_root/catalog/rules" "$claude_dir/rules" "[OK] Workspace rules installed at: $claude_dir/rules"

        # MCP Server Config
        mkdir -p "$claude_dir/mcp-configs"
        safe_copy "$repo_root/catalog/mcp-configs/mcp-servers.json" "$claude_dir/mcp-configs/mcp-servers.json" false "[OK] MCP server config installed at: $claude_dir/mcp-configs"

        # Context & Memory
        safe_folder_copy "$repo_root/catalog/context" "$claude_dir/context" "[OK] Workspace context installed at: $claude_dir/context"
        safe_folder_copy "$repo_root/catalog/memory" "$claude_dir/memory" "[OK] Workspace memory installed at: $claude_dir/memory"

        # Git Guardrails Hook
        install_git_guardrails "$repo_root" "$claude_dir" "Workspace"

        # Usage Display Hook
        install_usage_display "$repo_root" "$claude_dir" "Workspace"

        # Require Description Hook
        install_require_description "$repo_root" "$claude_dir" "Workspace"

        # 2. Gemini / Antigravity
        write_header "GEMINI"
        write_item "Installing Workspace Resources..."
        local gemini_dir="$target_path/.gemini"
        local agent_dir="$target_path/.agent"

        mkdir -p "$gemini_dir"
        mkdir -p "$agent_dir"

        # GEMINI.md (rendered from template without Claude-specific concepts)
        render_template "$repo_root/templates/ai-instructions/base-gemini.md" "$gemini_dir/GEMINI.md" "$repo_root" "$languages"

        # Mirror Skills to Agent
        safe_folder_copy "$repo_root/catalog/skills" "$agent_dir/skills" "[OK] Workspace skills catalog installed at: $agent_dir/skills"

        # Mirror Commands to Agent Workflows
        safe_folder_copy "$repo_root/catalog/commands" "$agent_dir/workflows" "[OK] Workspace workflows installed at: $agent_dir/workflows"

        write_item "[OK] Copied Skills & Workflows structure" "$GREEN"

        # 3. OpenAI Codex
        write_header "CODEX"
        write_item "Installing Workspace Resources..."
        local codex_dir="$target_path/.codex"

        mkdir -p "$codex_dir"

        # Skills
        safe_folder_copy "$repo_root/catalog/skills" "$codex_dir/skills" "[OK] Workspace skills catalog installed at: $codex_dir/skills"

        # Custom Prompts (Codex equivalent of commands)
        safe_folder_copy "$repo_root/catalog/commands" "$codex_dir/prompts" "[OK] Workspace custom prompts installed at: $codex_dir/prompts"

        # AGENTS.md at project root (open standard for Codex, Jules, Cursor, Aider)
        render_template "$repo_root/templates/ai-instructions/base-codex.md" "$target_path/AGENTS.md" "$repo_root" "$languages"

        # --- Prepare Rules for Copilot (using concise snippets) ---
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

            # Use concise snippets instead of full language templates
            src="$repo_root/templates/ai-instructions/coding-snippets/${lang_key}.md"
            if [ -f "$src" ]; then
                merged_content+="\n"
                merged_content+=$(cat "$src")
                merged_content+="\n"
            fi
        done

        # 4. Microsoft - Github Copilot
        write_header "COPILOT"
        write_item "Installing Workspace Instructions..."
        local copilot_dir="$target_path/.github"
        mkdir -p "$copilot_dir"
        local copilot_file="$copilot_dir/copilot-instructions.md"

        local do_write=true
        if [ -f "$copilot_file" ] && [ "$OVERWRITE_ALL" = false ]; then
             write_item "File exists: copilot-instructions.md" "$YELLOW"
             local resp
             resp=$(read_prompt "Overwrite? [Y]es / [N]o / [A]ll")
             if [[ "$resp" =~ ^[Aa] ]]; then
                OVERWRITE_ALL=true
             elif [[ ! "$resp" =~ ^[Yy] ]]; then
                do_write=false
             fi
        fi

        if [ "$do_write" = true ]; then
            echo -e "$merged_content" > "$copilot_file"
            write_item "[OK] Workspace instructions installed at: $copilot_file" "$GREEN"
        fi
        echo ""
}

install_vscode_extensions() {
    local repo_root="$1"

    echo ""
    echo -e "[ ${DARK_YELLOW}---------- CLAUDE USAGE MONITOR ----------${RESET} ]"
    echo ""

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
            local install_resp
            install_resp=$(read_prompt "Install Node.js LTS via Homebrew? [Y]es / [N]o")
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
            install_resp=$(read_prompt "Install Node.js via apt? [Y]es / [N]o")
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

    write_item "  Installing dependencies..." "$GRAY"
    if ! npm install --silent 2>/dev/null; then
        write_item "npm install failed." "$RED"
        popd > /dev/null
        return
    fi

    write_item "  Compiling TypeScript..." "$GRAY"
    if ! npm run compile 2>/dev/null; then
        write_item "TypeScript compilation failed." "$RED"
        popd > /dev/null
        return
    fi

    write_item "[OK] Extension built successfully." "$GREEN"

    # Package as VSIX (uses locally installed @vscode/vsce from devDependencies)
    write_item "Packaging extension as VSIX..." "$RESET"
    npx vsce package --no-dependencies 2>/dev/null
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

    # Install into VS Code
    if command -v code >/dev/null 2>&1; then
        # Uninstall any existing version first so VS Code does not skip the reinstall
        code --uninstall-extension "nexus-hub.claude-usage-monitor" 2>/dev/null || true
        # --force ensures reinstall even when the version number has not changed
        if code --install-extension "$vsix_file" --force 2>/dev/null; then
            write_item "[OK] Claude Usage Monitor extension installed in VS Code!" "$GREEN"
            write_item "  Restart VS Code to activate. Look for 'Claude: --%' in the status bar." "$RESET"
        else
            write_item "VS Code install failed. Install manually:" "$YELLOW"
            write_item "  code --install-extension \"$vsix_file\"" "$RESET"
        fi
    else
        write_item "VS Code CLI ('code') not found in PATH." "$YELLOW"
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
    write_item "reports from Markdown files using the /generate-report command." "$RESET"
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

    # Copy feature-directory bootstrap scripts (v2.1.0 / adoption-spec-kit
    # Phase 7 / G5). The two scripts resolve the next specs/<NNN>-<slug>/
    # prefix (sequential or timestamp per .specify/init-options.json),
    # create the directory, and persist .specify/feature.json so downstream
    # commands (/clarify-spec, /analyze-spec, /tasks-to-issues) can locate
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

    # Copy style-guides (v1.0.0+). Reference content for /compile-deep-research
    # and /generate-report; deliberately not in catalog/commands/ so the files
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
    # /install-pre-commit-review-hook slash command from inside the target
    # repo, which copies the chosen platform's script to .git/hooks/pre-commit.
    local nexus_hooks_dest="$nexus_home/hooks"
    mkdir -p "$nexus_hooks_dest"
    for diff_review_variant in claude-diff-review.sh gemini-diff-review.sh codex-diff-review.sh opencode-diff-review.sh; do
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
    # `/generate-report` command (generic vs custom path gate). Bundled generic templates
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

    # Check Python >= 3.10
    local python_cmd=""
    for cmd in python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            local ver
            ver=$("$cmd" --version 2>&1 | grep -oP 'Python\s+3\.(\d+)' | grep -oP '\d+$')
            if [ -n "$ver" ] && [ "$ver" -ge 10 ]; then
                python_cmd="$cmd"
                break
            fi
        fi
    done

    if [ -z "$python_cmd" ]; then
        write_item "  Python 3.10+ not found. MCP server requires Python 3.10 or newer." "$YELLOW"
        write_item "  Install Python and re-run the installer." "$YELLOW"
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
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
" "$claude_settings" "$venv_path" "$nexus_home"

    write_item "  MCP servers registered in $claude_settings (nexus-skill-server, nexus-code-search, nexus-web-fetch)" "$GREEN"
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
 _   _ _____  __  __ _   _ ____       _   _ _   _ ____
| \ | | ____| \ \/ /| | | / ___|     | | | | | | | __ )
|  \| |  _|    \  / | | | \___ \  -  | |_| | | | |  _ \
| |\  | |___   /  \ | |_| |___) |    |  _  | |_| | |_) |
|_| \_|_____| /_/\_\ \___/|____/     |_| |_|\___/|____/
NEXUS_BANNER_EOF
    echo -e "${RESET}"
    echo "  The Skill Harness for Claude Code, Codex, Gemini, Copilot, Cursor, and Nexus"
    echo "  v${NEXUS_HUB_VERSION}  |  https://github.com/bendourthe/Nexus-Hub"
    echo ""
}

# Detects an existing ~/.devai-hub/ install and migrates it to ~/.nexus-hub/.
# One-shot, one-way per the backward-compat decision in
# docs/v2.0.0/rename-decisions.md. The installer does NOT ship a symlink or
# compatibility shim. Three branches:
#   1. legacy only            -> prompt to migrate (default Y), then `mv`.
#   2. legacy AND new co-exist -> ask user: keep-new, abort, or merge.
#   3. neither / new only      -> no-op (fresh or already-migrated install).
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
    echo ""
    echo -e "${DARK_CYAN}========================================================================================================================${RESET}"
    echo -e "${DARK_CYAN}                                      Welcome to the Nexus-Hub Universal Installer${RESET}"
    echo -e "${DARK_CYAN}                                                     (version ${NEXUS_HUB_VERSION})${RESET}"
    echo -e "${DARK_CYAN}========================================================================================================================${RESET}"
    echo ""
}

# --- Main ---

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

print_nexus_banner
migrate_legacy_install
print_banner

# Ask whether to install globally (recommended, user-scope) or to a specific workspace.
echo -e "${RESET}Where would you like to install Nexus-Hub?"
echo -e "  ${GREEN}[G]${RESET} Global (recommended) - applies to all projects on this machine (~/.claude/, ~/.gemini/, ~/.codex/, ~/.nexus-hub/)"
echo -e "  ${YELLOW}[W]${RESET} Workspace            - scoped to a specific project directory"
echo ""
SCOPE_CHOICE=$(read_prompt "Select [G/W]")

SCOPE_LABEL="Global"
case "$SCOPE_CHOICE" in
    [Ww]*)
        SCOPE_LABEL="Workspace"
        # Workspace install: prompt for project path, then run the workspace phase once.
        while true; do
            TARGET_PATH=$(read_prompt "Enter absolute path to project")
            # Remove surrounding quotes if user pasted them
            TARGET_PATH="${TARGET_PATH%\"}"
            TARGET_PATH="${TARGET_PATH#\"}"
            # Expand tilde if present
            TARGET_PATH="${TARGET_PATH/#\~/$HOME}"
            if [ -n "$TARGET_PATH" ] && [ -d "$TARGET_PATH" ]; then
                break
            fi
            write_item "Invalid directory: $TARGET_PATH" "$YELLOW"
        done
        install_workspace "$REPO_ROOT" "$TARGET_PATH"
        ;;
    *)
        # Default + explicit [Gg] both route here.
        install_global "$REPO_ROOT"
        ;;
esac

# Bundled report-generator templates + scripts are user-scope and always install silently.
# Interactive custom-template import moved to /generate-report at use time (v0.9.7).
install_templates "$REPO_ROOT"

echo ""
echo -e "${GREEN}------------------------------------------------------------------------------------------------------------------------${RESET}"
echo -e "${GREEN}                                             ${SCOPE_LABEL} Installation Complete.${RESET}"
echo -e "${GREEN}------------------------------------------------------------------------------------------------------------------------${RESET}"

echo ""
echo -e "${YELLOW}IMPORTANT: Restart any running Claude Code, Cursor, Gemini CLI, Codex, or Copilot sessions.${RESET}"
echo -e "${YELLOW}  Settings files (settings.json, AGENTS.md, .cursor/rules/) are read at session start and not hot-reloaded.${RESET}"
echo -e "${YELLOW}  New hooks, commands, skills, and permission entries will not take effect in already-running sessions until they restart.${RESET}"

echo ""
echo -e "${DARK_CYAN}========================================================================================================================${RESET}"
echo -e "${DARK_CYAN}                              Thank You For Using The Nexus-Hub Universal Installer${RESET}"
echo -e "${DARK_CYAN}                                                     (version ${NEXUS_HUB_VERSION})${RESET}"
echo -e "${DARK_CYAN}========================================================================================================================${RESET}"
echo ""
