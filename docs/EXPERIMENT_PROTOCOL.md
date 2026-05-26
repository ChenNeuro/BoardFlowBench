# Experiment Protocol

This file defines the initial BoardFlowBench experiment flow. It is not a runner implementation.

## Condition 1: No-Board Baseline

In `no_board_baseline`, the agent receives only the assigned task prompt and the demo repository state.

The agent must not use:

- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- `.board/handoffs/*.json`
- `AGENTS.md`
- `AI_CONTRACT.md`

This condition measures how much context continuity is available without repo-local shared state.

## Condition 2: BoardFlow Sequential Handoff

In `boardflow_sequential`, each agent uses the BoardFlow reading order from `AGENTS.md`, works on one assigned task, updates board state, and writes a structured handoff.

The observable repo state is the source of truth. Previous chat transcripts are not part of the handoff.

## Agent A Responsibilities

Agent A starts a task from the assigned benchmark task YAML.

Agent A should:

- read BoardFlow files in the required order,
- confirm milestone, task, dependencies, allowed paths, and acceptance commands,
- update the task to `IN_PROGRESS` when work begins,
- modify only allowed files,
- run relevant acceptance commands when possible,
- update task status before stopping,
- write a handoff JSON if the scenario requires handoff.

## Agent B Allowed Reading

Agent B may read only observable repo state:

- `AGENTS.md`
- `AI_CONTRACT.md`
- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- assigned benchmark task YAML
- latest relevant `.board/handoffs/*.json`
- files in the demo repo needed for the assigned task

Agent B must not rely on Agent A's chat transcript or private notes.

## Reviewer Checks

The Reviewer checks whether the run followed the protocol.

Reviewer checks include:

- board and machine-readable task state agree,
- task statuses use only allowed values,
- dependencies were respected,
- files changed are within allowed paths or exceptions are recorded,
- handoff JSON matches `.board/handoff.schema.json`,
- commands and tests are recorded honestly,
- temporary files were removed or recorded,
- no forbidden root scratch files were created.

## Observable Artifacts Used For Scoring

Scoring should use only observable artifacts:

- git diff and file tree
- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- `.board/handoffs/*.json`
- assigned `benchmark/tasks/*.yaml`
- command and test records inside handoff files
- future checker outputs under `benchmark/results/`

## Not Implemented Yet

- automatic checkers
- scoring script
- scenario runner
- result aggregation
- statistical analysis
