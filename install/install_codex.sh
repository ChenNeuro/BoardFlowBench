#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

# Install the agent-bridge skill
BRIDGE_SOURCE="$PROJECT_DIR/skills/agent-bridge"
BRIDGE_TARGET="$HOME/.agents/skills/agent-bridge"
mkdir -p "$BRIDGE_TARGET"
cp -R "$BRIDGE_SOURCE"/. "$BRIDGE_TARGET"/

# Install the code-health-review skill
HEALTH_SOURCE="$PROJECT_DIR/skills/code-health-review"
HEALTH_TARGET="$HOME/.agents/skills/code-health-review"
mkdir -p "$HEALTH_TARGET"
cp -R "$HEALTH_SOURCE"/. "$HEALTH_TARGET"/

# Install the core library
CORE_SOURCE="$PROJECT_DIR/repo_manager_core"
CORE_TARGET="$HOME/.agents/skills/repo-manager-core"
mkdir -p "$CORE_TARGET"
cp -R "$CORE_SOURCE"/. "$CORE_TARGET"/

echo "Repo Manager skills installed to $HOME/.agents/skills/"
echo "  - agent-bridge"
echo "  - code-health-review"
echo "  - core library: repo-manager-core"
echo ""
echo "Restart Codex if the skills do not appear."
