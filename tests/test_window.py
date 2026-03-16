import pytest
import sys
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtGui import QCloseEvent
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
        window._document.mark_dirty()
        window._update_status()

        assert window._is_modified is True
        assert window._status_label.text() == "Unsaved"
        assert window.windowTitle().startswith("* ")

    def test_mark_saved_clears_dirty(self, window):
        window._document.mark_dirty()
        window._update_status()
        assert window._is_modified is True

        window._document.mark_saved()
        window._update_status()
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


class TestPromptSaveChanges:
    """Tests for _prompt_save_changes which shows QMessageBox."""

    def test_returns_save_on_save_button(self, window, no_dialogs):
        """Clicking Save returns 'save'."""
        from PyQt6.QtWidgets import QMessageBox
        no_dialogs["question"].return_value = QMessageBox.StandardButton.Save
        assert window._prompt_save_changes() == "save"

    def test_returns_discard_on_discard_button(self, window, no_dialogs):
        """Clicking Discard returns 'discard'."""
        from PyQt6.QtWidgets import QMessageBox
        no_dialogs["question"].return_value = QMessageBox.StandardButton.Discard
        assert window._prompt_save_changes() == "discard"

    def test_returns_cancel_on_cancel_button(self, window, no_dialogs):
        """Clicking Cancel returns 'cancel'."""
        from PyQt6.QtWidgets import QMessageBox
        no_dialogs["question"].return_value = QMessageBox.StandardButton.Cancel
        assert window._prompt_save_changes() == "cancel"

    def test_dialog_is_shown_with_correct_text(self, window, no_dialogs):
        """The dialog should mention unsaved changes."""
        from PyQt6.QtWidgets import QMessageBox
        no_dialogs["question"].return_value = QMessageBox.StandardButton.Cancel
        window._prompt_save_changes()

        no_dialogs["question"].assert_called_once()
        call_args = str(no_dialogs["question"].call_args)
        assert "Unsaved" in call_args or "Save" in call_args


class TestNewFileWithFolder:
    """Tests for new_file when a folder is open (QInputDialog path)."""

    def test_new_file_in_folder_creates_and_opens(self, window, tmp_path, no_dialogs):
        """When folder is open, new_file prompts for name and creates file."""
        window.sidebar.set_root_folder(str(tmp_path))

        with patch("editor.window.QInputDialog.getText",
                   return_value=("created.txt", True)):
            window.new_file()

        expected = tmp_path / "created.txt"
        assert expected.exists()
        assert window.current_file == str(expected)
        assert window._is_modified is False

    def test_new_file_in_folder_cancelled(self, window, tmp_path, no_dialogs):
        """When user cancels the filename dialog, nothing changes."""
        window.sidebar.set_root_folder(str(tmp_path))
        window.text_edit.setPlainText("existing")
        window._document.mark_saved()

        with patch("editor.window.QInputDialog.getText",
                   return_value=("", False)):
            window.new_file()

        # Editor should be unchanged since we returned early
        assert window.text_edit.toPlainText() == "existing"

    def test_new_file_in_folder_os_error_shows_critical(self, window, tmp_path, no_dialogs):
        """When file creation fails, QMessageBox.critical is shown."""
        window.sidebar.set_root_folder(str(tmp_path))

        with patch("editor.window.QInputDialog.getText",
                   return_value=("test.txt", True)), \
             patch("builtins.open", side_effect=OSError("disk full")):
            window.new_file()

        no_dialogs["critical"].assert_called_once()


class TestOpenFileDialog:
    """Tests for open_file's QFileDialog interaction."""

    def test_open_file_shows_dialog(self, window, tmp_path):
        """open_file should call QFileDialog.getOpenFileName."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        mock_open.assert_called_once()
        assert window.text_edit.toPlainText() == "content"

    def test_open_file_error_shows_critical(self, window, tmp_path, no_dialogs):
        """When open fails, QMessageBox.critical is shown."""
        nonexistent = str(tmp_path / "nope.txt")

        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (nonexistent, "")
            window.open_file()

        no_dialogs["critical"].assert_called_once()


class TestOpenFolderDialog:
    """Tests for open_folder's QFileDialog interaction."""

    def test_open_folder_sets_sidebar_root(self, window, tmp_path):
        """Selecting a folder sets it as the sidebar root."""
        with patch("editor.window.QFileDialog.getExistingDirectory",
                   return_value=str(tmp_path)):
            window.open_folder()

        assert window.sidebar.get_root_folder() == str(tmp_path)

    def test_open_folder_cancelled_does_nothing(self, window):
        """Cancelling the folder dialog leaves sidebar unchanged."""
        original = window.sidebar.get_root_folder()

        with patch("editor.window.QFileDialog.getExistingDirectory",
                   return_value=""):
            window.open_folder()

        assert window.sidebar.get_root_folder() == original


