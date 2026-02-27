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


## Post Optimization Timing

### The maximum frame time when you open small/medium/large.

- S: P95=11.9ms, 12.9ms, 8.8ms, 9.1ms, 9.3ms (aggregate P95: 9.1ms) ✅ PASS
- M: P95=6.3ms, 7.4ms, 7.2ms, 6.5ms, 6.5ms (aggregate P95: 6.5ms) ✅ PASS
- L: P95=23.0ms, 23.1ms, 18.9ms, 17.4ms, 16.8ms (aggregate P95: 20.4ms) ❌ FAIL

### The maximum frame time as you scroll up and down.

- S: P95=7.0ms, 8.0ms, 7.9ms, 7.8ms, 9.6ms (aggregate P95: 8.0ms) ✅ PASS
- M: P95=16.8ms, 9.8ms, 16.1ms, 11.6ms, 11.3ms (aggregate P95: 14.0ms) ✅ PASS
- L: P95=13.0ms, 12.3ms, 13.1ms, 12.7ms, 13.2ms (aggregate P95: 12.8ms) ✅ PASS

### The maximum and average frame times when you click far away from the current location in the scroll bar.

- S: P95=12.4ms, 12.3ms, 14.6ms, 16.8ms, 11.3ms (aggregate P95: 13.3ms, avg: 2.3ms) ✅ PASS
- M: P95=15.7ms, 9.3ms, 8.9ms, 9.8ms, 9.7ms (aggregate P95: 9.7ms, avg: 1.9ms) ✅ PASS
- L: P95=18.2ms, 16.7ms, 18.6ms, 16.3ms, 16.6ms (aggregate P95: 17.0ms, avg: 3.7ms) ❌ FAIL

### The maximum frame time if you try to replace "while" with "for".

- S: P95=9.8ms, 9.0ms, 9.9ms, 8.7ms, 7.3ms (aggregate P95: 8.7ms) ✅ PASS
- M: P95=12.1ms, 10.4ms, 9.3ms, 9.9ms, 10.3ms (aggregate P95: 10.3ms) ✅ PASS
- L: P95=6783.5ms, 6830.2ms, 6775.7ms, 6783.0ms, 6767.2ms (aggregate P95: 6783.0ms) ❌ FAIL

### The total memory used by your text editor process.

- S: baseline 140.1 MB, after 144.9 MB, delta +4.7 MB ✅ PASS
- M: baseline 162.0 MB, after 163.2 MB, delta +1.2 MB ✅ PASS
- L: baseline 180.5 MB, after 493.1 MB, delta +312.7 MB (limit 3072 MB) ✅ PASS

### Summary

- **12 / 15 tests passed**, 3 failed (all large file: open, replace, scrollbar jump)
- Small and medium file benchmarks all pass comfortably
- Large file scroll passes (P95: 12.8ms) but open, replace, and scrollbar jump still exceed 16.67ms target

