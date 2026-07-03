# RepoFlow Rigorous Evaluation Plan

Date: 2026-07-03

This document evaluates RepoFlow as a repository-level scaffolding layer for
coding-agent collaboration. It is deliberately skeptical: it states what the
design can claim now, what remains unproven, what experiments can falsify the
claims, and how to spend large agent-token budgets productively.

## 1. Positioning

RepoFlow is not a complete coding-agent harness. A complete harness usually
owns model calls, tool routing, editing, shell execution, permission prompts,
context-window management, and sometimes cloud execution. Codex, Claude Code,
OpenCode, and Copilot already do much of that.

RepoFlow is instead a **repository-level coordination scaffold**:

- it lives inside or near a Git repository;
- it exposes task state, dependencies, handoffs, and evidence to fresh agents;
- it compiles repository-local state into task-conditioned context packets;
- it binds progress claims to observable evidence;
- it lets an external gate decide whether a stage is accepted.

The right claim is therefore:

> RepoFlow improves the repository interface for sequential coding-agent
> handoff.

The wrong claim is:

> RepoFlow is a better coding agent or a complete replacement for existing
> coding-agent harnesses.

## 2. Claims Ladder

RepoFlow claims should be separated by evidentiary strength.

### Claim A: Engineering Plausibility

Current status: supported by design and existing implementation.

RepoFlow can maintain repository-local task state, structured handoffs, scope
checks, and deterministic acceptance evidence for a sequential benchmark.

Evidence already present:

- `.board/tasks.yaml` and `PROJECT_BOARD.md` for task state;
- `.board/handoff.schema.json` and handoff validation;
- `repo_manager_core/benchmark/runner.py` for staged lifecycle;
- `repo_manager_core/benchmark/finalize.py` for deterministic finalization;
- `repo_manager_core/board/evidence.py` for acceptance-evidence validation;
- `repo_manager_core/benchmark/aggregation.py` for signed-result aggregation;
- existing scenarios for full board, native instructions, native docs handoff,
  and no-board baseline.

### Claim B: Better Observability

Current status: partially supported.

RepoFlow should make failures easier to diagnose than no-board or free-form
handoff baselines because it records task state, scope, handoff, and gate
results.

Evidence required:

- compare failure reports across conditions;
- measure how quickly a human reviewer can identify the failing task, changed
  files, missing evidence, or scope violation;
- show that invalid handoffs and missing tests are surfaced automatically.

### Claim C: Better Sequential Continuity

Current status: unproven.

RepoFlow should reduce downstream context loss, duplicated work, scope drift,
and regression in sequential handoff.

Evidence required:

- repeated mixed-agent runs under the same seed;
- comparison against no-board, native instructions, and native docs handoff;
- metrics that capture reuse of upstream interfaces and risks;
- enough repetitions to distinguish signal from prompt noise.

### Claim D: Context Expansion Is the Key Mechanism

Current status: hypothesis.

The strongest V2 hypothesis is that task-conditioned context packets outperform
plain task boards or handoff notes.

Evidence required:

- add a `repo_expanded_context` condition;
- compare it against `full_boardflow` without context compilation;
- verify that improvements are not merely caused by longer prompts or more
  detailed instructions.

### Claim E: Generality Across Repositories

Current status: unproven.

RepoFlow may work beyond Expense Lite, but this requires new target
repositories.

Evidence required:

- at least one second benchmark target with different file structure and task
  type;
- same conditions, metrics, and gates;
- results that do not depend on Expense Lite-specific affordances.

## 3. Falsifiable Hypotheses

The design should be tested through falsifiable hypotheses.

### H1: Board State Improves Protocol Compliance

Compared with `no_board_baseline`, `full_boardflow` reduces:

- missing handoff records;
- task status inconsistencies;
- out-of-scope modifications;
- unsupported `DONE` claims;
- missing validation records.

Falsification:

- no meaningful reduction across repeated runs;
- failures merely move from code to BoardFlow file manipulation.

### H2: Structured Handoff Improves Downstream Reuse

