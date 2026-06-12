# Human-Realistic Prompt Experiment

## Goal

Run a second comparison using lower-quality, human-realistic prompts.

The question is different from the high-control classroom run:

> Can BoardFlow reduce dependence on a perfectly written prompt?

## Controlled Variable

Both conditions receive the same user prompt for each task.

The only intended treatment difference:

- `full_boardflow`: workspace contains `AGENTS.md`, `AI_CONTRACT.md`, `PROJECT_BOARD.md`, `.board/`, handoffs, and context.
- `no_board_baseline`: workspace contains only the demo repository code and normal tests.

## Prompt Quality

These prompts intentionally do not include:

- allowed paths;
- exact public API names;
- handoff schema details;
- deterministic oracle details;
- exact hidden CLI/report contracts;
- full acceptance criteria.

The prompt asks the agent to inspect the repository and continue the next task, which is closer to a real user interaction.

## Task Scope For This Run

Run only:

- `B001 Date parser`
- `B002 CSV import`
- `B003 Monthly summary`

Stop after both runs reach `B004 awaiting_agent`.

## Shared Prompt Rule

For each task, use the same prompt text in both workspaces.

Do not add condition-specific instructions such as:

- "read `.board/tasks.yaml`" only for full;
- "do not create BoardFlow files" only for no-board;
- exact oracle feedback before the gate has failed.

Fair wording:

```text
先看看这个仓库里的说明文件和测试。继续做当前任务。
如果仓库里有项目规则或任务板，就按它来；如果没有，就按代码和测试推断。
不要大改无关文件。做完后跑相关测试，告诉我改了什么。
```

## Success Measures

Compare:

- final pass rate for B001-B003;
- repair count;
- scope drift count;
- handoff violation count;
- board consistency violation count;
- files changed per stage;
- whether the agent discovered repo-local instructions on its own.

## Expected Interpretation

If both conditions pass, BoardFlow may still show advantage through traceability and fewer process violations.

If no-board fails more often or needs more repair, that supports the stronger claim:

> BoardFlow lowers prompt-quality dependence by moving task context into repo-local control-plane files.
