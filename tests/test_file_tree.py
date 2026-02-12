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

    def test_directory_changed_signal_with_root(self, file_tree, temp_folder):
        """directory_changed should emit root path when set."""
        received = []
        file_tree.directory_changed.connect(received.append)

        file_tree._on_directory_changed(temp_folder)

        assert received == [temp_folder]

    def test_directory_changed_signal_without_root(self, app):
        """directory_changed should not emit when no root is set."""
        tree = FileTreeWidget()
        received = []
        tree.directory_changed.connect(received.append)

        tree._on_directory_changed("ignored")

        assert received == []


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
            visible_names.append(model.data(index))
        
        assert "refresh_test.txt" in visible_names

    def test_header_shows_folder_name(self, sidebar, temp_folder):
        """Header should display the root folder name."""
        folder_name = os.path.basename(temp_folder)
        assert folder_name in sidebar.header_label.text()


class TestFileTreeAutoRefresh:
    """Tests for auto-refresh functionality."""

    def test_file_watcher_detects_new_file(self, sidebar, temp_folder):
        """Tree should auto-update when new file is created."""
        # This test validates the watcher is set up
        assert sidebar.file_tree._watcher is not None
        assert temp_folder in sidebar.file_tree._watcher.directories()

    def test_file_watcher_detects_deletion(self, sidebar, temp_folder):
        """Tree should auto-update when file is deleted."""
        file_path = os.path.join(temp_folder, "file1.txt")
        
        # Delete file externally
        os.remove(file_path)
        
        # Trigger watcher callback manually for testing (sidebar handles the signal)
        sidebar.file_tree._on_directory_changed(temp_folder)
        
        model = sidebar.file_tree.model()
        root_index = sidebar.file_tree.rootIndex()
        
        visible_names = []
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            visible_names.append(model.data(index))
        
        assert "file1.txt" not in visible_names


class TestFileTreeWithProxyModel:
    """Tests for file tree operations when using a proxy model (via sidebar search)."""

    def test_double_click_file_with_filter_active(self, sidebar, temp_folder):
        """Double-clicking a file should work when search filter is active."""
        sidebar.search_input.setText("file1")
        
        signal_received = []
        sidebar.file_opened.connect(lambda path: signal_received.append(path))
        
        model = sidebar.file_tree.model()
        root_index = sidebar.file_tree.rootIndex()
        
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            if model.data(index) == "file1.txt":
                sidebar.file_tree._on_double_click(index)
                break
        
        assert len(signal_received) == 1
        assert signal_received[0].endswith("file1.txt")

    def test_get_selected_path_with_filter_active(self, sidebar, temp_folder):
        """get_selected_path should return correct path when filter is active."""
        sidebar.search_input.setText("file2")
        
        model = sidebar.file_tree.model()
        root_index = sidebar.file_tree.rootIndex()
        
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            if model.data(index) == "file2.py":
                sidebar.file_tree.setCurrentIndex(index)
                break
        
        selected_path = sidebar.file_tree.get_selected_path()
        assert selected_path.endswith("file2.py")

    def test_highlight_file_with_filter_active(self, sidebar, temp_folder):
        """highlight_file should work when filter is active."""
        file_path = os.path.join(temp_folder, "file1.txt")
        
        sidebar.search_input.setText("file1")
        sidebar.file_tree.highlight_file(file_path)
        
        selected_path = sidebar.file_tree.get_selected_path()
        assert selected_path == os.path.normpath(file_path)

    def test_context_menu_with_filter_active(self, sidebar, temp_folder):
        """Context menu operations should work when filter is active."""
        sidebar.search_input.setText("file1")
        
        model = sidebar.file_tree.model()
        root_index = sidebar.file_tree.rootIndex()
        
        file_index = None
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            if model.data(index) == "file1.txt":
                file_index = index
                break
        
        assert file_index is not None
        source_index = sidebar.file_tree._map_to_source(file_index)
        path = sidebar.file_tree._model.filePath(source_index)
        assert path.endswith("file1.txt")

    def test_search_filters_files(self, sidebar, temp_folder):
        """Search input should filter visible files."""
        sidebar.search_input.setText("file1")
        
        model = sidebar.file_tree.model()
        root_index = sidebar.file_tree.rootIndex()
        
        visible_names = []
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            visible_names.append(model.data(index))
        
        assert "file1.txt" in visible_names
        assert "file2.py" not in visible_names

    def test_clear_search_shows_all_files(self, sidebar, temp_folder):
        """Clearing search should show all files again."""
        sidebar.search_input.setText("file1")
        sidebar.search_input.clear()
        
        model = sidebar.file_tree.model()
        root_index = sidebar.file_tree.rootIndex()
        
        visible_names = []
        for row in range(model.rowCount(root_index)):
            index = model.index(row, 0, root_index)
            visible_names.append(model.data(index))
        
        assert "file1.txt" in visible_names
        assert "file2.py" in visible_names


