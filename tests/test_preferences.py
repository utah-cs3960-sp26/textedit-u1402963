import pytest
from unittest.mock import patch

from PyQt6.QtGui import QColor, QFont, QKeySequence
from PyQt6.QtWidgets import QApplication, QPushButton

from editor.highlighters.core.style_registry import StyleId, StyleRegistry
from editor.preferences_dialog import PreferencesDialog
from editor.settings import EditorSettings
from editor.window import MainWindow


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture
def window(app):
    win = MainWindow()
    yield win
    win.close()


def test_apply_settings_updates_ui_and_shortcuts(window):
    palette = window.text_edit.palette()
    defaults = EditorSettings.defaults(
        editor_background=palette.color(palette.ColorRole.Base).name(),
        editor_foreground=palette.color(palette.ColorRole.Text).name(),
        line_number_background=window.text_edit.DEFAULT_LINE_NUMBER_BG.name(),
        line_number_foreground=window.text_edit.DEFAULT_LINE_NUMBER_FG.name(),
        font_family=window.text_edit.font().family(),
        font_size=window.text_edit.font().pointSize(),
    )

    settings = EditorSettings(
        font_family=defaults.font_family,
        font_size=defaults.font_size + 1,
        editor_background="#112233",
        editor_foreground="#ddeeff",
        line_number_background="#445566",
        line_number_foreground="#778899",
        syntax_colors={**defaults.syntax_colors, "keyword": "#123456"},
        shortcuts={**defaults.shortcuts, "file_open": "Ctrl+Alt+O", "view_toggle_sidebar": "Alt+B"},
    )

    window._apply_settings(settings)

    assert window.text_edit.font().family() == settings.font_family
    assert window.text_edit.font().pointSize() == settings.font_size

    updated_palette = window.text_edit.palette()
    assert updated_palette.color(updated_palette.ColorRole.Base).name() == "#112233"
    assert updated_palette.color(updated_palette.ColorRole.Text).name() == "#ddeeff"

    assert window.text_edit._line_number_bg.name() == "#445566"
    assert window.text_edit._line_number_fg.name() == "#778899"

    registry = StyleRegistry.instance()
    assert registry.get_color(StyleId.KEYWORD) == "#123456"

    assert window._actions["file_open"].shortcut().toString() == "Ctrl+Alt+O"
    assert window._shortcuts["view_toggle_sidebar"].key().toString() == "Alt+B"

    html = window._build_shortcuts_html()
    assert "Ctrl+Alt+O" in html


def test_preferences_dialog_collects_updates(app):
    defaults = EditorSettings.defaults(
        editor_background="#202020",
        editor_foreground="#f0f0f0",
        line_number_background="#303030",
        line_number_foreground="#a0a0a0",
    )
    dialog = PreferencesDialog(defaults, defaults)

    dialog._font_size.setValue(defaults.font_size + 2)
    dialog._font_family.setCurrentFont(QFont(defaults.font_family))

    dialog._color_buttons["editor_background"].set_color(QColor("#010203"))
    dialog._color_buttons["keyword"].set_color(QColor("#0a0b0c"))

    dialog._shortcut_edits["file_open"].setKeySequence(QKeySequence("Ctrl+Alt+O"))

    updated = dialog.get_settings()
    assert updated.font_size == defaults.font_size + 2
    assert updated.editor_background == "#010203"
    assert updated.syntax_colors["keyword"] == "#0a0b0c"
    assert updated.shortcuts["file_open"] == "Ctrl+Alt+O"


