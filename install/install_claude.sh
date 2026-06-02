#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

# Install the agent-bridge skill
BRIDGE_SOURCE="$PROJECT_DIR/skills/agent-bridge"
BRIDGE_TARGET="$HOME/.claude/skills/agent-bridge"
mkdir -p "$BRIDGE_TARGET"
cp -R "$BRIDGE_SOURCE"/. "$BRIDGE_TARGET"/

# Install the code-health-review skill
HEALTH_SOURCE="$PROJECT_DIR/skills/code-health-review"
HEALTH_TARGET="$HOME/.claude/skills/code-health-review"
mkdir -p "$HEALTH_TARGET"
cp -R "$HEALTH_SOURCE"/. "$HEALTH_TARGET"/

# Install the boardflow-reviewer skill
REVIEWER_SOURCE="$PROJECT_DIR/skills/boardflow-reviewer"
REVIEWER_TARGET="$HOME/.claude/skills/boardflow-reviewer"
mkdir -p "$REVIEWER_TARGET"
cp -R "$REVIEWER_SOURCE"/. "$REVIEWER_TARGET"/

# Install the core library
CORE_SOURCE="$PROJECT_DIR/repo_manager_core"
CORE_TARGET="$HOME/.claude/skills/repo_manager_core"
mkdir -p "$CORE_TARGET"
cp -R "$CORE_SOURCE"/. "$CORE_TARGET"/

echo "Repo Manager skills installed to $HOME/.claude/skills/"
echo "  - agent-bridge"
echo "  - code-health-review"
echo "  - boardflow-reviewer"
echo "  - core library: repo_manager_core"
echo ""
echo "Restart Claude Code if the skills do not appear."
