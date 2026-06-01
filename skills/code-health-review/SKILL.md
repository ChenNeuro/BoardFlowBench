---
name: code-health-review
description: Review AI-generated Python code for patch-function bloat, unused helpers, wrapper functions, duplicate-like utilities, suspicious files, repository structure drift, and repo-adaptive smell rules. Use this skill when the user wants to check whether a Python repo is maintainable and structurally healthy, especially after coding-agent edits.
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
5. Detect function smells and repository-structure smells using `smell_rules`.
6. Read `.repo_manager/repo_style_profile.json` if available.
7. Generate `repo_manager_report/code_health_report.md`.
8. Summarize the top risks, learned policies, feedback questions, and suggested cleanup actions.

## Current Checks

- `patch_name_smell`: function names matching `patch_keywords`.
- `unused_function`: functions not called by another scanned function.
- `wrapper_function`: very short functions that delegate to one call.
- `duplicate_function_name`: repeated function names across scanned files.
- `suspicious_file_name`: files matching `suspicious_file_keywords`.
- `fragmented_helpers`: one file with many short helper-like functions.
- `too_many_top_level_python_files`: many root-level Python files.
- `suspicious_directory_name`: directories matching `suspicious_directory_keywords`.
- `python_file_inside_output_directory`: Python files under output/artifact/result-like directories.

Findings are suspicious signals, not proof of defects.

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
