# Clean Restart B001-B002 Failure Report

## Summary

This report records the clean restart comparison run created after the earlier workspaces were considered polluted.

The new run used a sanitized seed-only source repository, so the demo answer history was not visible through Git refs or objects.

Both conditions used the same low-quality human-realistic prompt:

```text
仔细阅读仓库，看看我们做到哪里了。然后继续当前应该做的任务。

不要急着改代码，先根据仓库里的说明、任务板、测试和已有文件判断当前状态。
如果发现有项目规则、任务板、交接记录或当前任务说明，请按它们执行。
做完后跑相关测试，说明你改了什么、测了什么、还有什么风险。
```

## Run Paths

| Item | Path |
| --- | --- |
| Sanitized source | `/private/tmp/ExpenseLiteBenchDemoSeedOnly-clean-20260604-104631` |
| Full BoardFlow workspace | `/private/tmp/boardflowbench-clean-full-clean-20260604-104631/workspace` |
| No-board workspace | `/private/tmp/boardflowbench-clean-noboard-clean-20260604-104631/workspace` |
| Results root | `/private/tmp/boardflowbench-clean-results-clean-20260604-104631` |
| Full run manifest | `/private/tmp/boardflowbench-clean-results-clean-20260604-104631/expense_lite-full_boardflow-1780541210735430000/run.json` |
| No-board run manifest | `/private/tmp/boardflowbench-clean-results-clean-20260604-104631/expense_lite-no_board_baseline-1780541210749172000/run.json` |

## Contamination Controls

The sanitized source kept only:

- `main` at seed commit `30ce6f0d76e2338e56d599fd2beb6fe954b96452`;
- tag `benchmark-seed-v1` at the same seed commit.

Checks performed:

- `reference-history` was not present in `git branch -a` or `git show-ref`;
- the reference implementation commit object was not available through `git cat-file`;
- no-board workspace had no `AGENTS.md`, `AI_CONTRACT.md`, `PROJECT_BOARD.md`, or `.board/`;
- Claude Code was started with one-shot `claude -p`, not reused interactive sessions.

## Result Overview

| Task | Full BoardFlow | No-board |
| --- | --- | --- |
| B001 Date parser | PASS | PASS |
| B002 CSV import | FAIL | FAIL |

The important result is not that one side won B002. Both failed. The useful signal is what kind of failure each condition made observable.

## B001

Both conditions implemented the same minimal fix:

- add `%Y/%m/%d` support to `normalize_date`;
- keep existing `YYYY-MM-DD` behavior;
- pass parser and validator tests;
- pass hidden oracle.

### Full BoardFlow

Final gate result:

- correctness: `50/50`;
- handoff: `15/15`;
- hygiene: `20/20`;
- scope control: `15/15`;
- board consistency: `10/10`;
- hard gate: PASS.

The agent initially marked B001 `DONE` before runner evidence existed. That was a process mistake. The control plane caught it because `DONE` requires gate evidence. After setting the task back to `READY_FOR_REVIEW`, the runner generated trusted evidence and finalized B001.

### No-board

Final gate result:

- correctness: `50/50`;
- hygiene: `20/20`;
- scope control: `15/15`;
- hard gate: PASS.

No-board produced a clean code-only fix. It had no taskboard, handoff, or state inheritance requirement.

## B002 Failure

Both agents misunderstood the CSV import contract.

The hidden oracle expected CSV import to:

- read `date`, `description`, `category`, and `amount`;
- normalize slash dates through existing date parsing;
- strip text fields through existing validation;
- convert `amount` to a number;
- raise `ValueError` containing `missing required CSV columns` for malformed CSV headers.

Both implementations returned raw CSV values instead of validated expense records.

## Full BoardFlow Problems

Full BoardFlow failed B002 for both product and process reasons.

### Product Bug

The implementation read CSV rows but did not reuse `validate_expense`.

Observed oracle mismatch:

- returned date: `2026/01/03`;
- expected date: `2026-01-03`;
- returned description: ` Notebook `;
- expected description: `Notebook`;
- returned category: ` office `;
- expected category: `office`;
- returned amount: `"12.50"`;
- expected amount: `12.5`.

