# B004 gate repair 4 prompt

_Use this shared prompt after the fourth B004 deterministic gate failed in the full BoardFlow condition. It is a controlled compatibility repair prompt._

---

## Shared repair prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled B004 compatibility repair after the deterministic gate. Use only the files that exist in this workspace as the source of truth. Do not assume the condition from this prompt.

Gate feedback:
The deterministic gate now passes import, render_markdown, grand-total formatting, and temporary output path behavior, but it still fails because the generated report file does not contain "# Expense Report".

Current generated title is likely "# Expense Lite Report". The gate expects the report content to include "# Expense Report".

Goal:
Repair only this B004 report-title compatibility gap while preserving existing parser, validator, CSV import, monthly summary, CLI, write_report, render_markdown, and grand-total behavior.

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
- Change the rendered Markdown report heading so generated report text contains "# Expense Report".
- Preserve the final line format exactly: "Grand total: $<amount with two decimals>\n".
- Preserve write_report support for absolute temporary paths outside artifacts/.
- Preserve CLI support for all existing forms, including main(["data/sample_expenses.json", "--output", output_path]).
- Add or update focused tests for the expected title.
- Preserve existing parser, validator, summary, report, and CLI tests.

Scope constraints:
- Keep changes limited to B004 allowed paths.
- Do not read external oracle files.
- Do not inspect parent directories, sibling benchmark workspaces, external results directories, or other benchmark runs.
- Do not use shell environment variables to locate another run.
- If .board/assigned_task.yaml exists, stay inside its allowed_paths.
- If no assigned task file exists, prefer changing only src/expense_lite/report.py, tests/test_report.py, and artifacts/.
- Do not create unrelated docs, scratch files, generated caches, or BoardFlow files in a no-board workspace.
- Remove any __pycache__ or .pyc files if they appear.

Validation commands:
Run all four commands after the repair:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_summary.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_report.py'

Also run this smoke check:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -c "from expense_lite import cli, report; import tempfile, pathlib; text = report.render_markdown({'2026-01': {'food': 58.25}}); print('# Expense Report' in text); print(text.endswith('Grand total: $58.25\n')); p = pathlib.Path(tempfile.mkdtemp()) / 'report.md'; print(cli.main(['data/sample_expenses.json', '--output', str(p)])); print('# Expense Report' in p.read_text(encoding='utf-8'))"

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, keep B004 at READY_FOR_REVIEW, not DONE.
- If the workspace requires a structured handoff, write a new complete JSON handoff under .board/handoffs/ for this repair, with real PASS command records and real PASS test records. Use agent_id "deepseek" unless the workspace instruction requires another value.
- If you write a new BoardFlow handoff, update the B004 current_handoff field to point to it.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a repair handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
