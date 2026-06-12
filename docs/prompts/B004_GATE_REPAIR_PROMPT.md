# B004 gate repair prompt

_Use this shared prompt after the first B004 deterministic gate failed in both conditions. It is a controlled repair prompt, not the original startup prompt._

---

## Shared repair prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled gate-repair run after the B004 Report artifact attempt. Use only the files that exist in this workspace as the source of truth. Do not assume the condition from this prompt.

Gate feedback:
The deterministic gate failed because the module expense_lite.cli is not importable. The report module may already exist and should be preserved.

Goal:
Repair only the B004 CLI/importability gap while preserving the existing report rendering behavior.

Workspace inspection before editing:
1. Inspect the repository root.
2. If AGENTS.md exists, read and follow it.
3. If AI_CONTRACT.md exists, read and follow it.
4. If PROJECT_BOARD.md exists, read it.
5. If .board/tasks.yaml exists, read it.
6. If .board/assigned_task.yaml exists, read it and treat its allowed_paths, acceptance commands, and handoff requirements as binding.
7. If a relevant B004 handoff exists under .board/handoffs/, read it.
8. If BoardFlow files do not exist, do not create them unless an existing repository instruction explicitly requires them.

Repair requirements:
- Create src/expense_lite/cli.py if it does not exist.
- Ensure `from expense_lite import cli, report` succeeds.
- Add generate_report(input_path: str, output_path: str) -> str.
- Add main(argv: list[str] | None = None) -> int.
- generate_report should:
  - load `.json` input using existing load_expenses_json;
  - load `.csv` input using existing load_expenses_csv;
  - validate JSON records with existing validate_expense before summarizing;
  - summarize records with existing monthly_summary;
  - write the Markdown report with existing write_report;
  - return the written report path.
- main should accept two positional arguments: input path and output path. It should call generate_report and return 0 on success.
- Do not duplicate report rendering or monthly summary logic.
- Keep output restricted to artifacts/.
- Add focused tests for the CLI/generate_report behavior.
- Preserve existing parser, validator, summary, and report tests.

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

Also run this import smoke:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -c "from expense_lite import cli, report; print(cli, report)"

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, keep B004 at READY_FOR_REVIEW, not DONE.
- If the workspace requires a structured handoff, write a new complete JSON handoff under .board/handoffs/ for this repair, with real PASS command records and real PASS test records. Use agent_id "deepseek" unless the workspace instruction requires another value.
- If you write a new BoardFlow handoff, update the B004 current_handoff field to point to it.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a repair handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
