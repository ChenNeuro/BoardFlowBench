---
name: repoflow-task-agent
description: Repository-local coding workflow for BoardFlowBench/RepoFlow task agents. Use when an agent must implement an assigned benchmark task, compare skill-vs-plain task execution, preserve task boundaries, produce handoff evidence, run Expense Lite B-series pilot tasks, or prepare non-official SWE-bench Lite smoke tasks with a local model.
---

# RepoFlow Task Agent

Apply this skill before editing a benchmark workspace.

## Workflow

1. Identify the assigned task id and read its task specification.
2. Read only repository state relevant to that task: source files, tests, board state, assigned task, and latest handoff if present.
3. Make the smallest code/test changes that satisfy the task.
4. Stay inside the task's `allowed_paths`. Treat that list as a hard boundary: do not edit package export files, fixtures, generated outputs, caches, slides, PDFs, or scratch files unless the task explicitly lists them.
5. Preserve public APIs from earlier tasks. For downstream tasks, reuse upstream functions instead of duplicating their logic.
6. Run the task's acceptance commands and focused regression commands.
7. If the workspace has `.board/`, update the assigned task state and write a non-empty structured handoff under `.board/handoffs/`.
8. Report changed files, validation commands, results, risks, and the next recommended step.

## Expense Lite B-Series Rules

- B001: update `normalize_date` to accept `YYYY-MM-DD` and `YYYY/MM/DD`, returning normalized `YYYY-MM-DD`; keep malformed dates rejected with `ValueError`. Prefer this simple pattern: loop over `("%Y-%m-%d", "%Y/%m/%d")`, return on successful `datetime.strptime`, and use `continue` only inside that loop.
- B002: add CSV import in the parser module with a name consistent with `load_expenses_json`; use `csv.DictReader`; require `date`, `description`, `category`, and `amount`; convert amount through validation; reuse `validate_expense` and `normalize_date`; missing columns must raise `ValueError` containing `missing required CSV columns`.
- B002 implementation checklist: initialize `records = []`; for each CSV row build a candidate record, validate it, append the validated record to `records`, and return `records` after the loop. Returned records must contain normalized date strings such as `2026-01-03`, not raw CSV date strings such as `2026/01/03`. Do not return raw CSV string values.
- B002 repair checklist: `validator.py` already imports `normalize_date` from `parser.py`, so avoid module-level reverse imports that create circular imports. In `load_expenses_csv`, use a local import such as `from .validator import REQUIRED_FIELDS, validate_expense`, convert the CSV `amount` field to a number before validation, and then call `validate_expense(candidate)`. Do not copy `normalize_date` into `validator.py`, do not create a second date parser, and do not move validation logic into `parser.py`.
- B002 test checklist: preserve existing tests and imports; append focused CSV tests to existing test files; use `tempfile.NamedTemporaryFile` or `TemporaryDirectory`; do not reference or create `tests/data/`, `data/*.csv`, or any new fixture directory; do not edit package `__init__.py` unless it appears in `allowed_paths`.

## SWE Lite Smoke Rules

- Treat SWE-bench Lite work as patch-generation smoke unless Docker and the official SWE-bench harness are available.
- Do not show or use `gold_patch.diff`, `test_patch.diff`, oracle files, or hidden evaluator material while generating a patch.
- Use the issue statement and checked-out base commit as the task source of truth.
- Make the smallest source change that addresses the issue; avoid broad refactors, formatting churn, and repository-wide rewrites.
- Run focused repository tests when dependencies are available. If tests cannot run locally, record the exact environment failure separately from model or harness failure.
- Write handoff evidence under `.repoflow/handoffs/` for SWE Lite smoke workspaces.

### Nested Composition Debugging

For bugs that appear only after nesting models, parsers, plans, or other composable objects:

1. Translate the expected result into a small block or tree composition before editing.
2. Trace the recursive path from the public function through the operator used at the failing nesting level.
3. Compare the operator's primitive-object branches with its already-computed/intermediate-result branches.
4. Treat an intermediate matrix or structure as computed dependency information. Preserve its values when repositioning it; do not replace it with an all-ones/default structure unless the operator intentionally marks the whole child as inseparable.
5. Check left/right branch symmetry and add or run one nested regression case.

## Handoff Minimum

When `.board/` exists, write JSON containing:

- `task_id`
- `agent_id`
- `role`
- `status`
- `files_changed`
- `commands_run`
- `tests`
- `temporary_files_created`
- `temporary_files_removed`
- `decisions`
- `risks`
- `next_recommended_step`

Do not claim validation passed unless the command was actually run. If validation fails, repair the implementation before changing tests. Do not weaken tests to match broken behavior.
