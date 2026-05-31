---
name: code-health-review
description: Review AI-generated Python code for patch-function bloat, unused helpers, wrapper functions, duplicate-like utilities, suspicious files, and repository style drift. Use this skill when checking whether code produced by coding agents is maintainable and structurally healthy.
---

# Code Health Review

This skill reviews Python repositories or diffs for function-level structural problems.

## Workflow

1. Identify the target repo or diff.
2. Scan Python files and build a function index.
3. Detect suspicious function smells.
4. Read `.repo_manager/repo_style_profile.json` if available.
5. Compare new code against learned repo style.
6. Generate `outputs/code_health_report.md`.
7. Summarize the top risks and suggested cleanup actions.

## Scripts

| Script | Purpose |
|--------|---------|
| `health_scan.py` | Scan repo and build function index JSON |
| `health_detect_smells.py` | Detect function smells from a profile |
| `health_generate_report.py` | Generate full Markdown health report |
| `health_review_diff.py` | Compare before/after profiles for drift |

## Outputs

- `outputs/repo_profile.json`
- `outputs/smell_report.json`
- `outputs/style_profile.json`
- `outputs/code_health_report.md`

## Rules

- Findings are suspicious signals, not proof of defects.
- Confirm public entry points before recommending removal.
- Never modify source files — only report findings.
- Style suggestions should reference `.repo_manager/repo_style_profile.json` when available.
