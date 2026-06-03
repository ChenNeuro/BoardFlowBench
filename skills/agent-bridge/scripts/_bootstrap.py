"""Import-path bootstrap for globally installed skill scripts."""

from __future__ import annotations

import sys
from pathlib import Path


def bootstrap_repo_manager_core() -> None:
    """Add a nearby repo_manager_core package to sys.path when available."""
    script_path = Path(__file__).resolve()
    # Global skill installs copy repo_manager_core next to the skill directory.
    # Checking cwd first also supports running from this source repo without install.
    candidates = [Path.cwd(), *script_path.parents]
    for base in candidates:
        if (base / "repo_manager_core").is_dir():
            path = str(base)
            if path not in sys.path:
                sys.path.insert(0, path)
            return
