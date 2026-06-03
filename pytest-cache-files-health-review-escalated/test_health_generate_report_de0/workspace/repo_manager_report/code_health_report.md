# Repo Manager Code Health Review

## Summary

Findings are suspicious signals, not absolute defects. Confirm public entry points before removing or inlining code.

- Repository: `.`
- Python files scanned: 1
- Functions scanned: 1
- Total warnings: 2
- Patch-like function names: 1
- Average function length: 2.0

## Warning Counts

- patch_name_smell: 1
- unused_function: 1

## Smell Taxonomy

Automated counts are signal counts, not defect counts. Smells with no automated signals remain manual review targets.

### Level 1: Agent Debt Multipliers

- Patch: 1 automated signal(s). Temporary fix names, patch files, debug files, or workaround vocabulary that can become permanent code.
- Helper Explosion: 0 automated signal(s). Many small generic helpers or thin wrappers that make the codebase harder to reason about.
- Shadow Implementation: 0 automated signal(s). Parallel implementations or duplicate-like helper names that may hide repeated behavior.

### Level 2: Maintenance Error Sources

- Mirror Logic: 0 automated signal(s). Copied logic that may diverge across files; current detection is partial and needs manual confirmation.
- Dead Zone: 1 automated signal(s). Unused functions, abandoned directories, temporary files, or source under output/artifact areas.
- Knowledge Duplication: manual review target. Repeated constants, schemas, prompts, docs, or config sources; currently a manual review target.

### Level 3: Architecture Consistency Risks

- Abandoned Abstraction: 1 automated signal(s). Wrapper layers, facades, or helper abstractions that no longer add a stable boundary.
- Configuration Drift: 0 automated signal(s). Search, smell, style, runtime, or generated config split across competing sources; current detection is partial.

### Level 4: Repo-Specific Learning

- User Rejection Patterns: manual review target. Explicit feedback and learned keyword policies from .repo_manager/user_feedback.jsonl and smell_rules.json.
- Style Violations: manual review target. Deviations from learned naming, docstring, length, and patch-like vocabulary style.

## Learned Repository Policies

- No learned repository policies recorded.

## Feedback Requested

- Keyword: `parse`
  - Category: `helper_keywords`
  - Observed: `parse_date_safe`
  - Question: Should "parse" be considered suspicious in this repository?
- Keyword: `safe`
  - Category: `patch_keywords`
  - Observed: `parse_date_safe`
  - Question: Should "safe" be considered suspicious in this repository?

## Findings

1. `patch_name_smell` (medium)
   - Location: `sample.py` / `parse_date_safe`
   - Reason: Function name 'parse_date_safe' contains keyword 'safe'.
   - Suggestion: Review whether this function is a durable abstraction or a temporary patch that should be merged.
2. `unused_function` (low)
   - Location: `sample.py` / `parse_date_safe`
   - Reason: The function is defined but not called by another scanned function.
   - Suggestion: Confirm whether it is an external entry point; otherwise remove it or add a clear call path.

## Style Profile

- Snake case functions: 1
- Functions with docstrings: 0
- Median function length: 2
- Max function length: 2
- Style warnings:
  - patch_like_naming_style: Found 1 function names with patch-like words.

## Health Capabilities

- AST-based function indexing with arguments, docstrings, leading comments, calls, and function lengths.
- Repo-local scan scope through `.repo_manager/search_rules.json`.
- Repo-local keyword policies through `.repo_manager/smell_rules.json`.
- Repository structure checks for suspicious files, directories, root-level scripts, and output/artifact source.
- Style profiling for naming, docstring coverage, function length, and patch-like vocabulary.
- Learned policy reporting and explicit feedback capture through `.repo_manager/user_feedback.jsonl`.
- Before/after review diffing through `health_review_diff.py` for new warnings, resolved warnings, and style drift.

## Cleanup Plan

1. Confirm public entry points, framework hooks, CLI commands, tests, and plugin callbacks.
2. Merge duplicate-like helpers only after behavior is covered by tests.
3. Inline thin wrappers when they do not validate input, document an API boundary, or improve readability.
4. Rename or remove temporary files after stable code is moved into clear modules.
5. Re-run Code Health Review and the repository's normal test suite.
