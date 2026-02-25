"""Tests for the FindReplaceBar widget."""

import time

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor

from editor.code_editor import CodeEditor
from editor.find_replace import FindReplaceBar


@pytest.fixture
def editor(qapp):
    editor = CodeEditor()
    editor.setPlainText("Hello world\nhello World\nHELLO WORLD\nfoo bar baz")
    return editor


@pytest.fixture
def bar(editor):
    bar = FindReplaceBar(editor)
    return bar


class TestFindNext:
    def test_find_next_basic(self, bar, editor):
        bar._find_input.setText("hello")
        found = bar.find_next()
        assert found
        assert editor.textCursor().selectedText() == "Hello"

    def test_find_next_case_sensitive(self, bar, editor):
        bar._case_check.setChecked(True)
        bar._find_input.setText("hello")
        found = bar.find_next()
        assert found
        assert editor.textCursor().selectedText() == "hello"

    def test_find_next_wraps_around(self, bar, editor):
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        bar._find_input.setText("Hello")
        found = bar.find_next()
        assert found

    def test_find_next_no_match(self, bar, editor):
        bar._find_input.setText("notfound")
        found = bar.find_next()
        assert not found

    def test_find_next_regex(self, bar, editor):
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"H\w+o")
        found = bar.find_next()
        assert found
        assert editor.textCursor().selectedText() == "Hello"

    def test_find_next_regex_case_insensitive(self, bar, editor):
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"hello")
        found = bar.find_next()
        assert found
        assert editor.textCursor().selectedText() == "Hello"

    def test_find_empty_pattern_returns_false(self, bar):
        bar._find_input.setText("")
        assert not bar.find_next()


class TestFindPrevious:
    def test_find_previous_basic(self, bar, editor):
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        bar._find_input.setText("hello")
        found = bar.find_previous()
        assert found
        assert editor.textCursor().selectedText() == "HELLO"

    def test_find_previous_wraps_to_end(self, bar, editor):
        bar._find_input.setText("baz")
        found = bar.find_previous()
        assert found
        assert editor.textCursor().selectedText() == "baz"

    def test_find_previous_no_match(self, bar, editor):
        bar._find_input.setText("zzz")
        found = bar.find_previous()
        assert not found


class TestReplaceNext:
    def test_replace_next_replaces_match(self, bar, editor):
        bar._find_input.setText("foo")
        bar._replace_input.setText("qux")
        bar.find_next()
        bar.replace_next()
        assert "qux" in editor.toPlainText()
        assert "foo" not in editor.toPlainText()

    def test_replace_next_finds_first_if_no_selection(self, bar, editor):
        bar._find_input.setText("foo")
        bar._replace_input.setText("qux")
        bar.replace_next()
        assert editor.textCursor().hasSelection()

    def test_replace_next_case_sensitive(self, bar, editor):
        bar._case_check.setChecked(True)
        bar._find_input.setText("Hello")
        bar._replace_input.setText("Goodbye")
        bar.find_next()
        bar.replace_next()
        text = editor.toPlainText()
        assert text.startswith("Goodbye world")
        assert "hello World" in text

    def test_replace_next_regex(self, bar, editor):
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"(foo) (bar)")
        bar._replace_input.setText(r"\2 \1")
        bar.find_next()
        bar.replace_next()
        assert "bar foo" in editor.toPlainText()


