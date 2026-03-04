"""GUI timing tests: scrollbar jump operations."""

from PyQt6.QtCore import QTimer

from benchmarks.conftest import TARGET_FRAME_MS_LARGE


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

    def test_gui_timing_scrollbar_jump_large(
        self, window, qapp, run_direct, large_file_path
    ):
        from editor.models.virtual_document import VirtualDocument

        shared_vdoc = VirtualDocument(large_file_path)

        window._vdoc = shared_vdoc
        window._document.file_path = large_file_path
        window._document.set_content("", mark_as_saved=True)
        window.text_edit.enter_virtual_mode(shared_vdoc, window._virtual_scrollbar)
        window._setup_highlighter(large_file_path, "")
        if window.highlighter:
            window.highlighter.set_batch_limit(100)
        qapp.processEvents()

        scrollbar = window._virtual_scrollbar
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

        passed = run_direct(
            "Scrollbar jump large.txt (6 jumps) [virtual mode]",
            jumps, target_ms=TARGET_FRAME_MS_LARGE,
        )

        if window.text_edit.virtual_mode:
            window.text_edit.exit_virtual_mode()
        window._vdoc = None
        shared_vdoc.close()

        assert passed, "Avg P95 frame time exceeds 60 fps target"
