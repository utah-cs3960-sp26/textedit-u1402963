# Optimization Plan: 60 FPS Target

## Current Baseline (Post-Benchmark Fix)

| Test | Status | P95 | Max | Frames > 16.67ms |
|---|---|---|---|---|
| Open small (173 lines) | ❌ FAIL | 17.2ms | 28.9ms | 7/92 |
| Open medium (8,739 lines) | ❌ FAIL | 382.6ms | 644.9ms | 10/98 |
| Open large (1,377,419 lines) | ⏭ SKIPPED | — | — | — |
| Replace small (19 matches) | ❌ FAIL | 22.5ms | 28.4ms | 4/38 |
| Replace medium (1,186 matches) | ❌ FAIL | 682.3ms | 801.8ms | 8/48 |
| Replace large (668,753 matches) | ⏭ SKIPPED | — | — | — |
| Scroll small | ✅ PASS | 11.9ms | 38.4ms | 54/1341 |
| Scroll medium | ❌ FAIL | 24.6ms | 63.2ms | 250/1800 |
| Scroll large | ⏭ SKIPPED | — | — | — |
| Scrollbar jump small | ❌ FAIL | 31.5ms | 45.9ms | 28/150 |
| Scrollbar jump medium | ❌ FAIL | 17.8ms | 20.3ms | 16/150 |
| Scrollbar jump large | ⏭ SKIPPED | — | — | — |
| Memory small | ✅ PASS | — | — | +5.0 MB |
| Memory medium | ✅ PASS | — | — | +8.6 MB |
| Memory large | ✅ PASS | — | — | +1672.7 MB (<3072) |

**Passing: 3/12 performance tests. Large tests all skipped (gated on small/medium passing).**

---

## Root Cause Analysis

### 1. Open — medium takes 400-650ms per frame
`setPlainText()` triggers two expensive synchronous operations in a single event:
- **Full document layout** — Qt rebuilds the internal block/line structure for all 8,739 blocks
- **Full rehighlight** — `DocumentHighlighter.highlightBlock()` runs on every single block, each calling the tokenizer with regex matching

For the large file, this would take minutes.

