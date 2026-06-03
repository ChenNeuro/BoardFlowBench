"""AST-based function scanner for a single Python file."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


class _CallCollector(ast.NodeVisitor):
    """Collect direct function and method call names from a function body."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def visit_Call(self, node: ast.Call) -> Any:
        # 中文说明：
        # 这里不做完整的静态调用解析，只提取调用表达式的“名字”。
        # 例如 helper(x) 记录 helper，obj.helper(x) 也记录 helper。
        # 这样做的原因是 smell 检测只需要一个轻量信号：
        # “某个函数名是否被扫描到的其他函数调用过”。
        # 它不能证明函数真的被使用或未使用，因为框架 hook、CLI、
        # 反射、插件入口都可能绕过这种静态扫描。
        name = self._call_name(node.func)
        if name:
            self.calls.append(name)
        self.generic_visit(node)

    @staticmethod
    def _call_name(node: ast.AST) -> str | None:
        # Store only the terminal call name: foo() -> foo, obj.foo() -> foo.
        # That is enough for smell heuristics without trying to resolve imports.
        # 中文说明：
        # 只保留最后一级名字是刻意的折中。精确解析 obj 来自哪个模块、
        # helper 是否被 import 重命名，会让实现复杂很多，而且跨仓库不稳定。
        # 当前目标是生成审查提示，而不是做类型检查器或调用图分析器。
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None


def extract_leading_comments(source_lines: list[str], start_line: int) -> str:
    """Return contiguous comments immediately above a function definition."""
    comments: list[str] = []
    index = start_line - 2

    # Blank lines break a comment block after at least one comment is found.
    # 中文说明：
    # leading comments 是 docstring 之外的补充文档信号。
    # 只取紧贴函数上方的连续注释，避免把文件头 license、模块说明、
    # 或上一个函数的注释误算到当前函数身上。
    while index >= 0:
        line = source_lines[index].strip()
        if not line:
            if comments:
                break
            index -= 1
            continue
        if not line.startswith("#"):
            break
        comments.append(line.lstrip("#").strip())
        index -= 1

    comments.reverse()
    return "\n".join(comments)


def _argument_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    # Preserve the public call shape, including *args and **kwargs markers.
    # 中文说明：
    # 参数名用于报告和后续风格分析，不尝试读取类型注解或默认值。
    # 保留 *args/**kwargs 标记，可以快速看出函数是否是通用 wrapper。
    args = [arg.arg for arg in node.args.posonlyargs]
    args.extend(arg.arg for arg in node.args.args)
    args.extend(arg.arg for arg in node.args.kwonlyargs)
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return args


def _default_argument_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    names: list[str] = []
    positional_args = [*node.args.posonlyargs, *node.args.args]
    default_start = len(positional_args) - len(node.args.defaults)
    for arg in positional_args[default_start:]:
        names.append(arg.arg)
    for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        if default is not None:
            names.append(arg.arg)
    return names


def _function_info(
    file_path: Path,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
    parse_succeeded: bool,
) -> dict[str, Any]:
    # Each function record is intentionally JSON-serializable because it becomes
    # part of repo_profile.json and may be consumed by other agents/tools.
    # 中文说明：
    # repo_profile.json 是后续 smell 检测、风格学习、报告生成共享的中间产物。
    # 所以这里返回的字段都保持简单类型：字符串、数字、列表、布尔值。
    # 不返回 AST node 本身，是为了让结果可落盘、可 diff、可被其他 agent 读取。
    collector = _CallCollector()
    collector.visit(node)
    start_line = int(getattr(node, "lineno", 0) or 0)
    end_line = int(getattr(node, "end_lineno", start_line) or start_line)

    return {
        "file_path": str(file_path),
        "function_name": node.name,
        "argument_names": _argument_names(node),
        "default_argument_names": _default_argument_names(node),
        "start_line": start_line,
        "end_line": end_line,
        "docstring": ast.get_docstring(node) or "",
        "leading_comments": extract_leading_comments(source_lines, start_line),
        "function_length": max(0, end_line - start_line + 1),
        "called_function_names": sorted(set(collector.calls)),
        "parse_succeeded": parse_succeeded,
    }


def scan_file_functions(file_path: str | Path) -> dict[str, Any]:
    """Scan one Python file and return parse status plus function metadata."""
    path = Path(file_path)
    result: dict[str, Any] = {
        "file_path": str(path),
        "parse_succeeded": False,
        "error": "",
        "functions": [],
    }

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Keep scanning best-effort for repositories with mixed encodings.
        # 中文说明：
        # 遇到编码问题时不直接失败，而是用 replacement character 继续扫描。
        # 这样一个坏文件不会阻断整个仓库报告；错误会保留在文件级结果里。
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        result["error"] = str(exc)
        return result

    source_lines = source.splitlines()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        # Syntax errors are reported in the profile instead of failing the whole
        # repository scan.
        # 中文说明：
        # 语法错误本身也是重要信号，但 health scan 的职责是“尽量生成报告”。
        # 因此这里记录 parse_succeeded=False 和 error，而不是抛异常中断。
        result["error"] = f"{exc.__class__.__name__}: {exc}"
        return result

    result["parse_succeeded"] = True
    # ast.walk includes nested functions; they are useful for helper bloat checks.
    # 中文说明：
    # ast.walk 会包含嵌套函数。嵌套函数有时是合理闭包，也可能是 agent 临时
    # 堆 helper 的痕迹；保留它们能让后续规则看到真实函数数量。
    result["functions"] = [
        _function_info(path, node, source_lines, True)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    result["functions"].sort(key=lambda item: (item["start_line"], item["function_name"]))
    return result
