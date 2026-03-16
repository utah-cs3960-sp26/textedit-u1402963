from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QScrollBar
from PyQt6.QtCore import Qt, QRect, QSize, QTimer
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QKeyEvent,
    QUndoStack,
    QPalette,
    QFont,
    QFontMetrics,
    QFontDatabase,
    QTextCursor,
)

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
    DEFAULT_LINE_NUMBER_BG = QColor(Qt.GlobalColor.lightGray).lighter(120)
    DEFAULT_LINE_NUMBER_FG = QColor(Qt.GlobalColor.darkGray)
    LINE_NUMBER_FONT_SIZE = 10

    CHUNK_SIZE = 1000  # lines per chunk in virtual mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.line_number_area = LineNumberArea(self)

        self._undo_stack = QUndoStack(self)
        self._undo_stack.setUndoLimit(self.MAX_UNDO_STEPS)

        self._highlighter = None
        self._pending_insert_text = ""
        self._pending_insert_start = -1
        self._is_applying_undo_redo = False
        self._line_number_bg = self.DEFAULT_LINE_NUMBER_BG
        self._line_number_fg = self.DEFAULT_LINE_NUMBER_FG
        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_font.setPointSize(self.LINE_NUMBER_FONT_SIZE)
        self._line_number_font = fixed_font
        self.line_number_area.setFont(self._line_number_font)

        self.document().setUndoRedoEnabled(False)

        # Virtual mode state
        self._virtual_mode = False
        self._vdoc = None
        self._chunk_start = 0
        self._chunk_line_count = 0
        self._virtual_scrollbar = None
        self._loading_chunk = False
        self._cached_ln_width = -1
        self._on_load_complete = None
        self._viewport_highlighter = None

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)

        self._update_line_number_area_width(0)

    @property
    def undo_stack(self) -> QUndoStack:
        return self._undo_stack

    def set_highlighter(self, highlighter):
        """Store reference to the syntax highlighter for bulk-op optimization."""
        self._highlighter = highlighter
        # Cancel any pending deferred reattachment of a stale highlighter
        if hasattr(self, '_deferred_hl'):
            self._deferred_hl = None

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
        if self._cached_ln_width >= 0:
            return self._cached_ln_width
        return self._compute_line_number_area_width()

    def _compute_line_number_area_width(self):
        digits = 1
        if self._virtual_mode and self._vdoc:
            max_block = max(1, self._vdoc.line_count)
        elif hasattr(self, '_deferred_lines') and self._deferred_lines is not None:
            max_block = max(1, len(self._deferred_lines))
        else:
            max_block = max(1, self.blockCount())
        while max_block >= 10:
            max_block //= 10
            digits += 1
        metrics = QFontMetrics(self._line_number_font)
        space = 3 + metrics.horizontalAdvance("9") * digits + 3
        self._cached_ln_width = space
        return space

    def _update_line_number_area_width(self, _):
        self._cached_ln_width = -1
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            w = self.line_number_area.width()
            self.line_number_area.update(0, rect.y(), w, rect.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), self._line_number_bg)
        painter.setFont(self._line_number_font)
        painter.setPen(self._line_number_fg)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = int(self.blockBoundingGeometry(block).translated(offset).top())
        block_height = int(self.blockBoundingRect(block).height())
        bottom = top + block_height

        # In virtual mode, offset line numbers by chunk start
        line_offset = self._chunk_start if self._virtual_mode else 0
        event_top = event.rect().top()
        event_bottom = event.rect().bottom()
        ln_width = self.line_number_area.width() - 3
        align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        while block.isValid() and top <= event_bottom:
            if block.isVisible() and bottom >= event_top:
                painter.drawText(
                    0, top, ln_width, block_height, align,
                    str(block_number + line_offset + 1),
                )
            block = block.next()
            if not block.isValid():
                break
            top = bottom
            block_height = int(self.blockBoundingRect(block).height())
            bottom = top + block_height
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
            is_newline = key in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                old_text = cursor.selectedText()
                new_text = "\n" if is_newline else event.text()
                if is_newline:
                    cursor.removeSelectedText()
                    cursor.insertBlock()
                else:
                    super().keyPressEvent(event)
                cmd = ReplaceTextCommand(self, start, end, old_text, new_text)
                self._undo_stack.push(cmd)
            else:
                pos = cursor.position()
                new_text = "\n" if is_newline else event.text()
                if is_newline:
                    cursor.insertBlock()
                else:
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

    _LOAD_CHUNK_SIZE = 500

    def bulk_set_text(self, text: str):
        """Replace document contents without clearing the undo stack.

        Used by BulkReplaceCommand for fast undo/redo of replace-all.
        """
        self._flush_pending_insert()
        self._load_text(text)

    def setPlainText(self, text: str):
        self._flush_pending_insert()
        self._undo_stack.clear()
        self._load_text(text)

    def _load_text(self, text: str):
        """Shared text-loading logic for setPlainText and bulk_set_text.

        Detaches the highlighter, loads text in chunks (one chunk per
        event-loop tick to keep frames under 16ms), then reattaches.
        """
        self._deferred_lines = None

        hl = self._highlighter
        if hl:
            hl.setDocument(None)

        lines = text.split('\n')
        if len(lines) <= self._LOAD_CHUNK_SIZE:
            self.blockSignals(True)
            super().setPlainText(text)
            self.blockSignals(False)
            self._cached_ln_width = -1
            self._update_line_number_area_width(0)
            if hl:
                hl._suppress_rehighlight = True
                hl.setDocument(self.document())
                hl._suppress_rehighlight = False
        else:
            self.setUpdatesEnabled(False)
            self.blockSignals(True)
            first_chunk = '\n'.join(lines[:self._LOAD_CHUNK_SIZE])
            super().setPlainText(first_chunk)
            self.blockSignals(False)
            self._deferred_lines = lines
            self._deferred_offset = self._LOAD_CHUNK_SIZE
            self._cached_ln_width = -1
            self._update_line_number_area_width(0)
            self._deferred_hl = hl
            QTimer.singleShot(0, self._load_next_chunk)

    def _load_next_chunk(self):
        """Append next chunk of lines to the document (deferred)."""
        if not hasattr(self, '_deferred_lines') or self._deferred_lines is None:
            return
        lines = self._deferred_lines
        end = min(self._deferred_offset + self._LOAD_CHUNK_SIZE, len(lines))
        chunk = '\n'.join(lines[self._deferred_offset:end])

        self.blockSignals(True)
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText('\n' + chunk)
        self.blockSignals(False)

        self._deferred_offset = end
        if self._deferred_offset < len(lines):
            QTimer.singleShot(0, self._load_next_chunk)
        else:
            self._deferred_lines = None
            self._cached_ln_width = -1
            self._update_line_number_area_width(0)
            # Reattach highlighter with cascade prevention: batch_limit
            # caps highlightBlock calls so the first paint doesn't cascade
            # through all blocks (which would take 300-600ms for 8K+ lines).
            hl = getattr(self, '_deferred_hl', None)
            if hl:
                hl.set_batch_limit(100)
                hl._suppress_rehighlight = True
                hl.setDocument(self.document())
                hl._suppress_rehighlight = False
                self._deferred_hl = None
                # Clear batch limit after initial paint so scrolling highlights work
                QTimer.singleShot(0, lambda: hl.set_batch_limit(-1))
            # Re-enable widget updates (disabled in setPlainText)
            self.setUpdatesEnabled(True)
            if self._on_load_complete:
                cb = self._on_load_complete
                self._on_load_complete = None
                cb()

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

    def apply_font(self, family: str, size: int) -> None:
        """Apply editor font settings."""
        if not family or size <= 0:
            return
        font = QFont(family, size)
        self.setFont(font)
        # Keep line number font fixed regardless of editor font changes.
        self.line_number_area.setFont(self._line_number_font)
        self._update_line_number_area_width(0)
        self.line_number_area.update()

    def apply_editor_colors(self, background: str, foreground: str) -> None:
        """Apply editor background and foreground colors."""
        palette = self.palette()
        if background:
            palette.setColor(QPalette.ColorRole.Base, QColor(background))
        if foreground:
            palette.setColor(QPalette.ColorRole.Text, QColor(foreground))
        self.setPalette(palette)

    def set_line_number_colors(self, background: str, foreground: str) -> None:
        """Set line number area colors."""
        if background:
            self._line_number_bg = QColor(background)
        if foreground:
            self._line_number_fg = QColor(foreground)
        self.line_number_area.update()

    # ── Virtual mode (large file support) ───────────────────────────

    @property
    def virtual_mode(self):
        return self._virtual_mode

    @property
    def vdoc(self):
        return self._vdoc

    def enter_virtual_mode(self, vdoc, scrollbar: QScrollBar):
        """Switch to virtual mode backed by a VirtualDocument."""
        self._vdoc = vdoc
        self._virtual_mode = True
        self._virtual_scrollbar = scrollbar
        self._chunk_start = 0
        self._chunk_line_count = 0

        # Hide native vertical scrollbar; we use the external one
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Configure the external scrollbar
        scrollbar.setRange(0, max(0, vdoc.line_count - 1))
        scrollbar.setSingleStep(3)
        scrollbar.setPageStep(self._visible_line_count())
        scrollbar.setValue(0)
        scrollbar.valueChanged.connect(self._on_virtual_scroll)
        scrollbar.setVisible(True)

        # Detach QSyntaxHighlighter — virtual mode uses ViewportHighlighter
        hl = self._highlighter
        if hl:
            hl.set_enabled(False)
            hl.setDocument(None)

        self._load_chunk(0)
        self._update_line_number_area_width(0)

    def exit_virtual_mode(self):
        """Leave virtual mode and restore normal editor behavior."""
        if not self._virtual_mode:
            return
        self._save_chunk_edits()
        if self._virtual_scrollbar:
            try:
                self._virtual_scrollbar.valueChanged.disconnect(self._on_virtual_scroll)
            except TypeError:
                pass
            self._virtual_scrollbar.setVisible(False)
        # Clean up viewport highlighter
        self._viewport_highlighter = None
        # Reattach QSyntaxHighlighter for normal mode
        hl = self._highlighter
        if hl:
            hl.set_enabled(True)
            hl._suppress_rehighlight = True
            hl.setDocument(self.document())
            hl._suppress_rehighlight = False
        self._virtual_mode = False
        self._vdoc = None
        self._chunk_start = 0
        self._chunk_line_count = 0
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def _visible_line_count(self):
        """Approximate number of visible lines in the viewport."""
        if self.fontMetrics().height() <= 0:
            return 40
        return max(1, self.viewport().height() // self.fontMetrics().height())

    _VIRTUAL_INITIAL_LINES = 500  # lines to load immediately per frame

    def _load_chunk(self, target_line: int, local_line: int = 0):
        """Load a chunk of lines centered around target_line into the editor.

        Loads a small initial slice immediately for fast first-frame rendering,
        then fills the rest of the chunk across subsequent event-loop ticks.
        """
        if not self._vdoc:
            return

        # Cancel any pending deferred chunk fill
        self._deferred_chunk = None

        # Only save edits if a previous chunk was loaded
        if self._chunk_line_count > 0:
            self._save_chunk_edits()

        half = self.CHUNK_SIZE // 2
        start = max(0, target_line - half)
        end = min(self._vdoc.line_count, start + self.CHUNK_SIZE)
        start = max(0, end - self.CHUNK_SIZE)

        self._chunk_start = start
        self._chunk_line_count = end - start

        # Load only a small initial slice for the first frame
        initial_count = min(self._VIRTUAL_INITIAL_LINES, self._chunk_line_count)
        text = self._vdoc.get_lines(start, initial_count)

        self._loading_chunk = True
        self.blockSignals(True)
        super().setPlainText(text)
        self.blockSignals(False)
        self._loading_chunk = False

        self._undo_stack.clear()

        # Scroll to the desired local line within the loaded range
        target_local = max(0, min(local_line, initial_count - 1))
        block = self.document().findBlockByNumber(target_local)
        if block.isValid():
            cursor = QTextCursor(block)
            self.setTextCursor(cursor)
            self.centerCursor()

        self._update_line_number_area_width(0)
        self.line_number_area.update()

        # Use viewport highlighter — no QSyntaxHighlighter cascade
        if self._viewport_highlighter:
            self._viewport_highlighter.clear_cache()
            self._viewport_highlighter.highlight_viewport()

        # Schedule deferred loading of the rest of the chunk
        if initial_count < self._chunk_line_count:
            self._deferred_chunk = {
                'start': start,
                'loaded': initial_count,
                'total': self._chunk_line_count,
            }
            QTimer.singleShot(0, self._fill_chunk)

    def _fill_chunk(self):
        """Append the next batch of lines to the document (deferred)."""
        dc = getattr(self, '_deferred_chunk', None)
        if dc is None:
            return

        loaded = dc['loaded']
        total = dc['total']
        chunk_start = dc['start']
        batch = min(self._VIRTUAL_INITIAL_LINES, total - loaded)

        text = self._vdoc.get_lines(chunk_start + loaded, batch)

        self._loading_chunk = True
        self.blockSignals(True)
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText('\n' + text)
        self.blockSignals(False)
        self._loading_chunk = False

        dc['loaded'] = loaded + batch
        if dc['loaded'] < total:
            QTimer.singleShot(0, self._fill_chunk)
        else:
            self._deferred_chunk = None

    def _save_chunk_edits(self):
        """Save any edits in the current chunk back to VirtualDocument."""
        if not self._virtual_mode or not self._vdoc:
            return
        current_text = self.toPlainText()
        self._vdoc.set_lines_from_chunk(self._chunk_start, current_text)

    def _on_virtual_scroll(self, value):
        """Handle external scrollbar value changes."""
        if self._loading_chunk:
            return

        # Check if the target line is within the current chunk with margin
        margin = self.CHUNK_SIZE // 4
        chunk_end = self._chunk_start + self._chunk_line_count
        if self._chunk_start + margin <= value <= chunk_end - margin - self._visible_line_count():
            # Still within chunk, just scroll internally
            local_line = value - self._chunk_start
            self.verticalScrollBar().setValue(local_line)
            # Re-highlight newly visible blocks
            if self._viewport_highlighter:
                self._viewport_highlighter.highlight_viewport()
            return

        # Need to load a new chunk
        self._load_chunk(value, value - max(0, value - self.CHUNK_SIZE // 2))

    def wheelEvent(self, event):
        if self._virtual_mode and self._virtual_scrollbar:
            delta = event.angleDelta().y()
            lines = -(delta // 40) if delta != 0 else 0
            new_val = self._virtual_scrollbar.value() + lines
            self._virtual_scrollbar.setValue(
                max(0, min(new_val, self._virtual_scrollbar.maximum()))
            )
            event.accept()
        else:
            super().wheelEvent(event)

    def go_to_line_virtual(self, line_no: int):
        """Jump to a specific global line number in virtual mode."""
        if not self._virtual_mode or not self._vdoc:
            return
        line_no = max(0, min(line_no, self._vdoc.line_count - 1))
        self._load_chunk(line_no, line_no - max(0, line_no - self.CHUNK_SIZE // 2))
        if self._virtual_scrollbar:
            self._virtual_scrollbar.blockSignals(True)
            self._virtual_scrollbar.setValue(line_no)
            self._virtual_scrollbar.blockSignals(False)