class TestReplaceAll:
    def test_replace_all_basic(self, bar, editor):
        bar._find_input.setText("hello")
        bar._replace_input.setText("bye")
        count = bar.replace_all()
        assert count == 3
        assert "hello" not in editor.toPlainText().lower()

    def test_replace_all_case_sensitive(self, bar, editor):
        bar._case_check.setChecked(True)
        bar._find_input.setText("hello")
        bar._replace_input.setText("bye")
        count = bar.replace_all()
        assert count == 1
        text = editor.toPlainText()
        assert "bye World" in text
        assert "Hello world" in text

    def test_replace_all_regex(self, bar, editor):
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"\bworld\b")
        bar._replace_input.setText("earth")
        count = bar.replace_all()
        assert count == 3
        assert "world" not in editor.toPlainText().lower()

    def test_replace_all_no_match(self, bar, editor):
        bar._find_input.setText("zzz")
        bar._replace_input.setText("aaa")
        count = bar.replace_all()
        assert count == 0

    def test_replace_all_empty_pattern(self, bar):
        count = bar.replace_all()
        assert count == 0

    def test_replace_all_regex_invalid(self, bar, editor):
        bar._regex_check.setChecked(True)
        bar._find_input.setText("[invalid")
        bar._replace_input.setText("x")
        count = bar.replace_all()
        assert count == 0


class TestMatchCount:
    def test_match_count_updates(self, bar, editor):
        bar._find_input.setText("hello")
        bar._on_search_changed()
        assert bar._match_count == 3

    def test_match_count_case_sensitive(self, bar, editor):
        bar._case_check.setChecked(True)
        bar._find_input.setText("hello")
        bar._on_search_changed()
        assert bar._match_count == 1

    def test_match_count_no_results(self, bar, editor):
        bar._find_input.setText("nothere")
        bar._on_search_changed()
        assert bar._match_count == 0
        assert bar._match_label.text() == "No results"

    def test_match_count_empty_clears(self, bar, editor):
        bar._find_input.setText("")
        bar._on_search_changed()
        assert bar._match_label.text() == ""


