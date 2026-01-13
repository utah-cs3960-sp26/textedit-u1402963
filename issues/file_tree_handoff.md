# File Tree Explorer Implementation Handoff

## Overview
Implement a file tree explorer with collapsible folders for the FART text editor. The boilerplate code and tests are already in place—this document describes what needs to be implemented.

## Files to Implement

### 1. `src/editor/file_tree.py` - FileTreeWidget
A `QTreeView` subclass for displaying and interacting with the file system.

#### Methods to Implement

| Method | Description |
|--------|-------------|
| `_setup_model()` | Create `QFileSystemModel`, set filter to show hidden files (`QDir.Filter.Hidden \| QDir.Filter.AllEntries \| QDir.Filter.NoDotAndDotDot`), call `setModel()` |
| `_setup_view()` | Hide columns 1-3, set header stretch, connect `doubleClicked` signal to `_on_double_click` |
| `_setup_watcher()` | Create `QFileSystemWatcher`, connect `directoryChanged` to `_on_directory_changed` |
| `_setup_context_menu()` | Set `CustomContextMenu` policy, connect `customContextMenuRequested` to `_show_context_menu` |
| `set_root_folder(path)` | Set model root path, set view root index, add path to watcher |
| `get_selected_path()` | Return `self._model.filePath(self.currentIndex())` |
| `highlight_file(path)` | Get index via `self._model.index(path)`, set current index, scroll to it |
| `_on_double_click(index)` | If directory: toggle expand. If file: emit `file_opened` signal with path |
| `_on_directory_changed(path)` | Force model refresh (may need to reset root index) |
| `_show_context_menu(pos)` | Create `QMenu` with New File, New Folder, Rename, Delete actions |
| `create_new_file(folder, name)` | `open(os.path.join(folder, name), 'w').close()` |
| `create_new_folder(folder, name)` | `os.makedirs(os.path.join(folder, name))` |
| `delete_item(path)` | `os.remove()` for files, `shutil.rmtree()` for folders |
| `rename_item(old_path, new_name)` | `os.rename(old_path, os.path.join(os.path.dirname(old_path), new_name))` |

#### Key PyQt6 Classes
- `QFileSystemModel` - provides file system data
- `QFileSystemWatcher` - monitors file system changes
- `QDir.Filter` - for filtering hidden files

---

### 2. `src/editor/sidebar.py` - SidebarWidget
A container widget with header toolbar and file tree.

#### Methods to Implement

| Method | Description |
|--------|-------------|
| `_setup_ui()` | Create `QVBoxLayout`, add header from `_create_header()`, create and add `FileTreeWidget`, set min width ~200px |
| `_create_header()` | Create widget with `QHBoxLayout`, add `QLabel` for folder name, add refresh `QPushButton`, return widget |
| `_connect_signals()` | Connect `file_tree.file_opened` → `self.file_opened.emit`, connect `refresh_button.clicked` → `self.refresh` |
| `set_root_folder(path)` | Store path, update `header_label` text with `os.path.basename(path)`, call `file_tree.set_root_folder(path)` |
| `refresh()` | Call `set_root_folder(self._root_path)` to re-initialize |
| `toggle_visibility()` | `self.setVisible(not self.isVisible())` |
| `highlight_file(path)` | Forward to `self.file_tree.highlight_file(path)` |

---

### 3. `src/editor/window.py` - MainWindow Modifications
Integrate the sidebar into the main window.

#### Changes Required

1. **Add imports:**
   ```python
   from PyQt6.QtWidgets import QSplitter
   from editor.sidebar import SidebarWidget
   ```

2. **Modify `_setup_central_widget()`:**
   - Create `QSplitter(Qt.Orientation.Horizontal)`
   - Create `SidebarWidget`
   - Add sidebar and `CodeEditor` to splitter
   - Set splitter as central widget
   - Set initial sizes (e.g., `[250, 550]`)

3. **Add to `_setup_menu()` in File menu:**
   - "Open &Folder" action with shortcut `Ctrl+Shift+O`, add shortcut to the help menu
   - Connect to new `open_folder()` method

4. **Add new methods:**
   ```python
   def open_folder(self):
       """Open folder dialog and set sidebar root."""
       folder = QFileDialog.getExistingDirectory(self, "Open Folder")
       if folder:
           self.sidebar.set_root_folder(folder)
   
   def _on_file_opened_from_tree(self, file_path: str):
       """Handle file opened from sidebar tree."""
       # Similar to open_file() but with known path
       # Check for unsaved changes first
       # Load file content
       # Update highlighter
       # Highlight file in tree
   ```

5. **Connect signals in `__init__`:**
   ```python
   self.sidebar.file_opened.connect(self._on_file_opened_from_tree)
   ```

6. **Add View menu with toggle:**
   - "Toggle &Sidebar" action with shortcut `Ctrl+B`
   - Connect to `self.sidebar.toggle_visibility`

---

## Tests Location
`tests/test_file_tree.py` - All tests are written and ready. Run with:
```bash
pytest tests/test_file_tree.py -v
```

Tests will fail until implementation is complete. Use TDD: implement each method until its corresponding test passes.

---

## Implementation Order (Recommended)

### Phase 1: Core FileTreeWidget
1. `_setup_model()` - gets basic tree rendering
2. `_setup_view()` - proper column display
3. `set_root_folder()` - enables setting root
4. `get_selected_path()` - selection support

### Phase 2: Interactions
5. `_on_double_click()` - open files, expand folders
6. `highlight_file()` - sync with editor

### Phase 3: Context Menu
7. `_setup_context_menu()` + `_show_context_menu()`
8. `create_new_file()`, `create_new_folder()`
9. `delete_item()`, `rename_item()`

### Phase 4: Auto-Refresh
10. `_setup_watcher()` + `_on_directory_changed()`

### Phase 5: Sidebar
11. `SidebarWidget._setup_ui()` + `_create_header()`
12. `SidebarWidget._connect_signals()`
13. Remaining sidebar methods

### Phase 6: Window Integration
14. Modify `window.py` to add splitter layout
15. Add "Open Folder" menu action
16. Add "Toggle Sidebar" action
17. Connect `file_opened` signal

---

## Verification
After implementation, verify:
1. All tests pass: `pytest tests/test_file_tree.py -v`
2. Full test suite passes: `pytest`
3. Manual testing:
   - Open folder via menu
   - Double-click files to open in editor
   - Double-click folders to expand/collapse
   - Right-click context menu works
   - Toggle sidebar with Ctrl+B
   - Active file is highlighted in tree

---

## Notes
- Use `QFileSystemModel` not custom model—it handles icons automatically
- Hidden files filter: `QDir.Filter.Hidden | QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot`
- For context menu dialogs, use `QInputDialog.getText()` for rename/new file prompts
- For delete confirmation, use `QMessageBox.question()`
