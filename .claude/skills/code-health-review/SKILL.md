---
name: code-health-review
description: Review AI-generated Python code for patch-function bloat, unused helpers, wrapper functions, duplicate-like utilities, suspicious files, and repository style drift in this repository. Use this skill when checking whether code produced by coding agents is maintainable and structurally healthy.
---

# Code Health Review

This is the Claude Code project-level entry point for the repository's Code Health Review skill.

The canonical implementation lives in:

- `skills/code-health-review/SKILL.md`
- `skills/code-health-review/scripts/`
- `repo_manager_core/health/`
- `repo_manager_core/style/`

## Workflow

1. Identify the target repo or diff.
2. Scan Python files and build a function index.
3. Detect suspicious function smells.
4. Read `.repo_manager/repo_style_profile.json` if available.
5. Compare new code against learned repo style.
6. Generate `outputs/code_health_report.md`.
7. Summarize the top risks and suggested cleanup actions.

## Commands

Run these commands from the repository root:

```bash
python skills/code-health-review/scripts/health_scan.py template/messy_ai_case --output outputs/repo_profile.json
python skills/code-health-review/scripts/health_detect_smells.py template/messy_ai_case --output outputs/smell_report.json
python skills/code-health-review/scripts/health_generate_report.py template/messy_ai_case --output-dir outputs
python skills/code-health-review/scripts/health_review_diff.py --before outputs/before.json --after outputs/after.json --output outputs/diff_review.md
```

## Outputs

- `outputs/repo_profile.json`
- `outputs/smell_report.json`
- `outputs/style_profile.json`
- `outputs/code_health_report.md`

## Rules

- Findings are suspicious signals, not proof of defects.
- Confirm public entry points before recommending removal.
- Never modify source files as part of review-only work.
- Style suggestions should reference `.repo_manager/repo_style_profile.json` when available.
