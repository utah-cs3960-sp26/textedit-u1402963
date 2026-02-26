import os
import sys
import time
import statistics
import contextlib

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(ROOT_DIR, "src") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from editor.frame_timer import FrameTimerApp
from editor.window import MainWindow

_FILES_DIR = os.path.join(ROOT_DIR, "s-m-l-files")
_SMALL_FILE = os.path.join(_FILES_DIR, "small.txt")
_MEDIUM_FILE = os.path.join(_FILES_DIR, "medium.txt")

TARGET_FRAME_MS = 16.67  # 60 fps
NUM_RUNS = 5


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


def _print_multi_result(operation, runs):
    """Print a formatted multi-run benchmark report. Returns True if passed."""
    avg_wall = statistics.mean(r["wall"] for r in runs)
    avg_max = statistics.mean(r["max"] for r in runs)
    avg_avg = statistics.mean(r["avg"] for r in runs)
    avg_p95 = statistics.mean(r["p95"] for r in runs)
    avg_frames = statistics.mean(r["frames"] for r in runs)

    passed = avg_p95 <= TARGET_FRAME_MS
    status = "PASS" if passed else "FAIL"

    print(f"\n{'='*60}")
    print(f"  {operation} -- {len(runs)} runs")
    print(f"{'='*60}")
    for i, r in enumerate(runs, 1):
        print(
            f"  Run {i}:  wall={r['wall']:>8.1f}ms  "
            f"max={r['max']:>8.1f}ms  "
            f"p95={r['p95']:>8.1f}ms"
        )
    print(f"  {'-'*56}")
    print(f"  Avg wall clock:    {avg_wall:>10.1f} ms")
    print(f"  Avg max frame:     {avg_max:>10.1f} ms")
    print(f"  Avg avg frame:     {avg_avg:>10.1f} ms")
    print(f"  Avg P95 frame:     {avg_p95:>10.1f} ms")
    print(f"  Avg frame count:   {avg_frames:>10.0f}")
    print(f"  Target (P95):      <={TARGET_FRAME_MS:.2f} ms (60 fps)")
    print(f"  Result:            {status}")
    print(f"{'='*60}")
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
    else:
        try:
            import resource
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            if sys.platform == "darwin":
                return rusage.ru_maxrss / (1024 * 1024)
            return rusage.ru_maxrss / 1024
        except ImportError:
            return None


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


@pytest.fixture
def run_timed(qapp, collector):
    """Run fn inside the event loop NUM_RUNS times, average results.

    Use for single blocking operations (setPlainText, replace_all) that need
    QTimer wrapping so notify() captures the time.

    ``setup`` is called before each run (outside the timed section).
    Returns True if averaged P95 <= target.
    """
    def _run(operation_name, fn, setup=None):
        all_runs = []
        for _ in range(NUM_RUNS):
            if setup:
                qapp.set_tracking(False)
                setup()
                qapp.processEvents()

            collector.reset()
            qapp.set_tracking(True)

            done = [False]
            def wrapper():
                fn()
                done[0] = True

            start = time.perf_counter()
            QTimer.singleShot(0, wrapper)
            while not done[0]:
                qapp.processEvents()
            qapp.processEvents()
            wall_ms = (time.perf_counter() - start) * 1000
            qapp.set_tracking(False)

            all_runs.append({
                "wall": wall_ms,
                "max": collector.max_ms,
                "avg": collector.avg_ms,
                "p95": collector.p95_ms,
                "frames": collector.frame_count,
            })

        return _print_multi_result(operation_name, all_runs)

    return _run


@pytest.fixture
def run_direct(qapp, collector):
    """Run fn directly NUM_RUNS times, average results.

    Use for multi-step operations (scrolling, scrollbar jumps) where each
    step already dispatches events through notify() via QTest or QTimer.

    ``setup`` is called before each run (outside the timed section).
    Returns True if averaged P95 <= target.
    """
    def _run(operation_name, fn, setup=None):
        all_runs = []
        for _ in range(NUM_RUNS):
            if setup:
                qapp.set_tracking(False)
                setup()
                qapp.processEvents()

            collector.reset()
            qapp.set_tracking(True)

            start = time.perf_counter()
            fn()
            qapp.processEvents()
            wall_ms = (time.perf_counter() - start) * 1000
            qapp.set_tracking(False)

            all_runs.append({
                "wall": wall_ms,
                "max": collector.max_ms,
                "avg": collector.avg_ms,
                "p95": collector.p95_ms,
                "frames": collector.frame_count,
            })

        return _print_multi_result(operation_name, all_runs)

    return _run


@pytest.fixture(scope="session")
def small_content():
    with open(_SMALL_FILE, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


@pytest.fixture(scope="session")
def medium_content():
    with open(_MEDIUM_FILE, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


@pytest.fixture
def measure_memory():
    """Returns a callable that measures current process RSS in MB."""
    return get_rss_mb
