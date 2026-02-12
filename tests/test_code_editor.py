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


class TestShiftEnterBehavior:
    """Tests for Shift+Enter creating proper new blocks with line numbers."""

    def _press_enter(self, editor, with_shift=False):
        """Helper to simulate Enter or Shift+Enter."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        modifiers = Qt.KeyboardModifier.ShiftModifier if with_shift else Qt.KeyboardModifier.NoModifier
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, modifiers, "\r")
        editor.keyPressEvent(event)

    def test_shift_enter_creates_new_block(self, editor):
        """Shift+Enter should create a new block, just like regular Enter."""
        editor.setPlainText("line1")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        
        initial_block_count = editor.blockCount()
        assert initial_block_count == 1
        
        self._press_enter(editor, with_shift=True)
        
        assert editor.blockCount() == 2, "Shift+Enter should create a new block"

    def test_shift_enter_line_numbers_match_block_count(self, editor):
        """After Shift+Enter, block count should match expected line numbers."""
        editor.setPlainText("")
        
        self._press_enter(editor, with_shift=True)
        assert editor.blockCount() == 2
        
        self._press_enter(editor, with_shift=True)
        assert editor.blockCount() == 3
        
        self._press_enter(editor, with_shift=False)
        assert editor.blockCount() == 4

    def test_regular_enter_still_works(self, editor):
        """Regular Enter should continue to create new blocks."""
        editor.setPlainText("test")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        
        self._press_enter(editor, with_shift=False)
        
        assert editor.blockCount() == 2

    def test_mixed_enter_and_shift_enter(self, editor):
        """Mixing Enter and Shift+Enter should create correct block counts."""
        editor.setPlainText("")
        
        self._press_enter(editor, with_shift=False)
        self._press_enter(editor, with_shift=True)
        self._press_enter(editor, with_shift=False)
        self._press_enter(editor, with_shift=True)
        
        assert editor.blockCount() == 5


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

    def test_line_number_paint_no_crash_on_last_block(self, editor):
        """Painting line numbers should not crash when reaching the last block."""
        from PyQt6.QtGui import QPaintEvent
        from PyQt6.QtCore import QRect

        editor.setPlainText("line1\nline2\nline3")
        editor.show()

        rect = QRect(0, 0, editor.line_number_area.width(), editor.height())
        event = QPaintEvent(rect)
        editor.line_number_area_paint_event(event)

    def test_line_number_paint_handles_empty_document(self, editor):
        """Painting line numbers should handle empty document without crash."""
        from PyQt6.QtGui import QPaintEvent
        from PyQt6.QtCore import QRect

        editor.setPlainText("")
        editor.show()

        rect = QRect(0, 0, editor.line_number_area.width(), editor.height())
        event = QPaintEvent(rect)
        editor.line_number_area_paint_event(event)

    def test_line_number_paint_single_line(self, editor):
        """Painting line numbers should work correctly for single line."""
        from PyQt6.QtGui import QPaintEvent
        from PyQt6.QtCore import QRect

        editor.setPlainText("single line")
        editor.show()

        rect = QRect(0, 0, editor.line_number_area.width(), editor.height())
        event = QPaintEvent(rect)
        editor.line_number_area_paint_event(event)

    def test_line_number_paint_skips_empty_rect(self, editor):
        """Painting with an empty rect should not enter the loop."""
        from PyQt6.QtGui import QPaintEvent
        from PyQt6.QtCore import QRect

        editor.setPlainText("line1")
        editor.show()

        rect = QRect(0, 0, editor.line_number_area.width(), 0)
        event = QPaintEvent(rect)
        editor.line_number_area_paint_event(event)

    def test_line_number_paint_skips_offscreen_block(self, editor):
        """Painting should skip blocks above the requested rect."""
        from PyQt6.QtGui import QPaintEvent
        from PyQt6.QtCore import QRect

        editor.setPlainText("line1\nline2\nline3")
        editor.show()

        rect = QRect(0, 1000, editor.line_number_area.width(), 10)
        event = QPaintEvent(rect)
        editor.line_number_area_paint_event(event)


class TestKeyboardShortcuts:
    """Tests for keyboard shortcuts (Ctrl+Z, Ctrl+Y, etc.)."""

    def _simulate_keypress(self, editor, key, modifiers=None):
        """Helper to simulate a keypress event."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        if modifiers is None:
            modifiers = Qt.KeyboardModifier.NoModifier
        
        text = ""
        if key == Qt.Key.Key_Z:
            text = "z"
        elif key == Qt.Key.Key_Y:
            text = "y"
        
        event = QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)
        editor.keyPressEvent(event)

    def test_ctrl_z_shortcut_triggers_undo(self, editor):
        """Ctrl+Z keypress should trigger undo."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        self._type_char(editor, "a")
        self._type_space(editor)
        
        assert editor.toPlainText() == "a "
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier, "")
        editor.keyPressEvent(event)
        
        assert editor.toPlainText() == "a"

    def test_ctrl_y_shortcut_triggers_redo(self, editor):
        """Ctrl+Y keypress should trigger redo."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        self._type_char(editor, "a")
        self._type_space(editor)
        editor.undo()
        
        assert editor.toPlainText() == "a"
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier, "")
        editor.keyPressEvent(event)
        
        assert editor.toPlainText() == "a "

    def _type_char(self, editor, char):
        """Helper to type a character."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        key = getattr(Qt.Key, f"Key_{char.upper()}")
        event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, char)
        editor.keyPressEvent(event)

    def _type_space(self, editor):
        """Helper to type a space (flushes pending insert)."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        editor.keyPressEvent(event)

    def test_ctrl_z_undoes_last_word(self, editor):
        """Ctrl+Z should undo the last word."""
        from PyQt6.QtCore import Qt
        
        self._type_char(editor, "a")
        self._type_space(editor)
        self._type_char(editor, "b")
        self._type_space(editor)
        
        assert editor.toPlainText() == "a b "
        
        editor.undo()
        assert editor.toPlainText() == "a b"
        
        editor.undo()
        assert editor.toPlainText() == "a "

    def test_ctrl_y_redoes_after_undo(self, editor):
        """Ctrl+Y should redo after undo."""
        from PyQt6.QtCore import Qt
        
        self._type_char(editor, "x")
        self._type_space(editor)
        
        assert editor.toPlainText() == "x "
        
        editor.undo()
        assert editor.toPlainText() == "x"
        
        editor.redo()
        assert editor.toPlainText() == "x "

    def test_multiple_undo_redo_cycle(self, editor):
        """Multiple undo/redo operations should work correctly."""
        self._type_char(editor, "a")
        self._type_space(editor)
        self._type_char(editor, "b")
        self._type_space(editor)
        self._type_char(editor, "c")
        self._type_space(editor)
        
        assert editor.toPlainText() == "a b c "
        
        editor.undo()
        assert editor.toPlainText() == "a b c"
        
        editor.undo()
        assert editor.toPlainText() == "a b "
        
        editor.undo()
        assert editor.toPlainText() == "a b"
        
        editor.redo()
        assert editor.toPlainText() == "a b "
        
        editor.redo()
        assert editor.toPlainText() == "a b c"

    def test_paste_is_single_undo_operation(self, editor, app):
        """Pasting text should be undone as a single operation."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        self._type_char(editor, "a")
        self._type_space(editor)
        
        clipboard = QApplication.clipboard()
        clipboard.setText("pasted text")
        
        editor.paste()
        
        assert editor.toPlainText() == "a pasted text"
        
        editor.undo()
        assert editor.toPlainText() == "a "

    def test_cut_paste_cycle_single_undo(self, editor, app):
        """Cut and paste should each be single undo operations."""
        from PyQt6.QtWidgets import QApplication
        
        self._type_char(editor, "h")
        self._type_char(editor, "e")
        self._type_char(editor, "l")
        self._type_char(editor, "l")
        self._type_char(editor, "o")
        self._type_space(editor)
        
        assert editor.toPlainText() == "hello "
        
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(5, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        
        editor.cut()
        assert editor.toPlainText() == " "
        
        editor.undo()
        assert editor.toPlainText() == "hello "


class TestKeyPressHandling:
    """Tests for keypress handling to ensure no duplicate characters."""

    def test_typing_single_character_no_duplicate(self, editor):
        """Typing a single character should not duplicate it."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, "a")
        editor.keyPressEvent(event)
        
        assert editor.toPlainText() == "a", f"Expected 'a', got '{editor.toPlainText()}'"

    def test_typing_character_then_space_no_duplicate(self, editor):
        """Typing 'a ' should result in exactly 'a ', not 'a a' or 'aa '."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        event_a = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, "a")
        editor.keyPressEvent(event_a)
        
        event_space = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        editor.keyPressEvent(event_space)
        
        assert editor.toPlainText() == "a ", f"Expected 'a ', got '{editor.toPlainText()}'"

    def test_typing_word_no_duplicates(self, editor):
        """Typing 'hello' should result in exactly 'hello'."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        for char in "hello":
            key = getattr(Qt.Key, f"Key_{char.upper()}")
            event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, char)
            editor.keyPressEvent(event)
        
        assert editor.toPlainText() == "hello", f"Expected 'hello', got '{editor.toPlainText()}'"


