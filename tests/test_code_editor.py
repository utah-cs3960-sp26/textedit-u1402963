import pytest
import sys

from PyQt6.QtWidgets import QApplication

from editor.code_editor import CodeEditor, LineNumberArea


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance()
    if application is None:
        application = QApplication(sys.argv)
    yield application


@pytest.fixture
def editor(app):
    return CodeEditor()


class TestCodeEditorLineNumbers:
    def test_line_number_area_exists(self, editor):
        assert editor.line_number_area is not None
        assert isinstance(editor.line_number_area, LineNumberArea)

    def test_line_number_area_width_single_digit(self, editor):
        editor.setPlainText("line1")
        width = editor.line_number_area_width()
        assert width > 0

    def test_line_number_area_width_increases_with_lines(self, editor):
        editor.setPlainText("line1")
        width_1_line = editor.line_number_area_width()

        lines = "\n".join([f"line{i}" for i in range(100)])
        editor.setPlainText(lines)
        width_100_lines = editor.line_number_area_width()

        assert width_100_lines > width_1_line

    def test_line_number_area_width_for_1000_lines(self, editor):
        lines = "\n".join([f"line{i}" for i in range(1000)])
        editor.setPlainText(lines)
        width_1000 = editor.line_number_area_width()

        editor.setPlainText("line1")
        width_1 = editor.line_number_area_width()

        assert width_1000 > width_1

    def test_block_count_matches_line_count(self, editor):
        editor.setPlainText("line1\nline2\nline3")
        assert editor.blockCount() == 3

    def test_block_count_empty_document(self, editor):
        editor.setPlainText("")
        assert editor.blockCount() == 1

    def test_block_count_single_line(self, editor):
        editor.setPlainText("single line no newline")
        assert editor.blockCount() == 1

    def test_viewport_margins_set(self, editor):
        editor.setPlainText("test")
        margins = editor.viewportMargins()
        assert margins.left() > 0


class TestLineNumberArea:
    def test_size_hint_width(self, editor):
        size_hint = editor.line_number_area.sizeHint()
        assert size_hint.width() == editor.line_number_area_width()
        assert size_hint.height() == 0

    def test_line_number_area_parent(self, editor):
        assert editor.line_number_area.editor is editor
