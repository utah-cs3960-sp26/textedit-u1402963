# textedit-u1402963
Text editor made using AI assistance for CS3960



# --------------------------------------- AI Generated ----------------------------
## Release R1 - Basic Editor Foundation

### Features
- **File Open** (Ctrl+O): Load text files with native file dialog
- **File Save** (Ctrl+S): Save content to disk with file dialog
- **Basic UI**: Main window with menu bar and text editing area
- **Line Numbers**: Dynamic line number gutter that scales with document size
- **Python Syntax Highlighting**: Keywords highlighted in bold cyan
- **Error Handling**: User-friendly error messages for file operations

### Architecture

**Project Structure:**
```
src/
├── main.py              # Application entry point
└── editor/
    ├── window.py        # MainWindow (UI layer)
    ├── code_editor.py   # CodeEditor with line numbers
    ├── highlighter.py   # PythonHighlighter (syntax highlighting)
    └── file_manager.py  # FileManager (I/O logic)
tests/
├── test_code_editor.py  # Line number tests
├── test_editor_io.py    # File I/O tests
└── test_highlighter.py  # Syntax highlighting tests
```

**Design Decisions:**
- **QPlainTextEdit**: Chosen over QTextEdit for better performance with large plain-text files and code. It uses a simpler document model optimized for plain text without rich formatting overhead.
- **CodeEditor**: Custom widget extending QPlainTextEdit with a LineNumberArea widget for displaying line numbers.
- **PythonHighlighter**: Uses QSyntaxHighlighter with regex patterns to highlight Python keywords.
- **Separated I/O Logic**: `FileManager` class isolates file operations from GUI code, enabling unit testing without Qt dependencies.
- **Modular Architecture**: UI and logic separation following MVC principles for maintainability.

### Testing
Validated using **pytest** (32 tests). Run tests with:
```
set PYTHONPATH=src && python -m pytest tests/ -v
```

---
# --------------------------------------- AI Generated ----------------------------

R2:


R3:
