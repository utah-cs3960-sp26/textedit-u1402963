from __future__ import annotations

from copy import deepcopy

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QWidget,
    QFormLayout,
    QFontComboBox,
    QSpinBox,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QColorDialog,
    QScrollArea,
    QDialogButtonBox,
    QLabel,
    QKeySequenceEdit,
)
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QFont, QKeySequence

from editor.settings import (
    ACTION_LABELS,
    ACTION_GROUPS,
    SYNTAX_STYLE_LABELS,
    EditorSettings,
)


class ColorButton(QPushButton):
    def __init__(self, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedWidth(80)
        self._update_style()
        self.clicked.connect(self._choose_color)

    def _update_style(self) -> None:
        self.setText(self._color.name())
        self.setStyleSheet(f"background-color: {self._color.name()};")

    def _choose_color(self) -> None:
        chosen = QColorDialog.getColor(self._color, self, "Select Color")
        if chosen.isValid():
            self._color = chosen
            self._update_style()

    def color(self) -> str:
        return self._color.name()


class PreferencesDialog(QDialog):
    def __init__(
        self,
        settings: EditorSettings,
        defaults: EditorSettings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(520, 520)

        self._original_settings = settings
        self._default_settings = defaults
        self._settings = deepcopy(settings)

        layout = QVBoxLayout(self)
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._font_family = QFontComboBox()
        self._font_size = QSpinBox()
        self._color_buttons: dict[str, ColorButton] = {}
        self._shortcut_edits: dict[str, QKeySequenceEdit] = {}

        self._tabs.addTab(self._build_general_tab(), "General")
        self._tabs.addTab(self._build_colors_tab(), "Colors")
        self._tabs.addTab(self._build_shortcuts_tab(), "Shortcuts")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self._reset_to_defaults)
        buttons.addButton(reset_button, QDialogButtonBox.ButtonRole.ResetRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_general_tab(self) -> QWidget:
        container = QWidget()
        form = QFormLayout(container)

        self._font_family.setCurrentFont(QFont(self._settings.font_family))
        self._font_size.setRange(8, 48)
        self._font_size.setValue(self._settings.font_size)

        form.addRow("Font family", self._font_family)
        form.addRow("Font size", self._font_size)
        return container

    def _build_colors_tab(self) -> QWidget:
        container = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        layout.addWidget(
            self._build_color_group(
                "Editor",
                {
                    "editor_background": ("Background", self._settings.editor_background),
                    "editor_foreground": ("Foreground", self._settings.editor_foreground),
                },
            )
        )
        layout.addWidget(
            self._build_color_group(
                "Line Numbers",
                {
                    "line_number_background": (
                        "Background",
                        self._settings.line_number_background,
                    ),
                    "line_number_foreground": (
                        "Foreground",
                        self._settings.line_number_foreground,
                    ),
                },
            )
        )
        layout.addWidget(self._build_syntax_group())
        layout.addStretch(1)

        scroll.setWidget(content)
        outer = QVBoxLayout(container)
        outer.addWidget(scroll)
        return container

    def _build_color_group(self, title: str, entries: dict[str, tuple[str, str]]) -> QGroupBox:
        group = QGroupBox(title)
        form = QFormLayout(group)
        for key, (label, color) in entries.items():
            button = ColorButton(color)
            self._color_buttons[key] = button
            form.addRow(QLabel(label), button)
        return group

    def _build_syntax_group(self) -> QGroupBox:
        group = QGroupBox("Syntax Colors")
        form = QFormLayout(group)
        for key, label in SYNTAX_STYLE_LABELS.items():
            color = self._settings.syntax_colors[key]
            button = ColorButton(color)
            self._color_buttons[key] = button
            form.addRow(QLabel(label), button)
        return group

    def _build_shortcuts_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        for group_name, action_ids in ACTION_GROUPS.items():
            group = QGroupBox(group_name)
            form = QFormLayout(group)
            for action_id in action_ids:
                label = ACTION_LABELS.get(action_id, action_id)
                editor = QKeySequenceEdit()
                editor.setKeySequence(QKeySequence(self._settings.shortcuts.get(action_id, "")))
                self._shortcut_edits[action_id] = editor
                form.addRow(QLabel(label), editor)
            layout.addWidget(group)

        layout.addStretch(1)
        return container

    def get_settings(self) -> EditorSettings:
        settings = deepcopy(self._original_settings)
        settings.font_family = self._font_family.currentFont().family()
        settings.font_size = self._font_size.value()

        settings.editor_background = self._color_buttons["editor_background"].color()
        settings.editor_foreground = self._color_buttons["editor_foreground"].color()
        settings.line_number_background = self._color_buttons["line_number_background"].color()
        settings.line_number_foreground = self._color_buttons["line_number_foreground"].color()

        for key in settings.syntax_colors:
            settings.syntax_colors[key] = self._color_buttons[key].color()

        for action_id in settings.shortcuts:
            editor = self._shortcut_edits.get(action_id)
            if editor is not None:
                settings.shortcuts[action_id] = editor.keySequence().toString()

        return settings

    def _reset_to_defaults(self) -> None:
        defaults = self._default_settings
        self._font_family.setCurrentFont(QFont(defaults.font_family))
        self._font_size.setValue(defaults.font_size)

        self._color_buttons["editor_background"]._color = QColor(defaults.editor_background)
        self._color_buttons["editor_background"]._update_style()
        self._color_buttons["editor_foreground"]._color = QColor(defaults.editor_foreground)
        self._color_buttons["editor_foreground"]._update_style()
        self._color_buttons["line_number_background"]._color = QColor(
            defaults.line_number_background
        )
        self._color_buttons["line_number_background"]._update_style()
        self._color_buttons["line_number_foreground"]._color = QColor(
            defaults.line_number_foreground
        )
        self._color_buttons["line_number_foreground"]._update_style()

        for key, color in defaults.syntax_colors.items():
            self._color_buttons[key]._color = QColor(color)
            self._color_buttons[key]._update_style()

        for action_id, sequence in defaults.shortcuts.items():
            editor = self._shortcut_edits.get(action_id)
            if editor is not None:
                editor.setKeySequence(QKeySequence(sequence))
