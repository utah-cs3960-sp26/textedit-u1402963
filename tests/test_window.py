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
    w = MainWindow()
    yield w
    w.close()


@pytest.fixture(autouse=True)
def no_dialogs():
    """Prevent any dialog popups during tests by patching QMessageBox and QFileDialog."""
    with patch("editor.window.QMessageBox.critical") as mock_critical, \
         patch("editor.window.QMessageBox.question") as mock_question, \
         patch("editor.window.QMessageBox.warning") as mock_warning, \
         patch("editor.window.QMessageBox.information") as mock_info:
        mock_question.return_value = MagicMock()
        yield {
            "critical": mock_critical,
            "question": mock_question,
            "warning": mock_warning,
            "information": mock_info,
        }


class TestUnsavedChangesTracking:
    def test_initial_state_is_saved(self, window):
        assert window._is_modified is False
        assert window._status_label.text() == "Saved"
        assert not window.windowTitle().startswith("* ")

    def test_typing_marks_unsaved(self, window):
        window.text_edit.setPlainText("new content")

        assert window._is_modified is True
        assert window._status_label.text() == "Unsaved"
        assert window.windowTitle().startswith("* ")

    def test_restoring_original_text_marks_saved(self, window):
        window.text_edit.setPlainText("some text")
        assert window._is_modified is True

        window.text_edit.setPlainText("")
        assert window._is_modified is False
        assert window._status_label.text() == "Saved"


class TestSaveFile:
    def test_save_writes_file_and_updates_ui(self, window, tmp_path):
        test_file = tmp_path / "test.txt"
        window.text_edit.setPlainText("content to save")
        assert window._is_modified is True

        with patch("editor.window.QFileDialog.getSaveFileName") as mock_save:
            mock_save.return_value = (str(test_file), "")
            window.save_file()

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == "content to save"
        assert window._is_modified is False
        assert window._status_label.text() == "Saved"
        assert not window.windowTitle().startswith("* ")

    def test_save_updates_current_file(self, window, tmp_path):
        test_file = tmp_path / "saved.txt"
        window.text_edit.setPlainText("test content")

        with patch("editor.window.QFileDialog.getSaveFileName") as mock_save:
            mock_save.return_value = (str(test_file), "")
            window.save_file()

        assert window.current_file == str(test_file)

    def test_save_cancelled_keeps_state(self, window):
        window.text_edit.setPlainText("unsaved content")
        assert window._is_modified is True

        with patch("editor.window.QFileDialog.getSaveFileName") as mock_save:
            mock_save.return_value = ("", "")
            window.save_file()

        assert window._is_modified is True
        assert window._status_label.text() == "Unsaved"


class TestOpenFile:
    def test_open_loads_content_and_updates_ui(self, window, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content", encoding="utf-8")

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        assert window.text_edit.toPlainText() == "file content"
        assert window.current_file == str(test_file)
        assert window._is_modified is False
        assert window._status_label.text() == "Saved"
        assert not window.windowTitle().startswith("* ")

    def test_open_updates_title_with_filename(self, window, tmp_path):
        test_file = tmp_path / "myfile.txt"
        test_file.write_text("content", encoding="utf-8")

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        assert str(test_file) in window.windowTitle()

    def test_open_with_unsaved_discard_proceeds(self, window, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content", encoding="utf-8")

        window.text_edit.setPlainText("unsaved changes")
        assert window._is_modified is True

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open, \
             patch.object(window, "_prompt_save_changes", return_value="discard"):
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        assert window.text_edit.toPlainText() == "file content"
        assert window._is_modified is False

    def test_open_with_unsaved_cancel_aborts(self, window, tmp_path):
        original_text = "unsaved changes"
        window.text_edit.setPlainText(original_text)
        assert window._is_modified is True

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open, \
             patch.object(window, "_prompt_save_changes", return_value="cancel"):
            mock_open.return_value = (str(tmp_path / "ignored.txt"), "")
            window.open_file()

        assert window.text_edit.toPlainText() == original_text
        assert window._is_modified is True

    def test_open_cancelled_keeps_state(self, window):
        window.text_edit.setPlainText("existing content")

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = ("", "")
            window.open_file()

        assert window.text_edit.toPlainText() == "existing content"


class TestStatusLabel:
    def test_status_label_shows_saved_initially(self, window):
        assert window._status_label.text() == "Saved"

    def test_status_label_shows_unsaved_after_edit(self, window):
        window.text_edit.setPlainText("edited content")
        assert window._status_label.text() == "Unsaved"

    def test_status_label_saved_style(self, window):
        assert "#228B22" in window._status_label.styleSheet()

    def test_status_label_unsaved_style(self, window):
        window.text_edit.setPlainText("modified")
        assert "#8B0000" in window._status_label.styleSheet()


class TestTitleAsterisk:
    def test_title_has_asterisk_when_unsaved(self, window):
        window.text_edit.setPlainText("modified content")
        assert window.windowTitle().startswith("* ")

    def test_title_no_asterisk_when_saved(self, window):
        assert not window.windowTitle().startswith("* ")

    def test_title_shows_filename_after_open(self, window, tmp_path):
        test_file = tmp_path / "myfile.py"
        test_file.write_text("# python", encoding="utf-8")

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        assert "myfile.py" in window.windowTitle()
        assert not window.windowTitle().startswith("* ")


class TestFileNotFoundHandling:
    def test_open_nonexistent_file_shows_error(self, window, tmp_path, no_dialogs):
        nonexistent = tmp_path / "nonexistent.txt"

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (str(nonexistent), "")
            window.open_file()

        no_dialogs["critical"].assert_called_once()
        assert "not found" in str(no_dialogs["critical"].call_args).lower()
