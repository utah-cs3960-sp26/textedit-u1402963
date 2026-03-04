"""GUI timing tests: memory usage after loading files.

Measures the physical (RSS) memory used by the editor process after loading
each test file. No pass/fail threshold — results are reported for review.
"""

import pytest


class TestGuiTimingMemory:
    def _load_and_measure(self, window, qapp, measure_memory, content, label):
        baseline = measure_memory()
        if baseline is None:
            pytest.skip("Cannot measure RSS on this platform")

        window.text_edit.setPlainText(content)
        qapp.processEvents()

        after = measure_memory()
        delta = after - baseline

        print(f"\n{'='*60}")
        print(f"  Memory: {label}")
        print(f"{'='*60}")
        print(f"  Baseline:  {baseline:>10.1f} MB")
        print(f"  After:     {after:>10.1f} MB")
        print(f"  Delta:     {delta:>+10.1f} MB")
        print(f"{'='*60}")

    def test_gui_timing_memory_small(
        self, window, qapp, measure_memory, small_content
    ):
        self._load_and_measure(
            window, qapp, measure_memory, small_content, "small.txt"
        )

    def test_gui_timing_memory_medium(
        self, window, qapp, measure_memory, medium_content
    ):
        self._load_and_measure(
            window, qapp, measure_memory, medium_content, "medium.txt"
        )

    def test_gui_timing_memory_large(
        self, window, qapp, measure_memory, large_file_path
    ):
        from editor.models.virtual_document import VirtualDocument

        baseline = measure_memory()
        if baseline is None:
            pytest.skip("Cannot measure RSS on this platform")

        vdoc = VirtualDocument(large_file_path)
        window._vdoc = vdoc
        window._document.file_path = large_file_path
        window._document.set_content("", mark_as_saved=True)
        window.text_edit.enter_virtual_mode(vdoc, window._virtual_scrollbar)
        qapp.processEvents()

        after = measure_memory()
        delta = after - baseline

        print(f"\n{'='*60}")
        print(f"  Memory: large.txt [virtual mode]")
        print(f"{'='*60}")
        print(f"  Baseline:  {baseline:>10.1f} MB")
        print(f"  After:     {after:>10.1f} MB")
        print(f"  Delta:     {delta:>+10.1f} MB")
        print(f"  Limit:     {'3072.0':>10} MB")
        print(f"{'='*60}")

        # Cleanup
        if window.text_edit.virtual_mode:
            window.text_edit.exit_virtual_mode()
        window._vdoc = None
        vdoc.close()

        assert delta < 3072, f"Memory delta {delta:.1f} MB exceeds 3 GiB limit"