class TestPromptNewFile:
    """Tests for _prompt_new_file which shows QInputDialog."""

    def test_creates_file_on_ok(self, file_tree, temp_folder):
        """When user enters a name and clicks OK, file is created."""
        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("new_test.txt", True)):
            file_tree._prompt_new_file(temp_folder)

        assert os.path.exists(os.path.join(temp_folder, "new_test.txt"))

    def test_cancelled_does_nothing(self, file_tree, temp_folder):
        """When user cancels the dialog, no file is created."""
        before = set(os.listdir(temp_folder))
        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("cancelled.txt", False)):
            file_tree._prompt_new_file(temp_folder)

        assert set(os.listdir(temp_folder)) == before

    def test_empty_name_does_nothing(self, file_tree, temp_folder):
        """When user clicks OK but name is empty, no file is created."""
        before = set(os.listdir(temp_folder))
        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("", True)):
            file_tree._prompt_new_file(temp_folder)

        assert set(os.listdir(temp_folder)) == before


class TestPromptNewFolder:
    """Tests for _prompt_new_folder which shows QInputDialog."""

    def test_creates_folder_on_ok(self, file_tree, temp_folder):
        """When user enters a name and clicks OK, folder is created."""
        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("new_dir", True)):
            file_tree._prompt_new_folder(temp_folder)

        created = os.path.join(temp_folder, "new_dir")
        assert os.path.isdir(created)

    def test_cancelled_does_nothing(self, file_tree, temp_folder):
        """When user cancels, no folder is created."""
        before = set(os.listdir(temp_folder))
        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("nope", False)):
            file_tree._prompt_new_folder(temp_folder)

        assert set(os.listdir(temp_folder)) == before

    def test_empty_name_does_nothing(self, file_tree, temp_folder):
        """When user clicks OK but name is empty, no folder is created."""
        before = set(os.listdir(temp_folder))
        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("", True)):
            file_tree._prompt_new_folder(temp_folder)

        assert set(os.listdir(temp_folder)) == before


class TestPromptRename:
    """Tests for _prompt_rename which shows QInputDialog."""

    def test_renames_file_on_ok(self, file_tree, temp_folder):
        """When user enters a new name and clicks OK, item is renamed."""
        old_path = os.path.join(temp_folder, "file1.txt")
        assert os.path.exists(old_path)

        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("renamed.txt", True)):
            file_tree._prompt_rename(old_path)

        assert os.path.exists(os.path.join(temp_folder, "renamed.txt"))
        assert not os.path.exists(old_path)

    def test_cancelled_does_nothing(self, file_tree, temp_folder):
        """When user cancels, file keeps its original name."""
        old_path = os.path.join(temp_folder, "file2.py")
        assert os.path.exists(old_path)

        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("nope.py", False)):
            file_tree._prompt_rename(old_path)

        assert os.path.exists(old_path)

    def test_same_name_does_nothing(self, file_tree, temp_folder):
        """When user clicks OK but enters the same name, no rename occurs."""
        old_path = os.path.join(temp_folder, "file2.py")
        assert os.path.exists(old_path)

        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("file2.py", True)):
            file_tree._prompt_rename(old_path)

        assert os.path.exists(old_path)

    def test_empty_name_does_nothing(self, file_tree, temp_folder):
        """When user clicks OK but name is empty, no rename occurs."""
        old_path = os.path.join(temp_folder, "file2.py")
        assert os.path.exists(old_path)

        with patch("editor.file_tree.QInputDialog.getText",
                   return_value=("", True)):
            file_tree._prompt_rename(old_path)

        assert os.path.exists(old_path)


