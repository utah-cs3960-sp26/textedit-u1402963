from PyQt6.QtGui import QUndoCommand, QTextCursor


def _utf16_len(text: str) -> int:
    """Return the UTF-16 code unit length of a string (for Qt cursor positions)."""
    return len(text.encode('utf-16-le')) // 2


class TextEditCommand(QUndoCommand):
    """
    Base command for text edit operations that can be undone/redone.
    
    IMPORTANT: These commands assume the text change has ALREADY been made
    to the document before the command is pushed. The first call to redo()
    (which happens automatically on push) is skipped. Subsequent redo() calls
    after undo() will apply the change.
    """

    def __init__(self, editor, description: str = "Text Edit"):
        super().__init__(description)
        self._editor = editor
        self._first_redo = True

    def _set_cursor_position(self, position: int):
        cursor = self._editor.textCursor()
        cursor.setPosition(position)
        self._editor.setTextCursor(cursor)


class InsertTextCommand(TextEditCommand):
    """Command for inserting text (text already inserted before push)."""

    def __init__(self, editor, text: str, position: int):
        super().__init__(editor, f"Insert '{text[:20]}...' " if len(text) > 20 else f"Insert '{text}'")
        self._text = text
        self._position = position

    def redo(self):
        if self._first_redo:
            self._first_redo = False
            return
        cursor = self._editor.textCursor()
        cursor.setPosition(self._position)
        cursor.insertText(self._text)
        self._editor.setTextCursor(cursor)

    def undo(self):
        cursor = self._editor.textCursor()
        cursor.setPosition(self._position)
        cursor.setPosition(self._position + _utf16_len(self._text), QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        self._editor.setTextCursor(cursor)


class DeleteTextCommand(TextEditCommand):
    """Command for deleting text (text already deleted before push)."""

    def __init__(self, editor, start: int, end: int, deleted_text: str):
        super().__init__(editor, f"Delete '{deleted_text[:20]}...'" if len(deleted_text) > 20 else f"Delete '{deleted_text}'")
        self._start = start
        self._end = end
        self._deleted_text = deleted_text

    def redo(self):
        if self._first_redo:
            self._first_redo = False
            return
        cursor = self._editor.textCursor()
        cursor.setPosition(self._start)
        cursor.setPosition(self._start + _utf16_len(self._deleted_text), QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        self._editor.setTextCursor(cursor)

    def undo(self):
        cursor = self._editor.textCursor()
        cursor.setPosition(self._start)
        cursor.insertText(self._deleted_text)
        self._editor.setTextCursor(cursor)


class ReplaceTextCommand(TextEditCommand):
    """Command for replacing selected text (replacement already done before push)."""

    def __init__(self, editor, start: int, end: int, old_text: str, new_text: str):
        super().__init__(editor, "Replace Text")
        self._start = start
        self._old_text = old_text
        self._new_text = new_text

    def redo(self):
        if self._first_redo:
            self._first_redo = False
            return
        cursor = self._editor.textCursor()
        cursor.setPosition(self._start)
        cursor.setPosition(self._start + _utf16_len(self._old_text), QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(self._new_text)
        self._editor.setTextCursor(cursor)

    def undo(self):
        cursor = self._editor.textCursor()
        cursor.setPosition(self._start)
        cursor.setPosition(self._start + _utf16_len(self._new_text), QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(self._old_text)
        self._editor.setTextCursor(cursor)
