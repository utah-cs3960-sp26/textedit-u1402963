import pytest

from PyQt6.QtGui import QTextDocument

from editor.highlighters.core.registry import HighlightRegistry
from editor.highlighters.document_highlighter import DocumentHighlighter


@pytest.fixture
def registry():
    original = HighlightRegistry._instance
    HighlightRegistry._instance = HighlightRegistry()
    yield HighlightRegistry._instance
    HighlightRegistry._instance = original


def test_document_highlighter_ignores_unknown_style(registry):
    doc = QTextDocument()
    highlighter = DocumentHighlighter(doc, "plain")

    class DummyResult:
        def __init__(self):
            self.tokens = [type("Token", (), {"start": 0, "length": 1, "style_id": 999})()]
            self.final_stack = ()

    class DummyTokenizer:
        def tokenize_line(self, text, stack):
            return DummyResult()

    highlighter._tokenizer = DummyTokenizer()
    highlighter.highlightBlock("x")


def test_document_highlighter_uses_embedded_tokenizer(registry):
    doc = QTextDocument()
    highlighter = DocumentHighlighter(doc, "html")

    class DummyTokenizer:
        def __init__(self):
            self.called = False

        def tokenize_line(self, text, stack):
            self.called = True
            return type("Result", (), {"tokens": [], "final_stack": stack})()

    embedded = DummyTokenizer()
    registry.register("javascript", embedded, [".js"])

    from editor.highlighters.core.types import StackFrame

    stack = (StackFrame(lang_id="javascript", sub_state=0, end_condition=None),)
    highlighter._stack_pool.intern(stack)
    highlighter.setCurrentBlockState(-1)
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(highlighter._stack_pool, "get", lambda _state_id: stack)
        highlighter.highlightBlock("console.log(1)")

    assert embedded.called is True


def test_document_highlighter_returns_default_tokenizer(registry):
    doc = QTextDocument()
    highlighter = DocumentHighlighter(doc, "plain")

    tokenizer = highlighter._get_active_tokenizer(())

    assert tokenizer is highlighter._tokenizer
