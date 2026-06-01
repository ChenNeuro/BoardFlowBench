# Repo Manager Code Health Review

## Summary

Findings are suspicious signals, not absolute defects.

- Repository: `{repo_path}`
- Python files scanned: {file_count}
- Functions scanned: {function_count}
- Total warnings: {warning_count}

## Warning Counts

<!-- Populated automatically -->

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
