from pathlib import Path

from core.scan_file_functions import scan_file_functions
from core.scan_repo_functions import scan_repo_functions

FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_file_extracts_function_metadata():
    sample = FIXTURES / "sample_repo" / "pkg" / "sample.py"
    result = scan_file_functions(sample)

    assert result["parse_succeeded"] is True
    assert [fn["function_name"] for fn in result["functions"]] == ["outer", "helper"]
    outer = result["functions"][0]
    assert outer["argument_names"] == ["value"]
    assert outer["docstring"] == "Example docstring."
    assert outer["leading_comments"] == "prepares value"
    assert outer["called_function_names"] == ["helper"]


def test_scan_repo_skips_ignored_directories():
    result = scan_repo_functions(Path(FIXTURES / "sample_repo"))

    assert result["python_file_count"] == 1
    assert result["function_count"] == 2
    assert {fn["function_name"] for fn in result["functions"]} == {"outer", "helper"}
