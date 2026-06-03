#!/usr/bin/env python3
"""Run the BoardFlowBench scorer."""

from __future__ import annotations

import sys
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.benchmark_scorer import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
