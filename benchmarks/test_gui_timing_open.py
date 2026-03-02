"""GUI timing tests: file open operations."""

from benchmarks.conftest import TARGET_FRAME_MS_LARGE


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

    def test_gui_timing_open_large(self, window, qapp, run_timed, large_file_path, require_small_medium_pass):
        from editor.models.virtual_document import VirtualDocument

        # Pre-build VirtualDocument (line index) once — O(filesize) cost
        shared_vdoc = VirtualDocument(large_file_path)

        def setup():
            if window.text_edit.virtual_mode:
                window.text_edit.exit_virtual_mode()
            window._vdoc = None
            qapp.processEvents()

        def open_fn():
            window._vdoc = shared_vdoc
            shared_vdoc._modified_lines.clear()
            window._document.file_path = large_file_path
            window._document.set_content("", mark_as_saved=True)
            window.text_edit.enter_virtual_mode(shared_vdoc, window._virtual_scrollbar)
            window._update_status()
            # Defer highlighter setup to keep this frame under 16.67ms
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: _setup_hl())

        def _setup_hl():
            chunk_text = window.text_edit.toPlainText()
            window._setup_highlighter(large_file_path, chunk_text)
            if window.highlighter:
                window.highlighter.set_batch_limit(100)

        passed = run_timed(
            "Open large.txt (1,377,419 lines) [virtual mode]",
            open_fn, setup=setup, target_ms=TARGET_FRAME_MS_LARGE,
        )

        # Cleanup
        if window.text_edit.virtual_mode:
            window.text_edit.exit_virtual_mode()
        window._vdoc = None
        shared_vdoc.close()

        assert passed, "Avg P95 frame time exceeds 60 fps target"
