"""Tests for VirtualDocument (mmap-backed large file support)."""

import os
import pytest

from editor.models.virtual_document import VirtualDocument


@pytest.fixture
def sample_file(tmp_path):
    """Create a sample text file with known content."""
    path = tmp_path / "sample.txt"
    lines = [f"line {i} with some data value={i}" for i in range(100)]
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


@pytest.fixture
def vdoc(sample_file):
    doc = VirtualDocument(sample_file)
    yield doc
    doc.close()


class TestLineIndex:
    def test_line_count(self, vdoc):
        assert vdoc.line_count == 100

    def test_get_first_line(self, vdoc):
        assert vdoc.get_line(0) == "line 0 with some data value=0"

    def test_get_last_line(self, vdoc):
        assert vdoc.get_line(99) == "line 99 with some data value=99"

    def test_get_middle_line(self, vdoc):
        assert vdoc.get_line(50) == "line 50 with some data value=50"

    def test_get_line_out_of_range(self, vdoc):
        assert vdoc.get_line(-1) == ""
        assert vdoc.get_line(100) == ""

    def test_get_lines_range(self, vdoc):
        text = vdoc.get_lines(0, 3)
        lines = text.split("\n")
        assert len(lines) == 3
        assert lines[0] == "line 0 with some data value=0"
        assert lines[2] == "line 2 with some data value=2"

    def test_get_lines_clamps_to_end(self, vdoc):
        text = vdoc.get_lines(98, 10)
        lines = text.split("\n")
        assert len(lines) == 2


class TestEditing:
    def test_set_line(self, vdoc):
        vdoc.set_line(5, "modified line 5")
        assert vdoc.get_line(5) == "modified line 5"

    def test_original_unaffected(self, vdoc):
        vdoc.set_line(5, "modified")
        assert vdoc.get_line_original(5) == "line 5 with some data value=5"

    def test_is_modified(self, vdoc):
        assert not vdoc.is_modified
        vdoc.set_line(0, "changed")
        assert vdoc.is_modified

    def test_set_lines_from_chunk(self, vdoc):
        chunk = "line 0 with some data value=0\nEDITED LINE\nline 2 with some data value=2"
        vdoc.set_lines_from_chunk(0, chunk)
        assert vdoc.get_line(0) == "line 0 with some data value=0"
        assert vdoc.get_line(1) == "EDITED LINE"
        assert vdoc.get_line(2) == "line 2 with some data value=2"
        assert 0 not in vdoc._modified_lines
        assert 1 in vdoc._modified_lines

    def test_set_lines_from_chunk_reverts_modification(self, vdoc):
        vdoc.set_line(1, "temp edit")
        assert 1 in vdoc._modified_lines
        # Now "revert" by sending original text
        original_chunk = vdoc.get_lines(0, 3)
        # Manually revert line 1
        lines = original_chunk.split("\n")
        lines[1] = vdoc.get_line_original(1)
        vdoc.set_lines_from_chunk(0, "\n".join(lines))
        assert 1 not in vdoc._modified_lines


class TestFindAll:
    def test_find_case_insensitive(self, vdoc):
        matches = vdoc.find_all("LINE", case_sensitive=False)
        assert len(matches) == 100

    def test_find_case_sensitive(self, vdoc):
        matches = vdoc.find_all("line", case_sensitive=True)
        assert len(matches) == 100

    def test_find_case_sensitive_no_match(self, vdoc):
        matches = vdoc.find_all("LINE", case_sensitive=True)
        assert len(matches) == 0

    def test_find_specific_value(self, vdoc):
        matches = vdoc.find_all("value=50", case_sensitive=True)
        assert len(matches) == 1
        line_no, col, length = matches[0]
        assert line_no == 50
        assert length == 8

    def test_find_regex(self, vdoc):
        matches = vdoc.find_all(r"value=\d{2}$", use_regex=True)
        # Lines 10-99 have 2-digit values at end
        assert len(matches) == 90

    def test_find_no_match(self, vdoc):
        matches = vdoc.find_all("ZZZZNOTFOUND")
        assert len(matches) == 0

    def test_find_empty_pattern(self, vdoc):
        matches = vdoc.find_all("")
        assert len(matches) == 0

    def test_find_invalid_regex(self, vdoc):
        matches = vdoc.find_all("[bad", use_regex=True)
        assert len(matches) == 0

    def test_find_in_modified_line(self, vdoc):
        vdoc.set_line(5, "REPLACED content here")
        matches = vdoc.find_all("REPLACED", case_sensitive=True)
        assert len(matches) == 1
        assert matches[0][0] == 5