class TestUndoHistoryLimit:
    """Tests for undo history limit using QUndoStack (MAX_UNDO_STEPS = 100)."""

    def test_max_undo_steps_constant_exists(self, editor):
        assert hasattr(editor, "MAX_UNDO_STEPS")
        assert editor.MAX_UNDO_STEPS == 100

    def test_undo_stack_has_limit_set(self, editor):
        """QUndoStack should have the limit properly configured."""
        assert editor.undo_stack.undoLimit() == editor.MAX_UNDO_STEPS

    def test_undo_history_never_exceeds_limit(self, editor):
        """
        Undo steps should never exceed MAX_UNDO_STEPS.
        When the limit is exceeded, the oldest operation is dropped.
        """
        from editor.undo_commands import InsertTextCommand
        
        for i in range(editor.MAX_UNDO_STEPS + 50):
            cmd = InsertTextCommand(editor, f"x", editor.textCursor().position())
            editor.undo_stack.push(cmd)

        assert editor.undo_stack.count() == editor.MAX_UNDO_STEPS

    def test_oldest_operation_dropped_when_limit_exceeded(self, editor):
        """
        When limit is exceeded, the OLDEST operation should be dropped,
        not the newest and not all of them.
        """
        from editor.undo_commands import InsertTextCommand
        
        for i in range(editor.MAX_UNDO_STEPS):
            cmd = InsertTextCommand(editor, str(i), editor.textCursor().position())
            editor.undo_stack.push(cmd)

        assert editor.undo_stack.count() == editor.MAX_UNDO_STEPS
        
        cmd = InsertTextCommand(editor, "NEW", editor.textCursor().position())
        editor.undo_stack.push(cmd)
        
        assert editor.undo_stack.count() == editor.MAX_UNDO_STEPS
        assert editor.undo_stack.canUndo()

    def test_undo_moves_to_redo_stack(self, editor):
        """Undoing should move the operation to redo stack, not delete it."""
        from editor.undo_commands import InsertTextCommand
        
        cmd = InsertTextCommand(editor, "test", 0)
        editor.undo_stack.push(cmd)
        
        assert editor.undo_stack.canUndo()
        assert not editor.undo_stack.canRedo()
        
        editor.undo_stack.undo()
        
        assert not editor.undo_stack.canUndo()
        assert editor.undo_stack.canRedo()

    def _insert_with_command(self, editor, text):
        """Helper to insert text and push the command (mimics real behavior)."""
        from editor.undo_commands import InsertTextCommand
        pos = editor.textCursor().position()
        cursor = editor.textCursor()
        cursor.insertText(text)
        editor.setTextCursor(cursor)
        cmd = InsertTextCommand(editor, text, pos)
        editor.undo_stack.push(cmd)

    def test_redo_restores_operation(self, editor):
        """Redo should restore an undone operation."""
        self._insert_with_command(editor, "hello")
        
        assert editor.toPlainText() == "hello"
        
        editor.undo_stack.undo()
        assert editor.toPlainText() == ""
        
        editor.undo_stack.redo()
        assert editor.toPlainText() == "hello"

    def test_content_preserved_after_undo_limit_reached(self, editor):
        """Document content should be preserved even when oldest undo is dropped."""
        for i in range(editor.MAX_UNDO_STEPS + 10):
            self._insert_with_command(editor, "x")

        expected_length = editor.MAX_UNDO_STEPS + 10
        assert len(editor.toPlainText()) == expected_length


