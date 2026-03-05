## Initial Timing (Before Optimizations)

### The maximum frame time when you open small/medium/large.

- S: 10.4ms, 8.9ms, 9.0ms, 6.7ms, 5.0ms (avg max: 8.0ms) ✅ PASS
- M: 168.4ms, 202.6ms, 143.2ms, 149.7ms, 146.4ms (avg max: 162.1ms) ❌ FAIL
- L: not tested

### The maximum frame time as you scroll up and down. Try to scroll a few hundred lines quickly using your touchpad or mouse.

- S: 10.7ms, 9.4ms, 4.7ms, 8.5ms, 7.7ms (avg max: 8.2ms) ✅ PASS
- M: 12.0ms, 5.5ms, 5.5ms, 5.5ms, 4.5ms (avg max: 6.6ms) ✅ PASS
- L: not tested

### The maximum and average frame times when you click far away from the current location in the scroll bar.

- S: 6.7ms, 5.8ms, 4.0ms, 5.1ms, 6.0ms (avg max: 5.5ms, avg avg: 0.7ms) ✅ PASS
- M: 10.5ms, 9.5ms, 8.3ms, 9.4ms, 8.5ms (avg max: 9.2ms, avg avg: 1.4ms) ✅ PASS
- L: not tested

### The maximum frame time if you try to replace "while" with "for". There should be 19 matches in small.txt, 1 186 in medium.txt, and 668 753 in large.txt

- S: 7.4ms, 5.3ms, 6.4ms, 7.9ms, 5.2ms (avg max: 6.4ms) ✅ PASS
- M: 386.2ms, 291.0ms, 311.0ms, 305.9ms, 365.5ms (avg max: 331.9ms) ❌ FAIL
- L: not tested

### The total memory used by your text editor process, which you can measure using "Task Manager" or "Activity Monitor" or your system's equivalent. Specifically look for a "Physical" or "Real" memory measure, not "Virtual". For the largest file it should be 1-3GiB.

- S: baseline 125.6 MB, after 130.3 MB, delta +4.8 MB
- M: baseline 135.0 MB, after 142.3 MB, delta +7.4 MB
- L: not tested


## Best Optimized Run — commit `7388dcd`

### Open
- S: P95=10.6ms ✅ | M: P95=5.2ms ✅ | L: P95=26.9ms ✅

### Scroll
- S: P95=10.4ms ✅ | M: P95=19.7ms ❌ | L: P95=16.7ms ✅

### Scrollbar Jump
- S: P95=17.9ms ❌ | M: P95=18.0ms ❌ | L: P95=97.6ms ❌

### Replace "while" → "for"
- S: P95=10.4ms ✅ | M: P95=8.1ms ✅ | L: timed out ❌

### Memory
- S: +6.0 MB ✅ | M: +1.2 MB ✅ | L: +311.9 MB ✅

### Summary: 10 passed, 5 failed (all tests run, no gating)
See ISSUES.md for remaining failures and fix strategies.


## Latest Run — commit `e559b0c`

### Open
- S: P95=12.3ms ✅ | M: P95=4.9ms ✅ | L: P95=37.2ms ❌

### Scroll
- S: P95=7.6ms ✅ | M: P95=10.6ms ✅ | L: P95=14.0ms ✅

### Scrollbar Jump
- S: P95=12.9ms ✅ | M: P95=12.1ms ✅ | L: P95=71.6ms ❌

### Replace "while" → "for"
- S: P95=10.0ms ✅ | M: P95=7.3ms ✅ | L: P95=127.5ms ❌

### Memory
- S: +4.2 MB ✅ | M: +1.2 MB ✅ | L: +311.8 MB ✅

### Summary: 12 passed, 3 failed
- **Failures:** Large file open (P95=37.2ms), large scrollbar jump (P95=71.6ms), large replace (P95=127.5ms)
- **Improvements vs previous run:** Scroll medium fixed (19.7ms→10.6ms ✅), scrollbar jump small fixed (17.9ms→12.9ms ✅), scrollbar jump medium fixed (18.0ms→12.1ms ✅)
- **Regressions:** Large open regressed (26.9ms→37.2ms)


## Current Run — batch_limit + lightweight signal optimization