class TestBarVisibility:
    def test_show_and_hide(self, bar, editor):
        assert not bar.isVisible()
        bar.show_bar()
        assert bar.isVisible()
        bar.hide_bar()
        assert not bar.isVisible()

    def test_show_populates_from_selection(self, bar, editor):
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(5, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        bar.show_bar()
        assert bar._find_input.text() == "Hello"

    def test_escape_hides(self, bar, editor):
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent

        bar.show_bar()
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        bar.keyPressEvent(event)
        assert not bar.isVisible()

    def test_hide_clears_highlights(self, bar, editor):
        bar._find_input.setText("hello")
        bar._on_search_changed()
        bar.find_next()
        bar.hide_bar()
        assert len(bar._extra_selections) == 0


# ---------------------------------------------------------------------------
# Edge-case fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_editor(qapp):
    ed = CodeEditor()
    ed.setPlainText("")
    return ed


@pytest.fixture
def empty_bar(empty_editor):
    return FindReplaceBar(empty_editor)


@pytest.fixture
def unicode_editor(qapp):
    ed = CodeEditor()
    ed.setPlainText("café naïve résumé\n🎉🎊🎉\nabc café def\nüöä straße")
    return ed


@pytest.fixture
def unicode_bar(unicode_editor):
    return FindReplaceBar(unicode_editor)


# ---------------------------------------------------------------------------
# Edge cases – empty / single-char documents
# ---------------------------------------------------------------------------

class TestEdgeCaseEmptyDocument:
    def test_find_in_empty_document(self, empty_bar):
        empty_bar._find_input.setText("a")
        assert not empty_bar.find_next()

    def test_replace_all_in_empty_document(self, empty_bar):
        empty_bar._find_input.setText("a")
        empty_bar._replace_input.setText("b")
        assert empty_bar.replace_all() == 0

    def test_match_count_empty_document(self, empty_bar):
        empty_bar._find_input.setText("x")
        empty_bar._on_search_changed()
        assert empty_bar._match_count == 0

    def test_find_empty_pattern_empty_document(self, empty_bar):
        empty_bar._find_input.setText("")
        assert not empty_bar.find_next()
        assert not empty_bar.find_previous()


class TestEdgeCaseSingleChar:
    def test_find_single_char_document(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("x")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("x")
        assert bar.find_next()
        assert ed.textCursor().selectedText() == "x"

    def test_replace_entire_single_char_document(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("x")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("x")
        bar._replace_input.setText("y")
        assert bar.replace_all() == 1
        assert ed.toPlainText() == "y"


# ---------------------------------------------------------------------------
# Edge cases – Unicode / multibyte
# ---------------------------------------------------------------------------

class TestEdgeCaseUnicode:
    def test_find_accented_characters(self, unicode_bar, unicode_editor):
        unicode_bar._find_input.setText("café")
        assert unicode_bar.find_next()
        assert unicode_editor.textCursor().selectedText() == "café"

    def test_find_accented_case_insensitive(self, unicode_bar, unicode_editor):
        unicode_bar._find_input.setText("CAFÉ")
        assert unicode_bar.find_next()

    def test_find_emoji(self, unicode_bar, unicode_editor):
        unicode_bar._find_input.setText("🎉")
        unicode_bar._on_search_changed()
        assert unicode_bar._match_count == 2

    def test_replace_unicode(self, unicode_bar, unicode_editor):
        unicode_bar._find_input.setText("straße")
        unicode_bar._replace_input.setText("strasse")
        assert unicode_bar.replace_all() == 1
        assert "strasse" in unicode_editor.toPlainText()
        assert "straße" not in unicode_editor.toPlainText()

    def test_replace_with_emoji(self, unicode_bar, unicode_editor):
        unicode_bar._find_input.setText("abc")
        unicode_bar._replace_input.setText("🚀")
        assert unicode_bar.replace_all() == 1
        assert "🚀" in unicode_editor.toPlainText()


# ---------------------------------------------------------------------------
# Edge cases – overlapping / adjacent matches
# ---------------------------------------------------------------------------

class TestEdgeCaseOverlapping:
    def test_overlapping_matches_plain(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("aaa")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("aa")
        bar._on_search_changed()
        assert bar._match_count == 2

    def test_adjacent_matches(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("ababab")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("ab")
        bar._on_search_changed()
        assert bar._match_count == 3

    def test_replace_all_overlapping(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("aaa")
        bar = FindReplaceBar(ed)
        bar._case_check.setChecked(True)
        bar._find_input.setText("aa")
        bar._replace_input.setText("b")
        count = bar.replace_all()
        assert count == 1
        assert ed.toPlainText() == "ba"


# ---------------------------------------------------------------------------
# Edge cases – boundary matches (start / end of document)
# ---------------------------------------------------------------------------

class TestEdgeCaseBoundaries:
    def test_match_at_document_start(self, bar, editor):
        bar._find_input.setText("Hello")
        found = bar.find_next(from_start=True)
        assert found
        cursor = editor.textCursor()
        assert cursor.selectionStart() == 0

    def test_match_at_document_end(self, bar, editor):
        bar._find_input.setText("baz")
        found = bar.find_next()
        assert found
        cursor = editor.textCursor()
        assert cursor.selectionEnd() == len(editor.toPlainText())

    def test_pattern_matches_entire_document(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("hello")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("hello")
        bar._on_search_changed()
        assert bar._match_count == 1
        bar._replace_input.setText("goodbye")
        assert bar.replace_all() == 1
        assert ed.toPlainText() == "goodbye"


# ---------------------------------------------------------------------------
# Edge cases – newlines and whitespace
# ---------------------------------------------------------------------------

class TestEdgeCaseWhitespace:
    def test_find_tab_character(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("col1\tcol2\tcol3")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("\t")
        bar._on_search_changed()
        assert bar._match_count == 2

    def test_replace_tabs_with_spaces(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("a\tb\tc")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("\t")
        bar._replace_input.setText("    ")
        count = bar.replace_all()
        assert count == 2
        assert "\t" not in ed.toPlainText()
        assert ed.toPlainText() == "a    b    c"

    def test_find_newline_in_regex(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("line1\nline2\nline3")
        bar = FindReplaceBar(ed)
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"line1\nline2")
        bar._on_search_changed()
        assert bar._match_count == 1

    def test_find_whitespace_only_pattern(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("a b c")
        bar = FindReplaceBar(ed)
        bar._find_input.setText(" ")
        bar._on_search_changed()
        assert bar._match_count == 2


# ---------------------------------------------------------------------------
# Edge cases – replacement content edge cases
# ---------------------------------------------------------------------------

class TestEdgeCaseReplacements:
    def test_replace_with_empty_string(self, bar, editor):
        bar._find_input.setText("foo bar baz")
        bar._replace_input.setText("")
        count = bar.replace_all()
        assert count == 1
        assert "foo" not in editor.toPlainText()

    def test_replace_with_longer_text(self, bar, editor):
        original_len = len(editor.toPlainText())
        bar._find_input.setText("foo")
        bar._replace_input.setText("a very long replacement string")
        bar.replace_all()
        assert len(editor.toPlainText()) > original_len

    def test_replace_with_pattern_in_replacement(self, qapp):
        """Replacing 'a' with 'aa' must not loop infinitely."""
        ed = CodeEditor()
        ed.setPlainText("aaa")
        bar = FindReplaceBar(ed)
        bar._case_check.setChecked(True)
        bar._find_input.setText("a")
        bar._replace_input.setText("aa")
        count = bar.replace_all()
        assert count == 3
        assert ed.toPlainText() == "aaaaaa"

    def test_replace_next_skips_non_matching_selection(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("abc def ghi")
        bar = FindReplaceBar(ed)
        cursor = ed.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(3, QTextCursor.MoveMode.KeepAnchor)
        ed.setTextCursor(cursor)
        bar._find_input.setText("def")
        bar._replace_input.setText("xyz")
        bar.replace_next()
        assert "abc" in ed.toPlainText()
        assert ed.textCursor().selectedText() == "def"

    def test_replace_next_with_empty_pattern(self, bar):
        bar._find_input.setText("")
        bar._replace_input.setText("x")
        bar.replace_next()

    def test_replace_next_regex_invalid(self, bar, editor):
        bar._regex_check.setChecked(True)
        bar._find_input.setText("[bad")
        bar._replace_input.setText("x")
        bar.find_next()
        bar.replace_next()


# ---------------------------------------------------------------------------
# Edge cases – special regex characters as literal search
# ---------------------------------------------------------------------------

class TestEdgeCaseSpecialChars:
    def test_literal_dot_search(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("file.txt file_txt")
        bar = FindReplaceBar(ed)
        bar._find_input.setText(".")
        bar._on_search_changed()
        assert bar._match_count == 1

    def test_regex_dot_matches_all(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("file.txt file_txt")
        bar = FindReplaceBar(ed)
        bar._regex_check.setChecked(True)
        bar._find_input.setText("file.txt")
        bar._on_search_changed()
        assert bar._match_count == 2

    def test_literal_bracket_search(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("array[0] = value")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("[0]")
        assert bar.find_next()
        assert ed.textCursor().selectedText() == "[0]"

    def test_literal_backslash_search(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("C:\\Users\\test")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("\\")
        bar._on_search_changed()
        assert bar._match_count == 2

    def test_literal_dollar_search(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("price is $100")
        bar = FindReplaceBar(ed)
        bar._find_input.setText("$100")
        assert bar.find_next()
        assert ed.textCursor().selectedText() == "$100"


# ---------------------------------------------------------------------------
# Edge cases – find cycling (next wraps, previous wraps)
# ---------------------------------------------------------------------------

class TestFindCycling:
    def test_find_next_cycles_through_all_matches(self, bar, editor):
        bar._case_check.setChecked(True)
        bar._find_input.setText("Hello")
        positions = []
        bar.find_next(from_start=True)
        first_pos = editor.textCursor().selectionStart()
        positions.append(first_pos)
        while True:
            bar.find_next()
            pos = editor.textCursor().selectionStart()
            if pos == first_pos:
                break
            positions.append(pos)
        assert len(positions) == 1

    def test_find_next_cycles_multiple_matches(self, bar, editor):
        bar._find_input.setText("hello")
        positions = []
        bar.find_next(from_start=True)
        first_pos = editor.textCursor().selectionStart()
        positions.append(first_pos)
        for _ in range(10):
            bar.find_next()
            pos = editor.textCursor().selectionStart()
            if pos == first_pos:
                break
            positions.append(pos)
        assert len(positions) == 3

    def test_find_previous_cycles_all_matches(self, bar, editor):
        bar._find_input.setText("hello")
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        positions = []
        bar.find_previous()
        first_pos = editor.textCursor().selectionStart()
        positions.append(first_pos)
        for _ in range(10):
            bar.find_previous()
            pos = editor.textCursor().selectionStart()
            if pos == first_pos:
                break
            positions.append(pos)
        assert len(positions) == 3


# ---------------------------------------------------------------------------
# Edge cases – match counter label accuracy
# ---------------------------------------------------------------------------

class TestMatchCounterAccuracy:
    def test_counter_label_format(self, bar, editor):
        bar._find_input.setText("hello")
        bar._on_search_changed()
        label = bar._match_label.text()
        assert "of" in label
        assert "3" in label

    def test_counter_updates_after_replace(self, bar, editor):
        bar._find_input.setText("hello")
        bar._on_search_changed()
        assert bar._match_count == 3
        bar._replace_input.setText("x")
        bar.find_next()
        bar.replace_next()
        assert bar._match_count == 2

    def test_counter_zero_after_replace_all(self, bar, editor):
        bar._find_input.setText("hello")
        bar._replace_input.setText("x")
        bar.replace_all()
        bar._on_search_changed()
        assert bar._match_count == 0

    def test_counter_no_results_style(self, bar, editor):
        bar._find_input.setText("zzzznotfound")
        bar._on_search_changed()
        assert "No results" in bar._match_label.text()
        assert "CC0000" in bar._match_label.styleSheet()


# ---------------------------------------------------------------------------
# Edge cases – regex specific
# ---------------------------------------------------------------------------

class TestRegexEdgeCases:
    def test_regex_case_sensitive(self, bar, editor):
        bar._regex_check.setChecked(True)
        bar._case_check.setChecked(True)
        bar._find_input.setText("hello")
        bar._on_search_changed()
        assert bar._match_count == 1

    def test_regex_multiline_pattern(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("start\nmiddle\nend")
        bar = FindReplaceBar(ed)
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"start\nmiddle")
        bar._on_search_changed()
        assert bar._match_count == 1

    def test_regex_groups_in_replace(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("John Smith, Jane Doe")
        bar = FindReplaceBar(ed)
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"(\w+) (\w+)")
        bar._replace_input.setText(r"\2, \1")
        count = bar.replace_all()
        assert count == 2
        text = ed.toPlainText()
        assert "Smith, John" in text
        assert "Doe, Jane" in text

    def test_regex_empty_match_pattern(self, qapp):
        """A pattern like .* can match empty strings; should not hang."""
        ed = CodeEditor()
        ed.setPlainText("abc")
        bar = FindReplaceBar(ed)
        bar._regex_check.setChecked(True)
        bar._find_input.setText("x*")
        matches = bar._find_all_matches()
        assert isinstance(matches, list)

    def test_regex_lookahead(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("foobar foobaz")
        bar = FindReplaceBar(ed)
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"foo(?=bar)")
        bar._on_search_changed()
        assert bar._match_count == 1

    def test_find_previous_empty_pattern(self, bar):
        bar._find_input.setText("")
        assert not bar.find_previous()

    def test_find_previous_regex(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("abc 123 def 456")
        bar = FindReplaceBar(ed)
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"\d+")
        cursor = ed.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        ed.setTextCursor(cursor)
        found = bar.find_previous()
        assert found
        assert ed.textCursor().selectedText() == "456"


# ---------------------------------------------------------------------------
# Edge cases – highlight integrity
# ---------------------------------------------------------------------------

class TestHighlightIntegrity:
    def test_highlights_count_matches_match_count(self, bar, editor):
        bar._find_input.setText("hello")
        bar._on_search_changed()
        assert len(bar._extra_selections) == bar._match_count

    def test_highlights_cleared_when_pattern_cleared(self, bar, editor):
        bar._find_input.setText("hello")
        bar._on_search_changed()
        assert len(bar._extra_selections) > 0
        bar._find_input.setText("")
        bar._on_search_changed()
        assert len(bar._extra_selections) == 0

    def test_highlights_update_after_case_toggle(self, bar, editor):
        bar._find_input.setText("hello")
        bar._on_search_changed()
        count_insensitive = len(bar._extra_selections)
        bar._case_check.setChecked(True)
        bar._on_search_changed()
        count_sensitive = len(bar._extra_selections)
        assert count_insensitive > count_sensitive


# ---------------------------------------------------------------------------
# Performance tests
# ---------------------------------------------------------------------------

class TestPerformance:
    @pytest.fixture
    def large_editor(self, qapp):
        lines = [f"line {i} with some text and data value={i}" for i in range(100_000)]
        ed = CodeEditor()
        ed.setPlainText("\n".join(lines))
        return ed

    def test_find_all_matches_large_file(self, large_editor, qapp):
        bar = FindReplaceBar(large_editor)
        bar._find_input.setText("data")
        start = time.perf_counter()
        matches = bar._find_all_matches()
        elapsed = time.perf_counter() - start
        assert len(matches) == 100_000
        assert elapsed < 2.0, f"find_all_matches took {elapsed:.2f}s on 100k lines"

    def test_find_all_case_sensitive_large_file(self, large_editor, qapp):
        bar = FindReplaceBar(large_editor)
        bar._case_check.setChecked(True)
        bar._find_input.setText("data")
        start = time.perf_counter()
        matches = bar._find_all_matches()
        elapsed = time.perf_counter() - start
        assert len(matches) == 100_000
        assert elapsed < 2.0, f"case-sensitive find took {elapsed:.2f}s"

    def test_find_next_large_file(self, large_editor, qapp):
        bar = FindReplaceBar(large_editor)
        bar._find_input.setText("value=99999")
        start = time.perf_counter()
        found = bar.find_next()
        elapsed = time.perf_counter() - start
        assert found
        assert elapsed < 2.0, f"find_next took {elapsed:.2f}s on 100k lines"

    def test_replace_all_large_file(self, large_editor, qapp):
        bar = FindReplaceBar(large_editor)
        bar._find_input.setText("data")
        bar._replace_input.setText("info")
        start = time.perf_counter()
        count = bar.replace_all()
        elapsed = time.perf_counter() - start
        assert count == 100_000
        assert elapsed < 5.0, f"replace_all took {elapsed:.2f}s on 100k lines"
        assert "data" not in large_editor.toPlainText()

    def test_regex_find_large_file(self, large_editor, qapp):
        bar = FindReplaceBar(large_editor)
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"value=\d+")
        start = time.perf_counter()
        matches = bar._find_all_matches()
        elapsed = time.perf_counter() - start
        assert len(matches) == 100_000
        assert elapsed < 3.0, f"regex find took {elapsed:.2f}s on 100k lines"

    def test_no_match_large_file_fast(self, large_editor, qapp):
        bar = FindReplaceBar(large_editor)
        bar._find_input.setText("ZZZZNOTFOUND")
        start = time.perf_counter()
        matches = bar._find_all_matches()
        elapsed = time.perf_counter() - start
        assert len(matches) == 0
        assert elapsed < 1.0, f"no-match search took {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# Undo / Redo integration
# ---------------------------------------------------------------------------

class TestReplaceAllUndo:
    def test_replace_all_undone_in_one_step(self, bar, editor):
        """Replace-all of N occurrences must revert with a single Ctrl+Z."""
        original = editor.toPlainText()
        bar._find_input.setText("hello")
        bar._replace_input.setText("goodbye")
        count = bar.replace_all()
        assert count == 3
        assert "hello" not in editor.toPlainText().lower()

        editor.undo()
        assert editor.toPlainText() == original

    def test_replace_all_redo_after_undo(self, bar, editor):
        """After undoing replace-all, redo should reapply it."""
        bar._find_input.setText("hello")
        bar._replace_input.setText("goodbye")
        bar.replace_all()
        replaced_text = editor.toPlainText()

        editor.undo()
        editor.redo()
        assert editor.toPlainText() == replaced_text

    def test_replace_all_case_sensitive_undo(self, bar, editor):
        original = editor.toPlainText()
        bar._case_check.setChecked(True)
        bar._find_input.setText("Hello")
        bar._replace_input.setText("Greetings")
        count = bar.replace_all()
        assert count == 1
        assert "Greetings" in editor.toPlainText()

        editor.undo()
        assert editor.toPlainText() == original

    def test_replace_all_regex_undo(self, bar, editor):
        original = editor.toPlainText()
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"\bhello\b")
        bar._replace_input.setText("hi")
        bar.replace_all()

        editor.undo()
        assert editor.toPlainText() == original

    def test_replace_all_with_empty_replacement_undo(self, bar, editor):
        """Deleting via replace-all (replace with '') must be undoable."""
        original = editor.toPlainText()
        bar._find_input.setText("foo bar baz")
        bar._replace_input.setText("")
        bar.replace_all()
        assert "foo" not in editor.toPlainText()

        editor.undo()
        assert editor.toPlainText() == original

    def test_multiple_replace_all_undo_independently(self, qapp):
        """Two separate replace-all operations should each undo separately."""
        ed = CodeEditor()
        ed.setPlainText("aaa bbb ccc")
        bar = FindReplaceBar(ed)

        bar._find_input.setText("aaa")
        bar._replace_input.setText("xxx")
        bar.replace_all()
        assert "xxx" in ed.toPlainText()

        bar._find_input.setText("bbb")
        bar._replace_input.setText("yyy")
        bar.replace_all()
        assert "yyy" in ed.toPlainText()

        ed.undo()
        assert ed.toPlainText() == "xxx bbb ccc"

        ed.undo()
        assert ed.toPlainText() == "aaa bbb ccc"


class TestReplaceNextUndo:
    def test_replace_next_undoable(self, bar, editor):
        """A single replace-next should be undoable."""
        original = editor.toPlainText()
        bar._find_input.setText("foo")
        bar._replace_input.setText("qux")
        bar.find_next()
        bar.replace_next()
        assert "qux" in editor.toPlainText()

        editor.undo()
        assert editor.toPlainText() == original

    def test_replace_next_redo(self, bar, editor):
        bar._find_input.setText("foo")
        bar._replace_input.setText("qux")
        bar.find_next()
        bar.replace_next()
        replaced_text = editor.toPlainText()

        editor.undo()
        editor.redo()
        assert editor.toPlainText() == replaced_text

    def test_multiple_replace_next_undo_individually(self, qapp):
        """Each replace-next should be a separate undo step."""
        ed = CodeEditor()
        ed.setPlainText("a b a b a")
        bar = FindReplaceBar(ed)
        bar._case_check.setChecked(True)
        bar._find_input.setText("a")
        bar._replace_input.setText("x")

        bar.find_next()
        bar.replace_next()
        bar.replace_next()
        assert ed.toPlainText() == "x b x b a"

        ed.undo()
        assert ed.toPlainText() == "x b a b a"

        ed.undo()
        assert ed.toPlainText() == "a b a b a"

    def test_replace_next_regex_undo(self, qapp):
        ed = CodeEditor()
        ed.setPlainText("foo bar")
        original = ed.toPlainText()
        bar = FindReplaceBar(ed)
        bar._regex_check.setChecked(True)
        bar._find_input.setText(r"(foo) (bar)")
        bar._replace_input.setText(r"\2 \1")
        bar.find_next()
        bar.replace_next()
        assert "bar foo" in ed.toPlainText()

        ed.undo()
        assert ed.toPlainText() == original
