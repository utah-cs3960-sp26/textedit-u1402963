from abc import ABC, abstractmethod

from editor.highlighters.core.types import StateStack, TokenizeResult


class BaseTokenizer(ABC):
    @abstractmethod
    def get_lang_id(self) -> str:
        pass

    @abstractmethod
    def tokenize_line(self, line: str, state_stack: StateStack) -> TokenizeResult:
        pass
