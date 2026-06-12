# Classroom Demo Run 20260604-002324

## Scope

This is a fresh classroom comparison slice for `B001 Date parser`, `B002 CSV import`, `B003 Monthly summary`, and `B004 Report artifact`.

It compares:

- `full_boardflow`
- `no_board_baseline`

Both conditions use the same Expense Lite seed, oracle pack, task, and Claude Code model path. The only intended variable is whether BoardFlow files and handoff requirements exist in the workspace.

This is now the full B001-B004 lifecycle result. Both runs completed.

## Run Paths

| Item | Path |
| --- | --- |
| Results root | `/tmp/boardflowbench-class-results-20260604-002324` |
| Full workspace | `/tmp/boardflowbench-class-full-20260604-002324/workspace` |
| No-board workspace | `/tmp/boardflowbench-class-noboard-20260604-002324/workspace` |
| Full run manifest | `/tmp/boardflowbench-class-results-20260604-002324/expense_lite-full_boardflow-1780503804525212000/run.json` |
| No-board run manifest | `/tmp/boardflowbench-class-results-20260604-002324/expense_lite-no_board_baseline-1780503805062491000/run.json` |
| Summary JSON | `/tmp/boardflowbench-class-results-20260604-002324/summary.json` |

## Seed Check

| Repository | Commit | Status |
| --- | --- | --- |
| `../ExpenseLiteBenchDemo` | `30ce6f0d76e2338e56d599fd2beb6fe954b96452` | clean |
| `../ExpenseLiteBenchOracles` | `03a6bbcd0703587addc043cdfee54fb0be704702` | clean |

## Starting State

Both fresh workspaces started from the same B001 failure:

- `test_normalize_accepts_slash_date`
- `test_normalize_strips_whitespace_from_slash_date`

The failure was identical in both workspaces: seed `normalize_date()` accepted `YYYY-MM-DD` but rejected `YYYY/MM/DD`.

## Agent Work

### Full BoardFlow

Changed files:

- `src/expense_lite/parser.py`
- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- `.board/handoffs/B001_handoff.json`

Agent-visible validation:

- `test_parser.py`: 5 tests passed
- `test_validator.py`: 3 tests passed

Runner result:

- B001 gate passed
- B002 activated

### No-Board Baseline

Changed files:

- `src/expense_lite/parser.py`

Agent-visible validation:

- `test_parser.py`: 5 tests passed
- `test_validator.py`: 3 tests passed

Runner result:

- B001 gate passed
- B002 activated


## B002 Update

### Full BoardFlow

Changed files:

- `src/expense_lite/parser.py`
- `tests/test_parser.py`
- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- `.board/handoffs/B002_handoff.json`
- `.board/handoffs/B002_repair_handoff.json`

Gate behavior:

- Initial B002 gate failed only on the missing-column error phrase.
- Repair changed the message to include `missing required CSV columns`.
- Repair handoff was corrected to match `.board/handoff.schema.json`.
- B002 deterministic gate passed and B003 was activated.

### No-Board Baseline

Changed files:

- `src/expense_lite/parser.py`
- `tests/test_parser.py`

Gate behavior:

- B002 deterministic gate passed and B003 was activated.
- No BoardFlow files or handoff were created.


## B003 Update

### Full BoardFlow

Changed files:

- `src/expense_lite/summary.py`
- `tests/test_summary.py`
- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- `.board/handoffs/B003_handoff.json`
- `.board/handoffs/B003_repair_handoff.json`

Gate behavior:

- Initial B003 gate failed because the module exposed `summarize_monthly` but the oracle expected `monthly_summary`.
- Repair added `monthly_summary` as a thin compatibility wrapper without duplicating implementation logic.
- B003 deterministic gate passed and B004 was activated.

### No-Board Baseline

Changed files:

- `src/expense_lite/summary.py`
- `tests/test_summary.py`

Gate behavior:

- Initial B003 gate failed for the same `monthly_summary` public API mismatch.
- Repair added the same compatibility wrapper.
- B003 deterministic gate passed and B004 was activated.
- No BoardFlow files or handoff were created.


## B004 Update

### Full BoardFlow

Changed files:

- `src/expense_lite/report.py`
- `src/expense_lite/cli.py`
- `tests/test_report.py`
- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- `.board/handoffs/B004_handoff.json`
- `.board/handoffs/B004_repair_handoff.json`
- `artifacts/.gitkeep`

Gate behavior:

- Initial B004 gate failed because `expense_lite.cli` was not importable.
- Repair 1 added CLI support, but full BoardFlow gate also caught two process issues: an out-of-scope `src/expense_lite/__init__.py` edit and a non-schema handoff field. Both were corrected.
- Repair 2 added `render_markdown` and `--output` CLI support.
- Repair 3 removed the `artifacts/` output-path restriction and fixed final `Grand total: $...` formatting.
- Repair 4 changed the report heading to include `# Expense Report`.
- B004 deterministic gate passed and the full run completed.

### No-Board Baseline

Changed files:

- `src/expense_lite/report.py`
- `src/expense_lite/cli.py`
- `tests/test_report.py`

Gate behavior:

- Initial B004 gate failed because `expense_lite.cli` was not importable.
- Repair 1 added CLI support.
- Repair 2 added `render_markdown` and `--output` CLI support.
- Repair 3 removed the `artifacts/` output-path restriction and fixed final `Grand total: $...` formatting.
- Repair 4 changed the report heading to include `# Expense Report`.
- B004 deterministic gate passed and the no-board run completed.
- No BoardFlow files or handoff were created.

## Aggregated Result

| Condition | Runs | Completed | Stages | Pass rate | Scope drift | Handoff violations | Board violations | Hygiene violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full_boardflow` | 1 | 1 | 4 | 1.00 | 0 | 0 | 0 | 0 |
| `no_board_baseline` | 1 | 1 | 4 | 1.00 | 0 | 0 | 0 | 0 |

## Interpretation

For B001, B002, B003, and B004, both conditions solved the assigned tasks and passed deterministic gate.

The visible difference is not correctness on this tiny task. The visible difference is process trace:

- `full_boardflow` produced board updates and a structured handoff.
- `no_board_baseline` produced only code changes.

For classroom explanation, use B001 as the clean setup example. Use B002 to show the first state-inheritance step: full BoardFlow carried B001 handoff and taskboard context into B002, while no-board relied only on the prompt and repository files. In this run, full BoardFlow needed a small gate-feedback repair for the CSV missing-column error phrase, and that repair was captured as a second structured handoff. Then use the previous B003/B004 repair-loop story to explain why the control plane matters more on longer multi-step tasks: visible tests can pass while hidden contract, API naming, CLI shape, artifact path, or report format still fail deterministic gate.

## Current State

Both fresh runs completed:

```text
status: complete
stages: B001, B002, B003, B004
```
