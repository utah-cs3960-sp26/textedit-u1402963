from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFontDatabase

from editor.highlighters.core.style_registry import StyleId, StyleRegistry


ACTION_LABELS = {
    "file_new": "New File",
    "file_open": "Open File",
    "file_open_folder": "Open Folder",
    "file_save": "Save File",
    "file_save_as": "Save File As",
    "file_exit": "Exit",
    "edit_undo": "Undo",
    "edit_redo": "Redo",
    "edit_cut": "Cut",
    "edit_copy": "Copy",
    "edit_paste": "Paste",
    "edit_select_all": "Select All",
    "view_toggle_sidebar": "Toggle File Explorer",
    "view_search_files": "Search Files in Explorer",
    "help_shortcuts": "Show Keyboard Shortcuts",
    "settings_preferences": "Preferences",
}


ACTION_GROUPS = {
    "File": [
        "file_new",
        "file_open",
        "file_open_folder",
        "file_save",
        "file_save_as",
        "file_exit",
    ],
    "Edit": [
        "edit_undo",
        "edit_redo",
        "edit_cut",
        "edit_copy",
        "edit_paste",
        "edit_select_all",
    ],
    "Navigation": [
        "view_toggle_sidebar",
        "view_search_files",
    ],
    "Help": [
        "help_shortcuts",
    ],
    "Settings": [
        "settings_preferences",
    ],
}


DEFAULT_SHORTCUTS = {
    "file_new": "Ctrl+N",
    "file_open": "Ctrl+O",
    "file_open_folder": "Ctrl+Shift+O",
    "file_save": "Ctrl+S",
    "file_save_as": "Ctrl+Shift+S",
    "file_exit": "Ctrl+Q",
    "edit_undo": "Ctrl+Z",
    "edit_redo": "Ctrl+Y",
    "edit_cut": "Ctrl+X",
    "edit_copy": "Ctrl+C",
    "edit_paste": "Ctrl+V",
    "edit_select_all": "Ctrl+A",
    "view_toggle_sidebar": "Ctrl+B",
    "view_search_files": "Ctrl+F",
    "help_shortcuts": "F1",
    "settings_preferences": "Ctrl+,",
}


SYNTAX_STYLE_KEYS = {
    "keyword": StyleId.KEYWORD,
    "string": StyleId.STRING,
    "comment": StyleId.COMMENT,
    "number": StyleId.NUMBER,
    "operator": StyleId.OPERATOR,
    "tag": StyleId.TAG,
    "attr_name": StyleId.ATTR_NAME,
    "attr_value": StyleId.ATTR_VALUE,
    "punctuation": StyleId.PUNCTUATION,
    "identifier": StyleId.IDENTIFIER,
    "embedded": StyleId.EMBEDDED,
    "plain": StyleId.PLAIN,
}


SYNTAX_STYLE_LABELS = {
    "keyword": "Keyword",
    "string": "String",
    "comment": "Comment",
    "number": "Number",
    "operator": "Operator",
    "tag": "Tag",
    "attr_name": "Attribute Name",
    "attr_value": "Attribute Value",
    "punctuation": "Punctuation",
    "identifier": "Identifier",
    "embedded": "Embedded",
    "plain": "Plain Text",
}


def _default_font() -> tuple[str, int]:
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    size = font.pointSize() if font.pointSize() > 0 else 12
    return font.family(), size


@dataclass
class EditorSettings:
    font_family: str
    font_size: int
    editor_background: str
    editor_foreground: str
    line_number_background: str
    line_number_foreground: str
    syntax_colors: dict[str, str]
    shortcuts: dict[str, str]

    @classmethod
    def defaults(
        cls,
        editor_background: str,
        editor_foreground: str,
        line_number_background: str,
        line_number_foreground: str,
        font_family: str | None = None,
        font_size: int | None = None,
    ) -> "EditorSettings":
        family, size = _default_font()
        if font_family:
            family = font_family
        if font_size and font_size > 0:
            size = font_size

        default_syntax_colors = {
            key: StyleRegistry.DEFAULT_COLORS[style_id]
            for key, style_id in SYNTAX_STYLE_KEYS.items()
        }

        return cls(
            font_family=family,
            font_size=size,
            editor_background=editor_background,
            editor_foreground=editor_foreground,
            line_number_background=line_number_background,
            line_number_foreground=line_number_foreground,
            syntax_colors=default_syntax_colors,
            shortcuts=DEFAULT_SHORTCUTS.copy(),
        )

    @classmethod
    def load(cls, store: QSettings, defaults: "EditorSettings") -> "EditorSettings":
        font_family = store.value("font/family", defaults.font_family)
        font_size = int(store.value("font/size", defaults.font_size))

        editor_background = store.value("colors/editor_background", defaults.editor_background)
        editor_foreground = store.value("colors/editor_foreground", defaults.editor_foreground)
        line_number_background = store.value(
            "colors/line_number_background", defaults.line_number_background
        )
        line_number_foreground = store.value(
            "colors/line_number_foreground", defaults.line_number_foreground
        )

        syntax_colors: dict[str, str] = {}
        for key, default in defaults.syntax_colors.items():
            syntax_colors[key] = store.value(f"colors/syntax/{key}", default)

        shortcuts: dict[str, str] = {}
        for key, default in defaults.shortcuts.items():
            shortcuts[key] = store.value(f"shortcuts/{key}", default)

        return cls(
            font_family=str(font_family),
            font_size=int(font_size),
            editor_background=str(editor_background),
            editor_foreground=str(editor_foreground),
            line_number_background=str(line_number_background),
            line_number_foreground=str(line_number_foreground),
            syntax_colors=syntax_colors,
            shortcuts=shortcuts,
        )

    def save(self, store: QSettings) -> None:
        store.setValue("font/family", self.font_family)
        store.setValue("font/size", self.font_size)
        store.setValue("colors/editor_background", self.editor_background)
        store.setValue("colors/editor_foreground", self.editor_foreground)
        store.setValue("colors/line_number_background", self.line_number_background)
        store.setValue("colors/line_number_foreground", self.line_number_foreground)
        for key, value in self.syntax_colors.items():
            store.setValue(f"colors/syntax/{key}", value)
        for key, value in self.shortcuts.items():
            store.setValue(f"shortcuts/{key}", value)
