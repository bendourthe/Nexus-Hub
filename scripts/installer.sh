#!/bin/bash
# DevAI-Hub Universal Installer V5 (macOS/Linux)
# Installs AI Skills Globally and to Workspaces with Safe Overwrite

set -e

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
    local color=$(get_provider_color "$provider")
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
    
    echo -ne "${spaces}${YELLOW}└─> ${message} ${RESET}"
    read -r response
    echo "$response"
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
            local resp=$(read_prompt "Overwrite? [Y]es / [N]o / [A]ll")
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
            write_item "✓ Installed to $destination" "$GREEN"
        fi
    fi
}

safe_folder_copy() {
    local source="$1"
    local destination="$2"
    local custom_message="$3"

    if [ ! -d "$source" ]; then
        return
    fi

    local do_copy=true

    if [ -d "$destination" ]; then
        if [ "$OVERWRITE_ALL" = false ]; then
            write_item "Folder exists: $destination" "$YELLOW"
            local resp=$(read_prompt "Overwrite contents? [Y]es / [N]o / [A]ll")
            if [[ "$resp" =~ ^[Aa] ]]; then
                OVERWRITE_ALL=true
            elif [[ ! "$resp" =~ ^[Yy] ]]; then
                write_item "Skipped." "$GRAY"
                do_copy=false
            fi
        fi
    else
        mkdir -p "$destination"
    fi

    if [ "$do_copy" = true ]; then
        # Use rsync if available, otherwise cp
        if command -v rsync >/dev/null 2>&1; then
            rsync -a "$source/" "$destination/"
        else
            cp -R "$source/"* "$destination/"
        fi
        
        if [ -n "$custom_message" ]; then
            write_item "$custom_message" "$GREEN"
        else
            write_item "✓ Installed to $destination" "$GREEN"
        fi
    fi
}

# --- Install Functions ---

install_global() {
    local repo_root="$1"
    local user_home="$HOME"

    clear
    OVERWRITE_ALL=false
    echo -e "${DARK_CYAN}================================================================${RESET}"
    echo -e "${DARK_CYAN}                   DevAI-Hub Universal Installer                ${RESET}"
    echo -e "${DARK_CYAN}================================================================${RESET}"
    echo ""
    echo -e "${CYAN}----------------------------------------------------------------${RESET}"
    echo -e "${CYAN}                  PHASE 1: Global Installation                  ${RESET}"
    echo -e "${CYAN}----------------------------------------------------------------${RESET}"
    echo ""
    echo -e "${GRAY}Checking User Profile ($user_home)...${RESET}"

    # 1. Claude
    write_header "CLAUDE"
    write_item "Checking Global Configuration..."
    local global_claude="$user_home/.claude"
    mkdir -p "$global_claude"

    # Global CLAUDE.md
    safe_copy "$repo_root/catalog/CLAUDE.md" "$global_claude/CLAUDE.md" true "✓ Global instructions installed at: $global_claude/CLAUDE.md"

    # Global Skills
    safe_folder_copy "$repo_root/catalog/skills" "$global_claude/skills" "✓ Global skills catalog installed at: $global_claude/skills"

    # Global Commands
    safe_folder_copy "$repo_root/catalog/commands" "$global_claude/commands" "✓ Global commands installed at: $global_claude/commands"

    # 2. Gemini / Antigravity
    write_header "GEMINI"
    write_item "Checking Global Configuration..."
    local global_gemini_dir="$user_home/.gemini"
    local global_agent_dir="$user_home/.agent"
    
    mkdir -p "$global_gemini_dir"
    mkdir -p "$global_agent_dir"

    # Global GEMINI.md
    safe_copy "$repo_root/templates/ai-instructions/generic-instructions.md" "$global_gemini_dir/GEMINI.md" true "✓ Global instructions installed at: $global_gemini_dir/GEMINI.md"

    # Mirror Skills to Agent (Antigravity)
    safe_folder_copy "$repo_root/catalog/skills" "$global_agent_dir/skills" "✓ Global skills catalog installed at: $global_agent_dir/skills"

    # Mirror Commands to Agent Workflows
    safe_folder_copy "$repo_root/catalog/commands" "$global_agent_dir/workflows" "✓ Global workflows installed at: $global_agent_dir/workflows"

    # 3. OpenAI Codex
    write_header "CODEX"
    write_item "Checking Global Configuration (OpenAI Codex)..."
    local global_codex_dir="$user_home/.codex"
    
    mkdir -p "$global_codex_dir"
    
    # Global Skills
    safe_folder_copy "$repo_root/catalog/skills" "$global_codex_dir/skills" "✓ Global skills catalog installed at: $global_codex_dir/skills"
    
    # Global Commands
    safe_folder_copy "$repo_root/catalog/commands" "$global_codex_dir/commands" "✓ Global commands installed at: $global_codex_dir/commands"

    # 4. Microsoft - Github Copilot
    write_header "COPILOT"
    # Copilot usually doesn't have a global config file in the same way, skipped as per Windows version or add if known.
    write_item "Check skipped (No global file support standard)." "$GRAY"

    echo ""
    echo -e "${GREEN}----------------------------------------------------------------${RESET}"
    echo -e "${GREEN}              Global Installation Phase Complete.               ${RESET}"
    echo -e "${GREEN}----------------------------------------------------------------${RESET}"
    echo ""
}

