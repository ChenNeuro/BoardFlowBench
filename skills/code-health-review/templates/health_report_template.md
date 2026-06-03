# Repo Manager Code Health Review

## Summary

Findings are suspicious signals, not absolute defects.

- Repository: `{repo_path}`
- Python files scanned: {file_count}
- Functions scanned: {function_count}
- Total warnings: {warning_count}

## Warning Counts

<!-- Populated automatically -->

## Smell Taxonomy

### Level 1: Agent Debt Multipliers

- Patch: patch-like functions, temporary files, and fix/workaround naming.
- Helper Explosion: many small generic helpers, thin wrappers, and utility clusters.
- Shadow Implementation: duplicate-like functions or parallel helper implementations.

### Level 2: Maintenance Error Sources

- Mirror Logic: copied logic that may evolve inconsistently.
- Dead Zone: unused functions, abandoned directories, and source files under output/artifact areas.
- Knowledge Duplication: repeated configuration, constants, schemas, prompts, or docs that compete as sources of truth.

### Level 3: Architecture Consistency Risks

- Abandoned Abstraction: wrapper layers or abstractions that no longer add meaning.
- Configuration Drift: scan, smell, style, runtime, or generated configuration split across competing sources.

### Level 4: Repo-Specific Learning

- User Rejection Patterns: learned feedback from `.repo_manager/user_feedback.jsonl` and `.repo_manager/smell_rules.json`.
- Style Violations: deviations from the learned repository style profile.

## Health Capabilities

- AST-based function indexing.
- Repo-local search scope and smell keyword policies.
- Structure warnings for suspicious files, directories, root-level scripts, and output/artifact source.
- Style profiling for naming, docstrings, function length, and patch-like vocabulary.
- Learned policy and feedback question reporting.
- Before/after diff reporting for new warnings, resolved warnings, and style drift.

## Findings

<!-- Populated automatically -->

## Style Profile

- Snake case functions: {snake_case_count}
- Functions with docstrings: {docstring_count}
- Median function length: {median_length}
- Max function length: {max_length}

## Cleanup Plan

1. Confirm public entry points, framework hooks, CLI commands, tests, and plugin callbacks.
2. Merge duplicate-like helpers only after behavior is covered by tests.
3. Inline thin wrappers when they do not validate input, document an API boundary, or improve readability.
4. Rename or remove temporary files after stable code is moved into clear modules.
5. Re-run Code Health Review and the repository's normal test suite.