Compared with `native_docs_handoff`, `full_boardflow` improves downstream
reuse of upstream decisions and interfaces.

Operational measures:

- B002 reuses B001 date parsing rather than creating a second parser;
- B003 consumes B002 imported records rather than re-reading raw files through
  a separate path;
- downstream agents mention or preserve risks from the previous handoff;
- tests from earlier tasks continue to pass.

Falsification:

- downstream agents ignore structured handoffs at the same rate as Markdown
  handoffs;
- structured handoff adds overhead but no continuity gain.

### H3: Context Expansion Beats Static Board Reading

Compared with `full_boardflow`, `repo_expanded_context` improves:

- first-edit correctness;
- relevant-file read coverage before edit;
- preservation of upstream interfaces;
- lower prompt-specific variance.

Falsification:

- compiled context is no better than asking agents to read board files;
- context packet causes overload and more mistakes.

### H4: Deterministic Gates Improve Evidence Honesty

Compared with conditions without blocking gates, gated conditions reduce:

- claimed-but-unobserved validation;
- task completion despite failing tests;
- hidden regression of previous tasks.

Falsification:

- agents can satisfy the gate while still hiding meaningful failures;
- gate failures are mostly false positives caused by protocol brittleness.

### H5: RepoFlow Is Client-Agnostic

RepoFlow should work across at least three different agent clients or models.

Operational sequence:

```text
DeepSeek / B001 -> Codex / B002 -> Claude Code or MiniMax / B003 -> B004 activation
```

Falsification:

- success depends on one client-specific behavior;
- prompts must be rewritten so heavily per agent that the repository protocol
  is not carrying the real state.

## 4. Threat Model

RepoFlow should explicitly define what it defends against.

### In Scope

- honest but forgetful agents;
- agents with no access to previous chat sessions;
- agents that skim instructions and miss task boundaries;
- accidental scope drift;
- accidental duplicate implementation;
- stale or incomplete handoff notes;
- validation claims without sufficient evidence;
- downstream regression after a previous stage.

### Partly In Scope

- agents that overwrite BoardFlow files accidentally;
- agents that misunderstand task dependencies;
- agents that create plausible but shallow handoffs.

These can be mitigated by schema validation, external evidence, and gates, but
not completely eliminated.

### Out of Scope

- malicious agents with arbitrary filesystem access;
- compromised oracle pack or results directory;
- hostile client harnesses;
- secrets exfiltration;
- operating-system sandbox escape;
- formal proof of semantic correctness for arbitrary software changes.

The current implementation correctly keeps benchmark authority outside the
workspace, but a hostile agent still requires an external sandbox.

## 5. Failure Modes to Test Deliberately

Do not only run happy-path demos. Introduce targeted failure cases.

### F1: Missing Handoff

Agent completes code and tests but writes no handoff.

Expected result:

- `full_boardflow` gate fails;
- `no_board_baseline` may still pass correctness but records no handoff.

### F2: False Validation Claim

Agent writes a handoff claiming tests passed without actually passing the
oracle.

Expected result:

- deterministic score rejects completion;
- evidence explains failing command or oracle mismatch.

### F3: Scope Drift

Agent modifies a downstream task file during an upstream stage.

Expected result:

- scope checker reports outside allowed paths;
- task is not finalized.

### F4: Duplicate Interface

B002 reimplements date parsing instead of using B001.

Expected result:

- correctness may still pass;
- continuity metric should detect duplicate implementation or missing reuse.

This is important because not all coordination failures are correctness
failures.

### F5: Stale Context

Agent reads an old handoff even though a newer one exists.

Expected result:

- context compiler index should reveal which handoff was included;
- future gate or reviewer should report stale context risk.

### F6: Future Unknown Feature

Introduce B005 after the run begins.

Expected result:

- existing tasks should not need to predict B005;
- task graph should allow appending B005 without rewriting prior handoffs;
- context compiler should expose B005 only when activated or dependency-relevant.

This directly tests the "repository growth is GPT-like, handoff understanding
is BERT-like" tension.

