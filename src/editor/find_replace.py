"""Find and Replace bar widget for the code editor."""

import re
import threading

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QTextDocument, QTextCursor, QColor, QTextCharFormat
from PyQt6.QtWidgets import QTextEdit

from editor.undo_commands import ReplaceTextCommand, BulkReplaceCommand


class FindWorker(QObject):
    """Runs VirtualDocument.find_all on a background thread."""

    finished = pyqtSignal(list, int)

    def __init__(self, vdoc, pattern, case_sensitive, use_regex, generation):
        super().__init__()
        self._vdoc = vdoc
        self._pattern = pattern
        self._case_sensitive = case_sensitive
        self._use_regex = use_regex
        self._generation = generation
        self._abort = threading.Event()

    def abort(self):
        self._abort.set()

    def run(self):
        results = self._vdoc.find_all(
            self._pattern,
            case_sensitive=self._case_sensitive,
            use_regex=self._use_regex,
            abort_flag=self._abort,
        )
        if not self._abort.is_set():
            self.finished.emit(results, self._generation)


class FindReplaceBar(QWidget):
    """A compact find-and-replace bar that sits below the editor."""

    HIGHLIGHT_COLOR = QColor("#33FFD700")
    CURRENT_HIGHLIGHT_COLOR = QColor("#80FFD700")

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self._editor = editor
        self._match_count = 0
        self._current_match = 0
        self._extra_selections = []
        self._search_generation = 0
        self._find_thread = None
        self._find_worker = None
        self._cached_virtual_matches = []
        self.setVisible(False)
        self._setup_ui()

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(400)
        self._debounce_timer.timeout.connect(self._on_search_changed)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(4)

        find_row = QHBoxLayout()
        find_row.setSpacing(4)

        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText("Find")
        self._find_input.setClearButtonEnabled(True)
        self._find_input.textChanged.connect(self._debounce_search)
        self._find_input.returnPressed.connect(self.find_next)
        find_row.addWidget(self._find_input, 1)

        self._case_check = QCheckBox("Aa")
        self._case_check.setToolTip("Match Case")
        self._case_check.toggled.connect(self._debounce_search)
        find_row.addWidget(self._case_check)

        self._regex_check = QCheckBox(".*")
        self._regex_check.setToolTip("Use Regular Expression")
        self._regex_check.toggled.connect(self._debounce_search)
        find_row.addWidget(self._regex_check)

        self._match_label = QLabel("")
        self._match_label.setMinimumWidth(70)
        self._match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        find_row.addWidget(self._match_label)

        prev_btn = QPushButton("▲")
        prev_btn.setFixedWidth(30)
        prev_btn.setToolTip("Find Previous")
        prev_btn.clicked.connect(self.find_previous)
        find_row.addWidget(prev_btn)

        next_btn = QPushButton("▼")
        next_btn.setFixedWidth(30)
        next_btn.setToolTip("Find Next")
        next_btn.clicked.connect(self.find_next)
        find_row.addWidget(next_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(30)
        close_btn.setToolTip("Close (Escape)")
        close_btn.clicked.connect(self.hide_bar)
        find_row.addWidget(close_btn)

        main_layout.addLayout(find_row)

        replace_row = QHBoxLayout()
        replace_row.setSpacing(4)

        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("Replace")
        self._replace_input.setClearButtonEnabled(True)
        self._replace_input.returnPressed.connect(self.replace_next)
        replace_row.addWidget(self._replace_input, 1)

        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self.replace_next)
        replace_row.addWidget(replace_btn)

        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self.replace_all)
        replace_row.addWidget(replace_all_btn)

        main_layout.addLayout(replace_row)

    def _debounce_search(self):
        if self._find_worker:
            self._find_worker.abort()
        self._debounce_timer.start()

    def _cancel_search(self):
        """Cancel any running background search."""
        if self._find_worker:
            self._find_worker.abort()
            try:
                self._find_worker.finished.disconnect(self._on_find_finished)
            except TypeError:
                pass
        if self._find_thread and self._find_thread.isRunning():
            self._find_thread.quit()
            self._find_thread.wait(2000)
        self._find_worker = None
        self._find_thread = None

    def _start_virtual_search(self):
        """Kick off a background find_all for virtual mode."""
        self._cancel_search()
        self._search_generation += 1
        gen = self._search_generation

        self._match_label.setText("Searching\u2026")
        self._match_label.setStyleSheet("")

        self._find_thread = QThread()
        self._find_worker = FindWorker(
            self._editor.vdoc,
            self._get_pattern(),
            self._case_check.isChecked(),
            self._regex_check.isChecked(),
            gen,
        )
        self._find_worker.moveToThread(self._find_thread)
        self._find_thread.started.connect(self._find_worker.run)
        self._find_worker.finished.connect(self._on_find_finished)
        self._find_worker.finished.connect(self._find_thread.quit)
        self._find_thread.start()

    def _on_find_finished(self, matches, generation):
        """Handle results arriving from the background search."""
        if generation != self._search_generation:
            return
        self._cached_virtual_matches = matches
        self._match_count = len(matches)
        if self._match_count == 0:
            self._match_label.setText("No results")
            self._match_label.setStyleSheet("color: #CC0000;")
            self._current_match = 0
        else:
            self._current_match = 1
            self._match_label.setText(f"1 of {self._match_count}")
            self._match_label.setStyleSheet("")
            self.find_next(wrap=True, from_start=True)

    def _build_find_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self._case_check.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def _get_pattern(self):
        return self._find_input.text()

    def _on_search_changed(self):
        pattern = self._get_pattern()
        if not pattern:
            self._cancel_search()
            self._cached_virtual_matches = []
            self._match_count = 0
            self._current_match = 0
            self._match_label.setText("")
            self._clear_highlights()
            return

        if self._editor.virtual_mode and self._editor.vdoc:
            self._start_virtual_search()
        else:
            self._update_match_count()
            self.find_next(wrap=True, from_start=True)

    def _find_all_matches(self):
        """Return a list of (start, end) positions for all matches.

        In virtual mode, returns (line_no, col, length) tuples from VirtualDocument.
        In normal mode, returns (start, end) character-position tuples.
        """
        pattern = self._get_pattern()
        if not pattern:
            return []

        if self._editor.virtual_mode and self._editor.vdoc:
            return self._cached_virtual_matches

        text = self._editor.toPlainText()
        matches = []

        if self._regex_check.isChecked():
            flags = 0 if self._case_check.isChecked() else re.IGNORECASE
            try:
                for m in re.finditer(pattern, text, flags):
                    matches.append((m.start(), m.end()))
            except re.error:
                return []
        else:
            if not self._case_check.isChecked():
                lower_text = text.lower()
                lower_pattern = pattern.lower()
            else:
                lower_text = text
                lower_pattern = pattern

            start = 0
            pat_len = len(lower_pattern)
            while True:
                idx = lower_text.find(lower_pattern, start)
                if idx == -1:
                    break
                matches.append((idx, idx + pat_len))
                start = idx + 1

        return matches

    def _update_match_count(self):
        matches = self._find_all_matches()
        self._match_count = len(matches)
        if not self._get_pattern():
            self._match_label.setText("")
            self._clear_highlights()
            return

        if self._match_count == 0:
            self._match_label.setText("No results")
            self._match_label.setStyleSheet("color: #CC0000;")
            self._clear_highlights()
        else:
            if self._editor.virtual_mode:
                self._current_match = 1
                self._match_label.setText(f"{self._current_match} of {self._match_count}")
                self._match_label.setStyleSheet("")
                self._clear_highlights()
            else:
                cursor_pos = self._editor.textCursor().position()
                self._current_match = 0
                for i, (start, end) in enumerate(matches):
                    if start >= cursor_pos:
                        self._current_match = i + 1
                        break
                else:
                    self._current_match = self._match_count

                self._match_label.setText(f"{self._current_match} of {self._match_count}")
                self._match_label.setStyleSheet("")
                self._highlight_matches(matches)

    def _highlight_matches(self, matches):
        """Highlight all matches using extra selections (efficient for QPlainTextEdit)."""
        selections = []
        doc = self._editor.document()
        current_cursor = self._editor.textCursor()
        current_sel_start = current_cursor.selectionStart()
        current_sel_end = current_cursor.selectionEnd()

        for start, end in matches:
            sel = QTextEdit.ExtraSelection()
            cursor = QTextCursor(doc)
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            fmt = QTextCharFormat()
            if start == current_sel_start and end == current_sel_end:
                fmt.setBackground(self.CURRENT_HIGHLIGHT_COLOR)
            else:
                fmt.setBackground(self.HIGHLIGHT_COLOR)
            sel.cursor = cursor
            sel.format = fmt
            selections.append(sel)

        self._extra_selections = selections
        self._editor.setExtraSelections(selections)

    def _clear_highlights(self):
        self._extra_selections = []
        self._editor.setExtraSelections([])

    def find_next(self, wrap=True, from_start=False):
        pattern = self._get_pattern()
        if not pattern:
            return False

        if self._editor.virtual_mode and self._editor.vdoc:
            return self._find_next_virtual(wrap, from_start)

        flags = self._build_find_flags()
        cursor = self._editor.textCursor()

        if from_start:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._editor.setTextCursor(cursor)

        if self._regex_check.isChecked():
            from PyQt6.QtCore import QRegularExpression

            rx_opts = QRegularExpression.PatternOption.NoPatternOption
            if not self._case_check.isChecked():
                rx_opts |= QRegularExpression.PatternOption.CaseInsensitiveOption
            rx = QRegularExpression(pattern, rx_opts)
            found = self._editor.find(rx, flags)
        else:
            found = self._editor.find(pattern, flags)

        if not found and wrap:
            cursor = self._editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._editor.setTextCursor(cursor)
            if self._regex_check.isChecked():
                found = self._editor.find(rx, flags)
            else:
                found = self._editor.find(pattern, flags)

        if found:
            self._update_match_count()
        return found

    def find_previous(self):
        pattern = self._get_pattern()
        if not pattern:
            return False

        if self._editor.virtual_mode and self._editor.vdoc:
            return self._find_previous_virtual()

        flags = self._build_find_flags() | QTextDocument.FindFlag.FindBackward

        if self._regex_check.isChecked():
            from PyQt6.QtCore import QRegularExpression

            rx_opts = QRegularExpression.PatternOption.NoPatternOption
            if not self._case_check.isChecked():
                rx_opts |= QRegularExpression.PatternOption.CaseInsensitiveOption
            rx = QRegularExpression(pattern, rx_opts)
            found = self._editor.find(rx, flags)
        else:
            found = self._editor.find(pattern, flags)

        if not found:
            cursor = self._editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self._editor.setTextCursor(cursor)
            if self._regex_check.isChecked():
                found = self._editor.find(rx, flags)
            else:
                found = self._editor.find(pattern, flags)

        if found:
            self._update_match_count()
        return found

    # ── Virtual mode find helpers ───────────────────────────────────

    def _find_next_virtual(self, wrap=True, from_start=False):
        """Find next match in virtual mode using VirtualDocument."""
        matches = self._find_all_matches()
        if not matches:
            return False

        editor = self._editor
        cursor = editor.textCursor()
        # Current global line and column
        if from_start:
            cur_line, cur_col = 0, 0
        else:
            local_block = cursor.blockNumber()
            cur_line = editor._chunk_start + local_block
            cur_col = cursor.positionInBlock()
            # Move past current selection
            if cursor.hasSelection():
                cur_col = cursor.positionInBlock()

        # Find the next match after current position
        for line_no, col, length in matches:
            if (line_no, col) > (cur_line, cur_col):
                self._jump_to_virtual_match(line_no, col, length)
                self._update_match_count()
                return True

        # Wrap around
        if wrap and matches:
            line_no, col, length = matches[0]
            self._jump_to_virtual_match(line_no, col, length)
            self._update_match_count()
            return True

        return False

    def _find_previous_virtual(self):
        """Find previous match in virtual mode."""
        matches = self._find_all_matches()
        if not matches:
            return False

        editor = self._editor
        cursor = editor.textCursor()
        local_block = cursor.blockNumber()
        cur_line = editor._chunk_start + local_block
        cur_col = cursor.positionInBlock()

        # Find the previous match before current position
        for line_no, col, length in reversed(matches):
            if (line_no, col) < (cur_line, cur_col):
                self._jump_to_virtual_match(line_no, col, length)
                self._update_match_count()
                return True

        # Wrap around to last match
        if matches:
            line_no, col, length = matches[-1]
            self._jump_to_virtual_match(line_no, col, length)
            self._update_match_count()
            return True

        return False

    def _jump_to_virtual_match(self, line_no, col, length):
        """Load the chunk containing the match and select it."""
        editor = self._editor
        editor.go_to_line_virtual(line_no)
        # Now select the match within the loaded chunk
        local_line = line_no - editor._chunk_start
        block = editor.document().findBlockByNumber(local_line)
        if block.isValid():
            cursor = QTextCursor(block)
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.MoveAnchor,
                col,
            )
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.KeepAnchor,
                length,
            )
            editor.setTextCursor(cursor)
            editor.centerCursor()

    def replace_next(self):
        """Replace the current selection if it matches, then find next."""
        pattern = self._get_pattern()
        if not pattern:
            return

        cursor = self._editor.textCursor()
        if not cursor.hasSelection():
            self.find_next()
            return

        selected = cursor.selectedText()
        replacement = self._replace_input.text()

        if self._regex_check.isChecked():
            flags = 0 if self._case_check.isChecked() else re.IGNORECASE
            try:
                match = re.fullmatch(pattern, selected, flags)
            except re.error:
                return
            if match:
                actual_replacement = match.expand(replacement)
                start = cursor.selectionStart()
                self._editor._flush_pending_insert()
                cursor.insertText(actual_replacement)
                cmd = ReplaceTextCommand(
                    self._editor, start, start + len(selected),
                    selected, actual_replacement,
                )
                self._editor.undo_stack.push(cmd)
            self.find_next()
        else:
            if self._case_check.isChecked():
                is_match = selected == pattern
            else:
                is_match = selected.lower() == pattern.lower()

            if is_match:
                start = cursor.selectionStart()
                self._editor._flush_pending_insert()
                cursor.insertText(replacement)
                cmd = ReplaceTextCommand(
                    self._editor, start, start + len(selected),
                    selected, replacement,
                )
                self._editor.undo_stack.push(cmd)
            self.find_next()

    def replace_all(self):
        """Replace all occurrences efficiently using a single edit block."""
        pattern = self._get_pattern()
        if not pattern:
            return 0

        if self._editor.virtual_mode and self._editor.vdoc:
            return self._replace_all_virtual()

        replacement = self._replace_input.text()
        text = self._editor.toPlainText()

        if self._regex_check.isChecked():
            flags = 0 if self._case_check.isChecked() else re.IGNORECASE
            try:
                new_text, count = re.subn(pattern, replacement, text, flags=flags)
            except re.error:
                return 0
        else:
            if self._case_check.isChecked():
                count = text.count(pattern)
                new_text = text.replace(pattern, replacement)
            else:
                compiled = re.compile(re.escape(pattern), re.IGNORECASE)
                new_text, count = compiled.subn(replacement, text)

        if count > 0:
            self._editor._flush_pending_insert()
            self._editor.bulk_set_text(new_text)
            cmd = BulkReplaceCommand(self._editor, text, new_text)
            self._editor.undo_stack.push(cmd)

            self._match_count = 0
            self._current_match = 0
            self._match_label.setText("0 matches")
            self._clear_highlights()

        return count

    def _replace_all_virtual(self):
        """Replace all occurrences in virtual mode via VirtualDocument."""
        self._cancel_search()
        pattern = self._get_pattern()
        replacement = self._replace_input.text()
        vdoc = self._editor.vdoc

        count = vdoc.replace_all(
            pattern, replacement,
            case_sensitive=self._case_check.isChecked(),
            use_regex=self._regex_check.isChecked(),
        )

        if count > 0:
            # Prevent _load_chunk from saving the stale (pre-replace) chunk
            # text back into vdoc, which would overwrite the replacements
            # for lines currently visible in the editor.
            self._editor._chunk_line_count = 0
            self._editor._load_chunk(
                self._editor._chunk_start,
                0,
            )
            self._cached_virtual_matches = []
            self._match_count = 0
            self._current_match = 0
            self._match_label.setText(f"{count} replaced")
            self._match_label.setStyleSheet("")
            self._clear_highlights()

        return count

    def show_bar(self, replace_visible=True):
        """Show the find bar, optionally with the replace row."""
        self.setVisible(True)
        self._find_input.setFocus()
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            self._find_input.setText(cursor.selectedText())
        self._find_input.selectAll()

    def hide_bar(self):
        self._cancel_search()
        self.setVisible(False)
        self._clear_highlights()
        self._editor.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_bar()
            return
        super().keyPressEvent(event)