# =============================================================================
# NEW QA TESTS FOR UNDO/REDO EDGE CASES AND COMMON BUGS
# =============================================================================


class TestUndoRedoEdgeCases:
    """Tests for edge cases and potential bugs in undo/redo functionality."""

    def _type_char(self, editor, char):
        """Helper to type a character."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        key = getattr(Qt.Key, f"Key_{char.upper()}")
        event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, char)
        editor.keyPressEvent(event)

    def _type_space(self, editor):
        """Helper to type a space (flushes pending insert)."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        editor.keyPressEvent(event)

    def _type_enter(self, editor):
        """Helper to type enter/newline."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier, "\n")
        editor.keyPressEvent(event)

    def _type_backspace(self, editor):
        """Helper to type backspace."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier, "")
        editor.keyPressEvent(event)

    def _type_delete(self, editor):
        """Helper to type delete key."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier, "")
        editor.keyPressEvent(event)

    # --- Undo on Empty Document ---
    
    def test_undo_on_empty_document_no_crash(self, editor):
        """Undo on empty document should not crash or throw."""
        assert editor.toPlainText() == ""
        editor.undo()
        assert editor.toPlainText() == ""

    def test_redo_on_empty_document_no_crash(self, editor):
        """Redo on empty document should not crash or throw."""
        assert editor.toPlainText() == ""
        editor.redo()
        assert editor.toPlainText() == ""

    def test_multiple_undo_on_empty_document(self, editor):
        """Multiple undos on empty document should be safe."""
        for _ in range(10):
            editor.undo()
        assert editor.toPlainText() == ""

    def test_multiple_redo_on_empty_document(self, editor):
        """Multiple redos on empty document should be safe."""
        for _ in range(10):
            editor.redo()
        assert editor.toPlainText() == ""

    # --- Redo After New Edit (Redo Stack Invalidation) ---

    def test_redo_stack_cleared_after_new_edit(self, editor):
        """After undoing and making a new edit, redo should not be available."""
        self._type_char(editor, "a")
        self._type_space(editor)
        self._type_char(editor, "b")
        self._type_space(editor)
        
        assert editor.toPlainText() == "a b "
        
        editor.undo()
        assert editor.toPlainText() == "a b"
        
        self._type_char(editor, "c")
        self._type_space(editor)
        
        assert not editor.canRedo(), "Redo stack should be cleared after new edit"

    def test_redo_after_new_edit_does_nothing(self, editor):
        """Redo after new edit should not restore old content."""
        self._type_char(editor, "x")
        self._type_space(editor)
        
        editor.undo()
        assert editor.toPlainText() == "x"
        
        self._type_char(editor, "y")
        self._type_space(editor)
        
        content_before = editor.toPlainText()
        editor.redo()
        
        assert editor.toPlainText() == content_before

    # --- Cursor Position After Undo/Redo ---

    def test_cursor_position_after_undo_insert(self, editor):
        """Cursor should be at correct position after undoing an insert."""
        self._type_char(editor, "a")
        self._type_char(editor, "b")
        self._type_char(editor, "c")
        self._type_space(editor)
        
        editor.undo()
        
        assert editor.textCursor().position() == 3

    def test_cursor_position_after_redo_insert(self, editor):
        """Cursor should be at correct position after redoing an insert."""
        self._type_char(editor, "a")
        self._type_char(editor, "b")
        self._type_char(editor, "c")
        self._type_space(editor)
        
        editor.undo()
        editor.redo()
        
        assert editor.textCursor().position() == 4

    def test_cursor_position_after_undo_delete(self, editor):
        """Cursor should be at correct position after undoing a delete."""
        self._type_char(editor, "a")
        self._type_char(editor, "b")
        self._type_char(editor, "c")
        self._type_space(editor)
        
        self._type_backspace(editor)
        
        editor.undo()
        
        assert editor.toPlainText() == "abc "
        assert editor.textCursor().position() == 4

    # --- Interleaved Insert/Delete Operations ---

    def test_interleaved_insert_delete_undo(self, editor):
        """Interleaved inserts and deletes should undo correctly."""
        self._type_char(editor, "a")
        self._type_char(editor, "b")
        self._type_space(editor)
        self._type_backspace(editor)
        self._type_char(editor, "c")
        self._type_space(editor)
        
        assert editor.toPlainText() == "abc "
        
        editor.undo()
        assert editor.toPlainText() == "abc"
        
        editor.undo()
        assert editor.toPlainText() == "ab"
        
        editor.undo()
        assert editor.toPlainText() == "ab "
        
        editor.undo()
        assert editor.toPlainText() == "ab"

    # --- Empty Undo/Redo After Clear ---

    def test_undo_after_clear_does_nothing(self, editor):
        """After clearing document, undo stack should be empty."""
        self._type_char(editor, "x")
        self._type_space(editor)
        
        editor.clear()
        
        assert not editor.canUndo()
        editor.undo()
        assert editor.toPlainText() == ""

    def test_redo_after_clear_does_nothing(self, editor):
        """After clearing document, redo stack should be empty."""
        self._type_char(editor, "x")
        self._type_space(editor)
        editor.undo()
        
        editor.clear()
        
        assert not editor.canRedo()
        editor.redo()
        assert editor.toPlainText() == ""

    # --- setPlainText Clears Undo Stack ---

    def test_undo_after_setPlainText_does_nothing(self, editor):
        """setPlainText should clear the undo stack."""
        self._type_char(editor, "x")
        self._type_space(editor)
        
        editor.setPlainText("new content")
        
        assert not editor.canUndo()
        editor.undo()
        assert editor.toPlainText() == "new content"

    # --- Multiline Operations ---

    def test_undo_multiline_insert(self, editor):
        """Undoing multiline inserts should work correctly."""
        self._type_char(editor, "a")
        self._type_enter(editor)
        self._type_char(editor, "b")
        self._type_enter(editor)
        self._type_char(editor, "c")
        self._type_space(editor)
        
        assert editor.toPlainText() == "a\nb\nc "
        
        editor.undo()
        assert editor.toPlainText() == "a\nb\nc"
        
        editor.undo()
        assert editor.toPlainText() == "a\nb\n"
        
        editor.undo()
        assert editor.toPlainText() == "a\nb"

    def test_undo_redo_newline_characters(self, editor):
        """Newlines should be handled correctly in undo/redo."""
        self._type_char(editor, "a")
        self._type_enter(editor)
        
        assert editor.toPlainText() == "a\n"
        
        editor.undo()
        assert editor.toPlainText() == "a"
        
        editor.redo()
        assert editor.toPlainText() == "a\n"

    # --- Rapid Undo/Redo Cycles ---

    def test_rapid_undo_redo_cycle(self, editor):
        """Rapidly alternating undo/redo should maintain consistency."""
        self._type_char(editor, "x")
        self._type_space(editor)
        
        for _ in range(20):
            editor.undo()
            assert editor.toPlainText() == "x"
            editor.redo()
            assert editor.toPlainText() == "x "

    # --- Selection Replace Undo ---

    def test_undo_replace_selection(self, editor):
        """Replacing selection should be undone as single operation."""
        self._type_char(editor, "h")
        self._type_char(editor, "e")
        self._type_char(editor, "l")
        self._type_char(editor, "l")
        self._type_char(editor, "o")
        self._type_space(editor)
        
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(5, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        
        self._type_char(editor, "x")
        
        assert editor.toPlainText() == "x "
        
        editor.undo()
        assert editor.toPlainText() == "hello "

    # --- Pending Insert Flush on Undo ---

    def test_pending_insert_flushed_on_undo(self, editor):
        """Pending insert should be flushed before undo."""
        self._type_char(editor, "a")
        self._type_char(editor, "b")
        self._type_char(editor, "c")
        
        editor.undo()
        
        assert editor.toPlainText() == ""

    def test_pending_insert_flushed_on_redo(self, editor):
        """Pending insert should be flushed before redo."""
        self._type_char(editor, "a")
        self._type_space(editor)
        editor.undo()
        
        self._type_char(editor, "b")
        self._type_char(editor, "c")
        
        editor.redo()
        
        assert "bc" in editor.toPlainText()


class TestUndoRedoBoundaryConditions:
    """Tests for boundary conditions in undo/redo."""

    def _type_char(self, editor, char):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        key = getattr(Qt.Key, f"Key_{char.upper()}")
        event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, char)
        editor.keyPressEvent(event)

    def _type_space(self, editor):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        editor.keyPressEvent(event)

    def _type_backspace(self, editor):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier, "")
        editor.keyPressEvent(event)

    # --- Undo Past Beginning ---

    def test_undo_stops_at_beginning(self, editor):
        """Cannot undo past the initial state."""
        self._type_char(editor, "a")
        self._type_space(editor)
        
        editor.undo()
        editor.undo()
        
        assert editor.toPlainText() == ""
        
        for _ in range(5):
            editor.undo()
        
        assert editor.toPlainText() == ""

    # --- Redo Past End ---

    def test_redo_stops_at_end(self, editor):
        """Cannot redo past the latest state."""
        self._type_char(editor, "a")
        self._type_space(editor)
        
        editor.undo()
        editor.redo()
        
        assert editor.toPlainText() == "a "
        
        for _ in range(5):
            editor.redo()
        
        assert editor.toPlainText() == "a "

    # --- Delete at Document Start ---

    def test_backspace_at_document_start(self, editor):
        """Backspace at document start should be no-op and not corrupt undo."""
        self._type_backspace(editor)
        
        assert editor.toPlainText() == ""
        
        self._type_char(editor, "a")
        self._type_space(editor)
        
        editor.undo()
        assert editor.toPlainText() == "a"

    # --- Delete at Document End ---

    def test_delete_at_document_end(self, editor):
        """Delete at document end should be no-op and not corrupt undo."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        
        self._type_char(editor, "a")
        self._type_space(editor)
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier, "")
        editor.keyPressEvent(event)
        
        assert editor.toPlainText() == "a "
        
        editor.undo()
        assert editor.toPlainText() == "a"

    # --- Very Long Text ---

    def test_undo_very_long_insert(self, editor, app):
        """Undoing a very long paste should work correctly."""
        from PyQt6.QtWidgets import QApplication
        
        long_text = "x" * 10000
        clipboard = QApplication.clipboard()
        clipboard.setText(long_text)
        
        editor.paste()
        
        assert len(editor.toPlainText()) == 10000
        
        editor.undo()
        assert editor.toPlainText() == ""

    # --- Unicode Characters ---

    def test_undo_unicode_characters(self, editor, app):
        """Undo should handle unicode characters correctly."""
        from PyQt6.QtWidgets import QApplication
        
        unicode_text = "你好世界🎉"
        clipboard = QApplication.clipboard()
        clipboard.setText(unicode_text)
        
        editor.paste()
        
        assert editor.toPlainText() == unicode_text
        
        editor.undo()
        assert editor.toPlainText() == ""
        
        editor.redo()
        assert editor.toPlainText() == unicode_text

    # --- Single Character Operations ---

    def test_single_character_undo_redo_cycle(self, editor):
        """Single character insert/delete should undo/redo correctly."""
        self._type_char(editor, "x")
        self._type_space(editor)
        
        editor.undo()
        assert editor.toPlainText() == "x"
        
        editor.undo()
        assert editor.toPlainText() == ""
        
        editor.redo()
        assert editor.toPlainText() == "x"
        
        editor.redo()
        assert editor.toPlainText() == "x "


