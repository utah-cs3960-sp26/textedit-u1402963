from PyQt6.QtWidgets import QPlainTextEdit, QWidget
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QKeyEvent, QUndoStack

from editor.undo_commands import InsertTextCommand, DeleteTextCommand, ReplaceTextCommand


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    WHITESPACE_KEYS = {Qt.Key.Key_Space, Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter}
    MAX_UNDO_STEPS = 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        self._undo_stack = QUndoStack(self)
        self._undo_stack.setUndoLimit(self.MAX_UNDO_STEPS)

        self._pending_insert_text = ""
        self._pending_insert_start = -1
        self._is_applying_undo_redo = False

        self.document().setUndoRedoEnabled(False)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)

        self._update_line_number_area_width(0)

    @property
    def undo_stack(self) -> QUndoStack:
        return self._undo_stack

    def undo(self):
        if self._pending_insert_text:
            self._flush_pending_insert()
        self._is_applying_undo_redo = True
        self._undo_stack.undo()
        self._is_applying_undo_redo = False

    def redo(self):
        if self._pending_insert_text:
            self._flush_pending_insert()
        self._is_applying_undo_redo = True
        self._undo_stack.redo()
        self._is_applying_undo_redo = False

    def canUndo(self) -> bool:
        return self._undo_stack.canUndo() or bool(self._pending_insert_text)

    def canRedo(self) -> bool:
        return self._undo_stack.canRedo()

    def line_number_area_width(self):
        digits = 1
        max_block = max(1, self.blockCount())
        while max_block >= 10:
            max_block //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance("9") * digits + 3
        return space

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(Qt.GlobalColor.lightGray).lighter(120))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(Qt.GlobalColor.darkGray))
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 3,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )
            block = block.next()
            if not block.isValid():
                break
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def _flush_pending_insert(self):
        """Push any pending insert as a command."""
        if self._pending_insert_text and self._pending_insert_start >= 0:
            cmd = InsertTextCommand(self, self._pending_insert_text, self._pending_insert_start)
            self._undo_stack.push(cmd)
            self._pending_insert_text = ""
            self._pending_insert_start = -1

    def keyPressEvent(self, event: QKeyEvent):
        if self._is_applying_undo_redo:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()
        cursor = self.textCursor()

        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Z:
                self.undo()
                return
            elif key == Qt.Key.Key_Y:
                self.redo()
                return
            elif key == Qt.Key.Key_X:
                self.cut()
                return
            elif key == Qt.Key.Key_V:
                self.paste()
                return

        if key == Qt.Key.Key_Backspace:
            self._flush_pending_insert()
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                deleted = cursor.selectedText()
                super().keyPressEvent(event)
                cmd = DeleteTextCommand(self, start, end, deleted)
                self._undo_stack.push(cmd)
            elif cursor.position() > 0:
                pos = cursor.position()
                cursor.setPosition(pos - 1, cursor.MoveMode.KeepAnchor)
                deleted = cursor.selectedText()
                super().keyPressEvent(event)
                cmd = DeleteTextCommand(self, pos - 1, pos, deleted)
                self._undo_stack.push(cmd)
            else:
                super().keyPressEvent(event)
            return

        if key == Qt.Key.Key_Delete:
            self._flush_pending_insert()
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                deleted = cursor.selectedText()
                super().keyPressEvent(event)
                cmd = DeleteTextCommand(self, start, end, deleted)
                self._undo_stack.push(cmd)
            elif cursor.position() < len(self.toPlainText()):
                pos = cursor.position()
                cursor.setPosition(pos + 1, cursor.MoveMode.KeepAnchor)
                deleted = cursor.selectedText()
                super().keyPressEvent(event)
                cmd = DeleteTextCommand(self, pos, pos + 1, deleted)
                self._undo_stack.push(cmd)
            else:
                super().keyPressEvent(event)
            return

        if key in self.WHITESPACE_KEYS:
            self._flush_pending_insert()
            
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                old_text = cursor.selectedText()
                new_text = "\n" if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) else event.text()
                super().keyPressEvent(event)
                cmd = ReplaceTextCommand(self, start, end, old_text, new_text)
                self._undo_stack.push(cmd)
            else:
                pos = cursor.position()
                new_text = "\n" if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) else event.text()
                super().keyPressEvent(event)
                cmd = InsertTextCommand(self, new_text, pos)
                self._undo_stack.push(cmd)
            return

        if event.text() and event.text().isprintable():
            if cursor.hasSelection():
                self._flush_pending_insert()
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                old_text = cursor.selectedText()
                new_text = event.text()
                super().keyPressEvent(event)
                cmd = ReplaceTextCommand(self, start, end, old_text, new_text)
                self._undo_stack.push(cmd)
            else:
                pos = cursor.position()
                if self._pending_insert_start < 0:
                    self._pending_insert_start = pos
                super().keyPressEvent(event)
                self._pending_insert_text += event.text()
            return

        self._flush_pending_insert()
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        self._flush_pending_insert()
        super().focusOutEvent(event)

    def clear(self):
        self._flush_pending_insert()
        self._undo_stack.clear()
        super().clear()

    def setPlainText(self, text: str):
        self._flush_pending_insert()
        self._undo_stack.clear()
        super().setPlainText(text)

    def cut(self):
        """Cut selected text with undo support."""
        self._flush_pending_insert()
        cursor = self.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            deleted_text = cursor.selectedText()
            super().cut()
            cmd = DeleteTextCommand(self, start, end, deleted_text)
            self._undo_stack.push(cmd)

    def paste(self):
        """Paste text with undo support."""
        from PyQt6.QtWidgets import QApplication
        
        self._flush_pending_insert()
        clipboard = QApplication.clipboard()
        text_to_paste = clipboard.text()
        
        if not text_to_paste:
            return
        
        cursor = self.textCursor()
        
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            old_text = cursor.selectedText()
            super().paste()
            cmd = ReplaceTextCommand(self, start, end, old_text, text_to_paste)
            self._undo_stack.push(cmd)
        else:
            pos = cursor.position()
            super().paste()
            cmd = InsertTextCommand(self, text_to_paste, pos)
            self._undo_stack.push(cmd)
