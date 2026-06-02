"""Repository layout heuristics."""

from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import Any

from repo_manager_core.search_rules import included_roots, is_excluded_path, load_search_rules
from repo_manager_core.smell_learning import (
    POLICY_ALLOWED,
    POLICY_CASE_BY_CASE,
    POLICY_CONTEXTUAL,
    feedback_question,
    generate_learned_policy_summary,
    keyword_rule,
    load_default_smell_rules,
    load_smell_rules,
    matching_keywords,
)

from .scan_repo_functions import IGNORED_DIRS, iter_python_files

OUTPUT_DIR_KEYWORDS = {"output", "outputs", "artifact", "artifacts", "result", "results"}


def _contains_keyword(value: str, keywords: set[str]) -> bool:
    lowered = value.lower()
    return any(keyword in lowered for keyword in keywords)


def _default_structure_rules() -> dict[str, Any]:
    # 中文说明：
    # 结构类规则和函数名规则共用同一份 default_smell_rules.json。
    # 这样 old/final/backup 等词是否可疑，也可以按仓库学习覆盖。
    return load_default_smell_rules()


def analyze_repo_structure(
    repo_path: str | Path,
    *,
    smell_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # 中文说明：
    # 这一层检查的是仓库布局，不依赖函数 AST。
    # 它主要捕捉“代码是不是散落在临时目录、输出目录、根目录脚本堆里”。
    root = Path(repo_path)
    rules = smell_rules or load_smell_rules(root, _default_structure_rules())
    search_rules = load_search_rules(root)
    warnings: list[dict[str, Any]] = []
    feedback_candidates: dict[tuple[str, str], set[str]] = {}
    python_files = iter_python_files(root, search_rules)
    top_level_files = [path for path in python_files if path.parent == root]

    # Many root-level scripts make handoffs harder because ownership and module
    # boundaries are unclear.
    # 中文说明：
    # 根目录 Python 文件过多会增加接手成本：入口、工具脚本、业务模块混在一起。
    # 阈值 8 是启发式，不是硬性质量标准。
    if len(top_level_files) > 8:
        warnings.append(
            {
                "severity": "medium",
                "type": "too_many_top_level_python_files",
                "file": "",
                "function": "",
                "reason": f"Found {len(top_level_files)} top-level Python files.",
                "suggestion": "Group related modules into packages instead of leaving many scripts at the repo root.",
            }
        )

    seen_dirs: set[Path] = set()
    for search_root in included_roots(root, search_rules):
        if not search_root.exists():
            continue
        for path in chain([search_root], search_root.rglob("*")):
            if not path.is_dir() or path in seen_dirs:
                continue
            seen_dirs.add(path)
            if is_excluded_path(path, root, search_rules):
                continue
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            # Directory names like old/temp/backup commonly hold stale code that
            # agents may accidentally edit or import.
            # 中文说明：
            # 目录名策略同样来自 smell rules。比如 old/ 在某些项目里可能是
            # compatibility layer，可以通过反馈标记为 allowed。扫描范围本身由
            # search_rules 控制，所以被排除的目录不会继续产生结构类误报。
            for keyword in matching_keywords(rules, "suspicious_directory_keywords", path.name):
                rule = keyword_rule(rules, "suspicious_directory_keywords", keyword)
                _maybe_request_feedback(
                    feedback_candidates,
                    rule,
                    "suspicious_directory_keywords",
                    keyword,
                    str(path),
                )
                if not _should_warn(rule):
                    continue
                severity = "low" if rule["policy"] == POLICY_CONTEXTUAL else "medium"
                warnings.append(
                    {
                        "severity": severity,
                        "type": "suspicious_directory_name",
                        "file": str(path),
                        "function": "",
                        "reason": f"Directory name '{path.name}' contains keyword '{keyword}'.",
                        "suggestion": "Move archived code outside the active repo or rename the directory to reflect its purpose.",
                        "keyword": keyword,
                        "policy": rule["policy"],
                        "policy_source": rule["source"],
                    }
                )

    for path in python_files:
        # File-level naming is checked separately from function-level naming so
        # empty or script-only files can still be flagged.
        # 中文说明：
        # 文件名命中策略时，不需要函数名也命中。因为 parser_final.py、
        # debug_utils.py 这类文件本身就可能是临时/归档痕迹。
        for keyword in matching_keywords(rules, "suspicious_file_keywords", path.name):
            rule = keyword_rule(rules, "suspicious_file_keywords", keyword)
            _maybe_request_feedback(
                feedback_candidates,
                rule,
                "suspicious_file_keywords",
                keyword,
                str(path),
            )
            if not _should_warn(rule):
                continue
            severity = "low" if rule["policy"] == POLICY_CONTEXTUAL else "medium"
            warnings.append(
                {
                    "severity": severity,
                    "type": "suspicious_file_name",
                    "file": str(path),
                    "function": "",
                    "reason": f"File name '{path.name}' contains keyword '{keyword}'.",
                    "suggestion": "Rename or consolidate the file after reviewing whether it is still needed.",
                    "keyword": keyword,
                    "policy": rule["policy"],
                    "policy_source": rule["source"],
                }
            )
        if any(_contains_keyword(part, OUTPUT_DIR_KEYWORDS) for part in _relative_parent_parts(path, root)):
            # Python under output/artifact directories is often generated or
            # misplaced source; either case is worth human review.
            # 中文说明：
            # output/artifact/result 目录里出现 Python 源码，通常表示生成物和
            # 源码边界不清。这里暂时不用学习规则，因为这类目录语义更稳定。
            warnings.append(
                {
                    "severity": "medium",
                    "type": "python_file_inside_output_directory",
                    "file": str(path),
                    "function": "",
                    "reason": "Python source appears inside an output/artifact/result-like directory.",
                    "suggestion": "Keep generated outputs separate from source code unless this is intentional.",
                }
            )

    return {
        "repo_path": str(root),
        "python_file_count": len(python_files),
        "top_level_python_file_count": len(top_level_files),
        "warnings": warnings,
        "smell_rules": rules,
        "learned_policies": generate_learned_policy_summary(rules),
        "feedback_questions": _feedback_questions(feedback_candidates),
    }


def _should_warn(rule: dict[str, str]) -> bool:
    # 中文说明：
    # 结构类规则目前没有 unused_by_scan 这类上下文，因此 contextual 仍会报警，
    # 但 severity 会降为 low；allowed 和 case_by_case 不自动报警。
    return rule["policy"] not in {POLICY_ALLOWED, POLICY_CASE_BY_CASE}


def _relative_parent_parts(path: Path, root: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(root).parent.parts
    except ValueError:
        return path.parent.parts


def _maybe_request_feedback(
    feedback_candidates: dict[tuple[str, str], set[str]],
    rule: dict[str, str],
    category: str,
    keyword: str,
    observed: str,
) -> None:
    if rule["source"] in {"default_bootstrap", "default_config"} or rule["policy"] == POLICY_CASE_BY_CASE:
        feedback_candidates.setdefault((category, keyword), set()).add(observed)


def _feedback_questions(
    feedback_candidates: dict[tuple[str, str], set[str]],
) -> list[dict[str, Any]]:
    questions = []
    for category, keyword in sorted(feedback_candidates):
        questions.append(
            feedback_question(
                category=category,
                keyword=keyword,
                observed=sorted(feedback_candidates[(category, keyword)]),
            )
        )
    return questions
