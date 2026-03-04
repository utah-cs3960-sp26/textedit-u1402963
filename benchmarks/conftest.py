import gc
import os
import sys
import time
import statistics

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(ROOT_DIR, "src") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from editor.frame_timer import FrameTimerApp
from editor.window import MainWindow

_FILES_DIR = os.path.join(ROOT_DIR, "s-m-l-files")
_SMALL_FILE = os.path.join(_FILES_DIR, "small.py")
_MEDIUM_FILE = os.path.join(_FILES_DIR, "medium.py")
_LARGE_FILE = os.path.join(_FILES_DIR, "large.py")

TARGET_FRAME_MS = 16.67       # 60 fps — default for small/medium files
TARGET_FRAME_MS_LARGE = 33.0  # 30 fps — relaxed target for large files
TEST_TIMEOUT = None  # no timeout — operations may be slow, we only care about frame times
NUM_RUNS = 5
WARMUP_RUNS = 1  # discarded before measurement


class FrameCollector:
    """Lightweight collector that records individual frame times."""

    def __init__(self):
        self.frame_times = []

    def record_frame(self, duration_ms):
        self.frame_times.append(duration_ms)

    def reset(self):
        self.frame_times.clear()

    @property
    def max_ms(self):
        return max(self.frame_times) if self.frame_times else 0.0

    @property
    def avg_ms(self):
        return statistics.mean(self.frame_times) if self.frame_times else 0.0

    @property
    def p95_ms(self):
        if not self.frame_times:
            return 0.0
        s = sorted(self.frame_times)
        return s[min(int(len(s) * 0.95), len(s) - 1)]

    @property
    def frame_count(self):
        return len(self.frame_times)


def _print_multi_result(operation, runs, all_frames, target_ms=None):
    """Print a formatted multi-run benchmark report.

    ``runs`` contains per-run wall-clock summaries.
    ``all_frames`` is the pooled list of every frame time across all runs.
    ``target_ms`` is the P95 threshold; defaults to TARGET_FRAME_MS.
    Returns True if passed.
    """
    if target_ms is None:
        target_ms = TARGET_FRAME_MS

    # Aggregate statistics over pooled frames
    if all_frames:
        agg_max = max(all_frames)
        agg_avg = statistics.mean(all_frames)
        agg_p95 = sorted(all_frames)[min(int(len(all_frames) * 0.95), len(all_frames) - 1)]
        agg_p99 = sorted(all_frames)[min(int(len(all_frames) * 0.99), len(all_frames) - 1)]
        agg_median = statistics.median(all_frames)
        agg_stdev = statistics.stdev(all_frames) if len(all_frames) > 1 else 0.0
        over_target = [f for f in all_frames if f > target_ms]
    else:
        agg_max = agg_avg = agg_p95 = agg_p99 = agg_median = agg_stdev = 0.0
        over_target = []

    passed = agg_p95 <= target_ms
    status = "PASS" if passed else "FAIL"

    fps_label = f"{1000 / target_ms:.0f} fps" if target_ms > 0 else "N/A"

    print(f"\n{'='*65}")
    print(f"  {operation} -- {len(runs)} runs ({WARMUP_RUNS} warmup discarded)")
    print(f"{'='*65}")
    for i, r in enumerate(runs, 1):
        print(
            f"  Run {i}:  wall={r['wall']:>8.1f}ms  "
            f"max={r['max']:>8.1f}ms  "
            f"p95={r['p95']:>8.1f}ms  "
            f"frames={r['frames']}"
        )
    print(f"  {'-'*61}")
    print(f"  Total frames pooled: {len(all_frames)}")
    print(f"  Aggregate max:       {agg_max:>10.1f} ms")
    print(f"  Aggregate P99:       {agg_p99:>10.1f} ms")
    print(f"  Aggregate P95:       {agg_p95:>10.1f} ms")
    print(f"  Aggregate median:    {agg_median:>10.1f} ms")
    print(f"  Aggregate avg:       {agg_avg:>10.1f} ms")
    print(f"  Aggregate stdev:     {agg_stdev:>10.1f} ms")
    print(f"  Frames > {target_ms:.1f}ms:  {len(over_target):>10} / {len(all_frames)}")
    if over_target:
        worst = sorted(over_target, reverse=True)[:5]
        print(f"  Worst offenders:     {', '.join(f'{v:.1f}ms' for v in worst)}")
    print(f"  Target (P95):        <={target_ms:.2f} ms ({fps_label})")
    print(f"  Result:              {status}")
    print(f"{'='*65}")
    return passed


