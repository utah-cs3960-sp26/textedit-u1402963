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

    DEFAULT_COLORS = {
        StyleId.KEYWORD: "#569CD6",
        StyleId.STRING: "#CE9178",
        StyleId.COMMENT: "#6A9955",
        StyleId.NUMBER: "#B5CEA8",
        StyleId.OPERATOR: "#D4D4D4",
        StyleId.TAG: "#569CD6",
        StyleId.ATTR_NAME: "#9CDCFE",
        StyleId.ATTR_VALUE: "#CE9178",
        StyleId.PUNCTUATION: "#D4D4D4",
        StyleId.IDENTIFIER: "#DCDCAA",
        StyleId.EMBEDDED: "#C586C0",
        StyleId.PLAIN: "#D4D4D4",
    }

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
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.KEYWORD]))
        keyword_fmt.setFontWeight(QFont.Weight.Bold)
        self._formats[StyleId.KEYWORD] = keyword_fmt

        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.STRING]))
        self._formats[StyleId.STRING] = string_fmt

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.COMMENT]))
        comment_fmt.setFontItalic(True)
        self._formats[StyleId.COMMENT] = comment_fmt

        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.NUMBER]))
        self._formats[StyleId.NUMBER] = number_fmt

        operator_fmt = QTextCharFormat()
        operator_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.OPERATOR]))
        self._formats[StyleId.OPERATOR] = operator_fmt

        tag_fmt = QTextCharFormat()
        tag_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.TAG]))
        tag_fmt.setFontWeight(QFont.Weight.Bold)
        self._formats[StyleId.TAG] = tag_fmt

        attr_name_fmt = QTextCharFormat()
        attr_name_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.ATTR_NAME]))
        self._formats[StyleId.ATTR_NAME] = attr_name_fmt

        attr_value_fmt = QTextCharFormat()
        attr_value_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.ATTR_VALUE]))
        self._formats[StyleId.ATTR_VALUE] = attr_value_fmt

        punctuation_fmt = QTextCharFormat()
        punctuation_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.PUNCTUATION]))
        self._formats[StyleId.PUNCTUATION] = punctuation_fmt

        identifier_fmt = QTextCharFormat()
        identifier_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.IDENTIFIER]))
        self._formats[StyleId.IDENTIFIER] = identifier_fmt

        embedded_fmt = QTextCharFormat()
        embedded_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.EMBEDDED]))
        self._formats[StyleId.EMBEDDED] = embedded_fmt

        plain_fmt = QTextCharFormat()
        plain_fmt.setForeground(QColor(self.DEFAULT_COLORS[StyleId.PLAIN]))
        self._formats[StyleId.PLAIN] = plain_fmt

    def get_format(self, style_id: StyleId) -> QTextCharFormat:
        """Get the QTextCharFormat for a given style.

        Args:
            style_id: The style identifier.

        Returns:
            The corresponding QTextCharFormat.
        """
        return self._formats[style_id]

    def set_color(self, style_id: StyleId, color: QColor | str) -> None:
        """Override the foreground color for a style."""
        if style_id not in self._formats:
            return
        fmt = self._formats[style_id]
        fmt.setForeground(QColor(color))

    def get_color(self, style_id: StyleId) -> str:
        """Return the current color for a style as a hex string."""
        return self._formats[style_id].foreground().color().name()

    def reset_colors(self) -> None:
        """Reset all colors to defaults."""
        for style_id, color in self.DEFAULT_COLORS.items():
            self.set_color(style_id, color)
