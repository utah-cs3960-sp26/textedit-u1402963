"""Document highlighter that integrates tokenizers with PyQt6's QSyntaxHighlighter."""

from PyQt6.QtGui import QSyntaxHighlighter, QTextDocument

from editor.highlighters.core.incremental_manager import IncrementalManager
from editor.highlighters.core.registry import HighlightRegistry
from editor.highlighters.core.stack_pool import StateStackPool
from editor.highlighters.core.style_registry import StyleId, StyleRegistry
from editor.highlighters.core.types import StackFrame, StateStack
from editor.highlighters.tokenizers.base_tokenizer import BaseTokenizer


class DocumentHighlighter(QSyntaxHighlighter):
    """Bridge between the tokenizer architecture and PyQt6."""

    def __init__(self, document: QTextDocument, lang_id: str = "plain") -> None:
        """Initialize the document highlighter.

        Args:
            document: The QTextDocument to highlight.
            lang_id: The language identifier for syntax highlighting.
        """
        super().__init__(document)
        self._registry = HighlightRegistry.instance()
        self._style_registry = StyleRegistry.instance()
        self._stack_pool = StateStackPool()
        self._incremental_manager = IncrementalManager()
        self._lang_id = lang_id
        self._tokenizer = self._get_tokenizer(lang_id)

    def _get_tokenizer(self, lang_id: str) -> BaseTokenizer:
        """Get tokenizer for the given language, falling back to plain."""
        tokenizer = self._registry.get_tokenizer(lang_id)
        if tokenizer is None:
            tokenizer = self._registry.get_default_tokenizer()
        return tokenizer

    def set_language(self, lang_id: str) -> None:
        """Switch to a different language tokenizer.

        Args:
            lang_id: The language identifier to switch to.
        """
        if lang_id == self._lang_id:
            return
        self._lang_id = lang_id
        self._tokenizer = self._get_tokenizer(lang_id)
        self._incremental_manager.clear()
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        """Qt override: Highlight a single block of text.

        Args:
            text: The text content of the block to highlight.
        """
        prev_state_id = self.previousBlockState()
        state_stack = self._stack_pool.get(prev_state_id)

        if not state_stack:
            state_stack = self._get_default_stack()

        tokenizer = self._get_active_tokenizer(state_stack)
        result = tokenizer.tokenize_line(text, state_stack)

        for token in result.tokens:
            try:
                style_id = StyleId(token.style_id)
                fmt = self._style_registry.get_format(style_id)
                self.setFormat(token.start, token.length, fmt)
            except ValueError:
                pass

        final_state_id = self._stack_pool.intern(result.final_stack)
        self.setCurrentBlockState(final_state_id)

        block = self.currentBlock()
        if block.isValid():
            block_number = block.blockNumber()
            doc = self.document()
            if doc:
                self._incremental_manager.set_line_count(doc.blockCount())
            self._incremental_manager.update_line(block_number, text, final_state_id)

    def _get_default_stack(self) -> StateStack:
        """Get the default state stack for the current language."""
        frame = StackFrame(
            lang_id=self._lang_id,
            sub_state=0,
            end_condition=None,
        )
        return (frame,)

    def _get_active_tokenizer(self, state_stack: StateStack) -> BaseTokenizer:
        """Get the appropriate tokenizer based on the state stack.

        Handles embedded languages by checking the top of the stack.

        Args:
            state_stack: The current state stack.

        Returns:
            The tokenizer to use for the current context.
        """
        if not state_stack:
            return self._tokenizer

        top_frame = state_stack[-1]
        if top_frame.lang_id != self._lang_id:
            embedded_tokenizer = self._registry.get_tokenizer(top_frame.lang_id)
            if embedded_tokenizer is not None:
                return embedded_tokenizer

        return self._tokenizer