class TestUndoRedoDataIntegrity:
    """Tests to ensure undo/redo doesn't corrupt document state."""

    def _type_char(self, editor, char):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        key = getattr(Qt.Key, f"Key_{char.upper()}")
        event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, char)
        editor.keyPressEvent(event)

    def _type_space(self, editor):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        editor.keyPressEvent(event)

    def _type_backspace(self, editor):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier, "")
        editor.keyPressEvent(event)

    # --- Full Undo Returns to Empty ---

    def test_full_undo_returns_to_empty(self, editor):
        """Undoing all operations should return to empty document."""
        for char in "hello world":
            if char == " ":
                self._type_space(editor)
            else:
                self._type_char(editor, char)
        self._type_space(editor)
        
        while editor.canUndo():
            editor.undo()
        
        assert editor.toPlainText() == ""

    # --- Full Redo Restores All ---

    def test_full_redo_restores_all(self, editor):
        """Redoing all operations should restore original content."""
        for char in "test":
            self._type_char(editor, char)
        self._type_space(editor)
        
        original = editor.toPlainText()
        
        while editor.canUndo():
            editor.undo()
        
        while editor.canRedo():
            editor.redo()
        
        assert editor.toPlainText() == original

    # --- Repeated Undo/Redo Cycles ---

    def test_repeated_full_undo_redo_cycles(self, editor):
        """Multiple full undo/redo cycles should be consistent."""
        self._type_char(editor, "a")
        self._type_space(editor)
        self._type_char(editor, "b")
        self._type_space(editor)
        
        original = editor.toPlainText()
        
        for _ in range(5):
            while editor.canUndo():
                editor.undo()
            assert editor.toPlainText() == ""
            
            while editor.canRedo():
                editor.redo()
            assert editor.toPlainText() == original

    # --- Interleaved Operations Data Integrity ---

    def test_complex_operation_sequence_integrity(self, editor, app):
        """Complex sequence of operations should maintain data integrity."""
        from PyQt6.QtWidgets import QApplication
        
        self._type_char(editor, "a")
        self._type_char(editor, "b")
        self._type_char(editor, "c")
        self._type_space(editor)
        
        self._type_backspace(editor)
        
        clipboard = QApplication.clipboard()
        clipboard.setText("123")
        editor.paste()
        
        self._type_char(editor, "d")
        self._type_space(editor)
        
        states = []
        while editor.canUndo():
            editor.undo()
            states.append(editor.toPlainText())
        
        states_reverse = []
        while editor.canRedo():
            editor.redo()
            states_reverse.append(editor.toPlainText())
        
        assert states[::-1][:-1] == states_reverse[:-1] or len(states) == len(states_reverse)


