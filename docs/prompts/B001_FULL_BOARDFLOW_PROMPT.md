# B001 full BoardFlow prompt

_Copy-paste prompt for the architecture-enabled classroom demo condition. The startup prompt is intentionally identical to the no-board baseline prompt._

---

## Shared startup prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled comparison run. Use the files that exist in this workspace as the source of truth. Do not assume the condition from this prompt.

Goal:
Implement only benchmark task B001, Date parser.

Workspace inspection before editing:
1. Inspect the repository root.
2. If AGENTS.md exists, read and follow it.
3. If AI_CONTRACT.md exists, read and follow it.
4. If PROJECT_BOARD.md exists, read it.
5. If .board/tasks.yaml exists, read it.
6. If .board/assigned_task.yaml exists, read it and treat its allowed_paths, acceptance commands, and handoff requirements as binding.
7. If a relevant handoff exists under .board/handoffs/, read it.
8. If BoardFlow files do not exist, do not create them unless an existing repository instruction explicitly requires them.

Task:
Fix the Expense Lite date parser so normalize_date accepts both YYYY-MM-DD and YYYY/MM/DD input strings and always returns normalized YYYY-MM-DD strings.

Acceptance criteria:
- Accept YYYY-MM-DD dates.
- Accept YYYY/MM/DD dates.
- Strip surrounding whitespace.
- Normalize both accepted formats to YYYY-MM-DD strings.
- Reject malformed dates with a clear ValueError.
- Keep public parser function names unchanged.

Scope constraints:
- Implement only B001.
- Do not implement B002, B003, or B004.
- Do not read external oracle files.
- Do not inspect parent directories, sibling benchmark workspaces, external results directories, or other benchmark runs.
- Do not use shell environment variables to locate another run.
- If .board/assigned_task.yaml exists, stay inside its allowed_paths.
- If no assigned task file exists, prefer changing only src/expense_lite/parser.py; change tests/test_parser.py only if the visible test itself is clearly wrong.
- Do not create unrelated docs, scratch files, temporary output files, or generated artifacts.

Before changing code:
Run the expected failing parser test and confirm slash-date input currently fails:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'

Validation commands:
Run both commands after the fix:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, update B001 to READY_FOR_REVIEW, not DONE. The runner finalize gate will mark DONE after deterministic acceptance.
- If the workspace requires a structured handoff, write a complete JSON handoff under .board/handoffs/ with real PASS command records and real PASS test records.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
