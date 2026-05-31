"""Task and board loading helpers for the BoardFlow protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_task(task_path: str | Path, repo: str | Path = ".") -> dict[str, Any]:
    """Load a benchmark task YAML file."""
    path = _resolve_path(repo, task_path)
    task = load_yaml(path)
    if not isinstance(task, dict):
        raise ValueError(f"task file must contain a mapping: {path}")
    return task


def load_board(repo: str | Path = ".") -> dict[str, Any]:
    """Load the machine-readable BoardFlow board from .board/tasks.yaml."""
    path = Path(repo) / ".board" / "tasks.yaml"
    board = load_yaml(path)
    if not isinstance(board, dict):
        raise ValueError(f"board file must contain a mapping: {path}")
    return board


def save_board(board: dict[str, Any], repo: str | Path = ".") -> Path:
    """Write board data back to .board/tasks.yaml."""
    root = Path(repo)
    path = root / ".board" / "tasks.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _dump_yaml(board)
    path.write_text(text, encoding="utf-8")
    return path


def task_id(task: dict[str, Any]) -> str:
    """Return the canonical task id field."""
    value = task.get("task_id") or task.get("id")
    if not isinstance(value, str) or not value:
        raise ValueError("task YAML must define task_id")
    return value


def load_yaml(path: str | Path) -> Any:
    """Load YAML with PyYAML when available, else a small local subset parser."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ModuleNotFoundError:
        return _parse_simple_yaml(text)


def _resolve_path(repo: str | Path, path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return Path(repo) / path


# ---- Simple YAML dumper (minimal, for task board) ----

def _dump_yaml(value: Any, indent: int = 0) -> str:
    prefix = "  " * indent
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = []
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_dump_yaml(v, indent + 1))
            elif v is None:
                lines.append(f"{prefix}{k}:")
            elif isinstance(v, bool):
                lines.append(f"{prefix}{k}: {'true' if v else 'false'}")
            elif isinstance(v, str):
                lines.append(f"{prefix}{k}: {v}")
            else:
                lines.append(f"{prefix}{k}: {v}")
        return "\n".join(lines) + "\n"
    if isinstance(value, list):
        if not value:
            return "[]"
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{prefix}- ")
                for k, v in item.items():
                    if isinstance(v, (dict, list)):
                        lines.append(f"{prefix}  {k}:")
                        lines.append(_dump_yaml(v, indent + 2))
                    else:
                        lines.append(f"{prefix}  {k}: {v}")
            elif isinstance(item, str):
                lines.append(f"{prefix}- {item}")
            else:
                lines.append(f"{prefix}- {item}")
        return "\n".join(lines) + "\n"
    return f"{prefix}{value}"


# ---- Simple YAML subset parser (fallback when PyYAML unavailable) ----

def _parse_simple_yaml(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))

    if not lines:
        return None

    value, index = _parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError("unsupported YAML structure")
    return value


def _parse_block(
    lines: list[tuple[int, str]], index: int, indent: int
) -> tuple[Any, int]:
    if index >= len(lines):
        return None, index

    current_indent, content = lines[index]
    if current_indent < indent:
        return None, index
    if current_indent != indent:
        raise ValueError(f"unexpected indentation near: {content}")

    if content.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_list(
    lines: list[tuple[int, str]], index: int, indent: int
) -> tuple[list[Any], int]:
    items: list[Any] = []

    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or not content.startswith("- "):
            break

        item_text = content[2:].strip()
        index += 1

        if not item_text:
            item, index = _parse_block(lines, index, indent + 2)
            items.append(item)
            continue

        if ":" in item_text:
            key, raw_value = item_text.split(":", 1)
            item: dict[str, Any] = {}
            if raw_value.strip():
                item[key.strip()] = _parse_scalar(raw_value.strip())
            else:
                item[key.strip()], index = _parse_block(lines, index, indent + 2)

            if index < len(lines) and lines[index][0] > indent:
                extra, index = _parse_mapping(lines, index, indent + 2)
                if isinstance(extra, dict):
                    item.update(extra)
                else:
                    raise ValueError("list item mapping expected")
            items.append(item)
        else:
            items.append(_parse_scalar(item_text))

    return items, index


def _parse_mapping(
    lines: list[tuple[int, str]], index: int, indent: int
) -> tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}

    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent:
            break
        if content.startswith("- "):
            break
        if ":" not in content:
            raise ValueError(f"expected key/value mapping near: {content}")

        key, raw_value = content.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        index += 1

        if raw_value:
            mapping[key] = _parse_scalar(raw_value)
        elif index < len(lines) and lines[index][0] > indent:
            mapping[key], index = _parse_block(lines, index, lines[index][0])
        else:
            mapping[key] = None

    return mapping, index


def _parse_scalar(value: str) -> Any:
    if value in {"null", "None", "~"}:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value
