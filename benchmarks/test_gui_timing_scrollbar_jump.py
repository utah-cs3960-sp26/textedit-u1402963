"""GUI timing tests: scrollbar jump operations."""

from PyQt6.QtCore import QTimer


class TestGuiTimingScrollbarJump:
    def _run_jumps(self, window, qapp, run_direct, content, label):
        window.text_edit.setPlainText(content)
        qapp.processEvents()

        scrollbar = window.text_edit.verticalScrollBar()
        max_val = scrollbar.maximum()
        jump_targets = [max_val, 0, max_val // 2, 0, max_val, max_val // 4]

        def jumps():
            for target in jump_targets:
                done = [False]

                def do_jump(pos=target):
                    scrollbar.setValue(pos)
                    done[0] = True

                QTimer.singleShot(0, do_jump)
                while not done[0]:
                    qapp.processEvents()
                qapp.processEvents()

        return run_direct(label, jumps)

    def test_gui_timing_scrollbar_jump_small(
        self, window, qapp, run_direct, small_content
    ):
        passed = self._run_jumps(
            window, qapp, run_direct, small_content,
            "Scrollbar jump small.txt (6 jumps)",
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"

    def test_gui_timing_scrollbar_jump_medium(
        self, window, qapp, run_direct, medium_content
    ):
        passed = self._run_jumps(
            window, qapp, run_direct, medium_content,
            "Scrollbar jump medium.txt (6 jumps)",
        )
        assert passed, "Avg P95 frame time exceeds 60 fps target"
