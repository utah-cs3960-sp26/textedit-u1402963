import os

from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QLabel,
    QWidget,
    QToolBar,
    QSizePolicy,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QSplitter,
    QInputDialog,
)
from PyQt6.QtGui import QAction, QCloseEvent, QShortcut, QKeySequence, QPalette
from PyQt6.QtCore import Qt, QSettings

from editor.sidebar import SidebarWidget

from editor.highlighters.detector import LanguageDetector
from editor.code_editor import CodeEditor
from editor.models.document import DocumentModel
from editor.controllers.file_controller import FileController
from editor.highlighters.core.style_registry import StyleRegistry
from editor.preferences_dialog import PreferencesDialog
from editor.settings import (
    ACTION_LABELS,
    ACTION_GROUPS,
    DEFAULT_SHORTCUTS,
    EditorSettings,
    SYNTAX_STYLE_KEYS,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Editor 9000")
        self.resize(800, 600)

        self._document = DocumentModel()
        self._controller = FileController(self._document)
        self.highlighter = None
        self._actions = {}
        self._shortcuts = {}

        self._setup_central_widget()
        self._init_settings()
        self._setup_highlighter()
        self._setup_menu()
        self._setup_status_label()
        self._setup_shortcuts()
        self._apply_settings(self._settings)

        self.text_edit.textChanged.connect(self._mark_modified)
        self.sidebar.file_opened.connect(self._on_file_opened_from_tree)
        self.sidebar.open_folder_requested.connect(self.open_folder)

    @property
    def current_file(self):
        return self._document.file_path

    @current_file.setter
    def current_file(self, value):
        self._document.file_path = value

    @property
    def _is_modified(self):
        return self._document.is_modified

    @_is_modified.setter
    def _is_modified(self, value):
        if value:
            self._document._current_content = self.text_edit.toPlainText()
        else:
            self._document.mark_saved()

    @property
    def _original_content(self):
        return self._document.original_content

    @_original_content.setter
    def _original_content(self, value):
        self._document._original_content = value

    def _setup_central_widget(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.sidebar = SidebarWidget()
        splitter.addWidget(self.sidebar)
        self.text_edit = CodeEditor()
        splitter.addWidget(self.text_edit)
        splitter.setSizes([250, 550])
        self.setCentralWidget(splitter)

    def _setup_shortcuts(self):
        self._sidebar_shortcut = QShortcut(QKeySequence(), self)
        self._sidebar_shortcut.activated.connect(self._toggle_sidebar)
        self._shortcuts["view_toggle_sidebar"] = self._sidebar_shortcut

        self._search_shortcut = QShortcut(QKeySequence(), self)
        self._search_shortcut.activated.connect(self._focus_file_search)
        self._shortcuts["view_search_files"] = self._search_shortcut
    
    def _toggle_sidebar(self):
        is_visible = self.sidebar.isVisible()
        self.sidebar.setVisible(not is_visible)
        self.toggle_sidebar_button.setChecked(not is_visible)
    
    def _focus_file_search(self):
        if not self.sidebar.isVisible():
            self.sidebar.setVisible(True)
            self.toggle_sidebar_button.setChecked(True)
        self.sidebar.focus_search()

    def _setup_highlighter(self, file_path: str = "", content: str = ""):
        if self.highlighter:
            self.highlighter.setDocument(None)
        self.highlighter = LanguageDetector.get_highlighter(
            self.text_edit.document(), file_path, content
        )

    def _setup_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        new_action = QAction("&New", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        self._actions["file_new"] = new_action

        open_action = QAction("&Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        self._actions["file_open"] = open_action

        open_folder_action = QAction("Open &Folder", self)
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        self._actions["file_open_folder"] = open_folder_action

        save_action = QAction("&Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        self._actions["file_save"] = save_action

        save_as_action = QAction("Save &As...", self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        self._actions["file_save_as"] = save_as_action

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        self._actions["file_exit"] = exit_action

        edit_menu = menu_bar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.triggered.connect(self.text_edit.undo)
        edit_menu.addAction(undo_action)
        self._actions["edit_undo"] = undo_action

        redo_action = QAction("&Redo", self)
        redo_action.triggered.connect(self.text_edit.redo)
        edit_menu.addAction(redo_action)
        self._actions["edit_redo"] = redo_action

        edit_menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.triggered.connect(self.text_edit.cut)
        edit_menu.addAction(cut_action)
        self._actions["edit_cut"] = cut_action

        copy_action = QAction("&Copy", self)
        copy_action.triggered.connect(self.text_edit.copy)
        edit_menu.addAction(copy_action)
        self._actions["edit_copy"] = copy_action

        paste_action = QAction("&Paste", self)
        paste_action.triggered.connect(self.text_edit.paste)
        edit_menu.addAction(paste_action)
        self._actions["edit_paste"] = paste_action

        edit_menu.addSeparator()

        select_all_action = QAction("Select &All", self)
        select_all_action.triggered.connect(self.text_edit.selectAll)
        edit_menu.addAction(select_all_action)
        self._actions["edit_select_all"] = select_all_action

        format_menu = menu_bar.addMenu("F&ormat")
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setMenuRole(QAction.MenuRole.NoRole)
        preferences_action.triggered.connect(self._open_preferences)
        format_menu.addAction(preferences_action)
        self._actions["settings_preferences"] = preferences_action

        help_menu = menu_bar.addMenu("&Help")

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)
        self._actions["help_shortcuts"] = shortcuts_action

    def _setup_status_label(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self.toggle_sidebar_button = QPushButton("📁")
        self.toggle_sidebar_button.setCheckable(True)
        self.toggle_sidebar_button.setChecked(True)
        self.toggle_sidebar_button.setFixedSize(28, 28)
        self.toggle_sidebar_button.setToolTip("Toggle File Explorer (Ctrl+B)")
        self.toggle_sidebar_button.clicked.connect(self._toggle_sidebar)
        toolbar.addWidget(self.toggle_sidebar_button)

        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(left_spacer)

        self._status_label = QLabel("New")
        self._status_label.setStyleSheet("color: #1E90FF; font-weight: bold;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar.addWidget(self._status_label)

        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(right_spacer)

        right_balance = QWidget()
        right_balance.setFixedWidth(28)
        toolbar.addWidget(right_balance)

    def _init_settings(self):
        self._settings_store = QSettings("FART", "Text Editor 9000")
        palette = self.text_edit.palette()
        editor_background = palette.color(QPalette.ColorRole.Base).name()
        editor_foreground = palette.color(QPalette.ColorRole.Text).name()
        line_number_background = self.text_edit.DEFAULT_LINE_NUMBER_BG.name()
        line_number_foreground = self.text_edit.DEFAULT_LINE_NUMBER_FG.name()
        self._default_settings = EditorSettings.defaults(
            editor_background=editor_background,
            editor_foreground=editor_foreground,
            line_number_background=line_number_background,
            line_number_foreground=line_number_foreground,
            font_family=self.text_edit.font().family(),
            font_size=self.text_edit.font().pointSize(),
        )
        self._settings = EditorSettings.load(self._settings_store, self._default_settings)

    def _apply_settings(self, settings: EditorSettings) -> None:
        self.text_edit.apply_font(settings.font_family, settings.font_size)
        self.text_edit.apply_editor_colors(
            settings.editor_background, settings.editor_foreground
        )
        self.text_edit.set_line_number_colors(
            settings.line_number_background, settings.line_number_foreground
        )
        style_registry = StyleRegistry.instance()
        for key, color in settings.syntax_colors.items():
            style_registry.set_color(SYNTAX_STYLE_KEYS[key], color)
        if self.highlighter:
            self.highlighter.rehighlight()
        self._apply_shortcuts(settings.shortcuts)

    def _apply_shortcuts(self, shortcuts: dict[str, str]) -> None:
        for action_id, action in self._actions.items():
            if action_id in shortcuts:
                action.setShortcut(QKeySequence(shortcuts[action_id]))
        for action_id, shortcut in self._shortcuts.items():
            if action_id in shortcuts:
                shortcut.setKey(QKeySequence(shortcuts[action_id]))

    def _open_preferences(self):
        dialog = PreferencesDialog(self._settings, self._default_settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._settings = dialog.get_settings()
            self._settings.save(self._settings_store)
            self._apply_settings(self._settings)

    def _mark_modified(self):
        current_content = self.text_edit.toPlainText()
        self._document.current_content = current_content
        self._update_status()

    def _update_status(self):
        if self._document.is_modified:
            self._status_label.setText("Unsaved")
            self._status_label.setStyleSheet("color: #8B0000; font-weight: bold;")
        elif not self._document.file_path:
            self._status_label.setText("New")
            self._status_label.setStyleSheet("color: #1E90FF; font-weight: bold;")
        else:
            self._status_label.setText("Saved")
            self._status_label.setStyleSheet("color: #228B22; font-weight: bold;")
        self._update_title()

    def _update_title(self):
        base_title = "Text Editor 9000"
        if self._document.file_path:
            base_title = f"Text Editor 9000 - {self._document.file_path}"
        if self._document.is_modified:
            self.setWindowTitle(f"* {base_title}")
        else:
            self.setWindowTitle(base_title)

    def _prompt_save_changes(self):
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "Save changes before closing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if reply == QMessageBox.StandardButton.Save:
            return "save"
        elif reply == QMessageBox.StandardButton.Discard:
            return "discard"
        else:
            return "cancel"

    def closeEvent(self, event: QCloseEvent):
        if self._document.is_modified:
            result = self._prompt_save_changes()
            if result == "save":
                self.save_file()
                if self._document.is_modified:
                    event.ignore()
                    return
            elif result == "cancel":
                event.ignore()
                return
        event.accept()

    def new_file(self):
        if self._document.is_modified:
            result = self._prompt_save_changes()
            if result == "save":
                self.save_file()
                if self._document.is_modified:
                    return
            elif result == "cancel":
                return

        root_folder = self.sidebar.get_root_folder()
        if root_folder:
            name, ok = QInputDialog.getText(self, "New File", "File name:")
            if ok and name:
                file_path = os.path.join(root_folder, name)
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("")
                    self.text_edit.clear()
                    self._document.reset()
                    self._document.file_path = file_path
                    self._document.set_content("", mark_as_saved=True)
                    self._setup_highlighter(file_path)
                    self._update_status()
                    self.sidebar.file_tree.highlight_file(file_path)
                except OSError as e:
                    QMessageBox.critical(self, "Error", f"Could not create file: {e}")
            return

        self.text_edit.clear()
        self._document.reset()
        self._setup_highlighter()
        self._update_status()

    def open_file(self):
        if self._document.is_modified:
            result = self._prompt_save_changes()
            if result == "save":
                self.save_file()
                if self._document.is_modified:
                    return
            elif result == "cancel":
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*);;Python (*.py);;C/C++ (*.c *.cpp *.h *.hpp);;Java (*.java);;HTML (*.html *.htm);;JSON (*.json);;Markdown (*.md);;Text (*.txt)",
        )
        if not file_path:
            return

        success, content, error_msg = self._controller.open_file(file_path)
        if success:
            self.text_edit.setPlainText(content)
            self._update_status()
            self._setup_highlighter(file_path, content)
        else:
            QMessageBox.critical(self, "Error", error_msg)

    def open_folder(self):
        """Open folder dialog and set sidebar root."""
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder:
            self.sidebar.set_root_folder(folder)

    def _on_file_opened_from_tree(self, file_path: str):
        """Handle file opened from sidebar tree."""
        if self._document.is_modified:
            result = self._prompt_save_changes()
            if result == "save":
                self.save_file()
                if self._document.is_modified:
                    return
            elif result == "cancel":
                return

        success, content, error_msg = self._controller.open_file(file_path)
        if success:
            self.text_edit.setPlainText(content)
            self._update_status()
            self._setup_highlighter(file_path, content)
            self.sidebar.highlight_file(file_path)
        else:
            QMessageBox.critical(self, "Error", error_msg)

    def save_file(self):
        content = self.text_edit.toPlainText()

        if self._document.file_path:
            file_path = self._document.file_path
            success, error_msg = self._controller.save_file(file_path, content)
            if success:
                self._update_status()
                self._setup_highlighter(self._document.file_path)
            else:
                QMessageBox.critical(self, "Error", error_msg)
        else:
            self.save_file_as()

    def save_file_as(self):
        content = self.text_edit.toPlainText()
        suggested_filter = self._controller.get_save_filter(content)
        all_filters = "All Files (*);;Python (*.py);;C Source (*.c);;C++ Source (*.cpp);;C Header (*.h);;C++ Header (*.hpp);;Java (*.java);;HTML (*.html);;HTM (*.htm);;JSON (*.json);;Markdown (*.md);;Text (*.txt)"

        start_dir = ""
        if self._document.file_path:
            start_dir = os.path.dirname(self._document.file_path)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            start_dir,
            all_filters,
            suggested_filter,
        )
        if not file_path:
            return

        success, error_msg = self._controller.save_file(file_path, content)
        if success:
            self._update_status()
            self._setup_highlighter(self._document.file_path)
        else:
            QMessageBox.critical(self, "Error", error_msg)

    def _show_shortcuts_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        shortcuts_text = QTextEdit()
        shortcuts_text.setReadOnly(True)
        shortcuts_text.setHtml(self._build_shortcuts_html())
        layout.addWidget(shortcuts_text)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.exec()

    def _build_shortcuts_html(self) -> str:
        sections = []
        for group_name, action_ids in ACTION_GROUPS.items():
            rows = []
            for action_id in action_ids:
                label = ACTION_LABELS.get(action_id, action_id)
                shortcut = self._get_shortcut_string(action_id)
                if not shortcut:
                    shortcut = ""
                rows.append(f"<tr><td><b>{shortcut}</b></td><td>{label}</td></tr>")
            sections.append(f"<h3>{group_name}</h3><table>{''.join(rows)}</table>")
        return "\n".join(sections)

    def _get_shortcut_string(self, action_id: str) -> str:
        action = self._actions.get(action_id)
        if action is not None:
            return action.shortcut().toString()
        shortcut = self._shortcuts.get(action_id)
        if shortcut is not None:
            return shortcut.key().toString()
        return DEFAULT_SHORTCUTS.get(action_id, "")
