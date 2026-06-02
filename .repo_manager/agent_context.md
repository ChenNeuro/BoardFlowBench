# Agent Context

> Generated for agent: `codex`
> Last task: `P004`

## Refresh

- Phase: `start`
- Override reason: Continue from existing P001-P003 implementation baseline and complete P004-P007 closure without discarding user-approved changes.
- Risks:
  - git workspace has staged, unstaged, or untracked files

## Current Milestone

- ID: `M1`
- Title: BoardFlowBench protocol separation and calibration
- Status: `IN_PROGRESS`
- Goal: Keep BoardFlowBench development separate from demo benchmark execution, then harden scorer calibration.

## Current Sticker

- ID: `P004`
- Title: Scorer calibration and hardening
- Status: `TODO`
- Owner: `unassigned`
- Notes: Correct protocol-scoring false positives, hard gates, and mutation fixtures.

## Unfinished Stickers

- No other active stickers.

## Long-Term Backlog

- **P004** [TODO] - Scorer calibration and hardening (owner: unassigned)

## Git Status

- Available: `True`
- Branch: `yihao/feature`
- Clean: `False`
- Staged:
  - none
- Unstaged:
  - `"docs/\344\270\255\346\226\207\350\257\264\346\230\216\344\270\216\346\211\251\345\261\225\346\214\207\345\215\227.md"`
  - `.board/handoff.schema.json`
  - `.board/handoffs/T001_agent_a_handoff.json`
  - `.board/handoffs/T001_agent_b_handoff.json`
  - `.board/reviews/T001_review.md`
  - `.board/tasks.yaml`
  - `.repo_manager/agent_context.md`
  - `.repo_manager/repo_style_profile.json`
  - `.repo_manager/user_feedback.jsonl`
  - `AGENTS.md`
  - `AI_CONTRACT.md`
  - `PROJECT_BOARD.md`
  - `README.md`
  - `benchmark/scenarios/boardflow_sequential.yaml`
  - `benchmark/scenarios/no_board_baseline.yaml`
  - `benchmark/tasks/task_001_date_parser.yaml`
  - `benchmark/tasks/task_002_csv_import.yaml`
  - `benchmark/tasks/task_003_monthly_summary.yaml`
  - `benchmark/tasks/task_004_report_artifact.yaml`
  - `demo_repo_template/.scratch/.gitkeep`
  - `demo_repo_template/README.md`
  - `demo_repo_template/artifacts/.gitkeep`
  - `demo_repo_template/data/sample_expenses.json`
  - `demo_repo_template/pyproject.toml`
  - `demo_repo_template/src/expense_lite/__init__.py`
  - `demo_repo_template/src/expense_lite/cli.py`
  - `demo_repo_template/src/expense_lite/parser.py`
  - `demo_repo_template/src/expense_lite/report.py`
  - `demo_repo_template/src/expense_lite/summary.py`
  - `demo_repo_template/src/expense_lite/validator.py`
  - `demo_repo_template/tests/test_parser.py`
  - `demo_repo_template/tests/test_report.py`
  - `demo_repo_template/tests/test_summary.py`
  - `demo_repo_template/tests/test_validator.py`
  - `docs/DESIGN.md`
  - `docs/EXPERIMENT_PROTOCOL.md`
  - `docs/RUN_TASK_001.md`
  - `repo_manager_core/board/board_io.py`
  - `repo_manager_core/style/context_writer.py`
  - `repo_manager_core/style/learn_repo_style.py`
  - `skills/agent-bridge/SKILL.md`
  - `skills/agent-bridge/scripts/bridge_handoff.py`
  - `skills/agent-bridge/scripts/bridge_status.py`
  - `skills/agent-bridge/scripts/bridge_update_context.py`
  - `tests/test_board_io.py`
  - `tests/test_board_validator.py`
  - `tests/test_handoff.py`
- Untracked:
  - `.board/handoffs/P001_codex_handoff.json`
  - `.board/handoffs/P002_codex_handoff.json`
  - `.board/handoffs/P003_codex_handoff.json`
  - `.github/workflows/reviewer.yml`
  - `.repo_manager/style_record.md`
  - `benchmark/targets/expense_lite.yaml`
  - `benchmark/tasks/expense_lite/b001_date_parser.yaml`
  - `benchmark/tasks/expense_lite/b002_csv_import.yaml`
  - `benchmark/tasks/expense_lite/b003_monthly_summary.yaml`
  - `benchmark/tasks/expense_lite/b004_report_artifact.yaml`
  - `benchmark/templates/boardflow/AGENTS.md`
  - `benchmark/templates/boardflow/AI_CONTRACT.md`
  - `docs/RUN_TASK_B001.md`
  - `project/tasks/p001_reviewer_integration.yaml`
  - `project/tasks/p002_bridge_refresh.yaml`
  - `project/tasks/p003_demo_repository_separation.yaml`
  - `project/tasks/p004_scorer_calibration.yaml`
  - `repo_manager_core/benchmark/__init__.py`
  - `repo_manager_core/benchmark/workspace.py`
  - `repo_manager_core/board/board_sync.py`
  - `repo_manager_core/board/git_state.py`
  - `repo_manager_core/health/reviewdog_export.py`
  - `scripts/activate_benchmark_task.py`
  - `scripts/init_benchmark_workspace.py`
  - `skills/agent-bridge/scripts/bridge_refresh.py`
  - `tests/test_benchmark_workspace.py`
  - `tests/test_board_sync.py`
  - `tests/test_bridge_refresh.py`
  - `tests/test_reviewdog_export.py`
  - `tests/test_style_bridge.py`

## Repository Style Summary

- Functions: 229
- Snake case compliance: 228/229
- With docstrings: 59
- Average function length: 18.7
- Patch-like names: 5

## Test Style Summary

- Test files: 18
- Test functions: 51
- Snake case test functions: 51
- Common test directories: [["tests", 16], ["tests/fixtures", 1], ["tests/fixtures/sample_repo/pkg", 1]]

## Latest Handoff

- No handoff recorded for the current sticker.

## Human Style Record

- Read `.repo_manager/style_record.md` when it exists. Preserve human-written text verbatim.

## Current Task Board

- **P001** [DONE] — Independent reviewer integration (owner: codex)
- **P002** [DONE] — Bridge lifecycle refresh (owner: codex)
- **P003** [DONE] — BoardFlowBench and demo repository separation (owner: codex)
- **P004** [TODO] — Scorer calibration and hardening (owner: unassigned)

## Notes for the Next Agent

- Read `.board/tasks.yaml` and `.board/handoffs/` for detailed handoff records.
- Read `.repo_manager/repo_style_profile.json` for style conventions.
- Read `.repo_manager/style_record.md` for human-written conventions.
- Match the prevailing naming and docstring style in this codebase.
