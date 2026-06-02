# AI_CONTRACT.md

This file contains stable rules for an isolated demo benchmark run.

## Task Discipline

- Work only on the task exposed in `.board/assigned_task.yaml`.
- Do not implement future backlog stickers early.
- Treat observable repository state as the source of truth.

## File Hygiene

- Do not create root-level temporary files.
- Keep generated report artifacts under `artifacts/`.
- Keep temporary work under `.scratch/` and remove it before handoff unless recorded.

## Done Criteria

- Run or explicitly waive relevant acceptance commands.
- Remove or record temporary files.
- Update both taskboard views.
- Create a handoff when the scenario requires one.
