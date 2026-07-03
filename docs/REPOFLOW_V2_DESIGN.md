# RepoFlow V2 Design

RepoFlow V2 turns the current BoardFlow protocol into a repository-level
scaffolding layer for coding-agent collaboration. The main shift is from "a
task board plus handoff notes" to "a repository-local context representation
that can be expanded, checked, and handed to a fresh agent".

This document is a design draft. It does not change the existing benchmark
runner or project board.

For a broader comparison with OpenAI, Anthropic, GitHub Copilot, OpenCode,
Codex, SWE-agent, OpenHands, Agentless, and related papers, see
`docs/HARNESS_LANDSCAPE_REVIEW.md`.

## 1. Core Thesis

Current coding-agent collaboration often behaves like an autoregressive
continuation process. A later agent sees the latest prompt, some visible files,
and perhaps a natural-language summary, then continues from that narrow slice
of state. This is fragile in sequential work: task boundaries drift, decisions
are repeated, validation evidence disappears, and the next agent cannot always
recover why the repository looks the way it does.

RepoFlow V2 takes a different position:

> The repository should not only be the object modified by agents. It should
> also be the durable context representation from which a fresh agent can
> recover task state, dependency structure, evidence, risks, and acceptance
> boundaries.

In this sense, RepoFlow is closer to a context-expansion scaffold than to a
prompting template. It is intended to sit below client harnesses such as Codex,
Claude Code, OpenCode, and Copilot. The client harness still owns tool calling,
editing, terminal access, permissions, and session management; RepoFlow owns
repository-local state, handoff evidence, context expansion, and the interface
to deterministic gates.

The informal "BERT-like" intuition is useful but should be stated carefully:
RepoFlow does not import BERT or use bidirectional language-model training.
The analogy is that the next agent should read an explicitly expanded context
space rather than merely continue a linear transcript.

## 2. Design Goals

RepoFlow V2 should satisfy six goals.

1. **Fresh-agent recoverability**: a new agent with no chat memory can recover
   current task state from repository-local files and trusted external
   evidence.
2. **Explicit task boundaries**: each task declares dependencies, allowed
   paths, acceptance commands, forbidden actions, and expected handoff fields.
3. **Evidence-first completion**: task completion is based on recorded commands,
   tests, diffs, and deterministic gates, not on the agent claiming completion.
4. **Sequential continuity**: downstream agents inherit upstream interfaces,
   decisions, risks, and validation results without needing private transcripts.
5. **Control-plane separation**: benchmark authority remains outside the mutable
   workspace while the workspace contains readable mirrors for agents.
6. **Low adoption friction**: the protocol remains file-based and can run in
   ordinary Git repositories without requiring a custom IDE or hosted service.

## 3. Non-Goals

RepoFlow V2 does not attempt to solve every multi-agent problem.

- It is not a general parallel-agent scheduler.
- It is not a replacement for Git, CI, issue trackers, or code review.
- It is not a guarantee against hostile agents without an operating-system
  sandbox.
- It is not a claim that more context is always better; the context compiler
  must prioritize relevant and checkable state.
- It is not a model benchmark for raw coding ability. The primary target is
  collaboration discipline under sequential handoff.

## 4. Conceptual Model

RepoFlow V2 has five layers.

```text
+--------------------------------------------------------------+
| Agent-facing context packet                                  |
| task brief, dependencies, prior decisions, evidence, risks    |
+--------------------------------------------------------------+
| Context compiler                                             |
| selects, normalizes, and orders repository-local state        |
+--------------------------------------------------------------+
| Repository-local state                                       |
| task graph, current state, handoffs, event log, evidence      |
+--------------------------------------------------------------+
| Harness control plane                                        |
| activation, scope checks, acceptance gates, signed results    |
+--------------------------------------------------------------+
| Target repository                                            |
| source code, tests, docs, fixtures, generated artifacts       |
+--------------------------------------------------------------+
```

The important distinction is between **readable state** and **trusted
authority**. Agents may read workspace-local state, but final acceptance should
come from deterministic checks controlled by the harness. This keeps the
repository useful to agents while preventing the agent from self-certifying
completion.

