"""Tests for CppTokenizer, PlainTokenizer, and IncrementalManager."""

import pytest

from editor.highlighters.core.types import StateStack, StackFrame, StyleId, Token
from editor.highlighters.tokenizers.cpp_tokenizer import CppTokenizer
from editor.highlighters.tokenizers.plain_tokenizer import PlainTokenizer
from editor.highlighters.core.incremental_manager import IncrementalManager


def extract(line, tokens):
    return [(line[t.start:t.start + t.length], t.style_id) for t in tokens]


# ─── CppTokenizer Tests ─────────────────────────────────────────────────────


class TestCppTokenizerKeywords:
    """Test that C++ specific keywords are recognised."""

    @pytest.fixture
    def tok(self):
        return CppTokenizer()

    @pytest.fixture
    def empty_stack(self) -> StateStack:
        return ()

    @pytest.mark.parametrize("keyword", [
        "class", "namespace", "template", "virtual", "override",
        "nullptr", "bool", "constexpr", "noexcept", "decltype",
    ])
    def test_cpp_keywords(self, tok, empty_stack, keyword):
        result = tok.tokenize_line(keyword, empty_stack)
        pairs = extract(keyword, result.tokens)
        assert pairs == [(keyword, StyleId.KEYWORD)]

    @pytest.mark.parametrize("keyword", ["int", "return", "if", "while"])
    def test_c_keywords_still_work(self, tok, empty_stack, keyword):
        result = tok.tokenize_line(keyword, empty_stack)
        pairs = extract(keyword, result.tokens)
        assert pairs == [(keyword, StyleId.KEYWORD)]

    def test_identifiers_not_keywords(self, tok, empty_stack):
        line = "myVar"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("myVar", StyleId.IDENTIFIER)]


class TestCppTokenizerComments:
    """Test block comment handling (inherited from CTokenizer)."""

    @pytest.fixture
    def tok(self):
        return CppTokenizer()

    @pytest.fixture
    def empty_stack(self) -> StateStack:
        return ()

    def test_single_line_block_comment(self, tok, empty_stack):
        line = "/* comment */"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("/* comment */", StyleId.COMMENT)]

    def test_multiline_block_comment_open(self, tok, empty_stack):
        line = "/* start of comment"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("/* start of comment", StyleId.COMMENT)]
        # State stack should have a frame with lang_id "cpp"
        assert len(result.final_stack) == 1
        assert result.final_stack[-1].lang_id == "cpp"
        assert result.final_stack[-1].sub_state == 1  # STATE_BLOCK_COMMENT

    def test_multiline_block_comment_continue(self, tok):
        # Simulate continuing inside a block comment
        comment_stack: StateStack = (StackFrame(lang_id="cpp", sub_state=1, end_condition=None),)
        line = "still in comment */"
        result = tok.tokenize_line(line, comment_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("still in comment */", StyleId.COMMENT)]
        # Stack should be empty after comment ends
        assert result.final_stack == ()

    def test_multiline_block_comment_no_close(self, tok):
        comment_stack: StateStack = (StackFrame(lang_id="cpp", sub_state=1, end_condition=None),)
        line = "middle of comment"
        result = tok.tokenize_line(line, comment_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("middle of comment", StyleId.COMMENT)]
        assert result.final_stack == comment_stack


class TestCppTokenizerLiterals:
    """Test strings, char literals, numbers, operators, punctuation."""

    @pytest.fixture
    def tok(self):
        return CppTokenizer()

    @pytest.fixture
    def empty_stack(self) -> StateStack:
        return ()

    def test_string_literal(self, tok, empty_stack):
        line = '"hello"'
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [('"hello"', StyleId.STRING)]

    def test_char_literal(self, tok, empty_stack):
        line = "'a'"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("'a'", StyleId.STRING)]

    def test_number(self, tok, empty_stack):
        line = "42"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("42", StyleId.NUMBER)]

    def test_operators(self, tok, empty_stack):
        line = "+"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("+", StyleId.OPERATOR)]

    def test_punctuation(self, tok, empty_stack):
        line = "{"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [("{", StyleId.PUNCTUATION)]


class TestCppTokenizerMixed:
    """Test mixed expressions and edge cases."""

    @pytest.fixture
    def tok(self):
        return CppTokenizer()

    @pytest.fixture
    def empty_stack(self) -> StateStack:
        return ()

    def test_include_directive(self, tok, empty_stack):
        line = "#include <iostream>"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        # #include is KEYWORD; <iostream> breaks into < OPERATOR, iostream IDENTIFIER, > OPERATOR
        assert pairs[0] == ("#include", StyleId.KEYWORD)
        # Verify < and > are operators, iostream is identifier
        texts = [p[0] for p in pairs]
        assert "<" in texts
        assert "iostream" in texts
        assert ">" in texts

    def test_class_declaration(self, tok, empty_stack):
        line = "class MyClass : public Base { };"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        expected = [
            ("class", StyleId.KEYWORD),
            ("MyClass", StyleId.IDENTIFIER),
            (":", StyleId.OPERATOR),
            ("public", StyleId.KEYWORD),
            ("Base", StyleId.IDENTIFIER),
            ("{", StyleId.PUNCTUATION),
            ("}", StyleId.PUNCTUATION),
            (";", StyleId.PUNCTUATION),
        ]
        assert pairs == expected

    def test_nullptr_vs_null(self, tok, empty_stack):
        line = "nullptr NULL"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ("nullptr", StyleId.KEYWORD),
            ("NULL", StyleId.IDENTIFIER),
        ]

    def test_auto_keyword_inherited(self, tok, empty_stack):
        line = "auto x = 42;"
        result = tok.tokenize_line(line, empty_stack)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ("auto", StyleId.KEYWORD),
            ("x", StyleId.IDENTIFIER),
            ("=", StyleId.OPERATOR),
            ("42", StyleId.NUMBER),
            (";", StyleId.PUNCTUATION),
        ]


