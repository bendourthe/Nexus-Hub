#!/usr/bin/env bash
# init-artifact.sh - scaffold a Vite + React + TypeScript + Tailwind v4 + shadcn/ui web artifact.
# Cross-platform sibling: init-artifact.ps1 (PowerShell, same output).
# Bundled with the web-artifacts-builder skill; invoked from SKILL.md instructions.

set -euo pipefail

log_info()  { printf '[INFO]  %s\n' "$*" >&2; }
log_warn()  { printf '[WARN]  %s\n' "$*" >&2; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

usage() {
    cat <<'EOF'
Usage: init-artifact.sh <project-name>

Scaffolds a multi-component HTML artifact using:
  - Vite (build tool)
  - React 18+ with TypeScript (strict)
  - Tailwind CSS v4 (via @tailwindcss/vite plugin)
  - shadcn/ui (initialized with the New York style + Slate base)

Requires: node (>= 20), npm (>= 10).
EOF
}

require_command() {
    local cmd="$1"
    local hint="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        log_error "$cmd not detected on PATH."
        log_error "Install via $hint and re-run this script."
        exit 1
    fi
}

main() {
    if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
        usage
        exit 0
    fi

    local project_name="${1:-}"
    if [ -z "$project_name" ]; then
        log_error "Project name is required."
        usage
        exit 1
    fi

    if [ -e "$project_name" ]; then
        log_error "'$project_name' already exists in the current directory."
        log_error "Pick a different name or remove the existing path."
        exit 1
    fi

    require_command "node" "https://nodejs.org or your platform package manager"
    require_command "npm"  "https://nodejs.org or your platform package manager"

    log_info "Scaffolding Vite + React + TypeScript project: $project_name"
    npm create vite@latest "$project_name" -- --template react-ts

    log_info "Entering project directory: $project_name"
    cd "$project_name"

    log_info "Installing base dependencies"
    npm install

    log_info "Installing Tailwind CSS v4 via @tailwindcss/vite plugin"
    npm install -D tailwindcss @tailwindcss/vite

    log_info "Wiring Tailwind into vite.config.ts"
    cat > vite.config.ts <<'TS'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
TS

    log_info "Replacing src/App.css with Tailwind import"
    cat > src/App.css <<'CSS'
@import "tailwindcss";

@theme {
  /* Wire theme-tokens here:
   * --color-primary, --color-secondary, --color-accent,
   * --color-background, --color-foreground, --color-muted,
   * --font-heading, --font-body, --font-mono,
   * --radius, --shadow.
   */
}
CSS

    log_info "Initializing shadcn/ui (New York style, Slate base)"
    if ! npx --yes shadcn@latest init --defaults --silent 2>/dev/null; then
        log_warn "shadcn init produced output or prompts; review the project root and re-run interactively if needed."
    fi

    log_info "Trimming default Vite demo content"
    cat > src/App.tsx <<'TSX'
function App() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <h1 className="text-3xl font-semibold">Hello, web artifact.</h1>
    </main>
  );
}

export default App;
TSX

    log_info "Scaffold complete."
    cat <<EOF

Next steps:
  cd $project_name
  npm run dev

Add shadcn components on demand:
  npx shadcn@latest add button card dialog input

Tailwind theme tokens go in: src/App.css inside the @theme { ... } block.
EOF
}

main "$@"