class TestReplaceAll:
    def test_replace_all_basic(self, vdoc):
        count = vdoc.replace_all("data", "info", case_sensitive=True)
        assert count == 100
        assert "info" in vdoc.get_line(0)
        assert "data" not in vdoc.get_line(0)

    def test_replace_all_case_insensitive(self, vdoc):
        count = vdoc.replace_all("LINE", "ROW", case_sensitive=False)
        assert count == 100

    def test_replace_all_regex(self, vdoc):
        count = vdoc.replace_all(r"value=(\d+)", r"val=\1", use_regex=True)
        assert count == 100
        assert "val=0" in vdoc.get_line(0)

    def test_replace_all_no_match(self, vdoc):
        count = vdoc.replace_all("ZZZZ", "XXX")
        assert count == 0

    def test_replace_all_empty_pattern(self, vdoc):
        count = vdoc.replace_all("", "XXX")
        assert count == 0


class TestSave:
    def test_save_preserves_content(self, vdoc, sample_file):
        vdoc.set_line(0, "MODIFIED FIRST LINE")
        vdoc.save()
        # Reread and verify
        with open(sample_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("MODIFIED FIRST LINE\n")
        assert "line 1 with some data value=1" in content

    def test_save_clears_modifications(self, vdoc):
        vdoc.set_line(0, "changed")
        assert vdoc.is_modified
        vdoc.save()
        assert not vdoc.is_modified

    def test_save_to_different_path(self, vdoc, tmp_path):
        alt_path = str(tmp_path / "alt.txt")
        vdoc.set_line(0, "MODIFIED")
        vdoc.save(alt_path)
        with open(alt_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("MODIFIED\n")


class TestGetFullText:
    def test_full_text_matches_file(self, vdoc, sample_file):
        with open(sample_file, "r", encoding="utf-8") as f:
            expected = f.read()
        assert vdoc.get_full_text() == expected

    def test_full_text_with_modifications(self, vdoc):
        vdoc.set_line(0, "CHANGED")
        text = vdoc.get_full_text()
        lines = text.split("\n")
        assert lines[0] == "CHANGED"
        assert lines[1] == "line 1 with some data value=1"


class TestIsLargeFile:
    def test_small_file_not_large(self, tmp_path):
        p = tmp_path / "small.txt"
        p.write_text("hello", encoding="utf-8")
        assert not VirtualDocument.is_large_file(str(p))

    def test_large_file_detected(self, tmp_path):
        p = tmp_path / "big.txt"
        p.write_bytes(b"x" * (VirtualDocument.LARGE_FILE_THRESHOLD + 1))
        assert VirtualDocument.is_large_file(str(p))

    def test_nonexistent_file(self):
        assert not VirtualDocument.is_large_file("/nonexistent/path.txt")


class TestFileProperties:
    def test_file_path(self, vdoc, sample_file):
        assert vdoc.file_path == sample_file

    def test_close(self, sample_file):
        doc = VirtualDocument(sample_file)
        doc.close()
        assert doc._mmap is None
        assert doc._file is None

    def test_double_close_safe(self, sample_file):
        doc = VirtualDocument(sample_file)
        doc.close()
        doc.close()  # should not raise


class TestCRLF:
    def test_crlf_line_endings(self, tmp_path):
        p = tmp_path / "crlf.txt"
        p.write_bytes(b"line1\r\nline2\r\nline3")
        doc = VirtualDocument(str(p))
        assert doc.line_count == 3
        assert doc.get_line(0) == "line1"
        assert doc.get_line(1) == "line2"
        assert doc.get_line(2) == "line3"
        doc.close()


class TestEmptyFile:
    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.txt"
        p.write_text("", encoding="utf-8")
        doc = VirtualDocument(str(p))
        assert doc.line_count == 1
        assert doc.get_line(0) == ""
        doc.close()

    def test_single_line_no_newline(self, tmp_path):
        p = tmp_path / "single.txt"
        p.write_text("hello", encoding="utf-8")
        doc = VirtualDocument(str(p))
        assert doc.line_count == 1
        assert doc.get_line(0) == "hello"
        doc.close()
