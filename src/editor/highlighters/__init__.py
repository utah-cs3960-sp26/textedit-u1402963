from editor.highlighters.base import BaseHighlighter
from editor.highlighters.python_hl import PythonHighlighter
from editor.highlighters.c_hl import CHighlighter
from editor.highlighters.cpp_hl import CppHighlighter
from editor.highlighters.java_hl import JavaHighlighter
from editor.highlighters.html_hl import HtmlHighlighter
from editor.highlighters.json_hl import JsonHighlighter
from editor.highlighters.markdown_hl import MarkdownHighlighter
from editor.highlighters.plain_hl import PlainTextHighlighter
from editor.highlighters.detector import LanguageDetector

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
