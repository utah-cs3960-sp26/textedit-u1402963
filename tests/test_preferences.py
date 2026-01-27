import pytest

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


def test_settings_menu_exists(window):
    menu_bar = window.menuBar()
    menus = [action.text() for action in menu_bar.actions()]
    assert any("Settings" in menu for menu in menus)


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

    dialog._color_buttons["editor_background"]._color = QColor("#010203")
    dialog._color_buttons["editor_background"]._update_style()
    dialog._color_buttons["keyword"]._color = QColor("#0a0b0c")
    dialog._color_buttons["keyword"]._update_style()

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

    reset_button.click()

    assert dialog._font_size.value() == defaults.font_size
    assert dialog._color_buttons["editor_background"].color() == defaults.editor_background
    assert dialog._color_buttons["line_number_background"].color() == defaults.line_number_background
    assert (
        dialog._color_buttons["keyword"].color().lower()
        == defaults.syntax_colors["keyword"].lower()
    )
    assert dialog._shortcut_edits["file_open"].keySequence().toString() == defaults.shortcuts["file_open"]
