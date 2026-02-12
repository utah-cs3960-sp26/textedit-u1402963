import pytest

from editor.highlighters.core.base_tokenizer import BaseTokenizer
from editor.highlighters.core.types import TokenizeResult


class DummyTokenizer(BaseTokenizer):
    def get_lang_id(self) -> str:
        return "dummy"

    def tokenize_line(self, line: str, state_stack):
        return TokenizeResult(tokens=[], final_stack=state_stack)


@pytest.fixture
def tokenizer():
    return DummyTokenizer()


def test_make_token(tokenizer):
    token = tokenizer._make_token(1, 2, 3)
    assert token.start == 1
    assert token.length == 2
    assert token.style_id == 3


def test_push_and_pop_state(tokenizer):
    stack = ()
    stack = tokenizer._push_state(stack, "dummy", sub_state=7, end_condition="end")
    assert len(stack) == 1
    assert stack[-1].lang_id == "dummy"
    assert stack[-1].sub_state == 7
    assert stack[-1].end_condition == "end"

    stack = tokenizer._pop_state(stack)
    assert stack == ()


def test_pop_state_empty(tokenizer):
    assert tokenizer._pop_state(()) == ()


def test_current_frame(tokenizer):
    assert tokenizer._current_frame(()) is None
    stack = tokenizer._push_state((), "dummy", sub_state=1, end_condition=None)
    assert tokenizer._current_frame(stack) == stack[-1]


def test_default_frame(tokenizer):
    frame = tokenizer._default_frame()
    assert frame.lang_id == "dummy"
    assert frame.sub_state == 0
    assert frame.end_condition is None


def test_base_tokenizer_pass_methods(tokenizer):
    """Calling abstract base implementations should execute pass lines."""
    assert BaseTokenizer.get_lang_id(tokenizer) is None
    assert BaseTokenizer.tokenize_line(tokenizer, "", ()) is None
