# Should Fix (Polish)

Fix these if you have time after the must-fix items. They add polish.

---

## 1. Add "Save As" Menu Option
**Time:** ~30 minutes

**Problem:** Can only save to current file. "Save As" is expected.

**Fix:** Add `save_file_as()` that always shows dialog, update menu.

---

## 2. Status Shows "Saved" for New Files  
**Time:** ~10 minutes  
**Location:** `src/editor/window.py`

**Problem:** New empty document shows "Saved" even though it was never saved. Confusing.

**Fix:** Check if `file_path` is None and show "New" or "Untitled" instead.

---

## 3. Add Python Decorators Highlighting
**Time:** ~5 minutes  
**Location:** `src/editor/highlighters/python_hl.py`

**Problem:** `@decorator` not highlighted. Common Python syntax.

**Fix:** Add one line:
```python
self.add_pattern(r"@\w+(\.\w+)*", "yellow")
```

---

## 4. Add F-string Support  
**Time:** ~10 minutes  
**Location:** `src/editor/highlighters/python_hl.py`

**Problem:** `f"..."`, `r"..."`, `b"..."` not highlighted.

**Fix:** Add patterns for prefixed strings.

---

## 5. Add Line/Column to Status Bar
**Time:** ~30 minutes

**Problem:** No indicator of current cursor position.

**Fix:** Connect to `cursorPositionChanged` signal, update status label with "Ln X, Col Y".

---

## 6. Current Line Highlight
**Time:** ~30 minutes  
**Location:** `src/editor/code_editor.py`

**Problem:** Hard to see which line cursor is on.

**Fix:** Override `cursorPositionChanged` to highlight current line with light background.

---

## 7. Markdown Code Fences
**Time:** ~1 hour  
**Location:** `src/editor/highlighters/markdown_hl.py`

**Problem:** ` ```code``` ` blocks not highlighted. Common in markdown.

---

## 8. HTML Multi-line Comments
**Time:** ~1 hour  
**Location:** `src/editor/highlighters/html_hl.py`

**Problem:** `<!-- multi-line -->` comments broken.
