# Experiment Protocol

This file defines the BoardFlowBench experiment flow for standalone demo workspaces.

## Condition 1: No-Board Baseline

In `no_board_baseline`, initialize a temporary clone of the fixed demo seed without injecting BoardFlow files. The agent receives only the assigned task prompt and demo repository state.

The agent must not use:

- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- `.board/handoffs/*.json`
- `AGENTS.md`
- `AI_CONTRACT.md`

This condition measures how much context continuity is available without repo-local shared state.

## Condition 2: Native Instructions

In `native_instructions`, inject only the repository instruction file native to the selected agent profile, such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.

## Condition 3: Native Docs Handoff

In `native_docs_handoff`, inject the native instruction file plus human-readable `PROJECT_BOARD.md` and `HANDOFF.md`. Do not inject `.board/`.

## Condition 4: Full BoardFlow

In `full_boardflow`, initialize a temporary clone of the fixed demo seed with run-local BoardFlow files. `boardflow_sequential` remains a compatibility alias. Each agent uses the injected reading order from `AGENTS.md`, works on one assigned B-series task, updates run-local board state, and writes a structured handoff.

The observable repo state is the source of truth. Previous chat transcripts are not part of the handoff.

Workspace `.board/run.yaml` and `.board/evidence/*.json` files are readable mirrors, not acceptance authority. The runner stores a signed `run.json`, trusted score files, and trusted evidence outside the workspace.

## Agent A Responsibilities

Agent A starts a task from the assigned benchmark task YAML.

Agent A should:

- read BoardFlow files in the required order,
- confirm milestone, task, dependencies, allowed paths, and acceptance commands,
- update the task to `IN_PROGRESS` when work begins,
- modify only allowed files,
- run relevant acceptance commands when possible,
- update task status before stopping,
- write a handoff JSON if the scenario requires handoff.

## Agent B Allowed Reading

Agent B may read only observable repo state:

- `AGENTS.md`
- `AI_CONTRACT.md`
- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- assigned benchmark task YAML
- latest relevant `.board/handoffs/*.json`
- files in the demo repo needed for the assigned task

Agent B must not rely on Agent A's chat transcript or private notes.

## Reviewer Checks

The Reviewer checks whether the run followed the protocol.

Reviewer checks include:

- board and machine-readable task state agree,
- task statuses use only allowed values,
- dependencies were respected,
- files changed are within allowed paths or exceptions are recorded,
- handoff JSON matches `.board/handoff.schema.json`,
- commands and tests are recorded honestly,
- temporary files were removed or recorded,
- no forbidden root scratch files were created.

## Observable Artifacts Used For Scoring

Scoring should use only observable artifacts:

- git diff and file tree
- `PROJECT_BOARD.md`
- `.board/tasks.yaml`
- `.board/handoffs/*.json`
- assigned `benchmark/tasks/*.yaml`
- command and test records inside handoff files
- external scorer, evidence, and reviewer outputs under the selected results directory

## Workspace Initialization

```bash
PYTHONPATH=. python3 scripts/init_benchmark_workspace.py \
  --target expense_lite \
  --condition full_boardflow \
  --task-id B001 \
  --workspace /tmp/boardflowbench-runs/run-001
```

The runner activates future task details only after deterministic acceptance. This command is limited to recovering a runner-authored signed activation transition:

```bash
PYTHONPATH=. python3 scripts/activate_benchmark_task.py \
  --run-manifest /tmp/boardflowbench-results/<run-id>/run.json
```

## Scenario Runner

```bash
PYTHONPATH=. python3 scripts/run_scenario.py \
  --target expense_lite \
  --condition full_boardflow \
  --workspace /tmp/boardflowbench-runs/run-001 \
  --oracle-root ../ExpenseLiteBenchOracles \
  --results-dir /tmp/boardflowbench-results
```

The runner validates the seed, requires a clean oracle pack at the target manifest's fixed commit, calls start and end refresh around each full-BoardFlow sticker, stores results outside the workspace, and stops when a deterministic finalize gate fails. The oracle pack and results directory must both stay outside the workspace. An optional reviewer command can publish non-blocking qualitative risks after acceptance, but it must not modify the finalized workspace or trusted control-plane files.

Use the runner for the complete lifecycle. Direct workspace initialization is for injection-boundary checks. HMAC signatures prevent workspace-local forgery; hostile agent commands still require an external OS sandbox.

Executable adapter commands are not persisted in signed manifests. Operators pass `--reviewer-command` again when resuming a manual checkpoint. Reviewer adapters are operator-trusted only: the runner hashes the key, signed manifest, score, and evidence before and after review, but hostile reviewers still require an external OS sandbox.

## Terms

- `seed`: the fixed starting commit cloned before an experiment begins. It contains the initial platform and an intentional task gap, not the reference answer.
- `scope`: the file boundary assigned to one sticker. The scorer compares the sticker baseline commit with the evaluated workspace and reports changes outside `allowed_paths`.
