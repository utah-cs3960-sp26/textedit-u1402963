"""GUI timing tests: scroll operations."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtTest import QTest

SCROLL_STEPS = 30


class TestGuiTimingScroll:
    def _run_scroll(self, window, qapp, run_direct, content, label):
        window.text_edit.setPlainText(content)
        qapp.processEvents()

        def setup():
            cursor = window.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            window.text_edit.setTextCursor(cursor)

        def scroll():
            for _ in range(SCROLL_STEPS):
                QTest.keyClick(window.text_edit, Qt.Key.Key_PageDown)
                qapp.processEvents()
            for _ in range(SCROLL_STEPS):
                QTest.keyClick(window.text_edit, Qt.Key.Key_PageUp)
                qapp.processEvents()

        return run_direct(label, scroll, setup=setup)

    def test_gui_timing_scroll_small(self, window, qapp, run_direct, small_content):
        passed = self._run_scroll(
            window, qapp, run_direct, small_content,
            "Scroll small.txt (30 pages down + 30 up)",
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"

    def test_gui_timing_scroll_medium(self, window, qapp, run_direct, medium_content):
        passed = self._run_scroll(
            window, qapp, run_direct, medium_content,
            "Scroll medium.txt (30 pages down + 30 up)",
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"