class TestUndoRedoWithSelection:
    """Tests for undo/redo with text selection operations."""

    def _type_char(self, editor, char):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        key = getattr(Qt.Key, f"Key_{char.upper()}")
        event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, char)
        editor.keyPressEvent(event)

    def _type_space(self, editor):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        editor.keyPressEvent(event)

    def _type_backspace(self, editor):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier, "")
        editor.keyPressEvent(event)

    # --- Delete Selection ---

    def test_undo_delete_selection(self, editor):
        """Undoing deletion of selected text should restore it."""
        for char in "hello":
            self._type_char(editor, char)
        self._type_space(editor)
        
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(3, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        
        self._type_backspace(editor)
        
        assert editor.toPlainText() == "lo "
        
        editor.undo()
        assert editor.toPlainText() == "hello "

    # --- Replace Selection With Multiple Characters ---

    def test_undo_replace_selection_multiple_chars(self, editor):
        """Replacing selection with multiple characters should undo correctly."""
        for char in "abc":
            self._type_char(editor, char)
        self._type_space(editor)
        
        cursor = editor.textCursor()
        cursor.setPosition(1)
        cursor.setPosition(2, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        
        self._type_char(editor, "x")
        
        assert editor.toPlainText() == "axc "
        
        editor.undo()
        assert editor.toPlainText() == "abc "

    # --- Select All and Delete ---

    def test_undo_select_all_and_delete(self, editor):
        """Undoing select-all delete should restore all content."""
        for char in "test":
            self._type_char(editor, char)
        self._type_space(editor)
        
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(len(editor.toPlainText()), cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        
        self._type_backspace(editor)
        
        assert editor.toPlainText() == ""
        
        editor.undo()
        assert editor.toPlainText() == "test "

    # --- Select All and Replace ---

    def test_undo_select_all_and_replace(self, editor):
        """Undoing select-all replace should restore original content."""
        for char in "old":
            self._type_char(editor, char)
        self._type_space(editor)
        
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(len(editor.toPlainText()), cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        
        self._type_char(editor, "n")
        
        assert editor.toPlainText() == "n"
        
        editor.undo()
        assert editor.toPlainText() == "old "


class TestUndoRedoMemoryAndPerformance:
    """Tests for memory management and performance of undo/redo."""

    def _insert_with_command(self, editor, text):
        from editor.undo_commands import InsertTextCommand
        pos = editor.textCursor().position()
        cursor = editor.textCursor()
        cursor.insertText(text)
        editor.setTextCursor(cursor)
        cmd = InsertTextCommand(editor, text, pos)
        editor.undo_stack.push(cmd)

    # --- Limit Enforcement ---

    def test_undo_limit_strictly_enforced(self, editor):
        """Undo stack should never exceed MAX_UNDO_STEPS."""
        for i in range(editor.MAX_UNDO_STEPS * 2):
            self._insert_with_command(editor, "x")
            assert editor.undo_stack.count() <= editor.MAX_UNDO_STEPS

    # --- Oldest Dropped First ---

    def test_fifo_behavior_at_limit(self, editor):
        """When at limit, oldest operations should be dropped (FIFO)."""
        for i in range(editor.MAX_UNDO_STEPS):
            self._insert_with_command(editor, str(i % 10))
        
        initial_count = editor.undo_stack.count()
        assert initial_count == editor.MAX_UNDO_STEPS
        
        self._insert_with_command(editor, "N")
        
        assert editor.undo_stack.count() == editor.MAX_UNDO_STEPS

    # --- Redo Stack Not Affected By Limit ---

    def test_redo_works_after_reaching_limit(self, editor):
        """Redo should still work after undo limit is reached."""
        for i in range(editor.MAX_UNDO_STEPS + 10):
            self._insert_with_command(editor, "x")
        
        editor.undo()
        assert editor.canRedo()
        
        content_after_undo = editor.toPlainText()
        editor.redo()
        
        assert len(editor.toPlainText()) == len(content_after_undo) + 1


class TestCodeEditorUncoveredPaths:
    """Tests targeting uncovered lines in code_editor.py."""

    # ── Helpers ──────────────────────────────────────────────────────

    def _type_char(self, editor, char):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        key = getattr(Qt.Key, f"Key_{char.upper()}")
        event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, char)
        editor.keyPressEvent(event)

    def _type_space(self, editor):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        editor.keyPressEvent(event)

    def _select_all(self, editor):
        cursor = editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor.setTextCursor(cursor)

    def _select_range(self, editor, start, end):
        cursor = editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)

    def _press_key(self, editor, key, modifiers=None, text=""):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        if modifiers is None:
            modifiers = Qt.KeyboardModifier.NoModifier
        event = QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)
        editor.keyPressEvent(event)

    def _press_enter(self, editor):
        from PyQt6.QtCore import Qt
        self._press_key(editor, Qt.Key.Key_Return, text="\r")

    # ── Lines 165-170: Ctrl+X and Ctrl+V ────────────────────────────

    def test_ctrl_x_cuts_selected_text(self, editor):
        """Ctrl+X should cut selected text to clipboard and support undo."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication

        editor.setPlainText("hello world")
        self._select_range(editor, 0, 5)  # select "hello"

        self._press_key(editor, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)

        assert editor.toPlainText() == " world"
        assert QApplication.clipboard().text() == "hello"

        editor.undo()
        assert editor.toPlainText() == "hello world"

    def test_ctrl_v_pastes_text(self, editor):
        """Ctrl+V should paste text from clipboard and support undo."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication

        editor.setPlainText("ab")
        QApplication.clipboard().setText("XY")

        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)

        self._press_key(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)

        assert editor.toPlainText() == "aXYb"

        editor.undo()
        assert editor.toPlainText() == "ab"

    def test_ctrl_shortcut_unhandled_key_no_changes(self, editor):
        """Unhandled Ctrl+Key should fall through without changes."""
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent

        editor.setPlainText("abc")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)

        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_P, Qt.KeyboardModifier.ControlModifier, "")
        editor.keyPressEvent(event)

        assert editor.toPlainText() == "abc"

    # ── Lines 195-207: Delete key ───────────────────────────────────

    def test_delete_key_with_selection(self, editor):
        """Delete key with selection removes selected text; undo restores it."""
        from PyQt6.QtCore import Qt

        editor.setPlainText("abcdef")
        self._select_range(editor, 1, 4)  # select "bcd"

        self._press_key(editor, Qt.Key.Key_Delete)

        assert editor.toPlainText() == "aef"

        editor.undo()
        assert editor.toPlainText() == "abcdef"

    def test_delete_key_without_selection(self, editor):
        """Delete key without selection removes char at cursor; undo restores it."""
        from PyQt6.QtCore import Qt

        editor.setPlainText("abc")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)

        self._press_key(editor, Qt.Key.Key_Delete)

        assert editor.toPlainText() == "ac"

        editor.undo()
        assert editor.toPlainText() == "abc"

    def test_delete_key_at_end_of_document(self, editor):
        """Delete key at end of document should be a no-op."""
        from PyQt6.QtCore import Qt

        editor.setPlainText("ab")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)

        self._press_key(editor, Qt.Key.Key_Delete)

        assert editor.toPlainText() == "ab"

    # ── Lines 217-227: Whitespace key with selection ────────────────

    def test_space_replaces_selection(self, editor):
        """Space key with selection replaces selected text; undo restores it."""
        editor.setPlainText("abcdef")
        self._select_range(editor, 1, 4)  # select "bcd"

        self._type_space(editor)

        assert editor.toPlainText() == "a ef"

        editor.undo()
        assert editor.toPlainText() == "abcdef"

    def test_enter_replaces_selection(self, editor):
        """Enter key with selection replaces selected text with newline; undo restores it."""
        editor.setPlainText("abcdef")
        self._select_range(editor, 1, 4)  # select "bcd"

        self._press_enter(editor)

        assert editor.toPlainText() == "a\nef"

        editor.undo()
        assert editor.toPlainText() == "abcdef"

    # ── Lines 257-258: Non-printable, non-special key ───────────────

    def test_non_printable_key_falls_through(self, editor):
        """A non-printable, non-special key (e.g. arrow) should not corrupt text."""
        from PyQt6.QtCore import Qt

        editor.setPlainText("test")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)

        # Type some chars to build up a pending insert, then press arrow to flush
        self._type_char(editor, "x")
        self._press_key(editor, Qt.Key.Key_Left)

        # Text should have the char, pending insert should be flushed (undo-able)
        assert "x" in editor.toPlainText()
        editor.undo()
        assert editor.toPlainText() == "test"

    # ── Lines 261-262: focusOutEvent ────────────────────────────────

    def test_focus_out_flushes_pending_insert(self, editor):
        """focusOutEvent should flush pending insert so it becomes undo-able."""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QFocusEvent

        editor.setPlainText("")
        self._type_char(editor, "a")
        self._type_char(editor, "b")

        # Pending insert hasn't been pushed yet
        assert editor.toPlainText() == "ab"

        # Simulate focus out
        focus_event = QFocusEvent(QEvent.Type.FocusOut)
        editor.focusOutEvent(focus_event)

        # Now undo should remove the pending "ab"
        editor.undo()
        assert editor.toPlainText() == ""

    # ── Lines 280-284: cut() with selection ─────────────────────────

    def test_cut_with_selection_and_undo(self, editor):
        """cut() removes selected text, puts it on clipboard, and undo restores it."""
        from PyQt6.QtWidgets import QApplication

        editor.setPlainText("hello world")
        self._select_range(editor, 6, 11)  # select "world"

        editor.cut()

        assert editor.toPlainText() == "hello "
        assert QApplication.clipboard().text() == "world"

        editor.undo()
        assert editor.toPlainText() == "hello world"

    def test_cut_without_selection_noop(self, editor):
        """cut() without selection should not change content or undo stack."""
        editor.setPlainText("hello")
        stack_count = editor.undo_stack.count()

        editor.cut()

        assert editor.toPlainText() == "hello"
        assert editor.undo_stack.count() == stack_count

    # ── Line 295: paste() with empty clipboard ──────────────────────

    def test_paste_with_empty_clipboard_is_noop(self, editor):
        """paste() with empty clipboard should not modify text."""
        from PyQt6.QtWidgets import QApplication

        editor.setPlainText("unchanged")
        QApplication.clipboard().setText("")

        editor.paste()

        assert editor.toPlainText() == "unchanged"

    # ── Lines 300-305: paste() over selection ────────────────────────

    def test_paste_over_selection_replaces_and_undo(self, editor):
        """paste() over selection replaces it; undo restores original."""
        from PyQt6.QtWidgets import QApplication

        editor.setPlainText("hello world")
        QApplication.clipboard().setText("PLANET")
        self._select_range(editor, 6, 11)  # select "world"

        editor.paste()

        assert editor.toPlainText() == "hello PLANET"

        editor.undo()
        assert editor.toPlainText() == "hello world"

    def test_apply_editor_colors_background_only(self, editor):
        """apply_editor_colors should handle background-only updates."""
        palette = editor.palette()
        original_text = palette.color(palette.ColorRole.Text).name()

        editor.apply_editor_colors("#112233", "")

        updated = editor.palette()
        assert updated.color(updated.ColorRole.Base).name() == "#112233"
        assert updated.color(updated.ColorRole.Text).name() == original_text

    def test_apply_editor_colors_no_changes(self, editor):
        """apply_editor_colors with empty values should not change palette."""
        palette = editor.palette()
        original_base = palette.color(palette.ColorRole.Base).name()
        original_text = palette.color(palette.ColorRole.Text).name()

        editor.apply_editor_colors("", "")

        updated = editor.palette()
        assert updated.color(updated.ColorRole.Base).name() == original_base
        assert updated.color(updated.ColorRole.Text).name() == original_text

    def test_apply_editor_colors_foreground_only(self, editor):
        """apply_editor_colors should handle foreground-only updates."""
        palette = editor.palette()
        original_base = palette.color(palette.ColorRole.Base).name()

        editor.apply_editor_colors("", "#ddeeff")

        updated = editor.palette()
        assert updated.color(updated.ColorRole.Base).name() == original_base
        assert updated.color(updated.ColorRole.Text).name() == "#ddeeff"

    def test_set_line_number_colors_partial_updates(self, editor):
        """set_line_number_colors should handle partial updates."""
        original_fg = editor._line_number_fg.name()

        editor.set_line_number_colors("#010203", "")
        assert editor._line_number_bg.name() == "#010203"
        assert editor._line_number_fg.name() == original_fg

        editor.set_line_number_colors("", "#040506")
        assert editor._line_number_fg.name() == "#040506"

    def test_set_line_number_colors_no_changes(self, editor):
        """set_line_number_colors with empty inputs should not change colors."""
        original_bg = editor._line_number_bg.name()
        original_fg = editor._line_number_fg.name()

        editor.set_line_number_colors("", "")

        assert editor._line_number_bg.name() == original_bg
        assert editor._line_number_fg.name() == original_fg

    # ── Line 315: apply_font with invalid size ──────────────────────

    def test_apply_font_invalid_size_no_change(self, editor):
        """apply_font with size <= 0 should not change the font."""
        original_font = editor.font().family()
        original_size = editor.font().pointSize()

        editor.apply_font("Courier", 0)

        assert editor.font().family() == original_font
        assert editor.font().pointSize() == original_size

    def test_apply_font_empty_family_no_change(self, editor):
        """apply_font with empty family should not change the font."""
        original_font = editor.font().family()
        original_size = editor.font().pointSize()

        editor.apply_font("", 12)

        assert editor.font().family() == original_font
        assert editor.font().pointSize() == original_size

    # ── Line 26: LineNumberArea.paintEvent delegation ───────────────

    def test_line_number_area_paint_event_delegation(self, editor):
        """LineNumberArea.paintEvent delegates to editor.line_number_area_paint_event."""
        from PyQt6.QtGui import QPaintEvent
        from PyQt6.QtCore import QRect
        from unittest.mock import patch

        editor.setPlainText("line1\nline2")
        editor.show()

        rect = QRect(0, 0, editor.line_number_area.width(), editor.height())
        event = QPaintEvent(rect)

        with patch.object(editor, "line_number_area_paint_event") as mock_paint:
            editor.line_number_area.paintEvent(event)
            mock_paint.assert_called_once_with(event)

    # ── Line 99: _update_line_number_area scroll branch ─────────────

    def test_update_line_number_area_scroll_branch(self, editor):
        """When dy != 0, the line_number_area should be scrolled."""
        from PyQt6.QtCore import QRect
        from unittest.mock import patch

        editor.setPlainText("\n".join(["line"] * 100))
        editor.show()

        with patch.object(editor.line_number_area, "scroll") as mock_scroll:
            editor._update_line_number_area(QRect(0, 0, 100, 100), 10)
            mock_scroll.assert_called_once_with(0, 10)

    # ── Lines 151-152: keyPressEvent during undo/redo ───────────────

    def test_key_press_during_undo_redo_passes_through(self, editor):
        """When _is_applying_undo_redo is True, keyPressEvent delegates to super."""
        from PyQt6.QtCore import Qt

        editor.setPlainText("abc")
        editor._is_applying_undo_redo = True

        try:
            # This should pass through to super without creating undo commands
            stack_count_before = editor.undo_stack.count()
            self._type_char(editor, "x")
            stack_count_after = editor.undo_stack.count()

            assert stack_count_after == stack_count_before, \
                "No undo command should be pushed during undo/redo application"
            assert "x" in editor.toPlainText()
        finally:
            editor._is_applying_undo_redo = False

    def test_focus_out_flushes_empty_pending_insert(self, editor):
        """focusOutEvent should be safe when no pending insert exists."""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QFocusEvent

        editor.setPlainText("")

        focus_event = QFocusEvent(QEvent.Type.FocusOut)
        editor.focusOutEvent(focus_event)

        assert editor.toPlainText() == ""