# ─── PlainTokenizer Tests ───────────────────────────────────────────────────


class TestPlainTokenizer:

    @pytest.fixture
    def tok(self):
        return PlainTokenizer()

    @pytest.fixture
    def empty_stack(self) -> StateStack:
        return ()

    def test_non_empty_line(self, tok, empty_stack):
        line = "Hello World"
        result = tok.tokenize_line(line, empty_stack)
        assert len(result.tokens) == 1
        t = result.tokens[0]
        assert t.start == 0
        assert t.length == 11
        assert t.style_id == StyleId.PLAIN

    def test_empty_line(self, tok, empty_stack):
        result = tok.tokenize_line("", empty_stack)
        assert result.tokens == []

    def test_state_stack_passed_through(self, tok):
        custom_stack: StateStack = (StackFrame("plain", 0, None),)
        result = tok.tokenize_line("text", custom_stack)
        assert result.final_stack is custom_stack

    def test_whitespace_only_line(self, tok, empty_stack):
        line = "   "
        result = tok.tokenize_line(line, empty_stack)
        assert len(result.tokens) == 1
        t = result.tokens[0]
        assert t.start == 0
        assert t.length == 3
        assert t.style_id == StyleId.PLAIN


# ─── IncrementalManager Tests ────────────────────────────────────────────────


class TestIncrementalManagerSetLineCount:

    def test_grow_from_zero(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        assert len(mgr._line_states) == 5
        assert len(mgr._line_hashes) == 5
        assert all(s == -1 for s in mgr._line_states)
        assert all(h == -1 for h in mgr._line_hashes)

    def test_shrink(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        mgr.set_line_count(3)
        assert len(mgr._line_states) == 3
        assert len(mgr._line_hashes) == 3

    def test_same_count(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        mgr._line_states[0] = 99
        mgr.set_line_count(5)
        # No change; existing data preserved
        assert len(mgr._line_states) == 5
        assert mgr._line_states[0] == 99


class TestIncrementalManagerUpdateLine:

    def test_first_update_returns_true(self):
        mgr = IncrementalManager()
        mgr.set_line_count(3)
        assert mgr.update_line(0, "hello", 0) is True

    def test_same_text_and_state_returns_false(self):
        mgr = IncrementalManager()
        mgr.set_line_count(3)
        mgr.update_line(0, "hello", 0)
        assert mgr.update_line(0, "hello", 0) is False

    def test_text_change_returns_true(self):
        mgr = IncrementalManager()
        mgr.set_line_count(3)
        mgr.update_line(0, "hello", 0)
        assert mgr.update_line(0, "world", 0) is True

    def test_state_change_returns_true(self):
        mgr = IncrementalManager()
        mgr.set_line_count(3)
        mgr.update_line(0, "hello", 0)
        assert mgr.update_line(0, "hello", 1) is True

    def test_out_of_bounds_returns_true(self):
        mgr = IncrementalManager()
        mgr.set_line_count(3)
        assert mgr.update_line(10, "hello", 0) is True


class TestIncrementalManagerGetInitialStateId:

    def test_line_zero_returns_neg1(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        assert mgr.get_initial_state_id(0) == -1

    def test_line_one_returns_state_of_line_zero(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        mgr.update_line(0, "hello", 42)
        assert mgr.get_initial_state_id(1) == 42

    def test_out_of_bounds_returns_neg1(self):
        mgr = IncrementalManager()
        mgr.set_line_count(3)
        assert mgr.get_initial_state_id(100) == -1


class TestIncrementalManagerInvalidate:

    def test_invalidate_from_sets_states_to_neg1(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        for i in range(5):
            mgr.update_line(i, f"line{i}", i * 10)
        mgr.invalidate_from(2)
        assert mgr._line_states[2] == -1
        assert mgr._line_states[3] == -1
        assert mgr._line_states[4] == -1

    def test_invalidate_preserves_before_index(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        for i in range(5):
            mgr.update_line(i, f"line{i}", i * 10)
        mgr.invalidate_from(2)
        assert mgr._line_states[0] == 0
        assert mgr._line_states[1] == 10


class TestIncrementalManagerClear:

    def test_clear_resets_everything(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        mgr.update_line(0, "hello", 42)
        mgr.clear()
        assert mgr._line_states == []
        assert mgr._line_hashes == []

    def test_after_clear_set_line_count_works(self):
        mgr = IncrementalManager()
        mgr.set_line_count(5)
        mgr.update_line(0, "hello", 42)
        mgr.clear()
        mgr.set_line_count(3)
        assert len(mgr._line_states) == 3
        assert all(s == -1 for s in mgr._line_states)


class TestPlainTokenizerLangId:
    def test_get_lang_id(self):
        tok = PlainTokenizer()
        assert tok.get_lang_id() == "plain"


class TestCoreBaseTokenizerHelpers:
    """Test the core BaseTokenizer helper methods via CppTokenizer."""

    def test_current_frame_empty_stack(self):
        tok = CppTokenizer()
        assert tok._current_frame(()) is None

    def test_current_frame_non_empty(self):
        tok = CppTokenizer()
        frame = StackFrame("cpp", 0, None)
        assert tok._current_frame((frame,)) == frame

    def test_pop_state_empty_stack(self):
        tok = CppTokenizer()
        assert tok._pop_state(()) == ()

    def test_default_frame(self):
        tok = CppTokenizer()
        frame = tok._default_frame()
        assert frame.lang_id == "cpp"
        assert frame.sub_state == 0
        assert frame.end_condition is None
