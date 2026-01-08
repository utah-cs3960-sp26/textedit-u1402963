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

from editor.file_manager import FileManager
from editor.highlighter import LanguageDetector
from editor.code_editor import CodeEditor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Editor 9000")
        self.resize(800, 600)
        self.current_file = None
        self.file_manager = FileManager()
        self.highlighter = None
        self._is_modified = False
        self._original_content = ""

        self._setup_central_widget()
        self._setup_highlighter()
        self._setup_menu()
        self._setup_status_label()

        self.text_edit.textChanged.connect(self._mark_modified)

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
        self._is_modified = current_content != self._original_content
        self._update_status()

    def _update_status(self):
        if self._is_modified:
            self._status_label.setText("Unsaved")
            self._status_label.setStyleSheet("color: #8B0000; font-weight: bold;")
        else:
            self._status_label.setText("Saved")
            self._status_label.setStyleSheet("color: #228B22; font-weight: bold;")
        self._update_title()

    def _update_title(self):
        base_title = "Text Editor 9000"
        if self.current_file:
            base_title = f"Text Editor 9000 - {self.current_file}"
        if self._is_modified:
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
        if self._is_modified:
            result = self._prompt_save_changes()
            if result == "save":
                self.save_file()
                if self._is_modified:
                    event.ignore()
                    return
            elif result == "cancel":
                event.ignore()
                return
        event.accept()

    def open_file(self):
        if self._is_modified:
            result = self._prompt_save_changes()
            if result == "save":
                self.save_file()
                if self._is_modified:
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

        try:
            content = self.file_manager.read_file(file_path)
            self.text_edit.setPlainText(content)
            self.current_file = file_path
            self._original_content = content
            self._is_modified = False
            self._update_status()
            self._setup_highlighter(file_path, content)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"File not found: {file_path}")
        except PermissionError:
            QMessageBox.critical(self, "Error", f"Permission denied: {file_path}")
        except UnicodeDecodeError:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open file: {file_path}\n\nThis appears to be a binary file. Only text files are supported.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def save_file(self):
        content = self.text_edit.toPlainText()
        
        if self.current_file:
            file_path = self.current_file
        else:
            suggested_filter = LanguageDetector.get_save_filter(
                self.current_file or "", content
            )
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

            file_path = LanguageDetector.suggest_extension(file_path, content)

        try:
            self.file_manager.write_file(file_path, content)
            self.current_file = file_path
            self._original_content = content
            self._is_modified = False
            self._update_status()
            self._setup_highlighter(file_path)
        except PermissionError:
            QMessageBox.critical(self, "Error", f"Permission denied: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")
