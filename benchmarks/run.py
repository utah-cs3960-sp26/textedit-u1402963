#!/usr/bin/env python3
"""Run GUI timing benchmarks for the text editor.

Usage:
    python benchmarks/run.py              # run all benchmarks
    python benchmarks/run.py -k open      # run only file-open benchmarks
    python benchmarks/run.py -k small     # run only small-file benchmarks
"""
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, "src"))

# Run on-screen for consistency with real user experience.
# Set QT_QPA_PLATFORM=offscreen before invoking to run headless.

import pytest

sys.exit(
    pytest.main(
        [
            os.path.dirname(os.path.abspath(__file__)),
            "-v",
            "-s",
            "--tb=short",
            "--no-cov",
            "--no-header",
        ]
        + sys.argv[1:]
    )
)