### 2. Replace All — medium takes 500-800ms per frame
`replace_all()` in `find_replace.py` (line 445-484):
1. Does the text replacement via Python string ops (fast, ~ms)
2. Then calls `cursor.beginEditBlock()` / `cursor.select(Document)` / `cursor.insertText(new_text)` — this replaces the entire document through Qt's cursor API, which triggers full relayout + full rehighlight (same cost as open, but on modified text)
3. Then calls `_update_match_count()` which re-scans the entire document for matches (unnecessary — they've all been replaced)

### 3. Scroll medium — P95 = 24.6ms
Each Page Down/Up dispatches a key event through `notify()`. The `line_number_area_paint_event()` and viewport repaint run per-scroll. With 8,739 lines loaded, Qt's internal block geometry lookups slow down proportionally. Lines in medium.txt may also be long, making text layout expensive per visible block.

### 4. Scrollbar jumps — even small file P95 = 31.5ms
`scrollbar.setValue()` triggers an immediate viewport repaint. The `_update_line_number_area` handler fires on every `updateRequest` signal. Each jump causes a full visible-region repaint cycle. The P95 of 31.5ms on 173 lines suggests something in the repaint path is unexpectedly expensive (possibly the `blockBoundingGeometry()` / `blockBoundingRect()` calls, or the highlighter re-running on visible blocks).

---

## Optimization Plan

### Phase 1: Disable Highlighting During Bulk Operations (HIGH IMPACT)
**Target: Open and Replace All for small/medium**

The single biggest cost is `highlightBlock()` running on every block during `setPlainText()`. The fix:

1. **In `CodeEditor.setPlainText()`**: Detach the highlighter before setting text, reattach after. Only re-highlight the visible viewport.
   ```python
   def setPlainText(self, text: str):
       self._flush_pending_insert()
       self._undo_stack.clear()
       # Detach highlighter to prevent per-block highlighting
       highlighter = self.parent()  # get window to access highlighter
       # ... detach, set text, reattach, rehighlight visible only
       super().setPlainText(text)
   ```

2. **In `FindReplaceBar.replace_all()`**: Use `setPlainText()` instead of cursor edit block operations. The cursor approach triggers the same rehighlight cost plus additional edit-tracking overhead. Since we're replacing the entire document anyway, `setPlainText()` is semantically equivalent and can benefit from the same highlighting optimization.

3. **Remove the `_update_match_count()` call** at the end of `replace_all()` — after replacing all occurrences, re-scanning is wasteful. Just set the count to 0 and clear highlights.

**Expected impact:** Open medium should drop from ~500ms to ~20-50ms. Replace medium should drop similarly.

### Phase 2: Optimize Line Number & Scroll Repaints (MEDIUM IMPACT)
**Target: Scroll medium, scrollbar jumps all sizes**

1. **Cache `line_number_area_width()`** — currently recalculated on every `updateRequest` (calls `blockCount()` and `QFontMetrics` each time). Cache the value and only recompute when `blockCountChanged` fires.

2. **Throttle `_update_line_number_area`** — the `updateRequest` signal fires very frequently during scrolling. Batch updates so the line number area repaints at most once per frame (~16ms).

3. **Investigate `blockBoundingRect()` cost** — if Qt is computing layout for long lines on every call, consider setting a maximum line width or enabling line wrapping for very long lines.

**Expected impact:** Scrollbar jump P95 should drop from ~31ms to <16ms. Scroll medium P95 should drop from ~25ms to <16ms.

### Phase 3: Large File Support (HIGH IMPACT)
**Target: All large file tests currently skipped**

The virtual document/chunking system already exists (`CHUNK_SIZE = 5000`). The main work:

1. **Ensure open-large goes through virtual mode** — `_open_file_path` already checks `VirtualDocument.is_large_file()`. Verify the benchmark test exercises this path (currently it calls `window.text_edit.setPlainText(large_content)` directly, bypassing virtual mode). **The test itself may need updating** to call `window._open_file_path()` or load via virtual mode.

2. **Ensure replace-all-large uses virtual mode path** — `_replace_all_virtual()` exists. Verify the benchmark exercises this.

3. **Ensure scroll-large works through virtual scrollbar** — the chunk-loading system handles this via `_on_virtual_scroll`.

4. **Ensure memory stays under 3 GiB** — currently at 1.67 GB for large file, well within limit.

**Expected impact:** Large file tests should become runnable and pass, since only 5,000 lines are loaded at a time.

### Phase 4: Stretch Optimizations (LOW IMPACT)
Only pursue if Phase 1-3 don't reach the target:

1. **Visible-only highlighting** — instead of rehighlighting the entire document, only highlight blocks that are currently visible. Use a viewport-aware approach: highlight on `paintEvent` or `updateRequest` for visible blocks only.

2. **Deferred highlighting** — use `QTimer.singleShot(0, ...)` to highlight blocks in small batches across multiple event loop iterations, keeping each frame under 16ms.

3. **Reduce tokenizer overhead** — profile the `tokenize_line()` call in `DocumentHighlighter.highlightBlock()`. If regex compilation is happening per-call, pre-compile patterns. If the plain-text tokenizer is doing unnecessary work, short-circuit it.

4. **Disable line number area during bulk operations** — similar to the highlighter detach, hide the line number area during `setPlainText()` to avoid geometry calculations.

---

## Execution Order

```
Phase 1 → run benchmarks → Phase 2 → run benchmarks → Phase 3 → run benchmarks → Phase 4 (if needed)
```

Each phase should be committed separately with before/after timing data recorded in `TIMING.md`.

## Success Criteria

All 15 benchmark tests pass:
- Every aggregate P95 ≤ 16.67ms
- Large file memory < 3 GiB
- All operations on large.txt complete within 60 seconds