## 5. Repository Context Expansion

The central primitive is a context expansion step:

```bash
repoflow context build --task B002 --repo /path/to/workspace
```

The command should emit a stable context packet, for example:

```text
.repoflow/context/B002_agent_context.md
.repoflow/context/B002_index.json
```

The packet is not a generic repository summary. It is a task-conditioned
projection of repository state. For a downstream task, it should include:

- current task id, title, status, owner, dependencies, and allowed paths;
- acceptance commands and expected outputs;
- upstream task completion summaries;
- latest relevant handoff records;
- changed files and public interfaces introduced by upstream tasks;
- validation evidence and failing or skipped checks;
- risks, unresolved questions, and constraints that must not be violated;
- a compact file tree focused on the task's reachable surface;
- a list of files the agent should read before editing.

This creates a stronger alternative to both plain prompts and free-form
handoffs. The agent receives a curated, reproducible context view derived from
observable repository state.

## 6. Proposed File Layout

The current project already uses `.board/` and `.repo_manager/`. RepoFlow V2 can
either extend those directories or introduce `.repoflow/` as the canonical
namespace. A staged migration is preferable:

```text
.repoflow/
  protocol.yaml
  task_graph.yaml
  state/
    current.yaml
    events.jsonl
  tasks/
    B001.yaml
    B002.yaml
  handoffs/
    B001_deepseek.json
    B002_codex.json
  evidence/
    B001/
      commands.jsonl
      tests.json
      diff.patch
      scope.json
    B002/
      commands.jsonl
      tests.json
      diff.patch
      scope.json
  reviews/
    B001_gate.json
    B002_gate.json
  context/
    B002_agent_context.md
    B002_index.json
```

Compatibility mapping:

| Current artifact | V2 artifact | Role |
| --- | --- | --- |
| `.board/tasks.yaml` | `.repoflow/task_graph.yaml` | Task graph and task state |
| `.board/handoffs/*.json` | `.repoflow/handoffs/*.json` | Structured handoff records |
| `.board/evidence/*.json` | `.repoflow/evidence/<task>/` | Commands, tests, diff, scope |
| `.repo_manager/agent_context.md` | `.repoflow/context/<task>_agent_context.md` | Compiled context packet |
| external `run.json` | harness-owned signed manifest | Trusted experiment authority |

The migration should be additive. Existing `.board/` support should remain
available until the benchmark runner, tests, and paper use the same names.

## 7. Task Graph Schema

Task graph state should be explicit enough for both agents and gates:

```yaml
schema_version: 2
project: ExpenseLite
current_task: B002
tasks:
  - id: B001
    title: Date parsing normalization
    status: READY_FOR_REVIEW
    owner: deepseek
    dependencies: []
    allowed_paths:
      - src/expense_lite/dates.py
      - tests/test_dates.py
    acceptance_commands:
      - python -m pytest tests/test_dates.py
    produces:
      - normalized date parser API
    handoff: .repoflow/handoffs/B001_deepseek.json

  - id: B002
    title: CSV import
    status: TODO
    owner: codex
    dependencies:
      - B001
    allowed_paths:
      - src/expense_lite/import_csv.py
      - tests/test_import_csv.py
    acceptance_commands:
      - python -m pytest tests/test_dates.py tests/test_import_csv.py
    consumes:
      - B001.normalized date parser API
```

Important fields:

- `dependencies`: tasks that must be accepted before this task starts;
- `allowed_paths`: scope boundary for implementation;
- `acceptance_commands`: expected validation commands;
- `produces`: interfaces or artifacts created for downstream tasks;
- `consumes`: upstream interfaces or artifacts that must be preserved;
- `handoff`: latest structured handoff for the task.

## 8. Event Log

The event log should be append-only and machine-readable:

