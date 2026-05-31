# Template Demos

Three demonstration projects for Repo Manager skills.

## clean_case

A well-structured Python project with clean naming and architecture. Should produce zero or minimal warnings from Code Health Review.

- `calculator.py` — arithmetic helpers with docstrings
- `main.py` — entry point
- `reporting.py` — reporting functions

## messy_ai_case

An intentionally messy AI-generated project with patch functions, wrappers, duplicate helpers, and suspicious file names. Designed to trigger all smell detectors.

- `app.py` — entry point calling patch functions
- `fix_parser.py` — contains wrapper functions and unused helpers
- `parser_final.py` — contains `parse_date_safe`, `parse_date_fixed`, `normalize_date_patch`, and other patch-like names

## expense_lite

A synthetic Python project demonstrating a multi-agent sequential workflow (T001→T002→T003→T004). Used by the Agent Bridge skill to demonstrate task handoff.

- `src/expense_lite/` — the expense processing package
- `tests/` — unit tests
- `data/` — sample expense JSON
- `artifacts/` — generated report output directory
- `.scratch/` — temporary workspace

Run: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=template/expense_lite/src python3 -m unittest discover -s template/expense_lite/tests -p 'test_*.py'`
