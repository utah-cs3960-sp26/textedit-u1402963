import re
from editor.highlighters.base import BaseHighlighter
from PyQt6.QtGui import QTextCharFormat, QColor


class PythonHighlighter(BaseHighlighter):
    KEYWORDS = [
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
        "while", "with", "yield",
    ]

    IN_TRIPLE_DOUBLE = 1
    IN_TRIPLE_SINGLE = 2

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"#.*$", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"\b\d+\.?\d*\b", "magenta")

        self._triple_string_format = QTextCharFormat()
        self._triple_string_format.setForeground(QColor("orange"))

        self._triple_double = re.compile(r'"""')
        self._triple_single = re.compile(r"'''")

    def highlightBlock(self, text: str):
        super().highlightBlock(text)
        self._highlight_multiline_strings(text)

    def _highlight_multiline_strings(self, text: str):
        self.setCurrentBlockState(0)

        prev_state = self.previousBlockState()

        if prev_state == self.IN_TRIPLE_DOUBLE:
            self._continue_multiline(text, self._triple_double, self.IN_TRIPLE_DOUBLE, 0)
        elif prev_state == self.IN_TRIPLE_SINGLE:
            self._continue_multiline(text, self._triple_single, self.IN_TRIPLE_SINGLE, 0)
        else:
            self._find_multiline_starts(text)

    def _continue_multiline(self, text: str, delimiter: re.Pattern, state: int, start: int):
        match = delimiter.search(text, start)
        if match:
            length = match.end() - start
            self.setFormat(start, length, self._triple_string_format)
            self._find_multiline_starts(text, match.end())
        else:
            self.setCurrentBlockState(state)
            self.setFormat(start, len(text) - start, self._triple_string_format)

    def _find_multiline_starts(self, text: str, start: int = 0):
        double_match = self._triple_double.search(text, start)
        single_match = self._triple_single.search(text, start)

        if double_match is None and single_match is None:
            return

        if double_match and (single_match is None or double_match.start() < single_match.start()):
            self._handle_start(text, double_match, self._triple_double, self.IN_TRIPLE_DOUBLE)
        elif single_match:
            self._handle_start(text, single_match, self._triple_single, self.IN_TRIPLE_SINGLE)

    def _handle_start(self, text: str, start_match, delimiter: re.Pattern, state: int):
        end_match = delimiter.search(text, start_match.end())
        if end_match:
            length = end_match.end() - start_match.start()
            self.setFormat(start_match.start(), length, self._triple_string_format)
            self._find_multiline_starts(text, end_match.end())
        else:
            self.setCurrentBlockState(state)
            self.setFormat(start_match.start(), len(text) - start_match.start(), self._triple_string_format)