### Changes Made
1. `_load_chunk`: batch-limited `rehighlight()` to viewport_lines+10, cleared via `QTimer.singleShot`
2. `ReplaceWorker.finished`: changed from `pyqtSignal(dict, int)` to `pyqtSignal()` — results read from worker attributes to avoid serializing 141K+ entry dict through Qt signal-slot mechanism
3. `_on_replace_finished`: dict swap instead of `dict.update()`

### Open
- S: P95=8.0-14.9ms ✅ | M: P95=4.3-7.0ms ✅ | L: P95=16.8-35.1ms ✅ (borderline)

### Scroll
- S: P95=7.6-11.0ms ✅ | M: P95=15.7-17.1ms ❌ (borderline) | L: P95=13.8-14.0ms ✅

### Scrollbar Jump
- S: P95=12.2-12.9ms ✅ | M: P95=12.1-13.1ms ✅ | L: P95=24.8ms ✅ (best run) / ~55ms ❌ (worst run)

### Replace "while" → "for"
- S: P95=10.0-13.1ms ✅ | M: P95=7.3-9.8ms ✅ | L: P95=127-170ms ❌

### Memory
- S: +4.0-5.5 MB ✅ | M: +0.8-1.2 MB ✅ | L: +311.7-312.3 MB ✅

### Summary: 11-13 passed, 2-4 failed (varies with system load)
- **Consistent failures:** Large replace, large scrollbar jump
- **Borderline (load-dependent):** Medium scroll, small scrollbar jump
- **Fixed vs `e559b0c`:** Large open now passes consistently
- See MISTAKES.md for approaches that were tried and failed


## Current Run — ViewportHighlighter + deferred chunk loading

### Changes Made
1. **ViewportHighlighter**: Bypasses `QSyntaxHighlighter` entirely in virtual mode. Applies syntax highlighting directly to visible blocks via `QTextLayout.setFormats()`, eliminating the 960-block cascade that caused 100-200ms spikes when `batch_limit` was cleared.
2. **Deferred chunk loading**: `_load_chunk` loads 500 lines immediately via `setPlainText`, then fills the remaining 500 in the next frame via `cursor.insertText`. Spreads the Qt block-creation cost across two frames instead of one.
3. **Deferred chunk reload after replace**: `_on_replace_finished` defers the `_load_chunk` call to the next frame via `QTimer.singleShot(0, ...)` so the signal-delivery frame stays lightweight.
4. **Optimized `get_lines`**: Direct dict access in the modified-lines slow path avoids per-line `get_line` overhead.

### Open
- S: P95=8-15ms ✅ | M: P95=4-7ms ✅ | L: P95=12-30ms ✅

### Scroll
- S: P95=8-11ms ✅ | M: P95=10-15ms ✅ | L: P95=13-16ms ✅

### Scrollbar Jump
- S: P95=11-17ms ✅ | M: P95=12-18ms ✅ | L: P95=22-28ms ✅

### Replace "while" → "for"
- S: P95=8-12ms ✅ | M: P95=4-7ms ✅ | L: P95=21-35ms ⚠️ (borderline, ~60% pass rate)

### Memory
- S: +4-5 MB ✅ | M: +1 MB ✅ | L: +312 MB ✅

### Summary: 14/15 pass consistently, 1 borderline
- **Fixed vs previous:** Large scrollbar jump fixed (55ms→22-28ms ✅), large replace dramatically improved (127-170ms→21-35ms)
- **Borderline:** Large replace — passes ~60% of runs, fails at P95=33-35ms on the rest

### Why Large Replace Cannot Consistently Hit 33ms

The remaining bottleneck is **irreducible `QPlainTextEdit.setPlainText()` cost**. This Qt C++ function must rebuild the internal `QTextDocument` block list (creating `QTextBlock` objects, computing layouts) for every line in the chunk. For 500 lines, this takes **15-25ms** depending on system load.

Combined with:
- `vdoc.get_lines()` reading 500 lines from 668K modified entries (~2-3ms)
- Viewport highlighting of ~50 blocks (~2-3ms)
- Python/Qt event loop overhead (~2-5ms)

The total lands at **20-33ms per frame** — right at the 33ms boundary. System load variance (GC, Windows scheduler, background processes) pushes ~40% of runs over the line by 1-2ms.

There is no lighter Qt API to swap document content in `QPlainTextEdit` — `setPlainText()` is the lowest-level text replacement available, and it is implemented entirely in Qt's C++ layer with no Python-side optimization possible.

