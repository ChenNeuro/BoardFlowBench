# Raw Agent-MD Prompt Experiment 20260604-113222

## Purpose

This run restarts the comparison with two custom human prompts:

- Full BoardFlow prompt explicitly asks the agent to read `AGENTS.md`, `AI_CONTRACT.md`, `PROJECT_BOARD.md`, `.board/tasks.yaml`, and `.board/assigned_task.yaml`.
- No-board prompt treats the workspace as a normal code repository and does not mention BoardFlow files.

This run preserves all agent-created residue. Cache files, egg-info, temporary fixtures, and out-of-scope files are counted as part of the raw result.

## Contamination Control

The run used a sanitized seed-only source repository:

```text
/private/tmp/ExpenseLiteBenchDemoSeedOnly-rawagent-20260604-113222
```

Visible refs:

```text
main -> 30ce6f0d76e2338e56d599fd2beb6fe954b96452
benchmark-seed-v1 -> 30ce6f0d76e2338e56d599fd2beb6fe954b96452
```

`reference-history` was not exposed.

## Run Paths

| Item | Path |
| --- | --- |
| Full workspace | `/private/tmp/boardflowbench-rawagent-full-rawagent-20260604-113222/workspace` |
| No-board workspace | `/private/tmp/boardflowbench-rawagent-noboard-rawagent-20260604-113222/workspace` |
| Results root | `/private/tmp/boardflowbench-rawagent-results-rawagent-20260604-113222` |
| Full run manifest | `/private/tmp/boardflowbench-rawagent-results-rawagent-20260604-113222/expense_lite-full_boardflow-1780543961446214000/run.json` |
| No-board run manifest | `/private/tmp/boardflowbench-rawagent-results-rawagent-20260604-113222/expense_lite-no_board_baseline-1780543961352691000/run.json` |

## Prompt Design

### Full BoardFlow Prompt

```text
请先理解这个仓库里的 agent 工作规则，然后开始完成当前任务。

具体步骤：
1. 先阅读 AGENTS.md。
2. 再阅读 AI_CONTRACT.md。
3. 再阅读 PROJECT_BOARD.md 和 .board/tasks.yaml。
4. 阅读 .board/assigned_task.yaml，确认当前任务、allowed_paths、acceptance commands 和 handoff 要求。
5. 如果有相关 handoff，也一起阅读。
6. 根据这些仓库内文件判断我们现在做到哪里，然后完成当前应该做的任务。

要求：
- 只完成当前任务，不要提前做后续任务。
- 遵守 allowed_paths。
- 不要把任务标成 DONE；完成后应等待 runner gate 验收。
- 如果需要 handoff，写符合 schema 的完整 JSON handoff，包含真实 PASS commands 和 PASS tests。
- 做完后运行相关测试，说明改了什么、测了什么、还有什么风险。
```

### No-board Prompt

```text
请先仔细阅读这个普通代码仓库，判断现在做到哪里，然后开始完成当前应该做的任务。

具体步骤：
1. 查看仓库根目录和 README。
2. 查看已有源码、测试和数据文件。
3. 先运行相关现有测试，确认当前失败或缺口。
4. 根据仓库内容判断下一个应该完成的功能。

要求：
- 只完成当前任务，不要提前做后续任务。
- 不要创建额外的项目管理文件或流程文件。
- 尽量只改必要的源码和测试。
- 做完后运行相关测试，说明改了什么、测了什么、还有什么风险。
```

## B001 Raw Result

| Condition | Correctness | Hard Gate | Main Failure |
| --- | ---: | ---: | --- |
| Full BoardFlow | PASS | FAIL | Handoff schema contains disallowed `$schema` field |
| No-board | PASS | FAIL | Agent jumped ahead to CSV import and created out-of-scope data fixture/cache residue |

## Full BoardFlow B001

The agent correctly identified the current task as `B001 Date parser`.

Product behavior:

- added `"%Y/%m/%d"` support to `normalize_date`;
- updated the date error message;
- parser tests passed;
- validator regression tests passed;
- hidden B001 oracle passed.

Gate scores:

- board consistency: `10/10`;
- correctness: `50/50`;
- handoff: `11/15`;
- hygiene: `20/20`;
- scope control: `15/15`;
- hard gate: FAIL.

Raw failure:

```text
handoff schema violations: $.$schema is not allowed
```

Interpretation:

Full BoardFlow kept task scope and repository hygiene clean. Its failure was process-schema related: the handoff existed and contained real evidence, but included one unsupported schema metadata field.

## No-board B001

The no-board agent did not align with runner task `B001`.

It reported:

```text
已完成任务 2：添加 CSV import
```

However, B001 correctness still passed because the resulting test suite included B001 behavior and the hidden B001 oracle passed.

Raw changes:

- `src/expense_lite/parser.py`;
- `tests/test_parser.py`;
- `data/sample_expenses.csv`.

Gate scores:

- correctness: `50/50`;
- hygiene: `15/20`;
- scope control: `7/15`;
- hard gate: FAIL.

Raw failures:

```text
cache or temp files found: .pytest_cache, tests/__pycache__, tests/__pycache__/test_parser.cpython-311-pytest-8.3.4.pyc, tests/__pycache__/test_validator.cpython-311-pytest-8.3.4.pyc
unexpected untracked files found: data/sample_expenses.csv
changed files outside allowed_paths: data/sample_expenses.csv
```

Interpretation:

No-board produced useful code, but it inferred the wrong current task and overreached into B002. The extra CSV fixture and cache files are counted as part of the raw agent behavior.

## Comparison

| Dimension | Full BoardFlow | No-board |
| --- | --- | --- |
| Identified current task | Yes, B001 | No, jumped to task 2 |
| B001 hidden oracle | PASS | PASS |
| Stayed in scope | Yes | No |
| Handoff/state trace | Present, schema-invalid | None |
| Cache/temporary residue | None blocking | Present |
| Raw hard gate | FAIL | FAIL |

## Interpretation

This run supports a more precise claim:

> When the full prompt explicitly asks the agent to read repo-local BoardFlow files, the agent aligns better with the current task and scope. No-board can still pass product checks, but it is more likely to infer the wrong next task and leave unstructured residue.

It also shows a remaining BoardFlow weakness:

> Having a handoff requirement is not enough. The handoff writer or agent guidance must prevent schema drift such as adding unsupported `$schema` fields.

## Next Step

For a fair raw continuation, do not clean either workspace. The next action should be a repair prompt that reports the raw gate failures:

- Full BoardFlow should remove the unsupported handoff field while preserving the B001 code.
- No-board should recognize it overreached, but its raw B001 run should remain recorded as failed because of scope and hygiene.
