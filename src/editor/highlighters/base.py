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
