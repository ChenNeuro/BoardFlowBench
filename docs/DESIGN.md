# Design Notes

BoardFlowBench separates protocol state, benchmark definitions, and the demo repository under test.

## BoardFlow Architecture

BoardFlow is a repo-local shared state protocol for sequential multi-agent coding handoff.

It has three layers:

- policy layer: `AGENTS.md` and `AI_CONTRACT.md`
- state layer: `PROJECT_BOARD.md`, `.board/tasks.yaml`, and `.board/handoffs/*.json`
- benchmark layer: `benchmark/tasks/`, `benchmark/scenarios/`, and future scoring checks

`demo_repo_template/` is the target repo that agents modify during benchmark tasks. It is intentionally small so the benchmark focuses on context continuity and coordination discipline rather than difficult application logic.

## Board And Handoff Separation

The board and handoff files answer different questions.

`PROJECT_BOARD.md` and `.board/tasks.yaml` describe the current shared state:

- current milestone
- task list
- task status
- owner
- dependencies
- allowed paths
- acceptance commands

Handoff files describe a single transition from one agent to the next:

- what changed
- what commands ran
- which tests passed, failed, or were not run
- temporary files created and removed
- decisions made
- risks and next recommended step

Keeping them separate prevents the board from becoming a long activity log and prevents handoff notes from becoming the only place to find current task state.

## AI_CONTRACT.md As Policy

`AI_CONTRACT.md` is a policy layer, not the core state mechanism. It defines stable rules such as scope control, file hygiene, handoff discipline, and done criteria.

It must not contain current milestone status, task owner, or task progress. Those values change during experiments and belong in `PROJECT_BOARD.md`, `.board/tasks.yaml`, and `.board/handoffs/*.json`.

## Consistency Verification

The benchmark should later verify:

- `PROJECT_BOARD.md` and `.board/tasks.yaml` name the same milestone.
- Task ids, statuses, owners, and dependencies match between board views.
- Task statuses use only `TODO`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_REVIEW`, and `DONE`.
- Handoff JSON files match `.board/handoff.schema.json`.
- Handoff `task_id` values exist in `.board/tasks.yaml`.
- Files changed by an agent stay within the task's allowed paths unless an exception is recorded.
