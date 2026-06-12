# B002 gate repair prompt

_Use this prompt when B002 deterministic gate fails only on the missing-column error message._

---

## Repair prompt

```text
You are inside an Expense Lite benchmark workspace.

This is a controlled B002 compatibility repair after the deterministic gate. Use only the files that exist in this workspace as the source of truth.

Gate feedback:
CSV import works, but the missing-column error message does not match the deterministic gate. The gate expects a ValueError message containing exactly this phrase:

missing required CSV columns

Current implementation may say something like:

CSV missing required columns: description, category

Goal:
Repair only the B002 missing-column ValueError message while preserving existing parser, validator, JSON loading, date normalization, CSV import behavior, taskboard state, and handoff behavior.

Requirements:
- When CSV required columns are missing, raise ValueError with a message containing "missing required CSV columns".
- Keep the missing column names in the message if they are already reported.
- Do not change public function names.
- Do not implement B003 or B004.
- Preserve existing tests and add/update a focused test for the exact phrase if needed.

Validation commands:
Run both commands after the repair:

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'

State and handoff behavior:
- If the workspace has BoardFlow taskboard files, keep B002 at READY_FOR_REVIEW, not DONE.
- If the workspace requires a structured handoff, write a new complete JSON handoff under .board/handoffs/ for this repair, with real PASS command records and real PASS test records.
- If you write a new BoardFlow handoff, update the B002 current_handoff field to point to it.
- If the workspace has no BoardFlow taskboard or handoff requirement, do not create BoardFlow files and do not invent a handoff.

Final response:
Summarize changed files, validation commands, and test results. If a repair handoff was required and written, include the handoff path. Do not claim final benchmark acceptance; say the runner should be resumed for deterministic scoring.
```
