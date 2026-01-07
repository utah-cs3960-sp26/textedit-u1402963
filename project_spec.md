# Project: Python Qt Text Editor
**Goal:** Build a native, cross-platform text editor using PyQt6.
**Constraints:**
- Framework: PyQt6 (Python)
- Testing: pytest (strictly TDD where possible)
- Style: PEP8, modular architecture (MVC pattern)
- No external libraries for core features.

**Architecture:**
- Separated Logic and UI.
- Use `QPlainTextEdit` for the central widget (better performance than QTextEdit for code).
- Main Window: Standard Menu bar, Status bar, Central Widget.

**Current Goal:** Release 1 (Basic file I/O, UI skeleton, Git setup).