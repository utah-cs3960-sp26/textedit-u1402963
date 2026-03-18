"""
Tests for opening, editing, and saving the small.py, medium.py, and large.py
test files to verify the full open → edit → save workflow and that syntax
highlighting is correctly applied for each file size.
"""

import os
import shutil
import sys

import pytest
from PyQt6.QtWidgets import QApplication

from editor.highlighters.document_highlighter import DocumentHighlighter
from editor.window import MainWindow


SML_DIR = os.path.join(os.path.dirname(__file__), "..", "s-m-l-files")
SMALL_FILE = os.path.join(SML_DIR, "small.py")
MEDIUM_FILE = os.path.join(SML_DIR, "medium.py")
LARGE_FILE = os.path.join(SML_DIR, "large.py")


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance()
    if application is None:
        application = QApplication(sys.argv)
    yield application


@pytest.fixture
def window(app):
    w = MainWindow()
    yield w
    # Reset modified state so close doesn't prompt a save dialog
    w._document.mark_saved()
    if w._vdoc:
        w._close_virtual_doc()
    w.close()


class TestSmallFile:
    """Tests for opening, editing, and saving small.py (~173 lines)."""

    def test_open_small_file(self, window):
        window._open_file_path(SMALL_FILE)

        assert window._document.file_path == SMALL_FILE
        assert window._document.is_modified is False
        assert window._status_label.text() == "Saved"

        content = window.text_edit.toPlainText()
        assert "#!/usr/bin/env python3" in content
        assert len(content) > 0

    def test_open_small_file_sets_python_highlighter(self, window):
        window._open_file_path(SMALL_FILE)

        assert window.highlighter is not None
        assert isinstance(window.highlighter, DocumentHighlighter)
        assert window.highlighter._lang_id == "python"

    def test_edit_small_file_marks_dirty(self, window):
        window._open_file_path(SMALL_FILE)
        assert window._document.is_modified is False

        window.text_edit.setPlainText(window.text_edit.toPlainText() + "\n# edited")
        assert window._document.is_modified is True
        assert window._status_label.text() == "Unsaved"

    def test_save_small_file(self, window, tmp_path):
        src = tmp_path / "small.py"
        shutil.copy2(SMALL_FILE, src)
        window._open_file_path(str(src))

        original = window.text_edit.toPlainText()
        edited = original + "\n# test edit"
        window.text_edit.setPlainText(edited)
        assert window._document.is_modified is True

        window.save_file()

        assert window._document.is_modified is False
        assert window._status_label.text() == "Saved"
        assert not window.windowTitle().startswith("* ")
        assert src.read_text(encoding="utf-8") == edited

    def test_save_small_file_preserves_highlighter(self, window, tmp_path):
        src = tmp_path / "small.py"
        shutil.copy2(SMALL_FILE, src)
        window._open_file_path(str(src))

        window.text_edit.setPlainText("# modified\nprint('hello')")
        window.save_file()

        assert isinstance(window.highlighter, DocumentHighlighter)
        assert window.highlighter._lang_id == "python"
        assert window.highlighter.document() is window.text_edit.document()


class TestMediumFile:
    """Tests for opening, editing, and saving medium.py (~8739 lines)."""

    def _open_and_wait(self, window, path):
        """Open file and process events until deferred loading completes."""
        window._open_file_path(path)
        # Drain deferred chunk-loading events
        for _ in range(50):
            QApplication.processEvents()
            if not getattr(window.text_edit, '_deferred_lines', None):
                break

    def test_open_medium_file(self, window):
        self._open_and_wait(window, MEDIUM_FILE)

        assert window._document.file_path == MEDIUM_FILE
        assert window._document.is_modified is False
        assert window._status_label.text() == "Saved"

        content = window.text_edit.toPlainText()
        assert "#!/usr/bin/env python3" in content
        assert len(content) > 1000

    def test_open_medium_file_sets_python_highlighter(self, window):
        self._open_and_wait(window, MEDIUM_FILE)

        assert window.highlighter is not None
        assert isinstance(window.highlighter, DocumentHighlighter)
        assert window.highlighter._lang_id == "python"

    def test_edit_medium_file_marks_dirty(self, window):
        self._open_and_wait(window, MEDIUM_FILE)
        assert window._document.is_modified is False

        window.text_edit.setPlainText(window.text_edit.toPlainText() + "\n# edited")
        assert window._document.is_modified is True
        assert window._status_label.text() == "Unsaved"

    def test_save_medium_file(self, window, tmp_path):
        src = tmp_path / "medium.py"
        shutil.copy2(MEDIUM_FILE, src)
        self._open_and_wait(window, str(src))

        original_mtime = src.stat().st_mtime
        window.text_edit.setPlainText("# replaced content\nprint('hello')")
        assert window._document.is_modified is True

        window.save_file()

        assert window._document.is_modified is False
        assert window._status_label.text() == "Saved"
        assert not window.windowTitle().startswith("* ")
        assert src.read_text(encoding="utf-8") == "# replaced content\nprint('hello')"

    def test_save_medium_file_preserves_highlighter(self, window, tmp_path):
        src = tmp_path / "medium.py"
        shutil.copy2(MEDIUM_FILE, src)
        self._open_and_wait(window, str(src))

        window.text_edit.setPlainText("# modified medium\nprint('test')")
        window.save_file()

        assert isinstance(window.highlighter, DocumentHighlighter)
        assert window.highlighter._lang_id == "python"
        assert window.highlighter.document() is window.text_edit.document()


