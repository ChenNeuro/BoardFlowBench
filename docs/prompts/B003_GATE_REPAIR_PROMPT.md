# B003 gate repair prompt

_Use this shared prompt after the first B003 deterministic gate failed in both conditions. It is a controlled repair prompt, not the original startup prompt._

---

## Shared repair prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled gate-repair run after the B003 Monthly summary attempt. Use only the files that exist in this workspace as the source of truth. Do not assume the condition from this prompt.

Gate feedback:
The deterministic gate failed because the module expense_lite.summary does not expose the expected public function name monthly_summary. The implementation currently may expose summarize_monthly instead.

Goal:
Repair only the B003 public API mismatch while preserving the existing monthly summary implementation.

Workspace inspection before editing:
1. Inspect the repository root.
2. If AGENTS.md exists, read and follow it.
3. If AI_CONTRACT.md exists, read and follow it.
4. If PROJECT_BOARD.md exists, read it.
5. If .board/tasks.yaml exists, read it.
6. If .board/assigned_task.yaml exists, read it and treat its allowed_paths, acceptance commands, and handoff requirements as binding.
7. If a relevant B003 handoff exists under .board/handoffs/, read it.
8. If BoardFlow files do not exist, do not create them unless an existing repository instruction explicitly requires them.

Repair requirements:
- Add a public function named monthly_summary(expenses: list[dict]) -> dict in src/expense_lite/summary.py.
- Preserve the existing summarize_monthly(expenses) behavior if it already exists.
- Prefer making monthly_summary call summarize_monthly, or make summarize_monthly call monthly_summary. Do not duplicate the full implementation.
- Add or update tests so both monthly_summary and the existing summarize_monthly entry point, if present, are covered.
- Do not change parser, validator, CSV import, JSON loading, or report-generation behavior.
- Do not implement B004.

Scope constraints:
- Keep changes limited to B003 allowed paths.
- Do not read external oracle files.
- Do not inspect parent directories, sibling benchmark workspaces, external results directories, or other benchmark runs.
- Do not use shell environment variables to locate another run.
- If .board/assigned_task.yaml exists, stay inside its allowed_paths.
- If no assigned task file exists, prefer changing only src/expense_lite/summary.py and tests/test_summary.py.
- Do not create unrelated docs, scratch files, temporary output files, generated artifacts, or BoardFlow files in a no-board workspace.

Validation commands:
Run all three commands after the repair:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_summary.py'

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, keep B003 at READY_FOR_REVIEW, not DONE.
- If the workspace requires a structured handoff, write a new complete JSON handoff under .board/handoffs/ for this repair, with real PASS command records and real PASS test records. Use agent_id "mimo" unless the workspace instruction requires another value.
- If you write a new BoardFlow handoff, update the B003 current_handoff field to point to it.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a repair handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
