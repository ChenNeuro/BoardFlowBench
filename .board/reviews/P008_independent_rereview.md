# P008 Independent Rereview

## Initial Independent Findings

Two read-only reviewers audited the pre-P008 implementation and reported blocking trust-boundary issues. The findings are recorded in `.board/reviews/P008_independent_review.md`.

## Remediation Implemented

- Signed external `run.json` state with HMAC and rejected unsigned or modified manifests.
- Required `results_dir` and `oracle_root` outside the agent workspace.
- Removed workspace-local result and policy-file exemptions from scope and hygiene checks.
- Bound activation to signed external stage evidence, current HEAD, target seed, oracle commit, and meaningful handoff records.
- Added `activating_task` signed transition state so finalize-to-activation interruptions are recoverable.
- Restricted standalone activation and finalize CLIs to signed runner lifecycle recovery.
- Checked reviewer-side workspace and trusted control-plane mutations after deterministic acceptance.
- Bound aggregation to signed run condition, seed commit, oracle commit, score digest, and complete trusted evidence.
- Rejected non-object or empty handoff JSON and selected latest handoffs by timestamp.
- Added mutation tests for the reviewed failure modes.

## Final Rereview Attempt

Final independent rereview was attempted with two read-only reviewer agents after remediation:

- Protocol security rereview agent: errored because the session hit the Codex subagent usage limit.
- Architecture lifecycle rereview agent: errored because the session hit the Codex subagent usage limit.

No final independent reviewer report was produced. This file intentionally does not claim that the final independent rereview passed.

## Local Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m pytest -p no:cacheprovider -q`: PASS, 111 passed.
- `git diff --check`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 - <<'PY' ... check_board_views('.') ... PY`: PASS, `[]`.
- Real smoke with `../ExpenseLiteBenchDemo` and `../ExpenseLiteBenchOracles`: PASS.
  - Fixed seed initialized.
  - B001 slash-date tests failed in the initial seed as expected.
  - B001 implementation, complete handoff, finalize, trusted external evidence, and B002 activation succeeded.
  - Workspace mirror did not leak oracle paths.
  - Aggregation accepted the trusted B001 stage.
  - `no_board_baseline` initialized without `.board/`, `PROJECT_BOARD.md`, or `AGENTS.md`.
  - `validate_benchmark_seed.py` confirmed the fixed seed boundary.

## Release Risk

P008 implementation is ready for PR review, but final independent rereview remains pending because reviewer agents were unavailable. Keep P008 at `READY_FOR_REVIEW` until an independent reviewer confirms the remediation.