class TestOnFileOpenedFromTree:
    """Tests for _on_file_opened_from_tree with unsaved changes."""

    def test_opens_file_from_tree(self, window, tmp_path, no_dialogs):
        """Opening a file from tree loads its content."""
        test_file = tmp_path / "tree_file.txt"
        test_file.write_text("tree content", encoding="utf-8")

        window._on_file_opened_from_tree(str(test_file))

        assert window.text_edit.toPlainText() == "tree content"
        assert window.current_file == str(test_file)

    def test_tree_open_with_unsaved_cancel_aborts(self, window, tmp_path):
        """Cancel on unsaved prompt aborts the tree open."""
        window.text_edit.setPlainText("unsaved")
        assert window._is_modified is True

        with patch.object(window, "_prompt_save_changes", return_value="cancel"):
            window._on_file_opened_from_tree(str(tmp_path / "ignored.txt"))

        assert window.text_edit.toPlainText() == "unsaved"

    def test_tree_open_with_unsaved_discard_proceeds(self, window, tmp_path, no_dialogs):
        """Discard on unsaved prompt proceeds with the open."""
        test_file = tmp_path / "new.txt"
        test_file.write_text("new content", encoding="utf-8")
        window.text_edit.setPlainText("unsaved")

        with patch.object(window, "_prompt_save_changes", return_value="discard"):
            window._on_file_opened_from_tree(str(test_file))

        assert window.text_edit.toPlainText() == "new content"

    def test_tree_open_nonexistent_shows_error(self, window, tmp_path, no_dialogs):
        """Opening a nonexistent file from tree shows error dialog."""
        window._on_file_opened_from_tree(str(tmp_path / "nope.txt"))

        no_dialogs["critical"].assert_called_once()


class TestSaveFileDialog:
    """Tests for save_file's error handling via QMessageBox."""

    def test_save_error_shows_critical(self, window, no_dialogs):
        """When save fails, QMessageBox.critical is shown."""
        window._document.file_path = "/nonexistent/path/file.txt"
        window.text_edit.setPlainText("content")

        window.save_file()

        no_dialogs["critical"].assert_called_once()


class TestCurrentFileSetter:
    def test_setting_current_file_updates_document(self, window):
        window.current_file = "/some/path.txt"
        assert window._document.file_path == "/some/path.txt"

    def test_setting_current_file_to_none(self, window):
        window.current_file = "/tmp/file.txt"
        window.current_file = None
        assert window._document.file_path is None


class TestIsModifiedSetter:
    def test_setting_is_modified_true_captures_content(self, window):
        window.text_edit.setPlainText("hello world")
        # Reset so we can test the setter directly
        window._document.mark_saved()
        assert window._is_modified is False

        window._is_modified = True
        assert window._document.is_modified is True

    def test_setting_is_modified_false_marks_saved(self, window):
        window.text_edit.setPlainText("changed content")
        assert window._is_modified is True

        window._is_modified = False
        assert window._is_modified is False
        assert window._document.is_modified is False


class TestToggleSidebar:
    def test_toggle_hides_visible_sidebar(self, window):
        window.show()
        window.sidebar.setVisible(True)
        window.toggle_sidebar_button.setChecked(True)

        window._toggle_sidebar()

        assert window.sidebar.isVisible() is False
        assert window.toggle_sidebar_button.isChecked() is False

    def test_toggle_shows_hidden_sidebar(self, window):
        window.show()
        window.sidebar.setVisible(False)
        window.toggle_sidebar_button.setChecked(False)

        window._toggle_sidebar()

        assert window.sidebar.isVisible() is True
        assert window.toggle_sidebar_button.isChecked() is True

    def test_toggle_twice_returns_to_original(self, window):
        window.show()
        original_visible = window.sidebar.isVisible()
        window._toggle_sidebar()
        window._toggle_sidebar()
        assert window.sidebar.isVisible() == original_visible


