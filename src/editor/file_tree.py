"""
FileTreeWidget - A tree view for browsing files and folders.

This widget displays a file system tree with:
- File/folder icons
- Hidden file visibility
- Double-click to open files or expand folders
- Context menu for New File, New Folder, Delete, Rename
- Auto-refresh via QFileSystemWatcher
"""

import os
import shutil

from PyQt6.QtWidgets import (
    QTreeView,
    QMenu,
    QInputDialog,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    QModelIndex,
    QDir,
    QFileSystemWatcher,
    QEventLoop,
)
from PyQt6.QtGui import QFileSystemModel, QAction


class FileTreeWidget(QTreeView):
    """
    A tree view widget for displaying and interacting with a file system.
    
    Signals:
        file_opened(str): Emitted when a file is double-clicked, with the file path.
        directory_changed(str): Emitted when a watched directory changes.
    """
    
    file_opened = pyqtSignal(str)
    directory_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._model = None
        self._watcher = None
        self._root_path = None
        
        self._setup_model()
        self._setup_view()
        self._setup_watcher()
        self._setup_context_menu()
    
    def _setup_model(self):
        """Initialize the QFileSystemModel."""
        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Filter.Hidden | QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self.setModel(self._model)
    
    def _setup_view(self):
        """Configure the tree view appearance."""
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)
        self.header().setStretchLastSection(True)
        self.setExpandsOnDoubleClick(False)
        self.doubleClicked.connect(self._on_double_click)
    
    def _setup_watcher(self):
        """Initialize QFileSystemWatcher for auto-refresh."""
        self._watcher = QFileSystemWatcher()
        self._watcher.directoryChanged.connect(self._on_directory_changed)
    
    def _setup_context_menu(self):
        """Enable and configure the context menu."""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def set_root_folder(self, folder_path: str):
        """
        Set the root folder for the tree view.
        
        Args:
            folder_path: Absolute path to the folder to display.
        """
        loop = QEventLoop()
        self._model.directoryLoaded.connect(loop.quit)
        self._model.setRootPath(folder_path)
        root_index = self._model.index(folder_path)
        self.setRootIndex(root_index)
        self._watcher.addPath(folder_path)
        self._root_path = folder_path
        loop.exec()
    
    def get_root_folder(self) -> str:
        """Return the current root folder path."""
        return self._root_path
    
    def get_selected_path(self) -> str:
        """
        Get the file path of the currently selected item.
        
        Returns:
            The absolute path of the selected item, or None if nothing selected.
        """
        source_index = self._map_to_source(self.currentIndex())
        path = self._model.filePath(source_index)
        return os.path.normpath(path) if path else path
    
    def highlight_file(self, file_path: str):
        """
        Select and scroll to a file in the tree.
        
        Args:
            file_path: Absolute path to the file to highlight.
        """
        source_index = self._model.index(file_path)
        proxy_index = self._map_from_source(source_index)
        self.setCurrentIndex(proxy_index)
        self.scrollTo(proxy_index)
    
    def _on_double_click(self, index: QModelIndex):
        """
        Handle double-click on an item.
        
        - If file: emit file_opened signal
        - If folder: toggle expand/collapse
        """
        source_index = self._map_to_source(index)
        if self._model.isDir(source_index):
            self.setExpanded(index, not self.isExpanded(index))
        else:
            path = self._model.filePath(source_index)
            self.file_opened.emit(path)
    
    def _map_to_source(self, index: QModelIndex) -> QModelIndex:
        """Map a proxy index to source index if using a proxy model."""
        proxy_model = self.model()
        if hasattr(proxy_model, 'mapToSource'):
            return proxy_model.mapToSource(index)
        return index
    
    def _map_from_source(self, index: QModelIndex) -> QModelIndex:
        """Map a source index to proxy index if using a proxy model."""
        proxy_model = self.model()
        if hasattr(proxy_model, 'mapFromSource'):
            return proxy_model.mapFromSource(index)
        return index
    
    def _on_directory_changed(self, path: str):
        """Handle directory change notification from watcher."""
        if self._root_path:
            self.directory_changed.emit(self._root_path)
    
    def _show_context_menu(self, position):
        """Show the right-click context menu."""
        menu = QMenu(self)
        
        new_file_action = QAction("New File", self)
        new_folder_action = QAction("New Folder", self)
        rename_action = QAction("Rename", self)
        delete_action = QAction("Delete", self)
        
        menu.addAction(new_file_action)
        menu.addAction(new_folder_action)
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        
        index = self.indexAt(position)
        if index.isValid():
            source_index = self._map_to_source(index)
            path = self._model.filePath(source_index)
            is_dir = self._model.isDir(source_index)
            parent_folder = path if is_dir else os.path.dirname(path)
        else:
            path = self._root_path
            parent_folder = self._root_path
            rename_action.setEnabled(False)
            delete_action.setEnabled(False)
        
        new_file_action.triggered.connect(lambda: self._prompt_new_file(parent_folder))
        new_folder_action.triggered.connect(lambda: self._prompt_new_folder(parent_folder))
        rename_action.triggered.connect(lambda: self._prompt_rename(path))
        delete_action.triggered.connect(lambda: self._prompt_delete(path))
        
        menu.exec(self.viewport().mapToGlobal(position))
    
    def _prompt_new_file(self, parent_folder: str):
        """Prompt user for new file name and create it."""
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name:
            self.create_new_file(parent_folder, name)
    
    def _prompt_new_folder(self, parent_folder: str):
        """Prompt user for new folder name and create it."""
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            self.create_new_folder(parent_folder, name)
    
    def _prompt_rename(self, path: str):
        """Prompt user for new name and rename item."""
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and new_name and new_name != old_name:
            self.rename_item(path, new_name)
    
    def _prompt_delete(self, path: str):
        """Prompt user for delete confirmation and delete item."""
        name = os.path.basename(path)
        reply = QMessageBox.question(
            self,
            "Delete",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_item(path)
    
    def create_new_file(self, parent_folder: str, file_name: str):
        """
        Create a new empty file.
        
        Args:
            parent_folder: Directory to create the file in.
            file_name: Name of the new file.
        """
        open(os.path.join(parent_folder, file_name), 'w').close()
    
    def create_new_folder(self, parent_folder: str, folder_name: str):
        """
        Create a new folder.
        
        Args:
            parent_folder: Directory to create the folder in.
            folder_name: Name of the new folder.
        """
        os.makedirs(os.path.join(parent_folder, folder_name))
    
    def delete_item(self, path: str):
        """
        Delete a file or folder.
        
        Args:
            path: Absolute path to the item to delete.
        """
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    
    def rename_item(self, old_path: str, new_name: str):
        """
        Rename a file or folder.
        
        Args:
            old_path: Current absolute path.
            new_name: New name (not full path).
        """
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        os.rename(old_path, new_path)
