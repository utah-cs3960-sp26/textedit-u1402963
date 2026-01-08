# Backward compatibility - re-export from new highlighters package
from editor.highlighters import (
    BaseHighlighter,
    PythonHighlighter,
    CHighlighter,
    CppHighlighter,
    JavaHighlighter,
    HtmlHighlighter,
    JsonHighlighter,
    MarkdownHighlighter,
    PlainTextHighlighter,
    LanguageDetector,
)

__all__ = [
    "BaseHighlighter",
    "PythonHighlighter",
    "CHighlighter",
    "CppHighlighter",
    "JavaHighlighter",
    "HtmlHighlighter",
    "JsonHighlighter",
    "MarkdownHighlighter",
    "PlainTextHighlighter",
    "LanguageDetector",
]
