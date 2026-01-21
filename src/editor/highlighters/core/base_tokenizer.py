from abc import ABC, abstractmethod

from editor.highlighters.core.types import (
    Token,
    StackFrame,
    StateStack,
    TokenizeResult,
    StyleId,
)


class BaseTokenizer(ABC):
    """Abstract base class for language-specific tokenizers."""

    STATE_DEFAULT = 0
    STATE_STRING = 1
    STATE_COMMENT = 2
    STATE_MULTILINE_STRING = 3
    STATE_BLOCK_COMMENT = 4

    @abstractmethod
    def tokenize_line(
        self, line: str, state_stack: StateStack
    ) -> TokenizeResult:
        """Tokenize a line of text.

        Args:
            line: The line of text to tokenize.
            state_stack: The current state stack from previous lines.

        Returns:
            TokenizeResult containing tokens and the final state stack.
        """
        pass

    @abstractmethod
    def get_lang_id(self) -> str:
        """Return the language identifier (e.g., 'python', 'html')."""
        pass

    def _make_token(self, start: int, length: int, style_id: StyleId) -> Token:
        """Factory method for creating Token instances."""
        return Token(start=start, length=length, style_id=style_id)

    def _push_state(
        self,
        stack: StateStack,
        lang_id: str,
        sub_state: int = 0,
        end_condition: str | None = None,
    ) -> StateStack:
        """Return a new stack with a frame pushed."""
        frame = StackFrame(
            lang_id=lang_id, sub_state=sub_state, end_condition=end_condition
        )
        return stack + (frame,)

    def _pop_state(self, stack: StateStack) -> StateStack:
        """Return a new stack with the top frame popped."""
        if not stack:
            return ()
        return stack[:-1]

    def _current_frame(self, stack: StateStack) -> StackFrame | None:
        """Return the top frame or None if the stack is empty."""
        if not stack:
            return None
        return stack[-1]

    def _default_frame(self) -> StackFrame:
        """Return the default stack frame for this language."""
        return StackFrame(
            lang_id=self.get_lang_id(), sub_state=0, end_condition=None
        )
