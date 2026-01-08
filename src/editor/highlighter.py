import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


class BaseHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self._highlighting_rules = []

    def add_keywords(self, keywords, color, bold=True):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        pattern = r"\b(" + "|".join(keywords) + r")\b"
        self._highlighting_rules.append((re.compile(pattern), fmt))

    def add_pattern(self, pattern, color, bold=False, italic=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        self._highlighting_rules.append((re.compile(pattern), fmt))

    def highlightBlock(self, text: str):
        for pattern, fmt in self._highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class PythonHighlighter(BaseHighlighter):
    KEYWORDS = [
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
        "while", "with", "yield",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"#.*$", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"\b\d+\.?\d*\b", "magenta")


class CHighlighter(BaseHighlighter):
    KEYWORDS = [
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "inline", "int", "long", "register", "restrict", "return", "short",
        "signed", "sizeof", "static", "struct", "switch", "typedef", "union",
        "unsigned", "void", "volatile", "while", "_Bool", "_Complex", "_Imaginary",
        "bool", "true", "false", "NULL",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"//.*$", "gray", italic=True)
        self.add_pattern(r"/\*.*?\*/", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"#\s*\w+", "magenta")
        self.add_pattern(r"\b\d+\.?\d*[fFlLuU]*\b", "magenta")


class CppHighlighter(BaseHighlighter):
    KEYWORDS = [
        "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
        "bool", "break", "case", "catch", "char", "char8_t", "char16_t", "char32_t",
        "class", "compl", "concept", "const", "consteval", "constexpr", "constinit",
        "const_cast", "continue", "co_await", "co_return", "co_yield", "decltype",
        "default", "delete", "do", "double", "dynamic_cast", "else", "enum",
        "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
        "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept",
        "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private", "protected",
        "public", "register", "reinterpret_cast", "requires", "return", "short",
        "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
        "switch", "template", "this", "thread_local", "throw", "true", "try",
        "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual",
        "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"//.*$", "gray", italic=True)
        self.add_pattern(r"/\*.*?\*/", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"#\s*\w+", "magenta")
        self.add_pattern(r"\b\d+\.?\d*[fFlLuU]*\b", "magenta")


class JavaHighlighter(BaseHighlighter):
    KEYWORDS = [
        "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
        "class", "const", "continue", "default", "do", "double", "else", "enum",
        "extends", "final", "finally", "float", "for", "goto", "if", "implements",
        "import", "instanceof", "int", "interface", "long", "native", "new",
        "package", "private", "protected", "public", "return", "short", "static",
        "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
        "transient", "try", "void", "volatile", "while", "true", "false", "null",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"//.*$", "gray", italic=True)
        self.add_pattern(r"/\*.*?\*/", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"@\w+", "yellow")
        self.add_pattern(r"\b\d+\.?\d*[fFdDlL]*\b", "magenta")


class HtmlHighlighter(BaseHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.add_pattern(r"</?[\w-]+", "cyan", bold=True)
        self.add_pattern(r"/?>", "cyan", bold=True)
        self.add_pattern(r"\b[\w-]+(?==)", "yellow")
        self.add_pattern(r'"[^"]*"', "orange")
        self.add_pattern(r"'[^']*'", "orange")
        self.add_pattern(r"<!--.*?-->", "gray", italic=True)
        self.add_pattern(r"&\w+;", "magenta")


class JsonHighlighter(BaseHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"\s*:', "cyan")
        self.add_pattern(r':\s*"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"\b(true|false|null)\b", "magenta", bold=True)
        self.add_pattern(r"\b-?\d+\.?\d*([eE][+-]?\d+)?\b", "magenta")


class MarkdownHighlighter(BaseHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.add_pattern(r"^#{1,6}\s.*$", "cyan", bold=True)
        self.add_pattern(r"\*\*[^*]+\*\*", "white", bold=True)
        self.add_pattern(r"__[^_]+__", "white", bold=True)
        self.add_pattern(r"\*[^*]+\*", "white", italic=True)
        self.add_pattern(r"_[^_]+_", "white", italic=True)
        self.add_pattern(r"`[^`]+`", "orange")
        self.add_pattern(r"^\s*[-*+]\s", "yellow", bold=True)
        self.add_pattern(r"^\s*\d+\.\s", "yellow", bold=True)
        self.add_pattern(r"\[([^\]]+)\]\([^)]+\)", "cyan")
        self.add_pattern(r"^>.*$", "gray", italic=True)


class PlainTextHighlighter(BaseHighlighter):
    def __init__(self, document):
        super().__init__(document)


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
