import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QApplication

from editor.file_tree import FileTreeWidget
from editor.sidebar import SidebarWidget


@pytest.fixture(scope="session")
def app():
    """Create QApplication instance for all tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    yield application


@pytest.fixture
def temp_folder():
    """Create a temporary folder structure for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test structure:
    # temp_dir/
    #   file1.txt
    #   file2.py
    #   .hidden_file
    #   subfolder/
    #     nested.txt
    #   .hidden_folder/
    #     secret.txt
    
    with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
        f.write("content1")
    with open(os.path.join(temp_dir, "file2.py"), "w") as f:
        f.write("print('hello')")
    with open(os.path.join(temp_dir, ".hidden_file"), "w") as f:
        f.write("hidden content")
    
    subfolder = os.path.join(temp_dir, "subfolder")
    os.makedirs(subfolder)
    with open(os.path.join(subfolder, "nested.txt"), "w") as f:
        f.write("nested content")
    
    hidden_folder = os.path.join(temp_dir, ".hidden_folder")
    os.makedirs(hidden_folder)
    with open(os.path.join(hidden_folder, "secret.txt"), "w") as f:
        f.write("secret content")
    
    yield temp_dir
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_tree(app, temp_folder):
    """Create a FileTreeWidget with the temp folder as root."""
    widget = FileTreeWidget()
    widget.set_root_folder(temp_folder)
    return widget


@pytest.fixture
def sidebar(app, temp_folder):
    """Create a SidebarWidget with the temp folder as root."""
    widget = SidebarWidget()
    widget.set_root_folder(temp_folder)
    return widget


class TestFileTreeWidget:
    """Tests for the FileTreeWidget component."""

    def test_set_root_folder_displays_contents(self, file_tree, temp_folder):
        """Tree should display folder contents after setting root."""
        model = file_tree.model()
        root_index = file_tree.rootIndex()
        
        # Should have items in the tree
        assert model.rowCount(root_index) > 0
        
        # Collect visible file names
        visible_names = []
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            visible_names.append(model.fileName(index))
        
        assert "file1.txt" in visible_names
        assert "file2.py" in visible_names
        assert "subfolder" in visible_names

    def test_hidden_files_visible(self, file_tree, temp_folder):
        """Hidden files (dotfiles) should be visible in the tree."""
        model = file_tree.model()
        root_index = file_tree.rootIndex()
        
        visible_names = []
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            visible_names.append(model.fileName(index))
        
        assert ".hidden_file" in visible_names
        assert ".hidden_folder" in visible_names

    def test_double_click_file_emits_signal(self, file_tree, temp_folder):
        """Double-clicking a file should emit file_opened signal with path."""
        signal_received = []
        file_tree.file_opened.connect(lambda path: signal_received.append(path))
        
        # Find file1.txt index
        model = file_tree.model()
        root_index = file_tree.rootIndex()
        file_index = None
        
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            if model.fileName(index) == "file1.txt":
                file_index = index
                break
        
        assert file_index is not None
        
        # Simulate double-click
        file_tree._on_double_click(file_index)
        
        assert len(signal_received) == 1
        assert signal_received[0].endswith("file1.txt")

    def test_double_click_folder_expands(self, file_tree, temp_folder):
        """Double-clicking a folder should expand/collapse it."""
        model = file_tree.model()
        root_index = file_tree.rootIndex()
        folder_index = None
        
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            if model.fileName(index) == "subfolder":
                folder_index = index
                break
        
        assert folder_index is not None
        
        # Initially collapsed
        assert not file_tree.isExpanded(folder_index)
        
        # Double-click should expand
        file_tree._on_double_click(folder_index)
        assert file_tree.isExpanded(folder_index)
        
        # Double-click again should collapse
        file_tree._on_double_click(folder_index)
        assert not file_tree.isExpanded(folder_index)

    def test_get_selected_path(self, file_tree, temp_folder):
        """get_selected_path should return the path of selected item."""
        model = file_tree.model()
        root_index = file_tree.rootIndex()
        
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            if model.fileName(index) == "file1.txt":
                file_tree.setCurrentIndex(index)
                break
        
        selected_path = file_tree.get_selected_path()
        assert selected_path is not None
        assert selected_path.endswith("file1.txt")

    def test_highlight_file(self, file_tree, temp_folder):
        """highlight_file should select and scroll to the given file."""
        file_path = os.path.join(temp_folder, "file2.py")
        
        file_tree.highlight_file(file_path)
        
        selected_path = file_tree.get_selected_path()
        assert selected_path == file_path


