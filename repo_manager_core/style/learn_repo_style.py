"""Repository style learning, profiling and IO helpers."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from repo_manager_core.smell_learning import (
    POLICY_ALLOWED,
    active_keywords,
    keyword_rule,
    load_smell_rules,
)


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Stable key ordering makes generated artifacts easier to diff between runs.
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_output_path(repo_path: str | Path, output_path: str | Path) -> Path:
    path = Path(output_path)
    if path.is_absolute():
        return path
    # Relative report paths belong to the scanned repository, not necessarily to
    # the process cwd or the installed skill directory.
    return Path(repo_path) / path


def learn_repo_style(repo_profile: dict[str, Any]) -> dict[str, Any]:
    """Analyze naming conventions, docstring coverage, and function length stats."""
    functions = repo_profile.get("functions", [])
    names = [fn["function_name"] for fn in functions]
    lengths = [int(fn.get("function_length", 0)) for fn in functions]
    modules = sorted({str(Path(fn["file_path"]).parent) for fn in functions})
    # The style profile is intentionally simple and measurable so agents can use
    # it as guidance without overfitting to subjective style rules.
    snake_case_pattern = re.compile(r"^[a-z_][a-z0-9_]*$")
    snake_case_count = sum(1 for name in names if snake_case_pattern.match(name))
    rules = load_smell_rules(repo_profile.get("repo_path", "."))
    patch_like_count = sum(1 for name in names if _matches_patch_policy(rules, name))
    docstring_count = sum(1 for fn in functions if fn.get("docstring"))
    # Prefixes help identify common local vocabulary such as parse_ or render_.
    prefixes = Counter(name.split("_", 1)[0] for name in names if "_" in name)

    style_warnings: list[dict[str, str]] = []
    if names and snake_case_count / len(names) < 0.8:
        style_warnings.append(
            {
                "severity": "low",
                "type": "mixed_function_naming",
                "reason": "Less than 80% of functions use snake_case naming.",
                "suggestion": "Prefer one naming convention for repository-local functions.",
            }
        )
    if patch_like_count:
        style_warnings.append(
            {
                "severity": "medium",
                "type": "patch_like_naming_style",
                "reason": f"Found {patch_like_count} function names with patch-like words.",
                "suggestion": "Replace temporary fix names with stable domain names after behavior is validated.",
            }
        )

    return {
        "repo_path": repo_profile.get("repo_path"),
        "function_count": len(functions),
        "module_count": len(modules),
        "snake_case_function_count": snake_case_count,
        "docstring_function_count": docstring_count,
        "patch_like_function_count": patch_like_count,
        "average_function_length": round(sum(lengths) / len(lengths), 2) if lengths else 0,
        "median_function_length": median(lengths) if lengths else 0,
        "max_function_length": max(lengths) if lengths else 0,
        "common_name_prefixes": prefixes.most_common(10),
        "style_warnings": style_warnings,
    }


def _matches_patch_policy(rules: dict[str, Any], name: str) -> bool:
    lowered = name.lower()
    for keyword in active_keywords(rules, "patch_keywords"):
        if keyword in lowered and keyword_rule(rules, "patch_keywords", keyword)["policy"] != POLICY_ALLOWED:
            return True
    return False
