import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from editor.file_manager import FileManager


class TestFileManager:
    def test_write_file_creates_file(self, tmp_path):
        file_path = tmp_path / "test.txt"
        content = "Hello, World!"

        FileManager.write_file(str(file_path), content)

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == content

    def test_write_file_overwrites_existing(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("old content", encoding="utf-8")

        FileManager.write_file(str(file_path), "new content")

        assert file_path.read_text(encoding="utf-8") == "new content"

    def test_write_file_handles_unicode(self, tmp_path):
        file_path = tmp_path / "unicode.txt"
        content = "Hello, 世界! 🌍"

        FileManager.write_file(str(file_path), content)

        assert file_path.read_text(encoding="utf-8") == content

    def test_write_file_handles_empty_content(self, tmp_path):
        file_path = tmp_path / "empty.txt"

        FileManager.write_file(str(file_path), "")

        assert file_path.read_text(encoding="utf-8") == ""

    def test_write_file_permission_error(self, tmp_path):
        if os.name == "nt":
            pytest.skip("Permission test not reliable on Windows")

        file_path = tmp_path / "readonly.txt"
        file_path.write_text("content", encoding="utf-8")
        file_path.chmod(0o444)

        try:
            with pytest.raises(PermissionError):
                FileManager.write_file(str(file_path), "new content")
        finally:
            file_path.chmod(0o644)

    def test_read_file_returns_content(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!", encoding="utf-8")

        content = FileManager.read_file(str(file_path))

        assert content == "Hello, World!"

    def test_read_file_handles_unicode(self, tmp_path):
        file_path = tmp_path / "unicode.txt"
        file_path.write_text("Hello, 世界! 🌍", encoding="utf-8")

        content = FileManager.read_file(str(file_path))

        assert content == "Hello, 世界! 🌍"

    def test_read_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            FileManager.read_file("/nonexistent/path/file.txt")

    def test_read_write_roundtrip(self, tmp_path):
        file_path = tmp_path / "roundtrip.txt"
        original = "Line 1\nLine 2\nLine 3"

        FileManager.write_file(str(file_path), original)
        result = FileManager.read_file(str(file_path))

        assert result == original

    def test_read_empty_file(self, tmp_path):
        file_path = tmp_path / "empty.txt"
        file_path.write_text("", encoding="utf-8")

        content = FileManager.read_file(str(file_path))

        assert content == ""

    def test_write_to_directory_raises(self, tmp_path):
        with pytest.raises((IsADirectoryError, PermissionError, OSError)):
            FileManager.write_file(str(tmp_path), "content")


class TestSaveAs:
    @pytest.fixture(scope="class")
    def app(self):
        from PyQt6.QtWidgets import QApplication
        import sys
        application = QApplication.instance()
        if application is None:
            application = QApplication(sys.argv)
        yield application

    @pytest.fixture
    def window(self, app):
        from editor.window import MainWindow
        w = MainWindow()
        yield w
        w.close()

    def test_save_as_saves_to_new_path(self, window, tmp_path):
        original_file = tmp_path / "original.txt"
        original_file.write_text("original content", encoding="utf-8")
        new_file = tmp_path / "new_file.txt"

        window.text_edit.setPlainText("new content")
        window._document.file_path = str(original_file)
        window._document.set_content("new content", mark_as_saved=False)

        with patch("editor.window.QFileDialog.getSaveFileName", return_value=(str(new_file), "")):
            window.save_file_as()

        assert new_file.exists()
        assert new_file.read_text(encoding="utf-8") == "new content"

    def test_save_as_updates_file_path(self, window, tmp_path):
        new_file = tmp_path / "saved_as.py"
        window.text_edit.setPlainText("print('hello')")

        with patch("editor.window.QFileDialog.getSaveFileName", return_value=(str(new_file), "")):
            window.save_file_as()

        assert window._document.file_path == str(new_file)

    def test_save_as_resets_unsaved_indicator(self, window, tmp_path):
        new_file = tmp_path / "saved.txt"
        window.text_edit.setPlainText("content")
        window._document._current_content = "content"

        with patch("editor.window.QFileDialog.getSaveFileName", return_value=(str(new_file), "")):
            window.save_file_as()

        assert not window._document.is_modified

    def test_save_as_updates_window_title(self, window, tmp_path):
        new_file = tmp_path / "new_title.txt"
        window.text_edit.setPlainText("content")

        with patch("editor.window.QFileDialog.getSaveFileName", return_value=(str(new_file), "")):
            window.save_file_as()

        assert str(new_file) in window.windowTitle()

    def test_save_as_dialog_starts_in_current_file_directory(self, window, tmp_path):
        current_file = tmp_path / "subdir" / "current.txt"
        current_file.parent.mkdir(parents=True, exist_ok=True)
        current_file.write_text("content", encoding="utf-8")
        window._document.file_path = str(current_file)

        with patch("editor.window.QFileDialog.getSaveFileName", return_value=("", "")) as mock_dialog:
            window.save_file_as()
            call_args = mock_dialog.call_args
            assert str(current_file.parent) in call_args[0][2]

    def test_save_as_cancelled_does_not_modify_state(self, window, tmp_path):
        original_file = tmp_path / "original.txt"
        original_file.write_text("content", encoding="utf-8")
        window._document.file_path = str(original_file)
        window._document.set_content("content", mark_as_saved=True)

        with patch("editor.window.QFileDialog.getSaveFileName", return_value=("", "")):
            window.save_file_as()

        assert window._document.file_path == str(original_file)

    def test_save_as_untitled_file_behaves_like_save(self, window, tmp_path):
        new_file = tmp_path / "untitled_saved.txt"
        window.text_edit.setPlainText("new file content")
        window._document.file_path = None

        with patch("editor.window.QFileDialog.getSaveFileName", return_value=(str(new_file), "")):
            window.save_file_as()

        assert new_file.exists()
        assert window._document.file_path == str(new_file)
