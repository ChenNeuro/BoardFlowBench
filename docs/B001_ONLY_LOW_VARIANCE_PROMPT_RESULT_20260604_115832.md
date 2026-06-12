# B001-Only Low-Variance Prompt Result 20260604-115832

## Purpose

This run controls prompt variance more tightly than the previous raw prompt experiment.

Only the reading order differs:

- Full BoardFlow reads BoardFlow control-plane files.
- No-board reads ordinary repository files.

The task requirements are otherwise identical.

No agent-generated residue was cleaned before scoring.

## Run Paths

| Item | Path |
| --- | --- |
| Full workspace | `/private/tmp/boardflowbench-b001only-full-b001only-20260604-115832/workspace` |
| No-board workspace | `/private/tmp/boardflowbench-b001only-noboard-b001only-20260604-115832/workspace` |
| Results root | `/private/tmp/boardflowbench-b001only-results-b001only-20260604-115832` |
| Full run manifest | `/private/tmp/boardflowbench-b001only-results-b001only-20260604-115832/expense_lite-full_boardflow-1780545529978972000/run.json` |
| No-board run manifest | `/private/tmp/boardflowbench-b001only-results-b001only-20260604-115832/expense_lite-no_board_baseline-1780545529862354000/run.json` |

## Prompts

### Full BoardFlow

```text
请先阅读并遵循这个仓库中的项目说明文件，然后开始完成当前任务。

阅读顺序：
1. AGENTS.md
2. AI_CONTRACT.md
3. PROJECT_BOARD.md
4. .board/tasks.yaml
5. .board/assigned_task.yaml
6. 如果 .board/handoffs/ 下有当前任务相关 handoff，也一起阅读

任务要求：
- 根据仓库内说明判断当前应该完成的任务。
- 遵循仓库要求、任务说明、测试要求和已有代码风格。
- 只完成当前任务，不要提前做后续任务。
- 不要创建无关文件。
- 尽量只改必要的源码和测试。
- 做完后运行相关测试。
- 最后说明你改了什么、运行了什么测试、还有什么风险。
```

### No-board

```text
请先阅读并遵循这个仓库中的项目说明文件，然后开始完成当前任务。

阅读顺序：
1. README.md
2. pyproject.toml
3. src/
4. tests/
5. data/

任务要求：
- 根据仓库内说明判断当前应该完成的任务。
- 遵循仓库要求、任务说明、测试要求和已有代码风格。
- 只完成当前任务，不要提前做后续任务。
- 不要创建无关文件。
- 尽量只改必要的源码和测试。
- 做完后运行相关测试。
- 最后说明你改了什么、运行了什么测试、还有什么风险。
```

## B001 Result

| Condition | Correctness | Hard Gate | Primary Failure |
| --- | ---: | ---: | --- |
| Full BoardFlow | PASS | FAIL | Task marked `DONE` without runner acceptance evidence |
| No-board | PASS | FAIL | Cache and `src/expense_lite.egg-info/` residue |

## Full BoardFlow

The agent correctly completed B001:

- added `"%Y/%m/%d"` to the date format loop;
- updated the parser error message;
- ran parser tests and validator regression tests;
- created a valid handoff.

Scores:

- board consistency: `7/10`;
- correctness: `50/50`;
- handoff: `15/15`;
- hygiene: `20/20`;
- scope control: `15/15`;
- hard gate: FAIL.

Raw failure:

```text
B001 has no acceptance evidence mirror
```

The agent marked the task `DONE`, but the runner had not yet generated trusted acceptance evidence. This is a process-state failure, not a product-code failure.

## No-board

The agent correctly completed the B001 code change:

- changed only `src/expense_lite/parser.py` in the tracked diff;
- hidden oracle passed;
- no taskboard or handoff was expected.

Scores:

- correctness: `50/50`;
- hygiene: `15/20`;
- scope control: `7/15`;
- hard gate: FAIL.

Raw failures:

```text
cache or temp files found: .pytest_cache, src/expense_lite/__pycache__, tests/__pycache__
unexpected untracked files found: src/expense_lite.egg-info/...
changed files outside allowed_paths: src/expense_lite.egg-info/...
```

The product fix is clean, but the workspace contains generated install/test residue.

## Comparison

| Dimension | Full BoardFlow | No-board |
| --- | --- | --- |
| Correct task identified | Yes | Yes |
| Product correctness | PASS | PASS |
| Tracked business-code diff | Minimal | Minimal |
| Handoff | Present and valid | Not applicable |
| Workspace hygiene | Clean | Fails due cache and egg-info |
| Process state | Incorrect `DONE` without evidence | No process state |
| Raw hard gate | FAIL | FAIL |

## Interpretation

With lower prompt variance, both conditions solve B001 correctly.

The difference is in failure type:

- Full BoardFlow exposes a state-machine violation: task status was advanced too far before trusted evidence existed.
- No-board exposes workspace hygiene residue from normal agent/test behavior.

This is a cleaner comparison than the earlier run because No-board no longer jumps to B002. The remaining contrast is control-plane correctness versus workspace cleanliness.
