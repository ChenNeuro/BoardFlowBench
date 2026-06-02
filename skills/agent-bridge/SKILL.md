---
name: agent-bridge
description: Manage agent handoff, task boards, repository style profiles, and shared context for multi-agent coding workflows. Use this skill when continuing a task, handing work to another agent, recording progress, learning repo conventions, or preparing context for a different coding agent.
---

# Agent Bridge

This skill maintains shared repository state for coding agents.

## Workflow

1. Read `.board/tasks.yaml` if it exists.
2. Run `bridge_refresh.py --phase start` before changing code.
3. Read `.repo_manager/agent_context.md` if it exists.
4. Identify the current task, owner, status, and dependencies.
5. Learn or update repository style using the style learner.
6. Record completed work and remaining work.
7. Write a handoff JSON file when stopping or transferring work.
8. Update task status through `bridge_status.py`.
9. Run `bridge_refresh.py --phase end` before stopping.
10. Summarize what the next agent should know.

## Scripts

| Script | Purpose |
|--------|---------|
| `bridge_init_board.py` | Initialize `.board/tasks.yaml` and handoffs/reviews directories |
| `bridge_status.py` | Update task status in both taskboard views |
| `bridge_handoff.py` | Create a structured handoff JSON for agent transition |
| `bridge_learn_style.py` | Learn repository style and write `.repo_manager/repo_style_profile.json` |
| `bridge_update_context.py` | Write `.repo_manager/agent_context.md` for the next agent |
| `bridge_refresh.py` | Check taskboard, git state, and shared context at turn start or end |

## Outputs

- `.board/tasks.yaml`
- `.board/handoffs/<task_id>_<agent>.json`
- `.board/reviews/<task_id>_review.md`
- `.repo_manager/repo_style_profile.json`
- `.repo_manager/agent_context.md`

## Rules

- Never modify files outside the task's allowed paths.
- Keep dynamic state in `.board/` files, not in agent memory.
- Treat each task as one sticker on the shared blackboard.
- Use `bridge_status.py` for status changes so `PROJECT_BOARD.md` and `.board/tasks.yaml` stay synchronized.
- Stop and resolve taskboard inconsistencies instead of guessing which view is correct.
- Preserve human-written records verbatim.
- Always write a handoff record before transferring work.
- Treat the repository as the source of truth, not chat history.
