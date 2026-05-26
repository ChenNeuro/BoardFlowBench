# Benchmark Scoring

This directory contains the minimal BoardFlowBench scoring harness.

The scorer evaluates observable repository state only. It does not inspect chat transcripts, hidden agent memory, or subjective writing quality.

## Run

From the repository root:

```bash
python3 scripts/run_score.py \
  --task benchmark/tasks/task_001_date_parser.yaml \
  --repo . \
  --output benchmark/results/task_001_score.json
```

## Output

The score JSON includes:

- `task_id`
- `total`
- `correctness`
- `hygiene`
- `scope_control`
- `handoff`
- `board_consistency`
- `violations`
- `warnings`

## Scoring Model

Total: 100

- Correctness: 40
- Repo hygiene: 20
- Scope control: 15
- Handoff: 15
- Board consistency: 10

## Current Limitations

- YAML loading uses PyYAML when available and a small fallback parser for this repo's simple YAML files.
- Scope and unexpected-untracked checks need a committed git baseline. If the repo has no tracked files, those checks are skipped with warnings.
- Handoff validation checks required fields directly; it does not implement full JSON Schema validation.
- Correctness is based on task acceptance commands and documented expected failures.
