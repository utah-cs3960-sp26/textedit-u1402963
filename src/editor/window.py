from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QLabel,
    QWidget,
    QToolBar,
    QSizePolicy,
)
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtCore import Qt

from editor.highlighters.detector import LanguageDetector
from editor.code_editor import CodeEditor
from editor.models.document import DocumentModel
from editor.controllers.file_controller import FileController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Editor 9000")
        self.resize(800, 600)

        self._document = DocumentModel()
        self._controller = FileController(self._document)
        self.highlighter = None

        self._setup_central_widget()
        self._setup_highlighter()
        self._setup_menu()
        self._setup_status_label()

        self.text_edit.textChanged.connect(self._mark_modified)

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
        self.text_edit = CodeEditor()
        self.setCentralWidget(self.text_edit)

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
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.text_edit.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.text_edit.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.text_edit.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.text_edit.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.text_edit.paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.text_edit.selectAll)
        edit_menu.addAction(select_all_action)

    def _setup_status_label(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(left_spacer)

        self._status_label = QLabel("Saved")
        self._status_label.setStyleSheet("color: #228B22; font-weight: bold;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar.addWidget(self._status_label)

        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(right_spacer)

    def _mark_modified(self):
        current_content = self.text_edit.toPlainText()
        self._document.current_content = current_content
        self._update_status()

    def _update_status(self):
        if self._document.is_modified:
            self._status_label.setText("Unsaved")
            self._status_label.setStyleSheet("color: #8B0000; font-weight: bold;")
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

    def save_file(self):
        content = self.text_edit.toPlainText()

        if self._document.file_path:
            file_path = self._document.file_path
        else:
            suggested_filter = self._controller.get_save_filter(content)
            all_filters = "All Files (*);;Python (*.py);;C Source (*.c);;C++ Source (*.cpp);;C Header (*.h);;C++ Header (*.hpp);;Java (*.java);;HTML (*.html);;HTM (*.htm);;JSON (*.json);;Markdown (*.md);;Text (*.txt)"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save File",
                "",
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