This is a real correctness failure. The task instructions and BoardFlow task spec were not enough to force the agent to reuse the validator.

### Scope Drift

The agent created CSV fixture files under `data/`:

- `data/sample_expenses.csv`;
- `data/bad_expenses.csv`;
- `data/empty_expenses.csv`.

Those paths were not in B002 `allowed_paths`, so scope control failed:

```text
changed files outside allowed_paths: data/bad_expenses.csv, data/empty_expenses.csv, data/sample_expenses.csv
```

This is useful because the framework identified the exact out-of-scope files.

### Invalid Handoff

The agent wrote a handoff, but it did not match the schema:

- `temporary_files_created` was missing;
- `temporary_files_removed` was missing;
- `files_created` was not allowed.

This shows a partial benefit and a remaining weakness. BoardFlow encouraged the agent to create a handoff, but the agent still needed deterministic schema validation.

### Premature DONE

The agent marked B002 as `DONE` and pointed `acceptance_evidence` at `.board/evidence/B002.json`, but that file did not exist.

The board gate caught this:

```text
B002 acceptance evidence mirror is unreadable
```

This is one of the strongest signals for BoardFlow: task state can be audited, and false completion claims are rejected.

## No-board Problems

No-board failed B002 more quietly.

### Product Bug

The implementation also returned raw CSV values instead of normalized validated records.

It failed the same core oracle expectation:

- date was not normalized;
- whitespace was not stripped;
- amount stayed a string;
- missing-column error message did not match the required contract.

### Missing Tests

The agent explicitly reported that it did not add CSV unit tests.

That mattered. Existing visible tests still passed, but they did not cover the new CSV behavior. The failure was only exposed by the hidden oracle.

### Hygiene Residue

The workspace contained generated cache files:

- `.pytest_cache`;
- `src/expense_lite/__pycache__/`;
- `tests/__pycache__/`.

This is a minor process issue, but it shows a common no-board failure mode: the agent has fewer repository-level cleanup expectations.

### Less State Trace

No-board did not create taskboard updates or handoffs. That is expected for the condition, but it means the failure is harder to diagnose from repository state alone.

The runner can say the code failed, but the workspace itself does not explain:

- what the agent thought the current task was;
- what commands it claims to have run;
- why it omitted tests;
- what should happen next.

## Comparison

| Dimension | Full BoardFlow | No-board |
| --- | --- | --- |
| B002 correctness | Failed | Failed |
| Reused validator | No | No |
| Added CSV tests | Yes | No |
| Scope drift visible | Yes, exact files reported | Not applicable in this case |
| Handoff available | Yes, but schema-invalid | No |
| Premature completion caught | Yes | No task state exists |
| Cache residue | No blocking cache issue | Cache files found |
| Diagnosis quality | High: board, handoff, scope, evidence failures | Lower: mostly code and oracle failure |

## Interpretation

This run does not prove that BoardFlow makes a weak prompt solve the task correctly on the first attempt.

It does show that BoardFlow changes the failure shape:

- Full BoardFlow made the agent produce more process artifacts.
- The artifacts were imperfect, but they gave the gate more surfaces to inspect.
- False `DONE`, missing evidence, schema-invalid handoff, and out-of-scope files were all detected deterministically.
- No-board failed with less trace. It had fewer process violations because it had fewer process obligations, not because the workflow was healthier.

The honest claim for the classroom demo is:

> Under a human-realistic weak prompt, both agents can still make product mistakes. BoardFlow's advantage is that mistakes become structured, auditable, and repairable instead of hidden inside a code-only diff.

## Next Step

The next experiment step should be a repair round.

Use only the deterministic gate feedback as the next prompt input, then compare:

- whether each condition repairs B002 correctly;
- how many repair rounds are needed;
- whether Full BoardFlow fixes board and handoff state together with code;
- whether No-board continues to rely only on code-level changes.

## Repair Round 1

Both conditions received the same repair prompt. The prompt summarized deterministic gate feedback without exposing oracle source paths or answer implementation.

### Shared Repair Prompt

