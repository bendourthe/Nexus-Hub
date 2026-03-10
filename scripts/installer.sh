#!/bin/bash
# DevAI-Hub Universal Installer V9 (v0.8.4) (macOS/Linux)
# Installs AI Skills Globally and to Workspaces with Safe Overwrite

set -e

# --- Window Title ---
printf '\033]0;DevAI-Hub Installer\007'

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
    
    echo -ne "${spaces}${YELLOW}└─> ${message} ${RESET}" >&2
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
        if [ -d "$destination" ]; then
            write_item "Syncing (old files not in source will be removed)..." "$GRAY"
        fi
        # Use rsync if available, otherwise cp
        if command -v rsync >/dev/null 2>&1; then
            rsync -a --delete "$source/" "$destination/"
        else
            rm -rf "$destination"/*
            cp -R "$source/"* "$destination/"
        fi
        
        if [ -n "$custom_message" ]; then
            write_item "$custom_message" "$GREEN"
        else
            write_item "✓ Installed to $destination" "$GREEN"
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
    safe_copy "$repo_root/catalog/hooks/git-guardrails.sh" "$hooks_dir/git-guardrails.sh" true "✓ $scope git guardrails hook installed at: $hooks_dir"
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
            write_item "✓ Git guardrails hook already configured in settings.json" "$GREEN"
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
                write_item "✓ $scope settings.json updated with git guardrails hook" "$GREEN"
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
        write_item "✓ $scope settings.json created with git guardrails hook" "$GREEN"
    fi
}

install_usage_display() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"  # "Global" or "Workspace"

    # Copy hook script
    local hooks_dir="$target_claude_dir/hooks"
    mkdir -p "$hooks_dir"
    safe_copy "$repo_root/catalog/hooks/usage-display.sh" "$hooks_dir/usage-display.sh" true "✓ $scope usage display hook installed at: $hooks_dir"
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
            write_item "✓ Usage display hook already configured in settings.json" "$GREEN"
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
                write_item "✓ $scope settings.json updated with usage display hook" "$GREEN"
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
    safe_folder_copy "$repo_root/catalog/skills" "$global_claude/skills" "✓ Global skills catalog installed at: $global_claude/skills"

    # Global Commands
    safe_folder_copy "$repo_root/catalog/commands" "$global_claude/commands" "✓ Global commands installed at: $global_claude/commands"

    # Git Guardrails Hook
    install_git_guardrails "$repo_root" "$global_claude" "Global"

    # Usage Display Hook
    install_usage_display "$repo_root" "$global_claude" "Global"

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
    
    # Global Custom Prompts (Codex equivalent of commands)
    safe_folder_copy "$repo_root/catalog/commands" "$global_codex_dir/prompts" "✓ Global custom prompts installed at: $global_codex_dir/prompts"

    # Global AGENTS.md (open standard instruction file for Codex, Jules, Cursor, Aider)
    render_template "$repo_root/templates/ai-instructions/base-codex.md" "$global_codex_dir/AGENTS.md" "$repo_root" ""

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
            local resp=$(read_prompt "Overwrite? [Y]es / [N]o / [A]ll")
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

        # Append language-specific snippets if available
        if [ -n "$languages" ]; then
            IFS=',' read -ra LANGS <<< "$languages"
            for lang in "${LANGS[@]}"; do
                local lang_key=$(echo "$lang" | tr '[:upper:]' '[:lower:]')
                if [ "$lang_key" == "c++" ]; then lang_key="cpp"; fi
                if [ "$lang_key" == "c#" ]; then lang_key="csharp"; fi

                local snippet="$repo_root/templates/ai-instructions/coding-snippets/${lang_key}.md"
                if [ -f "$snippet" ]; then
                    echo "" >> "$output"
                    cat "$snippet" >> "$output"
                fi
            done
        fi

        write_item "✓ Installed to $output" "$GREEN"
    fi
}

get_language_selection() {
    local detected="$1"
    
    if [ -n "$detected" ]; then
        echo -e "${YELLOW}Detected languages: $detected${RESET}" >&2
        local resp=$(read_prompt "Use these? [Y]es / [N]o")
        if [[ "$resp" =~ ^[Yy] ]]; then
            echo "$detected"
            return
        fi
    fi

    echo -e "  ${RESET}Select languages (comma separated):${RESET}" >&2
    echo -e "  ${RESET}1. Python  2. JS  3. TS  4. Java  5. C#  6. Go  7. C++${RESET}" >&2
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
        safe_folder_copy "$repo_root/catalog/skills" "$claude_dir/skills" "✓ Workspace skills catalog installed at: $claude_dir/skills"

        # Commands
        safe_folder_copy "$repo_root/catalog/commands" "$claude_dir/commands" "✓ Workspace commands installed at: $claude_dir/commands"

        # Context & Memory
        safe_folder_copy "$repo_root/catalog/context" "$claude_dir/context" "✓ Workspace context installed at: $claude_dir/context"
        safe_folder_copy "$repo_root/catalog/memory" "$claude_dir/memory" "✓ Workspace memory installed at: $claude_dir/memory"

        # Git Guardrails Hook
        install_git_guardrails "$repo_root" "$claude_dir" "Workspace"

        # Usage Display Hook
        install_usage_display "$repo_root" "$claude_dir" "Workspace"

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
        
        # Custom Prompts (Codex equivalent of commands)
        safe_folder_copy "$repo_root/catalog/commands" "$codex_dir/prompts" "✓ Workspace custom prompts installed at: $codex_dir/prompts"

        # AGENTS.md at project root (open standard for Codex, Jules, Cursor, Aider)
        render_template "$repo_root/templates/ai-instructions/base-codex.md" "$target_path/AGENTS.md" "$repo_root" "$languages"

        # --- Prepare Rules for Copilot (using concise snippets) ---
        local merged_content="# $PROJECT_NAME - Copilot Instructions\n\n"
        merged_content+="## Tech Stack\n"
        merged_content+="- **Language**: $PRIMARY_LANGUAGE\n"
        merged_content+="- **Package Manager**: $PACKAGE_MANAGER\n"
        merged_content+="- **Test**: $TEST_FRAMEWORK\n"
        merged_content+="- **Lint**: $LINT_TOOL\n\n"

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

install_vscode_extensions() {
    local repo_root="$1"

    echo ""
    echo -e "${CYAN}----------------------------------------------------------------${RESET}"
    echo -e "${CYAN}        PHASE 3: Claude Code Usage Monitor Installation          ${RESET}"
    echo -e "${CYAN}----------------------------------------------------------------${RESET}"
    echo ""

    write_item "The Claude Usage Monitor is a VS Code extension that displays your Claude" "$RESET"
    write_item "Code usage limits in the status bar and recommends when to switch models" "$RESET"
    write_item "(e.g., Opus to Sonnet) to stay within your session and weekly limits." "$RESET"
    echo ""

    local response=$(read_prompt "Install the Claude Usage Monitor VS Code extension? [Y]es / [N]o")
    if [[ ! "$response" =~ ^[Yy] ]]; then
        write_item "Skipped VS Code extension installation." "$GRAY"
        return
    fi

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
            local install_resp=$(read_prompt "Install Node.js LTS via Homebrew? [Y]es / [N]o")
            if [[ "$install_resp" =~ ^[Yy] ]]; then
                write_item "Installing Node.js LTS via Homebrew..." "$RESET"
                brew install node@22 || {
                    write_item "Homebrew install failed. Please install Node.js from https://nodejs.org" "$RED"
                    return
                }
                write_item "✓ Node.js installed successfully." "$GREEN"
            else
                write_item "Skipped. Install Node.js from https://nodejs.org and re-run." "$GRAY"
                return
            fi
        elif command -v apt-get >/dev/null 2>&1; then
            local install_resp=$(read_prompt "Install Node.js via apt? [Y]es / [N]o")
            if [[ "$install_resp" =~ ^[Yy] ]]; then
                write_item "Installing Node.js via apt..." "$RESET"
                sudo apt-get update -qq && sudo apt-get install -y -qq nodejs npm || {
                    write_item "apt install failed. Please install Node.js from https://nodejs.org" "$RED"
                    return
                }
                write_item "✓ Node.js installed successfully." "$GREEN"
            else
                write_item "Skipped. Install Node.js from https://nodejs.org and re-run." "$GRAY"
                return
            fi
        else
            write_item "Please install Node.js from https://nodejs.org and re-run the installer." "$YELLOW"
            return
        fi
    else
        local node_version=$(node --version)
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

    write_item "✓ Extension built successfully." "$GREEN"

    # Package as VSIX (uses locally installed @vscode/vsce from devDependencies)
    write_item "Packaging extension as VSIX..." "$RESET"
    npx vsce package --no-dependencies 2>/dev/null
    local vsix_file=$(ls -t "$extension_dir"/*.vsix 2>/dev/null | head -1)

    if [ -z "$vsix_file" ]; then
        write_item "VSIX packaging failed." "$RED"
        write_item "You can still use the extension in development mode (F5 in VS Code)." "$YELLOW"
        popd > /dev/null
        return
    fi

    write_item "✓ Packaged: $(basename "$vsix_file")" "$GREEN"

    popd > /dev/null

    # Install into VS Code
    if command -v code >/dev/null 2>&1; then
        if code --install-extension "$vsix_file" 2>/dev/null; then
            write_item "✓ Claude Usage Monitor extension installed in VS Code!" "$GREEN"
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
    echo -e "${GREEN}----------------------------------------------------------------${RESET}"
    echo -e "${GREEN}           VS Code Extension Phase Complete.                    ${RESET}"
    echo -e "${GREEN}----------------------------------------------------------------${RESET}"
}

# --- Template & Script Installation ---

install_templates() {
    local repo_root="$1"

    echo ""
    echo -e "${CYAN}----------------------------------------------------------------${RESET}"
    echo -e "${CYAN}     PHASE 4: Templates & Report Generator Installation         ${RESET}"
    echo -e "${CYAN}----------------------------------------------------------------${RESET}"
    echo ""
    write_item "DevAI-Hub can generate professional Word (.docx) and PowerPoint (.pptx)" "$RESET"
    write_item "reports from Markdown files using the /generate-report command." "$RESET"
    echo ""

    # Ensure global directories exist
    local devai_home="$HOME/.devai-hub"
    local templates_dest="$devai_home/templates/documentation"
    local scripts_dest="$devai_home/scripts"

    mkdir -p "$templates_dest"
    mkdir -p "$scripts_dest"

    # Copy bundled templates from repo
    local builtin_templates="$repo_root/templates/documentation"
    if [ -d "$builtin_templates" ]; then
        safe_folder_copy "$builtin_templates" "$templates_dest" "✓ Built-in templates installed at: $templates_dest"
    fi

    # Copy report generator script
    local script_source="$repo_root/scripts/generate_report.py"
    if [ -f "$script_source" ]; then
        safe_copy "$script_source" "$scripts_dest/generate_report.py" true "✓ Report generator installed at: $scripts_dest/generate_report.py"
    fi

    # Check Python availability
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        write_item "Note: Python 3 is required to generate reports." "$YELLOW"
        write_item "Install via your package manager (e.g., brew install python3, apt install python3)." "$YELLOW"
    else
        local python_cmd="python3"
        if ! command -v python3 >/dev/null 2>&1; then python_cmd="python"; fi

        if $python_cmd -c "import docx; import pptx" 2>/dev/null; then
            write_item "✓ Python dependencies (python-docx, python-pptx) are available" "$GREEN"
        else
            write_item "Note: Install report dependencies with: pip install python-docx python-pptx" "$YELLOW"
        fi
    fi

    echo ""

    # Custom template import
    local response=$(read_prompt "Import custom Word/PowerPoint templates? [Y]es / [N]o")
    if [[ ! "$response" =~ ^[Yy] ]]; then
        write_item "Skipped custom template import." "$GRAY"
        echo ""
        echo -e "${GREEN}----------------------------------------------------------------${RESET}"
        echo -e "${GREEN}        Templates & Scripts Installation Complete.               ${RESET}"
        echo -e "${GREEN}----------------------------------------------------------------${RESET}"
        return
    fi

    # Terminal-based file import loop (no native GUI dialog on Linux/macOS terminal)
    while true; do
        echo ""
        write_item "Enter the full path to a .docx or .pptx template file." "$RESET"
        write_item "You can also drag and drop a file into this terminal." "$RESET"
        local template_path=$(read_prompt "File path (or press Enter to finish)")

        # User pressed Enter without input
        if [ -z "$template_path" ]; then break; fi

        # Remove surrounding quotes (from drag-and-drop)
        template_path="${template_path%\"}"
        template_path="${template_path#\"}"
        template_path="${template_path%\'}"
        template_path="${template_path#\'}"
        # Expand tilde
        template_path="${template_path/#\~/$HOME}"
        # Trim trailing whitespace
        template_path="$(echo -e "${template_path}" | sed -e 's/[[:space:]]*$//')"

        if [ ! -f "$template_path" ]; then
            write_item "File not found: $template_path" "$RED"
            continue
        fi

        local ext="${template_path##*.}"
        ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

        if [[ "$ext" != "docx" && "$ext" != "pptx" ]]; then
            write_item "Only .docx and .pptx files are supported." "$YELLOW"
            continue
        fi

        local file_name=$(basename "$template_path")
        safe_copy "$template_path" "$templates_dest/$file_name" true "✓ Template imported: $file_name"

        local more=$(read_prompt "Import more templates? [Y]es / [N]o")
        if [[ ! "$more" =~ ^[Yy] ]]; then break; fi
    done

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
    echo -e "${GREEN}----------------------------------------------------------------${RESET}"
    echo -e "${GREEN}        Templates & Scripts Installation Complete.               ${RESET}"
    echo -e "${GREEN}----------------------------------------------------------------${RESET}"
}

# --- Main ---

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

install_global "$REPO_ROOT"
install_workspace "$REPO_ROOT"
install_vscode_extensions "$REPO_ROOT"
install_templates "$REPO_ROOT"

echo ""
echo -e "${DARK_CYAN}================================================================${RESET}"
echo -e "${DARK_CYAN}       Thank You For Using The DevAI-Hub Universal Installer    ${RESET}"
echo -e "${DARK_CYAN}================================================================${RESET}"
echo ""
