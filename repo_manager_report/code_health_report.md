# Repo Manager Code Health Review

## Summary

Findings are suspicious signals, not absolute defects. Confirm public entry points before removing or inlining code.

- Repository: `.`
- Python files scanned: 50
- Functions scanned: 178
- Total warnings: 86
- Patch-like function names: 4
- Average function length: 18.5

## Warning Counts

- duplicate_function_name: 25
- patch_name_smell: 4
- suspicious_directory_name: 3
- unused_function: 45
- wrapper_function: 9

## Smell Taxonomy

Automated counts are signal counts, not defect counts. Smells with no automated signals remain manual review targets.

### Level 1: Agent Debt Multipliers

- Patch: 4 automated signal(s). Temporary fix names, patch files, debug files, or workaround vocabulary that can become permanent code.
- Helper Explosion: 9 automated signal(s). Many small generic helpers or thin wrappers that make the codebase harder to reason about.
- Shadow Implementation: 25 automated signal(s). Parallel implementations or duplicate-like helper names that may hide repeated behavior.

### Level 2: Maintenance Error Sources

- Mirror Logic: 25 automated signal(s). Copied logic that may diverge across files; current detection is partial and needs manual confirmation.
- Dead Zone: 48 automated signal(s). Unused functions, abandoned directories, temporary files, or source under output/artifact areas.
- Knowledge Duplication: manual review target. Repeated constants, schemas, prompts, docs, or config sources; currently a manual review target.

### Level 3: Architecture Consistency Risks

- Abandoned Abstraction: 54 automated signal(s). Wrapper layers, facades, or helper abstractions that no longer add a stable boundary.
- Configuration Drift: 0 automated signal(s). Search, smell, style, runtime, or generated config split across competing sources; current detection is partial.

### Level 4: Repo-Specific Learning

- User Rejection Patterns: manual review target. Explicit feedback and learned keyword policies from .repo_manager/user_feedback.jsonl and smell_rules.json.
- Style Violations: manual review target. Deviations from learned naming, docstring, length, and patch-like vocabulary style.

## Learned Repository Policies

- No learned repository policies recorded.

## Feedback Requested

- Keyword: `format`
  - Category: `helper_keywords`
  - Observed: `format_money`, `test_parse_date_supports_common_formats`
  - Question: Should "format" be considered suspicious in this repository?
- Keyword: `helper`
  - Category: `helper_keywords`
  - Observed: `helper`
  - Question: Should "helper" be considered suspicious in this repository?
- Keyword: `normalize`
  - Category: `helper_keywords`
  - Observed: `normalize_header`
  - Question: Should "normalize" be considered suspicious in this repository?
- Keyword: `parse`
  - Category: `helper_keywords`
  - Observed: `test_parse_amount_supports_currency_commas_and_parentheses`, `test_parse_date_supports_common_formats`
  - Question: Should "parse" be considered suspicious in this repository?
- Keyword: `fix`
  - Category: `patch_keywords`
  - Observed: `_normalise_suffixes`
  - Question: Should "fix" be considered suspicious in this repository?
- Keyword: `patch`
  - Category: `patch_keywords`
  - Observed: `_matches_patch_policy`, `test_detects_patch_name_smell`, `test_learned_allowed_policy_suppresses_patch_keyword`
  - Question: Should "patch" be considered suspicious in this repository?
- Keyword: `temp`
  - Category: `suspicious_directory_keywords`
  - Observed: `skills\agent-bridge\templates`, `skills\code-health-review\templates`, `skills\style-record\templates`
  - Question: Should "temp" be considered suspicious in this repository?

## Findings

1. `patch_name_smell` (medium)
   - Location: `repo_manager_core\search_rules.py` / `_normalise_suffixes`
   - Reason: Function name '_normalise_suffixes' contains keyword 'fix'.
   - Suggestion: Review whether this function is a durable abstraction or a temporary patch that should be merged.
2. `patch_name_smell` (medium)
   - Location: `repo_manager_core\style\learn_repo_style.py` / `_matches_patch_policy`
   - Reason: Function name '_matches_patch_policy' contains keyword 'patch'.
   - Suggestion: Review whether this function is a durable abstraction or a temporary patch that should be merged.
3. `patch_name_smell` (medium)
   - Location: `tests\test_detect_smells.py` / `test_detects_patch_name_smell`
   - Reason: Function name 'test_detects_patch_name_smell' contains keyword 'patch'.
   - Suggestion: Review whether this function is a durable abstraction or a temporary patch that should be merged.
