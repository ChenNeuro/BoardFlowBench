# T001 Review

Reviewer: BoardFlow experiment reviewer

Task: T001 / task_001_date_parser

## Summary

T001 meets the functional acceptance criteria in the final repository state. The parser accepts `YYYY-MM-DD` and `YYYY/MM/DD`, normalizes both to `YYYY-MM-DD`, preserves the public `normalize_date` function name, and rejects malformed dates with `ValueError`.

Agent B correctly continued from Agent A's repository-local handoff. The board state, machine-readable task state, and latest handoff all mark T001 as `DONE` with owner `agent_b`.

This run is suitable as a course-report case study, but only as a single illustrative run. It should not be presented as proof that BoardFlow generally improves handoff.

## Commands Run

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=demo_repo_template/src python3 -m unittest discover -s demo_repo_template/tests -p 'test_parser.py'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=demo_repo_template/src python3 -m unittest discover -s demo_repo_template/tests
python3 -m json.tool .board/handoffs/T001_agent_a_handoff.json >/dev/null
python3 -m json.tool .board/handoffs/T001_agent_b_handoff.json >/dev/null
git ls-files | wc -l
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json
from benchmark.scoring.task_loader import load_task
from benchmark.scoring.hygiene import check_hygiene
from benchmark.scoring.board_consistency import check_board_consistency
from benchmark.scoring.handoff_check import check_handoff
from benchmark.scoring.scope_check import check_scope

repo='.'
task=load_task('benchmark/tasks/task_001_date_parser.yaml', repo)
report={
  'hygiene': check_hygiene(repo),
  'board_consistency': check_board_consistency(repo, task),
  'handoff': check_handoff(repo, task),
  'scope_control': check_scope(repo, task),
}
print(json.dumps(report, indent=2, sort_keys=True))
PY
python3 scripts/run_score.py --task benchmark/tasks/task_001_date_parser.yaml --repo . --output /tmp/boardflow_t001_reviewer_score.json
```

The temporary score file under `/tmp` was removed after inspection.

## Final Score

Final scorer result: `100/100`.

Breakdown:

- Correctness: `40/40`
- Repo hygiene: `20/20`
- Scope control: `15/15`
- Handoff: `15/15`
- Board consistency: `10/10`

Scorer warnings:

- no `regression_commands` field is defined for T001
- git has no tracked baseline, so changed-file and unexpected-untracked checks were skipped

## Evidence

Functional evidence:

- `demo_repo_template/src/expense_lite/parser.py` tries both `%Y-%m-%d` and `%Y/%m/%d`.
- `demo_repo_template/tests/test_parser.py` covers hyphen dates, slash dates, whitespace around slash dates, malformed dates, and JSON fixture loading.
- T001 parser test run passed: `5 tests OK`.
- Full demo test discovery passed: `10 tests OK`.

Board evidence:

- `PROJECT_BOARD.md` lists T001 as `DONE` with owner `agent_b`.
- `.board/tasks.yaml` lists T001 as `DONE`, owner `agent_b`, and `current_handoff: .board/handoffs/T001_agent_b_handoff.json`.

Handoff evidence:

- `.board/handoffs/T001_agent_a_handoff.json` records Agent A's partial progress, validation, temporary files, decisions, and risks.
- `.board/handoffs/T001_agent_b_handoff.json` records Agent B's verification, scoring result, temporary file cleanup, decisions, and next step.
- Both handoff files parse as valid JSON.

Hygiene evidence:

- Hygiene checker found no forbidden root files.
- Hygiene checker found no cache files.
- Hygiene checker found no `.scratch` entries beyond `.gitkeep`.
- Manual check found no `__pycache__` directories and no dirty `.scratch` files.

Git evidence:

- `git ls-files | wc -l` returned `0`.
- Because there is no tracked git baseline, git cannot reliably distinguish benchmark-run changes from initial repository skeleton files.

## Manual Notes

Agent B's continuation was clear. Agent A's handoff explicitly said what was changed, what was validated, what risks remained, and what Agent B should do next. Agent B followed that path without needing a chat transcript.

There was no harmful duplicated implementation work. Agent A added one focused parser test and Agent B verified rather than rewriting it. The repeated test and scorer runs were useful validation, not unnecessary code churn.

Allowed-path compliance is plausible from the handoff records: Agent A changed `PROJECT_BOARD.md`, `.board/tasks.yaml`, `.board/handoffs/`, and `demo_repo_template/tests/test_parser.py`; Agent B changed `PROJECT_BOARD.md`, `.board/tasks.yaml`, and `.board/handoffs/`. All are allowed for T001. However, the scorer cannot verify this independently because the repository has no tracked baseline.

One important ambiguity: the parser implementation was already fixed before Agent A began the BoardFlow handoff stage. Agent A documented this risk. That makes this run useful for studying handoff clarity and review discipline, but weaker as evidence that BoardFlow improved the original bug-fixing step.

## Did BoardFlow Improve Handoff Clarity?

For this run, yes, with caveats. BoardFlow made the current state easy to reconstruct from repository files:

- the board showed T001's state and owner
- the task YAML showed acceptance criteria and allowed paths
- Agent A's handoff explained why the task was left at `READY_FOR_REVIEW`
- Agent B's handoff explained why the task was moved to `DONE`

This is an observation from one run, not a general conclusion.

## Limitations

- Single run only; no statistical claim is possible.
- The parser was already fixed before Agent A's BoardFlow work, so the run does not isolate BoardFlow's effect on initial bug discovery.
- Git-based scope checks were skipped because the repo has no tracked baseline.
- The scorer gave full scope credit despite skipped changed-file detection, which should be adjusted before larger experiments.
- T001 has no explicit `regression_commands` field, so Agent B and the reviewer used full unittest discovery as a manual regression check.

## Recommendation

Include this run in the course presentation as a qualitative case study of repo-local handoff clarity, not as proof of benchmark effectiveness.

Next experiment:

1. Commit or snapshot a clean baseline before each condition.
2. Reset T001 to the intentionally buggy parser state before running the BoardFlow condition.
3. Add `regression_commands` to task YAML.
4. Rerun no-board and BoardFlow conditions from identical starting states.
5. Compare not only final score, but also whether agents used handoffs, avoided scope drift, and left the repo clean.
