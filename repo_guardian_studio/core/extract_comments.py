"""Small helpers for extracting comments near functions."""

from __future__ import annotations


def extract_leading_comments(source_lines: list[str], start_line: int) -> str:
    """Return contiguous comments immediately above a function definition."""
    comments: list[str] = []
    index = start_line - 2

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