```jsonl
{"ts":"2026-07-03T10:00:00Z","type":"task_started","task_id":"B002","agent_id":"codex"}
{"ts":"2026-07-03T10:03:12Z","type":"file_changed","task_id":"B002","path":"src/expense_lite/import_csv.py"}
{"ts":"2026-07-03T10:05:44Z","type":"command_run","task_id":"B002","command":"python -m pytest tests/test_import_csv.py","exit_code":0}
{"ts":"2026-07-03T10:08:01Z","type":"handoff_written","task_id":"B002","path":".repoflow/handoffs/B002_codex.json"}
```

The event log is not a substitute for Git history. It records collaboration
events that are not always visible in commits: commands run, skipped tests,
handoff creation, scope exceptions, and gate decisions.

## 9. Handoff Schema

Handoffs should remain structured JSON. A V2 handoff should answer four
questions:

1. What changed?
2. How was it validated?
3. What must the next agent preserve?
4. What remains risky or unresolved?

Suggested fields:

```json
{
  "schema_version": 2,
  "task_id": "B002",
  "agent_id": "codex",
  "agent_role": "implementation",
  "status": "READY_FOR_REVIEW",
  "summary": "Implemented CSV import using the B001 date parser.",
  "files_changed": [
    "src/expense_lite/import_csv.py",
    "tests/test_import_csv.py"
  ],
  "commands": [
    {
      "command": "python -m pytest tests/test_dates.py tests/test_import_csv.py",
      "exit_code": 0,
      "result": "passed"
    }
  ],
  "interfaces_produced": [
    "load_expenses_csv(path) returns normalized expense records"
  ],
  "interfaces_consumed": [
    "parse_expense_date from B001"
  ],
  "decisions": [
    "Rejected rows with missing amount instead of silently coercing them."
  ],
  "risks": [
    "Large CSV streaming behavior is not benchmarked."
  ],
  "next_recommended_step": "Run B003 monthly summary against imported records."
}
```

The schema should prohibit empty evidence and require explicit statements when
validation is skipped.

## 10. Context Compiler

The context compiler is the main new component in V2. It should build an
ordered packet for the next agent:

```text
1. Current task
2. Non-negotiable protocol rules
3. Dependencies and accepted upstream work
4. Required handoffs and risks
5. Allowed paths and forbidden paths
6. Relevant file tree
7. Suggested files to read
8. Acceptance commands
9. Required handoff fields
```

The compiler should be deterministic. Given the same repository state and task
id, it should produce the same packet. This makes prompt inputs reproducible
across agents and experiment runs.

The compiler should also emit an index:

```json
{
  "task_id": "B002",
  "source_files": [
    ".repoflow/task_graph.yaml",
    ".repoflow/handoffs/B001_deepseek.json",
    "src/expense_lite/dates.py",
    "tests/test_dates.py"
  ],
  "included_handoffs": [
    "B001_deepseek.json"
  ],
  "excluded_reason": {
    "B004_report_artifact.yaml": "downstream task is not visible yet"
  }
}
```

This index matters because it lets the harness and the paper state exactly what
the next agent was allowed to see.

## 11. Lifecycle

The RepoFlow V2 lifecycle:

```text
activate task
  -> build context packet
  -> launch fresh agent with packet
  -> agent reads packet and repository files
  -> agent updates status to IN_PROGRESS
  -> agent edits only allowed paths
  -> agent runs acceptance and regression commands
  -> agent writes structured handoff
  -> harness records diff and evidence
  -> deterministic gate accepts or rejects
  -> next task is activated only after acceptance
```

The gate should reject at least these failures:

- missing or malformed handoff;
- no recorded validation command;
- changed files outside allowed paths without an explicit exception;
- task marked `DONE` by the agent instead of `READY_FOR_REVIEW`;
- dependencies not accepted;
- acceptance command failure;
- workspace-local attempt to forge trusted results.

## 12. Harness Boundary

RepoFlow should separate three roles:

| Role | Authority | Mutable by agent |
| --- | --- | --- |
| Agent workspace | source files, tests, readable RepoFlow mirrors | yes |
| RepoFlow readable state | task graph, handoffs, context packet | partly |
| Harness control plane | signed run manifest, oracle pack, final score | no |

