import pytest

from PyQt6.QtGui import QColor, QFont

from editor.highlighters.core.style_registry import StyleId, StyleRegistry


@pytest.fixture
def registry():
    original = StyleRegistry._instance
    StyleRegistry._instance = StyleRegistry()
    yield StyleRegistry._instance
    StyleRegistry._instance = original


def test_registry_returns_format(registry):
    fmt = registry.get_format(StyleId.KEYWORD)
    assert fmt.fontWeight() == QFont.Weight.Bold


def test_registry_set_color_updates_format(registry):
    registry.set_color(StyleId.STRING, "#123456")
    assert registry.get_color(StyleId.STRING) == "#123456"


def test_registry_set_color_ignores_unknown(registry):
    registry.set_color(StyleId.KEYWORD, "#abcdef")
    assert registry.get_color(StyleId.COMMENT) == StyleRegistry.DEFAULT_COLORS[StyleId.COMMENT].lower()

    registry.set_color(StyleId.STRING, "#112233")
    assert registry.get_color(StyleId.STRING) == "#112233"

    registry._formats.pop(StyleId.IDENTIFIER)
    registry.set_color(StyleId.IDENTIFIER, "#ff0000")
    assert StyleId.IDENTIFIER not in registry._formats


def test_registry_reset_colors_restores_defaults(registry):
    registry.set_color(StyleId.KEYWORD, QColor("#101010"))
    registry.reset_colors()
    assert registry.get_color(StyleId.KEYWORD) == StyleRegistry.DEFAULT_COLORS[StyleId.KEYWORD].lower()
