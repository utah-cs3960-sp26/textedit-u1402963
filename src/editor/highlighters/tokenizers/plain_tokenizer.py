from editor.highlighters.core.types import Token, StateStack, TokenizeResult, StyleId
from editor.highlighters.tokenizers.base_tokenizer import BaseTokenizer


class PlainTokenizer(BaseTokenizer):
    def get_lang_id(self) -> str:
        return "plain"

    def tokenize_line(self, line: str, state_stack: StateStack) -> TokenizeResult:
        if line:
            tokens = [Token(start=0, length=len(line), style_id=StyleId.PLAIN)]
        else:
            tokens = []
        return TokenizeResult(tokens=tokens, final_stack=state_stack)
