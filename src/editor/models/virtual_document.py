import mmap
import os
import re
import bisect
from typing import Optional


class VirtualDocument:
    """
    Memory-mapped document for handling large files efficiently.
    Uses mmap for O(1) random access and maintains a line offset index
    for fast line-based operations.
    """

    LARGE_FILE_THRESHOLD = 5 * 1024 * 1024  # 5 MB

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._file_size = os.path.getsize(file_path)
        self._file = None
        self._mmap = None
        self._modified_lines = {}
        self._encoding = "utf-8"

        if self._file_size == 0:
            self._line_offsets = [0]
            return

        self._file = open(file_path, "rb")
        self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        self._line_offsets = self._build_line_index()

    def _build_line_index(self):
        """Build array of byte offsets for each line start."""
        offsets = [0]
        pos = 0
        while True:
            idx = self._mmap.find(b"\n", pos)
            if idx == -1:
                break
            offsets.append(idx + 1)
            pos = idx + 1
        return offsets

    @property
    def line_count(self):
        return len(self._line_offsets)

    @property
    def file_path(self):
        return self._file_path

    def get_line(self, line_no: int) -> str:
        """Get a single line by its global line number (without trailing newline)."""
        if line_no in self._modified_lines:
            return self._modified_lines[line_no]

        if line_no < 0 or line_no >= len(self._line_offsets):
            return ""

        if not self._mmap:
            return ""

        start = self._line_offsets[line_no]
        if line_no + 1 < len(self._line_offsets):
            end = self._line_offsets[line_no + 1]
        else:
            end = self._file_size

        raw = self._mmap[start:end]
        text = raw.decode(self._encoding, errors="replace")
        if text.endswith("\r\n"):
            text = text[:-2]
        elif text.endswith("\n"):
            text = text[:-1]
        return text

    def get_lines(self, start_line: int, count: int) -> str:
        """Get a range of lines as a single string joined by newlines."""
        end = min(start_line + count, self.line_count)

        # Fast path: no modifications in range — read one contiguous mmap slice
        if self._mmap and not any(
            i in self._modified_lines for i in range(start_line, end)
        ):
            start_offset = self._line_offsets[start_line]
            if end < self.line_count:
                end_offset = self._line_offsets[end]
            else:
                end_offset = self._file_size
            raw = self._mmap[start_offset:end_offset]
            text = raw.decode(self._encoding, errors="replace")
            # Strip trailing newline from the last line in the range
            if text.endswith("\r\n"):
                text = text[:-2]
            elif text.endswith("\n"):
                text = text[:-1]
            # Normalize \r\n to \n within the range
            if "\r\n" in text:
                text = text.replace("\r\n", "\n")
            return text

        # Slow path: per-line reads for ranges with modifications
        lines = []
        for i in range(start_line, end):
            lines.append(self.get_line(i))
        return "\n".join(lines)

    def set_line(self, line_no: int, text: str):
        """Update a line's content (for edit tracking)."""
        self._modified_lines[line_no] = text

    def set_lines_from_chunk(self, start_line: int, chunk_text: str):
        """
        Update the buffer from a chunk of edited text.
        Compares each line with the original and only stores modifications.
        """
        lines = chunk_text.split("\n")
        for i, line in enumerate(lines):
            global_line = start_line + i
            if global_line >= self.line_count:
                break
            original = self.get_line_original(global_line)
            if line != original:
                self._modified_lines[global_line] = line
            elif global_line in self._modified_lines:
                # Line was reverted to original, remove the modification
                del self._modified_lines[global_line]

    def get_line_original(self, line_no: int) -> str:
        """Get the original (unmodified) line from mmap."""
        if line_no < 0 or line_no >= len(self._line_offsets):
            return ""
        if not self._mmap:
            return ""
        start = self._line_offsets[line_no]
        if line_no + 1 < len(self._line_offsets):
            end = self._line_offsets[line_no + 1]
        else:
            end = self._file_size
        raw = self._mmap[start:end]
        text = raw.decode(self._encoding, errors="replace")
        if text.endswith("\r\n"):
            text = text[:-2]
        elif text.endswith("\n"):
            text = text[:-1]
        return text

    @property
    def is_modified(self):
        """Check if any lines have been modified."""
        return len(self._modified_lines) > 0

    def _byte_offset_to_line(self, byte_offset: int) -> int:
        """Binary search to find which line a byte offset belongs to."""
        line = bisect.bisect_right(self._line_offsets, byte_offset) - 1
        return max(0, line)

    def find_all(self, pattern: str, case_sensitive: bool = False,
                 use_regex: bool = False, abort_flag=None):
        """
        Find all matches in the document.
        Returns list of (line_no, column, match_length).
        Searches mmap directly for speed.
        abort_flag: optional threading.Event checked periodically to exit early.
        """
        results = []

        if not pattern:
            return results

        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled = re.compile(pattern, flags)
            except re.error:
                return []

            # Search line by line (handles both modified and unmodified)
            for line_no in range(self.line_count):
                if abort_flag and line_no % 1000 == 0 and abort_flag.is_set():
                    return results
                line_text = self.get_line(line_no)
                for m in compiled.finditer(line_text):
                    results.append((line_no, m.start(), m.end() - m.start()))
        else:
            # For plain text, search mmap directly for unmodified lines
            # and search modified lines separately
            if case_sensitive:
                pattern_bytes = pattern.encode(self._encoding)
            else:
                pattern_bytes = None  # Can't do case-insensitive on bytes easily

            if pattern_bytes and case_sensitive:
                # Fast mmap search for case-sensitive plain text
                pos = 0
                while True:
                    if abort_flag and abort_flag.is_set():
                        return results
                    idx = self._mmap.find(pattern_bytes, pos)
                    if idx == -1:
                        break
                    line_no = self._byte_offset_to_line(idx)
                    if line_no not in self._modified_lines:
                        line_start = self._line_offsets[line_no]
                        col = len(self._mmap[line_start:idx].decode(
                            self._encoding, errors="replace"))
                        results.append((line_no, col, len(pattern)))
                    pos = idx + 1
                # Also search modified lines
                for line_no in sorted(self._modified_lines):
                    line_text = self._modified_lines[line_no]
                    start = 0
                    while True:
                        idx = line_text.find(pattern, start)
                        if idx == -1:
                            break
                        results.append((line_no, idx, len(pattern)))
                        start = idx + 1
                results.sort(key=lambda x: (x[0], x[1]))
            else:
                # Case-insensitive: search line by line
                lower_pattern = pattern.lower()
                for line_no in range(self.line_count):
                    if abort_flag and line_no % 1000 == 0 and abort_flag.is_set():
                        return results
                    line_text = self.get_line(line_no)
                    search_text = line_text.lower()
                    start = 0
                    while True:
                        idx = search_text.find(lower_pattern, start)
                        if idx == -1:
                            break
                        results.append((line_no, idx, len(pattern)))
                        start = idx + 1

        return results

    def replace_all(self, pattern: str, replacement: str,
                    case_sensitive: bool = False, use_regex: bool = False) -> int:
        """
        Replace all occurrences in the document.
        Modifies lines in-place via _modified_lines.
        Returns the count of replacements made.
        """
        if not pattern:
            return 0

        count = 0
        for line_no in range(self.line_count):
            line_text = self.get_line(line_no)
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                try:
                    new_text, n = re.subn(pattern, replacement, line_text, flags=flags)
                except re.error:
                    return count
            else:
                if case_sensitive:
                    n = line_text.count(pattern)
                    new_text = line_text.replace(pattern, replacement)
                else:
                    compiled = re.compile(re.escape(pattern), re.IGNORECASE)
                    new_text, n = compiled.subn(replacement, line_text)

            if n > 0:
                self._modified_lines[line_no] = new_text
                count += n

        return count

    def get_full_text(self) -> str:
        """Get the full document text with all modifications applied."""
        lines = []
        for i in range(self.line_count):
            lines.append(self.get_line(i))
        return "\n".join(lines)

    def save(self, path: Optional[str] = None):
        """Save the document, applying all modifications."""
        save_path = path or self._file_path
        text = self.get_full_text()
        # Close mmap before writing if saving to same file
        if save_path == self._file_path:
            self._mmap.close()
            self._file.close()
        with open(save_path, "w", encoding=self._encoding) as f:
            f.write(text)
        # Reopen if saved to same file
        if save_path == self._file_path:
            self._file = open(self._file_path, "rb")
            self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
            self._file_size = os.path.getsize(self._file_path)
            self._line_offsets = self._build_line_index()
            self._modified_lines.clear()

    def close(self):
        """Close the mmap and file."""
        if self._mmap:
            self._mmap.close()
            self._mmap = None
        if self._file:
            self._file.close()
            self._file = None

    def __del__(self):
        self.close()

    @staticmethod
    def is_large_file(file_path: str) -> bool:
        """Check if a file should use virtual document mode."""
        try:
            return os.path.getsize(file_path) > VirtualDocument.LARGE_FILE_THRESHOLD
        except OSError:
            return False
