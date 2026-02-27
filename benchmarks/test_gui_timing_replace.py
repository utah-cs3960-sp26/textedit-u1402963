"""GUI timing tests: find-and-replace operations."""


class TestGuiTimingReplace:
    def _run_replace(self, window, qapp, run_timed, content, label):
        find_bar = window._find_replace_bar
        find_bar.show_bar()
        find_bar._find_input.setText("while")
        find_bar._replace_input.setText("for")
        qapp.processEvents()

        def setup():
            window.text_edit.setPlainText(content)

        passed = run_timed(label, lambda: find_bar.replace_all(), setup=setup)

        find_bar.hide_bar()
        qapp.processEvents()
        return passed

    def test_gui_timing_replace_small(self, window, qapp, run_timed, small_content):
        passed = self._run_replace(
            window, qapp, run_timed, small_content,
            "Replace 'while' -> 'for' in small.txt (19 matches)",
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"

    def test_gui_timing_replace_medium(self, window, qapp, run_timed, medium_content):
        passed = self._run_replace(
            window, qapp, run_timed, medium_content,
            "Replace 'while' -> 'for' in medium.txt (1,186 matches)",
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"

    def test_gui_timing_replace_large(self, window, qapp, run_timed, large_content, require_small_medium_pass):
        passed = self._run_replace(
            window, qapp, run_timed, large_content,
            "Replace 'while' -> 'for' in large.txt (668,753 matches)",
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"
