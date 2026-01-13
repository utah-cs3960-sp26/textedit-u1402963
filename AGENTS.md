# AGENTS.md - FART Text Editor

## Project Overview
**FART (Fast Async Runtime Text-editor)** is a cross-platform text editor built with PyQt6, inspired by Sublime Text. This is a class project for CS3960.

## Commands

### Run the application
```bash
python src/main.py
```

### Run tests
```bash
pytest
```

### Run tests with coverage
```bash
pytest --cov=src
```

## Code Style & Conventions

- **Language:** Python 3.10+
- **Style:** PEP8 compliant
- **Architecture:** MVC pattern with separated UI and logic
- **Framework:** PyQt6 only — no other UI/editor libraries
- **Testing:** pytest with Test Driven Development approach

### Naming Conventions
- Classes: `PascalCase` (e.g., `CodeEditor`, `FileManager`)
- Functions/methods: `snake_case` (e.g., `open_file`, `get_line_count`)
- Constants: `UPPER_SNAKE_CASE`
- Private methods: prefix with `_` (e.g., `_update_line_numbers`)

### File Organization
- UI components go in `src/editor/`
- Controllers go in `src/editor/controllers/`
- Data models go in `src/editor/models/`
- Language highlighters go in `src/editor/highlighters/`
- Tests mirror source structure in `tests/`

## Architecture Notes

### Central Widget
Use `QPlainTextEdit` (not `QTextEdit`) for the editor — better performance for code.

### Syntax Highlighting
- Base class: `highlighter.py`
- Language-specific highlighters inherit from base
- Language detection by file extension, with fallback pattern matching

### Undo/Redo
- Custom command stack in `undo_commands.py`
- Limited to 100 revisions to prevent memory bloat
- Ensure undo/redo stack are cleared when switching files

## Current Release: R2

### R2 Features
- Fix shift+enter un-numbered newline bug
- "Save as" dialogue
- File tree explorer with collapsible folders
- Multi-file tab support
- Tab management (close, switch, drag-to-reorder)

### R3 Goals (Next Week)
- Split views (horizontal/vertical)
- Stretch: auto-indent, bracket matching, custom themes

## Testing Guidelines

- Write tests BEFORE implementation
- ASK QUESTIONS to CLARIFY EXPECTED BEHAVIOR when unclear or unsure
- Test file naming: `test_<module>.py`
- Use pytest fixtures for common setup
- Mock file I/O operations in tests

## UI Inspiration
- Sublime Text aesthetics and workflow
- Clean, minimal, polished interface
- Keyboard-driven with discoverable shortcuts

## Important Files
- `project_spec.md` — Full project specification and release plan
- `src/main.py` — Application entry point
- `src/editor/window.py` — Main window UI
- `src/editor/code_editor.py` — Core editor widget with line numbers