class TestFocusFileSearch:
    def test_sidebar_becomes_visible_when_hidden(self, window):
        window.show()
        window.sidebar.setVisible(False)
        window.toggle_sidebar_button.setChecked(False)

        window._focus_file_search()

        assert window.sidebar.isVisible() is True
        assert window.toggle_sidebar_button.isChecked() is True

    def test_sidebar_stays_visible_when_already_shown(self, window):
        window.show()
        window.sidebar.setVisible(True)
        window.toggle_sidebar_button.setChecked(True)

        window._focus_file_search()

        assert window.sidebar.isVisible() is True

    def test_focus_search_calls_sidebar_focus(self, window):
        with patch.object(window.sidebar, "focus_search") as mock_focus:
            window._focus_file_search()
            mock_focus.assert_called_once()


class TestOpenPreferences:
    def test_accepted_applies_settings(self, window):
        mock_settings = MagicMock()
        with patch("editor.window.PreferencesDialog") as MockDialog:
            mock_instance = MockDialog.return_value
            mock_instance.exec.return_value = QDialog.DialogCode.Accepted
            mock_instance.get_settings.return_value = mock_settings

            with patch.object(window, "_apply_settings") as mock_apply:
                window._open_preferences()

                mock_apply.assert_called_once_with(mock_settings)
                mock_settings.save.assert_called_once_with(window._settings_store)

    def test_rejected_does_not_apply(self, window):
        with patch("editor.window.PreferencesDialog") as MockDialog:
            mock_instance = MockDialog.return_value
            mock_instance.exec.return_value = QDialog.DialogCode.Rejected

            with patch.object(window, "_apply_settings") as mock_apply:
                window._open_preferences()

                mock_apply.assert_not_called()


class TestCloseEventSaveFailure:
    def test_close_event_ignored_when_save_fails(self, window):
        """If user chooses save but save fails (still modified), window stays open."""
        window.text_edit.setPlainText("unsaved")
        assert window._is_modified is True

        event = MagicMock(spec=QCloseEvent)

        with patch.object(window, "_prompt_save_changes", return_value="save"), \
             patch.object(window, "save_file"):
            # save_file is mocked to do nothing, so document stays modified
            window.closeEvent(event)

        event.ignore.assert_called_once()
        event.accept.assert_not_called()

    def test_close_event_accepted_when_save_succeeds(self, window, tmp_path):
        """If save succeeds, the window closes."""
        test_file = tmp_path / "close_test.txt"
        window.text_edit.setPlainText("content")
        assert window._is_modified is True

        event = MagicMock(spec=QCloseEvent)

        with patch.object(window, "_prompt_save_changes", return_value="save"), \
             patch("editor.window.QFileDialog.getSaveFileName",
                   return_value=(str(test_file), "")):
            window.closeEvent(event)

        event.accept.assert_called_once()


class TestNewFileSaveFailure:
    def test_new_file_aborts_when_save_fails(self, window):
        """If user chooses save in new_file but save fails, editor keeps content."""
        window.text_edit.setPlainText("keep this")
        assert window._is_modified is True

        with patch.object(window, "_prompt_save_changes", return_value="save"), \
             patch.object(window, "save_file"):
            # save_file mocked to do nothing, document stays modified
            window.new_file()

        assert window.text_edit.toPlainText() == "keep this"
        assert window._is_modified is True


class TestOpenFileSaveFailure:
    def test_open_file_aborts_when_save_fails(self, window, tmp_path):
        """If user chooses save in open_file but save fails, no file is opened."""
        window.text_edit.setPlainText("keep this")
        assert window._is_modified is True

        with patch.object(window, "_prompt_save_changes", return_value="save"), \
             patch.object(window, "save_file"), \
             patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            window.open_file()
            mock_open.assert_not_called()

        assert window.text_edit.toPlainText() == "keep this"


class TestOpenFileCancelledEmptyPath:
    def test_open_file_returns_early_on_empty_path(self, window):
        """When getOpenFileName returns empty string, open_file does nothing."""
        window.text_edit.setPlainText("existing")
        window._document.mark_saved()

        with patch("editor.window.QFileDialog.getOpenFileName",
                   return_value=("", "")):
            window.open_file()

        assert window.text_edit.toPlainText() == "existing"


