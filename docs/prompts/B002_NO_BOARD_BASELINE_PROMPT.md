# B002 no-board baseline prompt

_Copy-paste prompt for the baseline classroom demo condition. The startup prompt is intentionally identical to the full BoardFlow prompt._

---

## Shared startup prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled comparison run. Use the files that exist in this workspace as the source of truth. Do not assume the condition from this prompt.

Goal:
Implement only benchmark task B002, CSV import.

Workspace inspection before editing:
1. Inspect the repository root.
2. If AGENTS.md exists, read and follow it.
3. If AI_CONTRACT.md exists, read and follow it.
4. If PROJECT_BOARD.md exists, read it.
5. If .board/tasks.yaml exists, read it.
6. If .board/assigned_task.yaml exists, read it and treat its allowed_paths, acceptance commands, and handoff requirements as binding.
7. If a relevant handoff exists under .board/handoffs/, read it, especially the B001 handoff.
8. If BoardFlow files do not exist, do not create them unless an existing repository instruction explicitly requires them.

Task:
Add CSV expense import after the B001 date parser work already exists.

Acceptance criteria:
- Read CSV rows with date, description, category, and amount fields.
- Reuse existing date normalization and expense validation instead of duplicating date or validation logic.
- Return normalized expense records consistent with validate_expense output.
- Report missing required CSV columns clearly with ValueError.
- Add focused tests for valid CSV import and malformed CSV import.
- Preserve existing JSON loading, date parser, and validator behavior.

Scope constraints:
- Implement only B002.
- Do not implement B003 or B004.
- Do not read external oracle files.
- Do not inspect parent directories, sibling benchmark workspaces, external results directories, or other benchmark runs.
- Do not use shell environment variables to locate another run.
- If .board/assigned_task.yaml exists, stay inside its allowed_paths.
- If no assigned task file exists, prefer changing only src/expense_lite/parser.py, src/expense_lite/validator.py, tests/test_parser.py, and tests/test_validator.py.
- Do not create unrelated docs, scratch files, temporary output files, generated artifacts, or BoardFlow files in a no-board workspace.
- Keep the implementation small and consistent with the existing load_expenses_json and validate_expense style.

Before changing code:
Run the current parser and validator tests to confirm the B001 baseline still passes:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'

Implementation guidance:
- If there is no CSV import entry point yet, add one in the parser module using a name consistent with load_expenses_json.
- Use Python standard library CSV parsing.
- Validate each imported row through the existing validator.
- Convert numeric CSV amount values to numbers through validation; do not leave amounts as raw strings.
- Keep errors deterministic and clear enough for tests to assert that required columns are missing.

Validation commands:
Run both commands after the fix:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, update B002 to READY_FOR_REVIEW, not DONE. The runner finalize gate will mark DONE after deterministic acceptance.
- If the workspace requires a structured handoff, write a complete JSON handoff under .board/handoffs/ with real PASS command records and real PASS test records.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
