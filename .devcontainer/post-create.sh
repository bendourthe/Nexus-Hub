#!/usr/bin/env bash
set -euo pipefail

# Nexus-Hub devcontainer post-create hook.
# Installs the AI CLIs that the catalog targets, idempotently. Existing installs are skipped.

log_info()  { printf '[post-create] %s\n' "$*" >&2; }
log_warn()  { printf '[post-create] WARN: %s\n' "$*" >&2; }

require_cmd() {
    if command -v "$1" >/dev/null 2>&1; then
        log_info "$1 already present at $(command -v "$1") -- skipping install."
        return 0
    fi
    return 1
}

install_claude_code() {
    if require_cmd claude; then return 0; fi
    log_info "Installing Claude Code CLI via npm..."
    if command -v npm >/dev/null 2>&1; then
        npm install -g @anthropic-ai/claude-code || log_warn "npm install @anthropic-ai/claude-code failed; install manually later."
    else
        log_warn "npm is not available; skipping claude install. Re-run after Node is on PATH."
    fi
}

install_gh() {
    if require_cmd gh; then return 0; fi
    log_info "Installing GitHub CLI (gh)..."
    # The devcontainer feature ghcr.io/devcontainers/features/github-cli already installs gh.
    # This branch is a safety net for images that ship without the feature.
    if command -v apt-get >/dev/null 2>&1; then
        (curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
            | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
            && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
            && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
                | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null \
            && sudo apt-get update -qq \
            && sudo apt-get install -y gh) || log_warn "gh install failed; install manually later."
    else
        log_warn "Non-apt distro detected; install gh manually."
    fi
}

install_python_tooling() {
    log_info "Installing Python tooling (pytest, ruff)..."
    pip install --quiet --upgrade pip
    pip install --quiet pytest ruff || log_warn "Python tooling install partially failed; re-run pip install pytest ruff manually."
}

main() {
    log_info "Starting Nexus-Hub devcontainer post-create setup."
    install_python_tooling
    install_gh
    install_claude_code
    log_info "Post-create setup complete."
    log_info ""
    log_info "Next steps:"
    log_info "  1. Authenticate gh:     gh auth login"
    log_info "  2. Authenticate claude: claude login"
    log_info "  3. Run installer:       bash scripts/installer.sh"
    log_info "  4. Validate catalog:    make validate"
}

main "$@"