detect_languages() {
    local target_path="$1"
    local detected_langs=""

    # Simple count check
    if [ $(find "$target_path" -maxdepth 3 -name "*.py" 2>/dev/null | wc -l) -gt 0 ]; then detected_langs+="Python,"; fi
    if [ $(find "$target_path" -maxdepth 3 -name "*.js" -o -name "*.jsx" 2>/dev/null | wc -l) -gt 0 ]; then detected_langs+="JavaScript,"; fi
    if [ $(find "$target_path" -maxdepth 3 -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l) -gt 0 ]; then detected_langs+="TypeScript,"; fi
    if [ $(find "$target_path" -maxdepth 3 -name "*.java" 2>/dev/null | wc -l) -gt 0 ]; then detected_langs+="Java,"; fi
    if [ $(find "$target_path" -maxdepth 3 -name "*.cs" 2>/dev/null | wc -l) -gt 0 ]; then detected_langs+="C#,"; fi
    if [ $(find "$target_path" -maxdepth 3 -name "*.go" 2>/dev/null | wc -l) -gt 0 ]; then detected_langs+="Go,"; fi
    if [ $(find "$target_path" -maxdepth 3 -name "*.cpp" -o -name "*.h" -o -name "*.hpp" 2>/dev/null | wc -l) -gt 0 ]; then detected_langs+="C++,"; fi

    # Remove trailing comma
    echo "${detected_langs%,}"
}

