# AI_CONTRACT.md

This file contains stable agent discipline and repo hygiene rules. It must not contain current milestone status, task owner, or other dynamic task state.

## Task Discipline

- Read the required BoardFlow files before changing code.
- Work only on the assigned task.
- Respect task dependencies before starting downstream work.
- Use only the task statuses defined by BoardFlow: `TODO`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_REVIEW`, `DONE`.
- Do not solve future benchmark tasks early.

## Scope Control

- Modify only files relevant to the assigned task.
- Stay within the task's `allowed_paths` unless the user explicitly broadens scope.
- Do not refactor unrelated code.
- Do not rename files or public interfaces unless the task requires it.
- Preserve existing research docs unless the user asks to change them.

## File Hygiene

- Do not create root-level temporary files.
- Do not create files named `result.txt`, `output.txt`, `final.md`, `tmp.py`, `debug.py`, or similar scratch artifacts.
- Keep generated demo artifacts under `demo_repo_template/artifacts/` when a task explicitly requires artifacts.
- Keep temporary demo work under `demo_repo_template/.scratch/` and remove it before handoff unless it is intentionally retained and recorded.
- Do not add unnecessary dependencies.

## Handoff Discipline

- Create a structured handoff when stopping task work or passing work to another agent.
- Record files changed, commands run, tests, temporary files, decisions, risks, and the next recommended step.
- Do not rely on previous chat transcripts as handoff state during benchmark runs.
- Treat observable repo state as the source of truth.

## Done Criteria

A task can be marked `DONE` only when:

- its acceptance criteria are satisfied,
- relevant acceptance commands were run or explicitly waived by the user,
- temporary files are removed or recorded,
- board state is updated in `PROJECT_BOARD.md` and `.board/tasks.yaml`,
- a handoff exists when the scenario requires one.

If any condition is missing, use `READY_FOR_REVIEW`, `BLOCKED`, or `IN_PROGRESS` instead of `DONE`.
