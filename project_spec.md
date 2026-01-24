# FART - Fast Async Runtime Text-editor

A native, cross-platform text editor built with PyQt6, inspired by Sublime Text.

## Constraints
- **Framework:** PyQt6 (Python)
- **Testing:** pytest (TDD approach)
- **Style:** PEP8, modular MVC architecture
- **No external libraries** for core features
- **Cross-platform:** Windows, macOS, Linux

## Architecture
- **Pattern:** MVC with separated logic and UI
- **Central Widget:** `QPlainTextEdit` (optimized for code)
- **Layout:** Menu bar, toolbar, status bar, central editor area
- **UI Inspiration:** Sublime Text

## Required Features (pick 2+)

| Feature | Status | Release |
|---------|--------|---------|
| Multi-language syntax highlighting | ✅ Done (needs multi-line fix) | R1 |
| File tree explorer (collapsible) | 🔲 Planned | R2 |
| Multi-file tabs + split views | 🔲 Planned | R2/R3 |
| Auto-indent + bracket/quote matching | 🔲 Stretch | R3+ |
| Custom fonts/colors/shortcuts | 🔲 Stretch | R3+ |

## Core Features (required)
- [x] Text editing, selection, cursor movement
- [x] Open/Save files (Ctrl+O / Ctrl+S)
- [x] New file creation (Ctrl+N)
- [x] Unsaved changes indicator
- [x] Undo/Redo (100 revision limit)
- [x] Edit menu (Undo/Redo/Cut/Copy/Paste/Select All)
- [x] Line numbers gutter
- [x] Keyboard shortcuts
- [ ] Save As option
- [ ] Help menu with shortcut reference
- [ ] Line/column position in status bar

## Known Bugs (Must Fix for R2 Demo)
- [ ] Line number gutter edge case crash (`code_editor.py` line 114)
- [ ] Multi-line block comments broken in C/C++/Java highlighters
- [ ] Python triple-quoted strings not highlighted
- [ ] Python decorators (@) not highlighted
- [ ] F-string/r-string/b-string prefixes not highlighted

## Release Plan

### R1 - Basic Editor Foundation + Syntax Highlighting ✅
- Basic UI skeleton (MainWindow, menus, toolbar, status bar)
- File I/O (open, save, new file)
- Saved/unsaved state tracking
- Syntax highlighting framework with language-specific highlighters
- Line number gutter
- Undo/redo with revision limit

### R2 - File Tree & Tabs (In Progress) — Demo Jan 21

**Must Fix Before Demo:**
- [ ] Line number gutter bug fix (`code_editor.py` line 114)
- [ ] Multi-line comment highlighting (C/C++/Java)
- [ ] Python triple-quoted string highlighting


## Project Structure
```
src/
├── main.py                 # Application entry point
└── editor/
    ├── window.py           # MainWindow (UI layer)
    ├── code_editor.py      # CodeEditor with line numbers
    ├── file_manager.py     # FileManager (I/O logic)
    ├── undo_commands.py    # Undo/redo command stack
    ├── highlighter.py      # Base syntax highlighter
    ├── controllers/        # MVC controllers
    ├── highlighters/       # Language-specific highlighters
    └── models/             # Data models
tests/
├── test_code_editor.py     # Line number tests
├── test_editor_io.py       # File I/O tests
└── test_highlighter.py     # Syntax highlighting tests
```
