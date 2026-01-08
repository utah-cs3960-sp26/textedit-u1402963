import os
import tempfile
import pytest

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
