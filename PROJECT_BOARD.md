# PROJECT_BOARD.md

Human-readable BoardFlow milestone board for BoardFlowBench.

Dynamic milestone and task state belongs here and in `.board/tasks.yaml`. Stable policy belongs in `AI_CONTRACT.md`.

## Current Milestone

Milestone: M1 - Basic expense parsing and reporting

Goal: complete the four-step Expense Lite task sequence used to evaluate sequential multi-agent handoff.

Status: IN_PROGRESS

## Task Board

| Task | Title | Status | Owner | Dependencies | Notes |
| --- | --- | --- | --- | --- | --- |
| T001 | Date parser | DONE | agent_b | none | Agent B verified acceptance and regression tests from repo-local state. |
| T002 | CSV import | TODO | unassigned | T001 | Import CSV rows using the date parser. |
| T003 | Monthly summary | TODO | unassigned | T002 | Summarize expenses by month and category. |
| T004 | Report artifact | TODO | unassigned | T003 | Render a stable Markdown report artifact. |

## Status Values

Use only: `TODO`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_REVIEW`, `DONE`.

## Handoff State

Latest T001 handoff: `.board/handoffs/T001_agent_b_handoff.json`

## Consistency Checks Planned

- `PROJECT_BOARD.md` and `.board/tasks.yaml` should name the same current milestone.
- Every task listed here should exist in `.board/tasks.yaml`.
- Task status and owner should match between this file and `.board/tasks.yaml`.
- Each completed task should have a relevant handoff when the scenario requires handoff.
