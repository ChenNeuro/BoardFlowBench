---
name: agent-bridge
description: Manage agent handoff, task boards, repository style profiles, and shared context for multi-agent coding workflows in this repository. Use this skill when continuing a task, handing work to another agent, recording progress, learning repo conventions, or preparing context for a different coding agent.
---

# Agent Bridge

This is the Claude Code project-level entry point for the repository's Agent Bridge skill.

The canonical implementation lives in:

- `skills/agent-bridge/SKILL.md`
- `skills/agent-bridge/scripts/`
- `repo_manager_core/board/`
- `repo_manager_core/style/`

## Workflow

1. Read `.board/tasks.yaml` if it exists.
2. Read `.repo_manager/agent_context.md` if it exists.
3. Identify the current task, owner, status, and dependencies.
4. Learn or update repository style when needed.
5. Record completed work and remaining work.
6. Write a handoff JSON file before stopping or transferring work.
7. Update `.board/tasks.yaml`.
8. Summarize what the next agent should know.

## Commands

Run these commands from the repository root:

```bash
python skills/agent-bridge/scripts/bridge_init_board.py
python skills/agent-bridge/scripts/bridge_status.py T001 IN_PROGRESS --owner agent-c
python skills/agent-bridge/scripts/bridge_handoff.py T001 agent-c first_worker --files src/parser.py
python skills/agent-bridge/scripts/bridge_learn_style.py .
python skills/agent-bridge/scripts/bridge_update_context.py --agent-id agent-c --task-id T001
```

## Outputs

- `.board/tasks.yaml`
- `.board/handoffs/<task_id>_<agent>.json`
- `.board/reviews/<task_id>_review.md`
- `.repo_manager/repo_style_profile.json`
- `.repo_manager/agent_context.md`

## Rules

- Never modify files outside the task's allowed paths.
- Keep dynamic state in `.board/` files, not in agent memory.
- Always write a handoff record before transferring work.
- Treat the repository as the source of truth, not chat history.
