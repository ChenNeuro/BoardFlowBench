"""Rule-based function smell detection."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from repo_manager_core.board.task_status import ENTRY_POINT_NAMES
from repo_manager_core.smell_learning import (
    POLICY_ALLOWED,
    POLICY_CASE_BY_CASE,
    POLICY_CONTEXTUAL,
    active_keywords,
    feedback_question,
    generate_learned_policy_summary,
    keyword_rule,
    load_default_smell_rules,
    load_smell_rules,
)


def called_function_names(functions: list[dict[str, Any]]) -> set[str]:
    """Return the set of all function names called by any scanned function."""
    # 中文说明：
    # 这里统计的是“扫描到的函数体中出现过的调用名集合”。
    # 它是 unused_function 的启发式依据，不是完整调用图。
    names: set[str] = set()
    for fn in functions:
        names.update(fn.get("called_function_names", []))
    return names


def _warning(
    severity: str,
    smell_type: str,
    file_path: str,
    function_name: str,
    reason: str,
    suggestion: str,
) -> dict[str, Any]:
    warning: dict[str, Any] = {
        "severity": severity,
        "type": smell_type,
        "file": file_path,
        "function": function_name,
        "reason": reason,
        "suggestion": suggestion,
    }
    return warning


def _default_smell_rules() -> dict[str, Any]:
    # 中文说明：
    # 默认规则来自 repo_manager_core/default_smell_rules.json。
    # 具体仓库可以通过 .repo_manager/smell_rules.json 覆盖这些策略，
    # 所以 Python 源码里不再维护固定 keyword 列表。
    return load_default_smell_rules()


def detect_function_smells(
    functions: list[dict[str, Any]],
    *,
    repo_path: str | Path = ".",
    smell_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Detect suspicious patterns. Findings are warnings, not proof of defects."""
    # 中文说明：
    # smell 检测的总入口。它不是 linter，也不是 bug detector；
    # 目标是生成“值得人工复核”的结构性信号。
    # 规则来源优先级：
    # 1. 函数参数 smell_rules（测试或上层显式传入）；
    # 2. 当前 repo 的 .repo_manager/smell_rules.json；
    # 3. 包内 default_smell_rules.json。
    rules = smell_rules or load_smell_rules(repo_path, _default_smell_rules())
    warnings: list[dict[str, Any]] = []
    feedback_candidates: dict[tuple[str, str], set[str]] = defaultdict(set)
    called_names = called_function_names(functions)
    # Duplicate names are a cheap signal for copy/paste helpers across files.
    # 中文说明：
    # 同名函数不一定错误，但在 agent 多轮接力中，经常意味着复制出多个
    # “差不多”的 helper。这里作为 low severity 信号处理。
    definitions = Counter(fn["function_name"] for fn in functions)
    functions_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for fn in functions:
        functions_by_file[fn["file_path"]].append(fn)

    for fn in functions:
        name = fn["function_name"]
        lowered = name.lower()
        file_path = fn["file_path"]
        unused_by_scan = (
            name not in called_names
            and not name.startswith("__")
            and name not in ENTRY_POINT_NAMES
        )

        # Patch-like names often mean a temporary fix escaped into durable code.
        # 中文说明：
        # patch_keywords 不再硬编码在 Python 中，而是来自规则文件。
        # policy 决定是否报警：
        # - suspicious：命中就报警；
        # - contextual：只有在 unused_by_scan 等上下文更可疑时报警；
        # - allowed/case_by_case：不自动报警，但可能生成反馈问题。
        for keyword in _matching_keywords(rules, "patch_keywords", lowered):
            rule = keyword_rule(rules, "patch_keywords", keyword)
            _maybe_request_feedback(feedback_candidates, rule, "patch_keywords", keyword, name)
            if not _should_warn(rule, unused_by_scan=unused_by_scan):
                continue
            severity = "low" if rule["policy"] == POLICY_CONTEXTUAL else "medium"
            warnings.append(
                _with_rule_context(
                    _warning(
                        "medium",
                        "patch_name_smell",
                        file_path,
                        name,
                        f"Function name '{name}' contains keyword '{keyword}'.",
                        "Review whether this function is a durable abstraction or a temporary patch that should be merged.",
                    ),
                    keyword=keyword,
                    rule=rule,
                    severity=severity,
                ),
            )

        if unused_by_scan:
            # This cannot prove a function is dead: frameworks, CLIs, tests, and
            # plugins may call it dynamically. Keep severity low.
            # 中文说明：
            # “未被扫描函数调用”只代表在当前静态扫描范围内找不到调用方。
            # 对公共 API、路由函数、测试入口、命令行入口要人工确认后再删除。
            warnings.append(
                _warning(
                    "low",
                    "unused_function",
                    file_path,
                    name,
                    "The function is defined but not called by another scanned function.",
                    "Confirm whether it is an external entry point; otherwise remove it or add a clear call path.",
                )
            )

        calls = fn.get("called_function_names", [])
        if fn.get("function_length", 0) <= 5 and len(calls) == 1:
            # Thin wrappers are not wrong, but they tend to accumulate in agent
            # handoff workflows unless they define a real API boundary.
            # 中文说明：
            # wrapper_function 只在“很短且只委托给一个函数”时触发。
            # 这类函数如果没有校验、日志、异常转换、API 兼容意义，
            # 往往可以内联，减少 agent 接力时的理解成本。
            warnings.append(
                _warning(
                    "low",
                    "wrapper_function",
                    file_path,
                    name,
                    f"Very short function mostly delegates to '{calls[0]}'.",
                    "Inline the wrapper or keep it only if it provides a meaningful public API boundary.",
                )
            )

        if definitions[name] > 1:
            # 中文说明：
            # 跨文件同名函数可能是正常的局部 helper，也可能是重复实现。
            # 因此保持 low severity，只提示人工看是否可以合并。
            warnings.append(
                _warning(
                    "low",
                    "duplicate_function_name",
                    file_path,
                    name,
                    f"Function name '{name}' appears {definitions[name]} times in the scanned repo.",
                    "Check for duplicate-like helpers and consolidate behavior when practical.",
                )
            )

        file_name = Path(file_path).name.lower()
        # 中文说明：
        # 文件名 smell 和函数名 smell 分开处理。即使一个文件没有很多函数，
        # 名字里出现 final/backup/debug 等策略命中的词，也可能说明代码归档
        # 或临时副本被留在主仓库。
        for keyword in _matching_keywords(rules, "suspicious_file_keywords", file_name):
            rule = keyword_rule(rules, "suspicious_file_keywords", keyword)
            _maybe_request_feedback(
                feedback_candidates,
                rule,
                "suspicious_file_keywords",
                keyword,
                file_path,
            )
            if not _should_warn(rule, unused_by_scan=unused_by_scan):
                continue
            severity = "low" if rule["policy"] == POLICY_CONTEXTUAL else "medium"
            warnings.append(
                _with_rule_context(
                    _warning(
                        "medium",
                        "suspicious_file_name",
                        file_path,
                        name,
                        f"This function lives in a file whose name contains keyword '{keyword}'.",
                        "Review the file role and fold stable code into the main module structure.",
                    ),
                    keyword=keyword,
                    rule=rule,
                    severity=severity,
                ),
            )

    for file_path, file_functions in functions_by_file.items():
        # Many tiny helper-like functions in one file often indicate fragmented
        # patch work rather than a cohesive abstraction.
        # 中文说明：
        # fragmented_helpers 看的是“一个文件里短小 helper-like 函数过多”。
        # 单个 parse/format/normalize 函数通常没问题；集中出现很多个，
        # 才更像补丁式堆叠或缺少更高层抽象。
        short_helpers = [
            fn
            for fn in file_functions
            if fn.get("function_length", 0) <= 8
            and _helper_keyword_match(rules, fn["function_name"].lower())
        ]
        _collect_helper_feedback(feedback_candidates, rules, short_helpers)
        if len(short_helpers) >= 4:
            warnings.append(
                _warning(
                    "medium",
                    "fragmented_helpers",
                    file_path,
                    "",
                    f"File contains {len(short_helpers)} short helper-like functions.",
                    "Group related helpers, remove duplicates, and prefer clearer domain-level functions.",
                )
            )

    severity_order = {"high": 0, "medium": 1, "low": 2}
    # Stable ordering keeps reports and tests deterministic.
    # 中文说明：
    # 排序固定可以让报告 diff 更稳定，也方便测试断言。
    warnings.sort(key=lambda item: (severity_order.get(item["severity"], 9), item["file"], item["function"]))
    return {
        "summary": {
            "function_count": len(functions),
            "warning_count": len(warnings),
            "called_name_count": len(called_names),
        },
        "warnings": warnings,
        "smell_rules": rules,
        "learned_policies": generate_learned_policy_summary(rules),
        "feedback_questions": _feedback_questions(feedback_candidates),
    }


