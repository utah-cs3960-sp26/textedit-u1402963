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

