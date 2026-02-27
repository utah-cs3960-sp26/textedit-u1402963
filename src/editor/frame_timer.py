import time

from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtGui import QFontDatabase


class FrameTimerApp(QApplication):
    """QApplication subclass that measures event processing time.

    Overrides ``notify()`` to measure the wall-clock time spent processing
    each top-level event (excluding idle waits between events).
    """

    def __init__(self, argv):
        super().__init__(argv)
        self._frame_timer_widget = None
        self._tracking = False
        self._notify_depth = 0

    def set_frame_timer(self, widget):
        self._frame_timer_widget = widget

    def set_tracking(self, enabled):
        self._tracking = enabled

    def notify(self, receiver, event):
        if not self._tracking or self._frame_timer_widget is None:
            return super().notify(receiver, event)

        self._notify_depth += 1
        try:
            if self._notify_depth == 1:
                start = time.perf_counter()
                result = super().notify(receiver, event)
                elapsed_ms = (time.perf_counter() - start) * 1000
                self._frame_timer_widget.record_frame(elapsed_ms)
                return result
            else:
                return super().notify(receiver, event)
        finally:
            self._notify_depth -= 1


class FrameTimerWidget(QLabel):
    """Displays last / average / max frame times and derived FPS."""

    DISPLAY_INTERVAL = 0.25  # seconds between display updates (4 Hz)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recording = False
        self._last_ms = 0.0
        self._max_ms = 0.0
        self._total_ms = 0.0
        self._frame_count = 0
        self._last_display_time = 0.0

        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(9)
        self.setFont(font)

        self.setVisible(False)
        self._update_display()

    def record_frame(self, duration_ms):
        if self._recording:
            return
        self._recording = True
        self._last_ms = duration_ms
        if duration_ms > self._max_ms:
            self._max_ms = duration_ms
        self._total_ms += duration_ms
        self._frame_count += 1
        now = time.perf_counter()
        if now - self._last_display_time >= self.DISPLAY_INTERVAL:
            self._update_display()
            self._last_display_time = now
        self._recording = False

    def _update_display(self):
        if self._frame_count == 0:
            self.setText("Last: --ms | Avg: --ms | Max: --ms | -- fps")
            return
        avg = self._total_ms / self._frame_count
        fps = 1000.0 / self._last_ms if self._last_ms > 0 else 0
        self.setText(
            f"Last: {self._last_ms:.1f}ms | "
            f"Avg: {avg:.1f}ms | "
            f"Max: {self._max_ms:.1f}ms | "
            f"{fps:.0f} fps"
        )

    def _reset(self):
        self._last_ms = 0.0
        self._max_ms = 0.0
        self._total_ms = 0.0
        self._frame_count = 0
        self._last_display_time = 0.0
        self._update_display()
