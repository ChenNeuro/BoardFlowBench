# B004 gate repair 2 prompt

_Use this shared prompt after the second B004 deterministic gate failed in both conditions. It is a controlled compatibility repair prompt._

---

## Shared repair prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled B004 compatibility repair after the deterministic gate. Use only the files that exist in this workspace as the source of truth. Do not assume the condition from this prompt.

Gate feedback:
The deterministic gate now imports expense_lite.cli and expense_lite.report successfully, but it still fails because:
- expense_lite.report does not expose render_markdown(monthly_totals).
- expense_lite.cli.main(["data/sample_expenses.json", "--output", output_path]) returns non-zero.

Goal:
Repair only these B004 compatibility gaps while preserving existing report rendering and write_report behavior.

Workspace inspection before editing:
1. Inspect the repository root.
2. If AGENTS.md exists, read and follow it.
3. If AI_CONTRACT.md exists, read and follow it.
4. If PROJECT_BOARD.md exists, read it.
5. If .board/tasks.yaml exists, read it.
6. If .board/assigned_task.yaml exists, read it and treat its allowed_paths, acceptance commands, and handoff requirements as binding.
7. If relevant B004 handoffs exist under .board/handoffs/, read the newest one.
8. If BoardFlow files do not exist, do not create them unless an existing repository instruction explicitly requires them.

Repair requirements:
- Add report.render_markdown(monthly_totals: dict) -> str as a compatibility alias for the existing report rendering function.
- Preserve render_report and render_markdown_report if they already exist.
- Update cli.main so it supports all of these forms:
  - main([input_path, output_path])
  - main([input_path, "--output", output_path])
  - main(["expense-lite", input_path, output_path])
  - main(["expense-lite", input_path, "--output", output_path])
- main should return 0 on success and non-zero on usage or generation errors.
- Do not duplicate report rendering, parsing, validation, or monthly summary logic.
- Add focused tests for render_markdown and the --output CLI form.
- Preserve existing parser, validator, summary, report, and CLI tests.

Scope constraints:
- Keep changes limited to B004 allowed paths.
- Do not read external oracle files.
- Do not inspect parent directories, sibling benchmark workspaces, external results directories, or other benchmark runs.
- Do not use shell environment variables to locate another run.
- If .board/assigned_task.yaml exists, stay inside its allowed_paths.
- If no assigned task file exists, prefer changing only src/expense_lite/cli.py, src/expense_lite/report.py, tests/test_report.py, and artifacts/.
- Do not create unrelated docs, scratch files, temporary output files outside artifacts/, generated caches, or BoardFlow files in a no-board workspace.
- Remove any __pycache__ or .pyc files if they appear.

Validation commands:
Run all four commands after the repair:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_summary.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_report.py'

Also run these smoke checks:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -c "from expense_lite import cli, report; print(hasattr(report, 'render_markdown')); print(cli.main(['data/sample_expenses.json', '--output', 'artifacts/smoke-report.md']))"
rm -f artifacts/smoke-report.md

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, keep B004 at READY_FOR_REVIEW, not DONE.
- If the workspace requires a structured handoff, write a new complete JSON handoff under .board/handoffs/ for this repair, with real PASS command records and real PASS test records. Use agent_id "deepseek" unless the workspace instruction requires another value.
- If you write a new BoardFlow handoff, update the B004 current_handoff field to point to it.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a repair handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
