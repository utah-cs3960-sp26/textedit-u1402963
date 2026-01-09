# Must Fix for Demo

These issues **will be noticed by graders** during the in-class demo. Fix before Jan 21.

---

## 1. Missing "New File" Menu Action
**Time:** ~30 minutes  
**Location:** `src/editor/window.py`

**Problem:** No way to create a new document. Graders will look for File → New.

**Fix:**
```python
# In _setup_menu(), add before open_action:
new_action = QAction("&New", self)
new_action.setShortcut("Ctrl+N")
new_action.triggered.connect(self.new_file)
file_menu.addAction(new_action)

# Add method:
def new_file(self):
    if self._document.is_modified:
        result = self._prompt_save_changes()
        if result == "save":
            self.save_file()
            if self._document.is_modified:
                return
        elif result == "cancel":
            return
    
    self.text_edit.clear()
    self._document.reset()
    self._setup_highlighter()
    self._update_status()
```

---

## 2. Missing Edit Menu
**Time:** ~20 minutes  
**Location:** `src/editor/window.py`

**Problem:** No Edit menu with Undo/Redo/Cut/Copy/Paste. Shortcuts work but aren't discoverable.

**Fix:** Add to `_setup_menu()`:
```python
edit_menu = menu_bar.addMenu("&Edit")

undo_action = QAction("&Undo", self)
undo_action.setShortcut("Ctrl+Z")
undo_action.triggered.connect(self.text_edit.undo)
edit_menu.addAction(undo_action)

redo_action = QAction("&Redo", self)
redo_action.setShortcut("Ctrl+Y")
redo_action.triggered.connect(self.text_edit.redo)
edit_menu.addAction(redo_action)

edit_menu.addSeparator()

cut_action = QAction("Cu&t", self)
cut_action.setShortcut("Ctrl+X")
cut_action.triggered.connect(self.text_edit.cut)
edit_menu.addAction(cut_action)

copy_action = QAction("&Copy", self)
copy_action.setShortcut("Ctrl+C")
copy_action.triggered.connect(self.text_edit.copy)
edit_menu.addAction(copy_action)

paste_action = QAction("&Paste", self)
paste_action.setShortcut("Ctrl+V")
paste_action.triggered.connect(self.text_edit.paste)
edit_menu.addAction(paste_action)

edit_menu.addSeparator()

select_all_action = QAction("Select &All", self)
select_all_action.setShortcut("Ctrl+A")
select_all_action.triggered.connect(self.text_edit.selectAll)
edit_menu.addAction(select_all_action)
```

---

## 3. Multi-line Block Comments Broken
**Time:** ~2 hours  
**Location:** `src/editor/highlighters/c_hl.py`, `cpp_hl.py`, `java_hl.py`

**Problem:** If you demo C/C++/Java code, multi-line `/* comments */` won't highlight correctly. Very visible during demo.

**Root Cause:** Current pattern `/\*.*?\*/` only works for single-line comments.

**Fix:** Override `highlightBlock()` with state tracking. See PyQt documentation for `setCurrentBlockState()`.

---

## 4. Python Triple-Quoted Strings Broken
**Time:** ~1 hour  
**Location:** `src/editor/highlighters/python_hl.py`

**Problem:** If you demo Python code with docstrings, they won't highlight correctly.

**Same fix approach as #3** - implement state tracking for multi-line strings.

---

## 5. Second Required Feature Missing
**Time:** ~4-8 hours  
**Location:** N/A

**Problem:** Assignment requires 2 features from the list. You have syntax highlighting. Pick and implement one more.

**Recommended: Find and Replace**
- High visibility during demo
- Moderate complexity
- Can be basic (single file, no regex)

**Alternative: Auto-indent + Bracket Matching**
- Lower effort
- Good for code editing demo

---

## 6. Line Number Gutter Bug
**Time:** ~15 minutes  
**Location:** `src/editor/code_editor.py` lines 76-78

**Problem:** Potential crash/glitch with line numbers on edge cases.

**Fix:**
```python
# Change this:
block = block.next()
top = bottom
bottom = top + int(self.blockBoundingRect(block).height())

# To this:
block = block.next()
if not block.isValid():
    break
top = bottom
bottom = top + int(self.blockBoundingRect(block).height())
```
