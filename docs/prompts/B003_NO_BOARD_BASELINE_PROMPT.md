# B003 no-board baseline prompt

_Copy-paste prompt for the baseline classroom demo condition. The startup prompt is intentionally identical to the full BoardFlow prompt._

---

## Shared startup prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled comparison run. Use the files that exist in this workspace as the source of truth. Do not assume the condition from this prompt.

Goal:
Implement only benchmark task B003, Monthly summary.

Workspace inspection before editing:
1. Inspect the repository root.
2. If AGENTS.md exists, read and follow it.
3. If AI_CONTRACT.md exists, read and follow it.
4. If PROJECT_BOARD.md exists, read it.
5. If .board/tasks.yaml exists, read it.
6. If .board/assigned_task.yaml exists, read it and treat its allowed_paths, acceptance commands, and handoff requirements as binding.
7. If a relevant handoff exists under .board/handoffs/, read it, especially the B002 handoff.
8. If BoardFlow files do not exist, do not create them unless an existing repository instruction explicitly requires them.

Task:
Add monthly expense summaries after the B002 CSV import work already exists.

Acceptance criteria:
- Group normalized expense records by YYYY-MM month.
- Sum amounts by category within each month.
- Keep deterministic ordering for stable reports.
- Add focused tests for multiple months and multiple categories.
- Preserve existing parser, CSV import, JSON loading, date parser, and validator behavior.

Required public API:
- Create src/expense_lite/summary.py if it does not exist.
- Add a public function named summarize_monthly(expenses: list[dict]) -> dict.
- The function should accept already-normalized expense records like validate_expense or load_expenses_csv returns.
- Return a plain nested dictionary shaped like {month: {category: total_amount}}.
- Month keys should be YYYY-MM strings derived from each record's date.
- Category keys should be strings.
- Amount totals should be floats.

Scope constraints:
- Implement only B003.
- Do not implement B004 or report generation.
- Do not read external oracle files.
- Do not inspect parent directories, sibling benchmark workspaces, external results directories, or other benchmark runs.
- Do not use shell environment variables to locate another run.
- If .board/assigned_task.yaml exists, stay inside its allowed_paths.
- If no assigned task file exists, prefer changing only src/expense_lite/summary.py and tests/test_summary.py.
- Do not create unrelated docs, scratch files, temporary output files, generated artifacts, or BoardFlow files in a no-board workspace.
- Keep the implementation small and consistent with the existing parser and validator style.

Before changing code:
Run the current parser and validator tests to confirm the B001-B002 baseline still passes:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'

Implementation guidance:
- Do not mutate input records.
- Validate that each input record has date, category, and amount fields.
- Reuse the existing date format by reading the first seven characters of a normalized YYYY-MM-DD date.
- Sort months and categories when constructing the returned dictionary so the result is deterministic.
- Raise ValueError for malformed records or non-numeric amounts.

Validation commands:
Run all three commands after the fix:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_summary.py'

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, update B003 to READY_FOR_REVIEW, not DONE. The runner finalize gate will mark DONE after deterministic acceptance.
- If the workspace requires a structured handoff, write a complete JSON handoff under .board/handoffs/ with real PASS command records and real PASS test records.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
