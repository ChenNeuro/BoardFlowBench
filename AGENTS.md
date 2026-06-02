# AGENTS.md

This is the entry point for coding agents working in BoardFlowBench.

This repository develops the BoardFlowBench protocol, skills, scorer, and experiment tooling. Expense Lite is a separate benchmark target repository. Do not add demo implementation work to this project board.

## Required Reading Order

1. `AGENTS.md`
2. `AI_CONTRACT.md`
3. `PROJECT_BOARD.md`
4. `.board/tasks.yaml`
5. assigned project task YAML under `project/tasks/`
6. latest relevant handoff under `.board/handoffs/`

If a handoff is missing, continue from the board and task YAML, then record the missing handoff as a risk.

## How To Find Current Work

- Run `PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_refresh.py --phase start --agent-id <agent> --task-id <task> --repo .` before beginning a coding turn.
- Current milestone: read `PROJECT_BOARD.md`, then confirm the same milestone in `.board/tasks.yaml`.
- Assigned task: use the task id given by the user or scenario. If none is given, do not choose one silently.
- Dependencies: read the task's `dependencies` in `.board/tasks.yaml`.
- Task specification: read the assigned project task YAML under `project/tasks/`.
- Acceptance commands: read the task's `acceptance_commands` in `.board/tasks.yaml`.

## Updating Progress

- Set the assigned task to `IN_PROGRESS` when beginning real task work.
- Use only these task statuses: `TODO`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_REVIEW`, `DONE`.
- Update both `PROJECT_BOARD.md` and `.board/tasks.yaml` when task state changes.
- Do not put dynamic task state in `AI_CONTRACT.md`.
- Do not add demo benchmark stickers to this project board.
- Initialize demo experiments with `scripts/init_benchmark_workspace.py`; work inside the generated standalone workspace.

## Handoff Expectations

Before ending a coding turn, run `PYTHONPATH=. python3 skills/agent-bridge/scripts/bridge_refresh.py --phase end --agent-id <agent> --task-id <task> --repo .`.

Before handing off, create a JSON handoff in `.board/handoffs/` that matches `.board/handoff.schema.json`.

Record:

- task id
- agent id and role
- status
- files changed
- commands run
- tests and results
- temporary files created and removed
- decisions
- risks
- next recommended step

If validation was not run, record that explicitly. If there is no useful update, do not invent one.
