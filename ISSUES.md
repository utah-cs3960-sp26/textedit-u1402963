# Open Performance Issues

Benchmark run: commit `7388dcd` on `speed-3` branch. All tests run (no gating).
**10 / 15 passed, 5 failed.** Target: P95 ≤ 16.67ms (60fps), large files ≤ 33ms (30fps).

---

## 1. Large File Replace — timed out (target ≤ 33ms) 🔴 CRITICAL

**What happens:** `VirtualDocument.replace_all()` in `src/editor/models/virtual_document.py:239-270` iterates all 1,377,419 lines synchronously on the main thread. Each line calls `get_line()` (mmap decode) then `re.subn()`. Blocks the GUI for ~8 seconds, exceeding the 15s test timeout.

**Why it's slow:** Pure Python loop over 1.37M lines with per-line string decode + regex.

**Fix:** Move `replace_all` to a background `QThread` worker (same pattern as `FindWorker` in `src/editor/find_replace.py:22-48`). Worker builds a replacement dict off the main thread, emits `finished` signal with count. Main thread swaps dict into `_modified_lines` and reloads current chunk. Use `threading.Lock` on `_modified_lines`.

---

## 2. Large Scrollbar Jump — P95: 97.6ms (target ≤ 33ms) 🔴 HIGH

**What happens:** Each scrollbar jump calls `_load_chunk()` which does `super().setPlainText()` for 1000 lines AND `hl.rehighlight()` synchronously. With 6 jumps, the worst frames are 100-140ms.

**Where:** `src/editor/code_editor.py` `_load_chunk()` lines 530-553. Line 540: `hl.rehighlight()` runs the tokenizer on all 1000 chunk blocks in one frame.

**Fix:** Don't call `hl.rehighlight()` after `_load_chunk`. Instead set `batch_limit` to viewport size (~30) and let Qt lazily highlight visible blocks on paint. Remaining blocks highlight when scrolled into view.

---

## 3. Medium Scroll — P95: 19.7ms (target ≤ 16.67ms) 🟡 MEDIUM

**What happens:** Each PageDown/PageUp triggers viewport repaint + line number repaint + `highlightBlock` on newly-visible blocks. With 8,739 lines loaded, Qt's internal block geometry lookups are slightly slow.

**Where:** `src/editor/code_editor.py` `line_number_area_paint_event()` and `src/editor/highlighters/document_highlighter.py` `highlightBlock()`.

**Fix options:**
- Throttle `_update_line_number_area` to coalesce rapid scroll repaints
- Profile whether `highlightBlock` tokenizer or `blockBoundingRect` is the bottleneck
- Consider reducing `_LOAD_CHUNK_SIZE` for deferred loading so less of the document is in Qt's block model

---

## 4. Small/Medium Scrollbar Jump — P95: 17.9ms / 18.0ms (target ≤ 16.67ms) 🟡 BORDERLINE

**What happens:** `scrollbar.setValue()` triggers immediate viewport + line number repaint. Even on 173 lines, worst frames hit 20-24ms. Shares repaint codepath with scroll.

**Where:** Same as scroll — `_update_line_number_area()` and `line_number_area_paint_event()`.

**Fix:** Same as medium scroll — likely the same optimization resolves both.

---

## Architecture Notes

### What's working well
- **Deferred chunk loading** (`_load_text`): shared by `setPlainText` and `bulk_set_text`, splits documents into 500-line chunks across frames
- **`BulkReplaceCommand`**: clean undo/redo for replace-all using `bulk_set_text()` — no flags, no cursor overhead
- **Virtual mode**: mmap-backed `VirtualDocument` with 1000-line chunks for large files
- **`FindWorker`**: background thread for `find_all` in virtual mode — reuse pattern for `replace_all`

### Libraries used
- **PyQt6** — UI framework (QPlainTextEdit, QSyntaxHighlighter, QThread, QTimer)
- **mmap** (stdlib) — memory-mapped file access for large files
- **re** (stdlib) — regex for find/replace and syntax highlighting
- **threading** (stdlib) — `threading.Event` for abort flags in `FindWorker`
