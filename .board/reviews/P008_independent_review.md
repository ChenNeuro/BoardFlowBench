# P008 Independent Review

Two read-only reviewers independently audited the P007 lifecycle implementation before P008 changes.

## Protocol And Security Reviewer

- Workspace evidence was forgeable and could be used to advance a benchmark task.
- Scope validation failed open when the baseline was unavailable, and workspace run metadata could replace the external baseline.
- Oracle packs were accepted without a trusted commit pin or clean-tree check.
- Accepted evidence was not bound to the workspace commit activated by the next stage.
- Workspace evidence leaked oracle and external result paths.
- Handoff validation checked structure but did not require meaningful passing validation.
- Scope and hygiene checks ignored the entire `.repo_manager/` directory.

## Architecture Reviewer

- Runner resume trusted mutable `run.json`, including executable adapter commands.
- Aggregation could report a fabricated completed run without trusted score or evidence files.
- Direct activation accepted self-authored workspace evidence.
- Bootstrap treated movable version tags as immutable and allowed CLI trust to override catalog policy.
- String command placeholder expansion broke paths containing spaces.
- Documentation overstated handoff validation and showed an incomplete legacy handoff example.

## Required Remediation

P008 is blocked from completion until external runner state is signed, activation consumes trusted external evidence, oracle packs are pinned and clean, scope checks fail closed, aggregation rejects incomplete runs, and mutation tests cover these boundaries.
