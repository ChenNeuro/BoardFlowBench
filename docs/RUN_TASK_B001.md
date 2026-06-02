# Run Task B001

B001 is the date parser task for the standalone Expense Lite demo repository.

The benchmark starts from a deliberately buggy state: `normalize_date` accepts `YYYY-MM-DD` but fails on `YYYY/MM/DD`. The test suite already describes the intended behavior, so parser tests should fail before an agent fixes B001.

## Run The Initial Failing Test

Initialize an isolated workspace from the BoardFlowBench repository:

```bash
PYTHONPATH=. python3 scripts/init_benchmark_workspace.py \
  --target expense_lite \
  --condition full_boardflow \
  --task-id B001 \
  --workspace /tmp/boardflowbench-runs/run-001
cd /tmp/boardflowbench-runs/run-001
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'
```

Expected initial result:

- `test_normalize_accepts_slash_date` fails.
- The failure is intentional and is the starting point for B001.

## Run B001 Manually With A Coding Agent

In the BoardFlow condition, open the initialized workspace, give the agent task `B001`, and require the reading order from its injected `AGENTS.md`:

1. `AGENTS.md`
2. `AI_CONTRACT.md`
3. `PROJECT_BOARD.md`
4. `.board/tasks.yaml`
5. `.board/assigned_task.yaml`
6. latest relevant handoff under `.board/handoffs/`

The agent should only modify the allowed paths listed in `.board/assigned_task.yaml`. It should not change public parser function names or unrelated modules.

Before stopping, the agent should update the board state and write a structured handoff if the scenario requires it.

The runner performs the blocking finalize gate and activates the next sticker only after acceptance evidence and a valid handoff exist.

## Compare Conditions Later

For the no-board baseline, initialize the same standalone seed without BoardFlow injection and provide only the task prompt and demo repo files needed for B001. Do not provide BoardFlow state files or previous handoffs.

For the full BoardFlow condition, provide the observable repo state and require the agent to use BoardFlow files. Compare:

- whether the agent identifies the same failing test,
- whether it stays within allowed paths,
- whether it records validation honestly,
- whether it leaves temporary files behind,
- whether board and handoff state remain consistent.