```text
继续当前任务。请先仔细阅读当前仓库状态、测试、任务说明和已有实现，然后修复 B002 CSV import。

上一轮 deterministic gate 反馈显示 B002 还没有通过。请只修 B002，不要做 B003/B004。

需要修复的核心问题：
- CSV import 不能返回 raw CSV 字符串。
- 必须复用已有 validate_expense / normalize_date 逻辑，让返回记录和 validate_expense 的输出一致。
- date 要规范化为 YYYY-MM-DD。
- description/category 要按现有验证逻辑处理空白。
- amount 要变成数字，不要保留字符串。
- 缺少必需 CSV columns 时，ValueError 信息需要包含 `missing required CSV columns`。
- 添加或修正聚焦的 CSV tests。
- 清理测试产生的缓存文件和临时文件。

如果这个 workspace 有 BoardFlow 文件：
- 遵守 .board/assigned_task.yaml 的 allowed_paths。
- 不要新增 data/ 下的测试 fixture；如已有这类 B002 临时 fixture，请移除或改为测试内临时文件。
- 不要把 B002 标成 DONE；完成后应为 READY_FOR_REVIEW，等待 runner gate 生成 evidence。
- handoff 必须符合 .board/handoff.schema.json，包含真实 PASS commands 和 PASS tests。
- 不要伪造 .board/evidence/B002.json。

如果这个 workspace 没有 BoardFlow 文件：
- 不要创建 AGENTS.md、AI_CONTRACT.md、PROJECT_BOARD.md 或 .board/。
- 只做代码和必要测试修复。

完成后运行相关 parser 和 validator 测试，并在最终回复中说明改了什么、跑了什么、还有什么风险。
```

### Repair Result

| Dimension | Full BoardFlow | No-board |
| --- | --- | --- |
| Correctness after repair | PASS | PASS |
| Hard gate after repair | FAIL | FAIL |
| Remaining blocker | Handoff schema, scope drift, cache/untracked files | Cache files only |
| Used `validate_expense` | No, duplicated validator behavior in `_validate_expense` | Yes |
| Added focused tests | Yes | Yes |
| Removed out-of-scope CSV fixtures | No | Not applicable |
| Board state | Required control normalization before scorer could run | Not applicable |

### Full BoardFlow Repair Problems

The full run fixed the visible product behavior enough for correctness to pass, but it still failed the hard gate.

Scores after control-normalizing the inconsistent board state:

- board consistency: `10/10`;
- correctness: `20/20`;
- handoff: `11/15`;
- hygiene: `15/20`;
- scope control: `7/15`;
- hard gate: FAIL.

Remaining issues:

- handoff still contained non-schema field `files_created`;
- `data/*.csv` fixtures were still present outside `allowed_paths`;
- `src/expense_lite.egg-info/` was left in the workspace;
- cache files were left in the workspace;
- implementation introduced `_validate_expense`, duplicating validator behavior instead of reusing `validate_expense`.

This is a useful negative finding. Even when the prompt explicitly said not to add `data/` fixtures and to reuse validator logic, the full agent retained those mistakes. BoardFlow did not prevent the mistake, but the gate made the remaining violations exact and auditable.

### No-board Repair Problems

The no-board run fixed the product behavior more directly.

Scores:

- correctness: `20/20`;
- scope control: `15/15`;
- hygiene: `17/20`;
- hard gate: FAIL.

Remaining issue:

- generated cache directories remained: `src/expense_lite/__pycache__` and `tests/__pycache__`.

No-board used `validate_expense` and added temp-file based CSV tests. It still lacked process trace, but the code repair was cleaner than the full run in this round.

### Updated Interpretation

The repair round weakens any simplistic claim that BoardFlow always produces cleaner code.

The better claim is narrower and more defensible:

> BoardFlow provides a control plane that exposes process, scope, handoff, and evidence failures. It does not guarantee that an agent will follow those controls without deterministic gates and repair loops.

For a classroom demo, this is stronger than a polished success-only story:

- B001 shows both conditions can solve a simple task.
- B002 initial failure shows weak prompts are not enough.
- Repair round 1 shows no-board can sometimes produce the cleaner code repair.
- Full BoardFlow still gives a richer failure report: exact bad handoff field, exact out-of-scope files, exact stale evidence/state problems.
