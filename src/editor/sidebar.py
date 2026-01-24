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
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel

from editor.file_tree import FileTreeWidget


class RecursiveFilterProxyModel(QSortFilterProxyModel):
    """A proxy model that shows parent folders when children match the filter."""
    
    def filterAcceptsRow(self, source_row: int, source_parent):
        if not self.filterRegularExpression().pattern():
            return True
        
        index = self.sourceModel().index(source_row, 0, source_parent)
        if self._matches_filter(index):
            return True
        return self._has_matching_child(index)
    
    def _matches_filter(self, index):
        """Check if this item matches the filter."""
        text = self.sourceModel().data(index)
        if text:
            return self.filterRegularExpression().match(text).hasMatch()
        return False
    
    def _has_matching_child(self, index):
        """Recursively check if any child matches the filter."""
        model = self.sourceModel()
        rows = model.rowCount(index)
        for row in range(rows):
            child = model.index(row, 0, index)
            if self._matches_filter(child) or self._has_matching_child(child):
                return True
        return False


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
        self.search_input = None
        self._root_path = None
        self._stack = None
        self._proxy_model = None
        
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
        tree_layout.addWidget(self._create_search_bar())
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
    
    def _create_search_bar(self) -> QWidget:
        """Create the search input for filtering files."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 0, 4, 4)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.search_input)
        
        return container
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.file_tree.file_opened.connect(self.file_opened.emit)
        self.file_tree.directory_changed.connect(self._on_directory_changed)
        self.refresh_button.clicked.connect(self.refresh)
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)
        self.search_input.textChanged.connect(self._on_search_changed)
    
    def _on_directory_changed(self, path: str):
        """Handle directory change - refresh while preserving search filter."""
        current_filter = self.search_input.text()
        self.set_root_folder(path)
        self.search_input.setText(current_filter)
    
    def _on_search_changed(self, text: str):
        """Filter file tree based on search text."""
        if self._proxy_model:
            self._proxy_model.setFilterFixedString(text)
    
    def set_root_folder(self, folder_path: str):
        """
        Set the root folder for the file tree.
        
        Args:
            folder_path: Absolute path to the folder.
        """
        self._root_path = folder_path
        self.header_label.setText(os.path.basename(folder_path))
        self.file_tree.set_root_folder(folder_path)
        
        self._proxy_model = RecursiveFilterProxyModel()
        self._proxy_model.setSourceModel(self.file_tree._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setRecursiveFilteringEnabled(True)
        self.file_tree.setModel(self._proxy_model)
        
        source_root = self.file_tree._model.index(folder_path)
        proxy_root = self._proxy_model.mapFromSource(source_root)
        self.file_tree.setRootIndex(proxy_root)
        
        self._stack.setCurrentIndex(1)
        self.search_input.clear()
    
    def get_root_folder(self) -> str:
        """Return the current root folder path."""
        return self._root_path
    
    def refresh(self):
        """Manually refresh the file tree."""
        if self._root_path:
            self.file_tree._model.setRootPath("")
            self.set_root_folder(self._root_path)
    
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
    
    def focus_search(self):
        """Focus the search input and select all text."""
        if self._root_path:
            self.search_input.setFocus()
            self.search_input.selectAll()
