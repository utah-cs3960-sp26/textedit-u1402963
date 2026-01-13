import pytest
from PyQt6.QtWidgets import QApplication, QDialog, QMenu
from PyQt6.QtCore import Qt

from editor.window import MainWindow


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture
def main_window(app):
    window = MainWindow()
    yield window
    window.close()


class TestHelpMenu:
    def test_help_menu_exists(self, main_window):
        menu_bar = main_window.menuBar()
        help_menu = None
        for action in menu_bar.actions():
            if "Help" in action.text():
                help_menu = action.menu()
                break
        assert help_menu is not None, "Help menu should exist in menu bar"

    def test_keyboard_shortcuts_action_exists(self, main_window):
        menu_bar = main_window.menuBar()
        help_menu = None
        for action in menu_bar.actions():
            if "Help" in action.text():
                help_menu = action.menu()
                break

        shortcuts_action = None
        for action in help_menu.actions():
            if "Shortcut" in action.text():
                shortcuts_action = action
                break
        assert shortcuts_action is not None, "Keyboard Shortcuts action should exist"

    def test_show_shortcuts_dialog_method_exists(self, main_window):
        assert hasattr(main_window, "_show_shortcuts_dialog")
        assert callable(main_window._show_shortcuts_dialog)