class TestPromptDelete:
    """Tests for _prompt_delete which shows QMessageBox."""

    def test_yes_deletes_file(self, file_tree, temp_folder):
        """When user confirms deletion, file is removed."""
        target = os.path.join(temp_folder, "file2.py")
        assert os.path.exists(target)

        with patch("editor.file_tree.QMessageBox.question") as mock_q:
            from PyQt6.QtWidgets import QMessageBox
            mock_q.return_value = QMessageBox.StandardButton.Yes
            file_tree._prompt_delete(target)

        assert not os.path.exists(target)

    def test_no_keeps_file(self, file_tree, temp_folder):
        """When user declines deletion, file is preserved."""
        target = os.path.join(temp_folder, "file1.txt")
        assert os.path.exists(target)

        with patch("editor.file_tree.QMessageBox.question") as mock_q:
            from PyQt6.QtWidgets import QMessageBox
            mock_q.return_value = QMessageBox.StandardButton.No
            file_tree._prompt_delete(target)

        assert os.path.exists(target)

    def test_yes_deletes_folder(self, file_tree, temp_folder):
        """When user confirms deletion of a folder, folder is removed."""
        target = os.path.join(temp_folder, "subfolder")
        assert os.path.isdir(target)

        with patch("editor.file_tree.QMessageBox.question") as mock_q:
            from PyQt6.QtWidgets import QMessageBox
            mock_q.return_value = QMessageBox.StandardButton.Yes
            file_tree._prompt_delete(target)

        assert not os.path.exists(target)


class TestSidebarFocusSearch:
    def test_focus_search_with_root(self, sidebar, temp_folder):
        """focus_search should focus the search input when root is set."""
        sidebar.focus_search()
        assert sidebar.search_input.hasFocus()
    
    def test_focus_search_without_root(self, app):
        """focus_search should do nothing when no root folder is set."""
        sidebar = SidebarWidget()
        sidebar.focus_search()
        # Should not crash, search should not have focus
        assert not sidebar.search_input.hasFocus()


class TestContextMenu:
    def test_context_menu_is_built(self, file_tree, temp_folder):
        """_show_context_menu should create a menu without crashing."""
        from PyQt6.QtCore import QPoint
        with patch("editor.file_tree.QMenu.exec"):
            file_tree._show_context_menu(QPoint(0, 0))

    def test_context_menu_on_valid_item(self, file_tree, temp_folder):
        """Context menu on a valid item should enable all actions."""
        from PyQt6.QtCore import QPoint
        with patch("editor.file_tree.QMenu.exec"):
            # Click at center of widget where items exist
            file_tree._show_context_menu(QPoint(50, 50))

    def test_context_menu_on_invalid_item_disables_actions(self, file_tree):
        """Context menu on invalid item should disable rename/delete."""
        from PyQt6.QtCore import QPoint, QModelIndex
        with patch("editor.file_tree.QMenu.exec"), \
             patch("editor.file_tree.QAction.setEnabled") as mock_set_enabled, \
             patch.object(file_tree, "indexAt", return_value=QModelIndex()):
            file_tree._show_context_menu(QPoint(0, 0))

        assert mock_set_enabled.call_count >= 2


class TestFileTreeNoRoot:
    def test_get_root_folder_none(self, app):
        """get_root_folder returns None when no root set."""
        tree = FileTreeWidget()
        assert tree.get_root_folder() is None