get_language_selection() {
    local detected="$1"
    
    if [ -n "$detected" ]; then
        echo -e "${YELLOW}Detected languages: $detected${RESET}"
        local resp=$(read_prompt "Use these? [Y]es / [N]o")
        if [[ "$resp" =~ ^[Yy] ]]; then
            echo "$detected"
            return
        fi
    fi

    write_item "Select languages (comma separated):" "$RESET"
    write_item "1. Python  2. JS  3. TS  4. Java  5. C#  6. Go  7. C++" "$RESET"
    local input_str=$(read_prompt "Selection")
    
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

    echo -e "${CYAN}----------------------------------------------------------------${RESET}"
    echo -e "${CYAN}                PHASE 2: Workspace Installation                 ${RESET}"
    echo -e "${CYAN}----------------------------------------------------------------${RESET}"

    while true; do
        echo ""
        echo -e "${RESET}Do you want to configure a specific local project/repository?"
        local response=$(read_prompt "Select Project? [Y]es / [N]o")
        if [[ ! "$response" =~ ^[Yy] ]]; then break; fi

        local target_path=$(read_prompt "Enter absolute path to project")
        # remove quotes if user pasted them
        target_path="${target_path%\"}"
        target_path="${target_path#\"}"
        
        # Expand tilde if present
        target_path="${target_path/#\~/$HOME}" 

        if [ -z "$target_path" ] || [ ! -d "$target_path" ]; then
            write_item "Invalid directory: $target_path" "$YELLOW"
            continue
        fi

        write_item "Target: $target_path" "$DARK_YELLOW"

        local detected=$(detect_languages "$target_path")
        local languages=$(get_language_selection "$detected")
        write_item "Selected: $languages" "$YELLOW"

        # --- Install Logic ---

        # 1. Claude
        write_header "CLAUDE"
        write_item "Installing Workspace Resources..."
        local claude_dir="$target_path/.claude"
        mkdir -p "$claude_dir"

        # CLAUDE.md
        safe_copy "$repo_root/catalog/CLAUDE.md" "$target_path/CLAUDE.md" true "✓ Workspace instructions installed at: $target_path/CLAUDE.md"

        # Skills
        safe_folder_copy "$repo_root/catalog/skills" "$claude_dir/skills" "✓ Workspace skills catalog installed at: $claude_dir/skills"

        # Commands
        safe_folder_copy "$repo_root/catalog/commands" "$claude_dir/commands" "✓ Workspace commands installed at: $claude_dir/commands"

        # Context & Memory
        safe_folder_copy "$repo_root/catalog/context" "$claude_dir/context" "✓ Workspace context installed at: $claude_dir/context"
        safe_folder_copy "$repo_root/catalog/memory" "$claude_dir/memory" "✓ Workspace memory installed at: $claude_dir/memory"

        # 2. Gemini / Antigravity
        write_header "GEMINI"
        write_item "Installing Workspace Resources..."
        local gemini_dir="$target_path/.gemini"
        local agent_dir="$target_path/.agent"

        mkdir -p "$gemini_dir"
        mkdir -p "$agent_dir"

        safe_copy "$repo_root/templates/ai-instructions/generic-instructions.md" "$gemini_dir/GEMINI.md" true "✓ Workspace instructions installed at: $gemini_dir/GEMINI.md"

        # Mirror Skills to Agent
        safe_folder_copy "$repo_root/catalog/skills" "$agent_dir/skills" "✓ Workspace skills catalog installed at: $agent_dir/skills"

        # Mirror Commands to Agent Workflows
        safe_folder_copy "$repo_root/catalog/commands" "$agent_dir/workflows" "✓ Workspace workflows installed at: $agent_dir/workflows"

        write_item "✓ Copied Skills & Workflows structure" "$GREEN"
        
        # 3. OpenAI Codex
        write_header "CODEX"
        write_item "Installing Workspace Resources..."
        local codex_dir="$target_path/.codex"
        
        mkdir -p "$codex_dir"
        
        # Skills
        safe_folder_copy "$repo_root/catalog/skills" "$codex_dir/skills" "✓ Workspace skills catalog installed at: $codex_dir/skills"
        
        # Commands
        safe_folder_copy "$repo_root/catalog/commands" "$codex_dir/commands" "✓ Workspace commands installed at: $codex_dir/commands"

        # --- Prepare Rules for Copilot ---
        local merged_content="# AI Coding Rules\n\n"
        
        IFS=',' read -ra LANGS <<< "$languages"
        for lang in "${LANGS[@]}"; do
            lang_key=$(echo "$lang" | tr '[:upper:]' '[:lower:]')
            if [ "$lang_key" == "c++" ]; then lang_key="cpp"; fi
            
            src="$repo_root/templates/ai-instructions/coding-instructions/${lang_key}.md"
            if [ ! -f "$src" ]; then
                # Try simple mapping fix if needed, e.g. c# -> csharp
                if [ "$lang_key" == "c#" ]; then src="$repo_root/templates/ai-instructions/coding-instructions/csharp.md"; fi
            fi

            if [ -f "$src" ]; then
                merged_content+="\n\n## Rules for $lang\n"
                merged_content+=$(cat "$src")
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
             local resp=$(read_prompt "Overwrite? [Y]es / [N]o / [A]ll")
             if [[ "$resp" =~ ^[Aa] ]]; then
                OVERWRITE_ALL=true
             elif [[ ! "$resp" =~ ^[Yy] ]]; then
                do_write=false
             fi
        fi

        if [ "$do_write" = true ]; then
            echo -e "$merged_content" > "$copilot_file"
            write_item "✓ Workspace instructions installed at: $copilot_file" "$GREEN"
        fi

        echo ""
        echo -e "${GREEN}----------------------------------------------------------------${RESET}"
        echo -e "${GREEN}      Project $(basename "$target_path") Configured!       ${RESET}"
        echo -e "${GREEN}----------------------------------------------------------------${RESET}"

    done
}

# --- Main ---

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

install_global "$REPO_ROOT"
install_workspace "$REPO_ROOT"

echo ""
echo -e "${DARK_CYAN}================================================================${RESET}"
echo -e "${DARK_CYAN}       Thank You For Using The DevAI-Hub Universal Installer    ${RESET}"
echo -e "${DARK_CYAN}================================================================${RESET}"
echo ""
