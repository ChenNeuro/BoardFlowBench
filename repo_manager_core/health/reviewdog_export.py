"""Export Repo Manager health findings as reviewdog rdjsonl diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SEVERITY_MAP = {
    "high": "ERROR",
    "medium": "WARNING",
    "low": "INFO",
}


def export_diagnostics(
    smell_report: dict[str, Any],
    *,
    repo: str | Path,
    repo_profile: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Convert file-backed smell warnings into reviewdog diagnostics."""
    root = Path(repo).resolve()
    line_index = _function_line_index(repo_profile or {}, root)
    diagnostics = []

    for warning in smell_report.get("warnings", []):
        path = _relative_file_path(warning.get("file"), root)
        if path is None:
            continue
        function = str(warning.get("function") or "")
        line = line_index.get((path, function), 1)
        diagnostics.append(
            {
                "message": _message(warning),
                "location": {
                    "path": path,
                    "range": {"start": {"line": line, "column": 1}},
                },
                "severity": SEVERITY_MAP.get(str(warning.get("severity")), "WARNING"),
                "code": {"value": str(warning.get("type") or "repo_manager_health")},
                "source": {"name": "repo-manager-health"},
            }
        )

    return diagnostics


def write_rdjsonl(diagnostics: list[dict[str, Any]], output: str | Path) -> None:
    """Write one reviewdog diagnostic JSON object per line."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(diagnostic, sort_keys=True) for diagnostic in diagnostics]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _function_line_index(repo_profile: dict[str, Any], root: Path) -> dict[tuple[str, str], int]:
    index = {}
    for function in repo_profile.get("functions", []):
        path = _relative_file_path(function.get("file_path"), root)
        name = str(function.get("function_name") or "")
        line = function.get("start_line")
        if path is not None and name and isinstance(line, int) and line > 0:
            index[(path, name)] = line
    return index


def _relative_file_path(value: Any, root: Path) -> str | None:
    if not value:
        return None
    path = Path(str(value))
    candidate = path if path.is_absolute() else root / path
    candidate = candidate.resolve()
    if not candidate.is_file():
        return None
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError:
        return None


def _message(warning: dict[str, Any]) -> str:
    smell_type = str(warning.get("type") or "repo_manager_health")
    reason = str(warning.get("reason") or "Repo Manager health signal.")
    suggestion = str(warning.get("suggestion") or "")
    return f"[{smell_type}] {reason}" + (f" Suggestion: {suggestion}" if suggestion else "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to smell_report.json.")
    parser.add_argument("--output", required=True, help="Destination rdjsonl path.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--profile", help="Optional repo_profile.json for function line numbers.")
    args = parser.parse_args(argv)

    smell_report = json.loads(Path(args.input).read_text(encoding="utf-8"))
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8")) if args.profile else None
    diagnostics = export_diagnostics(smell_report, repo=args.repo, repo_profile=profile)
    write_rdjsonl(diagnostics, args.output)
    print(f"Wrote {len(diagnostics)} reviewdog diagnostics to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
