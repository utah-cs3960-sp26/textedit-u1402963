# textedit-u1402963
Text editor made using AI assistance for CS3960



# --------------------------------------- AI Generated ----------------------------
## Release R1 - Basic Editor Foundation

### Features
- **File Open** (Ctrl+O): Load text files with native file dialog
- **File Save** (Ctrl+S): Save content to disk with file dialog
- **Basic UI**: Main window with menu bar and text editing area
- **Error Handling**: User-friendly error messages for file operations

### Architecture

**Project Structure:**
```
src/
├── main.py              # Application entry point
└── editor/
    ├── window.py        # MainWindow (UI layer)
    └── file_manager.py  # FileManager (I/O logic)
tests/
└── test_editor_io.py    # Unit tests for file operations
```

**Design Decisions:**
- **QPlainTextEdit**: Chosen over QTextEdit for better performance with large plain-text files and code. It uses a simpler document model optimized for plain text without rich formatting overhead.
- **Separated I/O Logic**: `FileManager` class isolates file operations from GUI code, enabling unit testing without Qt dependencies.
- **Modular Architecture**: UI and logic separation following MVC principles for maintainability.

### Testing
Validated using **pytest**. Run tests with:
```
set PYTHONPATH=src && python -m pytest tests/ -v
```

---
# --------------------------------------- AI Generated ----------------------------

R2:


R3:
