---
name: code-health-review
description: Review AI-generated Python code for agent debt smells including Patch, Helper Explosion, Shadow Implementation, Mirror Logic, Dead Zone, Knowledge Duplication, Abandoned Abstraction, Configuration Drift, User Rejection Patterns, and Style Violations. Use this skill when the user wants to check whether a Python repo is maintainable and structurally healthy, especially after coding-agent edits.
---

# Code Health Review

This skill reviews Python code health in the current workspace. It can run from this repository or from a global Claude Code skill install.

The canonical implementation lives in:

- `skills/code-health-review/SKILL.md`
- `skills/code-health-review/scripts/`
- `repo_manager_core/health/`
- `repo_manager_core/style/`
- `repo_manager_core/smell_learning.py`
- `repo_manager_core/search_rules.py`

## Repo-Local Rules

Always treat the target workspace as the source of truth for adaptive behavior.

- `.repo_manager/search_rules.json` controls scan scope: `include_paths`, `exclude_dirs`, `exclude_files`, `exclude_globs`, and `file_suffixes`.
- `.repo_manager/smell_rules.json` controls keyword policies for `patch_keywords`, `helper_keywords`, `suspicious_file_keywords`, and `suspicious_directory_keywords`.
- `.repo_manager/user_feedback.jsonl` records explicit user feedback events.
- `repo_manager_core/default_search_rules.json` and `repo_manager_core/default_smell_rules.json` are bootstrap defaults only.

If repo-local rule files are missing, the scripts create them from defaults. After that, prefer editing `.repo_manager/search_rules.json` and `.repo_manager/smell_rules.json`; do not change packaged defaults unless the user is intentionally changing bootstrap behavior for every future repo.

## Workflow

1. Use the current workspace root as the target repo unless the user explicitly names another path.
2. Load or create `.repo_manager/search_rules.json`.
3. Load or create `.repo_manager/smell_rules.json`.
4. Scan files allowed by `search_rules` and build a function index.
5. Detect function smells and repository-structure smells using `smell_rules`, then organize them through the Level 1-4 smell taxonomy below.
6. Read `.repo_manager/repo_style_profile.json` if available.
7. Generate `repo_manager_report/code_health_report.md`.
8. Summarize the top risks, learned policies, feedback questions, and suggested cleanup actions.

## Smell Taxonomy

Findings are suspicious signals, not proof of defects. The taxonomy is the review lens; some smells are directly detected today, while others are reported as manual review targets when the current scanner only has partial evidence.

### Level 1: Agent Debt Multipliers

These are the easiest ways for an agent to keep manufacturing technical debt.

- Patch: temporary fix naming or patch-like files. Current signals: `patch_name_smell`, `suspicious_file_name` when the keyword is patch/fix/temp/debug/safe/workaround-like, and `patch_like_naming_style`.
- Helper Explosion: excessive small generic utilities. Current signals: `fragmented_helpers`, helper keyword matches, and thin `wrapper_function` findings.
- Shadow Implementation: repeated or parallel implementations of similar behavior. Current signals: `duplicate_function_name`, repeated helper names, and duplicate-like utility clusters.

### Level 2: Maintenance Error Sources

These are the smells most likely to make future edits wrong.

- Mirror Logic: copied logic that evolves in multiple places. Current support: partial, through duplicate names and helper clusters; confirm manually before merging behavior.
- Dead Zone: abandoned or unreachable code regions. Current signals: `unused_function`, `suspicious_directory_name`, `suspicious_file_name`, and `python_file_inside_output_directory`.
- Knowledge Duplication: multiple sources of truth for the same project knowledge. Current support: partial; review duplicated config, constants, schemas, prompts, and docs when warning clusters point at the same domain.

### Level 3: Architecture Consistency Risks

These smells indicate that module boundaries or abstractions are no longer stable.

- Abandoned Abstraction: wrappers, facade functions, or helper layers that no longer add meaning. Current signals: `wrapper_function`, `unused_function`, and repeated helper groups.
- Configuration Drift: scan scope, keyword policy, style profile, or runtime config split across competing sources. Current support: partial; inspect `.repo_manager/search_rules.json`, `.repo_manager/smell_rules.json`, config files, and generated artifacts when structure warnings appear.

