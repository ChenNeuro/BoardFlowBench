# PROJECT_BOARD.md

Human-readable development board for BoardFlowBench itself.

Dynamic project state belongs here and in `.board/tasks.yaml`. Demo benchmark state belongs only inside an initialized demo workspace.

## Current Milestone

Milestone: M1 - BoardFlowBench protocol separation and calibration

Goal: keep BoardFlowBench development separate from demo benchmark execution, then harden scorer calibration.

Status: IN_PROGRESS

## Task Board

| Task | Title | Status | Owner | Dependencies | Notes |
| --- | --- | --- | --- | --- | --- |
| P001 | Independent reviewer integration | DONE | codex | none | Added reviewdog publishing and optional independent PR-Agent review. |
| P002 | Bridge lifecycle refresh | DONE | codex | none | Add minimal blackboard and sticker lifecycle refresh. |
| P003 | BoardFlowBench and demo repository separation | DONE | codex | P002 | Split the demo into an independent Git repository and keep root state project-only. |
| P004 | Scorer calibration and hardening | TODO | unassigned | P003 | Correct protocol-scoring false positives, hard gates, and mutation fixtures. |

## Status Values

Use only: `TODO`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_REVIEW`, `DONE`.

## Handoff State

Latest P001 handoff: `.board/handoffs/P001_codex_handoff.json`

Latest P002 handoff: `.board/handoffs/P002_codex_handoff.json`

Latest P003 handoff: `.board/handoffs/P003_codex_handoff.json`

## Consistency Checks

- `PROJECT_BOARD.md` and `.board/tasks.yaml` should name the same current milestone.
- Every task listed here should exist in `.board/tasks.yaml`.
- Task status and owner should match between this file and `.board/tasks.yaml`.
- Demo benchmark stickers must not be added to this project board.
