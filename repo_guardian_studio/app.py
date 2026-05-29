"""Streamlit GUI for RepoGuardian Studio."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.analyze_repo_structure import analyze_repo_structure
from core.call_agent import call_agent
from core.detect_function_smells import detect_function_smells
from core.generate_review_prompt import generate_review_prompt
from core.scan_file_functions import scan_file_functions
from core.scan_repo_functions import scan_repo_functions


ROOT = Path(__file__).resolve().parent


def _default_repo() -> str:
    return str(ROOT / "demo_repo" / "messy_ai_case")


def _function_dataframe(functions: list[dict]) -> pd.DataFrame:
    rows = []
    for fn in functions:
        rows.append(
            {
                "file": fn["file_path"],
                "function": fn["function_name"],
                "args": ", ".join(fn["argument_names"]),
                "lines": f"{fn['start_line']}-{fn['end_line']}",
                "length": fn["function_length"],
                "calls": ", ".join(fn["called_function_names"]),
                "docstring": bool(fn["docstring"]),
            }
        )
    return pd.DataFrame(rows)


def _warnings_dataframe(warnings: list[dict]) -> pd.DataFrame:
    if not warnings:
        return pd.DataFrame(columns=["severity", "type", "file", "function", "reason", "suggestion"])
    return pd.DataFrame(warnings)


st.set_page_config(page_title="RepoGuardian Studio", layout="wide")
st.title("RepoGuardian Studio")

repo_path = st.text_input("Repo path", value=_default_repo())
file_path = st.text_input("File path", value=str(ROOT / "demo_repo" / "messy_ai_case" / "parser_final.py"))
user_question = st.text_area("Optional review question", value="", height=80)

buttons = st.columns(4)
check_repo = buttons[0].button("Check Repo", use_container_width=True)
check_file = buttons[1].button("Check File", use_container_width=True)
detect_smells = buttons[2].button("Detect Function Smells", use_container_width=True)
generate_review = buttons[3].button("Generate LLM Review", use_container_width=True)

if "repo_profile" not in st.session_state:
    st.session_state.repo_profile = {}
if "functions" not in st.session_state:
    st.session_state.functions = []
if "smell_report" not in st.session_state:
    st.session_state.smell_report = {"summary": {}, "warnings": []}
if "agent_review" not in st.session_state:
    st.session_state.agent_review = ""

if check_repo:
    profile = scan_repo_functions(repo_path)
    structure = analyze_repo_structure(repo_path)
    profile["structure_warnings"] = structure["warnings"]
    profile["structure"] = structure
    st.session_state.repo_profile = profile
    st.session_state.functions = profile["functions"]
    st.success(f"Scanned {profile['python_file_count']} Python files and found {profile['function_count']} functions.")

if check_file:
    result = scan_file_functions(file_path)
    st.session_state.repo_profile = {
        "repo_path": str(Path(file_path).parent),
        "python_file_count": 1,
        "parsed_file_count": 1 if result["parse_succeeded"] else 0,
        "failed_file_count": 0 if result["parse_succeeded"] else 1,
        "function_count": len(result["functions"]),
        "files": [result],
        "functions": result["functions"],
        "structure_warnings": [],
    }
    st.session_state.functions = result["functions"]
    if result["parse_succeeded"]:
        st.success(f"Scanned file and found {len(result['functions'])} functions.")
    else:
        st.error(result["error"])

if detect_smells:
    if not st.session_state.functions:
        profile = scan_repo_functions(repo_path)
        structure = analyze_repo_structure(repo_path)
        profile["structure_warnings"] = structure["warnings"]
        profile["structure"] = structure
        st.session_state.repo_profile = profile
        st.session_state.functions = profile["functions"]
    smell_report = detect_function_smells(st.session_state.functions)
    smell_report["warnings"].extend(st.session_state.repo_profile.get("structure_warnings", []))
    smell_report["summary"]["warning_count"] = len(smell_report["warnings"])
    st.session_state.smell_report = smell_report
    st.success(f"Detected {len(smell_report['warnings'])} suspicious warnings.")

if generate_review:
    if not st.session_state.functions:
        profile = scan_repo_functions(repo_path)
        structure = analyze_repo_structure(repo_path)
        profile["structure_warnings"] = structure["warnings"]
        profile["structure"] = structure
        st.session_state.repo_profile = profile
        st.session_state.functions = profile["functions"]
    if not st.session_state.smell_report.get("warnings"):
        smell_report = detect_function_smells(st.session_state.functions)
        smell_report["warnings"].extend(st.session_state.repo_profile.get("structure_warnings", []))
        smell_report["summary"]["warning_count"] = len(smell_report["warnings"])
        st.session_state.smell_report = smell_report
    prompt = generate_review_prompt(
        st.session_state.repo_profile,
        st.session_state.smell_report,
        user_question or None,
    )
    st.session_state.agent_review = call_agent(prompt)

repo_tab, functions_tab, smells_tab, review_tab, chat_tab = st.tabs(
    ["Repo Summary", "Function Index", "Function Smells", "Agent Review", "Agent Chat placeholder"]
)

with repo_tab:
    profile = st.session_state.repo_profile
    if profile:
        st.json(
            {
                "repo_path": profile.get("repo_path"),
                "python_file_count": profile.get("python_file_count"),
                "parsed_file_count": profile.get("parsed_file_count"),
                "failed_file_count": profile.get("failed_file_count"),
                "function_count": profile.get("function_count"),
            }
        )
        structure = profile.get("structure")
        if structure:
            st.subheader("Structure warnings")
            st.dataframe(_warnings_dataframe(structure["warnings"]), use_container_width=True)
    else:
        st.info("Run Check Repo or Check File to see a summary.")

with functions_tab:
    if st.session_state.functions:
        st.dataframe(_function_dataframe(st.session_state.functions), use_container_width=True)
    else:
        st.info("No functions scanned yet.")

with smells_tab:
    warnings = st.session_state.smell_report.get("warnings", [])
    if warnings:
        st.dataframe(_warnings_dataframe(warnings), use_container_width=True)
    else:
        st.info("Run Detect Function Smells to see suspicious findings.")

with review_tab:
    if st.session_state.agent_review:
        st.markdown(st.session_state.agent_review)
    else:
        st.info("Run Generate LLM Review to create a mock or API-backed report.")

with chat_tab:
    st.info("Agent chat is a placeholder for future interactive review adapters.")

