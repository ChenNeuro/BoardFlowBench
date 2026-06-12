# B004 full BoardFlow prompt

_Copy-paste prompt for the architecture-enabled classroom demo condition. The startup prompt is intentionally identical to the no-board baseline prompt._

---

## Shared startup prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled comparison run. Use the files that exist in this workspace as the source of truth. Do not assume the condition from this prompt.

Goal:
Implement only benchmark task B004, Report artifact.

Workspace inspection before editing:
1. Inspect the repository root.
2. If AGENTS.md exists, read and follow it.
3. If AI_CONTRACT.md exists, read and follow it.
4. If PROJECT_BOARD.md exists, read it.
5. If .board/tasks.yaml exists, read it.
6. If .board/assigned_task.yaml exists, read it and treat its allowed_paths, acceptance commands, and handoff requirements as binding.
7. If a relevant handoff exists under .board/handoffs/, read it, especially the B003 handoff and B003 repair handoff.
8. If BoardFlow files do not exist, do not create them unless an existing repository instruction explicitly requires them.

Task:
Generate a stable Markdown report artifact from monthly summaries after B003 already exists.

Acceptance criteria:
- Render a Markdown report with deterministic headings and totals.
- Write generated reports only under artifacts/.
- Do not leave scratch files in the repository root.
- Add focused tests for report rendering.
- Preserve parser, CSV import, JSON loading, validator, and monthly summary behavior.

Required public API:
- Create src/expense_lite/report.py if it does not exist.
- Add render_report(monthly_totals: dict) -> str.
- Add render_markdown_report(monthly_totals: dict) -> str as a compatibility alias.
- Add write_report(monthly_totals: dict, path: str) -> str.
- write_report must reject output paths outside artifacts/.
- The Markdown should start with "# Expense Lite Report".
- Include deterministic month headings like "## 2026-01".
- Include category total lines with two decimal places.
- Include a deterministic grand total line.
- Sort months and categories for stable output.
- If you add src/expense_lite/cli.py, keep it small and do not make it required for tests.

Scope constraints:
- Implement only B004.
- Do not change B001, B002, or B003 behavior except imports needed for report code.
- Do not read external oracle files.
- Do not inspect parent directories, sibling benchmark workspaces, external results directories, or other benchmark runs.
- Do not use shell environment variables to locate another run.
- If .board/assigned_task.yaml exists, stay inside its allowed_paths.
- If no assigned task file exists, prefer changing only src/expense_lite/report.py, src/expense_lite/cli.py, tests/test_report.py, and artifacts/.
- Do not create unrelated docs, scratch files, temporary output files outside artifacts/, generated caches, or BoardFlow files in a no-board workspace.

Before changing code:
Run the current parser, validator, and summary tests to confirm the B001-B003 baseline still passes:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_summary.py'

Implementation guidance:
- render_report should accept the nested dictionary returned by monthly_summary.
- Avoid depending on wall-clock time, filesystem ordering, locale, or random data.
- Keep formatting simple and testable.
- If write_report creates parent directories, only create directories under artifacts/.
- Return the written path from write_report.

Validation commands:
Run all four commands after the fix:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_summary.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_report.py'

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, update B004 to READY_FOR_REVIEW, not DONE. The runner finalize gate will mark DONE after deterministic acceptance.
- If the workspace requires a structured handoff, write a complete JSON handoff under .board/handoffs/ with real PASS command records and real PASS test records. Use agent_id "deepseek" unless the workspace instruction requires another value.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
