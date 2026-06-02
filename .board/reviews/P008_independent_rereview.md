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

## Final Rereview Attempt 1

Final independent rereview was attempted with two read-only reviewer agents after remediation:

- Protocol security rereview agent: errored because the session hit the Codex subagent usage limit.
- Architecture lifecycle rereview agent: errored because the session hit the Codex subagent usage limit.

No final independent reviewer report was produced. This file intentionally does not claim that the final independent rereview passed.

## Final Rereview Attempt 2

After subagent quota became available again, two new read-only reviewer agents audited the current `yihao/feature` branch.

### Protocol Security Reviewer

Verdict: no blocking findings.

The reviewer confirmed that signed manifests, external placement, HMAC tamper rejection, resume and activation trust checks, evidence and score digest validation, oracle pinning, reviewer mutation protection, scope and hygiene boundaries, handoff fail-closed behavior, and aggregation semantic binding are all in place.

Validation reported by reviewer:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m pytest -p no:cacheprovider`: PASS, 111 passed.
- `git diff --check`: PASS.
- board sync check: PASS, `[]`.

Residual risks:

- HMAC protects control-plane integrity but does not replace OS sandboxing.
- Agent and reviewer subprocesses still do not have built-in timeouts.

### Architecture Lifecycle Reviewer

Verdict: no blocking findings.

The reviewer confirmed that finalize and activation crash recovery, recovery-only activation CLI behavior, signed state completeness, activation evidence checks, aggregation binding, latest handoff ordering, non-object handoff handling, tracked strategy baselines, and documentation consistency are closed.

Validation reported by reviewer:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m pytest -p no:cacheprovider`: PASS, 111 passed.
- `git diff --check`: PASS.
- board sync check: PASS, `[]`.

Residual risks:

- Agent and reviewer subprocesses still do not have built-in timeouts.
- HMAC and digest checks do not replace OS sandboxing for hostile same-user processes.
- The final architecture pass was read-only and did not rerun the sibling-repo Expense Lite smoke; the earlier P008 handoff records that smoke as passed.

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

The final independent rereview is complete and found no blocking findings. Remaining risks are non-blocking and should be tracked as follow-up hardening rather than blocking P008 completion.
