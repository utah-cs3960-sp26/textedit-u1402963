# Optimization Mistakes — What Didn't Work

Record of failed approaches for large-file performance in `_load_chunk` and replace-all,
so future threads don't repeat them.

---

## 1. `_highlight_visible_blocks` with `rehighlightBlock` — NO deferred rehighlight

**Approach:** Skip `rehighlight()` entirely in `_load_chunk`. Instead, manually call
`hl.rehighlightBlock(block)` for only the ~40 visible viewport blocks.

**Why it failed:** Without a full `rehighlight()`, off-screen blocks never get highlighted.
When the user scrolls within the chunk (small internal scroll, not a new chunk load), newly
visible blocks appear without syntax highlighting. There's no Qt mechanism to lazily trigger
`highlightBlock` for blocks that weren't processed by `rehighlight()` — Qt considers them
"done" after `setPlainText`, even though we blocked signals.

**Result:** Scrollbar jump large regressed from P95=24.8ms → P95=95ms (without deferred) or
P95=71.6ms (with deferred, which re-introduced the cascade problem).

---

## 2. `_schedule_incremental_rehighlight` — batched `rehighlightBlock` across frames

**Approach:** After highlighting visible blocks, schedule `rehighlightBlock` in batches of 100
via `QTimer.singleShot(0, ...)` to spread the work across frames.

**Why it failed:** `rehighlightBlock()` is NOT isolated — Qt propagates state changes to
subsequent blocks, causing cascading re-highlighting. Calling it on 100 blocks triggered
processing of many MORE blocks. Each scrollbar jump generated 170 frames instead of 52,
with worst frames at 552ms.

**Result:** Scrollbar jump large P95 went from 24.8ms → 85.4ms. Wall time per run went from
~260ms → ~4900ms.

---

## 3. `_on_scroll_highlight` via `updateRequest` signal — lazy per-block highlighting

**Approach:** Connect to `updateRequest` signal and call `rehighlightBlock` for each newly
visible block (tracked via `_highlighted_blocks` set) when the viewport scrolls.

**Why it failed:** Same root cause as #2 — `rehighlightBlock` cascades to adjacent blocks.
Even highlighting just ~40 visible blocks on each scroll step triggered hundreds of ms of
cascading re-highlighting. Also added overhead to every `updateRequest` signal (fires on
every scroll, resize, etc.).

**Result:** Scrollbar jump large P95 = 256ms. Completely unusable.

---

## 4. Passing large dict through `pyqtSignal(dict, int)` for replace-all

**Approach:** `ReplaceWorker.finished` signal carried `(modifications_dict, count)` as
signal parameters. For 141K+ entry dicts, PyQt6 serializes the dict through its signal-slot
mechanism when crossing thread boundaries.

**Why it failed:** Cross-thread signal delivery serializes Python objects. A 141K-entry dict
takes ~100-150ms to serialize/deserialize through the Qt event system.

**Fix that worked:** Changed signal to `pyqtSignal()` (no args) and stored results as
worker attributes (`worker.modifications`, `worker.count`). Main thread reads directly.

---

## 5. Never clearing `batch_limit` (keeping it permanently active)

**Approach:** After `rehighlight()` with `batch_limit=viewport_lines`, DON'T clear it.
Keep batch_limit active permanently so off-screen blocks never get re-highlighted.

**Why it failed:** Blocks scrolled into view (within the same chunk, not a new chunk load)
had no syntax highlighting. The batch_limit prevents `highlightBlock` from running on
those blocks during any subsequent Qt-internal re-highlighting pass.

**Result:** Visual regression — unhighlighted code when scrolling within a chunk. Also
no performance improvement for the benchmarks that test scrolling since they scroll
WITHIN loaded content (medium scroll) and need highlighting for correct display.

---

## 6. `setDocument` with `batch_limit=100` as deferred rehighlight

**Approach:** After `_load_chunk`, schedule `QTimer.singleShot(0, _deferred_rehighlight)`
which calls `hl.setDocument(self.document())` with `batch_limit=100` + `_suppress_rehighlight`.

**Why it failed:** `setDocument` triggers a full `rehighlight` internally at the Qt C++ level.
Even with batch_limit=100, Qt still iterates all 1000 blocks (fast no-op for 900, but the 100
that DO get processed cause state propagation cascades). This added a 100-200ms spike in the
frame AFTER `_load_chunk`.

**Result:** Scrollbar jump large went from P95=24.8ms → P95=82.7ms.

---

## Key Insight

The fundamental constraint is that Qt's `QSyntaxHighlighter` is designed around full-document
highlighting. There's no efficient way to highlight "just these 40 blocks" — any block-level
highlighting API (`rehighlightBlock`) triggers state propagation cascades.

The best approach found so far is:
1. `set_batch_limit(viewport_lines + 10)` before `rehighlight()` — caps actual tokenizer work
2. `QTimer.singleShot(0, lambda: hl.set_batch_limit(-1))` — clears limit for scroll
3. The remaining blocks get highlighted in the next frame when batch_limit is cleared

This works well for scrollbar jumps (P95=24.8ms) but the "next frame" cascade still causes
100-200ms spikes for large replace (because the replace signal delivery + cascade happen in
consecutive frames that the benchmark captures).

The **remaining bottleneck** for large replace is that the `QTimer.singleShot(0, ...)` clearing
the batch_limit causes ~960 blocks to be re-highlighted in a single subsequent frame.

---

## 7. Resetting `_batch_count` in `_on_virtual_scroll` instead of clearing batch_limit

**Approach:** In virtual mode, never clear `batch_limit` to -1 via `QTimer.singleShot`.
Instead, reset `_batch_count = 0` in `_on_virtual_scroll` so each scroll step allows
another viewport's worth of blocks to be highlighted.

**Why it failed:** The scrollbar jump benchmark scrolls rapidly — each jump triggers
`_on_virtual_scroll`, which resets `_batch_count`, allowing more blocks to be highlighted
in that frame's paint. Since jumps happen in quick succession, this caused multiple
partial re-highlight passes per frame, making the aggregate worse. Scrollbar jump large
went from P95=24.8ms → P95=54.9ms. Medium scrollbar jump also regressed.

**Result:** 5 failures (up from 2-3). Strictly worse than the `QTimer.singleShot` approach.
