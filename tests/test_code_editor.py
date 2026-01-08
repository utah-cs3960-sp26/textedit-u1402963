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

    @pytest.mark.parametrize("before_count,after_count", [
        (9, 10),
        (99, 100),
        (999, 1000),
    ])
    def test_line_number_width_increases_at_digit_boundaries(self, editor, before_count, after_count):
        editor.setPlainText("\n".join(["line"] * before_count))
        width_before = editor.line_number_area_width()

        editor.setPlainText("\n".join(["line"] * after_count))
        width_after = editor.line_number_area_width()

        assert width_after > width_before, (
            f"Width should increase from {before_count} to {after_count} lines "
            f"(was {width_before}, now {width_after})"
        )

    def test_line_number_area_width_updates_dynamically(self, editor):
        editor.setPlainText("line1")
        width_initial = editor.line_number_area_width()

        editor.appendPlainText("\n".join(["line"] * 100))
        width_after = editor.line_number_area_width()

        assert width_after > width_initial

    @pytest.mark.parametrize("text,expected_blocks", [
        ("", 1),
        ("single line no newline", 1),
        ("line1\nline2\nline3", 3),
        ("a\nb\nc\nd\ne", 5),
    ])
    def test_block_count(self, editor, text, expected_blocks):
        editor.setPlainText(text)
        assert editor.blockCount() == expected_blocks

    def test_viewport_margins_set(self, editor):
        editor.setPlainText("test")
        margins = editor.viewportMargins()
        expected_width = editor.line_number_area_width()
        assert margins.left() == expected_width


class TestLineNumberArea:
    def test_size_hint_width_matches_editor(self, editor):
        size_hint = editor.line_number_area.sizeHint()
        assert size_hint.width() == editor.line_number_area_width()

    def test_line_number_area_parent_is_editor(self, editor):
        assert editor.line_number_area.parent() is editor
