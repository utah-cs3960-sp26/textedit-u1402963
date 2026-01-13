import re
from editor.highlighters.base import BaseHighlighter
from PyQt6.QtGui import QTextCharFormat, QColor


class CHighlighter(BaseHighlighter):
    KEYWORDS = [
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "inline", "int", "long", "register", "restrict", "return", "short",
        "signed", "sizeof", "static", "struct", "switch", "typedef", "union",
        "unsigned", "void", "volatile", "while", "_Bool", "_Complex", "_Imaginary",
        "bool", "true", "false", "NULL",
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
