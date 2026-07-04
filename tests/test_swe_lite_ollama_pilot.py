import json
import tempfile
import unittest
from pathlib import Path

from scripts.swe_lite_ollama_pilot import (
    classify_validation,
    parse_replacement_payload,
    prepare_replacements,
)


ALLOWED = {"astropy/modeling/separable.py"}


class SweLiteOllamaPilotTests(unittest.TestCase):
    def test_parse_replacement_payload_requires_json_object(self):
        payload = parse_replacement_payload('{"skill_invocation": "none", "edits": []}')

        self.assertEqual(payload["skill_invocation"], "none")
        with self.assertRaises(json.JSONDecodeError):
            parse_replacement_payload("not-json")

    def test_prepare_replacements_accepts_exact_bounded_edit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "astropy/modeling/separable.py"
            source.parent.mkdir(parents=True)
            source.write_text("old\n", encoding="utf-8")
            payload = {
                "skill_invocation": "repoflow-task-agent",
                "edits": [{"path": "astropy/modeling/separable.py", "old": "old", "new": "new"}],
            }

            pending = prepare_replacements(workspace, payload, ALLOWED, "repoflow-task-agent")

            self.assertEqual(pending, {"astropy/modeling/separable.py": "new\n"})

    def test_prepare_replacements_rejects_wrong_invocation_and_unlisted_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "astropy/modeling/separable.py"
            source.parent.mkdir(parents=True)
            source.write_text("old\n", encoding="utf-8")
            payload = {
                "skill_invocation": "none",
                "edits": [{"path": "test_patch.diff", "old": "old", "new": "new"}],
            }

            with self.assertRaisesRegex(ValueError, "skill_invocation"):
                prepare_replacements(workspace, payload, ALLOWED, "repoflow-task-agent")
            with self.assertRaisesRegex(ValueError, "evaluator path is forbidden"):
                prepare_replacements(workspace, payload, {"test_patch.diff"}, "none")

    def test_prepare_replacements_rejects_non_unique_old_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "astropy/modeling/separable.py"
            source.parent.mkdir(parents=True)
            source.write_text("old\nold\n", encoding="utf-8")
            payload = {
                "skill_invocation": "none",
                "edits": [{"path": "astropy/modeling/separable.py", "old": "old", "new": "new"}],
            }

            with self.assertRaisesRegex(ValueError, "occurs 2 times"):
                prepare_replacements(workspace, payload, ALLOWED, "none")

    def test_prepare_replacements_rejects_no_op(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source = workspace / "astropy/modeling/separable.py"
            source.parent.mkdir(parents=True)
            source.write_text("old\n", encoding="utf-8")
            payload = {
                "skill_invocation": "none",
                "edits": [{"path": "astropy/modeling/separable.py", "old": "old", "new": "old"}],
            }

            with self.assertRaisesRegex(ValueError, "no-op"):
                prepare_replacements(workspace, payload, ALLOWED, "none")

    def test_classify_validation_separates_environment_and_test_failures(self):
        environment = [{"returncode": 1, "stdout": "", "stderr": "ModuleNotFoundError: No module named 'x'"}]
        test_failure = [{"returncode": 1, "stdout": "FAILED test_nested", "stderr": ""}]

        self.assertEqual(
            classify_validation(environment, None),
            ("dependency_environment_failure", "dependency_or_environment_failure"),
        )
        self.assertEqual(classify_validation(test_failure, None), ("failed", "repository_test_failure"))


if __name__ == "__main__":
    unittest.main()