## 6. Experimental Conditions

Minimum conditions:

| Condition | Visible coordination state | Gate | Purpose |
| --- | --- | --- | --- |
| `no_board_baseline` | README, source, tests | oracle only | ordinary repository baseline |
| `native_instructions` | client-native instruction file | oracle only | instruction-file baseline |
| `native_docs_handoff` | Markdown board and Markdown handoff | deterministic gate | human-readable coordination |
| `full_boardflow` | `.board/`, schema handoff, evidence mirror | deterministic gate | current protocol |
| `repo_expanded_context` | compiled task context plus supporting files | deterministic gate | V2 context hypothesis |

The key comparison is not only `full_boardflow` versus `no_board_baseline`.
The more rigorous comparison is:

```text
no shared state
  -> native instructions
  -> human-readable handoff
  -> machine-readable board and handoff
  -> compiled context packet
```

This isolates which scaffold component actually helps.

## 7. Metrics

### Primary Metrics

Use these for main claims:

- stage acceptance rate;
- full-run completion rate;
- regression count;
- scope drift count;
- handoff violation count;
- board consistency violation count;
- evidence violation count.

These are mostly already supported by the scorer and aggregator.

### Secondary Metrics

Use these to understand mechanism:

- downstream interface reuse;
- duplicate implementation count;
- stale handoff use;
- risk propagation from one task to the next;
- first failing stage;
- repair attempts required;
- token and wall-clock cost.

Some of these need new instrumentation or manual annotation.

### Context Metrics

Needed for the V2 context compiler:

- generated context packet size;
- number of source artifacts included;
- number of handoffs included;
- index of excluded artifacts and exclusion reason;
- whether required upstream handoff is present;
- whether downstream hidden tasks are excluded.

### Human Review Metrics

Optional but valuable:

- time for a reviewer to identify current state;
- time to identify the first failure cause;
- reviewer confidence score;
- number of files reviewer must open.

## 8. Measurement Quality

### Construct Validity

Risk:

- "handoff quality" may become a proxy for filling required fields rather than
  true continuity.

Mitigation:

- add downstream reuse metrics;
- bind claims to changed files and tests;
- include manual annotations for duplicate implementation and risk propagation.

### Internal Validity

Risk:

- prompt wording, model differences, and client defaults may explain results.

Mitigation:

- same seed commit;
- same task sequence;
- same oracle pack;
- prompt templates with only condition-specific differences;
- rotate agent order in a secondary experiment;
- record model, client version, and command.

### External Validity

Risk:

- Expense Lite may be too small or too tailored to RepoFlow.

Mitigation:

- add a second target repository;
- include at least one task with documentation, one with parsing, one with
  stateful behavior, and one with artifact generation.

### Statistical Conclusion Validity

Risk:

- small sample sizes make strong statistical claims invalid.

Mitigation:

- report as exploratory until there are enough runs;
- use exact counts and confidence intervals rather than overclaiming;
- preregister primary metrics before large runs;
- report failed runs, not only successful demos.

## 9. MiniMax Token Budget Use

Unlimited MiniMax tokens should be spent on repeated controlled runs, not on
one giant unconstrained run.

Credential setup and a direct API smoke test are documented in
`docs/MINIMAX_TESTING_RUNBOOK.md`.

DeepSeek-first testing is documented in `docs/DEEPSEEK_TESTING_RUNBOOK.md`.

Recommended first batch:

```text
Target: expense_lite
Tasks: B001 -> B002 -> B003 -> B004
Agents: MiniMax only
Conditions: no_board_baseline, native_docs_handoff, full_boardflow
Repetitions: 5 per condition
Total runs: 15
```

Why MiniMax-only first:

- controls for model identity;
- tests whether the scaffold helps the same model under different visible
  repository state;
- avoids confounding from DeepSeek/Codex/Claude differences.

Recommended second batch:

```text
Target: expense_lite
Tasks: B001 -> B002 -> B003 -> B004
Agents: DeepSeek -> Codex -> MiniMax
Conditions: no_board_baseline, full_boardflow, repo_expanded_context
Repetitions: 5 per condition
Total runs: 15
```

