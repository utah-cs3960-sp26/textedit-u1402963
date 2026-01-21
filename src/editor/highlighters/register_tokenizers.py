"""Registration module for all tokenizers."""

from editor.highlighters.core.registry import HighlightRegistry
from editor.highlighters.tokenizers import (
    PlainTokenizer,
    JsonTokenizer,
    HtmlTokenizer,
    MarkdownTokenizer,
    PythonTokenizer,
    CTokenizer,
    CppTokenizer,
    JavaTokenizer,
    JavaScriptTokenizer,
)


def register_all_tokenizers():
    """Register all tokenizers with the HighlightRegistry."""
    registry = HighlightRegistry.instance()

    registry.register("plain", PlainTokenizer(), [".txt"])
    registry.register("python", PythonTokenizer(), [".py", ".pyw"])
    registry.register("c", CTokenizer(), [".c", ".h"])
    registry.register("cpp", CppTokenizer(), [".cpp", ".hpp", ".cc", ".cxx", ".hxx"])
    registry.register("java", JavaTokenizer(), [".java"])
    registry.register("html", HtmlTokenizer(), [".html", ".htm", ".xml"])
    registry.register("json", JsonTokenizer(), [".json"])
    registry.register("markdown", MarkdownTokenizer(), [".md", ".markdown"])
    registry.register("javascript", JavaScriptTokenizer(), [".js", ".jsx"])


# Auto-register on import
register_all_tokenizers()