def get_rss_mb():
    """Get current process RSS in MB. Returns None if unavailable."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(pmc)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        fn = ctypes.windll.kernel32.K32GetProcessMemoryInfo
        fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
        fn.restype = wintypes.BOOL
        if fn(handle, ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize / (1024 * 1024)
        return None
    elif sys.platform == "linux":
        # /proc/self/statm fields: size resident shared text lib data dt (in pages)
        try:
            with open("/proc/self/statm") as f:
                fields = f.read().split()
            resident_pages = int(fields[1])
            page_size = os.sysconf("SC_PAGE_SIZE")
            return (resident_pages * page_size) / (1024 * 1024)
        except (OSError, IndexError, ValueError):
            return None
    else:
        # macOS / other Unix: ru_maxrss is peak RSS (bytes on macOS, KB on others).
        # This is peak, not current, so deltas may be inaccurate if peak was set
        # by an earlier operation. Best effort.
        try:
            import resource
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            if sys.platform == "darwin":
                return rusage.ru_maxrss / (1024 * 1024)
            return rusage.ru_maxrss / 1024
        except ImportError:
            return None


# ---------------------------------------------------------------------------
# Large-file gate — if ANY small or medium test fails, every large-file
# benchmark is automatically skipped.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = FrameTimerApp(sys.argv)
    yield app


@pytest.fixture
def window(qapp):
    win = MainWindow()
    win.show()
    qapp.processEvents()
    yield win
    win._document.mark_saved()
    if win._vdoc:
        win._vdoc._modified_lines.clear()
    win.close()
    qapp.processEvents()


@pytest.fixture
def collector(qapp):
    """Swap in a FrameCollector so benchmarks capture individual frame times."""
    c = FrameCollector()
    original = qapp._frame_timer_widget
    qapp.set_frame_timer(c)
    yield c
    qapp.set_frame_timer(original)


def _gc_settle():
    """Force GC and give the process a moment to stabilize."""
    gc.collect()
    gc.collect()


def _drain_deferred(qapp, collector=None):
    """Process events until no new frames are generated (deferred work done).

    When called without collector (e.g., during setup), just drains
    a fixed number of processEvents calls to complete deferred loading.
    """
    if collector is None:
        # Setup drain: process events until nothing is pending.
        # When deferred timers fire, processEvents takes measurable time.
        # When idle, it returns in <0.1ms.
        for _ in range(10000):
            t = time.perf_counter()
            qapp.processEvents()
            if time.perf_counter() - t < 0.001:
                break
        return

    prev_frames = collector.frame_count
    for _ in range(50000):
        qapp.processEvents()
        cur_frames = collector.frame_count
        if cur_frames == prev_frames:
            break
        prev_frames = cur_frames


@pytest.fixture
def run_timed(qapp, collector):
    """Run fn inside the event loop NUM_RUNS times (+ warmup), aggregate results.

    Use for single blocking operations (setPlainText, replace_all) that need
    QTimer wrapping so notify() captures the time.

    ``setup`` is called before each run (outside the timed section).
    Returns True if aggregate P95 <= target.
    """
    def _run(operation_name, fn, setup=None, target_ms=None):
        all_runs = []
        all_frames = []

        for run_idx in range(WARMUP_RUNS + NUM_RUNS):
            if setup:
                qapp.set_tracking(False)
                setup()
                _drain_deferred(qapp)

            _gc_settle()
            collector.reset()
            qapp.set_tracking(True)

            done = [False]

            def wrapper():
                try:
                    fn()
                finally:
                    done[0] = True

            start = time.perf_counter()
            QTimer.singleShot(0, wrapper)
            while not done[0]:
                qapp.processEvents()
            # Drain deferred work (chunked loading, batched highlighting)
            _drain_deferred(qapp, collector)
            wall_ms = (time.perf_counter() - start) * 1000
            qapp.set_tracking(False)

            # Discard warmup runs
            if run_idx < WARMUP_RUNS:
                continue

            all_frames.extend(collector.frame_times)
            all_runs.append({
                "wall": wall_ms,
                "max": collector.max_ms,
                "avg": collector.avg_ms,
                "p95": collector.p95_ms,
                "frames": collector.frame_count,
            })

        return _print_multi_result(operation_name, all_runs, all_frames, target_ms)

    return _run


@pytest.fixture
def run_direct(qapp, collector):
    """Run fn directly NUM_RUNS times (+ warmup), aggregate results.

    Use for multi-step operations (scrolling, scrollbar jumps) where each
    step already dispatches events through notify() via QTest or QTimer.

    ``setup`` is called before each run (outside the timed section).
    Returns True if aggregate P95 <= target.
    """
    def _run(operation_name, fn, setup=None, target_ms=None):
        all_runs = []
        all_frames = []

        for run_idx in range(WARMUP_RUNS + NUM_RUNS):
            if setup:
                qapp.set_tracking(False)
                setup()
                _drain_deferred(qapp)

            _gc_settle()
            collector.reset()
            qapp.set_tracking(True)

            start = time.perf_counter()
            fn()
            qapp.processEvents()
            wall_ms = (time.perf_counter() - start) * 1000
            qapp.set_tracking(False)

            # Discard warmup runs
            if run_idx < WARMUP_RUNS:
                continue

            all_frames.extend(collector.frame_times)
            all_runs.append({
                "wall": wall_ms,
                "max": collector.max_ms,
                "avg": collector.avg_ms,
                "p95": collector.p95_ms,
                "frames": collector.frame_count,
            })

        return _print_multi_result(operation_name, all_runs, all_frames, target_ms)

    return _run


@pytest.fixture(scope="session")
def small_content():
    with open(_SMALL_FILE, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


@pytest.fixture(scope="session")
def medium_content():
    with open(_MEDIUM_FILE, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


@pytest.fixture(scope="session")
def large_content():
    with open(_LARGE_FILE, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


@pytest.fixture(scope="session")
def large_file_path():
    return _LARGE_FILE


@pytest.fixture
def measure_memory():
    """Returns a callable that measures current process RSS in MB."""
    return get_rss_mb