def _matching_keywords(rules: dict[str, Any], category: str, value: str) -> list[str]:
    # 中文说明：
    # keyword 匹配目前是子串匹配，简单、透明、容易通过规则文件调整。
    # 如果未来误报多，可以在这里升级为 word-boundary 或正则策略。
    return [keyword for keyword in active_keywords(rules, category) if keyword in value]


def _should_warn(rule: dict[str, str], *, unused_by_scan: bool) -> bool:
    # 中文说明：
    # policy 是自适应学习的核心：
    # allowed：仓库约定允许，不报警；
    # case_by_case：不自动报警，但保留人工判断入口；
    # contextual：只有上下文更可疑时报警；
    # suspicious：默认可疑，命中就报警。
    if rule["policy"] == POLICY_ALLOWED:
        return False
    if rule["policy"] == POLICY_CASE_BY_CASE:
        return False
    if rule["policy"] == POLICY_CONTEXTUAL:
        return unused_by_scan
    return True


def _with_rule_context(
    warning: dict[str, Any],
    *,
    keyword: str,
    rule: dict[str, str],
    severity: str,
) -> dict[str, Any]:
    warning["severity"] = severity
    warning["keyword"] = keyword
    warning["policy"] = rule["policy"]
    warning["policy_source"] = rule["source"]
    return warning