def test_preferences_reset_to_defaults_button(app):
    defaults = EditorSettings.defaults(
        editor_background="#202020",
        editor_foreground="#f0f0f0",
        line_number_background="#303030",
        line_number_foreground="#a0a0a0",
    )
    modified = EditorSettings(
        font_family=defaults.font_family,
        font_size=defaults.font_size + 5,
        editor_background="#010203",
        editor_foreground="#040506",
        line_number_background="#070809",
        line_number_foreground="#0a0b0c",
        syntax_colors={**defaults.syntax_colors, "keyword": "#123456"},
        shortcuts={**defaults.shortcuts, "file_open": "Ctrl+Alt+O"},
    )
    dialog = PreferencesDialog(modified, defaults)

    reset_button = None
    for button in dialog.findChildren(QPushButton):
        if button.text() == "Reset to Defaults":
            reset_button = button
            break
    assert reset_button is not None

    dialog._tabs.setCurrentIndex(0)
    reset_button.click()

    assert dialog._font_size.value() == defaults.font_size
    assert dialog._color_buttons["editor_background"].color() == modified.editor_background
    assert dialog._shortcut_edits["file_open"].keySequence().toString() == "Ctrl+Alt+O"

    dialog._tabs.setCurrentIndex(1)
    reset_button.click()
    assert dialog._color_buttons["editor_background"].color() == defaults.editor_background
    assert dialog._color_buttons["line_number_background"].color() == defaults.line_number_background
    assert (
        dialog._color_buttons["keyword"].color().lower()
        == defaults.syntax_colors["keyword"].lower()
    )
    assert dialog._shortcut_edits["file_open"].keySequence().toString() == "Ctrl+Alt+O"

    dialog._tabs.setCurrentIndex(2)
    reset_button.click()
    assert dialog._shortcut_edits["file_open"].keySequence().toString() == defaults.shortcuts["file_open"]


def test_color_button_choose_color_applies_selection(app):
    """ColorButton should apply QColorDialog selection when valid."""
    from PyQt6.QtGui import QColor

    defaults = EditorSettings.defaults(
        editor_background="#202020",
        editor_foreground="#f0f0f0",
        line_number_background="#303030",
        line_number_foreground="#a0a0a0",
    )
    dialog = PreferencesDialog(defaults, defaults)
    button = dialog._color_buttons["editor_background"]

    with patch("editor.preferences_dialog.QColorDialog.getColor") as mock_dialog:
        mock_dialog.return_value = QColor("#112233")
        button._choose_color()

    assert button.color() == "#112233"


def test_settings_save_persists_all_fields(app):
    """EditorSettings.save() should write all fields to QSettings store."""
    from PyQt6.QtCore import QSettings
    defaults = EditorSettings.defaults(
        editor_background="#111111",
        editor_foreground="#eeeeee", 
        line_number_background="#222222",
        line_number_foreground="#dddddd",
    )
    
    store = QSettings("TestOrg", "TestApp_save")
    defaults.save(store)
    
    assert store.value("font/family") == defaults.font_family
    assert int(store.value("font/size")) == defaults.font_size
    assert store.value("colors/editor_background") == "#111111"
    assert store.value("colors/editor_foreground") == "#eeeeee"
    assert store.value("colors/line_number_background") == "#222222"
    assert store.value("colors/line_number_foreground") == "#dddddd"
    
    for key, color in defaults.syntax_colors.items():
        assert store.value(f"colors/syntax/{key}") == color
    
    for key, shortcut in defaults.shortcuts.items():
        assert store.value(f"shortcuts/{key}") == shortcut
    
    store.clear()


def test_settings_save_then_load_roundtrip(app):
    """Saving then loading should produce identical settings."""
    from PyQt6.QtCore import QSettings
    original = EditorSettings.defaults(
        editor_background="#aabbcc",
        editor_foreground="#ddeeff",
        line_number_background="#112233",
        line_number_foreground="#445566",
    )
    original.font_size = 18
    original.syntax_colors["keyword"] = "#ff0000"
    original.shortcuts["file_new"] = "Ctrl+Alt+N"
    
    store = QSettings("TestOrg", "TestApp_roundtrip")
    original.save(store)
    
    loaded = EditorSettings.load(store, original)
    assert loaded.font_family == original.font_family
    assert loaded.font_size == 18
    assert loaded.editor_background == "#aabbcc"
    assert loaded.syntax_colors["keyword"] == "#ff0000"
    assert loaded.shortcuts["file_new"] == "Ctrl+Alt+N"
    
    store.clear()
