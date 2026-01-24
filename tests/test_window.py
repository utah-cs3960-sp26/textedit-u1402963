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
    def test_initial_state_is_new(self, window):
        assert window._is_modified is False
        assert window._status_label.text() == "New"
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
        assert window._status_label.text() == "New"


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
    def test_status_label_shows_new_initially(self, window):
        assert window._status_label.text() == "New"

    def test_status_label_shows_unsaved_after_edit(self, window):
        window.text_edit.setPlainText("edited content")
        assert window._status_label.text() == "Unsaved"

    def test_status_label_new_style(self, window):
        assert "#1E90FF" in window._status_label.styleSheet()

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


class TestUndoRedoGranularity:
    """
    Tests for proper undo/redo behavior using QUndoStack.
    
    Expected behavior (based on established text editors like VSCode, Sublime, Notepad++):
    
    1. WORD-BASED GROUPING: Typing consecutive characters without breaks should group
       into logical chunks. Undo should remove one "word" or "chunk" at a time, not
       character-by-character (too granular) or entire content (too coarse).
    
    2. WHITESPACE BREAKS GROUPS: Typing a space, tab, or newline should start a new
       undo group. So "hello world" typed continuously = 2 undo operations.
    
    3. PASTE IS ATOMIC: Pasting text should be a single undo operation regardless of
       how much text is pasted.
    
    4. DELETE SELECTION IS ATOMIC: Selecting and deleting text should be one undo step.
    
    5. CURSOR MOVEMENT BREAKS GROUPS: If user clicks elsewhere or uses arrow keys,
       then types more, the new typing is a separate undo group.
    """

    def _insert_with_command(self, window, text):
        """Helper to insert text and push command (mimics real keypress behavior)."""
        from editor.undo_commands import InsertTextCommand
        pos = window.text_edit.textCursor().position()
        cursor = window.text_edit.textCursor()
        cursor.insertText(text)
        window.text_edit.setTextCursor(cursor)
        cmd = InsertTextCommand(window.text_edit, text, pos)
        window.text_edit.undo_stack.push(cmd)

    def test_undo_removes_word_not_everything(self, window):
        """
        Typing "hello world" should create 2 undo groups (one per word).
        First undo should remove "world", leaving "hello ".
        
        This tests that undo doesn't remove everything at once (the current bug).
        """
        self._insert_with_command(window, "hello ")
        self._insert_with_command(window, "world")
        
        assert window.text_edit.toPlainText() == "hello world"
        
        window.text_edit.undo()
        
        assert window.text_edit.toPlainText() == "hello "

    def test_undo_word_by_word(self, window):
        """
        Typing three words should require 3 undos to clear.
        Each undo removes one word.
        """
        self._insert_with_command(window, "one ")
        self._insert_with_command(window, "two ")
        self._insert_with_command(window, "three")
        
        assert window.text_edit.toPlainText() == "one two three"
        
        window.text_edit.undo()
        assert window.text_edit.toPlainText() == "one two "
        
        window.text_edit.undo()
        assert window.text_edit.toPlainText() == "one "
        
        window.text_edit.undo()
        assert window.text_edit.toPlainText() == ""

    def test_redo_restores_word(self, window):
        """
        After undoing a word, redo should restore exactly that word.
        """
        self._insert_with_command(window, "hello ")
        self._insert_with_command(window, "world")
        
        window.text_edit.undo()
        assert window.text_edit.toPlainText() == "hello "
        
        window.text_edit.redo()
        assert window.text_edit.toPlainText() == "hello world"

    def test_newline_breaks_undo_group(self, window):
        """
        Pressing Enter should start a new undo group.
        """
        self._insert_with_command(window, "line1")
        self._insert_with_command(window, "\n")
        self._insert_with_command(window, "line2")
        
        assert window.text_edit.toPlainText() == "line1\nline2"
        
        window.text_edit.undo()
        assert window.text_edit.toPlainText() == "line1\n"

    def test_paste_is_single_undo_operation(self, window):
        """
        Pasting multi-word text should be undone in one operation.
        """
        self._insert_with_command(window, "before ")
        self._insert_with_command(window, "pasted content here")
        
        assert window.text_edit.toPlainText() == "before pasted content here"
        
        window.text_edit.undo()
        assert window.text_edit.toPlainText() == "before "

    def test_delete_selection_is_single_undo(self, window):
        """
        Selecting and deleting text should be one undo operation.
        """
        from editor.undo_commands import DeleteTextCommand
        
        self._insert_with_command(window, "hello world")
        window.text_edit.undo_stack.clear()
        
        cursor = window.text_edit.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(5, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        window.text_edit.setTextCursor(cursor)
        
        cmd = DeleteTextCommand(window.text_edit, 0, 5, "hello")
        window.text_edit.undo_stack.push(cmd)
        
        assert window.text_edit.toPlainText() == " world"
        
        window.text_edit.undo()
        assert window.text_edit.toPlainText() == "hello world"


class TestEditMenu:
    def test_edit_menu_exists(self, window):
        menu_bar = window.menuBar()
        menus = [action.text() for action in menu_bar.actions()]
        assert any("Edit" in menu for menu in menus)

    def _insert_with_command(self, window, text):
        """Helper to insert text and push command."""
        from editor.undo_commands import InsertTextCommand
        pos = window.text_edit.textCursor().position()
        cursor = window.text_edit.textCursor()
        cursor.insertText(text)
        window.text_edit.setTextCursor(cursor)
        cmd = InsertTextCommand(window.text_edit, text, pos)
        window.text_edit.undo_stack.push(cmd)

    def test_undo_action_works(self, window):
        self._insert_with_command(window, "hello")
        assert window.text_edit.toPlainText() == "hello"

        window.text_edit.undo()
        assert window.text_edit.toPlainText() == ""

    def test_redo_action_works(self, window):
        self._insert_with_command(window, "hello")
        window.text_edit.undo()
        assert window.text_edit.toPlainText() == ""

        window.text_edit.redo()
        assert window.text_edit.toPlainText() == "hello"

    def test_select_all_action_works(self, window):
        window.text_edit.setPlainText("hello world")
        window.text_edit.selectAll()
        assert window.text_edit.textCursor().selectedText() == "hello world"


class TestNewFile:
    def test_new_file_clears_editor(self, window):
        window.text_edit.setPlainText("some content")
        window._document.mark_saved()

        window.new_file()

        assert window.text_edit.toPlainText() == ""
        assert window._is_modified is False
        assert window._status_label.text() == "New"

    def test_new_file_resets_document_path(self, window, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        assert window.current_file == str(test_file)

        window.new_file()

        assert window.current_file is None
        assert window.text_edit.toPlainText() == ""

    def test_new_file_with_unsaved_discard_proceeds(self, window):
        window.text_edit.setPlainText("unsaved content")
        assert window._is_modified is True

        with patch.object(window, "_prompt_save_changes", return_value="discard"):
            window.new_file()

        assert window.text_edit.toPlainText() == ""
        assert window._is_modified is False

    def test_new_file_with_unsaved_cancel_aborts(self, window):
        original_text = "unsaved content"
        window.text_edit.setPlainText(original_text)
        assert window._is_modified is True

        with patch.object(window, "_prompt_save_changes", return_value="cancel"):
            window.new_file()

        assert window.text_edit.toPlainText() == original_text
        assert window._is_modified is True

    def test_new_file_with_unsaved_save_then_clears(self, window, tmp_path):
        test_file = tmp_path / "saved.txt"
        window.text_edit.setPlainText("content to save")
        assert window._is_modified is True

        with patch.object(window, "_prompt_save_changes", return_value="save"), \
             patch("editor.window.QFileDialog.getSaveFileName") as mock_save:
            mock_save.return_value = (str(test_file), "")
            window.new_file()

        assert test_file.exists()
        assert window.text_edit.toPlainText() == ""
        assert window._is_modified is False

    def test_new_file_updates_title(self, window, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        assert str(test_file) in window.windowTitle()

        window.new_file()

        assert str(test_file) not in window.windowTitle()
        assert not window.windowTitle().startswith("* ")
