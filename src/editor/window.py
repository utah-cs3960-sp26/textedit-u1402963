from PyQt6.QtWidgets import (
    QMainWindow,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtGui import QAction

from editor.file_manager import FileManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hello World")
        self.resize(800, 600)
        self.current_file = None
        self.file_manager = FileManager()

        self._setup_central_widget()
        self._setup_menu()

    def _setup_central_widget(self):
        self.text_edit = QPlainTextEdit()
        self.setCentralWidget(self.text_edit)

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

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return

        try:
            content = self.file_manager.read_file(file_path)
            self.text_edit.setPlainText(content)
            self.current_file = file_path
            self.setWindowTitle(f"Hello World - {file_path}")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"File not found: {file_path}")
        except PermissionError:
            QMessageBox.critical(self, "Error", f"Permission denied: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            self.current_file or "",
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return

        try:
            self.file_manager.write_file(file_path, self.text_edit.toPlainText())
            self.current_file = file_path
            self.setWindowTitle(f"Hello World - {file_path}")
        except PermissionError:
            QMessageBox.critical(self, "Error", f"Permission denied: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")
