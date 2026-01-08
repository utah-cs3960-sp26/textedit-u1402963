import re

from editor.highlighters.python_hl import PythonHighlighter
from editor.highlighters.c_hl import CHighlighter
from editor.highlighters.cpp_hl import CppHighlighter
from editor.highlighters.java_hl import JavaHighlighter
from editor.highlighters.html_hl import HtmlHighlighter
from editor.highlighters.json_hl import JsonHighlighter
from editor.highlighters.markdown_hl import MarkdownHighlighter
from editor.highlighters.plain_hl import PlainTextHighlighter


class LanguageDetector:
    EXTENSION_MAP = {
        ".py": "python",
        ".pyw": "python",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hxx": "cpp",
        ".java": "java",
        ".html": "html",
        ".htm": "html",
        ".xml": "html",
        ".json": "json",
        ".md": "markdown",
        ".markdown": "markdown",
        ".txt": "plain",
    }

    LANGUAGE_TO_EXTENSION = {
        "python": ".py",
        "c": ".c",
        "cpp": ".cpp",
        "java": ".java",
        "html": ".html",
        "json": ".json",
        "markdown": ".md",
        "plain": ".txt",
    }

    LANGUAGE_TO_FILTER = {
        "python": "Python (*.py)",
        "c": "C Source (*.c)",
        "cpp": "C++ Source (*.cpp)",
        "java": "Java (*.java)",
        "html": "HTML (*.html)",
        "json": "JSON (*.json)",
        "markdown": "Markdown (*.md)",
        "plain": "Text (*.txt)",
    }

    HIGHLIGHTER_MAP = {
        "python": PythonHighlighter,
        "c": CHighlighter,
        "cpp": CppHighlighter,
        "java": JavaHighlighter,
        "html": HtmlHighlighter,
        "json": JsonHighlighter,
        "markdown": MarkdownHighlighter,
        "plain": PlainTextHighlighter,
    }

    @classmethod
    def detect_from_extension(cls, file_path: str) -> str:
        if not file_path:
            return ""
        file_path = file_path.lower()
        for ext, lang in cls.EXTENSION_MAP.items():
            if file_path.endswith(ext):
                return lang
        return ""

    @classmethod
    def detect_from_content(cls, content: str) -> str:
        lines = content.split("\n")[:50]
        text = "\n".join(lines)

        if re.search(r"^\s*(import|from)\s+\w+", text, re.MULTILINE):
            if re.search(r"^\s*def\s+\w+\s*\(", text, re.MULTILINE):
                return "python"
            if re.search(r"^\s*class\s+\w+.*:", text, re.MULTILINE):
                return "python"

        if re.search(r"^\s*#include\s*[<\"]", text, re.MULTILINE):
            if re.search(r"\b(class|namespace|template)\b", text):
                return "cpp"
            return "c"

        if re.search(r"^\s*(public|private|protected)\s+(class|interface)\s+\w+", text, re.MULTILINE):
            return "java"
        if re.search(r"^\s*package\s+[\w.]+;", text, re.MULTILINE):
            return "java"

        if re.search(r"^\s*<!DOCTYPE\s+html", text, re.MULTILINE | re.IGNORECASE):
            return "html"
        if re.search(r"<html[\s>]", text, re.IGNORECASE):
            return "html"

        text_stripped = text.strip()
        if text_stripped.startswith("{") or text_stripped.startswith("["):
            if re.search(r'"\w+"\s*:', text):
                return "json"

        if re.search(r"^#{1,6}\s", text, re.MULTILINE):
            return "markdown"
        if re.search(r"^\s*[-*]\s", text, re.MULTILINE) and re.search(r"\[.+\]\(.+\)", text):
            return "markdown"

        return "plain"

    @classmethod
    def detect(cls, file_path: str = "", content: str = "") -> str:
        lang = cls.detect_from_extension(file_path)
        if lang:
            return lang
        return cls.detect_from_content(content)

    @classmethod
    def get_highlighter(cls, document, file_path: str = "", content: str = ""):
        lang = cls.detect(file_path, content)
        highlighter_class = cls.HIGHLIGHTER_MAP.get(lang, PlainTextHighlighter)
        return highlighter_class(document)

    @classmethod
    def suggest_extension(cls, file_path: str, content: str) -> str:
        if cls.detect_from_extension(file_path):
            return file_path
        lang = cls.detect_from_content(content)
        ext = cls.LANGUAGE_TO_EXTENSION.get(lang, ".txt")
        return file_path + ext

    @classmethod
    def get_save_filter(cls, file_path: str = "", content: str = "") -> str:
        lang = cls.detect(file_path, content)
        return cls.LANGUAGE_TO_FILTER.get(lang, "All Files (*)")
