"""GUI timing tests: scroll operations."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtTest import QTest

from benchmarks.conftest import TARGET_FRAME_MS_LARGE

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

    def test_gui_timing_scroll_large(self, window, qapp, run_direct, large_file_path):
        from editor.models.virtual_document import VirtualDocument

        shared_vdoc = VirtualDocument(large_file_path)

        window._vdoc = shared_vdoc
        window._document.file_path = large_file_path
        window._document.set_content("", mark_as_saved=True)
        window.text_edit.enter_virtual_mode(shared_vdoc, window._virtual_scrollbar)
        window._setup_highlighter(large_file_path, "")
        if window.highlighter:
            window.highlighter.set_batch_limit(100)
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

        passed = run_direct(
            "Scroll large.txt (30 pages down + 30 up) [virtual mode]",
            scroll, setup=setup, target_ms=TARGET_FRAME_MS_LARGE,
        )

        if window.text_edit.virtual_mode:
            window.text_edit.exit_virtual_mode()
        window._vdoc = None
        shared_vdoc.close()

        assert passed, "Avg P95 frame time exceeds 60 fps target"
