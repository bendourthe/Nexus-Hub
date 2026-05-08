#!/usr/bin/env bash
# init-mcp-ts.sh - scaffold a Node / TypeScript MCP server (official @modelcontextprotocol/sdk).
# Cross-platform sibling: init-mcp-ts.ps1 (PowerShell, same output).
# Bundled with the mcp-builder skill; invoked from SKILL.md instructions.

set -euo pipefail

log_info()  { printf '[INFO]  %s\n' "$*" >&2; }
log_warn()  { printf '[WARN]  %s\n' "$*" >&2; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

usage() {
    cat <<'EOF'
Usage: init-mcp-ts.sh <server-name>

Scaffolds a Node / TypeScript MCP server with:
  - package.json (@modelcontextprotocol/sdk + zod dependencies)
  - tsconfig.json (ESM, ES2022)
  - src/server.ts with one example server.tool() registration
  - stdio transport configured by default

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

check_node_version() {
    local node_version
    node_version=$(node -v 2>/dev/null | sed 's/^v//' || echo "")
    if [ -z "$node_version" ]; then
        log_error "Could not determine Node version."
        exit 1
    fi
    local major
    major=$(echo "$node_version" | cut -d. -f1)
    if [ "$major" -lt 20 ]; then
        log_error "Node 20+ required (found $node_version)."
        log_error "The MCP TypeScript SDK requires Node 20 or newer."
        exit 1
    fi
}

main() {
    if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
        usage
        exit 0
    fi

    local server_name="${1:-}"
    if [ -z "$server_name" ]; then
        log_error "Server name is required."
        usage
        exit 1
    fi

    if [ -e "$server_name" ]; then
        log_error "'$server_name' already exists in the current directory."
        log_error "Pick a different name or remove the existing path."
        exit 1
    fi

    require_command "node" "https://nodejs.org or your platform package manager"
    require_command "npm"  "https://nodejs.org or your platform package manager"
    check_node_version

    log_info "Scaffolding TS MCP server: $server_name"
    mkdir -p "$server_name/src"
    cd "$server_name"

    log_info "Writing package.json"
    cat > package.json <<EOF
{
  "name": "$server_name",
  "version": "0.1.0",
  "description": "MCP server scaffolded by mcp-builder",
  "type": "module",
  "main": "build/server.js",
  "bin": {
    "$server_name": "build/server.js"
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsx src/server.ts",
    "start": "node build/server.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "tsx": "^4.7.0",
    "typescript": "^5.4.0",
    "@types/node": "^20.0.0"
  },
  "engines": {
    "node": ">=20"
  }
}
EOF

    log_info "Writing tsconfig.json"
    cat > tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": false,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "build"]
}
EOF

    log_info "Writing src/server.ts with one example tool"
    cat > src/server.ts <<'TS'
/**
 * MCP server scaffolded by mcp-builder.
 *
 * Replace the example tool with your own. Apply the pushy-description rule
 * in each tool's .describe() calls (trigger phrases + SKIP clause).
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
    name: "__SERVER_NAME__",
    version: "0.1.0",
});

server.tool(
    "echo",
    {
        message: z.string().describe("Message to echo back"),
    },
    async ({ message }) => {
        const result = { message, length: message.length };
        return {
            content: [
                { type: "text", text: JSON.stringify(result) },
            ],
            structuredContent: result,
        };
    },
);

const transport = new StdioServerTransport();
await server.connect(transport);
TS
    sed -i.bak "s/__SERVER_NAME__/$server_name/" src/server.ts && rm -f src/server.ts.bak

    log_info "Writing .gitignore"
    cat > .gitignore <<'EOF'
node_modules/
build/
*.log
.DS_Store
EOF

    log_info "Installing dependencies"
    npm install --silent

    log_info "Scaffold complete."
    cat <<EOF

Next steps:
  cd $server_name
  npm run dev                                         # runs the server over stdio (tsx)
  npx @modelcontextprotocol/inspector npm run dev     # launches the MCP Inspector

To build for production:
  npm run build && npm start

Replace the echo tool with your real capability, then register the server
in each AI CLI's settings.json (see mcp-builder/SKILL.md Step 6).
EOF
}

main "$@"
