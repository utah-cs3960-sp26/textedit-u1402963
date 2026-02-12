import pytest

from PyQt6.QtGui import QTextDocument

from editor.highlighters.core.registry import HighlightRegistry
from editor.highlighters.document_highlighter import DocumentHighlighter
from editor.highlighters.tokenizers.plain_tokenizer import PlainTokenizer


@pytest.fixture
def registry():
    original = HighlightRegistry._instance
    HighlightRegistry._instance = HighlightRegistry()
    yield HighlightRegistry._instance
    HighlightRegistry._instance = original


def test_document_highlighter_falls_back_to_default_tokenizer(registry):
    doc = QTextDocument()
    highlighter = DocumentHighlighter(doc, "unknown")
    assert isinstance(highlighter._tokenizer, PlainTokenizer)


def test_document_highlighter_set_language_noop_when_same(registry):
    doc = QTextDocument()
    highlighter = DocumentHighlighter(doc, "plain")
    tokenizer = highlighter._tokenizer

    highlighter.set_language("plain")

    assert highlighter._tokenizer is tokenizer


def test_document_highlighter_set_language_switches(registry):
    doc = QTextDocument()
    highlighter = DocumentHighlighter(doc, "plain")

    highlighter.set_language("python")

    assert highlighter._lang_id == "python"