This boundary is critical. A useful harness must give agents enough state to
coordinate, but not allow them to redefine the acceptance oracle.

## 13. Experiment Conditions

V2 should make the comparison sharper than the current full-board versus
no-board contrast:

| Condition | Agent-visible state | Question |
| --- | --- | --- |
| no-board | README, source, tests | What happens with ordinary repository context only? |
| handoff-only | README plus latest natural-language handoff | Is a summary enough? |
| board-only | task graph and rules, no prior handoff | Do boundaries help without evidence? |
| full-board | task graph, structured handoff, gate evidence | Does structured shared state help? |
| repo-expanded | compiled context packet plus supporting files | Does explicit context expansion improve continuity? |

The expected contribution is not merely that full-board wins. The more useful
research question is which part of the harness accounts for improvement:
boundaries, handoffs, evidence, or compiled context.

## 14. Metrics

RepoFlow V2 should report metrics that distinguish coding success from
collaboration quality.

Implementation metrics:

- task acceptance pass rate;
- regression count against previous tasks;
- final artifact correctness.

Coordination metrics:

- missing handoff rate;
- invalid handoff schema rate;
- downstream reference to upstream decisions;
- repeated implementation of an existing function;
- unresolved risk propagation.

Scope and hygiene metrics:

- out-of-scope file changes;
- temporary artifact residue;
- root clutter;
- inconsistent task status.

Evidence metrics:

- commands recorded versus commands required;
- claimed validation without observable evidence;
- skipped validation with explicit reason;
- gate failure diagnosis quality.

Context metrics:

- context packet size;
- number of source artifacts included;
- downstream files read before edit;
- whether the agent touched a file before reading required context.

## 15. Implementation Roadmap

The next implementation should be incremental.

### Phase 1: Design and Compatibility

- Keep existing `.board/` runner behavior.
- Add this V2 design document.
- Add a compatibility note mapping `.board/` to `.repoflow/`.
- Do not rename existing files yet.

### Phase 2: Context Compiler Prototype

Add:

```text
repo_manager_core/context/
  compiler.py
  models.py
  render_markdown.py
scripts/build_context.py
tests/test_context_compiler.py
```

Initial command:

```bash
PYTHONPATH=. python3 scripts/build_context.py --repo . --task-id B002
```

Initial output:

```text
.repo_manager/agent_context.md
.repo_manager/agent_context_index.json
```

This should reuse current files before introducing `.repoflow/`.

### Phase 3: Evidence Normalization

- Normalize command records into JSONL.
- Attach command records to handoff validation entries.
- Store accepted task diff patches under external results and readable mirrors.

### Phase 4: Repo-Expanded Experiment

Add a new benchmark condition:

```text
repo_expanded_context
```

The agent receives only:

- ordinary repository files;
- the compiled context packet;
- explicit instruction not to inspect hidden oracle or parent directories.

Compare it against `no_board_baseline`, `native_docs_handoff`, and
`full_boardflow`.

### Phase 5: Paper and Tooling Convergence

- Update the paper to call RepoFlow a repository-local context-expansion
  harness.
- Use the context compiler output as a figure in the paper.
- Report ablations by harness component rather than only by model.

## 16. Open Questions

1. Should `.repoflow/` replace `.board/`, or should `.board/` remain the public
   namespace for simplicity?
2. Should context packets include selected source snippets, or only paths and
   summaries?
3. How aggressively should the harness hide downstream task details?
4. Should event logs be written by agents, wrappers, or both?
5. How can the harness measure whether an agent truly read the context packet
   before editing?
6. How much protocol overhead is acceptable before the harness becomes too
   heavy for small repositories?

## 17. Recommended Next Step

The next concrete step is to implement the context compiler prototype without
renaming the current protocol:

```bash
PYTHONPATH=. python3 scripts/build_context.py --repo <workspace> --task-id <task>
```

It should read existing BoardFlow artifacts and emit a deterministic
`.repo_manager/agent_context.md`. This gives the project a testable bridge from
the current BoardFlow implementation to the stronger RepoFlow V2 thesis.