def _maybe_request_feedback(
    feedback_candidates: dict[tuple[str, str], set[str]],
    rule: dict[str, str],
    category: str,
    keyword: str,
    observed: str,
) -> None:
    # 中文说明：
    # 默认规则或 case_by_case 命中的 keyword 会进入 feedback_questions。
    # 但这里绝不自动写入 .repo_manager/smell_rules.json；
    # 只有用户显式 --feedback 时才更新规则，保证可审计。
    if rule["source"] in {"default_bootstrap", "default_config"} or rule["policy"] == POLICY_CASE_BY_CASE:
        feedback_candidates[(category, keyword)].add(observed)


def _helper_keyword_match(rules: dict[str, Any], function_name: str) -> bool:
    # 中文说明：
    # helper-like 的判断也走规则文件。如果某个仓库大量使用 parse/format
    # 作为稳定领域术语，可以把对应 keyword 标记为 allowed。
    for keyword in _matching_keywords(rules, "helper_keywords", function_name):
        rule = keyword_rule(rules, "helper_keywords", keyword)
        if rule["policy"] != POLICY_ALLOWED:
            return True
    return False


def _collect_helper_feedback(
    feedback_candidates: dict[tuple[str, str], set[str]],
    rules: dict[str, Any],
    short_helpers: list[dict[str, Any]],
) -> None:
    for fn in short_helpers:
        name = fn["function_name"]
        for keyword in _matching_keywords(rules, "helper_keywords", name.lower()):
            rule = keyword_rule(rules, "helper_keywords", keyword)
            _maybe_request_feedback(
                feedback_candidates,
                rule,
                "helper_keywords",
                keyword,
                name,
            )


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
