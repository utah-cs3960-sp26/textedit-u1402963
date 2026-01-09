# QA Report Summary (Adjusted for Assignment Scope)

**Application:** TextEdit 9000  
**Course:** CS 3960 Homework 1  
**Due:** January 23  
**Overall Grade:** B+ (Good foundation, needs polish for demo)

---

## Assignment Checklist

### Required Features
- [x] Native, cross-platform (PyQt6) ✅
- [x] pytest for testing ✅ (106 tests passing)
- [x] Editing, selection ✅
- [x] Opening files ✅
- [x] Saving files ✅
- [ ] Keyboard shortcuts (partial - needs menu visibility)
- [x] **Feature 1: Multi-language syntax highlighting** ✅

### Pick Second Feature (choose one):
- [ ] Find and replace ← **Recommended** (high impact, moderate effort)
- [ ] Automatic indentation + bracket matching
- [ ] Custom fonts, colors, keyboard shortcuts
- [ ] Multiple cursors / rectangular selection
- [ ] Multi-file support / tabs
- [ ] File tree explorer
- [ ] Jump to definition

---

## Issue Files (Reprioritized for Assignment)

1. **[01-must-fix-for-demo.md](01-must-fix-for-demo.md)** - Will affect grading if not fixed
2. **[02-should-fix.md](02-should-fix.md)** - Polish items, time permitting
3. **[03-nice-to-have.md](03-nice-to-have.md)** - Ignore unless you have extra time
4. **[04-out-of-scope.md](04-out-of-scope.md)** - Enterprise concerns, not relevant

---

## Quick Stats

| Priority | Count | Time Estimate |
|----------|-------|---------------|
| Must Fix | 6 | ~4-6 hours |
| Should Fix | 8 | ~4-8 hours |
| Nice to Have | 10 | ~8+ hours |
| Out of Scope | 38 | N/A |

---

## Top Priority for Demo (Jan 21)

1. **Add "New File"** - Professors will try this
2. **Fix multi-line comments** - Very visible bug during demo
3. **Add Edit menu** (Undo/Redo/Cut/Copy/Paste) - Expected by graders
4. **Pick & implement second feature** (Find/Replace recommended)

---

## What's Already Working Well ✅

- All 106 tests pass
- Clean MVC-ish architecture
- 8 language highlighters
- Language auto-detection
- Line numbers
- Unsaved changes tracking with visual indicator
- File open/save with error handling
- Window title shows filename and modified state
