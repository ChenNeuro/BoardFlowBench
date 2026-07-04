import os
import stat
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_swe_lite_smoke import remove_tree


class PrepareSweLiteSmokeTests(unittest.TestCase):
    def test_remove_tree_handles_readonly_files(self):
        with tempfile.TemporaryDirectory() as parent_name:
            target = Path(parent_name) / "workspace"
            target.mkdir()
            readonly = target / "git-object"
            readonly.write_text("content", encoding="utf-8")
            os.chmod(readonly, stat.S_IREAD)

            remove_tree(target)

            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
