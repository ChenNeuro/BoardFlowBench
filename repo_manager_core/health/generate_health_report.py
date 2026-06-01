"""Prompt generation and report rendering for code health review."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any


def generate_review_prompt(
    repo_profile: dict[str, Any],
    smell_report: dict[str, Any],
    user_question: str | None = None,
) -> str:
    """Build a compact LLM prompt from the repo profile and smell report."""
    # Keep prompt input bounded; the Markdown renderer below handles the full
    # local report without requiring an LLM.
    # 中文说明：
    # 这个 prompt 是给外部 LLM reviewer 的压缩输入，不是最终报告。
    # 因为仓库可能很大，所以这里只放汇总信息和最多 80 条 warning。
    compact_profile = {
        "repo_path": repo_profile.get("repo_path"),
        "python_file_count": repo_profile.get("python_file_count"),
        "function_count": repo_profile.get("function_count"),
        "parsed_file_count": repo_profile.get("parsed_file_count"),
        "failed_file_count": repo_profile.get("failed_file_count"),
        "structure_warnings": repo_profile.get("structure_warnings", []),
    }
    # Limit warning volume so very large repos do not produce oversized prompts.
    # 中文说明：
    # 完整 warning 仍然保存在 smell_report.json；prompt 只做抽样压缩，
    # 避免上下文过长导致模型忽略关键内容。
    compact_smells = smell_report.get("warnings", [])[:80]
    compact_policies = smell_report.get("learned_policies", [])
    compact_questions = smell_report.get("feedback_questions", [])[:20]

    prompt = f"""
You are Repo Manager Code Health Review, a reviewer for AI-generated Python repositories.

Write a concise, human-readable review. Treat findings as suspicious signals, not absolute errors.

Focus on:
- patch function bloat
- duplicate-like helper functions
- unused functions
- wrapper functions
- messy repository structure
- a practical cleanup plan

Repository profile:
{json.dumps(compact_profile, indent=2)}

Function smell warnings:
{json.dumps(compact_smells, indent=2)}

Learned repository policies:
{json.dumps(compact_policies, indent=2)}

Feedback questions:
{json.dumps(compact_questions, indent=2)}
""".strip()

    if user_question:
        prompt += f"\n\nUser question:\n{user_question.strip()}"

    return prompt


def _group_warning_counts(warnings: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(warning.get("type", "unknown") for warning in warnings).items()))


def render_review_report(
    repo_profile: dict[str, Any],
    smell_report: dict[str, Any],
    style_profile: dict[str, Any],
    user_question: str | None = None,
) -> str:
    """Generate a full Markdown health review report."""
    # 中文说明：
    # 这是本地 deterministic 报告生成器，不依赖 LLM。
    # 输入是扫描/检测阶段生成的 JSON，因此报告可重复、可 diff。
    warnings = smell_report.get("warnings", [])
    learned_policies = smell_report.get("learned_policies", [])
    feedback_questions = smell_report.get("feedback_questions", [])
    warning_counts = _group_warning_counts(warnings)
    # The report leads with the first 20 sorted warnings; full details remain in
    # smell_report.json for follow-up automation.
    # 中文说明：
    # Markdown 只展示前 20 条，避免报告过长；机器可读的完整结果在 JSON 中。
    top_warnings = warnings[:20]

    lines = [
        "# Repo Manager Code Health Review",
        "",
        "## Summary",
        "",
        "Findings are suspicious signals, not absolute defects. Confirm public entry points before removing or inlining code.",
        "",
        f"- Repository: `{repo_profile.get('repo_path', '')}`",
        f"- Python files scanned: {repo_profile.get('python_file_count', 0)}",
        f"- Functions scanned: {repo_profile.get('function_count', 0)}",
        f"- Total warnings: {len(warnings)}",
        f"- Patch-like function names: {style_profile.get('patch_like_function_count', 0)}",
        f"- Average function length: {style_profile.get('average_function_length', 0)}",
        "",
        "## Warning Counts",
        "",
    ]

    if warning_counts:
        lines.extend(f"- {name}: {count}" for name, count in warning_counts.items())
    else:
        lines.append("- No suspicious signals found.")

    lines.extend(["", "## Learned Repository Policies", ""])
    # 中文说明：
    # learned policies 来自 .repo_manager/smell_rules.json，
    # 用来解释为什么某些 keyword 被允许、降级或按上下文处理。
    if learned_policies:
        for policy in learned_policies:
            lines.extend(
                [
                    f"- Keyword: `{policy.get('keyword', '')}`",
                    f"  - Category: `{policy.get('category', '')}`",
                    f"  - Policy: `{policy.get('policy', '')}`",
                    f"  - Source: {policy.get('source', '')}",
                ]
            )
            if policy.get("reason"):
                lines.append(f"  - Reason: {policy.get('reason', '')}")
    else:
        lines.append("- No learned repository policies recorded.")

    lines.extend(["", "## Feedback Requested", ""])
    # 中文说明：
    # feedback questions 是系统“请求人类确认”的位置。
    # 这里不会自动学习，用户必须通过 --feedback 显式写入规则。
    if feedback_questions:
        for question in feedback_questions:
            observed = ", ".join(f"`{item}`" for item in question.get("observed", [])[:5])
            lines.extend(
                [
                    f"- Keyword: `{question.get('keyword', '')}`",
                    f"  - Category: `{question.get('category', '')}`",
                    f"  - Observed: {observed or '(none)'}",
                    f"  - Question: {question.get('question', '')}",
                ]
            )
    else:
        lines.append("- No feedback questions generated.")

    lines.extend(["", "## Findings", ""])
    if top_warnings:
        for index, warning in enumerate(top_warnings, start=1):
            target = warning.get("function") or "(module/repo)"
            file_path = warning.get("file") or "(repository)"
            lines.extend(
                [
                    f"{index}. `{warning.get('type', 'unknown')}` ({warning.get('severity', 'unknown')})",
                    f"   - Location: `{file_path}` / `{target}`",
                    f"   - Reason: {warning.get('reason', '')}",
                    f"   - Suggestion: {warning.get('suggestion', '')}",
                ]
            )
    else:
        lines.append("No suspicious function or structure warnings were detected.")

    style_warnings = style_profile.get("style_warnings", [])
    lines.extend(["", "## Style Profile", ""])
    lines.extend(
        [
            f"- Snake case functions: {style_profile.get('snake_case_function_count', 0)}",
            f"- Functions with docstrings: {style_profile.get('docstring_function_count', 0)}",
            f"- Median function length: {style_profile.get('median_function_length', 0)}",
            f"- Max function length: {style_profile.get('max_function_length', 0)}",
        ]
    )
    if style_warnings:
        lines.append("- Style warnings:")
        for warning in style_warnings:
            lines.append(f"  - {warning.get('type')}: {warning.get('reason')}")

    lines.extend(
        [
            "",
            "## Cleanup Plan",
            "",
            "1. Confirm public entry points, framework hooks, CLI commands, tests, and plugin callbacks.",
            "2. Merge duplicate-like helpers only after behavior is covered by tests.",
            "3. Inline thin wrappers when they do not validate input, document an API boundary, or improve readability.",
            "4. Rename or remove temporary files after stable code is moved into clear modules.",
            "5. Re-run Code Health Review and the repository's normal test suite.",
        ]
    )

    if user_question:
        lines.extend(["", "## User Question", "", user_question.strip()])

    return "\n".join(lines) + "\n"
