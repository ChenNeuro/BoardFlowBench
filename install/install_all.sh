#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

bash "$SCRIPT_DIR/install_claude.sh"
bash "$SCRIPT_DIR/install_codex.sh"
bash "$SCRIPT_DIR/install_opencode.sh"

echo ""
echo "All Repo Manager skills installed for Claude Code, Codex, and OpenCode."
