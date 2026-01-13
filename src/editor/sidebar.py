"""
SidebarWidget - Container for the file tree with header toolbar.

This widget provides:
- Header with folder name and refresh button
- FileTreeWidget for browsing files
- Toggle visibility support
"""

import os

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal

from editor.file_tree import FileTreeWidget


class SidebarWidget(QWidget):
    """
    A sidebar container with a file tree and header toolbar.
    
    Signals:
        file_opened(str): Forwarded from FileTreeWidget when a file is opened.
    """
    
    file_opened = pyqtSignal(str)
    open_folder_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.file_tree = None
        self.header_label = None
        self.refresh_button = None
        self.open_folder_button = None
        self._root_path = None
        self._stack = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Build the sidebar layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)
        
        self._stack.addWidget(self._create_empty_state())
        
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.addWidget(self._create_header())
        self.file_tree = FileTreeWidget()
        tree_layout.addWidget(self.file_tree)
        self._stack.addWidget(tree_container)
        
        self._stack.setCurrentIndex(0)
        
        self.setMinimumWidth(200)
        self.show()
    
    def _create_empty_state(self) -> QWidget:
        """Create the empty state widget shown before a folder is opened."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel("No folder open")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        shortcut_label = QLabel("Ctrl+Shift+O to open a folder")
        shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_label.setStyleSheet("color: gray;")
        layout.addWidget(shortcut_label)
        
        self.open_folder_button = QPushButton("Open Folder")
        layout.addWidget(self.open_folder_button)
        
        return container
    
    def _create_header(self) -> QWidget:
        """
        Create the header widget with folder name and buttons.
        
        Returns:
            QWidget containing the header layout.
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        
        self.header_label = QLabel()
        self.header_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.header_label)
        
        self.refresh_button = QPushButton("↻")
        layout.addWidget(self.refresh_button)
        
        return container
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.file_tree.file_opened.connect(self.file_opened.emit)
        self.refresh_button.clicked.connect(self.refresh)
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)
    
    def set_root_folder(self, folder_path: str):
        """
        Set the root folder for the file tree.
        
        Args:
            folder_path: Absolute path to the folder.
        """
        self._root_path = folder_path
        self.header_label.setText(os.path.basename(folder_path))
        self.file_tree.set_root_folder(folder_path)
        self._stack.setCurrentIndex(1)
    
    def get_root_folder(self) -> str:
        """Return the current root folder path."""
        return self._root_path
    
    def refresh(self):
        """Manually refresh the file tree."""
        if self._root_path:
            model = self.file_tree.model()
            model.setRootPath("")
            self.file_tree.set_root_folder(self._root_path)
    
    def toggle_visibility(self):
        """Toggle the sidebar visibility."""
        self.setVisible(not self.isVisible())
    
    def highlight_file(self, file_path: str):
        """
        Highlight a file in the tree.
        
        Args:
            file_path: Absolute path to the file.
        """
        self.file_tree.highlight_file(file_path)