### Level 4: Repo-Specific Learning

These are adaptive signals from the target repository itself.

- User Rejection Patterns: keywords or naming patterns explicitly marked through feedback. Current signals: `.repo_manager/user_feedback.jsonl`, learned policies in `.repo_manager/smell_rules.json`, and report feedback questions.
- Style Violations: deviations from learned repository style. Current signals: `.repo_manager/repo_style_profile.json`, `style_profile.json`, `mixed_function_naming`, `patch_like_naming_style`, docstring coverage, and function length statistics.

## Current Automated Checks

- `patch_name_smell`: function names matching `patch_keywords`.
- `unused_function`: functions not called by another scanned function.
- `wrapper_function`: very short functions that delegate to one call.
- `duplicate_function_name`: repeated function names across scanned files.
- `suspicious_file_name`: files matching `suspicious_file_keywords`.
- `fragmented_helpers`: one file with many short helper-like functions.
- `too_many_top_level_python_files`: many root-level Python files.
- `suspicious_directory_name`: directories matching `suspicious_directory_keywords`.
- `python_file_inside_output_directory`: Python files under output/artifact/result-like directories.

## Other Health Capabilities

- Builds an AST-based function index with arguments, docstrings, leading comments, called function names, and function lengths.
- Applies repo-local scan scope rules from `.repo_manager/search_rules.json`.
- Applies repo-local smell keyword policies from `.repo_manager/smell_rules.json`.
- Records explicit user feedback in `.repo_manager/user_feedback.jsonl` and reflects learned policies in future reports.
- Produces machine-readable artifacts for automation: `repo_profile.json`, `smell_report.json`, and `style_profile.json`.
- Produces a human-readable Markdown report with top risks, learned policies, feedback questions, style profile, and cleanup plan.
- Compares before/after repo profiles with `health_review_diff.py` to show new warnings, resolved warnings, and style drift.

## Commands

When running from this repository checkout:

```bash
PYTHONPATH=. python3 skills/code-health-review/scripts/health_scan.py .
PYTHONPATH=. python3 skills/code-health-review/scripts/health_detect_smells.py .
PYTHONPATH=. python3 skills/code-health-review/scripts/health_generate_report.py .
PYTHONPATH=. python3 skills/code-health-review/scripts/health_review_diff.py --before repo_manager_report/before.json --after repo_manager_report/after.json
```

When installed globally, resolve `scripts/health_generate_report.py` relative to this `SKILL.md`, pass the target workspace path as the repo argument, and keep output inside that workspace:

```bash
python3 <skill_dir>/scripts/health_generate_report.py .
```

To record explicit feedback:

```bash
python3 <skill_dir>/scripts/health_generate_report.py . \
  --feedback fix=contextual \
  --feedback-reason "Used in public APIs"

python3 <skill_dir>/scripts/health_generate_report.py . \
  --feedback suspicious_directory_keywords:old=allowed \
  --feedback-reason "Compatibility layer"
```

## Outputs

- `repo_manager_report/repo_profile.json`
- `repo_manager_report/smell_report.json`
- `repo_manager_report/style_profile.json`
- `repo_manager_report/code_health_report.md`
- `.repo_manager/search_rules.json`
- `.repo_manager/smell_rules.json`
- `.repo_manager/user_feedback.jsonl` when feedback is recorded

## Rules

- Do not modify application source files during a health review; report findings unless the user separately asks for cleanup implementation.
- Do not silently modify `.repo_manager/smell_rules.json`; update it only when the user gives explicit feedback or asks for a repo-specific adjustment.
- Search-scope adjustments belong in `.repo_manager/search_rules.json`.
- Use `exclude_files` for exact file exclusions such as `main_rocopar.py`; use `exclude_globs` for patterns such as `main_*.py` or `generated/*.py`.
- Keyword policy adjustments belong in `.repo_manager/smell_rules.json`.
- Supported policies are `suspicious`, `contextual`, `allowed`, and `case_by_case`.
- Confirm public entry points before recommending removal.
- Style suggestions should reference `.repo_manager/repo_style_profile.json` when available.
- When installed globally, do not pass this skill's own install directory as the repo path; scan `.` or the user's requested workspace path.
