"""Viewport-only syntax highlighter for virtual mode.

Bypasses QSyntaxHighlighter entirely to avoid cascade re-highlighting.
Applies formats directly to visible blocks via QTextLayout.setFormats(),
giving O(viewport) cost per scroll/update instead of O(document).
"""

from PyQt6.QtGui import QTextLayout, QTextCharFormat

from editor.highlighters.core.registry import HighlightRegistry
from editor.highlighters.core.stack_pool import StateStackPool
from editor.highlighters.core.style_registry import StyleId, StyleRegistry
from editor.highlighters.core.types import StackFrame, StateStack


class ViewportHighlighter:
    """Highlights only visible blocks by writing directly to QTextLayout."""

    def __init__(self, editor, lang_id: str = "plain"):
        self._editor = editor
        self._registry = HighlightRegistry.instance()
        self._style_registry = StyleRegistry.instance()
        self._stack_pool = StateStackPool()
        self._lang_id = lang_id
        self._tokenizer = self._get_tokenizer(lang_id)
        # Cache: block_number -> final_state_id for the loaded chunk
        self._state_cache: dict[int, int] = {}
        self._pending = False

    def set_language(self, lang_id: str):
        if lang_id == self._lang_id:
            return
        self._lang_id = lang_id
        self._tokenizer = self._get_tokenizer(lang_id)
        self._state_cache.clear()

    def clear_cache(self):
        self._state_cache.clear()

    def _get_tokenizer(self, lang_id: str):
        tokenizer = self._registry.get_tokenizer(lang_id)
        if tokenizer is None:
            tokenizer = self._registry.get_default_tokenizer()
        return tokenizer

    def _get_default_stack(self) -> StateStack:
        return (StackFrame(lang_id=self._lang_id, sub_state=0, end_condition=None),)

    def _get_active_tokenizer(self, state_stack: StateStack):
        if not state_stack:
            return self._tokenizer
        top = state_stack[-1]
        if top.lang_id != self._lang_id:
            t = self._registry.get_tokenizer(top.lang_id)
            if t is not None:
                return t
        return self._tokenizer

    def highlight_viewport(self):
        """Format only the visible blocks in the editor."""
        self._pending = False
        editor = self._editor
        doc = editor.document()
        if not doc:
            return

        # Determine visible block range
        first_block = editor.firstVisibleBlock()
        if not first_block.isValid():
            return

        first_num = first_block.blockNumber()
        viewport_height = editor.viewport().height()
        line_height = editor.fontMetrics().height()
        if line_height <= 0:
            visible_count = 40
        else:
            visible_count = (viewport_height // line_height) + 2

        last_num = min(first_num + visible_count, doc.blockCount() - 1)

        # Walk backwards from first_num to find a cached state, or start from 0
        start_num = first_num
        start_state_id = -1
        for bn in range(first_num - 1, -1, -1):
            if bn in self._state_cache:
                start_state_id = self._state_cache[bn]
                start_num = bn + 1
                break

        # If no cache found, tokenize from block 0 up to first_num
        if start_num > first_num:
            start_num = first_num
        if start_state_id == -1 and first_num > 0:
            start_num = 0

        # Tokenize from start_num through last_num
        block = doc.findBlockByNumber(start_num)
        state_stack = self._stack_pool.get(start_state_id)
        if not state_stack:
            state_stack = self._get_default_stack()

        bn = start_num
        while block.isValid() and bn <= last_num:
            text = block.text()
            tokenizer = self._get_active_tokenizer(state_stack)
            result = tokenizer.tokenize_line(text, state_stack)

            final_state_id = self._stack_pool.intern(result.final_stack)
            self._state_cache[bn] = final_state_id
            state_stack = result.final_stack

            # Only apply formats to visible blocks
            if bn >= first_num:
                ranges = []
                for token in result.tokens:
                    try:
                        sid = StyleId(token.style_id)
                        fmt = self._style_registry.get_format(sid)
                        fr = QTextLayout.FormatRange()
                        fr.start = token.start
                        fr.length = token.length
                        fr.format = fmt
                        ranges.append(fr)
                    except ValueError:
                        pass
                layout = block.layout()
                if layout:
                    layout.setFormats(ranges)

            block = block.next()
            bn += 1

        # Mark visible region dirty so Qt repaints.
        # Block signals to prevent textChanged from re-triggering _mark_modified.
        if first_num <= last_num:
            first_block = doc.findBlockByNumber(first_num)
            last_block = doc.findBlockByNumber(last_num)
            if first_block.isValid() and last_block.isValid():
                start_pos = first_block.position()
                end_pos = last_block.position() + last_block.length()
                editor.blockSignals(True)
                doc.markContentsDirty(start_pos, end_pos - start_pos)
                editor.blockSignals(False)

    def request_highlight(self):
        """Coalesced highlight request — at most once per event loop tick."""
        if self._pending:
            return
        self._pending = True
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self.highlight_viewport)
