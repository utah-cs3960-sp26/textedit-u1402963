import re
from editor.highlighters.base import BaseHighlighter
from PyQt6.QtGui import QTextCharFormat, QColor


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

    IN_BLOCK_COMMENT = 1

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"//.*$", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"#\s*\w+", "magenta")
        self.add_pattern(r"\b\d+\.?\d*[fFlLuU]*\b", "magenta")

        self._block_comment_format = QTextCharFormat()
        self._block_comment_format.setForeground(QColor("gray"))
        self._block_comment_format.setFontItalic(True)

        self._block_comment_start = re.compile(r"/\*")
        self._block_comment_end = re.compile(r"\*/")

    def highlightBlock(self, text: str):
        super().highlightBlock(text)
        self._highlight_multiline_comments(text)

    def _highlight_multiline_comments(self, text: str):
        self.setCurrentBlockState(0)

        start_index = 0
        if self.previousBlockState() != self.IN_BLOCK_COMMENT:
            match = self._block_comment_start.search(text)
            start_index = match.start() if match else -1
        else:
            start_index = 0

        while start_index >= 0:
            end_match = self._block_comment_end.search(text, start_index)
            if end_match:
                comment_length = end_match.end() - start_index
                self.setFormat(start_index, comment_length, self._block_comment_format)
                match = self._block_comment_start.search(text, end_match.end())
                start_index = match.start() if match else -1
            else:
                self.setCurrentBlockState(self.IN_BLOCK_COMMENT)
                self.setFormat(start_index, len(text) - start_index, self._block_comment_format)
                break
