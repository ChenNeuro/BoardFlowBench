# Design Notes

BoardFlowBench separates project development state, benchmark definitions, and standalone demo repositories under test.

## BoardFlow Architecture

BoardFlow is a repo-local shared state protocol for sequential multi-agent coding handoff.

It has three layers:

- policy layer: `AGENTS.md` and `AI_CONTRACT.md`
- project state layer: `PROJECT_BOARD.md`, `.board/tasks.yaml`, and `.board/handoffs/*.json`
- benchmark layer: `benchmark/targets/`, `benchmark/tasks/`, `benchmark/scenarios/`, and scoring checks

Expense Lite is maintained as the standalone `ChenNeuro/ExpenseLiteBenchDemo` target repository. Each experiment clones a fixed seed commit into an external workspace. BoardFlow condition setup injects run-local protocol state into that clone. No-board setup leaves the clone free of BoardFlow files.

## Board And Handoff Separation

The board and handoff files answer different questions.

The root `PROJECT_BOARD.md` and `.board/tasks.yaml` describe BoardFlowBench development state. Injected workspace copies describe one demo run:

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

The benchmark verifies:

- `PROJECT_BOARD.md` and `.board/tasks.yaml` name the same milestone.
- Task ids, statuses, owners, and dependencies match between board views.
- Task statuses use only `TODO`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_REVIEW`, and `DONE`.
- Handoff JSON files match `.board/handoff.schema.json`.
- Handoff `task_id` values exist in `.board/tasks.yaml`.
- Files changed by an agent stay within the task's allowed paths unless an exception is recorded.
