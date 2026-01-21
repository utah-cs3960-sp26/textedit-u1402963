"""Style registry for managing QTextCharFormat objects."""

from enum import IntEnum
from typing import Dict

from PyQt6.QtGui import QColor, QFont, QTextCharFormat


class StyleId(IntEnum):
    """Enumeration of syntax highlighting styles."""

    KEYWORD = 0
    STRING = 1
    COMMENT = 2
    NUMBER = 3
    OPERATOR = 4
    TAG = 5
    ATTR_NAME = 6
    ATTR_VALUE = 7
    PUNCTUATION = 8
    IDENTIFIER = 9
    EMBEDDED = 10
    PLAIN = 11


class StyleRegistry:
    """Singleton registry for syntax highlighting formats.

    Maps StyleId to QTextCharFormat with sensible dark-theme colors.
    """

    _instance: "StyleRegistry | None" = None

    def __init__(self) -> None:
        """Initialize the registry with pre-created formats."""
        self._formats: Dict[StyleId, QTextCharFormat] = {}
        self._create_formats()

    @classmethod
    def instance(cls) -> "StyleRegistry":
        """Get the singleton instance of StyleRegistry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _create_formats(self) -> None:
        """Create all QTextCharFormat objects with dark theme colors."""
        # KEYWORD: #569CD6 (blue), bold
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#569CD6"))
        keyword_fmt.setFontWeight(QFont.Weight.Bold)
        self._formats[StyleId.KEYWORD] = keyword_fmt

        # STRING: #CE9178 (orange)
        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("#CE9178"))
        self._formats[StyleId.STRING] = string_fmt

        # COMMENT: #6A9955 (green), italic
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6A9955"))
        comment_fmt.setFontItalic(True)
        self._formats[StyleId.COMMENT] = comment_fmt

        # NUMBER: #B5CEA8 (light green)
        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#B5CEA8"))
        self._formats[StyleId.NUMBER] = number_fmt

        # OPERATOR: #D4D4D4 (white)
        operator_fmt = QTextCharFormat()
        operator_fmt.setForeground(QColor("#D4D4D4"))
        self._formats[StyleId.OPERATOR] = operator_fmt

        # TAG: #569CD6 (blue), bold
        tag_fmt = QTextCharFormat()
        tag_fmt.setForeground(QColor("#569CD6"))
        tag_fmt.setFontWeight(QFont.Weight.Bold)
        self._formats[StyleId.TAG] = tag_fmt

        # ATTR_NAME: #9CDCFE (light blue)
        attr_name_fmt = QTextCharFormat()
        attr_name_fmt.setForeground(QColor("#9CDCFE"))
        self._formats[StyleId.ATTR_NAME] = attr_name_fmt

        # ATTR_VALUE: #CE9178 (orange)
        attr_value_fmt = QTextCharFormat()
        attr_value_fmt.setForeground(QColor("#CE9178"))
        self._formats[StyleId.ATTR_VALUE] = attr_value_fmt

        # PUNCTUATION: #D4D4D4 (white)
        punctuation_fmt = QTextCharFormat()
        punctuation_fmt.setForeground(QColor("#D4D4D4"))
        self._formats[StyleId.PUNCTUATION] = punctuation_fmt

        # IDENTIFIER: #DCDCAA (yellow)
        identifier_fmt = QTextCharFormat()
        identifier_fmt.setForeground(QColor("#DCDCAA"))
        self._formats[StyleId.IDENTIFIER] = identifier_fmt

        # EMBEDDED: #C586C0 (purple)
        embedded_fmt = QTextCharFormat()
        embedded_fmt.setForeground(QColor("#C586C0"))
        self._formats[StyleId.EMBEDDED] = embedded_fmt

        # PLAIN: #D4D4D4 (white)
        plain_fmt = QTextCharFormat()
        plain_fmt.setForeground(QColor("#D4D4D4"))
        self._formats[StyleId.PLAIN] = plain_fmt

    def get_format(self, style_id: StyleId) -> QTextCharFormat:
        """Get the QTextCharFormat for a given style.

        Args:
            style_id: The style identifier.

        Returns:
            The corresponding QTextCharFormat.
        """
        return self._formats[style_id]
