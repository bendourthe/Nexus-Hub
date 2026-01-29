#!/bin/bash
# Entry point for macOS and Linux installation
# Delegates to the core script in ./scripts/installer.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
INSTALLER_SCRIPT="$SCRIPT_DIR/scripts/installer.sh"

if [ ! -f "$INSTALLER_SCRIPT" ]; then
    echo "Error: Installer script not found at $INSTALLER_SCRIPT"
    exit 1
fi

chmod +x "$INSTALLER_SCRIPT"
exec "$INSTALLER_SCRIPT" "$@"
