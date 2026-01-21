import os
import sys

import pytest

# Use offscreen platform to prevent GUI windows during tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create a single QApplication instance for all tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
