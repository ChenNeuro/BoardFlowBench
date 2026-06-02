"""Tests for deterministic acceptance-evidence integrity."""
from __future__ import annotations

import json

from repo_manager_core.board.evidence import validate_acceptance_evidence


def test_acceptance_evidence_rejects_workspace_local_score(tmp_path):
    repo = tmp_path / "repo"
    score = repo / ".board" / "score.json"
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
    evidence = repo / ".board" / "evidence" / "B001.json"
    evidence.parent.mkdir()
    evidence.write_text(
        json.dumps(
            {
                "task_id": "B001",
                "condition": "full_boardflow",
                "gate_pass": True,
                "baseline_commit": "baseline",
                "evaluated_head": "head",
                "seed_commit": "seed",
                "oracle_pack_commit": "oracle",
                "score_file": str(score),
            }
        )
    )

    violations = validate_acceptance_evidence(
        repo,
        {"id": "B001", "acceptance_evidence": ".board/evidence/B001.json"},
    )

    assert "B001 acceptance score must be stored outside the workspace" in violations
