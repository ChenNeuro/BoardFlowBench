# BoardFlowBench

A benchmark for repo-local shared state in sequential multi-agent coding handoff.

BoardFlowBench studies whether a lightweight repo-local protocol can reduce context loss, repeated work, hygiene issues, and unclear ownership when one coding agent hands work to another.

This repository is an initial course-project skeleton. It defines the benchmark shape, BoardFlow coordination files, task fixtures, and a minimal synthetic demo repository template. It does not yet implement automatic scoring, checkers, or the full experimental runner.

## Repository Layout

- `AGENTS.md`: entry point for coding agents.
- `AI_CONTRACT.md`: stable agent discipline and repo hygiene rules.
- `PROJECT_BOARD.md`: human-readable milestone and task board.
- `.board/tasks.yaml`: machine-readable task board.
- `.board/handoff.schema.json`: structured handoff format.
- `benchmark/tasks/`: benchmark task definitions and acceptance criteria.
- `benchmark/scenarios/`: experimental condition definitions.
- `benchmark/scoring/`: placeholder for future automatic checkers and scoring.
- `demo_repo_template/`: small synthetic Python repo used by benchmark tasks.
- `docs/`: research and design notes.

## Current Status

Initial skeleton only. The next stage should define checker specifications and decide the first runnable pilot path.
