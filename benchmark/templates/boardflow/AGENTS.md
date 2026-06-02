# AGENTS.md

This workspace is an isolated BoardFlowBench demo run. The repository files are the source of truth.

## Required Reading Order

1. `AGENTS.md`
2. `AI_CONTRACT.md`
3. `PROJECT_BOARD.md`
4. `.board/tasks.yaml`
5. `.board/assigned_task.yaml`
6. latest relevant handoff under `.board/handoffs/`

## Rules

- Run `PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_refresh.py --phase start --agent-id <agent> --task-id <task> --repo .` before changing code when the script is available.
- Work only on the assigned benchmark task.
- Do not infer future task requirements from the backlog.
- Respect the assigned task's dependencies and allowed paths.
- Update `PROJECT_BOARD.md` and `.board/tasks.yaml` together.
- Record a JSON handoff before transferring work.
- Run `PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_refresh.py --phase end --agent-id <agent> --task-id <task> --repo .` before stopping when the script is available.