Why mixed-agent second:

- tests the real handoff problem;
- isolates whether repository state survives client/model switching.

Recommended adversarial batch:

```text
Target: expense_lite
Failure injections: missing handoff, false validation, scope drift, duplicate interface
Conditions: full_boardflow, repo_expanded_context
Repetitions: 3 per failure per condition
Total runs: 24
```

Goal:

- verify that gates catch the failures they are supposed to catch;
- reveal failures that only manual review can catch.

## 10. Prompt Control

Prompts should differ only by condition.

### Full BoardFlow Prompt Skeleton

```text
You are a fresh coding agent for task {task_id}.

Read and follow AGENTS.md, AI_CONTRACT.md, PROJECT_BOARD.md,
.board/tasks.yaml, .board/assigned_task.yaml, and the latest relevant handoff.

Only complete {task_id}. Stay within allowed_paths. Update the task to
IN_PROGRESS before editing and READY_FOR_REVIEW after validation. Do not mark
DONE. Run acceptance and regression commands. Write a valid handoff.
```

### No-Board Prompt Skeleton

```text
You are a fresh coding agent for task {task_id}.

Read README.md, then inspect the relevant source and tests. Only complete
{task_id}. Do not create BoardFlow files, task boards, or handoffs. Run relevant
tests and report changed files and results.
```

### Repo-Expanded Prompt Skeleton

```text
You are a fresh coding agent for task {task_id}.

Start by reading .repo_manager/agent_context.md and the source files listed in
.repo_manager/agent_context_index.json. Treat that context packet as the
repository-level scaffold for this task. Only complete {task_id}. Follow the
allowed paths, validation commands, and handoff requirements specified there.
```

## 11. Minimal Implementation Gaps

The current implementation is strong enough for `full_boardflow`, but not yet
for the full V2 claim.

Needed:

1. `repo_expanded_context` scenario condition.
2. Deterministic context compiler.
3. Context packet index with included and excluded sources.
4. Tests for context determinism.
5. Instrumentation for interface reuse and duplicate implementation.
6. Result aggregation fields for context metrics.
7. A clearer distinction between repository scaffold output and external gate
   authority.

## 12. Acceptance Criteria for the Design Itself

RepoFlow V2 should not be considered validated until it meets these criteria.

### Engineering Criteria

- context compiler is deterministic;
- context packet is task-conditioned;
- downstream hidden tasks are not leaked;
- handoff schema rejects empty validation;
- gate rejects missing handoff, scope drift, and failing oracle;
- aggregation rejects tampered evidence.

### Research Criteria

- at least three conditions compared;
- at least five repeated runs per condition for pilot claims;
- all failed runs reported;
- primary metrics declared before running the batch;
- model/client versions recorded;
- no claim of statistical significance unless supported.

### Practical Criteria

- setup is not harder than ordinary agent-client setup;
- users can inspect the scaffold files without custom UI;
- an agent can start from repository state alone;
- a human reviewer can diagnose a failure from artifacts.

## 13. Interpretation Rules

Use these rules when writing the paper or README.

If RepoFlow improves correctness and coordination:

- claim that repository-level scaffolding improved sequential handoff in this
  benchmark;
- still avoid claiming model-independent generality without more targets.

If RepoFlow improves coordination but not correctness:

- claim it improves observability and discipline, not task success.

If RepoFlow improves correctness but not coordination metrics:

- suspect prompt confounding or oracle alignment; inspect traces manually.

If RepoFlow fails to improve:

- reduce the protocol;
- identify which component added overhead;
- preserve the negative result because it is scientifically useful.

## 14. Immediate Next Step

Before spending MiniMax tokens, implement the `repo_expanded_context` prototype
or at least freeze the current three-condition protocol:

```text
no_board_baseline
native_docs_handoff
full_boardflow
```

Then run a MiniMax-only pilot with five repetitions per condition. That is the
cleanest first test of whether repository-level scaffolding helps beyond model
capability.
