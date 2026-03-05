# Open Performance Issues

---

## 1. Large File Replace — P95: 127-170ms (target ≤ 33ms) 🔴 CRITICAL

**Status:** Partially fixed. Replace now runs on background thread (`ReplaceWorker`), signal is
lightweight (`pyqtSignal()` with no args), and dict swap is O(1). The `_load_chunk` call in
`_on_replace_finished` takes only ~22ms. **The remaining 100-150ms spike comes from the
`QTimer.singleShot(0, lambda: hl.set_batch_limit(-1))` in `_load_chunk` — when the batch
limit is cleared in the next frame, Qt cascades re-highlighting of ~960 off-screen blocks.**

**Where:** `src/editor/code_editor.py` `_load_chunk()` line 556 — the deferred batch_limit clear.

**What was tried and failed:** See MISTAKES.md for 7 failed approaches including:
- `rehighlightBlock` per visible block (cascades to adjacent blocks)
- Incremental batched rehighlighting (same cascade problem)
- Never clearing batch_limit (visual regression)
- Resetting `_batch_count` on scroll (worse performance)

**Remaining fix ideas:**
- Reduce `CHUNK_SIZE` from 1000 to e.g. 200 — fewer blocks to cascade through
- Detach highlighter entirely during virtual mode and use a custom paint overlay
- Use `QSyntaxHighlighter.setDocument(None)` to detach, load text, reattach with batch_limit

---

## 2. Large Scrollbar Jump — P95: 24.8ms (best) / 55ms (worst) (target ≤ 33ms) 🔴 HIGH

**Status:** Significantly improved by batch-limited `rehighlight()` in `_load_chunk`.
Best run: P95=24.8ms ✅ PASS. But inconsistent — worst runs hit P95=55ms due to the same
`QTimer.singleShot` batch_limit cascade as issue #1.

**Where:** Same as #1 — `_load_chunk()` deferred batch_limit clear.

**Fix:** Same as #1 — solving the cascade problem fixes both issues.

---

## ~~3. Medium Scroll — P95: 19.7ms (target ≤ 16.67ms)~~ 🟢 MOSTLY FIXED

**Status:** Passes in most runs (P95=10.6-15.7ms). Borderline under high system load.

---

## ~~4. Small/Medium Scrollbar Jump~~ 🟢 FIXED

**Status:** Both now pass consistently (S: P95=12.2ms, M: P95=12.1ms).

---

## Architecture Notes

### What's working well
- **Deferred chunk loading** (`_load_text`): shared by `setPlainText` and `bulk_set_text`, splits documents into 500-line chunks across frames
- **`BulkReplaceCommand`**: clean undo/redo for replace-all using `bulk_set_text()` — no flags, no cursor overhead
- **Virtual mode**: mmap-backed `VirtualDocument` with 1000-line chunks for large files
- **`FindWorker`**: background thread for `find_all` in virtual mode
- **`ReplaceWorker`**: background thread for `replace_all` in virtual mode — lightweight signal, results read from worker attributes
- **Batch-limited `rehighlight()`**: highlights only viewport blocks (~50) initially, prevents 300-600ms cascade

### What's not working
- **`QTimer.singleShot(0, lambda: hl.set_batch_limit(-1))`**: clearing batch_limit causes Qt to cascade re-highlight ~960 blocks in one frame. This is the root cause of both remaining failures.
- **`QSyntaxHighlighter` design**: Qt's highlighter is all-or-nothing — no API to highlight "just these blocks" without cascading state propagation to adjacent blocks.

### Libraries used
- **PyQt6** — UI framework (QPlainTextEdit, QSyntaxHighlighter, QThread, QTimer)
- **mmap** (stdlib) — memory-mapped file access for large files
- **re** (stdlib) — regex for find/replace and syntax highlighting
- **threading** (stdlib) — `threading.Event` for abort flags in workers
