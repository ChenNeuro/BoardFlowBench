"""Tests for isolated standalone demo benchmark workspaces."""
from __future__ import annotations

import json
import hashlib
import subprocess
from pathlib import Path

import pytest

from repo_manager_core.benchmark.workspace import activate_task, initialize_workspace
from repo_manager_core.benchmark.control import write_run_state
from repo_manager_core.board.board_io import load_board, save_board
from repo_manager_core.board.board_sync import update_task_status


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "boardflow"
    source = tmp_path / "demo-source"
    project.mkdir()
    source.mkdir()

    _git(source, "init", "-b", "main")
    _git(source, "config", "user.name", "Test")
    _git(source, "config", "user.email", "test@example.com")
    _write(source / "src" / "expense_lite" / "parser.py", "def normalize_date(value):\n    return value\n")
    _write(source / "tests" / "test_parser.py", "def test_seed():\n    assert True\n")
    _git(source, "add", ".")
    _git(source, "commit", "-m", "seed")
    seed = _git(source, "rev-parse", "HEAD")
    _git(source, "tag", "benchmark-seed-v1")

    _write(
        project / "benchmark" / "targets" / "expense_lite.yaml",
        "schema_version: 1\n"
        "id: expense_lite\n"
        "title: Expense Lite Bench Demo\n"
        "repo_url: https://example.invalid/demo.git\n"
        f"seed_commit: {seed}\n"
        'oracle_commit: "0000000000000000000000000000000000000000"\n'
        "task_directory: benchmark/tasks/expense_lite\n",
    )
    _write(
        project / "benchmark" / "tasks" / "expense_lite" / "b001_date_parser.yaml",
        "task_id: B001\n"
        "title: Date parser\n"
        "description: Assigned parser task.\n"
        "dependencies: []\n"
        "allowed_paths:\n"
        "  - src/expense_lite/parser.py\n",
    )
    _write(
        project / "benchmark" / "tasks" / "expense_lite" / "b002_csv_import.yaml",
        "task_id: B002\n"
        "title: CSV import\n"
        "description: Future CSV details must stay hidden.\n"
        "dependencies:\n"
        "  - B001\n"
        "allowed_paths:\n"
        "  - src/expense_lite/parser.py\n",
    )
    _write(project / "benchmark" / "templates" / "boardflow" / "AGENTS.md", "# Demo agents\n")
    _write(project / "benchmark" / "templates" / "boardflow" / "AI_CONTRACT.md", "# Demo contract\n")
    _write(project / "repo_manager_core" / "default_search_rules.json", "{}\n")
    _write(project / "repo_manager_core" / "default_smell_rules.json", "{}\n")
    _write(
        project / ".board" / "handoff.schema.json",
        '{"type":"object","properties":{"task_id":{"pattern":"^[A-Z][0-9]{3}$"}}}\n',
    )
    return project, source