class TestLargeFile:
    """Tests for opening, editing, and saving large.py (~253 MB, virtual mode).

    These tests open the original file read-only (no 253 MB copy) except for
    the save test which creates a small temporary virtual-mode file.
    """

    def test_open_large_file_enters_virtual_mode(self, window):
        window._open_file_path(LARGE_FILE)

        assert window._document.file_path == LARGE_FILE
        assert window._document.is_modified is False
        assert window._vdoc is not None
        assert window.text_edit.virtual_mode is True

        window._close_virtual_doc()

    def test_open_large_file_shows_saved_after_highlighter_setup(self, window, tmp_path):
        """After deferred highlighter setup completes, status should still be 'Saved'."""
        src = self._make_virtual_file(tmp_path, "hl_test.py")
        window._open_file_path(str(src))
        # Directly trigger deferred highlighter setup (normally runs via QTimer)
        window._finish_large_file_setup(str(src))

        assert window._status_label.text() == "Saved"
        assert not window.windowTitle().startswith("* ")
        assert window.text_edit._virtual_dirty is False

        window._close_virtual_doc()

    def test_open_large_file_loads_content(self, window):
        window._open_file_path(LARGE_FILE)

        content = window.text_edit.toPlainText()
        assert len(content) > 0

        window._close_virtual_doc()

    def test_open_large_file_sets_highlighter(self, window):
        window._open_file_path(LARGE_FILE)

        # Highlighter is set synchronously before the deferred QTimer setup
        assert window.highlighter is not None

        window._close_virtual_doc()

    def test_save_large_file(self, window, tmp_path):
        """Create a file just over the virtual-mode threshold to test save."""
        src = self._make_virtual_file(tmp_path, "big_enough.py")
        window._open_file_path(str(src))
        assert window._vdoc is not None

        window.save_file()

        assert window._document.is_modified is False
        assert window._status_label.text() == "Saved"

        window._close_virtual_doc()

    def _make_virtual_file(self, tmp_path, name="virtual.py"):
        """Create a file just over the virtual-mode threshold."""
        from editor.models.virtual_document import VirtualDocument

        src = tmp_path / name
        threshold = VirtualDocument.LARGE_FILE_THRESHOLD
        line = "# " + "x" * 97 + "\n"
        lines_needed = (threshold // len(line.encode())) + 10
        src.write_text(line * lines_needed, encoding="utf-8")
        return src

    def test_edit_large_file_shows_unsaved(self, window, tmp_path):
        """Typing in a virtual-mode file should show 'Unsaved' status."""
        src = self._make_virtual_file(tmp_path)
        window._open_file_path(str(src))
        assert window._status_label.text() == "Saved"

        cursor = window.text_edit.textCursor()
        cursor.insertText("# new text")
        window.text_edit.setTextCursor(cursor)

        assert window._status_label.text() == "Unsaved"
        assert window.windowTitle().startswith("* ")

        window._close_virtual_doc()

    def test_edit_then_save_large_file_shows_saved(self, window, tmp_path):
        """After editing and saving a virtual-mode file, status returns to 'Saved'."""
        src = self._make_virtual_file(tmp_path)
        window._open_file_path(str(src))

        cursor = window.text_edit.textCursor()
        cursor.insertText("# added")
        window.text_edit.setTextCursor(cursor)
        assert window._status_label.text() == "Unsaved"

        window.save_file()

        assert window._status_label.text() == "Saved"
        assert not window.windowTitle().startswith("* ")

        window._close_virtual_doc()

    def test_close_large_file_cleans_up(self, window, tmp_path):
        src = self._make_virtual_file(tmp_path, "close_test.py")
        window._open_file_path(str(src))
        assert window._vdoc is not None

        window._close_virtual_doc()
        assert window._vdoc is None
        assert window.text_edit.virtual_mode is False
