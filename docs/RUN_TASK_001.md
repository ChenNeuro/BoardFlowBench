# Run Task T001

T001 is the date parser task for the Expense Lite demo repository.

The benchmark starts from a deliberately buggy state: `normalize_date` accepts `YYYY-MM-DD` but fails on `YYYY/MM/DD`. The test suite already describes the intended behavior, so one parser test should fail before an agent fixes T001.

## Run The Initial Failing Test

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=demo_repo_template/src python3 -m unittest discover -s demo_repo_template/tests -p 'test_parser.py'
```

Expected initial result:

- `test_normalize_accepts_slash_date` fails.
- The failure is intentional and is the starting point for T001.

## Run T001 Manually With A Coding Agent

In the BoardFlow condition, give the agent task `T001` and require the reading order from `AGENTS.md`:

1. `AGENTS.md`
2. `AI_CONTRACT.md`
3. `PROJECT_BOARD.md`
4. `.board/tasks.yaml`
5. `benchmark/tasks/task_001_date_parser.yaml`
6. latest relevant handoff under `.board/handoffs/`

The agent should only modify the allowed paths listed in `benchmark/tasks/task_001_date_parser.yaml`. It should not change public parser function names or unrelated modules.

Before stopping, the agent should update the board state and write a structured handoff if the scenario requires it.

## Compare Conditions Later

For the no-board baseline, provide only the task prompt and demo repo files needed for T001. Do not provide BoardFlow state files or previous handoffs.

For the BoardFlow sequential condition, provide the observable repo state and require the agent to use BoardFlow files. Compare:

- whether the agent identifies the same failing test,
- whether it stays within allowed paths,
- whether it records validation honestly,
- whether it leaves temporary files behind,
- whether board and handoff state remain consistent.
