---
name: boardflow-reviewer
description: Independently review a BoardFlowBench workspace or result set without modifying implementation files or approving the reviewer's own changes.
---

# BoardFlow Reviewer

Use this skill as a read-only reviewer after a separate coding agent has finished a sticker or pull request.

## Workflow

1. Read the assigned task specification and the recorded baseline commit.
2. Run deterministic scoring before making qualitative judgments.
3. Review the baseline diff, acceptance evidence, handoff, tests, scope, and hygiene.
4. Record concrete risks and missing validation. Do not fix the implementation in the same reviewer pass.
5. Keep reviewer findings non-blocking. Deterministic finalize gates decide whether a sticker may advance.

## Commands

```bash
PYTHONPATH=. python3 tools/benchmark_scorer.py \
  --task <task-yaml> \
  --repo <workspace> \
  --baseline <sticker-baseline> \
  --oracle-root <private-oracle-repo> \
  --oracle-commit <fixed-oracle-pack-sha> \
  --output <external-score-json> \
  --fail-on-violations

PYTHONPATH=. python3 scripts/aggregate_benchmark_results.py \
  --results-dir <external-results-dir> \
  --output <external-summary-json>
```

## Rules

- Do not modify source files while acting as reviewer.
- Do not modify or commit the workspace after deterministic acceptance.
- Do not modify the external key, signed manifest, score, or evidence files.
- Do not treat an AI review as acceptance evidence.
- Report findings against observable repository state and exact file paths.
- Keep private oracle files and the results directory outside the agent workspace.
- Treat reviewer adapters as operator-trusted commands. Use an external OS sandbox for an untrusted reviewer process.