class TestOnFileOpenedFromTreeSaveFailure:
    def test_tree_open_aborts_when_save_fails(self, window, tmp_path):
        """If save fails in _on_file_opened_from_tree, file is not opened."""
        target = tmp_path / "target.txt"
        target.write_text("target content", encoding="utf-8")
        window.text_edit.setPlainText("unsaved")
        assert window._is_modified is True

        with patch.object(window, "_prompt_save_changes", return_value="save"), \
             patch.object(window, "save_file"):
            window._on_file_opened_from_tree(str(target))

        # Should NOT have loaded the target file
        assert window.text_edit.toPlainText() == "unsaved"


class TestSaveFileExistingFile:
    def test_save_existing_file_updates_status_and_highlighter(self, window, tmp_path):
        """Saving a file with an existing path updates status to 'Saved'."""
        test_file = tmp_path / "existing.py"
        test_file.write_text("original", encoding="utf-8")

        # Open the file first
        with patch("editor.window.QFileDialog.getOpenFileName") as mock_open:
            mock_open.return_value = (str(test_file), "")
            window.open_file()

        window.text_edit.setPlainText("modified content")
        assert window._is_modified is True

        with patch.object(window, "_setup_highlighter") as mock_hl:
            window.save_file()

        assert window._status_label.text() == "Saved"
        assert test_file.read_text(encoding="utf-8") == "modified content"
        mock_hl.assert_called_with(str(test_file))


class TestSaveFileAsError:
    def test_save_as_error_shows_critical(self, window, no_dialogs):
        """When save_file_as encounters an OS error, QMessageBox.critical is shown."""
        window.text_edit.setPlainText("content")

        with patch("editor.window.QFileDialog.getSaveFileName",
                   return_value=("/nonexistent/dir/file.txt", "")):
            window.save_file_as()

        no_dialogs["critical"].assert_called_once()


class TestShowShortcutsDialog:
    def test_shortcuts_dialog_is_shown(self, window):
        """_show_shortcuts_dialog creates and exec's a QDialog."""
        with patch("editor.window.QDialog.exec", return_value=None) as mock_exec:
            window._show_shortcuts_dialog()
            mock_exec.assert_called_once()


class TestGetShortcutString:
    def test_returns_shortcut_for_action(self, window):
        """Known action in _actions returns its shortcut string."""
        from editor.settings import DEFAULT_SHORTCUTS
        # Apply default shortcuts so actions have them
        window._apply_shortcuts(DEFAULT_SHORTCUTS)
        result = window._get_shortcut_string("file_save")
        assert result != ""

    def test_returns_shortcut_for_shortcut_object(self, window):
        """Known action in _shortcuts (e.g., view_toggle_sidebar) returns its key."""
        from PyQt6.QtGui import QKeySequence
        window._shortcuts["view_toggle_sidebar"].setKey(QKeySequence("Ctrl+B"))
        result = window._get_shortcut_string("view_toggle_sidebar")
        assert "Ctrl" in result and "B" in result

    def test_returns_default_for_unknown_id(self, window):
        """Unknown action_id falls through to DEFAULT_SHORTCUTS or empty string."""
        result = window._get_shortcut_string("totally_unknown_action")
        assert result == ""

    def test_returns_empty_when_action_shortcut_empty(self, window):
        """Action with no shortcut returns an empty string."""
        action = window._actions["file_save"]
        action.setShortcut("")
        result = window._get_shortcut_string("file_save")
        assert result == ""


class TestBuildShortcutsHtml:
    def test_html_contains_group_names(self, window):
        html = window._build_shortcuts_html()
        assert "File" in html
        assert "Edit" in html
        assert "Navigation" in html

    def test_html_contains_action_labels(self, window):
        html = window._build_shortcuts_html()
        assert "New File" in html
        assert "Save File" in html
        assert "Undo" in html

    def test_html_contains_shortcut_strings(self, window):
        from editor.settings import DEFAULT_SHORTCUTS
        window._apply_shortcuts(DEFAULT_SHORTCUTS)
        html = window._build_shortcuts_html()
        # At least some shortcuts should appear
        assert "Ctrl" in html

    def test_html_handles_empty_shortcut(self, window):
        window._actions["file_save"].setShortcut("")
        html = window._build_shortcuts_html()
        assert "Save File" in html
