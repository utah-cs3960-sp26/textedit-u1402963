# Open Performance Issues

Benchmark run: latest commit on `speed-3` branch.
**9 / 15 passed, 4 failed, 2 skipped.** Target: P95 ≤ 16.67ms (60fps), large files ≤ 33ms (30fps).

---

## 1. Large File Replace — P95: 7,777ms (target ≤ 33ms) 🔴 CRITICAL

**What happens:** `VirtualDocument.replace_all()` in `src/editor/models/virtual_document.py:239-270` iterates all 1,377,419 lines synchronously on the main thread. Each line calls `get_line()` (mmap decode) then `re.subn()`. The entire operation blocks the GUI for ~8 seconds.

**Why it's slow:** Pure Python loop over 1.37M lines with per-line string decode + regex. This is inherently O(n) and cannot be done in one frame.

**Fix:** Move `replace_all` to a background `QThread` worker (same pattern as `FindWorker` in `src/editor/find_replace.py:22-48`). The worker builds a replacement dict off the main thread, then emits a `finished` signal. The main thread swaps the dict into `_modified_lines` and reloads the current chunk. Use a `threading.Lock` on `_modified_lines` to prevent concurrent access.

**Match count:** Only needed after completion — the worker can return the count with the `finished` signal.

---

## 2. Large File Open — P95: 38ms (target ≤ 33ms) 🟡 MEDIUM

**What happens:** `test_gui_timing_open.py` calls `enter_virtual_mode()` + deferred `_setup_hl()`. The worst frames are 62-77ms, coming from `enter_virtual_mode` → `_load_chunk(0)` which calls `super().setPlainText()` for 1000 lines AND `hl.rehighlight()` in one frame.

**Where:** `src/editor/code_editor.py` `_load_chunk()` lines 530-553, specifically line 540: `hl.rehighlight()` runs on all 1000 blocks.

**Fix:** In `_load_chunk`, don't call `hl.rehighlight()` after enabling the highlighter. Instead set a tight `batch_limit` (e.g. 30 — just the visible viewport) and let Qt highlight blocks lazily as they paint. The remaining blocks get highlighted when scrolled into view.

---

## 3. Medium Scroll — P95: 17.0ms (target ≤ 16.67ms) 🟡 BORDERLINE

**What happens:** Each `PageDown`/`PageUp` dispatches a key event through `notify()`. With the full 8,739-line document loaded (via deferred chunks), the `line_number_area_paint_event()` and viewport repaint run per scroll. The P95 is 17.0ms — just 0.3ms over budget.

**Where:** `src/editor/code_editor.py` `line_number_area_paint_event()` lines 143-175. Also `src/editor/highlighters/document_highlighter.py` `highlightBlock()` runs on newly-visible blocks during scroll.

**Fix options:**
- Cache `blockBoundingRect()` results per block (currently recomputed every paint)
- Throttle `_update_line_number_area` to at most once per 16ms
- Profile `highlightBlock()` to see if tokenizer regex is the bottleneck on visible blocks

---

## 4. Small Scrollbar Jump — P95: 17.2ms (target ≤ 16.67ms) 🟡 BORDERLINE

**What happens:** `scrollbar.setValue()` triggers immediate viewport repaint + line number area repaint via `_update_line_number_area`. Even on 173 lines, the worst frames hit 20ms.

**Where:** `src/editor/code_editor.py` `_update_line_number_area()` line 129, triggered by `updateRequest` signal.

**Fix:** Same as scroll — this shares the repaint codepath. Likely the same fix (throttling or caching) resolves both issues.

---

## Architecture Notes

### What's already working well
- **Deferred chunk loading** (`setPlainText` / `bulk_set_text`): splits document loading into 500-line chunks across frames. This is why open/replace pass for small and medium.
- **`BulkReplaceCommand`**: clean undo/redo for replace-all using `bulk_set_text()` (doesn't clear undo stack, doesn't use expensive cursor operations).
- **Virtual mode** for large files: mmap-backed `VirtualDocument` with 1000-line chunks.
- **`FindWorker`**: background thread pattern for `find_all` in virtual mode — reuse this for `replace_all`.

### Libraries used
- **PyQt6** — UI framework (QPlainTextEdit, QSyntaxHighlighter, QThread, QTimer)
- **mmap** (stdlib) — memory-mapped file access for large files
- **re** (stdlib) — regex for find/replace and syntax highlighting
- **threading** (stdlib) — `threading.Event` for abort flags in `FindWorker`

---

## Suggested File Cleanup

| File | Status | Reason |
|---|---|---|
| `OPTIMIZATION_PLAN.md` | **Remove** | Superseded by this file. Contains stale baseline numbers (pre-optimization) and phases that are partially complete. |
| `TIMING.md` | **Remove or update** | Contains two snapshots of timing data that are now outdated. The benchmark itself (`benchmarks/run.py`) produces current numbers on each run. If keeping for historical record, rename to `TIMING_HISTORY.md`. |
| `COVERAGE.md` | **Keep** | Still accurate — documents test coverage approach. |
| `README.md` | **Keep** | Project readme with release notes. |
| `project_spec.md` | **Keep** | Assignment specification. |