4. `patch_name_smell` (medium)
   - Location: `tests\test_smell_learning.py` / `test_learned_allowed_policy_suppresses_patch_keyword`
   - Reason: Function name 'test_learned_allowed_policy_suppresses_patch_keyword' contains keyword 'patch'.
   - Suggestion: Review whether this function is a durable abstraction or a temporary patch that should be merged.
5. `unused_function` (low)
   - Location: `repo_manager_core\board\review_writer.py` / `write_review`
   - Reason: The function is defined but not called by another scanned function.
   - Suggestion: Confirm whether it is an external entry point; otherwise remove it or add a clear call path.
6. `wrapper_function` (low)
   - Location: `repo_manager_core\health\analyze_repo_structure.py` / `_default_structure_rules`
   - Reason: Very short function mostly delegates to 'load_default_smell_rules'.
   - Suggestion: Inline the wrapper or keep it only if it provides a meaningful public API boundary.
7. `duplicate_function_name` (low)
   - Location: `repo_manager_core\health\analyze_repo_structure.py` / `_feedback_questions`
   - Reason: Function name '_feedback_questions' appears 2 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
8. `duplicate_function_name` (low)
   - Location: `repo_manager_core\health\analyze_repo_structure.py` / `_matching_keywords`
   - Reason: Function name '_matching_keywords' appears 2 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
9. `duplicate_function_name` (low)
   - Location: `repo_manager_core\health\analyze_repo_structure.py` / `_maybe_request_feedback`
   - Reason: Function name '_maybe_request_feedback' appears 2 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
10. `duplicate_function_name` (low)
   - Location: `repo_manager_core\health\analyze_repo_structure.py` / `_should_warn`
   - Reason: Function name '_should_warn' appears 2 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
11. `unused_function` (low)
   - Location: `repo_manager_core\health\call_agent.py` / `call_agent`
   - Reason: The function is defined but not called by another scanned function.
   - Suggestion: Confirm whether it is an external entry point; otherwise remove it or add a clear call path.
12. `duplicate_function_name` (low)
   - Location: `repo_manager_core\health\detect_function_smells.py` / `_feedback_questions`
   - Reason: Function name '_feedback_questions' appears 2 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
13. `wrapper_function` (low)
   - Location: `repo_manager_core\health\detect_function_smells.py` / `_matching_keywords`
   - Reason: Very short function mostly delegates to 'active_keywords'.
   - Suggestion: Inline the wrapper or keep it only if it provides a meaningful public API boundary.
14. `duplicate_function_name` (low)
   - Location: `repo_manager_core\health\detect_function_smells.py` / `_matching_keywords`
   - Reason: Function name '_matching_keywords' appears 2 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
15. `duplicate_function_name` (low)
   - Location: `repo_manager_core\health\detect_function_smells.py` / `_maybe_request_feedback`
   - Reason: Function name '_maybe_request_feedback' appears 2 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
16. `duplicate_function_name` (low)
   - Location: `repo_manager_core\health\detect_function_smells.py` / `_should_warn`
   - Reason: Function name '_should_warn' appears 2 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
17. `unused_function` (low)
   - Location: `repo_manager_core\health\scan_file_functions.py` / `visit_Call`
   - Reason: The function is defined but not called by another scanned function.
   - Suggestion: Confirm whether it is an external entry point; otherwise remove it or add a clear call path.
18. `unused_function` (low)
   - Location: `repo_manager_core\style\context_writer.py` / `write_style_profile`
   - Reason: The function is defined but not called by another scanned function.
   - Suggestion: Confirm whether it is an external entry point; otherwise remove it or add a clear call path.
19. `duplicate_function_name` (low)
   - Location: `skills\agent-bridge\scripts\bridge_handoff.py` / `main`
   - Reason: Function name 'main' appears 11 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.
20. `duplicate_function_name` (low)
   - Location: `skills\agent-bridge\scripts\bridge_init_board.py` / `main`
   - Reason: Function name 'main' appears 11 times in the scanned repo.
   - Suggestion: Check for duplicate-like helpers and consolidate behavior when practical.

## Style Profile

- Snake case functions: 177
- Functions with docstrings: 56
- Median function length: 12.0
- Max function length: 193
- Style warnings:
  - patch_like_naming_style: Found 4 function names with patch-like words.

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
