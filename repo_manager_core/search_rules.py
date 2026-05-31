"""Repo-local search scope rules for health scans."""

from __future__ import annotations

from fnmatch import fnmatch
import json
from pathlib import Path
from typing import Any

SEARCH_RULES_PATH = ".repo_manager/search_rules.json"
DEFAULT_SEARCH_RULES_PATH = Path(__file__).with_name("default_search_rules.json")


def load_default_search_rules(path: str | Path = DEFAULT_SEARCH_RULES_PATH) -> dict[str, Any]:
    """Load packaged default search rules."""
    return _normalise_search_rules(_read_json(Path(path)))


def load_search_rules(
    repo_path: str | Path = ".",
    default_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load repo-local search rules, creating them from defaults when missing."""
    # 中文说明：
    # search_rules 和 smell_rules 的生命周期一致：
    # - 第一次运行时，如果当前仓库没有 .repo_manager/search_rules.json，
    #   就从 repo_manager_core/default_search_rules.json 生成一份；
    # - 后续 agent 或用户只改 repo-local 文件，不改包内默认文件；
    # - 加载时用 repo-local 配置覆盖默认值，保证行为可审计、可回滚。
    root = Path(repo_path)
    default = _normalise_search_rules(default_rules or load_default_search_rules())
    rules_path = root / SEARCH_RULES_PATH
    if not rules_path.exists():
        _write_json(default, rules_path)
        return default

    repo_rules = _read_json(rules_path)
    return _merge_search_rules(default, repo_rules)


def included_roots(repo_path: str | Path, rules: dict[str, Any]) -> list[Path]:
    """Return concrete roots to scan from include_paths."""
    # 中文说明：
    # include_paths 用来限制扫描入口。例如只扫描 src/ 和 tests/，
    # 就可以把仓库根目录下的实验脚本、文档样例或归档代码排除在主报告外。
    root = Path(repo_path)
    paths: list[Path] = []
    for value in rules.get("include_paths", ["."]):
        path = Path(value)
        paths.append(path if path.is_absolute() else root / path)
    return paths


def should_scan_path(path: Path, repo_path: str | Path, rules: dict[str, Any]) -> bool:
    """Return whether a path is allowed by suffix and directory exclusions."""
    if path.suffix not in set(rules.get("file_suffixes", [".py"])):
        return False
    return not is_excluded_path(path, repo_path, rules)


def is_excluded_path(path: Path, repo_path: str | Path, rules: dict[str, Any]) -> bool:
    """Return whether a path is inside a directory excluded by search rules."""
    # 中文说明：
    # 这个判断不关心文件后缀，因此函数扫描、结构扫描都能共用。
    # 只要相对路径的任意目录段命中 exclude_dirs，就视为不属于扫描范围。
    root = Path(repo_path)
    try:
        relative = path.relative_to(root)
        parts = relative.parts
    except ValueError:
        parts = path.parts
        relative_text = path.as_posix()
    else:
        relative_text = relative.as_posix()

    excluded = set(rules.get("exclude_dirs", []))
    if any(part in excluded for part in parts):
        return True

    if path.is_file() and _matches_excluded_file(path, relative_text, rules):
        return True

    return _matches_excluded_glob(path, relative_text, rules)


def _merge_search_rules(default: dict[str, Any], repo_rules: dict[str, Any]) -> dict[str, Any]:
    merged = dict(default)
    for key in ("include_paths", "exclude_dirs", "exclude_files", "exclude_globs", "file_suffixes"):
        if key in repo_rules:
            merged[key] = repo_rules[key]
    merged["schema_version"] = repo_rules.get("schema_version", default.get("schema_version", 1))
    return _normalise_search_rules(merged)


def _normalise_search_rules(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": int(raw.get("schema_version", 1)),
        "include_paths": _string_list(raw.get("include_paths", ["."])),
        "exclude_dirs": _string_list(raw.get("exclude_dirs", [])),
        "exclude_files": _normalise_relative_patterns(raw.get("exclude_files", [])),
        "exclude_globs": _normalise_relative_patterns(raw.get("exclude_globs", [])),
        "file_suffixes": _normalise_suffixes(raw.get("file_suffixes", [".py"])),
    }


def _normalise_suffixes(value: Any) -> list[str]:
    suffixes = []
    for item in _string_list(value):
        suffixes.append(item if item.startswith(".") else f".{item}")
    return sorted(set(suffixes))


def _normalise_relative_patterns(value: Any) -> list[str]:
    patterns = []
    for item in _string_list(value):
        patterns.append(item.replace("\\", "/").strip())
    return sorted({pattern for pattern in patterns if pattern})


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _matches_excluded_file(path: Path, relative_text: str, rules: dict[str, Any]) -> bool:
    # 中文说明：
    # exclude_files 支持两种写法：
    # - "main.py"：按文件名匹配，排除任意目录下的 main.py；
    # - "src/main.py"：按仓库相对路径精确匹配，只排除这个文件。
    for pattern in rules.get("exclude_files", []):
        if "/" in pattern:
            if relative_text == pattern:
                return True
        elif path.name == pattern:
            return True
    return False


def _matches_excluded_glob(path: Path, relative_text: str, rules: dict[str, Any]) -> bool:
    # 中文说明：
    # exclude_globs 用于排除一类路径。包含 "/" 的 pattern 按仓库相对路径匹配；
    # 不包含 "/" 的 pattern 按文件/目录名匹配，例如 "main_*.py"。
    for pattern in rules.get("exclude_globs", []):
        target = relative_text if "/" in pattern else path.name
        if fnmatch(target, pattern):
            return True
    return False


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"search rules file must contain an object: {path}")
    return data


def _write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