class TestFileTreeContextMenu:
    """Tests for context menu actions."""

    def test_create_new_file(self, file_tree, temp_folder):
        """Context menu 'New File' should create a file."""
        new_file_path = os.path.join(temp_folder, "new_file.txt")
        
        assert not os.path.exists(new_file_path)
        
        file_tree.create_new_file(temp_folder, "new_file.txt")
        
        assert os.path.exists(new_file_path)

    def test_create_new_folder(self, file_tree, temp_folder):
        """Context menu 'New Folder' should create a folder."""
        new_folder_path = os.path.join(temp_folder, "new_folder")
        
        assert not os.path.exists(new_folder_path)
        
        file_tree.create_new_folder(temp_folder, "new_folder")
        
        assert os.path.exists(new_folder_path)
        assert os.path.isdir(new_folder_path)

    def test_delete_file(self, file_tree, temp_folder):
        """Context menu 'Delete' should remove a file."""
        file_path = os.path.join(temp_folder, "file1.txt")
        
        assert os.path.exists(file_path)
        
        file_tree.delete_item(file_path)
        
        assert not os.path.exists(file_path)

    def test_delete_folder(self, file_tree, temp_folder):
        """Context menu 'Delete' should remove a folder and contents."""
        folder_path = os.path.join(temp_folder, "subfolder")
        
        assert os.path.exists(folder_path)
        
        file_tree.delete_item(folder_path)
        
        assert not os.path.exists(folder_path)

    def test_rename_file(self, file_tree, temp_folder):
        """Context menu 'Rename' should rename a file."""
        old_path = os.path.join(temp_folder, "file1.txt")
        new_path = os.path.join(temp_folder, "renamed.txt")
        
        assert os.path.exists(old_path)
        assert not os.path.exists(new_path)
        
        file_tree.rename_item(old_path, "renamed.txt")
        
        assert not os.path.exists(old_path)
        assert os.path.exists(new_path)


class TestSidebarWidget:
    """Tests for the SidebarWidget container."""

    def test_set_root_folder(self, sidebar, temp_folder):
        """Sidebar should pass root folder to file tree."""
        assert sidebar.file_tree.model() is not None
        assert sidebar.get_root_folder() == temp_folder

    def test_toggle_visibility(self, sidebar):
        """Toggle should hide/show the sidebar."""
        assert sidebar.isVisible()
        
        sidebar.toggle_visibility()
        assert not sidebar.isVisible()
        
        sidebar.toggle_visibility()
        assert sidebar.isVisible()

    def test_refresh_button_exists(self, sidebar):
        """Sidebar should have a refresh button."""
        assert sidebar.refresh_button is not None

    def test_manual_refresh(self, sidebar, temp_folder):
        """Manual refresh should update the tree."""
        # Create a new file
        new_file = os.path.join(temp_folder, "refresh_test.txt")
        with open(new_file, "w") as f:
            f.write("test")
        
        # Trigger refresh
        sidebar.refresh()
        
        # File should now be visible
        model = sidebar.file_tree.model()
        root_index = sidebar.file_tree.rootIndex()
        
        visible_names = []
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            visible_names.append(model.fileName(index))
        
        assert "refresh_test.txt" in visible_names

    def test_header_shows_folder_name(self, sidebar, temp_folder):
        """Header should display the root folder name."""
        folder_name = os.path.basename(temp_folder)
        assert folder_name in sidebar.header_label.text()


class TestFileTreeAutoRefresh:
    """Tests for auto-refresh functionality."""

    def test_file_watcher_detects_new_file(self, file_tree, temp_folder):
        """Tree should auto-update when new file is created."""
        # This test validates the watcher is set up
        assert file_tree._watcher is not None
        assert temp_folder in file_tree._watcher.directories()

    def test_file_watcher_detects_deletion(self, file_tree, temp_folder):
        """Tree should auto-update when file is deleted."""
        file_path = os.path.join(temp_folder, "file1.txt")
        
        # Delete file externally
        os.remove(file_path)
        
        # Trigger watcher callback manually for testing
        file_tree._on_directory_changed(temp_folder)
        
        model = file_tree.model()
        root_index = file_tree.rootIndex()
        
        visible_names = []
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            visible_names.append(model.fileName(index))
        
        assert "file1.txt" not in visible_names