def test_boardflow_init_clones_seed_and_exposes_only_assigned_task(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"

    result = initialize_workspace(
        project,
        "expense_lite",
        "boardflow_sequential",
        "B001",
        workspace,
        source_repo=source,
    )

    board = load_board(workspace)
    assigned = (workspace / ".board" / "assigned_task.yaml").read_text(encoding="utf-8")
    assert [task["id"] for task in board["tasks"]] == ["B001", "B002"]
    assert "P001" not in (workspace / "PROJECT_BOARD.md").read_text(encoding="utf-8")
    assert "Assigned parser task." in assigned
    assert "Future CSV details" not in assigned
    assert result["baseline_commit"] != result["seed_commit"]
    assert (workspace / ".repo_manager" / "search_rules.json").exists()
    assert (workspace / ".repo_manager" / "smell_rules.json").exists()
    assert ".repo_manager/search_rules.json" in _git(workspace, "ls-files")
    assert _git(workspace, "status", "--porcelain") == ""


def test_no_board_init_keeps_workspace_free_of_boardflow_files(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"

    result = initialize_workspace(
        project,
        "expense_lite",
        "no_board_baseline",
        "B001",
        workspace,
        source_repo=source,
    )

    assert not (workspace / ".board").exists()
    assert not (workspace / "PROJECT_BOARD.md").exists()
    assert not (workspace / "AGENTS.md").exists()
    assert result["task_spec"].endswith("b001_date_parser.yaml")
    assert _git(workspace, "status", "--porcelain") == ""


def test_init_refuses_to_overwrite_existing_workspace(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    workspace.mkdir()

    with pytest.raises(ValueError, match="workspace already exists"):
        initialize_workspace(
            project,
            "expense_lite",
            "boardflow_sequential",
            "B001",
            workspace,
            source_repo=source,
        )


def test_activate_task_requires_done_dependencies_and_commits_new_baseline(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    initialize_workspace(
        project,
        "expense_lite",
        "boardflow_sequential",
        "B001",
        workspace,
        source_repo=source,
    )

    run_manifest = _write_run_manifest(tmp_path, workspace, initialized=None)
    with pytest.raises(ValueError, match="task dependencies are not accepted: B001 is not DONE"):
        activate_task(project, workspace, "B002", run_manifest=run_manifest)

    handoff = workspace / ".board" / "handoffs" / "B001_test.json"
    handoff.write_text(
        '{"task_id":"B001","agent_id":"test","agent_role":"tester","status":"DONE",'
        '"files_changed":[],"commands_run":[{"command":"pytest","result":"PASS","notes":"passed"}],'
        '"tests":[{"name":"pytest","result":"PASS","notes":"passed"}],"temporary_files_created":[],'
        '"temporary_files_removed":[],"decisions":[],"risks":[],"next_recommended_step":"Continue."}\n',
        encoding="utf-8",
    )
    run_dir = Path(run_manifest).parent
    score = run_dir / "stages" / "B001" / "score.json"
    score.parent.mkdir(parents=True)
    score.write_text(
        json.dumps(
            {
                "task_id": "B001",
                "phase": "completion",
                "condition": "full_boardflow",
                "hard_gate_pass": True,
                "scope_control": {"details": {"baseline_commit": "baseline"}},
                "correctness": {
                    "details": {
                        "oracle": {
                            "seed_commit": "seed",
                            "oracle_pack_commit": "oracle",
                        }
                    }
                },
            }
        )
    )
    evidence = workspace / ".board" / "evidence" / "B001.json"
    evidence.write_text(
        '{"schema_version":1,"kind":"workspace_mirror","task_id":"B001",'
        '"condition":"full_boardflow","gate_pass":true,"baseline_commit":"baseline",'
        '"evaluated_head":"head","seed_commit":"seed","oracle_pack_commit":"oracle"}\n',
        encoding="utf-8",
    )
    board = load_board(workspace)
    board["tasks"][0]["current_handoff"] = ".board/handoffs/B001_test.json"
    board["tasks"][0]["acceptance_evidence"] = ".board/evidence/B001.json"
    save_board(board, workspace)
    update_task_status(workspace, "B001", "DONE", owner="tester", completion_validated=True)
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-m", "accept B001")

    _write_external_evidence(run_dir, workspace, score)
    result = activate_task(project, workspace, "B002", run_manifest=run_manifest)

    assigned = (workspace / ".board" / "assigned_task.yaml").read_text(encoding="utf-8")
    assert "Future CSV details must stay hidden." in assigned
    assert result["task_id"] == "B002"
    assert _git(workspace, "status", "--porcelain") == ""


def test_activate_task_rejects_empty_handoff_even_when_file_exists(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    initialize_workspace(project, "expense_lite", "full_boardflow", "B001", workspace, source_repo=source)
    run_manifest = _write_run_manifest(tmp_path, workspace, initialized=None)
    handoff = workspace / ".board" / "handoffs" / "B001_empty.json"
    handoff.write_text("{}\n", encoding="utf-8")
    evidence = workspace / ".board" / "evidence" / "B001.json"
    score = Path(run_manifest).parent / "stages" / "B001" / "score.json"
    score.parent.mkdir(parents=True)
    score.write_text(
        json.dumps(
            {
                "task_id": "B001",
                "phase": "completion",
                "condition": "full_boardflow",
                "hard_gate_pass": True,
                "scope_control": {"details": {"baseline_commit": "baseline"}},
                "correctness": {
                    "details": {
                        "oracle": {
                            "seed_commit": "seed",
                            "oracle_pack_commit": "oracle",
                        }
                    }
                },
            }
        )
    )
    evidence.write_text(
        '{"schema_version":1,"kind":"workspace_mirror","task_id":"B001",'
        '"condition":"full_boardflow","gate_pass":true,"baseline_commit":"baseline",'
        '"evaluated_head":"head","seed_commit":"seed","oracle_pack_commit":"oracle"}\n',
        encoding="utf-8",
    )
    board = load_board(workspace)
    board["tasks"][0]["status"] = "DONE"
    board["tasks"][0]["current_handoff"] = ".board/handoffs/B001_empty.json"
    board["tasks"][0]["acceptance_evidence"] = ".board/evidence/B001.json"
    save_board(board, workspace)
    project_board = workspace / "PROJECT_BOARD.md"
    project_board.write_text(project_board.read_text().replace("| B001 | Date parser | TODO |", "| B001 | Date parser | DONE |"))
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-m", "fake empty handoff")
    _write_external_evidence(Path(run_manifest).parent, workspace, score)

    with pytest.raises(ValueError, match="handoff required for B001 but none was found"):
        activate_task(project, workspace, "B002", run_manifest=run_manifest)


def test_activate_task_rejects_external_evidence_changed_after_signing(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    initialize_workspace(project, "expense_lite", "full_boardflow", "B001", workspace, source_repo=source)
    run_manifest = _write_run_manifest(tmp_path, workspace, initialized=None)
    _accept_b001_for_activation(workspace, run_manifest)
    evidence_path = Path(run_manifest).parent / "stages" / "B001" / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["tampered"] = True
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

    with pytest.raises(ValueError, match="external stage evidence differs from signed run manifest"):
        activate_task(project, workspace, "B002", run_manifest=run_manifest)


def test_activate_task_rejects_clean_commit_after_finalization(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    initialize_workspace(project, "expense_lite", "full_boardflow", "B001", workspace, source_repo=source)
    run_manifest = _write_run_manifest(tmp_path, workspace, initialized=None)
    _accept_b001_for_activation(workspace, run_manifest)
    (workspace / "hidden.txt").write_text("changed after finalization\n", encoding="utf-8")
    _git(workspace, "add", "hidden.txt")
    _git(workspace, "commit", "-m", "hidden post-finalize commit")

    with pytest.raises(ValueError, match="acceptance evidence is not bound to current HEAD"):
        activate_task(project, workspace, "B002", run_manifest=run_manifest)


def test_activate_task_always_requires_current_stage_even_without_declared_dependency(tmp_path):
    project, source = _fixture(tmp_path)
    task = project / "benchmark" / "tasks" / "expense_lite" / "b002_csv_import.yaml"
    task.write_text(task.read_text(encoding="utf-8").replace("dependencies:\n  - B001\n", "dependencies: []\n"), encoding="utf-8")
    workspace = tmp_path / "run"
    initialize_workspace(project, "expense_lite", "full_boardflow", "B001", workspace, source_repo=source)
    run_manifest = _write_run_manifest(tmp_path, workspace, initialized=None)

    with pytest.raises(ValueError, match="B001 is not DONE"):
        activate_task(project, workspace, "B002", run_manifest=run_manifest)


def test_activate_task_replays_interrupted_generated_control_commits(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    initialize_workspace(project, "expense_lite", "full_boardflow", "B001", workspace, source_repo=source)
    run_manifest = _write_run_manifest(tmp_path, workspace, initialized=None)
    _accept_b001_for_activation(workspace, run_manifest)
    from repo_manager_core.benchmark.control import load_run_state
    state = load_run_state(run_manifest)
    state["status"] = "activating_task"
    state["pending_task"] = "B002"
    write_run_state(Path(run_manifest).parent, state)

    first = activate_task(project, workspace, "B002", run_manifest=run_manifest)
    second = activate_task(project, workspace, "B002", run_manifest=run_manifest)

    assert first["task_id"] == "B002"
    assert second["task_id"] == "B002"
    assert _git(workspace, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("condition", "expected", "absent"),
    [
        ("native_instructions", "AGENTS.md", ".board"),
        ("native_docs_handoff", "HANDOFF.md", ".board"),
        ("no_board_baseline", "src/expense_lite/parser.py", ".board"),
    ],
)
def test_condition_injection_boundaries(tmp_path, condition, expected, absent):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    _write(project / "benchmark" / "templates" / "native" / "INSTRUCTIONS.md", "# Native\n")
    initialize_workspace(project, "expense_lite", condition, "B001", workspace, source_repo=source)
    assert (workspace / expected).exists()
    assert not (workspace / absent).exists()


def _write_run_manifest(tmp_path: Path, workspace: Path, initialized) -> Path:
    run_dir = tmp_path / "results" / "run-1"
    baseline = initialized["baseline_commit"] if initialized else _load_baseline(workspace)
    return write_run_state(
        run_dir,
        {
            "run_id": "run-1",
            "target": "expense_lite",
            "condition": "full_boardflow",
            "workspace": str(workspace.resolve()),
            "oracle_root": str((tmp_path / "oracle").resolve()),
            "seed_commit": _git(workspace, "rev-list", "--max-parents=0", "HEAD"),
            "oracle_commit": "0" * 40,
            "results_dir": str((tmp_path / "results").resolve()),
            "tasks": ["B001", "B002"],
            "current_task": "B001",
            "baseline_commit": baseline,
            "stages": [],
            "status": "awaiting_agent",
        },
    )


def _load_baseline(workspace: Path) -> str:
    from repo_manager_core.board.board_io import load_yaml
    return str(load_yaml(workspace / ".board" / "run.yaml")["stage_baselines"]["B001"])


def _write_external_evidence(run_dir: Path, workspace: Path, score: Path) -> None:
    seed = _git(workspace, "rev-list", "--max-parents=0", "HEAD")
    baseline = _load_baseline(workspace)
    score_data = json.loads(score.read_text(encoding="utf-8"))
    score_data["scope_control"]["details"]["baseline_commit"] = baseline
    score_data["correctness"]["details"]["oracle"]["seed_commit"] = seed
    score_data["correctness"]["details"]["oracle"]["oracle_pack_commit"] = "0" * 40
    score.write_text(json.dumps(score_data), encoding="utf-8")
    evidence = {
        "task_id": "B001",
        "condition": "full_boardflow",
        "gate_pass": True,
        "baseline_commit": baseline,
        "evaluated_head": "evaluated",
        "finalized_commit": _git(workspace, "rev-parse", "HEAD"),
        "seed_commit": seed,
        "oracle_pack_commit": "0" * 40,
        "score_file": str(score),
        "score_sha256": hashlib.sha256(score.read_bytes()).hexdigest(),
    }
    path = run_dir / "stages" / "B001" / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    from repo_manager_core.benchmark.control import load_run_state
    state = load_run_state(run_dir / "run.json")
    state["stages"] = [evidence]
    write_run_state(run_dir, state)


def _accept_b001_for_activation(workspace: Path, run_manifest: Path) -> None:
    handoff = workspace / ".board" / "handoffs" / "B001_test.json"
    handoff.write_text(
        '{"task_id":"B001","agent_id":"test","agent_role":"tester","status":"DONE",'
        '"files_changed":[],"commands_run":[{"command":"pytest","result":"PASS","notes":"passed"}],'
        '"tests":[{"name":"pytest","result":"PASS","notes":"passed"}],"temporary_files_created":[],'
        '"temporary_files_removed":[],"decisions":[],"risks":[],"next_recommended_step":"Continue."}\n',
        encoding="utf-8",
    )
    mirror = workspace / ".board" / "evidence" / "B001.json"
    mirror.write_text(
        '{"schema_version":1,"kind":"workspace_mirror","task_id":"B001",'
        '"condition":"full_boardflow","gate_pass":true,"baseline_commit":"baseline",'
        '"evaluated_head":"head","seed_commit":"seed","oracle_pack_commit":"oracle"}\n',
        encoding="utf-8",
    )
    board = load_board(workspace)
    board["tasks"][0]["current_handoff"] = ".board/handoffs/B001_test.json"
    board["tasks"][0]["acceptance_evidence"] = ".board/evidence/B001.json"
    save_board(board, workspace)
    update_task_status(workspace, "B001", "DONE", owner="tester", completion_validated=True)
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "-m", "accept B001")
    score = run_manifest.parent / "stages" / "B001" / "score.json"
    score.parent.mkdir(parents=True, exist_ok=True)
    score.write_text(
        json.dumps(
            {
                "task_id": "B001",
                "phase": "completion",
                "condition": "full_boardflow",
                "hard_gate_pass": True,
                "scope_control": {"details": {"baseline_commit": "baseline"}},
                "correctness": {"details": {"oracle": {"seed_commit": "seed", "oracle_pack_commit": "oracle"}}},
            }
        ),
        encoding="utf-8",
    )
    _write_external_evidence(run_manifest.parent, workspace, score)