class TestReplaceTextCommandRedo:
    """Tests for ReplaceTextCommand redo path (lines 94-98) and _set_cursor_position."""

    def _type_char(self, editor, char):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        key = getattr(Qt.Key, f"Key_{char.upper()}")
        event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, char)
        editor.keyPressEvent(event)

    def _type_space(self, editor):
        from PyQt6.QtCore import Qt, QEvent
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        editor.keyPressEvent(event)

    def test_replace_text_undo_then_redo(self, editor):
        """Replacing selected text, undoing, then redoing should hit ReplaceTextCommand.redo lines 94-98."""
        # Type "abc " to create some text
        for char in "abc":
            self._type_char(editor, char)
        self._type_space(editor)

        assert editor.toPlainText() == "abc "

        # Select "b" (position 1-2) and replace with "X"
        cursor = editor.textCursor()
        cursor.setPosition(1)
        cursor.setPosition(2, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        self._type_char(editor, "x")

        assert editor.toPlainText() == "axc "

        # Undo -> should restore "abc "
        editor.undo()
        assert editor.toPlainText() == "abc "

        # Redo -> should re-apply the replacement (hits lines 94-98)
        editor.redo()
        assert editor.toPlainText() == "axc "

    def test_set_cursor_position_via_undo_redo(self, editor):
        """_set_cursor_position is used during undo/redo; verify cursor lands correctly."""
        for char in "hello":
            self._type_char(editor, char)
        self._type_space(editor)

        # Select "ell" (positions 1-4) and replace with "X"
        cursor = editor.textCursor()
        cursor.setPosition(1)
        cursor.setPosition(4, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        self._type_char(editor, "x")

        assert editor.toPlainText() == "hxo "

        # Undo
        editor.undo()
        assert editor.toPlainText() == "hello "

        # Redo
        editor.redo()
        assert editor.toPlainText() == "hxo "
        # Cursor should be after the replacement
        assert editor.textCursor().position() == 2

class TestUndoCommandsCoverage:
    """Direct tests for undo command helpers and UTF-16 handling."""

    def test_utf16_len_handles_surrogate_pair(self):
        from editor.undo_commands import _utf16_len

        assert _utf16_len("A") == 1
        assert _utf16_len("\U0001F600") == 2

    def test_insert_text_command_manual_redo(self, editor):
        from editor.undo_commands import InsertTextCommand

        cursor = editor.textCursor()
        cursor.insertText("hi")
        editor.setTextCursor(cursor)

        cmd = InsertTextCommand(editor, "hi", 0)
        cmd.redo()
        assert editor.toPlainText() == "hi"

        cmd.redo()
        assert editor.toPlainText() == "hihi"

    def test_text_edit_command_set_cursor_position(self, editor):
        from editor.undo_commands import TextEditCommand

        cmd = TextEditCommand(editor)
        cmd._set_cursor_position(0)
        assert editor.textCursor().position() == 0
