"""GUI timing tests: file open operations."""


class TestGuiTimingOpen:
    def test_gui_timing_open_small(self, window, run_timed, small_content):
        passed = run_timed(
            "Open small.txt (173 lines)",
            lambda: window.text_edit.setPlainText(small_content),
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"

    def test_gui_timing_open_medium(self, window, run_timed, medium_content):
        passed = run_timed(
            "Open medium.txt (8,739 lines)",
            lambda: window.text_edit.setPlainText(medium_content),
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"
