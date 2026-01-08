import pytest
import sys
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication
from editor.window import MainWindow


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance()
    if application is None:
        application = QApplication(sys.argv)
    yield application


@pytest.fixture
def window(app):
    return MainWindow()


class TestUnsavedChangesTracking:
    def test_initial_state_is_saved(self, window):
        assert window._is_modified is False

    def test_typing_marks_unsaved(self, window):
        window.text_edit.setPlainText("new content")
        assert window._is_modified is True

    def test_undo_to_original_marks_saved(self, window):
        window.text_edit.setPlainText("some text")
        assert window._is_modified is True
        window.text_edit.setPlainText("")
        assert window._is_modified is False

    def test_save_resets_modified_flag(self, window, tmp_path):
        test_file = tmp_path / "test.txt"
        window.text_edit.setPlainText("content to save")
        assert window._is_modified is True

        with patch("editor.window.QFileDialog.getSaveFileName") as mock_save:
            mock_save.return_value = (str(test_file), "")
            window.save_file()

        assert window._is_modified is False

    def test_open_file_resets_modified_flag(self, window, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content")

        window.text_edit.setPlainText("unsaved changes")
        assert window._is_modified is True

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open, \
             patch.object(window, "_prompt_save_changes", return_value="discard"):
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        assert window._is_modified is False


class TestStatusLabel:
    def test_status_label_shows_saved_initially(self, window):
        assert window._status_label.text() == "Saved"

    def test_status_label_shows_unsaved_after_edit(self, window):
        window.text_edit.setPlainText("edited content")
        assert window._status_label.text() == "Unsaved"


class TestTitleAsterisk:
    def test_title_has_asterisk_when_unsaved(self, window):
        window.text_edit.setPlainText("modified content")
        assert window.windowTitle().startswith("* ")

    def test_title_no_asterisk_when_saved(self, window):
        assert not window.windowTitle().startswith("* ")
