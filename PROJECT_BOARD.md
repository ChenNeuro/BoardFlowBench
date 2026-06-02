# PROJECT_BOARD.md

Human-readable development board for BoardFlowBench itself.

Dynamic project state belongs here and in `.board/tasks.yaml`. Demo benchmark state belongs only inside an initialized demo workspace.

## Current Milestone

Milestone: M1 - BoardFlowBench protocol separation and calibration

Goal: keep BoardFlowBench development separate from demo benchmark execution, then harden scorer calibration.

Status: DONE

## Task Board

| Task | Title | Status | Owner | Dependencies | Notes |
| --- | --- | --- | --- | --- | --- |
| P001 | Independent reviewer integration | DONE | codex | none | Added reviewdog publishing and optional independent PR-Agent review. |
| P002 | Bridge lifecycle refresh | DONE | codex | none | Add minimal blackboard and sticker lifecycle refresh. |
| P003 | BoardFlowBench and demo repository separation | DONE | codex | P002 | Split the demo into an independent Git repository and keep root state project-only. |
| P004 | Evidence gate and scorer hardening | DONE | codex | P003 | Add deterministic finalize gates, condition-aware scoring, and baseline diff scope checks. |
| P005 | Trusted repository bootstrap | DONE | codex | P004 | Recommend allowlisted Copier or Git templates for empty repositories. |
| P006 | Scenario runner and oracle isolation | DONE | codex | P004 | Add four experiment conditions, isolated oracle packs, adapters, and checkpoints. |
| P007 | Result aggregation and reviewer reporting | DONE | codex | P006 | Aggregate external run results and keep independent reviewer findings non-blocking. |

## Status Values

Use only: `TODO`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_REVIEW`, `DONE`.

## Handoff State

Latest P001 handoff: `.board/handoffs/P001_codex_handoff.json`

Latest P002 handoff: `.board/handoffs/P002_codex_handoff.json`

Latest P003 handoff: `.board/handoffs/P003_codex_handoff.json`

Latest P004 handoff: `.board/handoffs/P004_codex_handoff.json`

Latest P005 handoff: `.board/handoffs/P005_codex_handoff.json`

Latest P006 handoff: `.board/handoffs/P006_codex_handoff.json`

Latest P007 handoff: `.board/handoffs/P007_codex_handoff.json`

## Consistency Checks

- `PROJECT_BOARD.md` and `.board/tasks.yaml` should name the same current milestone.
- Every task listed here should exist in `.board/tasks.yaml`.
- Task status and owner should match between this file and `.board/tasks.yaml`.
- Demo benchmark stickers must not be added to this project board.
